from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# የPostgreSQL ዳታቤዝ አድራሻ (Password እና Database ስምህን እንደ ራስህ አስተካክል)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost:5432/ipos_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ለእያንዳንዱ API ጥያቄ ዳታቤዝ ክፍት አድርጎ ሲያልቅ የሚዘጋ ተግባር
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()