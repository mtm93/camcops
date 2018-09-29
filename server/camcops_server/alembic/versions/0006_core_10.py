#!/usr/bin/env python
# camcops_server/alembic/versions/0006.py

"""
CORE-10

Revision ID: 0006
Revises: 0005
Creation date: 2018-09-28 11:17:38.988418

DATABASE REVISION SCRIPT

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
"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
import camcops_server.cc_modules.cc_sqla_coltypes


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('core10',
    sa.Column('q1', sa.Integer(), nullable=True),
    sa.Column('q2', sa.Integer(), nullable=True),
    sa.Column('q3', sa.Integer(), nullable=True),
    sa.Column('q4', sa.Integer(), nullable=True),
    sa.Column('q5', sa.Integer(), nullable=True),
    sa.Column('q6', sa.Integer(), nullable=True),
    sa.Column('q7', sa.Integer(), nullable=True),
    sa.Column('q8', sa.Integer(), nullable=True),
    sa.Column('q9', sa.Integer(), nullable=True),
    sa.Column('q10', sa.Integer(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('when_created', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=False),
    sa.Column('when_firstexit', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('firstexit_is_finish', sa.Boolean(), nullable=True),
    sa.Column('firstexit_is_abort', sa.Boolean(), nullable=True),
    sa.Column('editing_time_s', sa.Float(), nullable=True),
    sa.Column('_pk', sa.Integer(), nullable=False),
    sa.Column('_device_id', sa.Integer(), nullable=False),
    sa.Column('_era', sa.String(length=32), nullable=False),
    sa.Column('_current', sa.Boolean(), nullable=False),
    sa.Column('_when_added_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_when_added_batch_utc', sa.DateTime(), nullable=True),
    sa.Column('_adding_user_id', sa.Integer(), nullable=True),
    sa.Column('_when_removed_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_when_removed_batch_utc', sa.DateTime(), nullable=True),
    sa.Column('_removing_user_id', sa.Integer(), nullable=True),
    sa.Column('_preserving_user_id', sa.Integer(), nullable=True),
    sa.Column('_forcibly_preserved', sa.Boolean(), nullable=True),
    sa.Column('_predecessor_pk', sa.Integer(), nullable=True),
    sa.Column('_successor_pk', sa.Integer(), nullable=True),
    sa.Column('_manually_erased', sa.Boolean(), nullable=True),
    sa.Column('_manually_erased_at', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_manually_erasing_user_id', sa.Integer(), nullable=True),
    sa.Column('_camcops_version', camcops_server.cc_modules.cc_sqla_coltypes.SemanticVersionColType(length=147), nullable=True),
    sa.Column('_addition_pending', sa.Boolean(), nullable=False),
    sa.Column('_removal_pending', sa.Boolean(), nullable=True),
    sa.Column('_group_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('when_last_modified', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_move_off_tablet', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['_adding_user_id'], ['_security_users.id'], name=op.f('fk_core10__adding_user_id')),
    sa.ForeignKeyConstraint(['_device_id'], ['_security_devices.id'], name=op.f('fk_core10__device_id')),
    sa.ForeignKeyConstraint(['_group_id'], ['_security_groups.id'], name=op.f('fk_core10__group_id')),
    sa.ForeignKeyConstraint(['_manually_erasing_user_id'], ['_security_users.id'], name=op.f('fk_core10__manually_erasing_user_id')),
    sa.ForeignKeyConstraint(['_preserving_user_id'], ['_security_users.id'], name=op.f('fk_core10__preserving_user_id')),
    sa.ForeignKeyConstraint(['_removing_user_id'], ['_security_users.id'], name=op.f('fk_core10__removing_user_id')),
    sa.PrimaryKeyConstraint('_pk', name=op.f('pk_core10')),
    mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
    mysql_engine='InnoDB',
    mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('core10', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_core10__current'), ['_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10__device_id'), ['_device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10__era'), ['_era'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10__group_id'), ['_group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10__pk'), ['_pk'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_core10_when_last_modified'), ['when_last_modified'], unique=False)

    # ### end Alembic commands ###


# noinspection PyPep8,PyTypeChecker
def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table('core10', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_core10_when_last_modified'))
        batch_op.drop_index(batch_op.f('ix_core10_patient_id'))
        batch_op.drop_index(batch_op.f('ix_core10_id'))
        batch_op.drop_index(batch_op.f('ix_core10__pk'))
        batch_op.drop_index(batch_op.f('ix_core10__group_id'))
        batch_op.drop_index(batch_op.f('ix_core10__era'))
        batch_op.drop_index(batch_op.f('ix_core10__device_id'))
        batch_op.drop_index(batch_op.f('ix_core10__current'))

    op.drop_table('core10')
    # ### end Alembic commands ###
