Release History
================

Version 1.09, 2012-01-03
------------------------

- Added Two Phase Commit support, methods: 
  :meth:`~pg8000.dbapi.ConnectionWrapper.xid`, 
  :meth:`~pg8000.dbapi.ConnectionWrapper.tpc_begin`,
  :meth:`~pg8000.dbapi.ConnectionWrapper.tpc_prepare`,
  :meth:`~pg8000.dbapi.ConnectionWrapper.tpc_commit`,
  :meth:`~pg8000.dbapi.ConnectionWrapper.tpc_rollback`, and 
  :meth:`~pg8000.dbapi.ConnectionWrapper.tpc_recover`, based on prior TPC 
  connection wrapper for psycopg2 developed originally for 
  `pyreplica <http://pgfoundry.org/projects/pyreplica/>`_
  
- Added :attr:`~pg8000.dbapi.ConnectionWrapper.autocommit` attribute to avoid
  to send a BEGIN automatically. This is needed for some commands (e.g. CREATE 
  DATABASE, VACUUM...) that require to be run outside any transaction.
  Thanks funkybob for the original patch (adapted from a method to a property 
  to be compatible with other python connectors)

- Fixed NUMERIC representation issue (truncation on string conversion).
  Thanks zeha for the report and patch.

- Fixed "Empty array issue" that raised an exception when SELECTing an empty
  array field (with any primitive type into).
  Thanks franklx for the original patch (modified to return a true empty list)

- Fixed unicode issue in textout that caused an exception when using PostgreSQL 
  errors in non-English Locale and, in some cases, when using non ASCII chars.
  Now, the text is encoded correctly using the client_encoding.

- Added :attr:`~pg8000.dbapi.ConnectionWrapper.server_version` attribute as 
  reported by the backend.
  Thanks Ulrich Petri for the patch, docs and test case.

- Added OID 194 mapping for "string representing an internal node tree" 
  to support sqlalchemy introspection with PostgreSQL 9.1.
  Thanks dave42 for the original patch.

- Added OID 142 mapping for "xml" type basic support.
  Thanks dahilia for the report.

- Fixed issue with python 2.5 missing ssl (no ssl support if package is not
  installed)

- Added basic automatic test connection setup (using loged-in username)

- NOTE: this fork is maintained by Mariano Reingart at 
  `pg8000.googlecode.com <http://code.google.com/p/pg8000>`_
  Thanks to Mathieu Fenniak for the original version.

Version 1.08, 2010-06-08
------------------------

- Removed usage of deprecated :mod:`md5` module, replaced with :mod:`hashlib`.
  Thanks to Gavin Sherry for the patch.

- Start transactions on execute or executemany, rather than immediately at the
  end of previous transaction.  Thanks to Ben Moran for the patch.

- Add encoding lookups where needed, to address usage of SQL_ASCII encoding.
  Thanks to Benjamin Schweizer for the patch.

- Remove record type cache SQL query on every new pg8000 connection.

- Fix and test SSL connections.

- Handle out-of-band messages during authentication.


Version 1.07, 2009-01-06
------------------------

- Added support for :meth:`~pg8000.dbapi.CursorWrapper.copy_to` and
  :meth:`~pg8000.dbapi.CursorWrapper.copy_from` methods on cursor objects, to
  allow the usage of the PostgreSQL COPY queries.  Thanks to Bob Ippolito for
  the original patch.

- Added the :attr:`~pg8000.dbapi.ConnectionWrapper.notifies` and
  :attr:`~pg8000.dbapi.ConnectionWrapper.notifies_lock` attributes to DBAPI
  connection objects to provide access to server-side event notifications.
  Thanks again to Bob Ippolito for the original patch.

- Improved performance using buffered socket I/O.

- Added valid range checks for :class:`~pg8000.types.Interval` attributes.

- Added binary transmission of :class:`~decimal.Decimal` values.  This permits
  full support for NUMERIC[] types, both send and receive.

- New `Sphinx <http://sphinx.pocoo.org/>`_-based website and documentation.


Version 1.06, 2008-12-09
------------------------

- pg8000-py3: a branch of pg8000 fully supporting Python 3.0.

