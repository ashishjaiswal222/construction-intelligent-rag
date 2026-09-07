from enum import Enum

class ConstructionDiscipline(str, Enum):
    CIVIL = "Civil"
    STRUCTURAL = "Structural"
    MECHANICAL = "Mechanical"
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    HVAC = "HVAC"
    ARCHITECTURAL = "Architectural"
    LANDSCAPING = "Landscaping"
    FIRE_PROTECTION = "Fire Protection"
    TELECOMMUNICATIONS = "Telecommunications"
    UNKNOWN = "Unknown"
