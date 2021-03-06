from __future__ import with_statement

import os
import unittest
from pg8000 import dbapi
from contextlib import closing
from .connection_settings import db_connect

# Tests related to connecting to a database.
class Tests(unittest.TestCase):
    def testSocketMissing(self):
        self.assertRaises(dbapi.InterfaceError, dbapi.connect,
                unix_sock="/file-does-not-exist", user="doesn't-matter")

    def testDatabaseMissing(self):
        data = db_connect.copy()
        data["database"] = "missing-db"
        self.assertRaises(dbapi.ProgrammingError, dbapi.connect, **data)

    def testNotify(self):
        try:
            db = dbapi.connect(**db_connect)
            self.assert_(db.notifies == [])

            with closing(db.cursor()) as cursor:
                cursor.execute("LISTEN test")
                cursor.execute("NOTIFY test")
                db.commit()

                cursor.execute("VALUES (1, 2), (3, 4), (5, 6)")
                self.assert_(len(db.notifies) == 1)
                self.assert_(db.notifies[0][1] == "test")

        finally:
            db.close()

    def testServerVersion(self):
        with closing(dbapi.connect(**db_connect)) as db:
            self.assertRegexpMatches(db.server_version, r'\d{1,2}\.\d(\.\d)?')

    def testConnInfo(self):
        opts = dbapi.interface.conninfo_parse("   ")
        self.assertEquals(opts, {})
        opts = dbapi.interface.conninfo_parse("dbname = postgres")
        self.assertEquals(opts, {'dbname': 'postgres'})
        opts = dbapi.interface.conninfo_parse("dbname=postgres user=mariano password=secret host=localhost port=5432")
        self.assertEquals(opts, {'dbname': 'postgres', 'user': 'mariano', 'password': 'secret', 'host': 'localhost', 'port': '5432'})
        # test no spaces before/after ' (seem to be a valid libpq syntax)
        opts = dbapi.interface.conninfo_parse("dbname='postgres'user='mariano'password='secret'host='localhost'port=5432")
        self.assertEquals(opts, {'dbname': 'postgres', 'user': 'mariano', 'password': 'secret', 'host': 'localhost', 'port': '5432'})
        dsn = r"   user=mariano host  ='saraza\'.com' port= 5433   dbname='my crazy db' password=abra\'cadabra sslmode =  prefer  "
        opts = dbapi.interface.conninfo_parse(dsn)
        self.assertEquals(opts, {'dbname': 'my crazy db',
                'user': 'mariano', 'password': "abra'cadabra",
                'host': "saraza'.com", 'port': "5433", 'sslmode': 'prefer'
                                 })

    def testConnectDSN(self):
        dsn = "dbname='%(database)s' user='%(user)s' host='%(host)s' port=%(port)s "
        if 'password' in db_connect:
            dsn += "password='%(password)s' "
        if not 'host' in db_connect:
            # use unix socket directory and extension (see libpq-envars)
            db_connect['host'] = os.path.dirname(db_connect['unix_sock'])
            db_connect['port'] = os.path.splitext(db_connect['unix_sock'])[1][1:]
        dbapi.connect(dsn % db_connect)

    def testConnectEnv(self):
        import os
        if not 'host' in db_connect:
            # use unix socket directory and extension (see libpq-envars)
            db_connect['host'] = os.path.dirname(db_connect['unix_sock'])
            db_connect['port'] = os.path.splitext(db_connect['unix_sock'])[1][1:]
        os.environ['PGHOST'] = db_connect['host']
        os.environ['PGPORT'] = db_connect['port']
        os.environ['PGUSER'] = db_connect['user']
        if 'password' in db_connect:
            os.environ['PGPASSWORD'] = db_connect['password']
        dbapi.connect("")
                                 
if __name__ == "__main__":
    unittest.main()

