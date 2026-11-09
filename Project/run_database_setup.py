from persistence.database import init_db, SessionLocal
from persistence.repository import Repository
def main():
    init_db()
    db=SessionLocal()
    try:
        repo=Repository(db); repo.seed_users(); repo.import_csv()
        print("Database setup complete")
    finally: db.close()
if __name__=="__main__": main()