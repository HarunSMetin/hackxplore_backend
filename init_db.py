from database import engine
from models.container import Base as ContainerBase
from models.truck import Base as TruckBase
import os
import sys
from sqlalchemy import text

def init_db():
    print("Creating database tables if they don't exist...")
    
    # Create all tables
    ContainerBase.metadata.create_all(bind=engine)
    TruckBase.metadata.create_all(bind=engine)
    
    print("Database tables created successfully.")

    # Check if this is first run by checking if tables are empty
    with engine.connect() as connection:
        # Check containers table
        result = connection.execute(text("SELECT COUNT(*) FROM containers"))
        containers_count = result.scalar()
        
        # Check trucks table
        result = connection.execute(text("SELECT COUNT(*) FROM trucks"))
        trucks_count = result.scalar()
        
        if containers_count == 0:
            print("First setup detected - empty containers table.")
            print("Running initial data import...")
            try:
                # Add the scripts directory to the Python path
                sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
                from scripts.import_csv import import_data_from_csv
                
                csv_file_path = os.path.join(os.path.dirname(__file__), 
                                           "augmented_common_containers_with_types.csv")
                if os.path.exists(csv_file_path):
                    print(f"Importing data from {csv_file_path}...")
                    import_data_from_csv(csv_file_path)
                else:
                    print(f"CSV file not found: {csv_file_path}")
                    print("Skipping data import. You can run it manually later.")
            except Exception as e:
                print(f"Error during initial data import: {e}")
                print("Continuing with startup...")
        else:
            print(f"Database already contains {containers_count} containers.")
        
        if trucks_count == 0:
            print("First setup detected - empty trucks table.")
            print("Running initial truck data import...")
            try:
                from scripts.seed_trucks import seed_trucks
                seed_trucks()
                print("Initial truck data imported successfully.")
            except Exception as e:
                print(f"Error during truck data import: {e}")
                print("Continuing with startup...")

        print(f"Database contains {trucks_count} trucks.")

if __name__ == "__main__":
    init_db()