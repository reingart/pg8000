# vim: sw=4:expandtab:foldmethod=marker
#
# Copyright (c) 2007-2008, Mathieu Fenniak
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

__author__ = "Mathieu Fenniak"

import datetime
import decimal
import struct
from errors import (NotSupportedError, ArrayDataParseError, InternalError,
        ArrayContentEmptyError, ArrayContentNotHomogenousError,
        ArrayContentNotSupportedError, ArrayDimensionsNotConsistentError)

try:
    from pytz import utc
except ImportError:
    ZERO = datetime.timedelta(0)
    class UTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return ZERO
        def tzname(self, dt):
            return "UTC"
        def dst(self, dt):
            return ZERO
    utc = UTC()

class Bytea(str):
    pass

class Interval(object):
    def __init__(self, microseconds, days, months):
        self.microseconds = microseconds
        self.days = days
        self.months = months

    def __repr__(self):
        return "<Interval %s months %s days %s microseconds>" % (self.months, self.days, self.microseconds)

    def __cmp__(self, other):
        if other == None: return -1
        c = cmp(self.months, other.months)
        if c != 0: return c
        c = cmp(self.days, other.days)
        if c != 0: return c
        return cmp(self.microseconds, other.microseconds)

def pg_type_info(typ):
    value = None
    if isinstance(typ, dict):
        value = typ["value"]
        typ = typ["type"]

    data = py_types.get(typ)
    if data == None:
        raise NotSupportedError("type %r not mapped to pg type" % typ)

    # permit the type data to be determined by the value, if provided
    inspect_func = data.get("inspect")
    if value != None and inspect_func != None:
        data = inspect_func(value)

    type_oid = data.get("typeoid")
    if type_oid == None:
        raise InternalError("type %r has no type_oid" % typ)
    elif type_oid == -1:
        # special case: NULL values
        return type_oid, 0

    # prefer bin, but go with whatever exists
    if data.get("bin_out"):
        format = 1
    elif data.get("txt_out"):
        format = 0
    else:
        raise InternalError("no conversion fuction for type %r" % typ)

    return type_oid, format

def pg_value(value, fc, **kwargs):
    typ = type(value)
    data = py_types.get(typ)
    if data == None:
        raise NotSupportedError("type %r not mapped to pg type" % typ)

    # permit the type conversion to be determined by the value, if provided
    inspect_func = data.get("inspect")
    if value != None and inspect_func != None:
        data = inspect_func(value)

    # special case: NULL values
    if data.get("typeoid") == -1:
        return None

    if fc == 0:
        func = data.get("txt_out")
    elif fc == 1:
        func = data.get("bin_out")
    else:
        raise InternalError("unrecognized format code %r" % fc)
    if func == None:
        raise NotSupportedError("type %r, format code %r not supported" % (typ, fc))
    return func(value, **kwargs)

def py_type_info(description):
    type_oid = description['type_oid']
    data = pg_types.get(type_oid)
    if data == None:
        raise NotSupportedError("type oid %r not mapped to py type" % type_oid)
    # prefer bin, but go with whatever exists
    if data.get("bin_in"):
        format = 1
    elif data.get("txt_in"):
        format = 0
    else:
        raise InternalError("no conversion fuction for type oid %r" % type_oid)
    return format

def py_value(v, description, **kwargs):
    if v == None:
        # special case - NULL value
        return None
    type_oid = description['type_oid']
    format = description['format']
    data = pg_types.get(type_oid)
    if data == None:
        raise NotSupportedError("type oid %r not supported" % type_oid)
    if format == 0:
        func = data.get("txt_in")
    elif format == 1:
        func = data.get("bin_in")
    else:
        raise NotSupportedError("format code %r not supported" % format)
    if func == None:
        raise NotSupportedError("data response format %r, type %r not supported" % (format, type_oid))
    return func(v, **kwargs)

def boolrecv(data, **kwargs):
    return data == "\x01"

def boolsend(v, **kwargs):
    if v:
        return "\x01"
    else:
        return "\x00"

def int2recv(data, **kwargs):
    return struct.unpack("!h", data)[0]