- New Sphinx-based documentation.

- Support for PostgreSQL array types -- INT2[], INT4[], INT8[], FLOAT[],
  DOUBLE[], BOOL[], and TEXT[].  New support permits both sending and
  receiving these values.

- Limited support for receiving RECORD types.  If a record type is received,
  it will be translated into a Python dict object.

- Fixed potential threading bug where the socket lock could be lost during 
  error handling.


Version 1.05, 2008-09-03
------------------------

- Proper support for timestamptz field type:

  - Reading a timestamptz field results in a datetime.datetime instance that
    has a valid tzinfo property.  tzinfo is always UTC.

  - Sending a datetime.datetime instance with a tzinfo value will be
    sent as a timestamptz type, with the appropriate tz conversions done.

- Map postgres < -- > python text encodings correctly.

- Fix bug where underscores were not permitted in pyformat names.

- Support "%s" in a pyformat strin.

- Add cursor.connection DB-API extension.

- Add cursor.next and cursor.__iter__ DB-API extensions.

- DBAPI documentation improvements.

- Don't attempt rollback in cursor.execute if a ConnectionClosedError occurs.

- Add warning for accessing exceptions as attributes on the connection object,
  as per DB-API spec.

- Fix up open connection when an unexpected connection occurs, rather than
  leaving the connection in an unusable state.

- Use setuptools/egg package format.


Version 1.04, 2008-05-12
------------------------

- DBAPI 2.0 compatibility:

  - rowcount returns rows affected when appropriate (eg. UPDATE, DELETE)

  - Fix CursorWrapper.description to return a 7 element tuple, as per spec.

  - Fix CursorWrapper.rowcount when using executemany.

  - Fix CursorWrapper.fetchmany to return an empty sequence when no more
    results are available.

  - Add access to DBAPI exceptions through connection properties.

  - Raise exception on closing a closed connection.

  - Change DBAPI.STRING to varchar type.

  - rowcount returns -1 when appropriate.

  - DBAPI implementation now passes Stuart Bishop's Python DB API 2.0 Anal
    Compliance Unit Test.

- Make interface.Cursor class use unnamed prepared statement that binds to
  parameter value types.  This change increases the accuracy of PG's query
  plans by including parameter information, hence increasing performance in
  some scenarios.

- Raise exception when reading from a cursor without a result set.

- Fix bug where a parse error may have rendered a connection unusable.


Version 1.03, 2008-05-09
------------------------

- Separate pg8000.py into multiple python modules within the pg8000 package.
  There should be no need for a client to change how pg8000 is imported.

- Fix bug in row_description property when query has not been completed.

- Fix bug in fetchmany dbapi method that did not properly deal with the end of
  result sets.

- Add close methods to DB connections.

- Add callback event handlers for server notices, notifications, and runtime
  configuration changes.

- Add boolean type output.

- Add date, time, and timestamp types in/out.

- Add recognition of "SQL_ASCII" client encoding, which maps to Python's
  "ascii" encoding.

- Add types.Interval class to represent PostgreSQL's interval data type, and
  appropriate wire send/receive methods.

- Remove unused type conversion methods.


Version 1.02, 2007-03-13
------------------------

- Add complete DB-API 2.0 interface.

- Add basic SSL support via ssl connect bool.

- Rewrite pg8000_test.py to use Python's unittest library.

- Add bytea type support.

- Add support for parameter output types: NULL value, timestamp value, python
  long value.

- Add support for input parameter type oid.


Version 1.01, 2007-03-09
------------------------

- Add support for writing floats and decimal objs up to PG backend.

- Add new error handling code and tests to make sure connection can recover
  from a database error.

- Fixed bug where timestamp types were not always returned in the same binary
  format from the PG backend.  Text format is now being used to send
  timestamps.

- Fixed bug where large packets from the server were not being read fully, due
  to socket.read not always returning full read size requested.  It was a
  lazy-coding bug.

- Added locks to make most of the library thread-safe.

- Added UNIX socket support.


Version 1.00, 2007-03-08
------------------------

- First public release.  Although fully functional, this release is mostly
  lacking in production testing and in type support.

