from __future__ import with_statement

import unittest
import pg8000
import datetime
import decimal
from contextlib import closing, nested
from .connection_settings import db_connect

dbapi = pg8000.DBAPI
db2 = dbapi.connect(**db_connect)

# DBAPI compatible interface tests
class Tests(unittest.TestCase):
    def setUp(self):
        with closing(db2.cursor()) as c:
            try:
                c.execute("DROP TABLE t1")
            except pg8000.DatabaseError, e:
                # the only acceptable error is:
                self.assert_(e.args[1] == '42P01', # table does not exist
                        "incorrect error for drop table")
            c.execute("CREATE TEMPORARY TABLE t1 (f1 int primary key, f2 int not null, f3 varchar(50) null)")
            c.execute("INSERT INTO t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, None))
            c.execute("INSERT INTO t1 (f1, f2, f3) VALUES (%s, %s, %s)", (2, 10, None))
            c.execute("INSERT INTO t1 (f1, f2, f3) VALUES (%s, %s, %s)", (3, 100, None))
            c.execute("INSERT INTO t1 (f1, f2, f3) VALUES (%s, %s, %s)", (4, 1000, None))
            c.execute("INSERT INTO t1 (f1, f2, f3) VALUES (%s, %s, %s)", (5, 10000, None))

    def testParallelQueries(self):
        with nested(closing(db2.cursor()), closing(db2.cursor())) as (c1, c2):
            c1.execute("SELECT f1, f2, f3 FROM t1")
            while 1:
                row = c1.fetchone()
                if row == None:
                    break
                f1, f2, f3 = row
                c2.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > %s", (f1,))
                while 1:
                    row = c2.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row

    def testQmark(self):
        orig_paramstyle = dbapi.paramstyle
        try:
            dbapi.paramstyle = "qmark"
            with closing(db2.cursor()) as c1:
                c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > ?", (3,))
                while 1:
                    row = c1.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row
        finally:
            dbapi.paramstyle = orig_paramstyle

    def testNumeric(self):
        orig_paramstyle = dbapi.paramstyle
        try:
            dbapi.paramstyle = "numeric"
            with closing(db2.cursor()) as c1:
                c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > :1", (3,))
                while 1:
                    row = c1.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row
        finally:
            dbapi.paramstyle = orig_paramstyle

    def testNamed(self):
        orig_paramstyle = dbapi.paramstyle
        try:
            dbapi.paramstyle = "named"
            with closing(db2.cursor()) as c1:
                c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > :f1", {"f1": 3})
                while 1:
                    row = c1.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row
        finally:
            dbapi.paramstyle = orig_paramstyle

    def testFormat(self):
        orig_paramstyle = dbapi.paramstyle
        try:
            dbapi.paramstyle = "format"
            with closing(db2.cursor()) as c1:
                c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > %s", (3,))
                while 1:
                    row = c1.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row
        finally:
            dbapi.paramstyle = orig_paramstyle
    
    def testPyformat(self):
        orig_paramstyle = dbapi.paramstyle
        try:
            dbapi.paramstyle = "pyformat"
            with closing(db2.cursor()) as c1:
                c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > %(f1)s", {"f1": 3})
                while 1:
                    row = c1.fetchone()
                    if row == None:
                        break
                    f1, f2, f3 = row
        finally:
            dbapi.paramstyle = orig_paramstyle

    def testArraysize(self):
        with closing(db2.cursor()) as c1:
            c1.arraysize = 3
            c1.execute("SELECT * FROM t1")
            retval = c1.fetchmany()
            self.assert_(len(retval) == c1.arraysize,
                    "fetchmany returned wrong number of rows")

    def testDate(self):
        val = dbapi.Date(2001, 2, 3)
        self.assert_(val == datetime.date(2001, 2, 3),
                "Date constructor value match failed")

    def testTime(self):
        val = dbapi.Time(4, 5, 6)
        self.assert_(val == datetime.time(4, 5, 6),
                "Time constructor value match failed")

    def testTimestamp(self):
        val = dbapi.Timestamp(2001, 2, 3, 4, 5, 6)
        self.assert_(val == datetime.datetime(2001, 2, 3, 4, 5, 6),
                "Timestamp constructor value match failed")

    def testDateFromTicks(self):
        val = dbapi.DateFromTicks(1173804319)
        self.assert_(val == datetime.date(2007, 3, 13),
                "DateFromTicks constructor value match failed")

    def testTimeFromTicks(self):
        val = dbapi.TimeFromTicks(1173804319)
        self.assert_(val == datetime.time(10, 45, 19),
                "TimeFromTicks constructor value match failed")

    def testTimestampFromTicks(self):
        val = dbapi.TimestampFromTicks(1173804319)
        self.assert_(val == datetime.datetime(2007, 3, 13, 10, 45, 19),
                "TimestampFromTicks constructor value match failed")

    def testBinary(self):
        v = dbapi.Binary("\x00\x01\x02\x03\x02\x01\x00")
        self.assert_(v == "\x00\x01\x02\x03\x02\x01\x00",
                "Binary value match failed")
        self.assert_(isinstance(v, pg8000.Bytea),
                "Binary type match failed")

    def testRowCount(self):
        with closing(db2.cursor()) as c1:
            c1.execute("SELECT * FROM t1")
            self.assertEquals(5, c1.rowcount)

            c1.execute("UPDATE t1 SET f3 = %s WHERE f2 > 101", ("Hello!",))
            self.assertEquals(2, c1.rowcount)

            c1.execute("DELETE FROM t1")
            self.assertEquals(5, c1.rowcount)

    def testFetchMany(self):
        with closing(db2.cursor()) as cursor:
            cursor.arraysize = 2
            cursor.execute("SELECT * FROM t1")
            self.assertEquals(2, len(cursor.fetchmany()))
            self.assertEquals(2, len(cursor.fetchmany()))
            self.assertEquals(1, len(cursor.fetchmany()))
            self.assertEquals(0, len(cursor.fetchmany()))

    def testIterator(self):
        from warnings import filterwarnings
        filterwarnings("ignore", "DB-API extension cursor.next()")
        filterwarnings("ignore", "DB-API extension cursor.__iter__()")

        with closing(db2.cursor()) as cursor:
            cursor.execute("SELECT * FROM t1 ORDER BY f1")
            f1 = 0
            for row in cursor:
                next_f1 = row[0]
                assert next_f1 > f1
                f1 = next_f1

    def testEmptyArray(self):
        with closing(db2.cursor()) as c1:
            c1.execute("SELECT ARRAY[1,2,3, NULL];")
            retval = c1.fetchone()
            self.assert_(len(retval[0]) == 4, 
                         "%s is not a valid array" % repr(retval[0]))
            for i, value in enumerate((1, 2, 3, None)):
                self.assertEquals(value, retval[0][i])
            c1.execute("SELECT '{}'::text[];")
            retval = c1.fetchone()
            self.assert_(len(retval[0]  ) == 0, 
                         "%s is not an empty array" % repr(retval))


    def testDecimalNumeric(self):
        with closing(db2.cursor()) as c1:
            # On the other hand, this simple select returns 0.2600:
            test_dec_val = decimal.Decimal('0.260')
            c1.execute('SELECT %s', [test_dec_val])
            retval = c1.fetchone()
            self.assertEquals(retval[0], test_dec_val)
            
            #Table schema: 
            c1.execute('CREATE TEMP TABLE foo_dec_num1 (a NUMERIC);')
            
            # I'd expect that 0.26 is stored in table foo, but psql shows it as 0.
            c1.execute('INSERT INTO foo_dec_num1 VALUES (%s)', [test_dec_val])
            db2.commit()
            c1.execute('SELECT a::TEXT FROM foo_dec_num1')
            retval = c1.fetchone()
            print retval
            self.assertEquals(retval[0], str(test_dec_val))

    def testXML(self):
        with closing(db2.cursor()) as c1:
            c1.execute("SELECT '<nothing/>'::xml;")
            retval = c1.fetchone()
            self.assertEquals(retval[0], "<nothing/>")

    def testAutocommitCreateDatabase(self):
        # Forced transactions prevent CREATE DATABASE (needs autocommit)
        db2.autocommit(True)
        db2.rollback()
        with closing(db2.cursor()) as c1:
            c1.execute('CREATE DATABASE FOOFOOFOOFOO')
            c1.execute('DROP DATABASE FOOFOOFOOFOO')
        # this should not throw ProgrammingError: 
        # ('ERROR', '25001', 
        #  'CREATE DATABASE cannot run inside a transaction block')


if __name__ == "__main__":
    unittest.main()

