#!/usr/bin/env python
# camcops_server/webview.py

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

Quick tutorial on Pyramid views:

-   The configurator registers routes, and routes have URLs associated with
    them. Those URLs can be templatized, e.g. to accept numerical parameters.
    The configurator associates view callables ("views" for short) with routes,
    and one method for doing that is an automatic scan via Venusian for views
    decorated with @view_config().

-   All views take a Request object and return a Response or raise an exception
    that Pyramid will translate into a Response.

-   Having matched a route, Pyramid uses its "view lookup" process to choose
    one from potentially several views. For example, a single route might be
    associated with:

        @view_config(route_name="myroute")
        def myroute_default(req: Request) -> Response:
            pass

        @view_config(route_name="myroute", method="POST")
        def myroute_post(req: Request) -> Response:
            pass

    In this example, POST requests will go to the second; everything else will
    go to the first. Pyramid's view lookup rule is essentially: if multiple
    views match, choose the one with the most specifiers.

-   Specifiers include:

        route_name=ROUTENAME

            the route

        request_method="POST"

            requires HTTP GET, POST, etc.

        request_param="XXX"

            ... requires the presence of a GET/POST variable with this name in
            the request.params dictionary

        request_param="XXX=YYY"

            ... requires the presence of a GET/POST variable called XXX whose
            value is YYY, in the request.params dictionary

        match_param="XXX=YYY"

            .. requires the presence of this key/value pair in
            request.matchdict, which contains parameters from the URL

    https://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_view  # noqa

-   Getting parameters

        request.params

            ... parameters from HTTP GET or POST, including both the query
            string (as in http://somewhere/path?key=value) and the body (e.g.
            POST).

        request.matchdict

            ... parameters from the URL, via URL dispatch; see
            https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#urldispatch-chapter  # noqa

-   Regarding rendering:

    There might be some simplicity benefits from converting to a template
    system like Mako. On the downside, that would entail a bit more work;
    likely a minor performance hit (relative to plain Python string rendering);
    and a loss of type checking. The type checking is also why we prefer:

        html = " ... {param_blah} ...".format(param_blah=PARAM.BLAH)

    to

        html = " ... {PARAM.BLAH} ...".format(PARAM=PARAM)

    as in the first situation, PyCharm will check that "BLAH" is present in
    "PARAM", and in the second it won't. Automatic checking is worth a lot.

"""

import cgi
import codecs
import collections
import io
import logging
import typing
from typing import Any, Dict, Iterable, List, Optional, Type, Union
import zipfile

from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import WSGI_TUPLE_TYPE
from cardinal_pythonlib.sqlalchemy.dialect import get_dialect_name
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from cardinal_pythonlib.sqlalchemy.orm_query import CountStarSpecializedQuery
from cardinal_pythonlib.sqlalchemy.session import get_engine_from_session
from deform.exception import ValidationFailure
from pendulum import Pendulum
import pyramid.httpexceptions as exc
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
)
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.security import Authenticated, NO_PERMISSION_REQUIRED
import pygments
import pygments.lexers
import pygments.lexers.sql
import pygments.lexers.web
import pygments.formatters
from sqlalchemy.sql.expression import desc, or_

from .cc_audit import audit, AuditEntry
from .cc_constants import (
    ACTION,
    CAMCOPS_URL,
    DateFormat,
    MINIMUM_PASSWORD_LENGTH,
    PARAM,
    VALUE,
)
from .cc_blob import Blob
from .cc_convert import get_tsv_header_from_dict, get_tsv_line_from_dict
from camcops_server.cc_modules import cc_db
from .cc_db import GenericTabletRecordMixin
from .cc_device import (
    Device,
    get_device_filter_dropdown,
)
from .cc_dt import (
    get_now_localtz,
    format_datetime,
)
from .cc_dump import (
    get_database_dump_as_sql,
    get_multiple_views_data_as_tsv_zip,
    get_permitted_tables_views_sorted_labelled,
    NOTHING_VALID_SPECIFIED,
)
from .cc_forms import (
    AddGroupForm,
    AddUserForm,
    AuditTrailForm,
    ChangeOtherPasswordForm,
    ChangeOwnPasswordForm,
    ChooseTrackerForm,
    DEFAULT_ROWS_PER_PAGE,
    DeleteGroupForm,
    DeleteUserForm,
    DIALECT_CHOICES,
    EditGroupForm,
    EditUserForm,
    get_head_form_html,
    HL7MessageLogForm,
    HL7RunLogForm,
    LoginForm,
    OfferTermsForm,
    RefreshTasksForm,
    SetUserUploadGroupForm,
    EditTaskFilterForm,
    TasksPerPageForm,
    ViewDdlForm,
)
from .cc_group import Group
from .cc_hl7 import HL7Message, HL7Run
from .cc_html import (
    get_generic_action_url,
    get_url_main_menu,
)
from .cc_patient import Patient
from .cc_plot import ccplot_no_op
from .cc_policy import (
    get_finalize_id_policy_principal_numeric_id,
    get_upload_id_policy_principal_numeric_id,
    id_policies_valid,
)
from .cc_pyramid import (
    CamcopsPage,
    Dialect,
    FormAction,
    PageUrl,
    PdfResponse,
    Permission,
    Routes,
    SqlalchemyOrmPage,
    ViewArg,
    ViewParam,
    XmlResponse,
)
from .cc_report import get_report_instance
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_simpleobjects import IdNumDefinition
from .cc_specialnote import SpecialNote
from .cc_sqlalchemy import get_all_ddl
from .cc_storedvar import DeviceStoredVar
from .cc_task import (
    gen_tasks_for_patient_deletion,
    gen_tasks_live_on_tablet,
    gen_tasks_using_patient,
    Task,
)
from .cc_taskfactory import (
    task_factory,
    TaskFilter,
    TaskCollection,
    TaskSortMethod,
)
from .cc_taskfilter import (
    task_classes_from_table_names,
    TaskClassSortMethod,
)
from .cc_tracker import ClinicalTextView, Tracker
from .cc_unittest import unit_test_ignore
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User
from .cc_version import CAMCOPS_SERVER_VERSION

log = BraceStyleAdapter(logging.getLogger(__name__))
ccplot_no_op()

# =============================================================================
# Constants
# =============================================================================

ALLOWED_TASK_VIEW_TYPES = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                           ViewArg.XML]
ALLOWED_TRACKER_VIEW_TYPE = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                             ViewArg.XML]
AFFECTED_TASKS_HTML = "<h1>Affected tasks:</h1>"
CANNOT_DUMP = "User not authorized to dump data/regenerate summary tables."
CANNOT_REPORT = "User not authorized to run reports."
CAN_ONLY_CHANGE_OWN_PASSWORD = "You can only change your own password!"
TASK_FAIL_MSG = "Task not found or user not authorized."
NOT_AUTHORIZED_MSG = "User not authorized."
NO_INTROSPECTION_MSG = "Introspection not permitted"
INTROSPECTION_INVALID_FILE_MSG = "Invalid file for introspection"
INTROSPECTION_FAILED_MSG = "Failed to read file for introspection"
MISSING_PARAMETERS_MSG = "Missing parameters"
ERROR_TASK_LIVE = (
    "Task is live on tablet; finalize (or force-finalize) first.")


# =============================================================================
# Simple success/failure/redirection, and other snippets used by views
# =============================================================================

def simple_success(req: CamcopsRequest, msg: str,
                   extra_html: str = "") -> Response:
    """Simple success message."""
    return render_to_response("generic_success.mako",
                              dict(msg=msg,
                                   extra_html=extra_html),
                              request=req)


def simple_failure(req: CamcopsRequest, msg: str,
                   extra_html: str = "") -> Response:
    """Simple failure message."""
    return render_to_response("generic_failure.mako",
                              dict(msg=msg,
                                   extra_html=extra_html),
                              request=req)


# =============================================================================
# Unused
# =============================================================================

# def query_result_html_core(req: CamcopsRequest,
#                            descriptions: Sequence[str],
#                            rows: Sequence[Sequence[Any]],
#                            null_html: str = "<i>NULL</i>") -> str:
#     return render("query_result_core.mako",
#                   dict(descriptions=descriptions,
#                        rows=rows,
#                        null_html=null_html),
#                   request=req)


# def query_result_html_orm(req: CamcopsRequest,
#                           attrnames: List[str],
#                           descriptions: List[str],
#                           orm_objects: Sequence[Sequence[Any]],
#                           null_html: str = "<i>NULL</i>") -> str:
#     return render("query_result_orm.mako",
#                   dict(attrnames=attrnames,
#                        descriptions=descriptions,
#                        orm_objects=orm_objects,
#                        null_html=null_html),
#                   request=req)


# =============================================================================
# Error views
# =============================================================================

@notfound_view_config(renderer="not_found.mako")
def not_found(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


@view_config(context=exc.HTTPBadRequest, renderer="bad_request.mako")
def bad_request(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


# =============================================================================
# Test pages
# =============================================================================
# Not on the menus...

@view_config(route_name=Routes.TESTPAGE_PUBLIC_1,
             permission=NO_PERMISSION_REQUIRED)
def test_page_1(req: CamcopsRequest) -> Response:
    return Response("Hello! This is a public CamCOPS test page.")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_1)
def test_page_private_1(req: CamcopsRequest) -> Response:
    return Response("Private test page.")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_2,
             renderer="testpage.mako",
             permission=Permission.SUPERUSER)
def test_page_2(req: CamcopsRequest) -> Dict[str, Any]:
    # Contains POTENTIALLY SENSITIVE test information, including environment
    # variables
    return dict(param1="world")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_3,
             renderer="inherit_cache_test_child.mako",
             permission=Permission.SUPERUSER)
def test_page_3(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


@view_config(route_name=Routes.CRASH, permission=Permission.SUPERUSER)
def crash(req: CamcopsRequest) -> Response:
    """Deliberately raises an exception."""
    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# =============================================================================
# Authorization: login, logout, login failures, terms/conditions
# =============================================================================

# Do NOT use extra parameters for functions decorated with @view_config;
# @view_config can take functions like "def view(request)" but also
# "def view(context, request)", so if you add additional parameters, it thinks
# you're doing the latter and sends parameters accordingly.

@view_config(route_name=Routes.LOGIN, permission=NO_PERMISSION_REQUIRED)
def login_view(req: CamcopsRequest) -> Response:
    cfg = req.config
    autocomplete_password = not cfg.disable_password_autocomplete

    form = LoginForm(request=req, autocomplete_password=autocomplete_password)

    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            # log.critical("controls from POST: {!r}", controls)
            appstruct = form.validate(controls)
            # log.critical("appstruct from POST: {!r}", appstruct)
            log.debug("Validating user login.")
            ccsession = req.camcops_session
            username = appstruct.get(ViewParam.USERNAME)
            password = appstruct.get(ViewParam.PASSWORD)
            redirect_url = appstruct.get(ViewParam.REDIRECT_URL)
            # 1. If we don't have a username, let's stop quickly.
            if not username:
                ccsession.logout(req)
                return login_failed(req)
            # 2. Is the user locked?
            if SecurityAccountLockout.is_user_locked_out(req, username):
                return account_locked(req,
                                      User.user_locked_out_until(username))
            # 3. Is the username/password combination correct?
            user = User.get_user_from_username_password(
                req, username, password)  # checks password
            if user is not None and user.may_use_webviewer:
                # Successful login.
                user.login(req)  # will clear login failure record
                ccsession.login(user)
                audit(req, "Login")
            elif user is not None:
                # This means a user who can upload from tablet but who cannot
                # log in via the web front end.
                return login_failed(req)
            else:
                # Unsuccessful. Note that the username may/may not be genuine.
                SecurityLoginFailure.act_on_login_failure(req, username)
                # ... may lock the account
                # Now, call audit() before session.logout(), as the latter
                # will wipe the session IP address:
                ccsession.logout(req)
                return login_failed(req)

            # OK, logged in.
            # Redirect to the main menu, or wherever the user was heading.
            # HOWEVER, that may lead us to a "change password" or "agree terms"
            # page, via the permissions system (Permission.HAPPY or not).

            if redirect_url:
                # log.critical("Redirecting to {!r}", redirect_url)
                raise exc.HTTPFound(redirect_url)  # redirect
            raise exc.HTTPFound(req.route_url(Routes.HOME))  # redirect

        except ValidationFailure as e:
            rendered_form = e.render()

    else:
        redirect_url = req.get_str_param(ViewParam.REDIRECT_URL, "")
        # ... use default of "", because None gets serialized to "None", which
        #     would then get read back later as "None".
        appstruct = {ViewParam.REDIRECT_URL: redirect_url}
        # log.critical("appstruct from GET/POST: {!r}", appstruct)
        rendered_form = form.render(appstruct)

    return render_to_response(
        "login.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


def login_failed(req: CamcopsRequest) -> Response:
    """
    HTML given after login failure.
    Returned by login_view() only.
    """
    return render_to_response(
        "login_failed.mako",
        dict(),
        request=req
    )


def account_locked(req: CamcopsRequest, locked_until: Pendulum) -> Response:
    """
    HTML given when account locked out.
    Returned by login_view() only.
    """
    return render_to_response(
        "accounted_locked.mako",
        dict(
            locked_until=format_datetime(locked_until,
                                         DateFormat.LONG_DATETIME_WITH_DAY,
                                         "(never)")
        ),
        request=req
    )


@view_config(route_name=Routes.LOGOUT, renderer="logged_out.mako")
def logout(req: CamcopsRequest) -> Dict[str, Any]:
    """Logs a session out."""
    audit(req, "Logout")
    ccsession = req.camcops_session
    ccsession.logout(req)
    return dict()


@view_config(route_name=Routes.OFFER_TERMS, renderer="offer_terms.mako")
def offer_terms(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML offering terms/conditions and requesting acknowledgement."""
    form = OfferTermsForm(
        request=req,
        agree_button_text=req.wappstring("disclaimer_agree"))

    if FormAction.SUBMIT in req.POST:
        req.camcops_session.agree_terms(req)
        raise exc.HTTPFound(req.route_url(Routes.HOME))  # redirect

    return dict(
        title=req.wappstring("disclaimer_title"),
        subtitle=req.wappstring("disclaimer_subtitle"),
        content=req.wappstring("disclaimer_content"),
        form=form.render(),
        head_form_html=get_head_form_html(req, [form]),
    )


