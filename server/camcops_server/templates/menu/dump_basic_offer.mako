## dump_basic_offer.mako
<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Basic research data dump")}</h1>

<h2>${_("Explanation")}</h2>
<div>
    <ul>
        <li>
            ${_("Provides a spreadsheet-style download (usually one sheet per task; for some tasks, more than one).")}
        </li>
        <li>
            ${_("Incorporates patient and summary information into each row. Doesn’t provide BLOBs (e.g. pictures).")}
        </li>
        <li>
            ${_("If there are no instances of a particular task, no sheet is returned.")}
        </li>
        <li>
            ${_("Restricted to current records (i.e. ignores historical versions of tasks that have been edited).")}
        </li>
        <li>
            ${_("For TSV, NULL values are represented by blank fields and are therefore indistinguishable from blank strings, and the Excel dialect of TSV is used. If you want to read TSV files into R, try:")}
            <code>mydf = read.table("something.tsv", sep="\t", header=TRUE, na.strings="", comment.char="")</code>.
            ${_("Note that R will prepend ‘X’ to variable names starting with an underscore; see")}
            <code>?make.names</code>).
            ${_("Inspect the results with e.g.")}
            <code>colnames(mydf)</code>,
            ${_("or in RStudio,")}
            <code>View(mydf)</code>.
        </li>
        <li>
            ${_("For more advanced features, use the")}
            <a href="${ request.route_url(Routes.OFFER_SQL_DUMP) }">${_("SQL dump")}</a>
            ${_("to get the raw data.")}
        </li>
        <li>
            ${_("For explanations of each field (field comments), see each task’s XML view or")}
            <a href="${ request.route_url(Routes.VIEW_DDL) }">${_("inspect the table definitions")}</a>.
        </li>
    </ul>
</div>

<h2>${_("Choose basic dump settings")}</h2>

${ form }

<%include file="to_main_menu.mako"/>
