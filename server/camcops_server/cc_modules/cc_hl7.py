#!/usr/bin/env python3
# cc_hl7.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import datetime
import errno
import codecs
import hl7
import lockfile
import os
import socket
import subprocess
import sys
import typing
from typing import Any, List, Optional, Tuple, Union

import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_net import ping

from .cc_constants import (
    ACTION,
    DATEFORMAT,
    HL7MESSAGE_TABLENAME,
    ERA_NOW,
    PARAM,
    VALUE,
)
from . import cc_db
from . import cc_dt
from . import cc_filename
from .cc_hl7core import (
    escape_hl7_text,
    get_mod11_checkdigit,
    make_msh_segment,
    make_obr_segment,
    make_obx_segment,
    make_pid_segment,
    msg_is_successful_ack,
    SEGMENT_SEPARATOR,
)
from . import cc_html
from .cc_logger import log
from . import cc_namedtuples
from .cc_pls import pls
from .cc_recipdef import RecipientDefinition
from . import cc_task
from .cc_unittest import unit_test_ignore


# =============================================================================
# General HL7 sources
# =============================================================================
# http://python-hl7.readthedocs.org/en/latest/
# http://www.interfaceware.com/manual/v3gen_python_library_details.html
# http://www.interfaceware.com/hl7_video_vault.html#how
# http://www.interfaceware.com/hl7-standard/hl7-segments.html
# http://www.hl7.org/special/committees/vocab/v26_appendix_a.pdf
# http://www.ncbi.nlm.nih.gov/pmc/articles/PMC130066/

# =============================================================================
# HL7 design
# =============================================================================

# WHICH RECORDS TO SEND?
# Most powerful mechanism is not to have a sending queue (which would then
# require careful multi-instance locking), but to have a "sent" log. That way:
# - A record needs sending if it's not in the sent log (for an appropriate
#   server).
# - You can add a new server and the system will know about the (new) backlog
#   automatically.
# - You can specify criteria, e.g. don't upload records before 1/1/2014, and
#   modify that later, and it would catch up with the backlog.
# - Successes and failures are logged in the same table.
# - Multiple recipients are handled with ease.
# - No need to alter database.pl code that receives from tablets.
# - Can run with a simple cron job.

# LOCKING
# - Don't use database locking:
#   https://blog.engineyard.com/2011/5-subtle-ways-youre-using-mysql-as-a-queue-and-why-itll-bite-you  # noqa
# - Locking via UNIX lockfiles:
#       https://pypi.python.org/pypi/lockfile
#       http://pythonhosted.org/lockfile/

# CALLING THE HL7 PROCESSOR
# - Use "camcops -7 ..." or "camcops --hl7 ..."
# - Call it via a cron job, e.g. every 5 minutes.

# CONFIG FILE
# q.v.

# TO CONSIDER
# - batched messages (HL7 batching protocol)
#   http://docs.oracle.com/cd/E23943_01/user.1111/e23486/app_hl7batching.htm
# - note: DG1 segment = diagnosis

# BASIC MESSAGE STRUCTURE
# - package into HL7 2.X message as encapsulated PDF
#   http://www.hl7standards.com/blog/2007/11/27/pdf-attachment-in-hl7-message/
# - message ORU^R01
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-messages
#   MESSAGES: http://www.interfaceware.com/hl7-standard/hl7-messages.html
# - OBX segment = observation/result segment
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-obx-segment  # noqa
#   http://www.interfaceware.com/hl7-standard/hl7-segment-OBX.html
# - SEGMENTS:
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-segments
# - ED field (= encapsulated data)
#   http://www.interfaceware.com/hl7-standard/hl7-fields.html
# - base-64 encoding
# - Option for structure (XML), HTML, PDF export.


# =============================================================================
# HL7Run class
# =============================================================================

class HL7Run(object):
    """Class representing an HL7/file run for a specific recipient.

    May be associated with multiple HL7/file messages.
    """
    TABLENAME = "_hl7_run_log"
    FIELDSPECS = [
        dict(name="run_id", cctype="BIGINT_UNSIGNED", pk=True,
             autoincrement=True, comment="Arbitrary primary key"),
        # 4294967296 values, so at 1/minute, 8165 years.
        dict(name="start_at_utc", cctype="DATETIME",
             comment="Time run was started (UTC)"),
        dict(name="finish_at_utc", cctype="DATETIME",
             comment="Time run was finished (UTC)"),
    ] + RecipientDefinition.FIELDSPECS + [
        dict(name="script_retcode", cctype="INT",
             comment="Return code from the script_after_file_export script"),
        dict(name="script_stdout", cctype="TEXT",
             comment="stdout from the script_after_file_export script"),
        dict(name="script_stderr", cctype="TEXT",
             comment="stderr from the script_after_file_export script"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, param: Union[RecipientDefinition, int]) -> None:
        if isinstance(param, RecipientDefinition):
            rnc_db.blank_object(self, HL7Run.FIELDS)
            # Copy all attributes from the RecipientDefinition
            self.__dict__.update(param.__dict__)

            self.start_at_utc = cc_dt.get_now_utc_notz()
            self.finish_at_utc = None
            self.save()
        else:
            pls.db.fetch_object_from_db_by_pk(self, HL7Run.TABLENAME,
                                              HL7Run.FIELDS, param)

    def save(self) -> None:
        pls.db.save_object_to_db(self, HL7Run.TABLENAME, HL7Run.FIELDS,
                                 self.run_id is None)

    def call_script(self, files_exported: Optional[List[str]]) -> None:
        if not self.script_after_file_export:
            # No script to call
            return
        if not files_exported:
            # Didn't export any files; nothing to do.
            self.script_after_file_export = None  # wasn't called
            return
        args = [self.script_after_file_export] + files_exported
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            self.script_stdout, self.script_stderr = p.communicate()
            self.script_retcode = p.returncode
        except Exception as e:
            self.script_stdout = "Failed to run script"
            self.script_stderr = str(e)

    def finish(self) -> None:
        self.finish_at_utc = cc_dt.get_now_utc_notz()
        self.save()

    @classmethod
    def get_html_header_row(cls) -> str:
        html = "<tr>"
        for fs in cls.FIELDSPECS:
            html += "<th>{}</th>".format(fs["name"])
        html += "</tr>\n"
        return html

    def get_html_data_row(self) -> str:
        html = "<tr>"
        for fs in self.FIELDSPECS:
            name = fs["name"]
            value = ws.webify(getattr(self, name))
            html += "<td>{}</td>".format(value)
        html += "</tr>\n"
        return html


# =============================================================================
# HL7Message class
# =============================================================================

class HL7Message(object):
    TABLENAME = HL7MESSAGE_TABLENAME
    FIELDSPECS = [
        dict(name="msg_id", cctype="INT_UNSIGNED", pk=True,
             autoincrement=True, comment="Arbitrary primary key"),
        dict(name="run_id", cctype="INT_UNSIGNED",
             comment="FK to _hl7_run_log.run_id"),
        dict(name="basetable", cctype="TABLENAME", indexed=True,
             comment="Base table of task concerned"),
        dict(name="serverpk", cctype="INT_UNSIGNED", indexed=True,
             comment="Server PK of task in basetable (_pk field)"),
        dict(name="sent_at_utc", cctype="DATETIME",
             comment="Time message was sent at (UTC)"),
        dict(name="reply_at_utc", cctype="DATETIME",
             comment="(HL7) Time message was replied to (UTC)"),
        dict(name="success", cctype="BOOL",
             comment="Message sent successfully (and, for HL7, acknowledged)"),
        dict(name="failure_reason", cctype="TEXT",
             comment="Reason for failure"),
        dict(name="message", cctype="LONGTEXT",
             comment="(HL7) Message body, if kept"),
        dict(name="reply", cctype="TEXT",
             comment="(HL7) Server's reply, if kept"),
        dict(name="filename", cctype="TEXT",
             comment="(FILE) Destination filename"),
        dict(name="rio_metadata_filename", cctype="TEXT",
             comment="(FILE) RiO metadata filename, if used"),
        dict(name="cancelled", cctype="BOOL",
             comment="Message subsequently invalidated (may trigger resend)"),
        dict(name="cancelled_at_utc", cctype="DATETIME",
             comment="Time message was cancelled at (UTC)"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Creates underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self,
                 msg_id: int = None,
                 basetable: str = None,
                 serverpk: int = None,
                 hl7run: HL7Run = None,
                 recipient_def: RecipientDefinition = None,
                 show_queue_only: bool = False) -> None:
        """Initializes.

        Use either:
            HL7Message(msg_id)
        or:
            HL7Message(basetable, serverpk, hl7run, recipient_def)
        """
        if basetable and serverpk and recipient_def:
            # HL7Message(basetable, serverpk, hl7run, recipient_def)
            rnc_db.blank_object(self, HL7Message.FIELDS)
            self.basetable = basetable
            self.serverpk = serverpk
            self.hl7run = hl7run
            if self.hl7run:
                self.run_id = self.hl7run.run_id
            self.recipient_def = recipient_def
            self.show_queue_only = show_queue_only
            self.no_saving = show_queue_only
            self.task = cc_task.task_factory(self.basetable, self.serverpk)
        else:
            # HL7Message(msg_id)
            pls.db.fetch_object_from_db_by_pk(self, HL7Message.TABLENAME,
                                              HL7Message.FIELDS, msg_id)
            self.hl7run = HL7Run(self.run_id)

    def valid(self) -> bool:
        """Checks for internal validity; returns Boolean."""
        if not self.recipient_def or not self.recipient_def.valid:
            return False
        if not self.basetable or self.serverpk is None:
            return False
        if not self.task:
            return False
        anonymous_ok = (self.recipient_def.using_file() and
                        self.recipient_def.include_anonymous)
        task_is_anonymous = self.task.is_anonymous
        if task_is_anonymous and not anonymous_ok:
            return False
        # After this point, all anonymous tasks must be OK. So:
        task_has_primary_id = self.task.get_patient_idnum(
            self.recipient_def.primary_idnum) is not None
        if not task_is_anonymous and not task_has_primary_id:
            return False
        return True

    def save(self) -> None:
        """Writes to database, unless saving is prohibited."""
        if self.no_saving:
            return
        if self.basetable is None or self.serverpk is None:
            return
        is_new_record = self.msg_id is None
        pls.db.save_object_to_db(self, HL7Message.TABLENAME,
                                 HL7Message.FIELDS, is_new_record)

    def divert_to_file(self, f: typing.io.TextIO) -> None:
        """Write an HL7 message to a file."""
        infomsg = (
            "OUTBOUND MESSAGE DIVERTED FROM RECIPIENT {} AT {}\n".format(
                self.recipient_def.recipient,
                cc_dt.format_datetime(self.sent_at_utc, DATEFORMAT.ISO8601)
            )
        )
        print(infomsg, file=f)
        print(str(self.msg), file=f)
        print("\n", file=f)
        log.debug(infomsg)
        self.host = self.recipient_def.divert_to_file
        if self.recipient_def.treat_diverted_as_sent:
            self.success = True

    def send(self,
             queue_file: typing.io.TextIO = None,
             divert_file: typing.io.TextIO = None) -> Tuple[bool, bool]:
        """Send an outbound HL7/file message, by the appropriate method."""
        # returns: tried, succeeded
        if not self.valid():
            return False, False

        if self.show_queue_only:
            print("{},{},{},{},{}".format(
                self.recipient_def.recipient,
                self.recipient_def.type,
                self.basetable,
                self.serverpk,
                self.task.when_created
            ), file=queue_file)
            return False, True

        if not self.hl7run:
            return True, False

        self.save()  # creates self.msg_id
        now = cc_dt.get_now_localtz()
        self.sent_at_utc = cc_dt.convert_datetime_to_utc_notz(now)

        if self.recipient_def.using_hl7():
            self.make_hl7_message(now)  # will write its own error msg/flags
            if self.recipient_def.divert_to_file:
                self.divert_to_file(divert_file)
            else:
                self.transmit_hl7()
        elif self.recipient_def.using_file():
            self.send_to_filestore()
        else:
            raise AssertionError("HL7Message.send: invalid recipient_def.type")
        self.save()

        log.debug(
            "HL7Message.send: recipient={}, basetable={}, "
            "serverpk={}".format(
                self.recipient_def.recipient,
                self.basetable,
                self.serverpk
            )
        )
        return True, self.success

    def send_to_filestore(self) -> None:
        """Send a file to a filestore."""
        self.filename = self.recipient_def.get_filename(
            is_anonymous=self.task.is_anonymous,
            surname=self.task.get_patient_surname(),
            forename=self.task.get_patient_forename(),
            dob=self.task.get_patient_dob(),
            sex=self.task.get_patient_sex(),
            idnums=self.task.get_patient_idnum_array(),
            idshortdescs=self.task.get_patient_idshortdesc_array(),
            creation_datetime=self.task.get_creation_datetime(),
            basetable=self.basetable,
            serverpk=self.serverpk,
        )

        filename = self.filename
        directory = os.path.dirname(filename)
        task = self.task
        task_format = self.recipient_def.task_format
        allow_overwrite = self.recipient_def.overwrite_files

        if task_format == VALUE.OUTPUTTYPE_PDF:
            data = task.get_pdf()
        elif task_format == VALUE.OUTPUTTYPE_HTML:
            data = task.get_html()
        elif task_format == VALUE.OUTPUTTYPE_XML:
            data = task.get_xml()
        else:
            raise AssertionError("write_to_filestore_file: bug")

        if not allow_overwrite and os.path.isfile(filename):
            self.failure_reason = "File already exists"
            return

        if self.recipient_def.make_directory:
            try:
                make_sure_path_exists(directory)
            except Exception as e:
                self.failure_reason = "Couldn't make directory {} ({})".format(
                    directory, e)
                return

        try:
            if task_format == VALUE.OUTPUTTYPE_PDF:
                # binary for PDF
                with open(filename, mode="wb") as f:
                    f.write(data)
            else:
                # UTF-8 for HTML, XML
                with codecs.open(filename, mode="w", encoding="utf8") as f:
                    f.write(data)
        except Exception as e:
            self.failure_reason = "Failed to open or write file: {}".format(e)
            return

        # RiO metadata too?
        if self.recipient_def.rio_metadata:
            # No spaces in filename
            self.rio_metadata_filename = cc_filename.change_filename_ext(
                self.filename, ".metadata").replace(" ", "")
            self.rio_metadata_filename = self.rio_metadata_filename
            metadata = task.get_rio_metadata(
                self.recipient_def.rio_idnum,
                self.recipient_def.rio_uploading_user,
                self.recipient_def.rio_document_type
            )
            try:
                dos_newline = "\r\n"
                # ... Servelec say CR = "\r", but DOS is \r\n.
                with codecs.open(self.rio_metadata_filename, mode="w",
                                 encoding="ascii") as f:
                    # codecs.open() means that file writing is in binary mode,
                    # so newline conversion has to be manual:
                    f.write(metadata.replace("\n", dos_newline))
                # UTF-8 is NOT supported by RiO for metadata.
            except Exception as e:
                self.failure_reason = ("Failed to open or write RiO metadata "
                                       "file: {}".format(e))
                return

        self.success = True

    def make_hl7_message(self, now: datetime.datetime) -> None:
        """Stores HL7 message in self.msg.

        May also store it in self.message (which is saved to the database), if
        we're saving HL7 messages.
        """
        # http://python-hl7.readthedocs.org/en/latest/index.html

        msh_segment = make_msh_segment(
            message_datetime=now,
            message_control_id=str(self.msg_id)
        )
        pid_segment = self.task.get_patient_hl7_pid_segment(self.recipient_def)
        other_segments = self.task.get_hl7_data_segments(self.recipient_def)

        # ---------------------------------------------------------------------
        # Whole message
        # ---------------------------------------------------------------------
        segments = [msh_segment, pid_segment] + other_segments
        self.msg = hl7.Message(SEGMENT_SEPARATOR, segments)
        if self.recipient_def.keep_message:
            self.message = str(self.msg)

    def transmit_hl7(self) -> None:
        """Sends HL7 message over TCP/IP."""
        # Default MLLP/HL7 port is 2575
        # ... MLLP = minimum lower layer protocol
        # ... http://www.cleo.com/support/byproduct/lexicom/usersguide/mllp_configuration.htm  # noqa
        # ... http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=hl7  # noqa
        # Essentially just a TCP socket with a minimal wrapper:
        #   http://stackoverflow.com/questions/11126918

        self.host = self.recipient_def.host
        self.port = self.recipient_def.port
        self.success = False

        # http://python-hl7.readthedocs.org/en/latest/api.html
        # ... but we've modified that
        try:
            with MLLPTimeoutClient(self.recipient_def.host,
                                   self.recipient_def.port,
                                   self.recipient_def.network_timeout_ms) \
                    as client:
                server_replied, reply = client.send_message(self.msg)
        except socket.timeout:
            self.failure_reason = "Failed to send message via MLLP: timeout"
            return
        except Exception as e:
            self.failure_reason = "Failed to send message via MLLP: {}".format(
                str(e))
            return

        if not server_replied:
            self.failure_reason = "No response from server"
            return
        self.reply_at_utc = cc_dt.get_now_utc_notz()
        if self.recipient_def.keep_reply:
            self.reply = reply
        try:
            replymsg = hl7.parse(reply)
        except Exception as e:
            self.failure_reason = "Malformed reply: {}".format(e)
            return

        self.success, self.failure_reason = msg_is_successful_ack(replymsg)

    @classmethod
    def get_html_header_row(cls,
                            showmessage: bool = False,
                            showreply: bool = False) -> str:
        """Returns HTML table header row for this class."""
        html = "<tr>"
        for fs in cls.FIELDSPECS:
            if fs["name"] == "message" and not showmessage:
                continue
            if fs["name"] == "reply" and not showreply:
                continue
            html += "<th>{}</th>".format(fs["name"])
        html += "</tr>\n"
        return html

    def get_html_data_row(self,
                          showmessage: bool = False,
                          showreply: bool = False) -> bool:
        """Returns HTML table data row for this instance."""
        html = "<tr>"
        for fs in self.FIELDSPECS:
            name = fs["name"]
            if name == "message" and not showmessage:
                continue
            if name == "reply" and not showreply:
                continue
            value = ws.webify(getattr(self, name))
            if name == "serverpk":
                contents = "<a href={}>{}</a>".format(
                    cc_task.get_url_task_html(self.basetable, self.serverpk),
                    value
                )
            elif name == "run_id":
                contents = "<a href={}>{}</a>".format(
                    get_url_hl7_run(value),
                    value
                )
            else:
                contents = str(value)
            html += "<td>{}</td>".format(contents)
        html += "</tr>\n"
        return html

# =============================================================================
# MLLPTimeoutClient
# =============================================================================
# Modification of MLLPClient from python-hl7, to allow timeouts and failure.

SB = '\x0b'  # <SB>, vertical tab
EB = '\x1c'  # <EB>, file separator
CR = '\x0d'  # <CR>, \r
FF = '\x0c'  # <FF>, new page form feed

RECV_BUFFER = 4096


class MLLPTimeoutClient(object):
    """Class for MLLP TCP/IP transmission that implements timeouts."""

    def __init__(self, host: str, port: int, timeout_ms: int = None) -> None:
        """Creates MLLP client and opens socket."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        timeout_s = float(timeout_ms) / float(1000) \
            if timeout_ms is not None else None
        self.socket.settimeout(timeout_s)
        self.socket.connect((host, port))

    def __enter__(self):
        """For use with "with" statement."""
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, traceback):
        """For use with "with" statement."""
        self.close()

    def close(self):
        """Release the socket connection"""
        self.socket.close()

    def send_message(self, message: Union[str, hl7.Message]) \
            -> Tuple[bool, Optional[str]]:
        """Wraps a str, unicode, or :py:class:`hl7.Message` in a MLLP container
        and send the message to the server
        """
        if isinstance(message, hl7.Message):
            message = str(message)
        # wrap in MLLP message container
        data = SB + message + CR + EB + CR
        # ... the CR immediately after the message is my addition, because
        # HL7 Inspector otherwise says: "Warning: last segment have no segment
        # termination char 0x0d !" (sic).
        return self.send(data.encode('utf-8'))

    def send(self, data: bytes) -> Tuple[bool, Optional[str]]:
        """Low-level, direct access to the socket.send (data must be already
        wrapped in an MLLP container).  Blocks until the server returns.
        """
        # upload the data
        self.socket.send(data)
        # wait for the ACK/NACK
        try:
            ack_msg = self.socket.recv(RECV_BUFFER)
            return True, ack_msg
        except socket.timeout:
            return False, None


# =============================================================================
# Main functions
# =============================================================================

def send_all_pending_hl7_messages(show_queue_only: bool = False) -> None:
    """Sends all pending HL7 or file messages.

    Obtains a file lock, then iterates through all recipients.
    """
    queue_stdout = sys.stdout
    if not pls.HL7_LOCKFILE:
        log.error("send_all_pending_hl7_messages: No HL7_LOCKFILE specified"
                  " in config; can't proceed")
        return
    # On UNIX, lockfile uses LinkLockFile
    # https://github.com/smontanaro/pylockfile/blob/master/lockfile/
    #         linklockfile.py
    lock = lockfile.FileLock(pls.HL7_LOCKFILE)
    if lock.is_locked():
        log.warning("send_all_pending_hl7_messages: locked by another"
                    " process; aborting")
        return
    with lock:
        if show_queue_only:
            print("recipient,basetable,_pk,when_created", file=queue_stdout)
        for recipient_def in pls.HL7_RECIPIENT_DEFS:
            send_pending_hl7_messages(recipient_def, show_queue_only,
                                      queue_stdout)
        pls.db.commit()  # HL7 commit (prior to releasing file lock)


def send_pending_hl7_messages(recipient_def: RecipientDefinition,
                              show_queue_only: bool,
                              queue_stdout: typing.io.TextIO) -> None:
    """Pings recipient if necessary, opens any files required, creates an
    HL7Run, then sends all pending HL7/file messages to a specific
    recipient."""
    # Called once per recipient.
    log.debug("send_pending_hl7_messages: " + str(recipient_def))

    use_ping = (recipient_def.using_hl7() and
                not recipient_def.divert_to_file and
                recipient_def.ping_first)
    if use_ping:
        # No HL7 PING method yet. Proposal is:
        # http://hl7tsc.org/wiki/index.php?title=FTSD-ConCalls-20081028
        # So use TCP/IP ping.
        try:
            timeout_s = min(recipient_def.network_timeout_ms // 1000, 1)
            if not ping(hostname=recipient_def.host,
                        timeout_s=timeout_s):
                log.error("Failed to ping {}".format(recipient_def.host))
                return
        except socket.error:
            log.error("Socket error trying to ping {}; likely need to "
                      "run as root".format(recipient_def.host))
            return

    if show_queue_only:
        hl7run = None
    else:
        hl7run = HL7Run(recipient_def)

    # Do things, but with safe file closure if anything goes wrong
    use_divert = (recipient_def.using_hl7() and recipient_def.divert_to_file)
    if use_divert:
        try:
            with codecs.open(recipient_def.divert_to_file, "a", "utf8") as f:
                send_pending_hl7_messages_2(recipient_def, show_queue_only,
                                            queue_stdout, hl7run, f)
        except Exception as e:
            log.error("Couldn't open file {} for appending: {}".format(
                recipient_def.divert_to_file, e))
            return
    else:
        send_pending_hl7_messages_2(recipient_def, show_queue_only,
                                    queue_stdout, hl7run, None)


def send_pending_hl7_messages_2(
        recipient_def: RecipientDefinition,
        show_queue_only: bool,
        queue_stdout: typing.io.TextIO,
        hl7run: HL7Run,
        divert_file: Optional[typing.io.TextIO]) -> None:
    """Sends all pending HL7/file messages to a specific recipient."""
    # Also called once per recipient, but after diversion files safely
    # opened and recipient pinged successfully (if desired).
    n_hl7_sent = 0
    n_hl7_successful = 0
    n_file_sent = 0
    n_file_successful = 0
    files_exported = []
    basetables = cc_task.get_base_tables(recipient_def.include_anonymous)
    for bt in basetables:
        # Current records...
        args = []
        sql = """
            SELECT _pk
            FROM {basetable}
            WHERE _current
        """.format(basetable=bt)

        # Having an appropriate date...
        # Best to use when_created, or _when_added_batch_utc?
        # The former. Because nobody would want a system that would miss
        # amendments to records, and records are defined (date-wise) by
        # when_created.
        if recipient_def.start_date:
            sql += """
                AND {} >= ?
            """.format(
                cc_db.mysql_select_utc_date_field_from_iso8601_field(
                    "when_created")
            )
            args.append(recipient_def.start_date)
        if recipient_def.end_date:
            sql += """
                AND {} <= ?
            """.format(
                cc_db.mysql_select_utc_date_field_from_iso8601_field(
                    "when_created")
            )
            args.append(recipient_def.end_date)

        # That haven't already had a successful HL7 message sent to this
        # server...
        sql += """
            AND _pk NOT IN (
                SELECT m.serverpk
                FROM {hl7table} m
                INNER JOIN {hl7runtable} r
                ON m.run_id = r.run_id
                WHERE m.basetable = ?
                AND r.recipient = ?
                AND m.success
                AND (NOT m.cancelled OR m.cancelled IS NULL)
            )
        """.format(hl7table=HL7Message.TABLENAME, hl7runtable=HL7Run.TABLENAME)
        args.append(bt)
        args.append(recipient_def.recipient)
        # http://explainextended.com/2009/09/18/not-in-vs-not-exists-vs-left-join-is-null-mysql/  # noqa

        # That are finalized (i.e. aren't still on the tablet and potentially
        # subject to modification)?
        if recipient_def.finalized_only:
            sql += """
                AND _era <> ?
            """
            args.append(ERA_NOW)

        # OK. Fetch PKs and send information.
        # log.debug("{}, args={}".format(sql, args))
        pklist = pls.db.fetchallfirstvalues(sql, *args)
        for serverpk in pklist:
            msg = HL7Message(basetable=bt,
                             serverpk=serverpk,
                             hl7run=hl7run,
                             recipient_def=recipient_def,
                             show_queue_only=show_queue_only)
            tried, succeeded = msg.send(queue_stdout, divert_file)
            if not tried:
                continue
            if recipient_def.using_hl7():
                n_hl7_sent += 1
                n_hl7_successful += 1 if succeeded else 0
            else:
                n_file_sent += 1
                n_file_successful += 1 if succeeded else 0
                if succeeded:
                    files_exported.append(msg.filename)
                    if msg.rio_metadata_filename:
                        files_exported.append(msg.rio_metadata_filename)

    if hl7run:
        hl7run.call_script(files_exported)
        hl7run.finish()
    log.info("{} HL7 messages sent, {} successful, {} failed".format(
        n_hl7_sent, n_hl7_successful, n_hl7_sent - n_hl7_successful))
    log.info("{} files sent, {} successful, {} failed".format(
        n_file_sent, n_file_successful, n_file_sent - n_file_successful))


# =============================================================================
# File-handling functions
# =============================================================================

def make_sure_path_exists(path: str) -> None:
    """Creates a directory/directories if the path doesn't already exist."""
    # http://stackoverflow.com/questions/273192
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


# =============================================================================
# URLs
# =============================================================================

def get_url_hl7_run(run_id: Any) -> str:
    """URL to view an HL7Run instance."""
    url = cc_html.get_generic_action_url(ACTION.VIEW_HL7_RUN)
    url += cc_html.get_url_field_value_pair(PARAM.HL7RUNID, run_id)
    return url


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests() -> None:
    """Unit tests for cc_hl7 module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS (UNIT TESTING ONLY)
    # -------------------------------------------------------------------------
    import tasks.phq9 as phq9

    # skip: send_all_pending_hl7_messages
    # skip: send_pending_hl7_messages

    current_pks = pls.db.fetchallfirstvalues(
        "SELECT _pk FROM {} WHERE _current".format(phq9.Phq9.tablename)
    )
    pk = current_pks[0] if current_pks else None
    task = phq9.Phq9(pk)
    pitlist = [
        cc_namedtuples.PatientIdentifierTuple(
            id="1", id_type="TT", assigning_authority="AA")
    ]
    now = cc_dt.get_now_localtz()

    unit_test_ignore("", get_mod11_checkdigit, "12345")
    unit_test_ignore("", get_mod11_checkdigit, "badnumber")
    unit_test_ignore("", get_mod11_checkdigit, None)
    unit_test_ignore("", make_msh_segment, now, "control_id")
    unit_test_ignore("", make_pid_segment, "fname", "sname", now, "sex",
                     "addr", pitlist)
    unit_test_ignore("", make_obr_segment, task)
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_PDF,
                     "obs_id", now, "responsible_observer")
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_HTML,
                     "obs_id", now, "responsible_observer")
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_XML,
                     "obs_id", now, "responsible_observer",
                     xml_field_comments=True)
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_XML,
                     "obs_id", now, "responsible_observer",
                     xml_field_comments=False)
    unit_test_ignore("", escape_hl7_text, "blahblah")
    # not yet tested: HL7Message class
    # not yet tested: MLLPTimeoutClient class