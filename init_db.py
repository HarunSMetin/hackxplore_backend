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
            print("CSV import disabled in init - use /admin/import-csv endpoint instead.")
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