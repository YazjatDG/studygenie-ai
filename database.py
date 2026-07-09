import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_DIR = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "studygenie.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    streak = Column(Integer, default=0)
    last_login = Column(Date, default=date.today)
    dark_mode = Column(Boolean, default=True)

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, default="#6366F1")
    homeworks = relationship("Homework", back_populates="subject", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="subject", cascade="all, delete-orphan")
    sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")

class Homework(Base):
    __tablename__ = "homework"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    priority = Column(String, default="Medium")
    status = Column(String, default="Pending")
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="homeworks")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    target_marks = Column(Float, default=100.0)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="exams")

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    duration_minutes = Column(Integer, nullable=False)
    date = Column(Date, default=date.today)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="sessions")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    flashcards = Column(Text, nullable=True)
    questions = Column(Text, nullable=True)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    target_value = Column(Float, default=100.0)
    current_value = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)

class TimetableItem(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False)
    time_slot = Column(String, nullable=False)
    subject_name = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            default_user = User(username="Student", streak=5, last_login=date.today(), dark_mode=True)
            db.add(default_user)
            
            sub1 = Subject(name="Mathematics", color="#3B82F6")
            sub2 = Subject(name="Physics", color="#8B5CF6")
            sub3 = Subject(name="Computer Science", color="#EC4899")
            db.add_all([sub1, sub2, sub3])
            db.commit()

            db.add_all([
                Homework(title="Calculus Assignment 3", due_date=date.today(), priority="High", status="Pending", subject_id=sub1.id),
                Homework(title="Lab Report 2", due_date=date.today(), priority="Medium", status="Completed", subject_id=sub2.id),
                Exam(title="Mid-Term Exam", date=date.today(), target_marks=95.0, subject_id=sub2.id),
                StudySession(duration_minutes=45, date=date.today(), subject_id=sub1.id),
                StudySession(duration_minutes=60, date=date.today(), subject_id=sub3.id),
                Goal(description="Study 3 hours daily", target_value=180, current_value=105, completed=False),
                Goal(description="Finish Physics mechanics module", target_value=100, current_value=100, completed=True)
            ])
            
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            slots = ["09:00 AM - 10:30 AM", "11:00 AM - 12:30 PM", "02:00 PM - 03:30 PM"]
            for d in days:
                db.add(TimetableItem(day=d, time_slot=slots[0], subject_name="Mathematics"))
                db.add(TimetableItem(day=d, time_slot=slots[1], subject_name="Physics"))
                db.add(TimetableItem(day=d, time_slot=slots[2], subject_name="Computer Science"))
                
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
