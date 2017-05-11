/*
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
*/

#include "photosequencephoto.h"

const QString PHOTOSEQUENCEPHOTO_TABLENAME("photosequence_photos");

const QString PhotoSequencePhoto::FK_NAME("photosequence_id");  // FK to photosequence.id
const QString PhotoSequencePhoto::SEQNUM("seqnum");
const QString PhotoSequencePhoto::DESCRIPTION("description");
const QString PhotoSequencePhoto::PHOTO_BLOBID("photo_blobid");
// const QString PhotoSequenceItem::ROTATION("rotation");  // DEFUNCT in v2


PhotoSequencePhoto::PhotoSequencePhoto(CamcopsApp& app, const QSqlDatabase& db,
                                       int load_pk) :
    DatabaseObject(app, db, PHOTOSEQUENCEPHOTO_TABLENAME,
                   dbconst::PK_FIELDNAME,  // pk_fieldname
                   true,  // has_modification_timestamp
                   false,  // has_creation_timestamp
                   true,  // has_move_off_tablet_field
                   true)  // triggers_need_upload
{
    addField(FK_NAME, QVariant::Int);
    addField(SEQNUM, QVariant::Int);
    addField(DESCRIPTION, QVariant::String);
    addField(PHOTO_BLOBID, QVariant::Int);

    load(load_pk);
}


void PhotoSequencePhoto::setForeignKeyToOwner(int fk)
{
    setValue(FK_NAME, fk);
}


void PhotoSequencePhoto::setSeqnum(int seqnum)
{
    setValue(SEQNUM, seqnum);
}


int PhotoSequencePhoto::seqnum() const
{
    return valueInt(SEQNUM);
}


QString PhotoSequencePhoto::description() const
{
    return valueString(DESCRIPTION);
}