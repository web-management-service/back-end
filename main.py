from fastapi import FastAPI, Depends
from typing import Annotated, ClassVar
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
import models

app = FastAPI()

# Set up CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # Add the URL of your React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TeamBase(BaseModel):
    team_name: str
    team_leader_id: int
    total_members: int

class TeamModel(TeamBase):
    class Config:
        orm_mode = True

class EmployeeBase(BaseModel):
    team_id: int
    first_name: str
    last_name: str
    username: str
    password: str
    national_code: str
    phone_number: str
    address: str

class EmployeeModel(EmployeeBase):
    class Config:
        orm_mode = True

        
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/teams/new", response_model=TeamModel)
async def create_team(team: TeamBase, db: Session = Depends(get_db)):
    team_leader_id = team.team_leader_id
    team_leader = db.query(models.Employee).filter(models.Employee.employee_id == team_leader_id).first()
    if not team_leader:
        raise HTTPException(status_code=404, detail="Team leader not found")
    db_team = models.Team(**team.dict())
    db_team.team_leader = team_leader
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@app.post("/employee/new", response_model=EmployeeModel)
async def create_emp(emp: EmployeeBase, db: Session = Depends(get_db)):
    db_employee = models.Employee(**emp.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee