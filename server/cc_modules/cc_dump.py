#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

import ConfigParser
import io
import subprocess
import zipfile

from cc_audit import audit
import cc_blob
from cc_constants import CONFIG_FILE_MAIN_SECTION
import cc_patient
from cc_pls import pls
import cc_task

# =============================================================================
# Constants
# =============================================================================

NOTHING_VALID_SPECIFIED = "No valid tables or views specified"
POSSIBLE_SYSTEM_TABLES = [  # always exist
    cc_blob.Blob.TABLENAME,
    cc_patient.Patient.TABLENAME,
]
POSSIBLE_SYSTEM_VIEWS = [
]


# =============================================================================
# Ancillary functions
# =============================================================================

def get_possible_task_tables_views():
    """Returns (tables, views) pertaining to tasks."""
    tables = []
    views = []
    for cls in cc_task.Task.__subclasses__():
        (tasktables, taskviews) = cls.get_all_table_and_view_names()
        tables.extend(tasktables)
        views.extend(taskviews)
    return (tables, views)


def get_permitted_tables_and_views():
    """Returns list of tables/views suitable for downloading."""
    tables_that_exist = pls.db.get_all_table_names()
    (tasktables, taskviews) = get_possible_task_tables_views()
    return list(set(tables_that_exist).intersection(POSSIBLE_SYSTEM_TABLES +
                                                    POSSIBLE_SYSTEM_VIEWS +
                                                    tasktables +
                                                    taskviews))


def get_permitted_tables_views_sorted_labelled():
    """Returns sorted list of tables/views suitable for downloading.

    Each list element is a dictionary with attributes:
        name: name of table/view
        view: Boolean
    """
    (tasktables, taskviews) = get_possible_task_tables_views()
    tables_that_exist = pls.db.get_all_table_names()
    valid_system_tables = list(set(tables_that_exist).intersection(
        POSSIBLE_SYSTEM_TABLES))
    valid_system_views = list(set(tables_that_exist).intersection(
        POSSIBLE_SYSTEM_VIEWS))
    valid_tasktables = list(set(tables_that_exist).intersection(tasktables))
    valid_taskviews = list(set(tables_that_exist).intersection(taskviews))

    system_list = (
        [{"view": False, "name": x} for x in valid_system_tables]
        + [{"view": True, "name": x} for x in valid_system_views]
    )
    task_list = (
        [{"view": False, "name": x} for x in valid_tasktables]
        + [{"view": True, "name": x} for x in valid_taskviews]
    )
    return (
        sorted(system_list, key=lambda k: k["name"])
        + sorted(task_list, key=lambda k: k["name"])
    )
    # ... makes system tables be at one end of the list for visibility


def validate_table_list(tables):
    """Returns the list supplied, minus any invalid tables/views."""
    return sorted(list(
        set(tables).intersection(get_permitted_tables_and_views())
    ))


def validate_single_table(table):
    """Returns the table name supplied, or None if it's not valid."""
    tl = list(set([table]).intersection(get_permitted_tables_and_views()))
    if not tl:
        return None
    return tl[0]


# =============================================================================
# Providing user with database dump output in various formats
# =============================================================================

def get_database_dump_as_sql(tables=[]):
    """Returns a database dump of all the tables requested, in SQL format."""
    tables = validate_table_list(tables)
    if not tables:
        return NOTHING_VALID_SPECIFIED

    # We'll need to re-fetch the database password,
    # since we don't store it (for security reasons).
    config = ConfigParser.ConfigParser()
    config.read(pls.CAMCOPS_CONFIG_FILE)

    # -------------------------------------------------------------------------
    # SECURITY: from this point onwards, consider the possibility of a
    # password leaking via a debugging exception handler
    # -------------------------------------------------------------------------
    try:
        DB_PASSWORD = config.get(CONFIG_FILE_MAIN_SECTION, "DB_PASSWORD")
    except Exception as e:  # deliberately conceal details for security
        raise RuntimeError(
            "Problem reading DB_PASSWORD from config: {}".format(e))
    if DB_PASSWORD is None:
        raise RuntimeError("No database password specified")
        # OK from a security perspective: if there's no password, there's no
        # password to leak via a debugging exception handler

    # Database:
    try:
        audit("dump as SQL: " + " ".join(tables))
        return subprocess.check_output([
            pls.MYSQLDUMP,
            "-h", pls.DB_SERVER,  # rather than --host=X
            "-P", str(pls.DB_PORT),  # rather than --port=X
            "-u", pls.DB_USER,  # rather than --user=X
            "-p{}".format(DB_PASSWORD),
            # neither -pPASSWORD nor --password=PASSWORD accept spaces
            "--opt",
            "--hex-blob",
            "--default-character-set=utf8",
            pls.DB_NAME,
        ] + tables).decode('utf8')
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem opening or reading from database; "
                           "details concealed for security reasons")
    finally:
        # Executed whether an exception is raised or not.
        DB_PASSWORD = None


