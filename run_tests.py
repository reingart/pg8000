import unittest

from warnings import filterwarnings
filterwarnings("ignore", "DB-API extension connection")

from tests.connection import Tests as ConnectionTests
from tests.query import Tests as QueryTests
from tests.paramstyle import Tests as ParamStyleTests
from tests.dbapi import Tests as DbapiTests
from tests.typeconversion import Tests as TypeTests
from tests.pg8000_dbapi20 import Tests as Dbapi20Tests
from tests.error_recovery import Tests as ErrorRecoveryTests
from tests.typeobjects import Tests as TypeObjectTests
from tests.copy import Tests as CopyTests
from tests.tpc import TwoPhaseTests
from tests.types import Tests as TypeTests

if __name__ == "__main__":
    unittest.main()

