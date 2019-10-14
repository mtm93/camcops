## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/tasks/apeq_cpft_perinatal_report.mako

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

</%doc>

<%inherit file="base_web.mako"/>
<%block name="css">
${parent.css()}

h2, h3 {
    margin-top: 20px;
}

.table-cell {
    text-align: right;
}

.table-cell.col-0 {
    text-align: initial;
}

.ff-why-table > tbody > tr > .col-1 {
    text-align: initial;
}
</%block>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewParam
%>


<%include file="db_user_info.mako"/>

<h1>${ title | h }</h1>

<p>
%if start_datetime:
${_("Created")} <b>&ge; ${ start_datetime }</b>.
%endif
%if end_datetime:
${_("Created")} <b>&lt; ${ end_datetime }</b>.
%endif
</p>

<h2>${ qa_q }</h2>

<%include file="table.mako" args="column_headings=qa_column_headings, rows=qa_rows"/>

<h2>${ qb_q }</h2>

<%include file="table.mako" args="column_headings=qb_column_headings, rows=qb_rows"/>

<h2>${ q1_stem }</h2>

<%include file="table.mako" args="column_headings=q1_column_headings, rows=q1_rows"/>

<h2>${ q2_stem }</h2>

<%include file="table.mako" args="column_headings=q2_column_headings, rows=q2_rows, escape_cells=False"/>

<h2>${ q3_stem }</h2>

<%include file="table.mako" args="column_headings=q3_column_headings, rows=q3_rows, escape_cells=False"/>

<h2>${ participation_q }</h2>

<%include file="table.mako" args="column_headings=fp_column_headings, rows=fp_rows, escape_cells=False"/>

<h2>${_("Comments")}</h2>
%for comment_row in comment_rows:
   <blockquote>
       <p>${comment_row[0] | h}</p>
   </blockquote>
%endfor
<div>
    <a href="${ request.route_url(Routes.OFFER_REPORT, _query={ViewParam.REPORT_ID: report_id}) }">${_("Re-configure report")}</a>
</div>
<div>
    <a href="${request.route_url(Routes.REPORTS_MENU)}">${_("Return to reports menu")}</a>
</div>
<%include file="to_main_menu.mako"/>