def int4recv(data, **kwargs):
    return struct.unpack("!i", data)[0]

def int4send(v, **kwargs):
    return struct.pack("!i", v)

def int8recv(data, **kwargs):
    return struct.unpack("!q", data)[0]

def float4recv(data, **kwargs):
    return struct.unpack("!f", data)[0]

def float8recv(data, **kwargs):
    return struct.unpack("!d", data)[0]

def float8send(v, **kwargs):
    return struct.pack("!d", v)

def datetime_inspect(value):
    if value.tzinfo != None:
        # send as timestamptz if timezone is provided
        return {"typeoid": 1184, "bin_out": timestamp_send}
    else:
        # otherwise send as timestamp
        return {"typeoid": 1114, "bin_out": timestamp_send}

def timestamp_recv(data, integer_datetimes, **kwargs):
    if integer_datetimes:
        # data is 64-bit integer representing milliseconds since 2000-01-01
        val = struct.unpack("!q", data)[0]
        return datetime.datetime(2000, 1, 1) + datetime.timedelta(microseconds = val)
    else:
        # data is double-precision float representing seconds since 2000-01-01
        val = struct.unpack("!d", data)[0]
        return datetime.datetime(2000, 1, 1) + datetime.timedelta(seconds = val)

# return a timezone-aware datetime instance if we're reading from a
# "timestamp with timezone" type.  The timezone returned will always be UTC,
# but providing that additional information can permit conversion to local.
def timestamptz_recv(data, **kwargs):
    return timestamp_recv(data, **kwargs).replace(tzinfo=utc)

def timestamp_send(v, integer_datetimes, **kwargs):
    if v.tzinfo != None:
        # timestamps should be sent as UTC.  If they have zone info,
        # convert them.
        delta = v.astimezone(utc) - datetime.datetime(2000, 1, 1, tzinfo=utc)
    else:
        delta = v - datetime.datetime(2000, 1, 1)
    val = delta.microseconds + (delta.seconds * 1000000) + (delta.days * 86400000000)
    if integer_datetimes:
        # data is 64-bit integer representing milliseconds since 2000-01-01
        return struct.pack("!q", val)
    else:
        # data is double-precision float representing seconds since 2000-01-01
        return struct.pack("!d", val / 1000.0 / 1000.0)

def date_in(data, **kwargs):
    year = int(data[0:4])
    month = int(data[5:7])
    day = int(data[8:10])
    return datetime.date(year, month, day)

def date_out(v, **kwargs):
    return v.isoformat()

def time_in(data, **kwargs):
    hour = int(data[0:2])
    minute = int(data[3:5])
    sec = decimal.Decimal(data[6:])
    return datetime.time(hour, minute, int(sec), int((sec - int(sec)) * 1000000))

def time_out(v, **kwargs):
    return v.isoformat()

def numeric_in(data, **kwargs):
    if data.find(".") == -1:
        return int(data)
    else:
        return decimal.Decimal(data)

def numeric_out(v, **kwargs):
    return str(v)

# PostgreSQL encodings:
#   http://www.postgresql.org/docs/8.3/interactive/multibyte.html
# Python encodings:
#   http://www.python.org/doc/2.4/lib/standard-encodings.html
#
# Commented out encodings don't require a name change between PostgreSQL and
# Python.  If the py side is None, then the encoding isn't supported.
pg_to_py_encodings = {
    # Not supported:
    "mule_internal": None,
    "euc_tw": None,

    # Name fine as-is:
    #"euc_jp",
    #"euc_jis_2004",
    #"euc_kr",
    #"gb18030",
    #"gbk",
    #"johab",
    #"sjis",
    #"shift_jis_2004",
    #"uhc",
    #"utf8",

    # Different name:
    "euc_cn": "gb2312",
    "iso_8859_5": "is8859_5",
    "iso_8859_6": "is8859_6",
    "iso_8859_7": "is8859_7",
    "iso_8859_8": "is8859_8",
    "koi8": "koi8_r",
    "latin1": "iso8859-1",
    "latin2": "iso8859_2",
    "latin3": "iso8859_3",
    "latin4": "iso8859_4",
    "latin5": "iso8859_9",
    "latin6": "iso8859_10",
    "latin7": "iso8859_13",
    "latin8": "iso8859_14",
    "latin9": "iso8859_15",
    "sql_ascii": "ascii",
    "win866": "cp886",
    "win874": "cp874",
    "win1250": "cp1250",
    "win1251": "cp1251",
    "win1252": "cp1252",
    "win1253": "cp1253",
    "win1254": "cp1254",
    "win1255": "cp1255",
    "win1256": "cp1256",
    "win1257": "cp1257",
    "win1258": "cp1258",
}

