from __future__ import with_statement

import unittest
import pg8000
import pg8000.types
import datetime
import decimal
from contextlib import closing, nested
from .connection_settings import db_connect

dbapi = pg8000.DBAPI
db2 = dbapi.connect(**db_connect)

# DBAPI compatible interface tests
class Tests(unittest.TestCase):
    def setUp(self):
        pass
        
    def testENUM(self):

        class MyType(str):
            pass
            
        def cast_mytype(data, client_encoding, **kwargs):
            "convert postgres type to python object"
            text = pg8000.types.varcharin(data, client_encoding, **kwargs)
            return MyType(text)
        
        def adapt_mytype(value, client_encoding, **kwargs):
            "convert python object to postgres type"
            return pg8000.types.textout(value, client_encoding)
        
        with closing(db2.cursor()) as c1:
            try:
                c1.execute("DROP TYPE mytype;")
                #c1.execute("DROP TABLE mytable;")
            except:
                pass
            c1.execute("CREATE TYPE mytype AS ENUM ('one', 'two', 'three')")
            c1.execute("""SELECT pg_type.oid
                            FROM pg_type JOIN pg_namespace
                            ON typnamespace = pg_namespace.oid
                            WHERE typname = %s
                              AND nspname = %s""",
                        ['mytype', 'public'])
            mytype_oid = c1.fetchone()[0]
            self.assert_(mytype_oid, 'oid should not be null')
            # create new pg8000 type cast for this enum:
            mytype = pg8000.types.new_type(oids=[mytype_oid], name='mytype', 
                                           pyclass=MyType,
                                           txt_in=cast_mytype, 
                                           bin_in=None, 
                                           txt_out=adapt_mytype, 
                                           bin_out=None,
                                           )
            # map the new type
            pg8000.types.register_type(mytype)

            c1.execute("CREATE TEMP TABLE mytable (somedata mytype)")
            c1.execute("INSERT INTO mytable (somedata) VALUES ('one') RETURNING *", [])
            retval = c1.fetchall()
            self.assertEquals(retval[0][0], u'one')
            self.assertEquals(type(retval[0][0]), MyType)
            c1.execute("INSERT INTO mytable (somedata) VALUES (%s) RETURNING *", [MyType("two")])
            retval = c1.fetchall()
            self.assertEquals(retval[0][0], u'two')
            self.assertEquals(type(retval[0][0]), MyType)
                
    def testDefault(self):

        # register the default conversion function (varcharin)
        # remember to cast input parameters!
        pg8000.types.register_default()
        
        with closing(db2.cursor()) as c1:
            try:
                c1.execute("DROP TYPE mytype;")
                #c1.execute("DROP TABLE mytable;")
            except:
                pass
            c1.execute("CREATE TYPE mytype AS ENUM ('one', 'two', 'three')")
            c1.execute("CREATE TEMP TABLE mytable (somedata mytype)")
            c1.execute("INSERT INTO mytable (somedata) VALUES ('one') RETURNING *", [])
            retval = c1.fetchall()
            self.assertEquals(retval[0][0], u'one')
            c1.execute("INSERT INTO mytable (somedata) VALUES (%s::mytype) RETURNING *", ["two"])
            retval = c1.fetchall()
            self.assertEquals(retval[0][0], u'two')

if __name__ == "__main__":
    unittest.main()

