import math
from typing import Callable, Tuple
from ini_manager import IniManager

Vector = Tuple[float, float, float]

# ------------------------ Trajektorien / Motoren ------------------------
class AxisMotion:
    """Einfaches Modell: konstante Geschwindigkeit bis zum Ziel, dann Verweilen."""
    def __init__(self, start: float, target: float, speed: float):
        self.start = start
        self.target = target
        self.speed = abs(speed)
        self.dir = 1.0 if target >= start else -1.0
        self.distance = abs(target - start)
        self.duration = 0.0 if self.speed == 0 else self.distance / self.speed

    def pos(self, t: float) -> float: 
        if t <= 0:
            return self.start
        if t >= self.duration:
            return self.target
        return self.start + self.dir * self.speed * t

class Trajectory:
    """Gesamttrajektorie aus drei Achsen (x,y,z)
    Jede Achse ist ein AxisMotion; r(t) liefert die 3D-Position zur Zeit t.
    """
    def __init__(self, x_motion: AxisMotion, y_motion: AxisMotion, z_motion: AxisMotion):
        self.x = x_motion
        self.y = y_motion
        self.z = z_motion
        self.T = max(self.x.duration, self.y.duration, self.z.duration)

    def r(self, t: float) -> Vector:
        return (self.x.pos(t), self.y.pos(t), self.z.pos(t))

# ------------------------ Hindernisse ------------------------
class Sphere:
    def __init__(self, center: Vector, radius: float):
        self.center = center
        self.radius = radius

    def contains(self, p: Vector) -> bool:
        return distance(p, self.center) <= self.radius
    
class Box:
    """Achsenparalleler Quader (AABB)"""
    def __init__(self, bmin: Vector, bmax: Vector):
        self.bmin = bmin
        self.bmax = bmax

    def contains(self, p: Vector) -> bool:
        x, y, z = p
        return (self.bmin[0] <= x <= self.bmax[0] and
                self.bmin[1] <= y <= self.bmax[1] and
                self.bmin[2] <= z <= self.bmax[2])

# ------------------------ Hilfsfunktionen ------------------------

def distance(a: Vector, b: Vector) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def lerp(a: Vector, b: Vector, alpha: float) -> Vector:
    return (a[0] + (b[0]-a[0])*alpha,
            a[1] + (b[1]-a[1])*alpha,
            a[2] + (b[2]-a[2])*alpha)

# ------------------------ Analytische Segment-vs-Sphere Prüfung ------------------------

def segment_sphere_collision(p0: Vector, p1: Vector, sphere: Sphere) -> bool:
    """
    Prüft ob das Liniensegment p0->p1 die Kugel (sphere) schneidet.
    Lösung durch Projektion und quadratische Gleichung (klassisch).
    """
    # Verschiebe Koordinaten so Kugelzentrum im Ursprung
    cx, cy, cz = sphere.center
    p0r = (p0[0]-cx, p0[1]-cy, p0[2]-cz)
    p1r = (p1[0]-cx, p1[1]-cy, p1[2]-cz)
    dx = p1r[0] - p0r[0]
    dy = p1r[1] - p0r[1]
    dz = p1r[2] - p0r[2]
    a = dx*dx + dy*dy + dz*dz
    b = 2*(p0r[0]*dx + p0r[1]*dy + p0r[2]*dz)
    c = p0r[0]*p0r[0] + p0r[1]*p0r[1] + p0r[2]*p0r[2] - sphere.radius*sphere.radius

    if a == 0.0:
        # Degenerater Fall: p0 == p1 als Punkt
        return c <= 0

    disc = b*b - 4*a*c
    if disc < 0:
        return False
    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2*a)
    t2 = (-b + sqrt_disc) / (2*a)
    # Segment corresponds zu t in [0,1]
    return (0.0 <= t1 <= 1.0) or (0.0 <= t2 <= 1.0)

