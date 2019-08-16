#!/usr/bin/env python

"""
camcops_server/alembic/versions/0040_khandaker_2_mojomedical.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

DATABASE REVISION SCRIPT

khandaker_2_mojomedical

Revision ID: 0040
Revises: 0039
Creation date: 2019-08-16 17:49:35.784820

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
import cardinal_pythonlib.sqlalchemy.list_types
import camcops_server.cc_modules.cc_sqla_coltypes


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0040'
down_revision = '0039'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        'khandaker_2_mojomedical',
        sa.Column('diagnosis', sa.Integer(), nullable=True, comment='Diagnosis (0 Rheumatoid Arthritis, 1 Ankylosing Spondylitis, 2 Sjögren’s Syndrome)'),
        sa.Column('diagnosis_date', sa.Date(), nullable=True, comment="Date of first diagnosis (may be approx from 'duration of illness (years))'"),
        sa.Column('has_fibromyalgia', sa.Boolean(), nullable=True, comment='Do you have a diagnosis of fibromyalgia?'),
        sa.Column('is_pregnant', sa.Boolean(), nullable=True, comment='Are you, or is there any possibility that you might be pregnant?'),
        sa.Column('has_infection_past_month', sa.Boolean(), nullable=True, comment='Do you currently have an infection, or had treatment for an infection (e.g antibiotics) in the past month?'),
        sa.Column('had_infection_two_months_preceding', sa.Boolean(name='ck_kh2mm_had_infection'), nullable=True, comment='Have you had an infection, or had treatment for an infection (e.g antibiotics) in the 2 months preceding last month?'),
        sa.Column('has_alcohol_substance_dependence', sa.Boolean(name='ck_kh2mm_has_alcohol'), nullable=True, comment='Do you have a current diagnosis of alcohol or substance dependence?'),
        sa.Column('smoking_status', sa.Integer(), nullable=True, comment='What is your smoking status? (0 Never smoked, 1 Ex-smoker, 2 Current smoker)'),
        sa.Column('alcohol_units_per_week', sa.Float(), nullable=True, comment='How much alcohol do you drink per week? (medium glass of wine = 2 units, pint of beer at 4.5% = 2.5 units, 25ml of spirits at 40% = 1 unit)'),
        sa.Column('depression', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('bipolar_disorder', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('schizophrenia', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('autism', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('ptsd', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('anxiety', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('personality_disorder', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('intellectual_disability', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('other_mental_illness', sa.Boolean(), nullable=True, comment='Have you had any of the following conditions diagnosed by a doctor?'),
        sa.Column('other_mental_illness_details', sa.UnicodeText(), nullable=True, comment='If other, please list here'),
        sa.Column('hospitalised_in_last_year', sa.Boolean(), nullable=True, comment='Have you had a physical or mental illness requiring hospitalisation in the previous 12 months?'),
        sa.Column('hospitalisation_details', sa.UnicodeText(), nullable=True, comment='If yes, please list here (name of illness, number of hospitilisations and duration):'),
        sa.Column('family_depression', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_bipolar_disorder', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_schizophrenia', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_autism', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_ptsd', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_anxiety', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_personality_disorder', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_intellectual_disability', sa.Boolean(name='ck_kh2mm_fam_int_dis'), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_other_mental_illness', sa.Boolean(), nullable=True, comment='Has anyone in your immediate family (parents, siblings or children) had any of the following conditions diagnosed by a doctor?'),
        sa.Column('family_other_mental_illness_details', sa.UnicodeText(), nullable=True, comment='If other, please list here'),
        sa.Column('patient_id', sa.Integer(), nullable=False, comment='(TASK) Foreign key to patient.id (for this device/era)'),
        sa.Column('when_created', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=False, comment='(TASK) Date/time this task instance was created (ISO 8601)'),
        sa.Column('when_firstexit', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(TASK) Date/time of the first exit from this task (ISO 8601)'),
        sa.Column('firstexit_is_finish', sa.Boolean(), nullable=True, comment='(TASK) Was the first exit from the task because it was finished (1)?'),
        sa.Column('firstexit_is_abort', sa.Boolean(), nullable=True, comment='(TASK) Was the first exit from this task because it was aborted (1)?'),
        sa.Column('editing_time_s', sa.Float(), nullable=True, comment='(TASK) Time spent editing (s)'),
        sa.Column('_pk', sa.Integer(), autoincrement=True, nullable=False, comment='(SERVER) Primary key (on the server)'),
        sa.Column('_device_id', sa.Integer(), nullable=False, comment='(SERVER) ID of the source tablet device'),
        sa.Column('_era', sa.String(length=32), nullable=False, comment="(SERVER) 'NOW', or when this row was preserved and removed from the source device (UTC ISO 8601)"),
        sa.Column('_current', sa.Boolean(), nullable=False, comment='(SERVER) Is the row current (1) or not (0)?'),
        sa.Column('_when_added_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time this row was added (ISO 8601)'),
        sa.Column('_when_added_batch_utc', sa.DateTime(), nullable=True, comment='(SERVER) Date/time of the upload batch that added this row (DATETIME in UTC)'),
        sa.Column('_adding_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that added this row'),
        sa.Column('_when_removed_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time this row was removed, i.e. made not current (ISO 8601)'),
        sa.Column('_when_removed_batch_utc', sa.DateTime(), nullable=True, comment='(SERVER) Date/time of the upload batch that removed this row (DATETIME in UTC)'),
        sa.Column('_removing_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that removed this row'),
        sa.Column('_preserving_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that preserved this row'),
        sa.Column('_forcibly_preserved', sa.Boolean(), nullable=True, comment='(SERVER) Forcibly preserved by superuser (rather than normally preserved by tablet)?'),
        sa.Column('_predecessor_pk', sa.Integer(), nullable=True, comment='(SERVER) PK of predecessor record, prior to modification'),
        sa.Column('_successor_pk', sa.Integer(), nullable=True, comment='(SERVER) PK of successor record  (after modification) or NULL (whilst live, or after deletion)'),
        sa.Column('_manually_erased', sa.Boolean(), nullable=True, comment='(SERVER) Record manually erased (content destroyed)?'),
        sa.Column('_manually_erased_at', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time of manual erasure (ISO 8601)'),
        sa.Column('_manually_erasing_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that erased this row manually'),
        sa.Column('_camcops_version', camcops_server.cc_modules.cc_sqla_coltypes.SemanticVersionColType(length=147), nullable=True, comment='(SERVER) CamCOPS version number of the uploading device'),
        sa.Column('_addition_pending', sa.Boolean(), nullable=False, comment='(SERVER) Addition pending?'),
        sa.Column('_removal_pending', sa.Boolean(), nullable=True, comment='(SERVER) Removal pending?'),
        sa.Column('_group_id', sa.Integer(), nullable=False, comment='(SERVER) ID of group to which this record belongs'),
        sa.Column('id', sa.Integer(), nullable=False, comment='(TASK) Primary key (task ID) on the tablet device'),
        sa.Column('when_last_modified', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(STANDARD) Date/time this row was last modified on the source tablet device (ISO 8601)'),
        sa.Column('_move_off_tablet', sa.Boolean(), nullable=True, comment='(SERVER/TABLET) Record-specific preservation pending?'),
        sa.ForeignKeyConstraint(['_adding_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_2_mojomedical__adding_user_id')),
        sa.ForeignKeyConstraint(['_device_id'], ['_security_devices.id'], name=op.f('fk_khandaker_2_mojomedical__device_id')),
        sa.ForeignKeyConstraint(['_group_id'], ['_security_groups.id'], name=op.f('fk_khandaker_2_mojomedical__group_id')),
        sa.ForeignKeyConstraint(['_manually_erasing_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_2_mojomedical__manually_erasing_user_id')),
        sa.ForeignKeyConstraint(['_preserving_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_2_mojomedical__preserving_user_id')),
        sa.ForeignKeyConstraint(['_removing_user_id'], ['_security_users.id'], name=op.f('fk_khandaker_2_mojomedical__removing_user_id')),
        sa.PrimaryKeyConstraint('_pk', name=op.f('pk_khandaker_2_mojomedical')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('khandaker_2_mojomedical', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical__current'), ['_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical__device_id'), ['_device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical__era'), ['_era'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical__group_id'), ['_group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical__pk'), ['_pk'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_khandaker_2_mojomedical_when_last_modified'), ['when_last_modified'], unique=False)


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table('khandaker_2_mojomedical')
