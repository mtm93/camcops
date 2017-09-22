#!/usr/bin/env python
# camcops_server/cc_modules/cc_db.py

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
from typing import Any, Dict, Iterable, List, Union, Type, TypeVar

from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_db as rnc_db
from cardinal_pythonlib.rnc_db import FIELDSPECLIST_TYPE
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_columns
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer
# from sqlalchemy.sql.type_api import TypeEngine

from .cc_constants import DateFormat, ERA_NOW
from .cc_dt import format_datetime
from .cc_sqla_coltypes import (
    CamcopsColumn,
    PendulumDateTimeAsIsoTextColType,
    EraColType,
    PermittedValueChecker,
    RelationshipInfo,
    SemanticVersionColType,
)
from .cc_tsv import TsvChunk
from .cc_xml import (
    make_xml_branches_from_blobs,
    make_xml_branches_from_columns,
    XmlElement,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

T = TypeVar('T')


# =============================================================================
# Base classes implementing common fields
# =============================================================================

class GenericTabletRecordMixin(object):
    __tablename__ = None  # type: str  # sorts out some mixin type checking

    # -------------------------------------------------------------------------
    # On the server side:
    # -------------------------------------------------------------------------

    # Plain columns

    # noinspection PyMethodParameters
    @declared_attr
    def _pk(cls) -> Column:
        return Column(
            "_pk", Integer,
            primary_key=True, autoincrement=True, index=True,
            comment="(SERVER) Primary key (on the server)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _device_id(cls) -> Column:
        return Column(
            "_device_id", Integer, ForeignKey("_security_devices.id"),
            nullable=False, index=True,
            comment="(SERVER) ID of the source tablet device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _era(cls) -> Column:
        return Column(
            "_era", EraColType,
            nullable=False, index=True,
            comment="(SERVER) 'NOW', or when this row was preserved and "
                    "removed from the source device (UTC ISO 8601)",
        )
        # ... note that _era is textual so that plain comparison
        # with "=" always works, i.e. no NULLs -- for USER comparison too, not
        # just in CamCOPS code

    # noinspection PyMethodParameters
    @declared_attr
    def _current(cls) -> Column:
        return Column(
            "_current", Boolean,
            nullable=False, index=True,
            comment="(SERVER) Is the row current (1) or not (0)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_added_exact(cls) -> Column:
        return Column(
            "_when_added_exact", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time this row was added (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_added_batch_utc(cls) -> Column:
        return Column(
            "_when_added_batch_utc", DateTime,
            comment="(SERVER) Date/time of the upload batch that added this "
                    "row (DATETIME in UTC)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _adding_user_id(cls) -> Column:
        return Column(
            "_adding_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that added this row",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_removed_exact(cls) -> Column:
        return Column(
            "_when_removed_exact", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time this row was removed, i.e. made "
                    "not current (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_removed_batch_utc(cls) -> Column:
        return Column(
            "_when_removed_batch_utc", DateTime,
            comment="(SERVER) Date/time of the upload batch that removed "
                    "this row (DATETIME in UTC)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _removing_user_id(cls) -> Column:
        return Column(
            "_removing_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that removed this row"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _preserving_user_id(cls) -> Column:
        return Column(
            "_preserving_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that preserved this row"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _forcibly_preserved(cls) -> Column:
        return Column(
            "_forcibly_preserved", Boolean,
            comment="(SERVER) Forcibly preserved by superuser (rather than "
                    "normally preserved by tablet)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _predecessor_pk(cls) -> Column:
        return Column(
            "_predecessor_pk", Integer,
            comment="(SERVER) PK of predecessor record, prior to modification"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _successor_pk(cls) -> Column:
        return Column(
            "_successor_pk", Integer,
            comment="(SERVER) PK of successor record  (after modification) "
                    "or NULL (whilst live, or after deletion)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erased(cls) -> Column:
        return Column(
            "_manually_erased", Boolean,
            comment="(SERVER) Record manually erased (content destroyed)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erased_at(cls) -> Column:
        return Column(
            "_manually_erased_at", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time of manual erasure (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erasing_user_id(cls) -> Column:
        return Column(
            "_manually_erasing_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that erased this row manually"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _camcops_version(cls) -> Column:
        return Column(
            "_camcops_version", SemanticVersionColType,
            comment="(SERVER) CamCOPS version number of the uploading device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _addition_pending(cls) -> Column:
        return Column(
            "_addition_pending", Boolean,
            nullable=False,
            comment="(SERVER) Addition pending?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _removal_pending(cls) -> Column:
        return Column(
            "_removal_pending", Boolean,
            comment="(SERVER) Removal pending?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _group_id(cls) -> Column:
        return Column(
            "_group_id", Integer, ForeignKey("_security_groups.id"),
            nullable=False, index=True,
            comment="(SERVER) ID of group to which this record belongs"
        )

    RESERVED_FIELDS = [  # fields that tablets can't upload
        "_pk",
        "_device_id",
        "_era",
        "_current",
        "_when_added_exact",
        "_when_added_batch_utc",
        "_adding_user_id",
        "_when_removed_exact",
        "_when_removed_batch_utc",
        "_removing_user_id",
        "_preserving_user_id",
        "_forcibly_preserved",
        "_predecessor_pk",
        "_successor_pk",
        "_manually_erased",
        "_manually_erased_at",
        "_manually_erasing_user_id",
        "_camcops_version",
        "_addition_pending",
        "_removal_pending",
        "_group_id",
    ]

    # -------------------------------------------------------------------------
    # Fields that *all* client tables have:
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @declared_attr
    def id(cls) -> Column:
        return Column(
            "id", Integer,
            nullable=False, index=True,
            comment="(TASK) Primary key (task ID) on the tablet device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def when_last_modified(cls) -> Column:
        return Column(
            "when_last_modified", PendulumDateTimeAsIsoTextColType,
            comment="(STANDARD) Date/time this row was last modified on the "
                    "source tablet device (ISO 8601)"
            # *** WHEN ALEMBIC UP: INDEX THIS: USED BY DATABASE UPLOAD SCRIPT.
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _move_off_tablet(cls) -> Column:
        return Column(
            "_move_off_tablet", Boolean,
            comment="(SERVER/TABLET) Record-specific preservation pending?"
        )

    # Relationships

    # noinspection PyMethodParameters
    @declared_attr
    def _device(cls) -> RelationshipProperty:
        return relationship("Device")

    # noinspection PyMethodParameters
    @declared_attr
    def _adding_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._adding_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _removing_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._removing_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _preserving_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._preserving_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erasing_user(cls) -> RelationshipProperty:
        return relationship("User",
                            foreign_keys=[cls._manually_erasing_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _group(cls) -> RelationshipProperty:
        return relationship("Group",
                            foreign_keys=[cls._group_id])

    def _get_xml_root(self,
                      skip_attrs: List[str] = None,
                      include_plain_columns: bool=True,
                      include_blobs: bool = True,
                      sort_by_attr: bool = True) -> XmlElement:
        """
        Called to create an XML root object for records ancillary to Task
        objects. Tasks themselves use a more complex mechanism.
        """
        skip_attrs = skip_attrs or []  # type: List[str]
        # "__tablename__" will make the type checker complain, as we're
        # defining a function for a mixin that assumes it's mixed in to a
        # SQLAlchemy Base-derived class
        # noinspection PyUnresolvedReferences
        return XmlElement(
            name=self.__tablename__,
            value=self._get_xml_branches(
                skip_attrs=skip_attrs,
                include_plain_columns=include_plain_columns,
                include_blobs=include_blobs,
                sort_by_attr=sort_by_attr
            )
        )

    def _get_xml_branches(self,
                          skip_attrs: List[str],
                          include_plain_columns: bool = True,
                          include_blobs: bool = True,
                          sort_by_attr: bool = True) -> List[XmlElement]:
        """
        Gets the values of SQLAlchemy columns as XmlElement objects.
        Optionally, find any SQLAlchemy relationships that are relationships
        to Blob objects, and include them too.

        Used by _get_xml_root above, but also by Tasks themselves.
        """
        # log.critical("_get_xml_branches for {!r}", self)
        skip_attrs = skip_attrs or []  # type: List[str]
        branches = []  # type: List[XmlElement]
        if include_plain_columns:
            branches += make_xml_branches_from_columns(self,
                                                       skip_fields=skip_attrs)
        if include_blobs:
            branches += make_xml_branches_from_blobs(self,
                                                     skip_fields=skip_attrs)
        if sort_by_attr:
            branches.sort(key = lambda el: el.name)
        # log.critical("... branches for {!r}: {!r}", self, branches)
        return branches

    def _get_core_tsv_chunk(self, heading_prefix: str = "") -> TsvChunk:
        headings = []  # type: List[str]
        row = []  # type: List[Any]
        for attrname, column in gen_columns(self):
            value = getattr(self, attrname)
            headings.append(heading_prefix + attrname)
            row.append(value)
        return TsvChunk(
            filename_stem=self.__tablename__,
            headings=headings,
            rows=[row]
        )


# =============================================================================
# Relationships
# =============================================================================

def ancillary_relationship(
        parent_class_name: str,
        ancillary_class_name: str,
        ancillary_fk_to_parent_attr_name: str,
        ancillary_order_by_attr_name: str = None,
        read_only: bool = True) -> RelationshipProperty:
    """
    Implements a one-to-many relationship, i.e. one parent to many ancillaries.
    """
    parent_pk_attr_name = "id"  # always
    return relationship(
        ancillary_class_name,
        primaryjoin=(
            "and_("
            " remote({a}.{fk}) == foreign({p}.{pk}), "
            " remote({a}._device_id) == foreign({p}._device_id), "
            " remote({a}._era) == foreign({p}._era), "
            " remote({a}._current) == True "
            ")".format(
                a=ancillary_class_name,
                fk=ancillary_fk_to_parent_attr_name,
                p=parent_class_name,
                pk=parent_pk_attr_name,
            )
        ),
        uselist=True,
        order_by="{a}.{f}".format(a=ancillary_class_name,
                                  f=ancillary_order_by_attr_name),
        viewonly=read_only,
        info={RelationshipInfo.IS_ANCILLARY: True},
        # ... "info" is a user-defined dictionary; see
        # http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship.params.info  # noqa
        # http://docs.sqlalchemy.org/en/latest/orm/internals.html#MapperProperty.info  # noqa
    )


# =============================================================================
# Field creation assistance
# =============================================================================

# TypeEngineBase = TypeVar('TypeEngineBase', bound=TypeEngine)

def add_multiple_columns(
        cls: Type,
        prefix: str,
        start: int,
        end: int,
        coltype=Integer,
        # this type fails: Union[Type[TypeEngineBase], TypeEngine]
        # ... https://stackoverflow.com/questions/38106227
        # ... https://github.com/python/typing/issues/266
        colkwargs: Dict[str, Any] = None,
        comment_fmt: str = None,
        comment_strings: List[str] = None,
        minimum: Union[int, float] = None,
        maximum: Union[int, float] = None,
        pv: List[Any] = None) -> None:
    """
    Add a sequence of SQLAlchemy columns to a class.
    Called from a metaclass.

    Args:
        cls: class to which to add columns
        prefix: Fieldname will be prefix + str(n), where n defined as below.
        start: Start of range.
        end: End of range. Thus:
            ... i will range from 0 to (end - start) inclusive
            ... n will range from start to end inclusive
        coltype: SQLAlchemy column type, in either of these formats:
                Integer     general type: Type[TypeEngine] ?
                Integer()   general type: TypeEngine
        colkwargs: SQLAlchemy column arguments
            ... as in: Column(name, coltype, **colkwargs)
        comment_fmt: Format string defining field comments. Substitutable
            values are:
                {n}     field number (from range)
                {s}     comment_strings[i], or "" if out of range
        comment_strings: see comment_fmt
        minimum: minimum permitted value, or None
        maximum: maximum permitted value, or None
        pv: list of permitted values, or None
    """
    colkwargs = {} if colkwargs is None else colkwargs  # type: Dict[str, Any]
    comment_strings = comment_strings or []
    fieldspecs = []
    for n in range(start, end + 1):
        nstr = str(n)
        i = n - start
        colname = prefix + nstr
        if comment_fmt:
            s = ""
            if 0 <= i < len(comment_strings):
                s = comment_strings[i] or ""
            colkwargs["comment"] = comment_fmt.format(n=n, s=s)
        if minimum is not None or maximum is not None or pv is not None:
            colkwargs["permitted_value_checker"] = PermittedValueChecker(
                minimum=minimum,
                maximum=maximum,
                permitted_values=pv
            )
            setattr(cls, colname, CamcopsColumn(colname, coltype, **colkwargs))
        else:
            setattr(cls, colname, Column(colname, coltype, **colkwargs))

# =============================================================================
# Database routines.
# =============================================================================

def delete_from_table_by_pklist(tablename: str,
                                pkname: str,
                                pklist: Iterable[int]) -> None:
    query = "DELETE FROM {} WHERE {} = ?".format(tablename, pkname)
    for pk in pklist:
        pls.db.db_exec(query, pk)


# noinspection PyProtectedMember
def manually_erase_record_object_and_save(obj: T,
                                          table: str,
                                          fields: Iterable[str],
                                          user_id: int) -> None:
    """Manually erases a standard record and marks it so erased.
    The object remains _current, as a placeholder, but its contents are wiped.
    WRITES TO DATABASE."""
    if obj._pk is None or obj._era == ERA_NOW:
        return
    standard_task_fields = [x["name"] for x in STANDARD_TASK_FIELDSPECS]
    erasure_fields = [
        x
        for x in fields
        if x not in standard_task_fields
    ]
    rnc_db.blank_object(obj, erasure_fields)
    obj._current = False
    obj._manually_erased = True
    obj._manually_erased_at = format_datetime(pls.NOW_LOCAL_TZ,
                                              DateFormat.ISO8601)
    obj._manually_erasing_user_id = user_id
    pls.db.update_object_in_db(obj, table, fields)


def delete_subtable_records_common(tablename: str,
                                   pkname: str,
                                   fkname: str,
                                   fkvalue: Any,
                                   device_id: int,
                                   era: str) -> None:
    """Used to delete records entirely from the database."""
    pklist = get_server_pks_of_record_group(
        tablename, pkname, fkname, fkvalue, device_id, era)
    delete_from_table_by_pklist(tablename, pkname, pklist)


def erase_subtable_records_common(itemclass: Type[T],
                                  tablename: str,
                                  fieldnames: Iterable[str],
                                  pkname: str,
                                  fkname: str,
                                  fkvalue: Any,
                                  device_id: int,
                                  era: str,
                                  user_id: int) -> None:
    """Used to wipe objects and re-save them."""
    pklist = get_server_pks_of_record_group(
        tablename, pkname, fkname, fkvalue, device_id, era)
    items = pls.db.fetch_all_objects_from_db_by_pklist(
        itemclass, tablename, fieldnames, pklist, True)
    for i in items:
        manually_erase_record_object_and_save(i, tablename, fieldnames,
                                              user_id)


def forcibly_preserve_client_table(table: str,
                                   device_id: int,
                                   user_id: int) -> None:
    """WRITES TO DATABASE."""
    new_era = format_datetime(pls.NOW_UTC_NO_TZ, DateFormat.ERA)
    query = """
        UPDATE  {table}
        SET     _era = ?,
                _forcibly_preserved = 1,
                _preserving_user_id = ?
        WHERE   _device_id = ?
        AND     _era = '{now}'
    """.format(table=table, now=ERA_NOW)
    args = [
        new_era,
        user_id,
        device_id
    ]
    pls.db.db_exec(query, *args)


# =============================================================================
# More SQL
# =============================================================================

def create_or_update_table(tablename: str,
                           fieldspecs_with_cctype: FIELDSPECLIST_TYPE,
                           drop_superfluous_columns: bool = False) -> None:
    """Adds the sqltype to a set of fieldspecs using cctype, then creates the
    table."""
    add_sqltype_to_fieldspeclist_in_place(fieldspecs_with_cctype)
    pls.db.create_or_update_table(
        tablename, fieldspecs_with_cctype,
        drop_superfluous_columns=drop_superfluous_columns,
        dynamic=True,
        compressed=False)
    if not pls.db.mysql_table_using_barracuda(tablename):
        pls.db.mysql_convert_table_to_barracuda(tablename, compressed=False)


def create_standard_table(tablename: str,
                          fieldspeclist: FIELDSPECLIST_TYPE,
                          drop_superfluous_columns: bool = False) -> None:
    """Create a table and its associated current view."""
    create_or_update_table(tablename, fieldspeclist,
                           drop_superfluous_columns=drop_superfluous_columns)
    create_simple_current_view(tablename)


def create_standard_task_table(tablename: str,
                               fieldspeclist: FIELDSPECLIST_TYPE,
                               anonymous: bool = False,
                               drop_superfluous_columns: bool = False) -> None:
    """Create a task's table and its associated current view."""
    create_standard_table(tablename, fieldspeclist,
                          drop_superfluous_columns=drop_superfluous_columns)
    if anonymous:
        create_simple_current_view(tablename)
    else:
        create_task_current_view(tablename)


def create_standard_ancillary_table(
        tablename: str,
        fieldspeclist: FIELDSPECLIST_TYPE,
        ancillaryfk: str,
        tasktable: str,
        drop_superfluous_columns: bool = False) -> None:
    """Create an ancillary table and its associated current view."""
    create_standard_table(tablename, fieldspeclist,
                          drop_superfluous_columns=drop_superfluous_columns)
    create_ancillary_current_view(tablename, ancillaryfk, tasktable)


def create_simple_current_view(table: str) -> None:
    """Create a current view for a table."""
    pass
    # sql = """
    #     CREATE OR REPLACE VIEW {0}_current AS
    #     SELECT *
    #     FROM {0}
    #     WHERE _current
    # """.format(table)
    # pls.db.db_exec_literal(sql)


def create_task_current_view(tasktable: str) -> None:
    """Create tasks views that link to patient information (either giving the
    FK to the patient table, or bringing across more detail for convenience).

    Only to be used for non-anonymous tasks.
    """
    pass

    # # Simple view
    # sql = """
    #     CREATE OR REPLACE VIEW {0}_current AS
    #     SELECT {0}.*, patient._pk AS _patient_server_pk
    #     FROM {0}
    #     INNER JOIN patient
    #         ON {0}.patient_id = patient.id
    #         AND {0}._device_id = patient._device_id
    #         AND {0}._era = patient._era
    #     WHERE
    #         {0}._current
    #         AND patient._current
    # """.format(tasktable)
    # pls.db.db_exec_literal(sql)
    #
    # # View joined to patient info
    # sql = """
    #     CREATE OR REPLACE VIEW {0}_current_withpt AS
    #     SELECT
    #         {0}_current.*
    #         , patient_current.forename AS patient_forename
    #         , patient_current.surname AS patient_surname
    #         , patient_current.dob AS patient_dob
    #         , patient_current.sex AS patient_sex
    # """.format(tasktable)
    # for n in range(1, NUMBER_OF_IDNUMS + 1):
    #     sql += """
    #         , patient_current.idnum{0} AS patient_idnum{0}
    #     """.format(n)
    # sql += """
    #         , patient_current.address AS patient_address
    #         , patient_current.gp AS patient_gp
    #         , patient_current.other AS patient_other
    #     FROM {0}_current
    #     INNER JOIN patient_current
    #         ON {0}_current._patient_server_pk = patient_current._pk
    # """.format(tasktable)
    # pls.db.db_exec_literal(sql)
    # # MySQL can't add comments to view columns.


def create_ancillary_current_view(ancillarytable: str,
                                  ancillaryfk: str,
                                  tasktable: str) -> None:
    """Create an ancillary view that links to its task's table."""
    pass

    # sql = """
    #     CREATE OR REPLACE VIEW {1}_current AS
    #     SELECT {1}.*, {0}._pk AS _task_server_pk
    #     FROM {1}
    #     INNER JOIN {0}
    #         ON {1}.{2} = {0}.id
    #         AND {1}._device_id = {0}._device_id
    #         AND {1}._era = {0}._era
    #     WHERE
    #         {1}._current
    #         AND {0}._current
    # """.format(tasktable, ancillarytable, ancillaryfk)
    # pls.db.db_exec_literal(sql)


def create_summary_table_current_view_withpt(
        summarytable: str,
        basetable: str,
        summarytable_fkfieldname: str) -> None:
    """Create a current view for the summary table, in versions with simple
    (FK) or more detailed patient information.

    Only to be used for non-anonymous tasks.
    """
    pass

    # # Current view with patient ID
    # sql = """
    #     CREATE OR REPLACE VIEW {0}_current AS
    #     SELECT {0}.*, patient._pk AS _patient_server_pk
    #     FROM {0}
    #     INNER JOIN {1}
    #         ON {0}.{2} = {1}._pk
    #     INNER JOIN patient
    #         ON {1}.patient_id = patient.id
    #         AND {1}._device_id = patient._device_id
    #         AND {1}._era = patient._era
    #     WHERE
    #         {1}._current
    #         AND patient._current
    # """.format(summarytable, basetable, summarytable_fkfieldname)
    # pls.db.db_exec_literal(sql)
    #
    # # Current view with patient info
    # sql = """
    #     CREATE OR REPLACE VIEW {0}_current_withpt AS
    #     SELECT
    #         {0}_current.*
    #         , patient_current.forename AS patient_forename
    #         , patient_current.surname AS patient_surname
    #         , patient_current.dob AS patient_dob
    #         , patient_current.sex AS patient_sex
    # """.format(summarytable)
    # for n in range(1, NUMBER_OF_IDNUMS + 1):
    #     sql += """
    #         , patient_current.idnum{0} AS patient_idnum{0}
    #     """.format(n)
    # sql += """
    #         , patient_current.address AS patient_address
    #         , patient_current.gp AS patient_gp
    #         , patient_current.other AS patient_other
    #     FROM {0}_current
    #     INNER JOIN patient_current
    #         ON {0}_current._patient_server_pk = patient_current._pk
    # """.format(summarytable)
    # pls.db.db_exec_literal(sql)
