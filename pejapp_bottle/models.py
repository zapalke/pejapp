from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    bio = Column(Text, nullable=True)
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    date_posted = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_flag = Column(Boolean, default=False)
    original_content = Column(Text, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")
