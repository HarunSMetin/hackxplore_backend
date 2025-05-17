import csv
import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database connection details from .env
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))

print(f"[CSV_IMPORT_DEBUG] DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}, DB_PORT: {DB_PORT}")

def get_db_connection():
    print("[CSV_IMPORT_DEBUG] Attempting to connect to database...")
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("[CSV_IMPORT_DEBUG] Database connection successful.")
        return connection
    except Exception as e:
        print(f"[CSV_IMPORT_DEBUG] Database connection failed: {e}")
        raise

def convert_capacity_to_litres(capacity_m3_str):
    try:
        return float(capacity_m3_str.replace(',', '.')) * 1000
    except ValueError:
        print(f"Warning: Could not convert capacity '{capacity_m3_str}' to float. Using 0.")
        return 0

def convert_fill_to_litres(fill_m3_str):
    try:
        return float(fill_m3_str.replace(',', '.')) * 1000
    except ValueError:
        print(f"Warning: Could not convert fill level '{fill_m3_str}' to float. Using 0.")
        return 0

def parse_timestamp(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"Warning: Could not parse date/time '{date_str} {time_str}'. Using current time.")
        return datetime.now()

def import_data_from_csv(filepath):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print("[CSV_IMPORT_DEBUG] Cursor created.")

            # Debug: Show schema of containers table before attempting to modify/use it
            try:
                cursor.execute("SHOW CREATE TABLE containers;")
                create_table_statement = cursor.fetchone()
                print(f"[CSV_IMPORT_DEBUG] Existing 'containers' table schema: {create_table_statement}")
            except Exception as e:
                print(f"[CSV_IMPORT_DEBUG] Could not get 'containers' table schema (it might not exist yet): {e}")
            
            # Define table creation SQL (matches models/container.py)
            create_containers_table_sql = """
            CREATE TABLE IF NOT EXISTS containers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL DEFAULT '',
                location_lat FLOAT NOT NULL,
                location_lng FLOAT NOT NULL,
                type VARCHAR(50) NOT NULL,
                capacity INT NOT NULL,
                current_fill INT NOT NULL,
                last_updated DATETIME NOT NULL,
                UNIQUE KEY uq_container_name_address (name, address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            print(f"[CSV_IMPORT_DEBUG] Executing SQL to create/ensure 'containers' table: {create_containers_table_sql}")
            cursor.execute(create_containers_table_sql)
            print("[CSV_IMPORT_DEBUG] 'containers' table ensured.")

            create_readings_table_sql = """
            CREATE TABLE IF NOT EXISTS container_readings (
                reading_id INT AUTO_INCREMENT PRIMARY KEY,
                container_id INT NOT NULL,
                timestamp DATETIME NOT NULL,
                fill_level_litres INT NOT NULL,
                INDEX idx_container_timestamp (container_id, timestamp),
                FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            print(f"[CSV_IMPORT_DEBUG] Executing SQL to create/ensure 'container_readings' table: {create_readings_table_sql}")
            cursor.execute(create_readings_table_sql)
            print("[CSV_IMPORT_DEBUG] 'container_readings' table ensured.")
            
            connection.commit()
            print("[CSV_IMPORT_DEBUG] Schema creation/ensurance committed.")

            with open(filepath, mode='r', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                
                header = csv_reader.fieldnames
                if header:
                    print(f"[CSV_IMPORT_DEBUG] CSV Header: {header}")
                else:
                    print("[CSV_IMPORT_DEBUG] Warning: CSV file has no header row or is empty.")
                    return
                
                # Map German CSV column names to internal Python variable names / database model names
                column_mapping = {
                    'csv_name': 'Label',
                    'csv_address': 'Location', # This is 'Location' in CSV, will map to 'address' in DB
                    'csv_latitude': 'Latitude',
                    'csv_longitude': 'Longitude',
                    'csv_date': 'Datum',
                    'csv_time': 'Uhrzeit',
                    'csv_fill_level': 'Füllstand',
                    'csv_capacity': 'Containergröße',
                    'csv_type': 'Container-Typ'
                }
                
                missing_csv_cols = [csv_col_name for py_var, csv_col_name in column_mapping.items() if csv_col_name not in header]
                if missing_csv_cols:
                    print(f"[CSV_IMPORT_DEBUG] Error: Missing expected columns in CSV: {missing_csv_cols}")
                    return

                containers_cache = {} 
                rows_processed_count = 0

                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Use mapped names to read from CSV row
                        container_name_val = row[column_mapping['csv_name']]
                        # The 'Location' from CSV will become the 'address' in the database
                        container_address_val = row[column_mapping['csv_address']] 
                        location_lat_val = float(row[column_mapping['csv_latitude']].replace(',', '.'))
                        location_lng_val = float(row[column_mapping['csv_longitude']].replace(',', '.'))
                        container_type_val = row[column_mapping['csv_type']]
                        capacity_litres_val = convert_capacity_to_litres(row[column_mapping['csv_capacity']])
                        fill_level_litres_val = convert_fill_to_litres(row[column_mapping['csv_fill_level']])
                        timestamp_val = parse_timestamp(row[column_mapping['csv_date']], row[column_mapping['csv_time']])

                        container_key = (container_name_val, container_address_val)
                        container_id = None

                        if container_key not in containers_cache:
                            select_sql = "SELECT id FROM containers WHERE name = %s AND address = %s"
                            print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Checking for existing container. SQL: {select_sql} with values: ('{container_name_val}', '{container_address_val}')")
                            cursor.execute(select_sql, (container_name_val, container_address_val))
                            container_record = cursor.fetchone()
                            
                            if container_record:
                                container_id = container_record['id']
                                print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Found existing container. ID: {container_id}")
                            else:
                                insert_sql = (
                                    "INSERT INTO containers (name, address, location_lat, location_lng, type, capacity, current_fill, last_updated) "
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                )
                                insert_values = (container_name_val, container_address_val, location_lat_val, location_lng_val, container_type_val, capacity_litres_val, fill_level_litres_val, timestamp_val)
                                print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Creating new container. SQL: {insert_sql} with values: {insert_values}")
                                cursor.execute(insert_sql, insert_values)
                                container_id = cursor.lastrowid
                                print(f"[CSV_IMPORT_DEBUG] Row {row_num}: New container created. ID: {container_id}")
                            containers_cache[container_key] = container_id
                        else:
                            container_id = containers_cache[container_key]
                            print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Container ID {container_id} from cache for key {container_key}")
                        
                        # Insert reading
                        insert_reading_sql = "INSERT INTO container_readings (container_id, timestamp, fill_level_litres) VALUES (%s, %s, %s)"
                        reading_values = (container_id, timestamp_val, fill_level_litres_val)
                        # print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Inserting reading. SQL: {insert_reading_sql} with values: {reading_values}") # Too verbose
                        cursor.execute(insert_reading_sql, reading_values)
                        
                        # Update containers table with the latest reading
                        update_container_sql = (
                            "UPDATE containers SET current_fill = %s, last_updated = %s "
                            "WHERE id = %s AND (%s > last_updated OR last_updated IS NULL)"
                        )
                        update_values = (fill_level_litres_val, timestamp_val, container_id, timestamp_val)
                        # print(f"[CSV_IMPORT_DEBUG] Row {row_num}: Updating container latest reading. SQL: {update_container_sql} with values: {update_values}") # Too verbose
                        cursor.execute(update_container_sql, update_values)
                        
                        rows_processed_count += 1
                        if rows_processed_count % 1000 == 0: # Commit every 1000 rows
                            connection.commit()
                            print(f"[CSV_IMPORT_DEBUG] Processed and committed {rows_processed_count} rows...")

                    except KeyError as e:
                        print(f"[CSV_IMPORT_DEBUG] Error: CSV Key error {e} in row {row_num}. Skipping row: {row}")
                        continue
                    except ValueError as e:
                        print(f"[CSV_IMPORT_DEBUG] Error: Data conversion error in row {row_num}: {e}. Skipping row: {row}")
                        continue
                    except Exception as e:
                        print(f"[CSV_IMPORT_DEBUG] An unexpected error occurred processing row {row_num}: {e}. SQL that might have failed was related to container: '{container_name_val}', address: '{container_address_val}'. Skipping row.")
                        continue
                
                connection.commit() # Final commit
                print(f"[CSV_IMPORT_DEBUG] Data import completed. Total rows processed in this run: {rows_processed_count}")

    except pymysql.MySQLError as e:
        print(f"[CSV_IMPORT_DEBUG] Database error during import: {e}")
        if connection: connection.rollback()
    except FileNotFoundError:
        print(f"[CSV_IMPORT_DEBUG] Error: CSV file not found at {filepath}")
    except Exception as e:
        print(f"[CSV_IMPORT_DEBUG] An unexpected error occurred during setup or file open: {e}")
        if connection: connection.rollback()
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("[CSV_IMPORT_DEBUG] Database connection closed.")

if __name__ == "__main__":
    print("[CSV_IMPORT_DEBUG] import_csv.py script execution started directly.")
    # Make sure to place your CSV file in the root of the project or provide the correct path.
    csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'augmented_common_containers_with_types.csv')
    print(f"[CSV_IMPORT_DEBUG] Resolved CSV file path: {csv_file_path}")
    if not os.path.exists(csv_file_path):
        print(f"[CSV_IMPORT_DEBUG] FATAL ERROR: CSV file not found at the resolved path: {csv_file_path}")
    else:
        import_data_from_csv(csv_file_path) 