from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)

SessionLocal = scoped_session(sessionmaker(bind=engine))
