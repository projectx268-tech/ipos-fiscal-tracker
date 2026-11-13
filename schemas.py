from pydantic import BaseModel
from datetime import date
from typing import Optional

class MachineCheckIn(BaseModel):
    client_name: str
    tin: str
    phone: str
    model: str
    serial: str
    mrc: str
    entry_date: date
    last_renewal_date: date
    problem: str

# ለEdit (ማስተካከያ) የሚያገለግል Schema
class MachineUpdate(BaseModel):
    client_name: str
    tin: str
    phone: str
    model: str
    serial: str
    mrc: str
    last_renewal_date: date
    problem: str
    status: str

class MachineResponse(BaseModel):
    id: str
    clientName: str
    tin: str
    phone: str
    model: str
    serial: str
    mrc: Optional[str] = None
    entryDate: str
    lastRenewalDate: str
    dueDate: str
    daysLeft: int
    problem: str
    status: str

    class Config:
        from_attributes = True