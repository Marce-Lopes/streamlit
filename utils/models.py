from dataclasses import dataclass
from enum import Enum

class KPIType(Enum):
    TEXT = "TEXT"
    GREATER_THAN = "GREATER_THAN"
    LOWER_THAN = "LOWER_THAN"

@dataclass
class KPI:
    id: str
    name: str
    description: str
    type: KPIType
    prev_target: str
    prev_achieved: str
    curr_target: str
    curr_value: str = ""
    justification: str = ""
    countermeasure: str = ""
    countermeasure_date: str = ""
    countermeasure_resp: str = ""