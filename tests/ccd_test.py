"""
ccd_example.py

Konkretes Beispiel für zeit-parametrisierte Kollisionsprüfung (Continuous Collision Detection)
für drei unabhängige Achsen (x,y,z).

Enthalten:
- Zeitparametrisierte lineare Achsenbewegung (mit Stop, wenn Ziel erreicht)
- Analytische Segment-vs-Sphere Prüfung (für lineare Abschnitte)
- Adaptive Zeit-Sampling (Bisection) als Fallback/Allgemeinlösung
- Demo: zwei Geschwindigkeitssets (10,10,10) vs (50,2,2) mit gleicher Start-/Ziel-Config
- Optionaler Plot, wenn matplotlib installiert ist

Einfach ausführen: python ccd_example.py
"""

import math
from typing import Callable, Tuple

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
        self.duration = 0.0 if self.speed == 0 else self.distance / self.speed # self.duration muss möglicherweise bearbeitet werden

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


def demo():
    start = (0.0, 0.0, 0.0)
    target = (30.0, 10.0, 10.0)

    #sphere = Sphere(center=(0.0, 0.0, 5.0), radius=0)
    box = Box(bmin=(25.0, 5.0, 0.0), bmax=(35.0, 8.0, 2.0))
    box1 = Box(bmin=(0.0, 4.0, 0.0), bmax=(5.0, 6.0, 2.0))
    box2 = Box(bmin=(25.0, 9.0, 0.0), bmax=(30.0, 10.0, 9.0))

    speeds1 = (10.0, 10.0, 10.0)
    speeds2 = (50.0, 2.0, 2.0)

    traj1 = make_traj_from_speeds(start, target, speeds1)
    traj2 = make_traj_from_speeds(start, target, speeds2)

    #print("Traj1 durations (x,y,z):", traj1.x.duration, traj1.y.duration, traj1.z.duration, "T=", traj1.T)
    #print("Traj2 durations (x,y,z):", traj2.x.duration, traj2.y.duration, traj2.z.duration, "T=", traj2.T)

    for name, traj in [("v=10,10,10", traj1), ("v=50,2,2", traj2)]:
        for obs_name, obs in [("box", box), ("box1", box1), ("box2", box2)]:
            coll = ccd_adaptive(traj, obs, tol=1e-3)
            print(f"Trajectory {name} collision with {obs_name}? -> {coll}")


    # optional: sample and print a few points
    #print("\nSampled positions (traj1):")
    #for t in [0.0, 0.5, 1.0, 2.5, 5.0]:
    #    if t <= traj1.T:
    #        print(t, traj1.r(t))

    # 3D-Plot der Trajektorien und Hindernisse
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        import numpy as np

        def sample_traj(traj, n=200):
            ts = np.linspace(0, traj.T, n)
            pts = np.array([traj.r(t) for t in ts])
            return pts

        p1 = sample_traj(traj1)
        p2 = sample_traj(traj2)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(p1[:,0], p1[:,1], p1[:,2], label="v=" + str(speeds1).strip("()").replace(".0", ""), color='C0')
        ax.plot(p2[:,0], p2[:,1], p2[:,2], label="v=" + str(speeds2).strip("()").replace(".0", ""), color='C1')

        # --- Kugel (als transparente Oberfläche) ---
        #u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
        #x = sphere.center[0] + sphere.radius * np.cos(u) * np.sin(v)
        #y = sphere.center[1] + sphere.radius * np.sin(u) * np.sin(v)
        #z = sphere.center[2] + sphere.radius * np.cos(v)
        #ax.plot_surface(x, y, z, color='blue', alpha=0.2, linewidth=0)

        # --- Quader (Drahtgitter) ---
        def draw_box(ax, box, color='orange'):
            x = [box.bmin[0], box.bmax[0]]
            y = [box.bmin[1], box.bmax[1]]
            z = [box.bmin[2], box.bmax[2]]
            for xs in [x[0], x[1]]:
                ax.plot([xs, xs], [y[0], y[0]], [z[0], z[1]], color=color)
                ax.plot([xs, xs], [y[1], y[1]], [z[0], z[1]], color=color)
                ax.plot([xs, xs], [y[0], y[1]], [z[0], z[0]], color=color)
                ax.plot([xs, xs], [y[0], y[1]], [z[1], z[1]], color=color)
            for ys in [y[0], y[1]]:
                ax.plot([x[0], x[1]], [ys, ys], [z[0], z[0]], color=color)
                ax.plot([x[0], x[1]], [ys, ys], [z[1], z[1]], color=color)
            for zs in [z[0], z[1]]:
                ax.plot([x[0], x[0]], [y[0], y[1]], [zs, zs], color=color)
                ax.plot([x[1], x[1]], [y[0], y[1]], [zs, zs], color=color)

        draw_box(ax, box, color='orange')
        draw_box(ax, box1, color='magenta')  # zweite Box mit anderer Farbe
        draw_box(ax, box2, color='red')  # zweite Box mit anderer Farbe

        ax.plot([], [], [], color='orange', label='Box')
        ax.plot([], [], [], color='magenta', label='Box1')
        ax.plot([], [], [], color='red', label='Box2')

        # --- Start/Zielpunkte ---
        ax.scatter(start[0], start[1], start[2], c='green', s=50, label='Start')
        ax.scatter(target[0], target[1], target[2], c='red', s=50, label='Ziel')

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.legend()
        ax.set_title('3D-Trajektorien mit Kugel- und Quader-Hindernissen')
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print("Plot error:", e)


if __name__ == '__main__':
    demo()