@forbidden_view_config()
def forbidden(req: CamcopsRequest) -> Dict[str, Any]:
    if req.has_permission(Authenticated):
        user = req.user
        assert user, "Bug! Authenticated but no user...!?"
        if user.must_change_password():
            raise exc.HTTPFound(req.route_url(Routes.CHANGE_OWN_PASSWORD))
        if user.must_agree_terms():
            raise exc.HTTPFound(req.route_url(Routes.OFFER_TERMS))
    # Otherwise...
    redirect_url = req.url
    # Redirects to login page, with onwards redirection to requested
    # destination once logged in:
    querydict = {ViewParam.REDIRECT_URL: redirect_url}
    return render_to_response("forbidden.mako",
                              dict(querydict=querydict),
                              request=req)


# =============================================================================
# Changing passwords
# =============================================================================

@view_config(route_name=Routes.CHANGE_OWN_PASSWORD)
def change_own_password(req: CamcopsRequest) -> Response:
    ccsession = req.camcops_session
    expired = ccsession.user_must_change_password()
    form = ChangeOwnPasswordForm(request=req, must_differ=True)
    user = req.user
    assert user is not None
    extra_msg = ""
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            # ... form will validate old password, etc.
            # OK
            user.set_password(req, new_password)
            return password_changed(req, user.username, own_password=True)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "change_own_password.mako",
        dict(form=rendered_form,
             expired=expired,
             extra_msg=extra_msg,
             min_pw_length=MINIMUM_PASSWORD_LENGTH,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


@view_config(route_name=Routes.CHANGE_OTHER_PASSWORD,
             permission=Permission.SUPERUSER,
             renderer="change_other_password.mako")
def change_other_password(req: CamcopsRequest) -> Response:
    """For administrators, to change another's password."""
    form = ChangeOtherPasswordForm(request=req)
    username = None  # for type checker
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user_id = appstruct.get(ViewParam.USER_ID)
            must_change_pw = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            user = User.get_user_by_id(req.dbsession, user_id)
            if not user:
                raise exc.HTTPBadRequest(
                    "Missing user for id {}".format(user_id))
            user.set_password(req, new_password)
            if must_change_pw:
                user.force_password_change()
            return password_changed(req, user.username, own_password=False)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        user_id = req.get_int_param(ViewParam.USER_ID)
        if user_id is None:
            raise exc.HTTPBadRequest("Improper user_id of {}".format(
                repr(user_id)))
        user = User.get_user_by_id(req.dbsession, user_id)
        if user is None:
            raise exc.HTTPBadRequest("Missing user for id {}".format(user_id))
        username = user.username
        appstruct = {ViewParam.USER_ID: user_id}
        rendered_form = form.render(appstruct)
    return render_to_response(
        "change_other_password.mako",
        dict(username=username,
             form=rendered_form,
             min_pw_length=MINIMUM_PASSWORD_LENGTH,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


def password_changed(req: CamcopsRequest,
                     username: str,
                     own_password: bool) -> Response:
    return render_to_response("password_changed.mako",
                              dict(username=username,
                                   own_password=own_password),
                              request=req)


# =============================================================================
# Main menu; simple information things
# =============================================================================

@view_config(route_name=Routes.HOME, renderer="main_menu.mako")
def main_menu(req: CamcopsRequest) -> Dict[str, Any]:
    """Main HTML menu."""
    ccsession = req.camcops_session
    cfg = req.config
    return dict(
        authorized_as_superuser=ccsession.authorized_as_superuser(),
        authorized_for_reports=ccsession.authorized_for_reports(),
        authorized_to_dump=ccsession.authorized_to_dump(),
        camcops_url=CAMCOPS_URL,
        id_policies_valid=id_policies_valid(),
        introspection=cfg.introspection,
        now=format_datetime(req.now, DateFormat.SHORT_DATETIME_SECONDS),
        server_version=CAMCOPS_SERVER_VERSION,
    )


# =============================================================================
# Tasks
# =============================================================================

def edit_filter(req: CamcopsRequest, task_filter: TaskFilter,
                redirect_url: str) -> Response:
    if FormAction.SET_FILTERS in req.POST:
        form = EditTaskFilterForm(request=req)
        try:
            controls = list(req.POST.items())
            fa = form.validate(controls)

            who = fa.get(ViewParam.WHO)
            what = fa.get(ViewParam.WHAT)
            when = fa.get(ViewParam.WHEN)
            admin = fa.get(ViewParam.ADMIN)
            task_filter.surname = who.get(ViewParam.SURNAME)
            task_filter.forename = who.get(ViewParam.FORENAME)
            task_filter.dob = who.get(ViewParam.DOB)
            task_filter.sex = who.get(ViewParam.SEX)
            task_filter.idnum_criteria = [
                IdNumDefinition(which_idnum=x[ViewParam.WHICH_IDNUM],
                                idnum_value=x[ViewParam.IDNUM_VALUE])
                for x in who.get(ViewParam.ID_DEFINITIONS)
            ]
            task_filter.task_types = what.get(ViewParam.TASKS)
            task_filter.text_contents = what.get(ViewParam.TEXT_CONTENTS)
            task_filter.complete_only = what.get(ViewParam.COMPLETE_ONLY)
            task_filter.start_datetime = when.get(ViewParam.START_DATETIME)
            task_filter.end_datetime = when.get(ViewParam.END_DATETIME)
            task_filter.device_ids = admin.get(ViewParam.DEVICE_IDS)
            task_filter.adding_user_ids = admin.get(ViewParam.USER_IDS)
            task_filter.group_ids = admin.get(ViewParam.GROUP_IDS)

            raise exc.HTTPFound(redirect_url)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        if FormAction.CLEAR_FILTERS in req.POST:
            # skip validation
            task_filter.clear()
        who = {
            ViewParam.SURNAME: task_filter.surname,
            ViewParam.FORENAME: task_filter.forename,
            ViewParam.DOB: task_filter.dob,
            ViewParam.SEX: task_filter.sex or "",
            ViewParam.ID_DEFINITIONS: [
                {ViewParam.WHICH_IDNUM: x.which_idnum,
                 ViewParam.IDNUM_VALUE: x.idnum_value}
                for x in task_filter.idnum_criteria
            ],
        }
        what = {
            ViewParam.TASKS: task_filter.task_types,
            ViewParam.TEXT_CONTENTS: task_filter.text_contents,
            ViewParam.COMPLETE_ONLY: task_filter.complete_only,
        }
        when = {
            ViewParam.START_DATETIME: task_filter.start_datetime,
            ViewParam.END_DATETIME: task_filter.end_datetime,
        }
        admin = {
            ViewParam.DEVICE_IDS: task_filter.device_ids,
            ViewParam.USER_IDS: task_filter.adding_user_ids,
            ViewParam.GROUP_IDS: task_filter.group_ids,
        }
        log.critical("{!r}", who.values())
        open_who = any(i for i in who.values())
        open_what = any(i for i in what.values())
        open_when = any(i for i in when.values())
        open_admin = any(i for i in admin.values())
        fa = {
            ViewParam.WHO: who,
            ViewParam.WHAT: what,
            ViewParam.WHEN: when,
            ViewParam.ADMIN: admin,
        }
        form = EditTaskFilterForm(request=req,
                                  open_admin=open_admin,
                                  open_what=open_what,
                                  open_when=open_when,
                                  open_who=open_who)
        rendered_form = form.render(fa)

    return render_to_response(
        "edit_filter.mako",
        dict(
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.SET_FILTERS)
def set_filters(req: CamcopsRequest) -> Response:
    redirect_url = req.get_str_param(ViewParam.REDIRECT_URL,
                                     req.route_url(Routes.VIEW_TASKS))
    task_filter = req.camcops_session.get_task_filter()
    return edit_filter(req, task_filter=task_filter, redirect_url=redirect_url)


@view_config(route_name=Routes.VIEW_TASKS, renderer="view_tasks.mako")
def view_tasks(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML displaying tasks and applicable filters."""
    ccsession = req.camcops_session

    # Read from the GET parameters (or in some cases potentially POST but those
    # will be re-read).
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE,
        ccsession.number_to_view or DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    errors = False

    # "Number of tasks per page" form
    tpp_form = TasksPerPageForm(request=req, css_class="form-inline")
    if FormAction.SUBMIT_TASKS_PER_PAGE in req.POST:
        try:
            controls = list(req.POST.items())
            tpp_appstruct = tpp_form.validate(controls)
            rows_per_page = tpp_appstruct.get(ViewParam.ROWS_PER_PAGE)
            ccsession.number_to_view = rows_per_page
        except ValidationFailure:
            errors = True
        rendered_tpp_form = tpp_form.render()
    else:
        tpp_appstruct = {ViewParam.ROWS_PER_PAGE: rows_per_page}
        rendered_tpp_form = tpp_form.render(tpp_appstruct)

    # Refresh tasks. Slightly pointless. Doesn't need validating. The user
    # could just press the browser's refresh button, but this improves the UI
    # slightly.
    refresh_form = RefreshTasksForm(request=req)
    rendered_refresh_form = refresh_form.render()

    # Get tasks, unless there have been form errors.
    # In principle, for some filter settings (single task, no "complete"
    # preference...) we could produce an ORM query and use SqlalchemyOrmPage,
    # which would apply LIMIT/OFFSET (or equivalent) to the query, and be
    # very nippy. In practice, this is probably an unusual setting, so we'll
    # simplify things here with a Python list regardless of the settings.
    if errors:
        collection = []
    else:
        taskfilter = ccsession.get_task_filter()
        collection = TaskCollection(
            req=req,
            taskfilter=taskfilter,
            sort_method_global=TaskSortMethod.CREATION_DATE_DESC
        ).all_tasks
    page = CamcopsPage(collection=collection,
                       page=page_num,
                       items_per_page=rows_per_page,
                       url_maker=PageUrl(req))
    return dict(
        page=page,
        head_form_html=get_head_form_html(req, [tpp_form,
                                                refresh_form]),
        tpp_form=rendered_tpp_form,
        refresh_form=rendered_refresh_form,
        no_patient_selected_and_user_restricted=(
            not ccsession.user_may_view_all_patients_when_unfiltered() and
            not ccsession.any_specific_patient_filtering()
        ),
    )


@view_config(route_name=Routes.TASK)
def serve_task(req: CamcopsRequest) -> Response:
    """Serves an individual task."""
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML, lower=True)
    tablename = req.get_str_param(ViewParam.TABLE_NAME)
    server_pk = req.get_int_param(ViewParam.SERVER_PK)
    anonymise = req.get_bool_param(ViewParam.ANONYMISE, False)

    if viewtype not in ALLOWED_TASK_VIEW_TYPES:
        raise exc.HTTPBadRequest(
            "Bad output type: {!r} (permissible: {!r}".format(
                viewtype, ALLOWED_TASK_VIEW_TYPES))

    task = task_factory(req, tablename, server_pk)

    if task is None:
        raise exc.HTTPNotFound(
            "Task not found or not permitted: tablename={!r}, "
            "server_pk={!r}".format(tablename, server_pk))

    task.audit(req, "Viewed " + viewtype.upper())

    if viewtype == ViewArg.HTML:
        return Response(
            task.get_html(req=req, anonymise=anonymise)
        )
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            content=task.get_pdf(req, anonymise=anonymise),
            filename=task.suggested_pdf_filename(req)
        )
    elif viewtype == VALUE.OUTPUTTYPE_PDFHTML:  # debugging option
        return Response(
            task.get_pdf_html(req, anonymise=anonymise)
        )
    elif viewtype == VALUE.OUTPUTTYPE_XML:
        include_blobs = req.get_bool_param(ViewParam.INCLUDE_BLOBS, True)
        include_calculated = req.get_bool_param(ViewParam.INCLUDE_CALCULATED,
                                                True)
        include_patient = req.get_bool_param(ViewParam.INCLUDE_PATIENT, True)
        include_comments = req.get_bool_param(ViewParam.INCLUDE_COMMENTS, True)
        return XmlResponse(
            task.get_xml(req=req,
                         include_blobs=include_blobs,
                         include_calculated=include_calculated,
                         include_patient=include_patient,
                         include_comments=include_comments)
        )
    else:
        assert False, "Bug in logic above"


# =============================================================================
# Trackers, CTVs
# =============================================================================

def choose_tracker_or_ctv(req: CamcopsRequest,
                          as_ctv: bool) -> Dict[str, Any]:
    """HTML form for tracker selection."""

    form = ChooseTrackerForm(req, as_ctv=as_ctv, css_class="form-inline")

    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.WHICH_IDNUM,
                ViewParam.IDNUM_VALUE,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
                ViewParam.TASKS,
                ViewParam.ALL_TASKS,
                ViewParam.VIEWTYPE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            # Not so obvious this can be redirected cleanly via POST.
            # It is possible by returning a form that then autosubmits: see
            # https://stackoverflow.com/questions/46582/response-redirect-with-post-instead-of-get  # noqa
            # However, since everything's on this server, we could just return
            # an appropriate Response directly. But the information is not
            # sensitive, so we lose nothing by using a GET redirect:
            raise exc.HTTPFound(req.route_url(
                Routes.CTV if as_ctv else Routes.TRACKER,
                _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.CHOOSE_TRACKER, renderer="choose_tracker.mako")
def choose_tracker(req: CamcopsRequest) -> Dict[str, Any]:
    return choose_tracker_or_ctv(req, as_ctv=False)


@view_config(route_name=Routes.CHOOSE_CTV, renderer="choose_ctv.mako")
def choose_ctv(req: CamcopsRequest) -> Dict[str, Any]:
    return choose_tracker_or_ctv(req, as_ctv=True)


def serve_tracker_or_ctv(req: CamcopsRequest,
                         as_ctv: bool) -> Response:
    which_idnum = req.get_int_param(ViewParam.WHICH_IDNUM)
    idnum_value = req.get_int_param(ViewParam.IDNUM_VALUE)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    tasks = req.get_str_list_param(ViewParam.TASKS)
    all_tasks = req.get_bool_param(ViewParam.ALL_TASKS, True)
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML)

    if all_tasks:
        task_classes = None
    else:
        try:
            task_classes = task_classes_from_table_names(
                tasks, sortmethod=TaskClassSortMethod.SHORTNAME)
        except KeyError:
            raise exc.HTTPBadRequest("Invalid tasks specified")
        if not all(c.provides_trackers for c in task_classes):
            raise exc.HTTPBadRequest("Not all tasks specified provide trackers")

    if not viewtype in ALLOWED_TRACKER_VIEW_TYPE:
        raise exc.HTTPBadRequest("Invalid view type")

    iddefs = [IdNumDefinition(which_idnum, idnum_value)]

    as_tracker = not as_ctv
    taskfilter = TaskFilter(
        task_classes=task_classes,
        trackers_only=as_tracker,
        idnum_criteria=iddefs,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        complete_only=as_tracker,  # trackers require complete tasks
        has_patient=True,
        sort_method=TaskClassSortMethod.SHORTNAME,
    )
    tracker_ctv_class = ClinicalTextView if as_ctv else Tracker
    tracker = tracker_ctv_class(req=req, taskfilter=taskfilter)

    if viewtype == ViewArg.HTML:
        return Response(
            tracker.get_html()
        )
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            content=tracker.get_pdf(),
            filename=tracker.suggested_pdf_filename()
        )
    elif viewtype == VALUE.OUTPUTTYPE_PDFHTML:  # debugging option
        return Response(
            tracker.get_pdf_html()
        )
    elif viewtype == VALUE.OUTPUTTYPE_XML:
        include_comments = req.get_bool_param(ViewParam.INCLUDE_COMMENTS, True)
        return XmlResponse(
            tracker.get_xml(include_comments=include_comments)
        )
    else:
        assert False, "Bug in logic above"


@view_config(route_name=Routes.TRACKER)
def serve_tracker(req: CamcopsRequest) -> Response:
    return serve_tracker_or_ctv(req, as_ctv=False)


@view_config(route_name=Routes.CTV)
def serve_ctv(req: CamcopsRequest) -> Response:
    return serve_tracker_or_ctv(req, as_ctv=True)


# =============================================================================
# Reports
# =============================================================================

@view_config(route_name=Routes.REPORTS_MENU, renderer="reports_menu.mako",
             permission=Permission.REPORTS)
def reports_menu(req: CamcopsRequest) -> Dict[str, Any]:
    """Offer a menu of reports."""
    return {}


@view_config(route_name=Routes.OFFER_REPORT, renderer="offer_report.mako",
             permission=Permission.REPORTS)
def offer_report(req: CamcopsRequest) -> Dict[str, Any]:
    """Offer configuration options for a single report."""
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        raise exc.HTTPBadRequest("No such report ID: {}".format(
            repr(report_id)))
    form = report.get_form(req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            querydict = {k: v for k, v in appstruct.items()
                         if k != ViewParam.CSRF_TOKEN}
            raise exc.HTTPFound(req.route_url(Routes.REPORT, _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render({ViewParam.REPORT_ID: report_id})
    return dict(
        report=report,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form])
    )


@view_config(route_name=Routes.REPORT, permission=Permission.REPORTS)
def provide_report(req: CamcopsRequest) -> Response:
    """Serve up a configured report."""
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        raise exc.HTTPBadRequest("No such report ID: {}".format(
            repr(report_id)))
    return report.get_response(req)


# =============================================================================
# Research downloads
# =============================================================================

# ***

# noinspection PyUnusedLocal
def offer_basic_dump(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offer options for a basic research data dump."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
    classes = get_all_task_classes()
    possible_tasks = "".join([
        """
            <label>
                <input type="checkbox" name="{PARAM.TASKTYPES}"
                    value="{tablename}" checked>
                {shortname}
            </label><br>
        """.format(PARAM=PARAM,
                   tablename=cls.tablename,
                   shortname=cls.shortname)
        for cls in classes])

    return pls.WEBSTART + """
        {userdetails}
        <h1>Basic research data dump</h1>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.BASIC_DUMP}">

                <label onclick="show_tasks(false);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_EVERYTHING}" checked>
                    Everything
                </label><br>

                <label onclick="show_tasks(false);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_AS_TASK_FILTER}">
                    Those tasks selected by the current filters
                </label><br>

                <label onclick="show_tasks(true);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_SPECIFIC_TASKS}">
                    Just specific tasks
                </label><br>

                <div id="tasklist" class="indented" style="display: none">
                    {possible_tasks}
                    <!-- buttons must have type "button" in order not to
                            submit -->
                    <button type="button" onclick="select_all(true);">
                        Select all
                    </button>
                    <button type="button" onclick="select_all(false);">
                        Deselect all
                    </button>
                </div>

                <br>

                <input type="submit" value="Dump data">

                <script>
            function select_all(state) {{
                checkboxes = document.getElementsByName("{PARAM.TASKTYPES}");
                for (var i = 0, n = checkboxes.length; i < n; i++) {{
                    checkboxes[i].checked = state;
                }}
            }}
            function show_tasks(state) {{
                s = state ? "block" : "none";
                document.getElementById("tasklist").style.display = s;
            }}
                </script>
            </form>
        </div>
        <h2>Explanation</h2>
        <div>
          <ul>
            <li>
              Provides a ZIP file containing tab-separated value (TSV)
              files (usually one per task; for some tasks, more than
              one).
            </li>
            <li>
              Restricted to current records (i.e. ignores historical
              versions of tasks that have been edited), unless you use
              the settings from the
              <a href="{view_tasks}">current filters</a> and those
              settings include non-current versions.
            </li>
            <li>
              If there are no instances of a particular task, no TSV is
              returned.
            </li>
            <li>
              Incorporates patient and summary information into each row.
              Doesn’t provide BLOBs (e.g. pictures).
              NULL values are represented by blank fields and are therefore
              indistinguishable from blank strings.
              Tabs are escaped to a literal <code>\\t</code>.
              Newlines are escaped to a literal <code>\\n</code>.
            </li>
            <li>
              Once you’ve unzipped the resulting file, you can import TSV files
              into many other software packages. Here are some examples:
              <ul>
                <li>
                  <b>OpenOffice:</b>
                  Character set =  UTF-8; Separated by / Tab.
                  <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                  <b>Excel:</b> Delimited / Tab.
                  <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                  <b>R:</b>
                  <code>mydf = read.table("something.tsv", sep="\\t",
                  header=TRUE, na.strings="", comment.char="")</code>
                  <i>(note that R will prepend ‘X’ to variable names starting
                  with an underscore; see <code>?make.names</code>)</i>.
                  Inspect the results with e.g. <code>colnames(mydf)</code>, or
                  in RStudio, <code>View(mydf)</code>.
                </li>
              </ul>
            </li>
            <li>
              For more advanced features, use the <a href="{table_dump}">
              table/view dump</a> to get the raw data.
            </li>
            <li>
              <b>For explanations of each field (field comments), see each
              task’s XML view or inspect the table definitions.</b>
            </li>
          </ul>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        VALUE=VALUE,
        view_tasks=get_generic_action_url(ACTION.VIEW_TASKS),
        table_dump=get_generic_action_url(ACTION.OFFER_TABLE_DUMP),
        possible_tasks=possible_tasks,
    ) + WEBEND


def basic_dump(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Provides a basic research dump (ZIP of TSV files)."""

    # Permissions
    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)

    # Parameters
    dump_type = ws.get_cgi_parameter_str(form, PARAM.BASIC_DUMP_TYPE)
    permitted_dump_types = [VALUE.DUMPTYPE_EVERYTHING,
                            VALUE.DUMPTYPE_AS_TASK_FILTER,
                            VALUE.DUMPTYPE_SPECIFIC_TASKS]
    if dump_type not in permitted_dump_types:
        return fail_with_error_stay_logged_in(
            "Basic dump: {PARAM.BASIC_DUMP_TYPE} must be one of "
            "{permitted}.".format(
                PARAM=PARAM,
                permitted=str(permitted_dump_types),
            )
        )
    task_tablename_list = ws.get_cgi_parameter_list(form, PARAM.TASKTYPES)

    # Create memory file
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")

    # Generate everything
    classes = get_all_task_classes()
    processed_tables = []
    for cls in classes:
        if dump_type == VALUE.DUMPTYPE_AS_TASK_FILTER:
            if not cls.filter_allows_task_type(session):
                continue
        table = cls.tablename
        if dump_type == VALUE.DUMPTYPE_SPECIFIC_TASKS:
            if table not in task_tablename_list:
                continue
        processed_tables.append(table)
        if dump_type == VALUE.DUMPTYPE_AS_TASK_FILTER:
            genfunc = cls.gen_all_tasks_matching_session_filter
            args = [session]
        else:
            genfunc = cls.gen_all_current_tasks
            args = []
        kwargs = dict(sort=True, reverse=False)
        allfiles = collections.OrderedDict()
        # Some tasks may not return any rows for some of their potential
        # files. So we can't rely on the first task as being an exemplar.
        # Instead, we have a filename/contents mapping.
        for task in genfunc(*args, **kwargs):
            dictlist = task.get_dictlist_for_tsv()
            for i in range(len(dictlist)):
                filename = dictlist[i]["filenamestem"] + ".tsv"
                rows = dictlist[i]["rows"]
                if not rows:
                    continue
                if filename not in allfiles:
                    # First time we've encountered this filename; add header
                    allfiles[filename] = (
                        get_tsv_header_from_dict(rows[0]) + "\n"
                    )
                for r in rows:
                    allfiles[filename] += get_tsv_line_from_dict(r) + "\n"
        # If there are no valid task instances, there'll be no TSV; that's OK.
        for filename, contents in allfiles.items():
            z.writestr(filename, contents.encode("utf-8"))
    z.close()

    # Audit
    audit("basic dump: " + " ".join(processed_tables))

    # Return the result
    zip_contents = memfile.getvalue()
    filename = "CamCOPS_dump_" + format_datetime(
        pls.NOW_LOCAL_TZ,
        DateFormat.FILENAME
    ) + ".zip"
    # atypical content type
    return ws.zip_result(zip_contents, [], filename)


# noinspection PyUnusedLocal
def offer_table_dump(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """HTML form to request dump of table data."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
    # POST, not GET, or the URL exceeds the Apache limit
    html = pls.WEBSTART + """
        {userdetails}
        <h1>Dump table/view data</h1>
        <div class="warning">
            Beware including the blobs table; it is usually
            giant (BLOB = binary large object = pictures and the like).
        </div>
        <div class="filter">
            <form method="POST" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.TABLE_DUMP}">
                <br>

                Possible tables/views:<br>
                <br>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
    )

    for x in get_permitted_tables_views_sorted_labelled():
        if x["name"] == Blob.__tablename__:
            name = PARAM.TABLES_BLOB
            checked = ""
        else:
            if x["view"]:
                name = PARAM.VIEWS
                checked = ""
            else:
                name = PARAM.TABLES
                checked = "checked"
        html += """
            <label>
                <input type="checkbox" name="{}" value="{}" {}>{}
            </label><br>
        """.format(name, x["name"], checked, x["name"])

    html += """
                <button type="button"
                        onclick="select_all_tables(true); deselect_blobs();">
                    Select all tables except blobs
                </button>
                <button type="button"
                        onclick="select_all_tables(false); deselect_blobs();">
                    Deselect all tables
                </button><br>
                <button type="button" onclick="select_all_views(true);">
                    Select all views
                </button>
                <button type="button" onclick="select_all_views(false);">
                    Deselect all views
                </button><br>
                <br>

                Dump as:<br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_SQL}">
                    SQL in UTF-8 encoding, views as their definitions
                </label><br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_TSV}" checked>
                    ZIP file containing tab-separated values (TSV) files in
                    UTF-8 encoding, NULL values as the string literal
                    <code>NULL</code>, views as their contents
                </label><br>
                <br>

                <input type="submit" value="Dump">

                <script>
        function select_all_tables(state) {{
            checkboxes = document.getElementsByName("{PARAM.TABLES}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = state;
            }}
        }}
        function select_all_views(state) {{
            checkboxes = document.getElementsByName("{PARAM.VIEWS}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = state;
            }}
        }}
        function deselect_blobs() {{
            checkboxes = document.getElementsByName("{PARAM.TABLES_BLOB}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = false;
            }}
        }}
                </script>
            </form>
        </div>
    """.format(
        PARAM=PARAM,
        VALUE=VALUE,
    )
    return html + WEBEND


def serve_table_dump(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve a dump of table +/- view data."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    tables = (
        ws.get_cgi_parameter_list(form, PARAM.TABLES) +
        ws.get_cgi_parameter_list(form, PARAM.VIEWS) +
        ws.get_cgi_parameter_list(form, PARAM.TABLES_BLOB)
    )
    if outputtype == VALUE.OUTPUTTYPE_SQL:
        filename = "CamCOPS_dump_" + format_datetime(
            pls.NOW_LOCAL_TZ,
            DateFormat.FILENAME
        ) + ".sql"
        # atypical content type
        return ws.text_result(
            get_database_dump_as_sql(tables), [], filename
        )
    elif outputtype == VALUE.OUTPUTTYPE_TSV:
        zip_contents = get_multiple_views_data_as_tsv_zip(tables)
        if zip_contents is None:
            return fail_with_error_stay_logged_in(NOTHING_VALID_SPECIFIED)
        filename = "CamCOPS_dump_" + format_datetime(
            pls.NOW_LOCAL_TZ,
            DateFormat.FILENAME
        ) + ".zip"
        # atypical content type
        return ws.zip_result(zip_contents, [], filename)
    else:
        return fail_with_error_stay_logged_in(
            "Dump: outputtype must be '{}' or '{}'".format(
                VALUE.OUTPUTTYPE_SQL,
                VALUE.OUTPUTTYPE_TSV
            )
        )


# =============================================================================
# View DDL (table definitions)
# =============================================================================

LEXERMAP = {
    Dialect.MYSQL: pygments.lexers.sql.MySqlLexer,
    Dialect.MSSQL: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.ORACLE: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.FIREBIRD: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.POSTGRES: pygments.lexers.sql.PostgresLexer,
    Dialect.SQLITE: pygments.lexers.sql.SqlLexer,  # generic; SqliteConsoleLexer is wrong  # noqa
    Dialect.SYBASE: pygments.lexers.sql.SqlLexer,  # generic
}


@view_config(route_name=Routes.VIEW_DDL)
def view_ddl(req: CamcopsRequest) -> Response:
    """Inspect table definitions with field comments."""
    form = ViewDdlForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dialect = appstruct.get(ViewParam.DIALECT)
            ddl = get_all_ddl(dialect_name=dialect)
            lexer = LEXERMAP[dialect]()
            formatter = pygments.formatters.HtmlFormatter()
            html = pygments.highlight(ddl, lexer, formatter)
            css = formatter.get_style_defs('.highlight')
            return render_to_response("introspect_file.mako",
                                      dict(css=css,
                                           code_html=html),
                                      request=req)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    current_dialect = get_dialect_name(get_engine_from_session(req.dbsession))
    current_dialect_description = {k: v for k, v in DIALECT_CHOICES}.get(
        current_dialect, "?")
    return render_to_response(
        "view_ddl_choose_dialect.mako",
        dict(current_dialect=current_dialect,
             current_dialect_description=current_dialect_description,
             form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


# =============================================================================
# View audit trail
# =============================================================================

@view_config(route_name=Routes.OFFER_AUDIT_TRAIL,
             permission=Permission.SUPERUSER)
def offer_audit_trail(req: CamcopsRequest) -> Response:
    form = AuditTrailForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
                ViewParam.SOURCE,
                ViewParam.REMOTE_IP_ADDR,
                ViewParam.USERNAME,
                ViewParam.TABLE_NAME,
                ViewParam.SERVER_PK,
                ViewParam.TRUNCATE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET:
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_AUDIT_TRAIL,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "audit_trail_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


AUDIT_TRUNCATE_AT = 100


@view_config(route_name=Routes.VIEW_AUDIT_TRAIL,
             permission=Permission.SUPERUSER)
def view_audit_trail(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    source = req.get_str_param(ViewParam.SOURCE, None)
    remote_addr = req.get_str_param(ViewParam.REMOTE_IP_ADDR, None)
    username = req.get_str_param(ViewParam.USERNAME, None)
    table_name = req.get_str_param(ViewParam.TABLE_NAME, None)
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    truncate = req.get_bool_param(ViewParam.TRUNCATE, True)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(AuditEntry)
    if start_datetime:
        q = q.filter(AuditEntry.when_access_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(AuditEntry.when_access_utc <= end_datetime)
        add_condition(ViewParam.END_DATETIME, end_datetime)
    if source:
        q = q.filter(AuditEntry.source == source)
        add_condition(ViewParam.SOURCE, source)
    if remote_addr:
        q = q.filter(AuditEntry.remote_addr == remote_addr)
        add_condition(ViewParam.REMOTE_IP_ADDR, remote_addr)
    if username:
        # https://stackoverflow.com/questions/8561470/sqlalchemy-filtering-by-relationship-attribute  # noqa
        q = q.join(User).filter(User.username == username)
        add_condition(ViewParam.USERNAME, username)
    if table_name:
        q = q.filter(AuditEntry.table_name == table_name)
        add_condition(ViewParam.TABLE_NAME, table_name)
    if server_pk is not None:
        q = q.filter(AuditEntry.server_pk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)

    q = q.order_by(desc(AuditEntry.id))

    # audit_entries = dbsession.execute(q).fetchall()
    # ... no! That executes to give you row-type results.
    # audit_entries = q.all()
    # ... yes! But let's paginate, too:
    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("audit_trail_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page,
                                   truncate=truncate,
                                   truncate_at=AUDIT_TRUNCATE_AT),
                              request=req)


# =============================================================================
# View HL7 message log
# =============================================================================

@view_config(route_name=Routes.OFFER_HL7_MESSAGE_LOG,
             permission=Permission.SUPERUSER)
def offer_hl7_message_log(req: CamcopsRequest) -> Response:
    form = HL7MessageLogForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.TABLE_NAME,
                ViewParam.SERVER_PK,
                ViewParam.HL7_RUN_ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_HL7_MESSAGE_LOG,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_message_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


@view_config(route_name=Routes.VIEW_HL7_MESSAGE_LOG,
             permission=Permission.SUPERUSER)
def view_hl7_message_log(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    table_name = req.get_str_param(ViewParam.TABLE_NAME, None)
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(HL7Message)
    if table_name:
        q = q.filter(HL7Message.basetable == table_name)
        add_condition(ViewParam.TABLE_NAME, table_name)
    if server_pk is not None:
        q = q.filter(HL7Message.serverpk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)
    if hl7_run_id is not None:
        q = q.filter(HL7Message.run_id == hl7_run_id)
        add_condition(ViewParam.HL7_RUN_ID, hl7_run_id)
    if start_datetime:
        q = q.filter(HL7Message.sent_at_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(HL7Message.sent_at_utc <= end_datetime)
        add_condition(ViewParam.END_DATETIME, end_datetime)

    q = q.order_by(desc(HL7Message.msg_id))

    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("hl7_message_log_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page),
                              request=req)


@view_config(route_name=Routes.VIEW_HL7_MESSAGE,
             permission=Permission.SUPERUSER)
def view_hl7_message(req: CamcopsRequest) -> Response:
    hl7_msg_id = req.get_int_param(ViewParam.HL7_MSG_ID, None)
    dbsession = req.dbsession
    hl7msg = dbsession.query(HL7Message)\
        .filter(HL7Message.msg_id == hl7_msg_id)\
        .first()
    if hl7msg is None:
        raise exc.HTTPBadRequest("Bad HL7 message ID {}".format(hl7_msg_id))
    return render_to_response("hl7_message_view.mako",
                              dict(msg=hl7msg),
                              request=req)


# =============================================================================
# View HL7 run log and individual runs
# =============================================================================

@view_config(route_name=Routes.OFFER_HL7_RUN_LOG,
             permission=Permission.SUPERUSER)
def offer_hl7_run_log(req: CamcopsRequest) -> Response:
    form = HL7RunLogForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.HL7_RUN_ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_HL7_RUN_LOG,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_run_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


@view_config(route_name=Routes.VIEW_HL7_RUN_LOG,
             permission=Permission.SUPERUSER)
def view_hl7_run_log(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(HL7Run)
    if hl7_run_id is not None:
        q = q.filter(HL7Run.run_id == hl7_run_id)
        add_condition("hl7_run_id", hl7_run_id)
    if start_datetime:
        q = q.filter(HL7Run.start_at_utc >= start_datetime)
        add_condition("start_datetime", start_datetime)
    if end_datetime:
        q = q.filter(HL7Run.start_at_utc <= end_datetime)
        add_condition("end_datetime", end_datetime)

    q = q.order_by(desc(HL7Run.run_id))

    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("hl7_run_log_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page),
                              request=req)


@view_config(route_name=Routes.VIEW_HL7_RUN,
             permission=Permission.SUPERUSER)
def view_hl7_run(req: CamcopsRequest) -> Response:
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    dbsession = req.dbsession
    hl7run = dbsession.query(HL7Run)\
        .filter(HL7Run.run_id == hl7_run_id)\
        .first()
    if hl7run is None:
        raise exc.HTTPBadRequest("Bad HL7 run ID {}".format(hl7_run_id))
    return render_to_response("hl7_run_view.mako",
                              dict(hl7run=hl7run),
                              request=req)


# =============================================================================
# User/server info views
# =============================================================================

@view_config(route_name=Routes.VIEW_OWN_USER_INFO,
             renderer="view_own_user_info.mako")
def view_own_user_info(req: CamcopsRequest) -> Dict[str, Any]:
    return dict(user=req.camcops_session.user)


@view_config(route_name=Routes.VIEW_SERVER_INFO,
             renderer="view_server_info.mako")
def view_server_info(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML showing server's ID policies."""
    cfg = req.config
    which_idnums = cfg.get_which_idnums()
    dbsession = req.dbsession
    groups = dbsession.query(Group)\
        .order_by(Group.name)\
        .all()  # type: List[Group]
    return dict(
        cfg=cfg,
        which_idnums=which_idnums,
        descriptions=[cfg.get_id_desc(n) for n in which_idnums],
        short_descriptions=[cfg.get_id_shortdesc(n) for n in which_idnums],
        upload=cfg.id_policy_upload_string,
        finalize=cfg.id_policy_finalize_string,
        upload_principal=get_upload_id_policy_principal_numeric_id(),
        finalize_principal=get_finalize_id_policy_principal_numeric_id(),
        groups=groups,
    )


