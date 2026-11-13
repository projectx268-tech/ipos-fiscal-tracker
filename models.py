from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.sql import func
from database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), nullable=False)
    tin_number = Column(String(15), unique=True, nullable=False)
    vat_number = Column(String(20))
    contact_person = Column(String(100))
    phone_number = Column(String(20), nullable=False)
    alternate_phone = Column(String(20))
    email = Column(String(100))
    city = Column(String(50), default="Hawassa")
    subcity_or_woreda = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    mrc_number = Column(String(50), unique=True)
    initial_fiscalization_date = Column(Date)
    last_annual_renewal_date = Column(Date)
    next_renewal_due_date = Column(Date, nullable=False)
    device_status = Column(String(30), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JobCard(Base):
    __tablename__ = "job_cards"

    id = Column(Integer, primary_key=True, index=True)
    job_card_number = Column(String(30), unique=True, nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    received_date = Column(DateTime(timezone=True), server_default=func.now())
    expected_completion_date = Column(Date)
    reported_problem = Column(Text, nullable=False)
    received_with_accessories = Column(Text)
    requires_annual_inspection = Column(Boolean, default=False)
    status = Column(String(30), default="received")
    assigned_technician_id = Column(Integer)
    total_labor_cost = Column(Numeric(10, 2), default=0.00)
    total_parts_cost = Column(Numeric(10, 2), default=0.00)
    delivered_date = Column(DateTime(timezone=True))
    received_by_person = Column(String(100))
    notes = Column(Text)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="ቴክኒሻን (Technician)")
    is_active = Column(Boolean, default=True)