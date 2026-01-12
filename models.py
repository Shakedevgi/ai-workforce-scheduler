from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# --- Input Models ---

class EmployeeConfig(BaseModel):
    name: str
    min_shifts: int
    max_shifts: int
    min_shabbat: int
    max_shabbat: int
    shabbat_night_only: bool = False

class UnavailabilityConstraint(BaseModel):
    employee_name: str
    day: int
    shift: Optional[int] = None  # 0=Morning, 1=Night, None=All Day

class SolverConfig(BaseModel):
    weight_deficit: int = 10     # Weight for missing min_shifts
    weight_balance: int = 1      # Weight for M/N balance
    timeout_seconds: float = 10.0

class ScheduleRequest(BaseModel):
    year: int
    month: int
    employees: List[EmployeeConfig]
    constraints: List[UnavailabilityConstraint] = []
    config: SolverConfig = SolverConfig()

# --- Output Models ---

class ShiftAssignment(BaseModel):
    day: int
    day_name: str
    morning_employee: Optional[str]
    night_employee: Optional[str]
    is_shabbat_morning: bool
    is_shabbat_night: bool

class EmployeeStats(BaseModel):
    total_shifts: int
    morning_shifts: int
    night_shifts: int
    shabbat_shifts: int
    min_shifts_req: int
    max_shifts_req: int
    min_shabbat_req: int
    max_shabbat_req: int

class SolverMetadata(BaseModel):
    status: str
    objective_value: float
    wall_time: float

class ScheduleResponse(BaseModel):
    metadata: SolverMetadata
    schedule: List[ShiftAssignment]
    statistics: Dict[str, EmployeeStats]