from datetime import datetime, date
import logging
from fastapi import FastAPI, Depends , HTTPException
from typing import Annotated, ClassVar,List
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
    total_members: int = 1

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
    pass
    class Config:
        orm_mode = True

class UserCredentials(BaseModel):
    username: str
    password: str
    
        
class EmployeeAttendanceLog(BaseModel):
    time_entry: datetime
    time_leave: datetime
    employee_id: int
class EmployeeAttendanceLogModel(EmployeeAttendanceLog):
    class Config:
        orm_mode = True

class EmployeeDailyLeaveRecord(BaseModel):
    time_started: date
    time_end: date
    employee_id: int
    
class EmployeeDailyLeaveRecordModel(EmployeeDailyLeaveRecord):
    class Config:
        orm_mode = True

class EmployeeHourlyLeaveRecord(BaseModel):
    time_started: datetime
    time_end: datetime
    employee_id: int

class EmployeeHourlyLeaveRecordModel(EmployeeHourlyLeaveRecord):
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

class EmployeeTeamUpdate(BaseModel):
    team_id: int

# Route to update team_id

@app.get("/teams")
async def get_all_teams(db: Session = Depends(get_db)):
    teams = db.query(models.Team).all()
    return teams


@app.post("/teams/new", response_model=TeamModel)
async def create_team(team: TeamBase, db: Session = Depends(get_db)):
    team_leader_id = team.team_leader_id
    team_leader = db.query(models.Employee).filter(models.Employee.employee_id == team_leader_id).first()
    if not team_leader:
        raise HTTPException(status_code=404, detail="کارمندی با این آیدی پیدا نشد!")
    if team_leader.team_id == 0:
        db_team = models.Team(**team.dict())
        db_team.team_leader = team_leader
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        team_leader.team_id = db_team.team_id
        db.commit()
        db.refresh(team_leader)

        return db_team
    raise HTTPException(status_code=403, detail="مدیریت تیم دیگری بر عهده این شخص میباشد.")


@app.get("/teams/{team_id}", response_model=TeamModel)
async def get_team_by_id(team_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="تیم مدنظر پیدا نشد.")
    return team

@app.get("/employees/")
async def get_employees(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    employees = db.query(models.Employee).offset(skip).limit(limit).all()
    return employees

@app.get("/employees/{employee_id}")
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد.")
    return employee

@app.post("/employee/new", response_model=EmployeeModel)
async def create_emp(emp: EmployeeBase, db: Session = Depends(get_db)):
    db_employee = models.Employee(**emp.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@app.put("/employees/{employee_id}/update-team", response_model=EmployeeModel)
async def update_employee_team(employee_id: int, team_update: EmployeeTeamUpdate, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="کارمندی با آیدی وارده یافت نشد.")
    team = db.query(models.Team).filter(models.Team.team_id == team_update.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="تیمی یافت نشد.")
    employee.team_id = team_update.team_id
    team.total_members += 1
    db.commit()
    db.refresh(employee)
    db.refresh(team)
    return employee


@app.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    # Query the database to find the employee
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        # If employee not found, raise an HTTPException with status code 404
        raise HTTPException(status_code=404, detail="کارمند یافت نشد.")

    # Delete the employee from the database
    db.delete(employee)
    db.commit()

    return {"message": "کارمند با موفقیت حذف شد"}

@app.post("/login")
async def authenticate_user(employee: UserCredentials, db: Session = Depends(get_db)):
    username = employee.username
    password = employee.password

    user = db.query(models.Employee).filter(models.Employee.username == username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="نام کاربری یا پسورد خطا است.")

    return {"message": "با موفقیت وارد شدید" , "user" : user}

@app.post("/attendance-log/", response_model=EmployeeAttendanceLogModel)
async def create_employee_attendance_log(log : EmployeeAttendanceLog,
    db: Session = Depends(get_db)
):
    # Check if the employee exists
    employee = db.query(models.Employee).filter(models.Employee.employee_id == log.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")

    # Create the attendance log
    db_attendance_log = models.EmployeeAttendanceLog(**log.dict())
    db.add(db_attendance_log)
    db.commit()
    db.refresh(db_attendance_log)
    return db_attendance_log


@app.post("/attendance-log/range", response_model=List[EmployeeAttendanceLogModel])
async def get_attendance_logs_between_dates(start_date: datetime, end_date: datetime, db: Session = Depends(get_db)):
    logs = db.query(models.EmployeeAttendanceLog).filter(
        models.EmployeeAttendanceLog.time_entry >= start_date,
        models.EmployeeAttendanceLog.time_leave <= end_date
    ).all()
    
    return logs

@app.post("/daily-leave-record/", response_model=EmployeeDailyLeaveRecordModel)
async def create_employee_daily_leave_record(record: EmployeeDailyLeaveRecord, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.employee_id == record.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")


    db_record = models.EmployeeDailyLeaveRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@app.post("/daily-leave-record/range", response_model=List[EmployeeDailyLeaveRecordModel])
async def get_daily_leave_records_between_dates(start_date: date, end_date: date, db: Session = Depends(get_db)):
    records = db.query(models.EmployeeDailyLeaveRecord).filter(
        models.EmployeeDailyLeaveRecord.time_started >= start_date,
        models.EmployeeDailyLeaveRecord.time_end <= end_date
    ).all()
    
    return records


@app.post("/hourly-leave-record/", response_model=EmployeeHourlyLeaveRecordModel)
async def create_employee_hourly_leave_record(
   record : EmployeeHourlyLeaveRecord,
    db: Session = Depends(get_db)
):
    # Check if the employee exists
    employee = db.query(models.Employee).filter(models.Employee.employee_id == record.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")

    # Create the hourly leave record
    db_attendance_log = models.EmployeeHourlyLeaveRecord(**record.dict())
    db.add(db_attendance_log)
    db.commit()
    db.refresh(db_attendance_log)
    return db_attendance_log

@app.post("/hourly-leave-record/range", response_model=List[EmployeeHourlyLeaveRecordModel])
async def get_hourly_leave_records_between_dates(start_date: datetime, end_date: datetime, db: Session = Depends(get_db)):
    records = db.query(models.EmployeeHourlyLeaveRecord).filter(
        models.EmployeeHourlyLeaveRecord.time_started >= start_date,
        models.EmployeeHourlyLeaveRecord.time_end <= end_date
    ).all()
    
    return records
