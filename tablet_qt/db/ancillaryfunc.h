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

#pragma once
#include <QSqlDatabase>
#include <QSqlQuery>
#include "common/camcopsapp.h"
#include "db/databasemanager.h"
#include "db/sqlargs.h"


namespace ancillaryfunc
{

// ============================================================================
// Assistance function to load multiple ancillary objects
// - Class must inherit from DatabaseObject
// - Class must have a constructor like SomeAncillary(app, db, pk)
// ============================================================================

template<class AncillaryType, class AncillaryPtrType>
void loadAncillary(QVector<AncillaryPtrType>& ancillaries,
                   CamcopsApp& app,
                   DatabaseManager& db,
                   const QString& fk_name,
                   const OrderBy& order_by,
                   int parent_pk)
{
    ancillaries.clear();
    WhereConditions where;
    where.add(fk_name, parent_pk);
    AncillaryType specimen(app, db);
    SqlArgs sqlargs = specimen.fetchQuerySql(where, order_by);
    QueryResult result = db.query(sqlargs);
    int nrows = result.nRows();
    for (int row = 0; row < nrows; ++row) {
        AncillaryType* raw_ptr_ancillary = new AncillaryType(
                    app, db, dbconst::NONEXISTENT_PK);
        raw_ptr_ancillary->setFromQuery(result, row, true);
        AncillaryPtrType ancillary(raw_ptr_ancillary);
        ancillaries.append(ancillary);
    }
}


}  // namespace ancillaryfunc