# =============================================================================
# User management
# =============================================================================

EDIT_USER_KEYS = [
    # SPECIAL HANDLING # ViewParam.USER_ID,
    ViewParam.USERNAME,
    ViewParam.FULLNAME,
    ViewParam.EMAIL,
    ViewParam.MAY_UPLOAD,
    ViewParam.MAY_REGISTER_DEVICES,
    ViewParam.MAY_USE_WEBVIEWER,
    ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED,
    ViewParam.SUPERUSER,
    ViewParam.MAY_DUMP_DATA,
    ViewParam.MAY_RUN_REPORTS,
    ViewParam.MAY_ADD_NOTES,
    ViewParam.MUST_CHANGE_PASSWORD,
    # SPECIAL HANDLING # ViewParam.GROUP_IDS,
]


def get_user_from_request_user_id_or_raise(req: CamcopsRequest) -> User:
    user_id = req.get_int_param(ViewParam.USER_ID)
    user = User.get_user_by_id(req.dbsession, user_id)
    if not user:
        raise exc.HTTPBadRequest("No such user ID: {}".format(repr(user_id)))
    return user


@view_config(route_name=Routes.VIEW_ALL_USERS,
             permission=Permission.SUPERUSER,
             renderer="view_users.mako")
def view_all_users(req: CamcopsRequest) -> Dict[str, Any]:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    q = dbsession.query(User).order_by(User.username)
    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return dict(page=page)


