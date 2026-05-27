
import pymysql
import pymysql.cursors
import pandas as pd 

class DBInitializer:
    """Handles verification of tables, automatic user indexing via triggers, and credentials validation."""
    
    def __init__(self):
        self.server_config = {
            'host': 's501.sureserver.com',
            'user': 'Student',
            'password': 'Barcelona2024*',
            'database': 'metales_traking',
            'connect_timeout': 10
        }

    def initialize_auth_system(self) -> bool:
        """Verifies tables, builds a BEFORE INSERT trigger for EMP000N format, and seeds the admin user."""
        conn = None
        cursor = None
        try:
            conn = pymysql.connect(**self.server_config)
            cursor = conn.cursor()
            
            # 1. Create the base table structure using a standard VARCHAR for employee_number
            print("Verificando estructura de la tabla 'employees'...")
            create_table_query = """
            CREATE TABLE IF NOT EXISTS `employees` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `employee_number` VARCHAR(30) NULL,
                `username` VARCHAR(50) NOT NULL UNIQUE,
                `name` VARCHAR(100) NOT NULL,
                `surname` VARCHAR(100) NOT NULL,
                `date_of_birth` DATE NOT NULL,
                `department` VARCHAR(100) NOT NULL,
                `password` VARCHAR(255) NOT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY (`employee_number`)
            ) ENGINE=InnoDB;
            """
            cursor.execute(create_table_query)
            conn.commit()
            
            # 2. Cleanly drop the trigger first to prevent duplicate errors
            print("Limpiando e instalando disparador automático (Trigger) para códigos de empleado...")
            cursor.execute("DROP TRIGGER IF EXISTS `ts_assign_employee_number`;")
            conn.commit()
            
            # 3. Create the Trigger cleanly without the forbidden inline clause
            trigger_query = """
            CREATE TRIGGER `ts_assign_employee_number`
            BEFORE INSERT ON `employees`
            FOR EACH ROW
            BEGIN
                IF NEW.`employee_number` IS NULL OR NEW.`employee_number` = '' THEN
                    SET @next_id = (
                        SELECT AUTO_INCREMENT 
                        FROM information_schema.TABLES 
                        WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'employees'
                    );
                    SET NEW.`employee_number` = CONCAT('EMP', LPAD(@next_id, 4, '0'));
                END IF;
            END;
            """
            cursor.execute(trigger_query)
            conn.commit()
            
            # 4. Check if the database has any users. If completely empty, seed the first admin.
            cursor.execute("SELECT COUNT(*) FROM `employees`;")
            if cursor.fetchone()[0] == 0: # type: ignore
                print("Tabla 'employees' vacía. Creando el primer usuario Administrador...")
                
                insert_admin_query = """
                INSERT INTO `employees` 
                (`username`, `name`, `surname`, `date_of_birth`, `department`, `password`) 
                VALUES (%s, %s, %s, %s, %s, %s);
                """
                admin_payload = (
                    'admin',                
                    'Administrador',        
                    'Sistema',              
                    '2026-01-01',           
                    'Dirección / Sistemas', 
                    'sepsis'                
                )
                cursor.execute(insert_admin_query, admin_payload)
                conn.commit()
                print("Primer usuario creado con éxito: Usuario='admin' / Contraseña='sepsis'")
                print("El sistema ha asignado automáticamente el código: EMP0001")
            
            print("Inicialización del sistema completada con éxito.")
            return True

        except pymysql.MySQLError as err:
            print(f"Error crítico durante la inicialización de la Base de Datos:\n{err}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def register_user(self, user_data: dict) -> tuple[bool, str]:
        """Registers a new standard user into the system database matrix."""
        username = str(user_data.get('username', '')).strip()
        name = str(user_data.get('name', '')).strip()
        surname = str(user_data.get('surname', '')).strip()
        dob = user_data.get('date_of_birth')
        dept = str(user_data.get('department', '')).strip()
        pwd = str(user_data.get('password', '')).strip()
        rep_pwd = str(user_data.get('repeat_password', '')).strip()

        if not all([username, name, surname, dob, dept, pwd, rep_pwd]):
            return False, "Error: Todos los campos son obligatorios para completar el registro."

        if pwd != rep_pwd:
            return False, "Error de Validación: Las contraseñas ingresadas no coinciden."

        conn = None
        cursor = None
        try:
            conn = pymysql.connect(**self.server_config)
            cursor = conn.cursor()

            # Prevent duplicate username issues
            check_query = "SELECT id FROM `employees` WHERE `username` = %s;"
            cursor.execute(check_query, (username,))
            if cursor.fetchone() is not None:
                return False, f"Error: El nombre de usuario '{username}' ya está en uso."

            # Save the record (trigger executes automatically in the background)
            insert_query = """
            INSERT INTO `employees` 
            (`username`, `name`, `surname`, `date_of_birth`, `department`, `password`) 
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (username, name, surname, dob, dept, pwd))
            conn.commit()

            # Retrieve the newly generated code to show inside the UI notification
            cursor.execute("SELECT `employee_number` FROM `employees` WHERE `id` = LAST_INSERT_ID();")
            new_emp_code = cursor.fetchone()[0] # type: ignore

            return True, f"Registro completado. ID asignado automáticamente por el sistema: {new_emp_code}"

        except pymysql.MySQLError as err:
            return False, f"Error del servidor de Base de Datos al guardar registro:\n{err}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def login_user(self, credential_input: str, password: str) -> tuple[bool, str | dict]:
        """
        Authenticates an employee. Accepts either their unique 'employee_number' (EMP0001) 
        or their clean 'username' (admin) to maximize interface flexibility.
        """
        input_token = str(credential_input).strip()
        pwd = str(password).strip()

        if not input_token or not pwd:
            return False, "Por favor, complete todos los campos de acceso."

        conn = None
        cursor = None
        try:
            conn = pymysql.connect(**self.server_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            query = """
            SELECT `employee_number`, `username`, `name`, `surname`, `department`, `password` 
            FROM `employees` 
            WHERE `employee_number` = %s OR `username` = %s;
            """
            cursor.execute(query, (input_token, input_token))
            user_record = cursor.fetchone()

            if user_record is None:
                return False, "Acceso Denegado: Las credenciales ingresadas no corresponden a ningún usuario."

            if user_record['password'] != pwd: # type: ignore
                return False, "Acceso Denegado: La contraseña ingresada es incorrecta."

            del user_record['password'] # type: ignore
            return True, user_record # type: ignore

        except pymysql.MySQLError as err:
            return False, f"Error de conexión con el servidor de autenticación:\n{err}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    # Puedes añadir esto directamente a tu clase DBInitializer en el archivo correspondiente

    def initialize_sample_sepsis_table(self) -> bool:
        """
        Crea la tabla 'pcare_sepsis_patients' si no existe y añade un set aleatorio de 50
        instancias extraídas del dataset original de MIMIC-4 para su consumo en la UI.
        """
        import numpy as np
        
        path = "../mimic4_data_sepsis.csv"
        try:
            data = pd.read_csv(path)
        except Exception as e:
            print(f"Error al cargar el archivo CSV local en la ruta {path}: {e}")
            return False

        # Tomar una muestra aleatoria de exactamente 50 filas (o menos si el dataset es pequeño)
        sample_size = min(50, len(data))
        # Reemplazar NaN e infinitos para evitar romper la inserción SQL de tipos flotantes/numéricos
        sample_df = data.sample(n=sample_size, random_state=42).copy()
        sample_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        sample_df = sample_df.fillna(0) # Inyectar ceros defensivos en nulos antes de persistir

        # Extraer variables y estructurar dinámicamente el query de creación de columnas según el CSV
        columns_schema = []
        for col in sample_df.columns:
            if col in ['subject_id', 'hadm_id', 'stay_id', 'sepsis3']:
                columns_schema.append(f"`{col}` INT NOT NULL")
            else:
                columns_schema.append(f"`{col}` DOUBLE NULL")

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `pcare_sepsis_patients` (
            `sample_id` INT AUTO_INCREMENT PRIMARY KEY,
            {", ".join(columns_schema)},
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """

        conn = None
        cursor = None
        try:
            conn = pymysql.connect(**self.server_config)
            cursor = conn.cursor()
            
            # 1. Crear la tabla adaptada al set de variables predictoras
            print("Verificando estructura de la tabla 'pcare_sepsis_patients'...")
            cursor.execute(create_table_query)
            conn.commit()
            
            # 2. Verificar si ya se encuentra poblada para no duplicar datos
            cursor.execute("SELECT COUNT(*) FROM `pcare_sepsis_patients`;")
            if cursor.fetchone()[0] == 0: # type: ignore
                print(f"Poblando la tabla 'pcare_sepsis_patients' con {sample_size} registros aleatorios...")
                
                cols_names = [f"`{c}`" for c in sample_df.columns]
                placeholders = [col_format := "%s"] * len(sample_df.columns)
                
                insert_query = f"""
                INSERT INTO `pcare_sepsis_patients` ({", ".join(cols_names)}) 
                VALUES ({", ".join(placeholders)});
                """
                

                records_to_insert = [tuple(row) for row in sample_df.values]
                
                cursor.executemany(insert_query, records_to_insert)
                conn.commit()
                print(f"Inserción masiva de {cursor.rowcount} registros completada.")
                
            return True

        except pymysql.MySQLError as err:
            print(f"Error crítico en el motor relacional al inicializar muestras de Sepsis:\n{err}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


if __name__ == "__main__":
    initializer = DBInitializer()
    db_ready = initializer.initialize_auth_system()
    initializer.initialize_sample_sepsis_table()
    
    
    if db_ready:
        print("\n--- Realizando prueba de login simulada ---")
        success, result = initializer.login_user("admin", "sepsis")
        if success:
            print(f"Prueba Exitosa! Conectado como: {result['name']} ({result['employee_number']})") # type: ignore
        else:
            print(f"Fallo en la prueba de login: {result}")

