from api.constraints import config
from api.utils.logger import get_logger
from api.database.interface import DatabaseInterface

logger = get_logger("api.database")

def get_local_database():
    logger.info("Using local database configuration.")
    from api.database.local import LocalDatabase
    database = LocalDatabase()
    logger.info("Local database initialized successfully.")
    return database

db : DatabaseInterface

try:
    if config.get("Database",{}).get("local", True):
        db = get_local_database()
    else:
        logger.info("Using Firebase database configuration.")
        try:
            from api.database.firebase import FirebaseDB
            db = FirebaseDB()
            logger.info("Firebase database initialized successfully.")
        except:
            logger.warning("Failed to import Firebase database module. Trying local database.")
            db = get_local_database()
            
except Exception as e:
    logger.error(f"An error occurred while initializing the database: {e}")        
    exit(1)