def segment_box_collision(p0: Vector, p1: Vector, box: Box) -> bool:
    """Kollisionstest zwischen Liniensegment p0->p1 und AABB (Box)"""
    tmin, tmax = 0.0, 1.0
    for i in range(3):  # x, y, z
        d = p1[i] - p0[i]
        if abs(d) < 1e-9:
            # Linie parallel zur Achse
            if p0[i] < box.bmin[i] or p0[i] > box.bmax[i]:
                return False
        else:
            inv_d = 1.0 / d
            t1 = (box.bmin[i] - p0[i]) * inv_d
            t2 = (box.bmax[i] - p0[i]) * inv_d
            t1, t2 = min(t1, t2), max(t1, t2)
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return False
    return True

# ------------------------ Adaptive time-sampling CCD ------------------------

def bbox_of_points(points: Tuple[Vector, ...]) -> Tuple[Vector, Vector]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def bbox_intersects_sphere(bmin: Vector, bmax: Vector, sphere: Sphere) -> bool:
    # schnelle AABB-vs-sphere Test: nächster Punkt in AABB zum Kugelzentrum
    cx, cy, cz = sphere.center
    nx = max(bmin[0], min(cx, bmax[0]))
    ny = max(bmin[1], min(cy, bmax[1]))
    nz = max(bmin[2], min(cz, bmax[2]))
    return distance((nx,ny,nz), sphere.center) <= sphere.radius


def ccd_adaptive(traj: Trajectory, obstacle, t0: float = 0.0, t1: float = None,
                 tol: float = 1e-3, depth_limit: int = 20) -> bool:
    """
    Adaptive CCD: prüft rekursiv das Intervall [t0,t1] auf Kollision.
    Unterstützt Sphere und Box (AABB).
    """
    if t1 is None:
        t1 = traj.T

    p0 = traj.r(t0)
    p1 = traj.r(t1)

    # --- Bounding-Box Vorprüfung ---
    bmin, bmax = bbox_of_points((p0, p1))

    # 1. Schnelle Vorprüfung je nach Objekttyp
    if isinstance(obstacle, Sphere):
        if not bbox_intersects_sphere(bmin, bmax, obstacle):
            return False
    elif isinstance(obstacle, Box):
        # einfache AABB-Vorprüfung
        if (bmax[0] < obstacle.bmin[0] or bmin[0] > obstacle.bmax[0] or
            bmax[1] < obstacle.bmin[1] or bmin[1] > obstacle.bmax[1] or
            bmax[2] < obstacle.bmin[2] or bmin[2] > obstacle.bmax[2]):
            return False
    else:
        raise TypeError("ccd_adaptive(): unsupported obstacle type")

    # --- genaue Segmentprüfung ---
    if isinstance(obstacle, Sphere):
        if segment_sphere_collision(p0, p1, obstacle):
            return True
    elif isinstance(obstacle, Box):
        if segment_box_collision(p0, p1, obstacle):
            return True

    # --- Abbruchkriterien ---
    if (t1 - t0) < tol or depth_limit <= 0:
        return False

    # --- Rekursive Unterteilung ---
    tm = 0.5 * (t0 + t1)
    return (ccd_adaptive(traj, obstacle, t0, tm, tol, depth_limit - 1) or
            ccd_adaptive(traj, obstacle, tm, t1, tol, depth_limit - 1))

# ------------------------ Demo / Beispiele ------------------------

def make_traj_from_speeds(start: Vector, target: Vector, speeds: Vector) -> Trajectory:
    xm = AxisMotion(start[0], target[0], speeds[0])
    ym = AxisMotion(start[1], target[1], speeds[1])
    zm = AxisMotion(start[2], target[2], speeds[2])
    return Trajectory(xm, ym, zm)


def calc_collision(start, target, speed) -> tuple[bool, str]:
    ini_manager = IniManager()

    boxes_wrong_type = ini_manager.get_security_zones()
    boxes = {}

    for key, value in boxes_wrong_type.items(): #Converts .ini data in type Box()
        boxes[key] = Box(bmin=value[0], bmax=value[1])

    traj = make_traj_from_speeds(start, target, speed)

    for box_name, box_object in boxes.items():
        coll = ccd_adaptive(traj, box_object, tol=1e-3)
        print(f"Trajectory {target} collision with {box_name}? -> {coll}")

        if coll:
            return (True, box_name)
        else:
            continue
    
    return (False, "No collision")

if __name__ == '__main__':
    calc_collision((0,0,0), (0,0,0), (0,0,0))