from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
import os
DB_URL=os.getenv("DB_URL","sqlite:///./data.db")
engine=create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)
Base=declarative_base()
class Interview(Base):
    __tablename__="interviews"; id=Column(String, primary_key=True, index=True); candidate_email=Column(String); created_at=Column(DateTime, server_default=func.now())
class Answer(Base):
    __tablename__="answers"; id=Column(Integer, primary_key=True, autoincrement=True); interview_id=Column(String, index=True); question_id=Column(String, index=True); score=Column(Float, default=0.0); feedback=Column(Text, default=""); answer_text=Column(Text); answer_table_json=Column(Text); created_at=Column(DateTime, server_default=func.now())
def init_db(): Base.metadata.create_all(bind=engine)
