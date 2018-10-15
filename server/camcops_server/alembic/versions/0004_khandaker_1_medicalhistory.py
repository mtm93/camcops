#!/usr/bin/env python

"""
camcops_server/alembic/versions/0004_khandaker_1_medicalhistory.py

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

khandaker_1_medicalhistory
Revision ID: 0004
Revises: 0003
Creation date: 2018-06-23 15:48:01.147404
DATABASE REVISION SCRIPT
"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
# import cardinal_pythonlib.sqlalchemy.list_types
import camcops_server.cc_modules.cc_sqla_coltypes


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('khandaker_1_medicalhistory',
    sa.Column('cancer_yn', sa.Boolean(), nullable=True),
    sa.Column('cancer_comment', sa.UnicodeText(), nullable=True),
    sa.Column('epilepsy_yn', sa.Boolean(), nullable=True),
    sa.Column('epilepsy_comment', sa.UnicodeText(), nullable=True),
    sa.Column('cva_headinjury_braintumour_yn', sa.Boolean(), nullable=True),
    sa.Column('cva_headinjury_braintumour_comment', sa.UnicodeText(), nullable=True),
    sa.Column('ms_pd_dementia_yn', sa.Boolean(), nullable=True),
    sa.Column('ms_pd_dementia_comment', sa.UnicodeText(), nullable=True),
    sa.Column('cerebralpalsy_otherbrain_yn', sa.Boolean(), nullable=True),
    sa.Column('cerebralpalsy_otherbrain_comment', sa.UnicodeText(), nullable=True),
    sa.Column('visual_impairment_yn', sa.Boolean(), nullable=True),
    sa.Column('visual_impairment_comment', sa.UnicodeText(), nullable=True),
    sa.Column('heart_disorder_yn', sa.Boolean(), nullable=True),
    sa.Column('heart_disorder_comment', sa.UnicodeText(), nullable=True),
    sa.Column('respiratory_yn', sa.Boolean(), nullable=True),
    sa.Column('respiratory_comment', sa.UnicodeText(), nullable=True),
    sa.Column('gastrointestinal_yn', sa.Boolean(), nullable=True),
    sa.Column('gastrointestinal_comment', sa.UnicodeText(), nullable=True),
    sa.Column('other_inflammatory_yn', sa.Boolean(), nullable=True),
    sa.Column('other_inflammatory_comment', sa.UnicodeText(), nullable=True),
    sa.Column('musculoskeletal_yn', sa.Boolean(), nullable=True),
    sa.Column('musculoskeletal_comment', sa.UnicodeText(), nullable=True),
    sa.Column('renal_urinary_yn', sa.Boolean(), nullable=True),
    sa.Column('renal_urinary_comment', sa.UnicodeText(), nullable=True),
    sa.Column('dermatological_yn', sa.Boolean(), nullable=True),
    sa.Column('dermatological_comment', sa.UnicodeText(), nullable=True),
    sa.Column('diabetes_yn', sa.Boolean(), nullable=True),
    sa.Column('diabetes_comment', sa.UnicodeText(), nullable=True),
    sa.Column('other_endocrinological_yn', sa.Boolean(), nullable=True),
    sa.Column('other_endocrinological_comment', sa.UnicodeText(), nullable=True),
    sa.Column('haematological_yn', sa.Boolean(), nullable=True),
    sa.Column('haematological_comment', sa.UnicodeText(), nullable=True),
    sa.Column('infections_yn', sa.Boolean(), nullable=True),
    sa.Column('infections_comment', sa.UnicodeText(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('firstexit_is_abort', sa.Boolean(), nullable=True),
    sa.Column('when_created', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=False),
    sa.Column('when_firstexit', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('editing_time_s', sa.Float(), nullable=True),
    sa.Column('firstexit_is_finish', sa.Boolean(), nullable=True),
    sa.Column('_adding_user_id', sa.Integer(), nullable=True),
    sa.Column('_addition_pending', sa.Boolean(), nullable=False),
    sa.Column('_when_added_batch_utc', sa.DateTime(), nullable=True),
    sa.Column('_removal_pending', sa.Boolean(), nullable=True),
    sa.Column('_predecessor_pk', sa.Integer(), nullable=True),
    sa.Column('_when_removed_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_when_removed_batch_utc', sa.DateTime(), nullable=True),
    sa.Column('_manually_erased_at', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_group_id', sa.Integer(), nullable=False),
    sa.Column('when_last_modified', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_current', sa.Boolean(), nullable=False),
    sa.Column('_manually_erasing_user_id', sa.Integer(), nullable=True),
    sa.Column('_when_added_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True),
    sa.Column('_manually_erased', sa.Boolean(), nullable=True),
    sa.Column('_device_id', sa.Integer(), nullable=False),
    sa.Column('_move_off_tablet', sa.Boolean(), nullable=True),
    sa.Column('_successor_pk', sa.Integer(), nullable=True),
    sa.Column('_removing_user_id', sa.Integer(), nullable=True),
    sa.Column('_preserving_user_id', sa.Integer(), nullable=True),
    sa.Column('_era', sa.String(length=32), nullable=False),
    sa.Column('_camcops_version', camcops_server.cc_modules.cc_sqla_coltypes.SemanticVersionColType(length=147), nullable=True),
    sa.Column('_forcibly_preserved', sa.Boolean(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_pk', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['_adding_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_1_medicalhistory__adding_user_id')),
    sa.ForeignKeyConstraint(['_device_id'], ['_security_devices.id'], name=op.f('fk_khandaker_1_medicalhistory__device_id')),
    sa.ForeignKeyConstraint(['_group_id'], ['_security_groups.id'], name=op.f('fk_khandaker_1_medicalhistory__group_id')),
    sa.ForeignKeyConstraint(['_manually_erasing_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_1_medicalhistory__manually_erasing_user_id')),
    sa.ForeignKeyConstraint(['_preserving_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_1_medicalhistory__preserving_user_id')),
    sa.ForeignKeyConstraint(['_removing_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_1_medicalhistory__removing_user_id')),
    sa.PrimaryKeyConstraint('_pk', name=op.f('pk_khandaker_1_medicalhistory')),
    # mysql_charset='utf8mb4',
    # mysql_collate='utf8mb4_unicode_ci',
    mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
    mysql_engine='InnoDB',
    mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('khandaker_1_medicalhistory', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory__current'), ['_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory__device_id'), ['_device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory__era'), ['_era'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory__group_id'), ['_group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory__pk'), ['_pk'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_1_medicalhistory_when_last_modified'), ['when_last_modified'], unique=False)

    # ### end Alembic commands ###


# noinspection PyPep8
def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('khandaker_1_medicalhistory', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory_when_last_modified'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory_patient_id'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory_id'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory__pk'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory__group_id'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory__era'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory__device_id'))
        batch_op.drop_index(batch_op.f('ix_khandaker_1_medicalhistory__current'))

    op.drop_table('khandaker_1_medicalhistory')
    # ### end Alembic commands ###