def encoding_convert(encoding):
    return pg_to_py_encodings.get(encoding.lower(), encoding)

def varcharin(data, client_encoding, **kwargs):
    return unicode(data, encoding_convert(client_encoding))

def textout(v, client_encoding, **kwargs):
    return v.encode(encoding_convert(client_encoding))

def byteasend(v, **kwargs):
    return str(v)

def bytearecv(data, **kwargs):
    return Bytea(data)

# interval support does not provide a Python-usable interval object yet
def interval_recv(data, integer_datetimes, **kwargs):
    if integer_datetimes:
        microseconds, days, months = struct.unpack("!qii", data)
    else:
        seconds, days, months = struct.unpack("!dii", data)
        microseconds = int(seconds * 1000 * 1000)
    return Interval(microseconds, days, months)

def interval_send(data, integer_datetimes, **kwargs):
    if integer_datetimes:
        return struct.pack("!qii", data.microseconds, data.days, data.months)
    else:
        return struct.pack("!dii", data.microseconds / 1000.0 / 1000.0, data.days, data.months)

def array_recv(data, **kwargs):
    dim, hasnull, typeoid = struct.unpack("!iii", data[:12])
    data = data[12:]

    # get type conversion method for typeoid
    conversion = pg_types[typeoid]["bin_in"]

    # Read dimension info
    dim_lengths = []
    element_count = 1
    for idim in range(dim):
        dim_len, dim_lbound = struct.unpack("!ii", data[:8])
        data = data[8:]
        dim_lengths.append(dim_len)
        element_count *= dim_len

    # Read all array values
    array_values = []
    for i in range(element_count):
        element_len, = struct.unpack("!i", data[:4])
        data = data[4:]
        if element_len == -1:
            array_values.append(None)
        else:
            array_values.append(conversion(data[:element_len], **kwargs))
            data = data[element_len:]
    if data != "":
        raise ArrayDataParseError("unexpected data left over after array read")

    # at this point, {{1,2,3},{4,5,6}}::int[][] looks like [1,2,3,4,5,6].
    # go through the dimensions and fix up the array contents to match
    # expected dimensions
    for dim_length in reversed(dim_lengths[1:]):
        val = []
        while array_values:
            val.append(array_values[:dim_length])
            array_values = array_values[dim_length:]
        array_values = val

    return array_values

def array_inspect(value):
    # Check if array has any values.  If not, we can't determine the proper
    # array typeoid.
    first_element = array_find_first_element(value)
    if first_element == None:
        raise ArrayContentEmptyError("array has no values")

    # supported array output
    typ = type(first_element)
    array_typeoid = py_array_types.get(typ)
    if array_typeoid == None:
        raise ArrayContentNotSupportedError("type %r not supported as array contents" % typ)

    # check for homogenous array
    for v in array_flatten(value):
        if v != None and not isinstance(v, typ):
            raise ArrayContentNotHomogenousError("not all array elements are of type %r" % typ)

    # check that all array dimensions are consistent
    array_check_dimensions(value)

    type_data = py_types[typ]
    return {
        "typeoid": array_typeoid,
        "bin_out": array_send(type_data["typeoid"], type_data["bin_out"])
    }

def array_find_first_element(arr):
    for v in array_flatten(arr):
        if v != None:
            return v
    return None

def array_flatten(arr):
    for v in arr:
        if isinstance(v, list):
            for v2 in array_flatten(v):
                yield v2
        else:
            yield v

