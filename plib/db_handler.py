import mysql.connector
from plib.utils.general import getCurrentBranch
from plib.utils.custom_exceptions import BranchWarning
from plib.terminal import error
import traceback

class Database:
    def __init__(self) -> None:
        self.mainDb = mysql.connector.connect(
        host= "161.97.78.70",
        user= "u34176_uEuxXMbGcY",
        password= "t3KAs4vxN==w1C^cSPQt79AH",
        database= "s34176_general"
        )
    
    def _checkTable (self, table: str):
        cursor = self.mainDb.cursor()

        cursor.execute("SELECT table_name FROM information_schema.tables")

        tabes = cursor.fetchall()

        for table_name in tabes:
            if table in table_name:
                return True
        
        return False
    
    def insert(self, table: str, names: list, values: list):
        if not self._checkTable(table= table):
            raise NameError(f"Table {table} does not exist.")

        if getCurrentBranch() != "main":
            try:
                raise BranchWarning(branch= getCurrentBranch())
            except BranchWarning as e:
                error(e, traceback.format_exc(), "Not on main branch", "Please switch to the main branch to update the database.", level= "WARNING")
                raise

        cursor = self.mainDb.cursor()
        
        names_str = "("
        for name_index, name in enumerate(names):
            if name_index > 0:
                names_str += ", "
            names_str += name
        names_str += ")"

        values_str = "("
        for value_index, _ in enumerate(values):
            if value_index > 0:
                values_str += ", "
            values_str += r"%s"
        values_str += ")"
        print(values_str)

        sql = f"INSERT INTO {table} {names_str} VALUES {values_str}"
        print (sql)

        cursor.execute(sql, values)

        self.mainDb.commit()

        print(cursor.rowcount, "record(s) affected")

    def select (self, table: str, conditions: dict = None):
        if not self._checkTable(table= table):
            raise NameError(f"Table {table} does not exist.")
        cursor = self.mainDb.cursor()

        sql = f"SELECT * FROM {table}"

        if conditions:
            sql += " WHERE "

            for condition_index, condition in enumerate(conditions):
                if condition_index > 0:
                    sql += " AND "
                sql += f"{condition} = \"{conditions[condition]}\""

        cursor.execute(sql)

        payload = cursor.fetchall()

        return payload

    def update (self, table: str, key_name: str, key_value: str, value_name: str, value_value: int):
        if not self._checkTable(table= table):
            raise NameError(f"Table {table} does not exist.")

        if getCurrentBranch() != "main":
            try:
                raise BranchWarning(branch= getCurrentBranch())
            except BranchWarning as e:
                error(e, traceback.format_exc(), "Not on main branch", "Please switch to the main branch to update the database.", level= "WARNING")
                raise

        cursor = self.mainDb.cursor()

        sql = f"UPDATE {table} SET {value_name} = {value_value} WHERE {key_name} = \"{key_value}\""

        print(sql)

        cursor.execute(sql)

        self.mainDb.commit()

        print(cursor.rowcount, "record(s) affected")
    
    def delete (self, table: str, conditions: dict):
        if not self._checkTable(table= table):
            raise NameError(f"Table {table} does not exist.")

        if getCurrentBranch() != "main":
            try:
                raise BranchWarning(branch= getCurrentBranch())
            except BranchWarning as e:
                error(e, traceback.format_exc(), "Not on main branch", "Please switch to the main branch to update the database.", level= "WARNING")
                raise

        cursor = self.mainDb.cursor()

        sql = f"DELETE FROM {table} WHERE "

        for condition_index, condition in enumerate(conditions):
            if condition_index > 0:
                sql += " AND "
            sql += f"{condition} = \"{conditions[condition]}\""

        print(sql)

        cursor.execute(sql)

        self.mainDb.commit()

        print(cursor.rowcount, "record(s) affected")