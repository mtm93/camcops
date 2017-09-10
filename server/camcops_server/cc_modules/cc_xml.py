#!/usr/bin/env python
# camcops_server/cc_modules/cc_xml.py

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

import base64
import datetime
from typing import Any, Dict, List, Optional
import xml.sax.saxutils

from cardinal_pythonlib.sqlalchemy.orm_inspect import get_orm_columns
from pendulum import Date, Pendulum, Time
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.type_api import TypeEngine

from .cc_simpleobjects import XmlSimpleValue


# =============================================================================
# Constants
# =============================================================================

XML_COMMENT_ANONYMOUS = "<!-- Anonymous task; no patient info -->"
XML_COMMENT_BLOBS = "<!-- Associated BLOBs -->"
XML_COMMENT_CALCULATED = "<!-- Calculated fields -->"
XML_COMMENT_PATIENT = "<!-- Associated patient details -->"
XML_COMMENT_SPECIAL_NOTES = "<!-- Any special notes added -->"
XML_COMMENT_STORED = "<!-- Stored fields -->"

XML_NAMESPACES = [
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    # ' xmlns:dt="http://www.w3.org/2001/XMLSchema-datatypes"'
]
XML_IGNORE_NAMESPACES = [
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"',
    'xmlns:ignore="http://www.camcops.org/ignore"',
    # ... actual URL unimportant
    'mc:Ignorable="ignore"'
]
# http://www.w3.org/TR/xmlschema-1/
# http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html


class XmlDataTypes(object):
    BASE64BINARY = "base64Binary"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "dateTime"
    DOUBLE = "double"
    INTEGER = "integer"
    STRING = "string"
    TIME = "time"


# =============================================================================
# XML element
# =============================================================================

class XmlElement(object):
    """Represents XML data in a tree. See functions in cc_xml.py"""
    def __init__(self, name: str, value: Any = None, datatype: str = None,
                 comment: str = None):
        # Special: boolean requires lower case "true"/"false" (or 0/1)
        if datatype == XmlDataTypes.BOOLEAN and value is not None:
            value = str(value).lower()
        self.name = name
        self.value = value
        self.datatype = datatype
        self.comment = comment


# =============================================================================
# XML processing
# =============================================================================
# The xml.etree.ElementTree and lxml libraries can both do this sort of thing.
# However, they do look quite fiddly and we only want to create something
# simple. Therefore, let's roll our own:

def make_xml_branches_from_fieldspecs(
        obj,
        skip_fields: List[str] = None) -> List[XmlElement]:
    """
    Returns a list of XML branches, each an XmlElementTuple, from an object,
    using the list of SQLAlchemy Column objects that define/describe its
    fields.
    """
    skip_fields = skip_fields or []
    columns = get_orm_columns(obj.__class__)
    branches = []
    for column in columns:
        name = column.name
        if name in skip_fields:
            continue
        branches.append(XmlElement(
            name=name,
            value=getattr(obj, name),
            datatype=get_xml_datatype_from_sqla_column(column.type),
            comment=column.comment
        ))
    return branches


def make_xml_branches_from_summaries(
        summaries: List[Dict],
        skip_fields: List[str] = None) -> List[XmlElement]:
    """Returns a list of XML branches, each an XmlElementTuple, from a
    list of summary data provided by a task."""
    skip_fields = skip_fields or []
    branches = []
    for d in summaries:
        name = d["name"]
        if name in skip_fields:
            continue
        branches.append(XmlElement(
            name=name,
            value=d["value"],
            datatype=get_xml_datatype_from_sqla_column(d),
            comment=d.get("comment", None)
        ))
    return branches


