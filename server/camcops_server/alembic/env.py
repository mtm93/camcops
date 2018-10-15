#!/usr/bin/env python

"""
camcops_server/alembic/env.py

===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

**This file configures and runs Alembic.**

It is loaded directly by Alembic, via a pseudo-"main" environment.

"""

# =============================================================================
# Imports
# =============================================================================

import logging
from typing import Iterable, Generator, List, Tuple, Union

from alembic import context
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations.ops import (
    AlterColumnOp,
    DowngradeOps,
    ModifyTableOps,
    MigrationScript,
    OpContainer,
    UpgradeOps,
)
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_url
from sqlalchemy import engine_from_config, pool
from sqlalchemy.dialects.mysql.types import LONGTEXT, TINYINT
from sqlalchemy.sql.sqltypes import Boolean, UnicodeText
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.schema import MetaData

# No relative imports from within the Alembic zone.
from camcops_server.cc_modules.cc_baseconstants import ALEMBIC_VERSION_TABLE
from camcops_server.cc_modules.cc_config import get_default_config_from_os_env
from camcops_server.cc_modules.cc_sqlalchemy import Base
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa

log = logging.getLogger(__name__)


# =============================================================================
# Sort out unwanted autogenerated things; see
# - https://alembic.zzzcomputing.com/en/latest/api/autogenerate.html
# - https://alembic.zzzcomputing.com/en/latest/cookbook.html
# - https://bitbucket.org/zzzeek/alembic/issues/46/mysqltinyint-display_width-1-vs-saboolean  # noqa
# - http://alembic.zzzcomputing.com/en/latest/api/autogenerate.html
# =============================================================================

def debug_op_object(op: Union[List, OpContainer, Tuple],
                    level: int = 0) -> str:
    """
    Describes a :class:`OpContainer`.
    """
    lines = []  # type: List[str]
    spacer = "    " * level
    thisobj = spacer + str(op)
    if isinstance(op, ModifyTableOps):
        thisobj += " for table {}".format(op.table_name)
    if isinstance(op, AlterColumnOp):
        thisobj += " for column {}.{}".format(op.table_name, op.column_name)
    lines.append(thisobj)
    if hasattr(op, "ops"):
        for sub_op in op.ops:
            lines.append(debug_op_object(sub_op, level + 1))
    return "\n".join(lines)


def types_equivalent(database_type: TypeEngine,
                     metadata_type: TypeEngine) -> bool:
    """
    Are two types equivalent?

    Args:
        database_type: a type reflected from the database
        metadata_type: a type from the SQLAlchemy metadata

    Returns:
        equivalent, in a non-trivial way?

    Specifically, it detects:

    - MySQL ``TINYINT(1)`` is equivalent to SQLAlchemy ``Boolean()``, because
      ``TINYINT(1)`` is the correct instantiation of ``Boolean()``.

    - ``LONGTEXT(collation='utf8mb4_unicode_ci')`` is the MySQL database
      version of ``UnicodeText(length=4294967295)``
    """
    if (isinstance(database_type, TINYINT) and
            database_type.display_width == 1 and
            isinstance(metadata_type, Boolean)):
        return True

    if (isinstance(database_type, LONGTEXT) and
            database_type.collation == 'utf8mb4_unicode_ci' and
            isinstance(metadata_type, UnicodeText) and
            metadata_type.length == 4294967295):
        return True

    return False


def filter_column_ops(column_ops: Iterable[AlterColumnOp],
                      upgrade: bool) \
        -> Generator[AlterColumnOp, None, None]:
    """
    Generates column operations removing redundant changes from one type
    to an equivalent type, as judged by :func:`types_equivalent`.
    """
    method = "upgrade" if upgrade else "downgrade"

    for column_op in column_ops:
        if not isinstance(column_op, AlterColumnOp):
            yield column_op  # don't know what it is; yield it unmodified
            continue

        existing_type = column_op.existing_type
        modify_type = column_op.modify_type

        if upgrade:
            database_type = existing_type
            metadata_type = modify_type
        else:
            database_type = modify_type
            metadata_type = existing_type

        if types_equivalent(database_type=database_type,
                            metadata_type=metadata_type):
            log.info(
                "Skipping duff {} type change of {!r} to {!r} for "
                "{}.{}".format(
                    method,
                    existing_type, modify_type,
                    column_op.table_name, column_op.column_name
                ))
            continue  # skip this one!

        yield column_op