def get_query_as_tsv(sql):
    """Returns the result of the SQL query supplied, in TSV format."""
    # Security considerations as above.
    config = ConfigParser.ConfigParser()
    config.read(pls.CAMCOPS_CONFIG_FILE)
    try:
        DB_PASSWORD = config.get(CONFIG_FILE_MAIN_SECTION, "DB_PASSWORD")
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem reading DB_PASSWORD from config")
    if DB_PASSWORD is None:
        raise RuntimeError("No database password specified")
    try:
        return subprocess.check_output([
            pls.MYSQL,
            "-h", pls.DB_SERVER,
            # ... rather than --host=X; the subprocess call handles arguments
            # with spaces much better (e.g. escaping for us)
            "-P", str(pls.DB_PORT),  # rather than --port=X
            "-u", pls.DB_USER,  # rather than --user=X
            "-p{}".format(DB_PASSWORD),
            # ... neither -pPASSWORD nor --password=PASSWORD accept spaces
            "-D", pls.DB_NAME,  # rather than --database=X
            "-e", sql,
            # ... rather than --execute="X"; this is the real reason we use
            # this format, so that subprocess can escape the query
            # appropriately for us
            "--batch",
            # ... create TSV output (will escape actual tabs, unless --raw also
            # specified); note that NULLs come out as the string literal NULL,
            # which is not ideal.
            "--default-character-set=utf8",
        ]).decode('utf8')
        # This will throw an error if BLOBs are used (the binary will screw up
        # the UTF8 decoding).
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem opening or reading from database; "
                           "details concealed for security reasons")
    finally:
        # Executed whether an exception is raised or not.
        DB_PASSWORD = None


def get_view_data_as_tsv(view, prevalidated=False, audit_individually=True):
    """Returns the data from the view specified, in TSV format."""
    # Views need special handling: mysqldump will provide the view-generating
    # SQL, not the contents. If the output is saved as .XLS, Excel will open it
    # without prompting for conversion.
    if not prevalidated:
        view = validate_single_table(view)
        if not view:
            return "Invalid table or view"
    # Special blob handling...
    if view == cc_blob.Blob.TABLENAME:
        query = (
            "SELECT "
            + ",".join(cc_blob.Blob.FIELDS_WITHOUT_BLOB)
            + ",HEX(theblob) FROM " + cc_blob.Blob.TABLENAME
        )
    else:
        query = "SELECT * FROM " + view
    if audit_individually:
        audit("dump as TSV: " + view)
    return get_query_as_tsv(query)


def get_multiple_views_data_as_tsv_zip(tables):
    """Returns the data from multiple views, as multiple TSV files in a ZIP."""
    tables = validate_table_list(tables)
    if not tables:
        return None
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")
    for t in tables:
        result = get_view_data_as_tsv(t, prevalidated=True,
                                      audit_individually=False)
        z.writestr(t + ".tsv", result.encode("utf-8"))
    z.close()
    audit("dump as TSV ZIP: " + " ".join(tables))
    return memfile.getvalue()


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests():
    """Unit tests for the cc_dump module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    from cc_unittest import unit_test_ignore

    unit_test_ignore("", get_possible_task_tables_views)
    unit_test_ignore("", get_permitted_tables_and_views)
    unit_test_ignore("", get_permitted_tables_views_sorted_labelled)
    unit_test_ignore("", validate_table_list, [None, "phq9",
                                               "nonexistent_table"])
    unit_test_ignore("", validate_single_table, None)
    unit_test_ignore("", validate_single_table, "phq9")
    unit_test_ignore("", validate_single_table, "nonexistent_table")
    unit_test_ignore("", get_database_dump_as_sql)
    # get_query_as_tsv tested indirectly
    unit_test_ignore("", get_view_data_as_tsv, "phq9")
    unit_test_ignore("", get_view_data_as_tsv, "nonexistent_table")
    unit_test_ignore("", get_multiple_views_data_as_tsv_zip,
                     [None, "phq9", "nonexistent_table"])