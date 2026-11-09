try:
    from config.config import ROLE_AREA_ACCESS, AREA_BY_PATH_START
except ImportError:
    from Project.config.config import ROLE_AREA_ACCESS, AREA_BY_PATH_START
def can_access_area(role,area): return area in ROLE_AREA_ACCESS.get(role,[])
def area_for_path(path):
    if path.endswith("/decision"): return "decision"
    for prefix,area in AREA_BY_PATH_START.items():
        if path.startswith(prefix): return area
    return None
def can_access_path(role,path):
    area=area_for_path(path); return area is None or can_access_area(role,area)
def require_area(role,area):
    if not can_access_area(role,area): raise PermissionError(f"A {role} may not use the {area} area")
    return True