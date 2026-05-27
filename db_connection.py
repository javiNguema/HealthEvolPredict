

import pymysql
import pymysql.cursors

class DBConnectionManager:
    """Manages active life-cycle instances and state validation hooks for MySQL using PyMySQL."""
    
    def __init__(self):
        self.config_data = None

    def save_configuration(self, config: dict) -> None:
        self.config_data = {
            'host': config.get('host', 'localhost').strip(),
            'port': int(config.get('port', 3306)),
            'user': config.get('user', 'root').strip(),
            'password': config.get('password', '').strip(),
            'database': config.get('database', '').strip(),
            'connect_timeout': 5
        }

    def test_connection(self, config: dict) -> tuple[bool, str]:
        if not config.get('database', '').strip():
            return False, "Falta Información: Por favor especifique una base de datos."
            
        try:
            conn = pymysql.connect(
                host=config.get('host', 'localhost').strip(),
                port=int(config.get('port', 3306)),
                user=config.get('user', 'root').strip(),
                password=config.get('password', '').strip(),
                database=config.get('database', '').strip(),
                connect_timeout=5
            )
            # PyMySQL opens connection instantly on execution; close it right after validation
            conn.close()
            return True, f"Conexión exitosa a la Base de Datos: {config.get('database')}"
                
        except pymysql.MySQLError as err:
            return False, f"Error de conexión MySQL:\n{err}"
        except ValueError:
            return False, "El puerto ingresado debe ser un valor numérico válido."
        
        return False, "No se pudo establecer la conexión."

    def get_connection(self):
        if not self.config_data:
            raise ValueError("No configuration settings found. Save parameters first.")
            
        try:
            return pymysql.connect(**self.config_data)
        except pymysql.MySQLError as err:
            print(f"Failed to generate runtime operational cursor: {err}")
            return None

    def get_tables(self) -> list[str]:
        """
        Returns a list of tables in the selected database that match the 'pcare_' signature.
        Keeps original table names without modification to maintain data consistency.
        """
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor()
            # Use LIKE with a wildcard (%) to retrieve only matching signature prefixes
            cursor.execute("SHOW TABLES LIKE 'pcare_%';")
            raw_tables = [row[0] for row in cursor.fetchall()] # type: ignore
            
            # Return original table names as they are stored in the schema
            return raw_tables # type: ignore

        except pymysql.MySQLError as err:
            print(f"Error fetching filtered tables: {err}")
            return []

        finally:
            if 'cursor' in locals() and cursor: # type: ignore
                cursor.close()
            if conn:
                conn.close()

    def get_table_schema(self, table_name: str) -> list[dict]:
        """
        Returns column metadata for a given table.
        Output: list of dicts with column info.
        """
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            # Replaces dictionary=True by generating a DictCursor explicitly
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(f"DESCRIBE `{table_name}`;")
            schema = cursor.fetchall()
            return schema # type: ignore

        except pymysql.MySQLError as err:
            print(f"Error fetching schema for {table_name}: {err}")
            return []

        finally:
            if 'cursor' in locals() and cursor: # type: ignore
                cursor.close()
            if conn:
                conn.close()

    def fetch_table_data(self, table_name: str, limit: int = 100) -> list[dict]:
        """
        Fetches rows from a table (limited to avoid overload).
        """
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            # Replaces dictionary=True by generating a DictCursor explicitly
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT %s;", (limit,))
            rows = cursor.fetchall()
            return rows # type: ignore

        except pymysql.MySQLError as err:
            print(f"Error fetching data from {table_name}: {err}")
            return []

        finally:
            if 'cursor' in locals() and cursor: # type: ignore
                cursor.close()
            if conn:
                conn.close()
            
    def close_connection(self) -> None:
        """Clears the active configuration data to disconnect from the database backend."""
        self.config_data = None
        print("Database configuration cache wiped successfully.")