@view_config(route_name=Routes.VIEW_USER,
             permission=Permission.SUPERUSER,
             renderer="view_other_user_info.mako")
def view_user(req: CamcopsRequest) -> Dict[str, Any]:
    user = get_user_from_request_user_id_or_raise(req)
    return dict(user=user)


@view_config(route_name=Routes.EDIT_USER,
             permission=Permission.SUPERUSER,
             renderer="edit_user.mako")
def edit_user(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    user = get_user_from_request_user_id_or_raise(req)
    form = EditUserForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dbsession = req.dbsession
            new_user_name = appstruct.get(ViewParam.USERNAME)
            existing_user = User.get_user_by_name(dbsession, new_user_name)
            if existing_user and existing_user.id != user.id:
                raise exc.HTTPBadRequest(
                    "Can't rename user {!r} (ID {!r}) to {!r}; that "
                    "conflicts with existing user with ID {!r}".format(
                        user.name, user.id, new_user_name,
                        existing_user.id
                    ))
            for k in EDIT_USER_KEYS:
                setattr(user, k, appstruct.get(k))
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            user.set_group_ids(group_ids)
            # Also, if the user was uploading to a group that they are now no
            # longer a member of, we need to fix that
            if user.upload_group_id not in group_ids:
                user.upload_group_id = None
            raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {k: getattr(user, k) for k in EDIT_USER_KEYS}
        appstruct[ViewParam.USER_ID] = user.id
        appstruct[ViewParam.GROUP_IDS] = user.group_ids()
        rendered_form = form.render(appstruct)
    return dict(user=user,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def set_user_upload_group(req: CamcopsRequest,
                          user: User,
                          as_superuser: bool) -> Response:
    destination = Routes.VIEW_ALL_USERS if as_superuser else Routes.HOME
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(destination))
    form = SetUserUploadGroupForm(request=req, user=user)
    # ... need to show the groups permitted to THAT user, not OUR user
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user.upload_group_id = appstruct.get(ViewParam.UPLOAD_GROUP_ID)
            raise exc.HTTPFound(req.route_url(destination))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.USER_ID: user.id,
            ViewParam.UPLOAD_GROUP_ID: user.upload_group_id
        }
        rendered_form = form.render(appstruct)
    return render_to_response(
        "set_user_upload_group.mako",
        dict(user=user,
             form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


@view_config(route_name=Routes.SET_OWN_USER_UPLOAD_GROUP)
def set_own_user_upload_group(req: CamcopsRequest) -> Response:
    return set_user_upload_group(req, req.user, False)


@view_config(route_name=Routes.SET_OTHER_USER_UPLOAD_GROUP,
             permission=Permission.SUPERUSER)
def set_other_user_upload_group(req: CamcopsRequest) -> Response:
    user = get_user_from_request_user_id_or_raise(req)
    return set_user_upload_group(req, user, True)


@view_config(route_name=Routes.UNLOCK_USER,
             permission=Permission.SUPERUSER)
def unlock_user(req: CamcopsRequest) -> Response:
    user = get_user_from_request_user_id_or_raise(req)
    user.enable(req)
    return simple_success(req, "User {} enabled".format(user.username))


@view_config(route_name=Routes.ADD_USER,
             permission=Permission.SUPERUSER,
             renderer="add_user.mako")
def add_user(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    form = AddUserForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user = User()
            user.username = appstruct.get(ViewParam.USERNAME)
            user.set_password(req, appstruct.get(ViewParam.NEW_PASSWORD))
            user.must_change_password = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)  # noqa
            if User.get_user_by_name(dbsession, user.username):
                raise exc.HTTPBadRequest("User with username {!r} already "
                                         "exists!".format(user.username))
            dbsession.add(user)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def any_records_use_user(req: CamcopsRequest, user: User) -> bool:
    dbsession = req.dbsession
    user_id = user.id
    # Our own or users filtering on us?
    q = CountStarSpecializedQuery(CamcopsSession, session=dbsession).filter(
        CamcopsSession.filter_user_id == user_id,
    )
    if q.count_star() > 0:
        return True
    # Device?
    q = CountStarSpecializedQuery(Device, session=dbsession).filter(
        or_(
            Device.registered_by_user_id == user_id,
            Device.uploading_user_id == user_id,
        )
    )
    if q.count_star() > 0:
        return True
    # SpecialNote?
    q = CountStarSpecializedQuery(SpecialNote, session=dbsession).filter(
        SpecialNote.user_id == user_id
    )
    if q.count_star() > 0:
        return True
    # Uploaded records?
    for cls in gen_orm_classes_from_base(GenericTabletRecordMixin):  # type: Type[GenericTabletRecordMixin]  # noqa
        q = CountStarSpecializedQuery(cls, session=dbsession).filter(
            or_(
                cls._adding_user_id == user_id,
                cls._removing_user_id == user_id,
                cls._preserving_user_id == user_id,
                cls._manually_erasing_user_id == user_id,
            )
        )
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(route_name=Routes.DELETE_USER,
             permission=Permission.SUPERUSER,
             renderer="delete_user.mako")
def delete_user(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    user = get_user_from_request_user_id_or_raise(req)
    form = DeleteUserForm(request=req)
    rendered_form = ""
    error = ""
    if user.id == req.user.id:
        error = "Can't delete your own user!"
    elif user.may_use_webviewer or user.may_upload:
        error = "Unable to delete user; still has webviewer login and/or " \
                "tablet upload permission"
    else:
        if any_records_use_user(req, user):
            error = "Unable to delete user; records refer to that user. " \
                    "Disable login and upload permissions instead."
        else:
            if FormAction.DELETE in req.POST:
                try:
                    controls = list(req.POST.items())
                    appstruct = form.validate(controls)
                    assert appstruct.get(ViewParam.USER_ID) == user.id
                    # (*) Sessions belonging to this user
                    # ... done by modifying its ForeignKey to use "ondelete"
                    # (*) user_group_table mapping
                    # http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#relationships-many-to-many-deletion  # noqa
                    # Simplest way:
                    user.groups = []  # will delete the mapping entries
                    # (*) User itself
                    req.dbsession.delete(user)
                    # Done
                    raise exc.HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
                except ValidationFailure as e:
                    rendered_form = e.render()
            else:
                appstruct = {ViewParam.USER_ID: user.id}
                rendered_form = form.render(appstruct)

    return dict(user=user,
                error=error,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# =============================================================================
# Group management
# =============================================================================

@view_config(route_name=Routes.VIEW_GROUPS,
             permission=Permission.SUPERUSER,
             renderer="view_groups.mako")
def view_groups(req: CamcopsRequest) -> Dict[str, Any]:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    q = dbsession.query(Group).order_by(Group.name)
    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return dict(page=page)


def get_group_from_request_group_id_or_raise(req: CamcopsRequest) -> Group:
    group_id = req.get_int_param(ViewParam.GROUP_ID)
    group = None
    if group_id is not None:
        dbsession = req.dbsession
        group = dbsession.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise exc.HTTPBadRequest("No such group ID: {}".format(repr(group_id)))
    return group


@view_config(route_name=Routes.EDIT_GROUP,
             permission=Permission.SUPERUSER,
             renderer="edit_group.mako")
def edit_group(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
    group = get_group_from_request_group_id_or_raise(req)
    form = EditGroupForm(request=req, group=group)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            new_group_name = appstruct.get(ViewParam.NAME)
            existing_group = Group.get_group_by_name(dbsession, new_group_name)
            if existing_group and existing_group.id != group.id:
                raise exc.HTTPBadRequest(
                    "Can't rename group {!r} (ID {!r}) to {!r}; that "
                    "conflicts with existing group with ID {!r}".format(
                        group.name, group.id, new_group_name,
                        existing_group.id
                    ))
            group.name = new_group_name
            group.description = appstruct.get(ViewParam.DESCRIPTION)
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            group_ids = [gid for gid in group_ids if gid != group.id]
            # ... don't bother saying "you can see yourself"
            other_groups = Group.get_groups_from_id_list(dbsession, group_ids)
            group.can_see_other_groups = other_groups
            raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        other_group_ids = list(group.ids_of_other_groups_group_may_see())
        other_groups = Group.get_groups_from_id_list(dbsession, other_group_ids)
        other_groups.sort(key=lambda g: g.name)
        appstruct = {
            ViewParam.GROUP_ID: group.id,
            ViewParam.NAME: group.name,
            ViewParam.DESCRIPTION: group.description,
            ViewParam.GROUP_IDS: [g.id for g in other_groups],
        }
        rendered_form = form.render(appstruct)
    return dict(group=group,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.ADD_GROUP,
             permission=Permission.SUPERUSER,
             renderer="add_group.mako")
def add_group(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
    form = AddGroupForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            group = Group()
            group.name = appstruct.get(ViewParam.NAME)
            if Group.get_group_by_name(dbsession, group.name):
                raise exc.HTTPBadRequest("Group with name {!r} already "
                                         "exists!".format(group.name))
            dbsession.add(group)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def any_records_use_group(req: CamcopsRequest, group: Group) -> bool:
    dbsession = req.dbsession
    group_id = group.id
    # Our own or users filtering on us?
    # *** IMPLEMENT
    # Uploaded records?
    for cls in gen_orm_classes_from_base(GenericTabletRecordMixin):  # type: Type[GenericTabletRecordMixin]  # noqa
        q = CountStarSpecializedQuery(cls, session=dbsession).filter(
            cls._group_id == group_id
        )
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(route_name=Routes.DELETE_GROUP,
             permission=Permission.SUPERUSER,
             renderer="delete_group.mako")
def delete_group(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
    group = get_group_from_request_group_id_or_raise(req)
    form = DeleteGroupForm(request=req)
    rendered_form = ""
    error = ""
    if group.users:
        error = "Unable to delete group; there are users who are members!"
    else:
        if any_records_use_group(req, group):
            error = "Unable to delete group; records refer to it."
        else:
            if FormAction.DELETE in req.POST:
                try:
                    controls = list(req.POST.items())
                    appstruct = form.validate(controls)
                    assert appstruct.get(ViewParam.GROUP_ID) == group.id
                    req.dbsession.delete(group)
                    # Done
                    raise exc.HTTPFound(req.route_url(Routes.VIEW_GROUPS))
                except ValidationFailure as e:
                    rendered_form = e.render()
            else:
                appstruct = {ViewParam.GROUP_ID: group.id}
                rendered_form = form.render(appstruct)

    return dict(group=group,
                error=error,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# =============================================================================
# Introspection of source code
# =============================================================================

@view_config(route_name=Routes.OFFER_INTROSPECTION)
def offer_introspection(req: CamcopsRequest) -> Response:
    """Page to offer CamCOPS server source code."""
    cfg = req.config
    if not cfg.introspection:
        return simple_failure(req, NO_INTROSPECTION_MSG)
    return render_to_response(
        "introspection_file_list.mako",
        dict(ifd_list=cfg.introspection_files),
        request=req
    )


@view_config(route_name=Routes.INTROSPECT)
def introspect(req: CamcopsRequest) -> Response:
    """Provide formatted source code."""
    cfg = req.config
    if not cfg.introspection:
        return simple_failure(req, NO_INTROSPECTION_MSG)
    filename = req.get_str_param(ViewParam.FILENAME, None)
    try:
        ifd = next(ifd for ifd in cfg.introspection_files
                   if ifd.prettypath == filename)
    except StopIteration:
        return simple_failure(req, INTROSPECTION_INVALID_FILE_MSG)
    fullpath = ifd.fullpath

    if fullpath.endswith(".jsx"):
        lexer = pygments.lexers.web.JavascriptLexer()
    else:
        lexer = pygments.lexers.get_lexer_for_filename(fullpath)
    formatter = pygments.formatters.HtmlFormatter()
    try:
        with codecs.open(fullpath, "r", "utf8") as f:
            code = f.read()
    except Exception as e:
        log.debug("INTROSPECTION ERROR: {}", e)
        return simple_failure(req, INTROSPECTION_FAILED_MSG)
    code_html = pygments.highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return render_to_response("introspect_file.mako",
                              dict(css=css,
                                   code_html=code_html),
                              request=req)


# =============================================================================
# Altering data
# =============================================================================

def add_special_note(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Add a special note to a task (after confirmation)."""

    if not session.authorized_to_add_special_note():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 2
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    note = ws.get_cgi_parameter_str(form, PARAM.NOTE)
    task = task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    textarea = ""
    if confirmation_sequence == n_confirmations - 1:
        textarea = """
                <textarea name="{PARAM.NOTE}" rows="20" cols="80"></textarea>
                <br>
        """.format(
            PARAM=PARAM,
        )
    if confirmation_sequence < n_confirmations:
        return pls.WEBSTART + """
            {user}
            <h1>Add special note to task instance irrevocably</h1>
            {taskinfo}
            <div class="warning">
                <b>Are you {really} sure you want to apply a note?</b>
            </div>
            <p><i>Your note will be appended to any existing note.</i></p>
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.ADD_SPECIAL_NOTE}">
                <input type="hidden" name="{PARAM.TABLENAME}"
                        value="{tablename}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{serverpk}">
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                {textarea}
                <input type="submit" class="important" value="Apply note">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
        """.format(
            user=session.get_current_user_html(),
            taskinfo=task.get_task_header_html(),
            really=" really" * confirmation_sequence,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
            tablename=tablename,
            serverpk=serverpk,
            confirmation_sequence=confirmation_sequence + 1,
            textarea=textarea,
            cancelurl=get_url_task_html(tablename, serverpk),
        ) + WEBEND
    # If we get here, we'll apply the note.
    task.apply_special_note(note, session.user_id)
    return simple_success(
        "Note applied ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(get_url_task_html(tablename, serverpk))
    )


def erase_task(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
    """
    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    task = task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if task.is_erased():
        return fail_with_error_stay_logged_in("Task already erased.")
    if task.is_live_on_tablet():
        return fail_with_error_stay_logged_in(ERROR_TASK_LIVE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    if confirmation_sequence < n_confirmations:
        return pls.WEBSTART + """
            {user}
            <h1>Erase task instance irrevocably</h1>
            {taskinfo}
            <div class="warning">
                <b>ARE YOU {really} SURE YOU WANT TO ERASE THIS TASK?</b>
            </div>
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.ERASE_TASK}">
                <input type="hidden" name="{PARAM.TABLENAME}"
                        value="{tablename}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{serverpk}">
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important" value="Erase task">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
        """.format(
            user=session.get_current_user_html(),
            taskinfo=task.get_task_header_html(),
            really=" REALLY" * confirmation_sequence,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
            tablename=tablename,
            serverpk=serverpk,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=get_url_task_html(tablename, serverpk),
        ) + WEBEND
    # If we get here, we'll do the erasure.
    task.manually_erase(session.user_id)
    return simple_success(
        "Task erased ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(get_url_task_html(tablename, serverpk))
    )


def delete_patient(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Completely delete all data from a patient (after confirmation)."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient_server_pks = get_patient_server_pks_by_idnum(
        which_idnum, idnum_value, current_only=False)
    if which_idnum is not None or idnum_value is not None:
        # A patient was asked for...
        if not patient_server_pks:
            # ... but not found
            return fail_with_error_stay_logged_in("No such patient found.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if which_idnum is not None and idnum_value is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                gen_tasks_for_patient_deletion(which_idnum, idnum_value))
        if confirmation_sequence > 0:
            warning = """
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO ERASE THIS PATIENT AND
                    ALL ASSOCIATED TASKS?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            patient_picker_or_label = """
                <input type="hidden" name="{PARAM.WHICH_IDNUM}"
                        value="{which_idnum}">
                <input type="hidden" name="{PARAM.IDNUM_VALUE}"
                        value="{idnum_value}">
                {id_desc}:
                <b>{idnum_value}</b>
            """.format(
                PARAM=PARAM,
                which_idnum=which_idnum,
                idnum_value=idnum_value,
                id_desc=pls.get_id_desc(which_idnum),
            )
        else:
            warning = ""
            patient_picker_or_label = """
                ID number: {which_idnum_picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}"
                        value="{idnum_value}">
            """.format(
                PARAM=PARAM,
                which_idnum_picker=get_html_which_idnum_picker(
                    PARAM.WHICH_IDNUM, selected=which_idnum),
                idnum_value="" if idnum_value is None else idnum_value,
            )
        return pls.WEBSTART + """
            {user}
            <h1>Completely erase patient and associated tasks</h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.DELETE_PATIENT}">
                {patient_picker_or_label}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Erase patient and tasks">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            patient_picker_or_label=patient_picker_or_label,
            PARAM=PARAM,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=get_url_main_menu(),
            tasks=tasks,
        ) + WEBEND
    if not patient_server_pks:
        return fail_with_error_stay_logged_in("No such patient found.")
    # If we get here, we'll do the erasure.
    # Delete tasks (with subtables)
    for cls in get_all_task_classes():
        tablename = cls.tablename
        serverpks = cls.get_task_pks_for_patient_deletion(which_idnum,
                                                          idnum_value)
        for serverpk in serverpks:
            task = task_factory(tablename, serverpk)
            task.delete_entirely()
    # Delete patients
    for ppk in patient_server_pks:
        pls.db.db_exec("DELETE FROM patient WHERE _pk = ?", ppk)
        audit("Patient deleted", patient_server_pk=ppk)
    msg = "Patient with idnum{} = {} and associated tasks DELETED".format(
        which_idnum, idnum_value)
    audit(msg)
    return simple_success(msg)


def info_html_for_patient_edit(title: str,
                               display: str,
                               param: str,
                               value: Optional[str],
                               oldvalue: Optional[str]) -> str:
    different = value != oldvalue
    newblank = (value is None or value == "")
    oldblank = (oldvalue is None or oldvalue == "")
    changetonull = different and (newblank and not oldblank)
    titleclass = ' class="important"' if changetonull else ''
    spanclass = ' class="important"' if different else ''
    return """
        <span{titleclass}>{title}:</span> <span{spanclass}>{display}</span><br>
        <input type="hidden" name="{param}" value="{value}">
    """.format(
        titleclass=titleclass,
        title=title,
        spanclass=spanclass,
        display=display,
        param=param,
        value=value,
    )


def edit_patient(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    # Inputs. We operate with text, for HTML reasons.
    patient_server_pk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    changes = {
        "forename": ws.get_cgi_parameter_str(form, PARAM.FORENAME, default=""),
        "surname": ws.get_cgi_parameter_str(form, PARAM.SURNAME, default=""),
        "dob": ws.get_cgi_parameter_datetime(form, PARAM.DOB),
        "sex": ws.get_cgi_parameter_str(form, PARAM.SEX, default=""),
        "address": ws.get_cgi_parameter_str(form, PARAM.ADDRESS, default=""),
        "gp": ws.get_cgi_parameter_str(form, PARAM.GP, default=""),
        "other": ws.get_cgi_parameter_str(form, PARAM.OTHER, default=""),
    }
    idnum_changes = {}  # type: Dict[int, int]  # which_idnum, idnum_value
    if changes["forename"]:
        changes["forename"] = changes["forename"].upper()
    if changes["surname"]:
        changes["surname"] = changes["surname"].upper()
    changes["dob"] = format_datetime(
        changes["dob"], DateFormat.ISO8601_DATE_ONLY, default="")
    for n in pls.get_which_idnums():
        val = ws.get_cgi_parameter_int(form, PARAM.IDNUM_PREFIX + str(n))
        if val is not None:
            idnum_changes[n] = val
    # Calculations
    n_confirmations = 2
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient = Patient(patient_server_pk)
    if patient.get_pk() is None:
        return fail_with_error_stay_logged_in(
            "No such patient found.")
    if not patient.is_preserved():
        return fail_with_error_stay_logged_in(
            "Patient record is still live on tablet; cannot edit.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
            gen_tasks_using_patient(
                patient.id, patient.get_device_id(), patient.get_era()))
        if confirmation_sequence > 0:
            warning = """
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO ALTER THIS PATIENT
                    RECORD (AFFECTING ASSOCIATED TASKS)?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            details = (
                info_html_for_patient_edit("Forename", changes["forename"],
                                           PARAM.FORENAME, changes["forename"],
                                           patient.forename) +
                info_html_for_patient_edit("Surname", changes["surname"],
                                           PARAM.SURNAME, changes["surname"],
                                           patient.surname) +
                info_html_for_patient_edit("DOB", changes["dob"],
                                           PARAM.DOB, changes["dob"],
                                           patient.dob) +
                info_html_for_patient_edit("Sex", changes["sex"],
                                           PARAM.SEX, changes["sex"],
                                           patient.sex) +
                info_html_for_patient_edit("Address", changes["address"],
                                           PARAM.ADDRESS, changes["address"],
                                           patient.address) +
                info_html_for_patient_edit("GP", changes["gp"],
                                           PARAM.GP, changes["gp"],
                                           patient.gp) +
                info_html_for_patient_edit("Other", changes["other"],
                                           PARAM.OTHER, changes["other"],
                                           patient.other)
            )
            for n in pls.get_which_idnums():
                oldvalue = patient.get_idnum_value(n)
                newvalue = idnum_changes.get(n, None)
                if newvalue is None:
                    newvalue = oldvalue
                desc = pls.get_id_desc(n)
                details += info_html_for_patient_edit(
                    "ID number {} ({})".format(n, desc),
                    str(newvalue),
                    PARAM.IDNUM_PREFIX + str(n),
                    str(newvalue),
                    str(oldvalue))
        else:
            warning = ""
            dob_for_html = format_datetime(
                patient.dob, DateFormat.ISO8601_DATE_ONLY, default="")
            details = """
                Forename: <input type="text" name="{PARAM.FORENAME}"
                                value="{forename}"><br>
                Surname: <input type="text" name="{PARAM.SURNAME}"
                                value="{surname}"><br>
                DOB: <input type="date" name="{PARAM.DOB}"
                                value="{dob}"><br>
                Sex: {sex_picker}<br>
                Address: <input type="text" name="{PARAM.ADDRESS}"
                                value="{address}"><br>
                GP: <input type="text" name="{PARAM.GP}"
                                value="{gp}"><br>
                Other: <input type="text" name="{PARAM.OTHER}"
                                value="{other}"><br>
            """.format(
                PARAM=PARAM,
                forename=patient.forename or "",
                surname=patient.surname or "",
                dob=dob_for_html,
                sex_picker=get_html_sex_picker(param=PARAM.SEX,
                                               selected=patient.sex,
                                               offer_all=False),
                address=patient.address or "",
                gp=patient.gp or "",
                other=patient.other or "",
            )
            for n in pls.get_which_idnums():
                details += """
                    ID number {n} ({desc}):
                    <input type="number" name="{paramprefix}{n}"
                            value="{value}"><br>
                """.format(
                    n=n,
                    desc=pls.get_id_desc(n),
                    paramprefix=PARAM.IDNUM_PREFIX,
                    value=patient.get_idnum_value(n),
                )
        return pls.WEBSTART + """
            {user}
            <h1>Edit finalized patient details</h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.EDIT_PATIENT}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{patient_server_pk}">
                {details}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Change patient details">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            PARAM=PARAM,
            ACTION=ACTION,
            patient_server_pk=patient_server_pk,
            details=details,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=get_url_main_menu(),
            tasks=tasks,
        ) + WEBEND
    # Line up the changes and validate, but DO NOT SAVE THE PATIENT as yet.
    changemessages = []
    for k, v in changes.items():
        if v == "":
            v = None
        oldval = getattr(patient, k)
        if v is None and oldval == "":
            # Nothing really changing!
            continue
        if v != oldval:
            changemessages.append(" {key}, {oldval} → {newval}".format(
                key=k,
                oldval=oldval,
                newval=v
            ))
            setattr(patient, k, v)
    for which_idnum, idnum_value in idnum_changes.items():
        oldvalue = patient.get_idnum_value(which_idnum)
        if idnum_value != oldvalue:
            patient.set_idnum_value(which_idnum, idnum_value)
    # Valid?
    if (not patient.satisfies_upload_id_policy() or
            not patient.satisfies_finalize_id_policy()):
        return fail_with_error_stay_logged_in(
            "New version does not satisfy uploading or finalizing policy; "
            "no changes made.")
    # Anything to do?
    if not changemessages:
        return simple_success("No changes made.")
    # If we get here, we'll make the change.
    patient.save()
    msg = "Patient details edited. Changes: "
    msg += "; ".join(changemessages) + "."
    patient.apply_special_note(msg, session.user_id,
                               audit_msg="Patient details edited")
    for task in gen_tasks_using_patient(patient.id,
                                        patient.get_device_id(),
                                        patient.get_era()):
        # Patient details changed, so resend any tasks via HL7
        task.delete_from_hl7_message_log()
    return simple_success(msg)


def task_list_from_generator(generator: Iterable[Task]) -> str:
    tasklist_html = ""
    for task in generator:
        tasklist_html += task.get_task_list_row()
    return """
        {TASK_LIST_HEADER}
        {tasklist_html}
        {TASK_LIST_FOOTER}
    """.format(
        TASK_LIST_HEADER=TASK_LIST_HEADER,
        tasklist_html=tasklist_html,
        TASK_LIST_FOOTER=TASK_LIST_FOOTER,
    )


def forcibly_finalize(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Force-finalize all live (_era == ERA_NOW) records from a device."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    device_id = ws.get_cgi_parameter_int(form, PARAM.DEVICE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    if confirmation_sequence > 0 and device_id is None:
        return fail_with_error_stay_logged_in("Device not specified.")
    d = None
    if device_id is not None:
        # A device was asked for...
        d = Device(device_id)
        if not d.is_valid():
            # ... but not found
            return fail_with_error_stay_logged_in("No such device found.")
        device_id = d.id
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if device_id is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                gen_tasks_live_on_tablet(device_id))
        if confirmation_sequence > 0:
            warning = """
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO FORCIBLY
                    PRESERVE/FINALIZE RECORDS FROM THIS DEVICE?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            device_picker_or_label = """
                <input type="hidden" name="{PARAM.DEVICE}"
                        value="{device_id}">
                <b>{device_nicename}</b>
            """.format(
                PARAM=PARAM,
                device_id=device_id,
                device_nicename=(ws.webify(d.get_friendly_name_and_id())
                                 if d is not None else ''),
            )
        else:
            warning = ""
            device_picker_or_label = get_device_filter_dropdown(device_id)
        return pls.WEBSTART + """
            {user}
            <h1>
                Forcibly preserve/finalize records from a given tablet device
            </h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.FORCIBLY_FINALIZE}">
                Device: {device_picker_or_label}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Forcibly finalize records from this device">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            device_picker_or_label=device_picker_or_label,
            PARAM=PARAM,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=get_url_main_menu(),
            tasks=tasks
        ) + WEBEND

    # If we get here, we'll do the forced finalization.
    # Force-finalize tasks (with subtables)
    tables = [
        # non-task but tablet-based tables
        Patient.__tablename__,
        Blob.__tablename__,
        DeviceStoredVar.__tablename__,
    ]
    for cls in get_all_task_classes():
        tables.append(cls.tablename)
        tables.extend(cls.get_extra_table_names())
    for t in tables:
        cc_db.forcibly_preserve_client_table(t, device_id, pls.session.user_id)
    # Field names are different in server-side tables, so they need special
    # handling:
    forcibly_preserve_special_notes(device_id)
    # OK, done.
    msg = "Live records for device {} forcibly finalized".format(device_id)
    audit(msg)
    return simple_success(msg)


# =============================================================================
# Main HTTP processor
# =============================================================================

# -------------------------------------------------------------------------
# Main set of action mappings.
# All functions take parameters (session, form)
# -------------------------------------------------------------------------
ACTIONDICT = {
    # Data dumps
    ACTION.OFFER_BASIC_DUMP: offer_basic_dump,
    ACTION.BASIC_DUMP: basic_dump,
    ACTION.OFFER_TABLE_DUMP: offer_table_dump,
    ACTION.TABLE_DUMP: serve_table_dump,

    # Amending and deleting data
    ACTION.ADD_SPECIAL_NOTE: add_special_note,
    ACTION.ERASE_TASK: erase_task,
    ACTION.DELETE_PATIENT: delete_patient,
    ACTION.EDIT_PATIENT: edit_patient,
    ACTION.FORCIBLY_FINALIZE: forcibly_finalize,
}



# =============================================================================
# Functions suitable for calling from the command line or webview
# =============================================================================

def write_descriptions_comments(file: typing.io.TextIO,
                                include_views: bool = False) -> None:
    """Save database fields/comments to a file in HTML format."""

    sql = """
        SELECT
            t.table_type, c.table_name, c.column_name, c.column_type,
            c.is_nullable, c.column_comment
        FROM information_schema.columns c
        INNER JOIN information_schema.tables t
            ON c.table_schema = t.table_schema
            AND c.table_name = t.table_name
        WHERE (
                t.table_type='BASE TABLE'
    """
    if include_views:
        sql += """
                OR t.table_type='VIEW'
        """
    sql += """
            )
            AND c.table_schema='{}' /* database name */
    """.format(
        pls.DB_NAME
    )
    rows = pls.db.fetchall(sql)
    print(COMMON_HEAD, file=file)
    # don't used fixed-width tables; they truncate contents
    print("""
            <table>
                <tr>
                    <th>Table type</th>
                    <th>Table</th>
                    <th>Column</th>
                    <th>Column type</th>
                    <th>May be NULL</th>
                    <th>Comment</th>
                </tr>
    """, file=file)
    for row in rows:
        outstring = "<tr>"
        for i in range(len(row)):
            outstring += "<td>{}</td>".format(ws.webify(row[i]))
        outstring += "</tr>"
        print(outstring, file=file)
    print("""
            </table>
        </body>
    """, file=file)

    # Other methods:
    # - To view columns with comments:
    #        SHOW FULL COLUMNS FROM tablename;
    # - or other methods at http://stackoverflow.com/questions/6752169


def get_descriptions_comments_html(include_views: bool = False) -> str:
    """Returns HTML of database field descriptions/comments."""
    f = io.StringIO()
    write_descriptions_comments(f, include_views)
    return f.getvalue()


# =============================================================================
# Unit tests
# =============================================================================

def webview_unit_tests() -> None:
    """Unit tests for camcops.py"""
    session = CamcopsSession()
    form = cgi.FieldStorage()
    # suboptimal tests, as form isn't tailed to these things

    # skip: ask_user
    # skip: ask_user_password
    unit_test_ignore("", login_failed, "test_redirect")
    unit_test_ignore("", account_locked, get_now_localtz(), "test_redirect")
    unit_test_ignore("", fail_not_user, "test_action", "test_redirect")
    unit_test_ignore("", fail_not_authorized_for_task)
    unit_test_ignore("", fail_task_not_found)
    unit_test_ignore("", fail_not_manager, "test_action")
    unit_test_ignore("", fail_unknown_action, "test_action")

    for ignorekey, func in ACTIONDICT.items():
        if func.__name__ == "crash":
            continue  # maybe skip this one!
        unit_test_ignore("", func, session, form)

    unit_test_ignore("", get_tracker, session, form)
    unit_test_ignore("", get_clinicaltextview, session, form)
    unit_test_ignore("", tsv_escape, "x\t\nhello")
    unit_test_ignore("", tsv_escape, None)
    unit_test_ignore("", tsv_escape, 3.45)
    # ignored: get_tsv_header_from_dict
    # ignored: get_tsv_line_from_dict

    unit_test_ignore("", get_url_next_page, 100)
    unit_test_ignore("", get_url_last_page, 100)
    unit_test_ignore("", get_url_introspect, "test_filename")
    unit_test_ignore("", redirect_to, "test_location")
    # ignored: main_http_processor
    # ignored: upgrade_database
    # ignored: make_tables

    f = io.StringIO()
    unit_test_ignore("", write_descriptions_comments, f, False)
    unit_test_ignore("", write_descriptions_comments, f, True)
    # ignored: export_descriptions_comments
    unit_test_ignore("", get_database_title)
    # ignored: reset_storedvars
    # ignored: make_summary_tables
    # ignored: make_superuser
    # ignored: reset_password
    # ignored: enable_user_cli