def filter_table_ops(table_ops: Iterable[ModifyTableOps], upgrade: bool) \
        -> Generator[ModifyTableOps, None, None]:
    """
    Generates table operations, removing those that fail
    :func:`filter_column_ops`.
    """
    method = "upgrade" if upgrade else "downgrade"
    log.warning("Filtering {} table operations".format(method))
    for table_op in table_ops:
        if not isinstance(table_op, ModifyTableOps):
            log.info("Don't understand: {!r}".format(table_op))
            yield table_op  # don't know what it is; yield it unmodified
            continue

        log.warning("Filtering {} ops for table: {}".format(
            method, table_op.table_name))
        table_op.ops = list(filter_column_ops(table_op.ops, upgrade=upgrade))
        if not table_op.ops:
            log.warning("Nothing to do for table: {}".format(
                table_op.table_name))
            continue

        yield table_op


# noinspection PyUnusedLocal
def process_revision_directives(context_: MigrationContext,  # empirically!
                                revision: Tuple[str],  # empirically!
                                directives: List[MigrationScript]) -> None:
    """
    Process autogenerated migration scripts and fix these problems.
    """
    if context_.config.cmd_opts.autogenerate:
        log.warning("Checking autogenerated operations")
        script = directives[0]

        # Check/filter our upgrade table ops.
        upgrade_ops = script.upgrade_ops  # type: UpgradeOps
        upgrade_ops.ops = list(filter_table_ops(upgrade_ops.ops, upgrade=True))

        # Check/filter our upgrade table ops.
        downgrade_ops = script.downgrade_ops  # type: DowngradeOps
        downgrade_ops.ops = list(filter_table_ops(downgrade_ops.ops,
                                                  upgrade=False))

        # If no changes to the schema are produced, don't generate a revision
        # file:
        log.info("upgrade_ops:\n{}".format(debug_op_object(upgrade_ops)))
        if upgrade_ops.is_empty():
            log.info("No changes; not generating a revision file.")
            directives[:] = []


# =============================================================================
# Migration functions
# =============================================================================

def run_migrations_offline(config: Config,
                           target_metadata: MetaData) -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well.  By skipping the Engine creation we
    don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    # RNC
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_as_batch=True,  # for SQLite mode; http://stackoverflow.com/questions/30378233  # noqa
        literal_binds=True,
        version_table=ALEMBIC_VERSION_TABLE,
        compare_type=True,
        # ... http://blog.code4hire.com/2017/06/setting-up-alembic-to-detect-the-column-length-change/  # noqa
        # ... https://eshlox.net/2017/08/06/alembic-migration-for-string-length-change/  # noqa

        # process_revision_directives=writer,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(config: Config,
                          target_metadata: MetaData) -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # RNC
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # for SQLite mode; http://stackoverflow.com/questions/30378233  # noqa
            version_table=ALEMBIC_VERSION_TABLE,
            compare_type=True,

            # process_revision_directives=writer,
            process_revision_directives=process_revision_directives,
        )
        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# Main commands
# =============================================================================
# We're in a pseudo-"main" environment.
# We need to reconfigure our logger, but __name__ is not "__main__".

def run_alembic() -> None:
    alembic_config = context.config  # type: Config
    target_metadata = Base.metadata
    camcops_config = get_default_config_from_os_env()
    dburl = camcops_config.db_url
    alembic_config.set_main_option('sqlalchemy.url', dburl)
    log.warning("Applying migrations to database at URL: {}".format(
        get_safe_url_from_url(dburl)))

    if context.is_offline_mode():
        run_migrations_offline(alembic_config, target_metadata)
    else:
        run_migrations_online(alembic_config, target_metadata)


main_only_quicksetup_rootlogger(level=logging.DEBUG)
# log.critical("IN CAMCOPS MIGRATION SCRIPT env.py")
run_alembic()
