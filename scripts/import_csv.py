import csv
import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

# Database connection details from .env
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306)) 

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

def import_data_from_csv(filepath, batch_size=100):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            batch = []
            containers_cache = {}
            
            with open(filepath, mode='r', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                rows_processed = 0
                
                for row in csv_reader:
                    try:
                        # Process row and prepare data
                        container_data = prepare_container_data(row)
                        reading_data = prepare_reading_data(row)
                        
                        batch.append((container_data, reading_data))
                        rows_processed += 1
                        
                        # Process batch when it reaches batch_size
                        if len(batch) >= batch_size:
                            process_batch(cursor, batch, containers_cache)
                            connection.commit()
                            print(f"[CSV_IMPORT_DEBUG] Committed batch of {batch_size} rows. Total processed: {rows_processed}")
                            batch = []
                            
                    except Exception as e:
                        print(f"[CSV_IMPORT_DEBUG] Error processing row: {e}")
                        continue
                
                # Process remaining batch
                if batch:
                    process_batch(cursor, batch, containers_cache)
                    connection.commit()
                    
            print(f"[CSV_IMPORT_DEBUG] Import completed. Total rows processed: {rows_processed}")
            
    except Exception as e:
        print(f"[CSV_IMPORT_DEBUG] Fatal error during import: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

def process_batch(cursor, batch, containers_cache):
    for container_data, reading_data in batch:
        container_key = (container_data['name'], container_data['address'])
        
        # Get or create container with retry logic
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                container_id = get_or_create_container(cursor, container_data, containers_cache, container_key)
                # Insert reading with container_id
                insert_reading(cursor, container_id, reading_data)
                # Update container's current fill level
                update_container_fill(cursor, container_id, reading_data)
                break
            except pymysql.OperationalError as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise
                time.sleep(0.1 * retry_count)  # Exponential backoff

def get_or_create_container(cursor, container_data, containers_cache, container_key):
    if container_key in containers_cache:
        return containers_cache[container_key]
        
    # Use SELECT ... FOR UPDATE to prevent race conditions
    select_sql = "SELECT id FROM containers WHERE name = %s AND address = %s FOR UPDATE"
    cursor.execute(select_sql, (container_data['name'], container_data['address']))
    result = cursor.fetchone()
    
    if result:
        container_id = result['id']
    else:
        insert_sql = """
            INSERT INTO containers 
            (name, address, location_lat, location_lng, type, capacity, current_fill, last_updated)
            VALUES (%(name)s, %(address)s, %(location_lat)s, %(location_lng)s, 
                    %(type)s, %(capacity)s, %(current_fill)s, %(last_updated)s)
        """
        cursor.execute(insert_sql, container_data)
        container_id = cursor.lastrowid
        
    containers_cache[container_key] = container_id
    return container_id

def prepare_container_data(row):
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
    
    # Extract and convert data
    name = row[column_mapping['csv_name']]
    address = row[column_mapping['csv_address']]
    location_lat = float(row[column_mapping['csv_latitude']].replace(',', '.'))
    location_lng = float(row[column_mapping['csv_longitude']].replace(',', '.'))
    type_ = row[column_mapping['csv_type']]
    capacity = convert_capacity_to_litres(row[column_mapping['csv_capacity']])
    current_fill = convert_fill_to_litres(row[column_mapping['csv_fill_level']])
    last_updated = parse_timestamp(row[column_mapping['csv_date']], row[column_mapping['csv_time']])
    
    return {
        'name': name,
        'address': address,
        'location_lat': location_lat,
        'location_lng': location_lng,
        'type': type_,
        'capacity': capacity,
        'current_fill': current_fill,
        'last_updated': last_updated
    }

def prepare_reading_data(row):
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
    
    # Extract and convert data
    date = row[column_mapping['csv_date']]
    time = row[column_mapping['csv_time']]
    fill_level = convert_fill_to_litres(row[column_mapping['csv_fill_level']])
    
    timestamp = parse_timestamp(date, time)
    
    return {
        'timestamp': timestamp,
        'current_fill': fill_level
    }

def insert_reading(cursor, container_id, reading_data):
    insert_reading_sql = "INSERT INTO container_readings (container_id, timestamp, current_fill) VALUES (%s, %s, %s)"
    reading_values = (container_id, reading_data['timestamp'], reading_data['current_fill'])
    cursor.execute(insert_reading_sql, reading_values)

def update_container_fill(cursor, container_id, reading_data):
    update_container_sql = (
        "UPDATE containers SET current_fill = %s, last_updated = %s "
        "WHERE id = %s AND (%s > last_updated OR last_updated IS NULL)"
    )
    update_values = (reading_data['current_fill'], reading_data['timestamp'], container_id, reading_data['timestamp'])
    cursor.execute(update_container_sql, update_values)

if __name__ == "__main__":
    print("[CSV_IMPORT_DEBUG] import_csv.py script execution started directly.")
    # Make sure to place your CSV file in the root of the project or provide the correct path.
    csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'augmented_common_containers_with_types.csv')
    print(f"[CSV_IMPORT_DEBUG] Resolved CSV file path: {csv_file_path}")
    if not os.path.exists(csv_file_path):
        print(f"[CSV_IMPORT_DEBUG] FATAL ERROR: CSV file not found at the resolved path: {csv_file_path}")
    else:
        import_data_from_csv(csv_file_path)