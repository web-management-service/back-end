from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(50), nullable=False)
    team_leader_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    total_members = Column(Integer, nullable=False)
    team_leader = relationship('Employee', back_populates='team' , foreign_keys=[team_leader_id])

class Employee(Base):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.team_id'), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    national_code = Column(String(10), nullable=False)
    phone_number = Column(String(11), nullable=False)
    address = Column(String(255), nullable=False)
    team = relationship('Team', back_populates='team_leader')
    attendance_log = relationship('EmployeeAttendanceLog', back_populates='employee')
    daily_leave_records = relationship('EmployeeDailyLeaveRecord', back_populates='employee')
    hourly_leave_records = relationship('EmployeeHourlyLeaveRecord', back_populates='employee')

class EmployeeAttendanceLog(Base):
    __tablename__ = 'employee_attendance_log'
    time_entry = Column(DateTime, nullable=False)
    time_leave = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), primary_key=True)

    employee = relationship('Employee', back_populates='attendance_log')

class EmployeeDailyLeaveRecord(Base):
    __tablename__ = 'employee_daily_leave_records'
    time_started = Column(Date, nullable=False)
    time_end = Column(Date, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), primary_key=True)

    employee = relationship('Employee', back_populates='daily_leave_records')

class EmployeeHourlyLeaveRecord(Base):
    __tablename__ = 'employee_hourly_leave_records'
    time_started = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), primary_key=True)

    employee = relationship('Employee', back_populates='hourly_leave_records')
