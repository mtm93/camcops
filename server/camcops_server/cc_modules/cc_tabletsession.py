#!/usr/bin/env python
# camcops_server/cc_modules/cc_tabletsession.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

import logging
from typing import Optional, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter

from .cc_client_api_core import fail_user_error, TabletParam
from .cc_device import Device
from .cc_user import User
from .cc_version import (
    FIRST_TABLET_VER_WITH_SEPARATE_IDNUM_TABLE,
    FIRST_TABLET_VER_WITHOUT_IDDESC_IN_PT_TABLE,
    make_version,
    MINIMUM_TABLET_VERSION,
)

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


class TabletSession(object):
    def __init__(self, req: "CamcopsRequest") -> None:
        # Read key things
        self.req = req
        post = req.POST
        self.operation = post.getone(TabletParam.OPERATION)  # type: str
        self.device_name = post.getone(TabletParam.DEVICE)  # type: str
        self.username = post.getone(TabletParam.USER)  # type: str
        self.password = post.getone(TabletParam.PASSWORD)  # type: str
        self.session_id = req.get_int_param(TabletParam.SESSION_ID)
        self.session_token = post.getone(TabletParam.SESSION_TOKEN)  # type: str  # noqa
        self.tablet_version_str = post.getone(TabletParam.CAMCOPS_VERSION)  # type: str  # noqa
        self.tablet_version_ver = make_version(self.tablet_version_str)
        # Look up device and user
        dbsession = req.dbsession
        self._device_obj = Device.get_device_by_name(dbsession,
                                                     self.device_name)
        self._user_obj = User.get_user_by_name(dbsession, self.username)

        # Ensure table version is OK
        if self.tablet_version_ver < MINIMUM_TABLET_VERSION:
            fail_user_error(
                "Tablet CamCOPS version too old: is {v}, need {r}".format(
                    v=self.tablet_version_str,
                    r=MINIMUM_TABLET_VERSION))
        # Other version things
        self.cope_with_deleted_patient_descriptors = (
            self.tablet_version_ver <
            FIRST_TABLET_VER_WITHOUT_IDDESC_IN_PT_TABLE)
        self.cope_with_old_idnums = (
            self.tablet_version_ver <
            FIRST_TABLET_VER_WITH_SEPARATE_IDNUM_TABLE)

        # Report
        log.info("Incoming connection from IP={i}, port={p}, device_name={dn},"
                 " device_id={di}, user={u}, operation={o}",
                 i=req.remote_addr,
                 p=req.remote_port,
                 dn=self.device_name,
                 di=self.device_id,
                 u=self.username,
                 o=self.operation)

    @property
    def device_id(self) -> Optional[int]:
        if not self._device_obj:
            return None
        return self._device_obj.get_id()

    @property
    def user_id(self) -> Optional[int]:
        if self._user_obj is None:
            return None
        return self._user_obj.get_id()

    def is_device_registered(self) -> bool:
        return self._device_obj is not None

    def reload_device(self):
        self._device_obj = Device.get_device_by_name(self.req.dbsession,
                                                     self.device_name)

    def ensure_device_registered(self) -> None:
        """
        Ensure the device is registered. Raises UserErrorException on failure.
        """
        if not self.is_device_registered():
            fail_user_error("Unregistered device")

    def ensure_valid_device_and_user_for_uploading(self) -> None:
        """
        Ensure the device/username/password combination is valid for uploading.
        Raises UserErrorException on failure.
        """
        if not self.req.user or not self.req.user.may_upload:
            fail_user_error(
                "Invalid username/password, or user not authorized to upload, "
                "or no upload group set")
        # Username/password combination found and is valid. Now check device.
        self.ensure_device_registered()

    def ensure_valid_user_for_device_registration(self) -> None:
        """
        Ensure the username/password combination is valid for device
        registration. Raises UserErrorException on failure.
        """
        if not self.req.user or not self.req.user.may_register_devices:
            fail_user_error("Invalid username/password, or user not "
                            "authorized to register devices")

    def set_session_id_token(self, session_id: int,
                             session_token: str) -> None:
        """
        Sets the session ID and token.
        Typical situation:
            - TabletSession created; may or may not have an ID/token as part
              of the POST request
            - CamcopsRequest translates that into a server-side session
            - If one wasn't found and needs to be created, we write back
              the values here.
        """
        self.session_id = session_id
        self.session_token = session_token
