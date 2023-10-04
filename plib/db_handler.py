import mysql.connector

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

        payload = cursor.fetchall()

        print(payload)
    
    def insert(self, table: str, names: list, values: list):
        self._checkTable(table= table)
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

    def select (self, table: str):
        self._checkTable(table= table)
        cursor = self.mainDb.cursor()

        cursor.execute(f"SELECT * FROM {table}")

        payload = cursor.fetchall()

        return payload

    def update (self, table: str, key_name: str, key_value: str, value_name: str, value_value: int):
        self._checkTable(table= table)
        cursor = self.mainDb.cursor()

        sql = f"UPDATE {table} SET {value_name} = {value_value} WHERE {key_name} = \"{key_value}\""

        print(sql)

        cursor.execute(sql)

        self.mainDb.commit()

        print(cursor.rowcount, "record(s) affected")