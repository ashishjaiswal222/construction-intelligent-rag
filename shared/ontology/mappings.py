from .disciplines import ConstructionDiscipline

def get_discipline_from_filename(filename: str) -> ConstructionDiscipline:
    """Very basic example of mapping filename parts to disciplines."""
    name_upper = filename.upper()
    if 'CIVIL' in name_upper or '-C-' in name_upper:
        return ConstructionDiscipline.CIVIL
    elif 'MECH' in name_upper or '-M-' in name_upper:
        return ConstructionDiscipline.MECHANICAL
    elif 'ELEC' in name_upper or '-E-' in name_upper:
        return ConstructionDiscipline.ELECTRICAL
    elif 'PLUMB' in name_upper or '-P-' in name_upper:
        return ConstructionDiscipline.PLUMBING
    elif 'ARCH' in name_upper or '-A-' in name_upper:
        return ConstructionDiscipline.ARCHITECTURAL
    elif 'STRUC' in name_upper or '-S-' in name_upper:
        return ConstructionDiscipline.STRUCTURAL
    
    return ConstructionDiscipline.UNKNOWN
