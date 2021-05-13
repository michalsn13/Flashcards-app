# GLOBAL IMPORTS (PYTHON PACKAGES)
import psycopg2 # pgsql handler
# LOCAL IMPORTS
from Connection.con_parameters import Con_parameters # parameters for the database I will be connecting to

class Connection:
    """
    Class was made to automatize projects connected to pgsql databases.
    """
    def __init__(self):
        """
        Defining the Connection object to use __enter__() and __exit__() dunder methods.
        """
        self.con=None
    def __enter__(self):
        """
        Using parameters from con_parameters.py to enter a certain database.
        You need to prepare those parameters first as they're gonna be set on default at start.
        """
        self.con=psycopg2.connect(database=Con_parameters.DATABASE, user=Con_parameters.USER, password=Con_parameters.PASSWORD, port=Con_parameters.PORT)
        return self.con
    def __exit__(self,exc_type, exc_value,exc_tb):
        """
        Exiting database and catching possible errors- if some error occurs program does not commit queries.
        """
        if exc_type or exc_value or exc_tb:
            self.con.close()
        else:
            self.con.commit()
            self.con.close()