def array_check_dimensions(arr):
    v0 = arr[0]
    if isinstance(v0, list):
        req_len = len(v0)
        req_inner_lengths = array_check_dimensions(v0)
        for v in arr:
            inner_lengths = array_check_dimensions(v)
            if len(v) != req_len or inner_lengths != req_inner_lengths:
                raise ArrayDimensionsNotConsistentError("array dimensions not consistent")
        retval = [req_len]
        retval.extend(req_inner_lengths)
        return retval
    else:
        # make sure nothing else at this level is a list
        for v in arr:
            if isinstance(v, list):
                raise ArrayDimensionsNotConsistentError("array dimensions not consistent")
        return []

def array_has_null(arr):
    for v in array_flatten(arr):
        if v == None:
            return True
    return False

def array_dim_lengths(arr):
    v0 = arr[0]
    if isinstance(v0, list):
        retval = [len(v0)]
        retval.extend(array_dim_lengths(v0))
    else:
        return [len(arr)]

class array_send(object):
    def __init__(self, typeoid, bin_out_func):
        self.typeoid = typeoid
        self.bin_out_func = bin_out_func

    def __call__(self, arr, **kwargs):
        has_null = array_has_null(arr)
        dim_lengths = array_dim_lengths(arr)
        data = struct.pack("!iii", len(dim_lengths), has_null, self.typeoid)
        for i in dim_lengths:
            data += struct.pack("!ii", i, 1)
        for v in array_flatten(arr):
            if v == None:
                data += struct.pack("!i", -1)
            else:
                inner_data = self.bin_out_func(v, **kwargs)
                data += struct.pack("!i", len(inner_data))
                data += inner_data
        return data

py_types = {
    bool: {"typeoid": 16, "bin_out": boolsend},
    int: {"typeoid": 23, "bin_out": int4send},
    long: {"typeoid": 1700, "txt_out": numeric_out},
    str: {"typeoid": 25, "txt_out": textout},
    unicode: {"typeoid": 25, "txt_out": textout},
    float: {"typeoid": 701, "bin_out": float8send},
    decimal.Decimal: {"typeoid": 1700, "txt_out": numeric_out},
    Bytea: {"typeoid": 17, "bin_out": byteasend},
    datetime.datetime: {"typeoid": 1114, "bin_out": timestamp_send, "inspect": datetime_inspect},
    datetime.date: {"typeoid": 1082, "txt_out": date_out},
    datetime.time: {"typeoid": 1083, "txt_out": time_out},
    Interval: {"typeoid": 1186, "bin_out": interval_send},
    type(None): {"typeoid": -1},
    list: {"inspect": array_inspect},
}

# py type -> pg array typeoid
py_array_types = {
    int: 1007,
    float: 1022,
    bool: 1000,
}

pg_types = {
    16: {"bin_in": boolrecv},
    17: {"bin_in": bytearecv},
    19: {"txt_in": varcharin}, # name type
    20: {"bin_in": int8recv},
    21: {"bin_in": int2recv},
    23: {"bin_in": int4recv},
    25: {"txt_in": varcharin}, # TEXT type
    26: {"txt_in": numeric_in}, # oid type
    700: {"bin_in": float4recv},
    701: {"bin_in": float8recv},
    1000: {"bin_in": array_recv}, # BOOL[]
    1005: {"bin_in": array_recv}, # INT2[]
    1007: {"bin_in": array_recv}, # INT4[]
    1016: {"bin_in": array_recv}, # INT8[]
    1021: {"bin_in": array_recv}, # FLOAT4[]
    1022: {"bin_in": array_recv}, # FLOAT8[]
    1042: {"txt_in": varcharin}, # CHAR type
    1043: {"txt_in": varcharin}, # VARCHAR type
    1082: {"txt_in": date_in},
    1083: {"txt_in": time_in},
    1114: {"bin_in": timestamp_recv},
    1184: {"bin_in": timestamptz_recv}, # timestamp w/ tz
    1186: {"bin_in": interval_recv},
    1700: {"txt_in": numeric_in},
    2275: {"txt_in": varcharin}, # cstring
}

