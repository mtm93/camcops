#!/usr/bin/env python

"""
camcops_server/alembic/versions/0042_lynall_iam_life.py

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

lynall_iam_life

Revision ID: 0042
Revises: 0041
Creation date: 2019-09-15 19:21:48.809716

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

revision = '0042'
down_revision = '0041'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lynall_iam_life',
        sa.Column('q1_main', sa.Boolean(), nullable=True, comment='Q1: in last 6 months: illness/injury/assault (self) (0 no, 1 yes)'),
        sa.Column('q1_severity', sa.Integer(), nullable=True, comment='Q1: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q1_frequency', sa.Integer(), nullable=True, comment='Q1: For what percentage of your life since aged 18 has [this event: illness/injury/assault (self)] been happening? (0-100)'),
        sa.Column('q2_main', sa.Boolean(), nullable=True, comment='Q2: in last 6 months: illness/injury/assault (relative) (0 no, 1 yes)'),
        sa.Column('q2_severity', sa.Integer(), nullable=True, comment='Q2: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q2_frequency', sa.Integer(), nullable=True, comment='Q2: For what percentage of your life since aged 18 has [this event: illness/injury/assault (relative)] been happening? (0-100)'),
        sa.Column('q3_main', sa.Boolean(), nullable=True, comment='Q3: in last 6 months: parent/child/spouse/sibling died (0 no, 1 yes)'),
        sa.Column('q3_severity', sa.Integer(), nullable=True, comment='Q3: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q3_frequency', sa.Integer(), nullable=True, comment='Q3: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q4_main', sa.Boolean(), nullable=True, comment='Q4: in last 6 months: close family friend/other relative died (0 no, 1 yes)'),
        sa.Column('q4_severity', sa.Integer(), nullable=True, comment='Q4: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q4_frequency', sa.Integer(), nullable=True, comment='Q4: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q5_main', sa.Boolean(), nullable=True, comment='Q5: in last 6 months: marital separation or broke off relationship (0 no, 1 yes)'),
        sa.Column('q5_severity', sa.Integer(), nullable=True, comment='Q5: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q5_frequency', sa.Integer(), nullable=True, comment='Q5: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q6_main', sa.Boolean(), nullable=True, comment='Q6: in last 6 months: ended long-lasting friendship with close friend/relative (0 no, 1 yes)'),
        sa.Column('q6_severity', sa.Integer(), nullable=True, comment='Q6: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q6_frequency', sa.Integer(), nullable=True, comment='Q6: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q7_main', sa.Boolean(), nullable=True, comment='Q7: in last 6 months: problems with close friend/neighbour/relative (0 no, 1 yes)'),
        sa.Column('q7_severity', sa.Integer(), nullable=True, comment='Q7: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q7_frequency', sa.Integer(), nullable=True, comment='Q7: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q8_main', sa.Boolean(), nullable=True, comment='Q8: in last 6 months: unsuccessful job-seeking for >1 month (0 no, 1 yes)'),
        sa.Column('q8_severity', sa.Integer(), nullable=True, comment='Q8: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q8_frequency', sa.Integer(), nullable=True, comment='Q8: For what percentage of your life since aged 18 has [this event: unsuccessful job-seeking for >1 month] been happening? (0-100)'),
        sa.Column('q9_main', sa.Boolean(), nullable=True, comment='Q9: in last 6 months: sacked/made redundant (0 no, 1 yes)'),
        sa.Column('q9_severity', sa.Integer(), nullable=True, comment='Q9: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q9_frequency', sa.Integer(), nullable=True, comment='Q9: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q10_main', sa.Boolean(), nullable=True, comment='Q10: in last 6 months: major financial crisis (0 no, 1 yes)'),
        sa.Column('q10_severity', sa.Integer(), nullable=True, comment='Q10: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q10_frequency', sa.Integer(), nullable=True, comment='Q10: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q11_main', sa.Boolean(), nullable=True, comment='Q11: in last 6 months: problem with police involving court appearance (0 no, 1 yes)'),
        sa.Column('q11_severity', sa.Integer(), nullable=True, comment='Q11: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q11_frequency', sa.Integer(), nullable=True, comment='Q11: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q12_main', sa.Boolean(), nullable=True, comment='Q12: in last 6 months: something valued lost/stolen (0 no, 1 yes)'),
        sa.Column('q12_severity', sa.Integer(), nullable=True, comment='Q12: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q12_frequency', sa.Integer(), nullable=True, comment='Q12: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q13_main', sa.Boolean(), nullable=True, comment='Q13: in last 6 months: self/partner gave birth (0 no, 1 yes)'),
        sa.Column('q13_severity', sa.Integer(), nullable=True, comment='Q13: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q13_frequency', sa.Integer(), nullable=True, comment='Q13: Since age 18, how many times has this happened to you in total?'),
        sa.Column('q14_main', sa.Boolean(), nullable=True, comment='Q14: in last 6 months: other significant negative events (0 no, 1 yes)'),
        sa.Column('q14_severity', sa.Integer(), nullable=True, comment='Q14: (if yes) how bad was that (1 not too bad, 2 moderately bad, 3 very bad)'),
        sa.Column('q14_frequency', sa.Integer(), nullable=True, comment='Q14: Since age 18, how many times has this happened to you in total?'),
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
        sa.ForeignKeyConstraint(['_adding_user_id'], ['_security_users.id'], name=op.f('fk_lynall_iam_life__adding_user_id')),
        sa.ForeignKeyConstraint(['_device_id'], ['_security_devices.id'], name=op.f('fk_lynall_iam_life__device_id')),
        sa.ForeignKeyConstraint(['_group_id'], ['_security_groups.id'], name=op.f('fk_lynall_iam_life__group_id')),
        sa.ForeignKeyConstraint(['_manually_erasing_user_id'], ['_security_users.id'], name=op.f('fk_lynall_iam_life__manually_erasing_user_id')),
        sa.ForeignKeyConstraint(['_preserving_user_id'], ['_security_users.id'], name=op.f('fk_lynall_iam_life__preserving_user_id')),
        sa.ForeignKeyConstraint(['_removing_user_id'], ['_security_users.id'], name=op.f('fk_lynall_iam_life__removing_user_id')),
        sa.PrimaryKeyConstraint('_pk', name=op.f('pk_lynall_iam_life')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('lynall_iam_life', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lynall_iam_life__current'), ['_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life__device_id'), ['_device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life__era'), ['_era'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life__group_id'), ['_group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life__pk'), ['_pk'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lynall_iam_life_when_last_modified'), ['when_last_modified'], unique=False)


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table('lynall_iam_life')