def xml_header(eol: str = '\n') -> str:
    """XML declaration header."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>{eol}'.format(
            eol=eol,
        )
    )


def get_xml_datatype_from_sqla_column_type(
        coltype: TypeEngine) -> Optional[str]:
    """
    Returns the XML schema datatype from an SQLAlchemy column type,
    such as Integer.
    """
    # http://www.xml.dvint.com/docs/SchemaDataTypesQR-2.pdf
    # http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html
    try:
        pt = coltype.python_type
        if isinstance(pt, datetime.datetime) or isinstance(pt, Pendulum):
            return XmlDataTypes.DATETIME
        if isinstance(pt, datetime.date) or isinstance(pt, Date):
            return XmlDataTypes.DATE
        if isinstance(pt, datetime.date) or isinstance(pt, Time):
            return XmlDataTypes.TIME
        if isinstance(pt, int):
            return XmlDataTypes.INTEGER
        if isinstance(pt, float):
            return XmlDataTypes.DOUBLE
        if isinstance(pt, bool):
            return XmlDataTypes.BOOLEAN
        if isinstance(pt, str):
            return XmlDataTypes.STRING
        # BLOBs are handled separately.
    except NotImplementedError:
        pass
    return None


def get_xml_datatype_from_sqla_column(column: Column) -> Optional[str]:
    """Returns the XML schema datatype from an SQLAlchemy Column."""
    coltype = column.type  # type: TypeEngine
    return get_xml_datatype_from_sqla_column_type(coltype)


def get_xml_blob_tuple(name: str,
                       blobdata: Optional[bytes],
                       comment: str = None) -> XmlElement:
    """Returns an XmlElementTuple representing a base-64-encoded BLOB."""
    return XmlElement(
        name=name,
        value=base64.b64encode(blobdata) if blobdata else None,
        datatype=XmlDataTypes.BASE64BINARY,
        comment=comment
    )
    # http://www.w3.org/TR/2001/REC-xmlschema-2-20010502/#base64Binary


def xml_escape_value(value: str) -> str:
    """Escape a value for XML."""
    # http://stackoverflow.com/questions/1091945/
    # https://wiki.python.org/moin/EscapingXml
    return xml.sax.saxutils.escape(value)


def xml_quote_attribute(attr: str) -> str:
    """Escapes and quotes an attribute for XML.

    More stringent than value escaping.
    """
    return xml.sax.saxutils.quoteattr(attr)


def get_xml_tree(element: XmlElement,
                 level: int = 0,
                 indent_spaces: int = 4,
                 eol: str = '\n',
                 include_comments: bool = False) -> str:
    """Returns an entire XML tree as text, given the root XmlElementTuple."""
    # We will represent NULL values with xsi:nil, but this requires a
    # namespace: http://stackoverflow.com/questions/774192
    # http://books.xmlschemata.org/relaxng/relax-CHP-11-SECT-1.html
    # Comments:
    # - http://blog.galasoft.ch/posts/2010/02/quick-tip-commenting-out-properties-in-xaml/  # noqa
    # - http://stackoverflow.com/questions/2073140/
    xmltext = ""
    prefix = ' ' * level * indent_spaces

    if isinstance(element, XmlElement):

        # Attributes
        namespaces = []
        if level == 0:  # root
            # Apply namespace to root element (will inherit):
            namespaces.extend(XML_NAMESPACES)
            if include_comments:
                namespaces.extend(XML_IGNORE_NAMESPACES)
        namespace = " ".join(namespaces)
        dt = ""
        if element.datatype:
            dt = ' xsi:type="{}"'.format(element.datatype)
        cmt = ""
        if include_comments and element.comment:
            cmt = ' ignore:comment={}'.format(
                xml_quote_attribute(element.comment))
        attributes = "{ns}{dt}{cmt}".format(ns=namespace, dt=dt, cmt=cmt)

        # Assemble
        if element.value is None:
            # NULL handling
            xmltext += '{pr}<{name}{attributes} xsi:nil="true"/>{eol}'.format(
                name=element.name,
                pr=prefix,
                eol=eol,
                attributes=attributes,
            )
        else:
            complex_value = isinstance(element.value, XmlElement) \
                or isinstance(element.value, list)
            value_to_recurse = element.value if complex_value else \
                XmlSimpleValue(element.value)
            # ... XmlSimpleValue is a marker that subsequently distinguishes
            # things that were part of an XmlElementTuple from user-inserted
            # raw XML.
            nl = eol if complex_value else ""
            pr2 = prefix if complex_value else ""
            xmltext += (
                '{pr}<{name}{attributes}>{nl}'
                '{value}{pr2}</{name}>{eol}'.format(
                    name=element.name,
                    pr=prefix,
                    eol=eol,
                    pr2=pr2,
                    nl=nl,
                    value=get_xml_tree(
                        value_to_recurse,
                        level=level + 1,
                        indent_spaces=indent_spaces,
                        eol=eol,
                        include_comments=include_comments
                    ),
                    attributes=attributes,
                )
            )

    elif isinstance(element, list):
        for subelement in element:
            xmltext += get_xml_tree(subelement, level,
                                    indent_spaces=indent_spaces,
                                    eol=eol,
                                    include_comments=include_comments)
        # recursive

    elif isinstance(element, XmlSimpleValue):
        # The lowest-level thing a value. No extra indent.
        xmltext += xml_escape_value(str(element.value))
        # Regarding newlines: no need to do anything special (although some
        # browsers may fail to display them correctly):
        # http://stackoverflow.com/questions/2004386

    else:
        # A user-inserted piece of XML. Insert, but indent.
        xmltext += prefix + str(element) + eol

    return xmltext


def get_xml_document(root: XmlElement,
                     indent_spaces: int = 4,
                     eol: str = '\n',
                     include_comments: bool = False) -> str:
    """Returns an entire XML document as text, given the root
    XmlElementTuple."""
    if not isinstance(root, XmlElement):
        raise AssertionError("get_xml_document: root not an XmlElementTuple; "
                             "XML requires a single root")
    return xml_header(eol) + get_xml_tree(
        root,
        indent_spaces=indent_spaces,
        eol=eol,
        include_comments=include_comments
    )
