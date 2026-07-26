from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import uuid

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./scheduler.db" # Swap with postgresql:// user:pass@localhost/dbname for Postgres
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    major = Column(String, index=True)
    completed_courses = Column(JSON) 

class DBCourse(Base):
    __tablename__ = "courses"
    id = Column(String, primary_key=True, index=True) # e.g., "COMPSCI-61A"
    title = Column(String)
    department = Column(String)
    prerequisites = Column(JSON)
    seat_status = Column(String)

Base.metadata.create_all(bind=engine)

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class UserCreate(BaseModel):
    major: str
    completed_courses: list[str]

# --- Scraping Logic ---
def scrape_berkeley_catalog(department: str):
    """
    Live scraper function for classes.berkeley.edu using BeautifulSoup.
    """
    # Search the catalog by keyword/department
    url = f"https://classes.berkeley.edu/search/class/?search={department}"
    
    # We must use a User-Agent so the website doesn't immediately block us as a bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    courses = []
    
    # UC Berkeley's catalog wraps search results in list items with the class "search-result"
    course_nodes = soup.find_all("li", class_="search-result")
    
    for node in course_nodes:
        try:
            # The title node usually contains both the ID and the Title (e.g., "DATA 8 - Foundations of Data Science")
            title_node = node.find("div", class_="search-result-title")
            if not title_node:
                continue
                
            raw_title = title_node.text.strip()
            
            # Split the string to separate the course code from the human-readable title
            if " - " in raw_title:
                parts = raw_title.split(" - ", 1)
                course_id = parts[0].replace(" ", "-").strip().upper()
                course_title = parts[1].strip()
            else:
                course_id = raw_title.replace(" ", "-").upper()
                course_title = raw_title

            courses.append({
                "id": course_id,
                "title": course_title,
                "department": department.upper(),
                "prerequisites": [], # Note: Getting prereqs requires loading a second page
                "seat_status": "Pending" 
            })
        except Exception as e:
            print(f"Error parsing a course: {e}")
            continue
            
    return courses

# --- API Endpoints ---
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user_id = str(uuid.uuid4())
    db_user = DBUser(id=user_id, major=user.major, completed_courses=user.completed_courses)
    db.add(db_user)
    db.commit()
    return {"user_id": user_id}

@app.get("/users/{user_id}/eligible_courses")
def get_eligible_courses(user_id: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_courses = db.query(DBCourse).all()
    eligible = []
    
    completed = set(user.completed_courses)
    for course in all_courses:
        reqs = set(course.prerequisites)
        # Check if prerequisites are a subset of completed courses
        if reqs.issubset(completed):
            eligible.append(course)
            
    return eligible

@app.post("/admin/sync_department/{dept}")
def sync_department(dept: str, db: Session = Depends(get_db)):
    scraped_data = scrape_berkeley_catalog(dept)
    
    for item in scraped_data:
        existing = db.query(DBCourse).filter(DBCourse.id == item["id"]).first()
        if existing:
            existing.seat_status = item["seat_status"]
            existing.prerequisites = item["prerequisites"]
        else:
            new_course = DBCourse(**item)
            db.add(new_course)
    
    db.commit()
    return {"message": f"Synced {len(scraped_data)} courses for {dept}"}
