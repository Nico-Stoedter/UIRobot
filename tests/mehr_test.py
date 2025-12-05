"""
demo_box_only.py

Standalone demo:
- Box-only collision checking for a moving tool-box along linear trajectories.
- Draws 2 trajectories, 3 static boxes and sampled positions of the moving tool box.
- Uses your tool geometry:
    offset_min = (-0.002, -0.006, 0.0)
    offset_max = ( 0.002,  0.0,   0.002)
(all in meters)
"""

import math
from typing import Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

Vector = Tuple[float, float, float]

# ------------------------ Kinematik (linear motion) ------------------------

class AxisMotion:
    def __init__(self, start: float, target: float, speed: float):
        self.start = float(start)
        self.target = float(target)
        self.speed = abs(float(speed))
        self.dir = 1.0 if self.target >= self.start else -1.0
        self.distance = abs(self.target - self.start)
        self.duration = 0.0 if self.speed == 0 else self.distance / self.speed

    def pos(self, t: float) -> float:
        if t <= 0.0:
            return self.start
        if t >= self.duration:
            return self.target
        return self.start + self.dir * self.speed * t

class Trajectory:
    """3D trajectory as separate AxisMotion on x,y,z (linear per axis)"""
    def __init__(self, x_motion: AxisMotion, y_motion: AxisMotion, z_motion: AxisMotion):
        self.x = x_motion
        self.y = y_motion
        self.z = z_motion
        self.T = max(self.x.duration, self.y.duration, self.z.duration)

    def r(self, t: float) -> Vector:
        return (self.x.pos(t), self.y.pos(t), self.z.pos(t))

def make_traj_from_speeds(start: Vector, target: Vector, speeds: Vector) -> Trajectory:
    xm = AxisMotion(start[0], target[0], speeds[0])
    ym = AxisMotion(start[1], target[1], speeds[1])
    zm = AxisMotion(start[2], target[2], speeds[2])
    return Trajectory(xm, ym, zm)

# ------------------------ Box geometry + helpers ------------------------

class Box:
    def __init__(self, bmin: Vector, bmax: Vector):
        self.bmin = (float(bmin[0]), float(bmin[1]), float(bmin[2]))
        self.bmax = (float(bmax[0]), float(bmax[1]), float(bmax[2]))

def bbox_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

def boxes_intersect(a: Box, b: Box) -> bool:
    return not (a.bmax[0] < b.bmin[0] or a.bmin[0] > b.bmax[0] or
                a.bmax[1] < b.bmin[1] or a.bmin[1] > b.bmax[1] or
                a.bmax[2] < b.bmin[2] or a.bmin[2] > b.bmax[2])

# ------------------------ Moving tool box (offsets relative to TCP) ------------------------

class MovingBox:
    def __init__(self, offset_min: Vector, offset_max: Vector):
        # offsets in meters relative to TCP (0,0,0)
        self.offset_min = (float(offset_min[0]), float(offset_min[1]), float(offset_min[2]))
        self.offset_max = (float(offset_max[0]), float(offset_max[1]), float(offset_max[2]))

    def box_at(self, pos: Vector) -> Box:
        bmin = (pos[0] + self.offset_min[0],
                pos[1] + self.offset_min[1],
                pos[2] + self.offset_min[2])
        bmax = (pos[0] + self.offset_max[0],
                pos[1] + self.offset_max[1],
                pos[2] + self.offset_max[2])
        return Box(bmin, bmax)

# ------------------------ CCD adaptive for moving box vs static box ------------------------

def bbox_intersects_box(bmin, bmax, box: Box) -> bool:
    if (bmax[0] < box.bmin[0] or bmin[0] > box.bmax[0] or
        bmax[1] < box.bmin[1] or bmin[1] > box.bmax[1] or
        bmax[2] < box.bmin[2] or bmin[2] > box.bmax[2]):
        return False
    return True

def ccd_adaptive_with_box(traj: Trajectory, moving_box: MovingBox, obstacle: Box,
                          t0: float = 0.0, t1: Optional[float] = None,
                          tol: float = 1e-3, depth_limit: int = 20) -> bool:
    """
    Adaptive CCD for movingBox vs static Box.
    Returns True if collision occurs somewhere in [t0,t1].
    """
    if t1 is None:
        t1 = traj.T

    p0 = traj.r(t0)
    p1 = traj.r(t1)
    box0 = moving_box.box_at(p0)
    box1 = moving_box.box_at(p1)

    # quick AABB of swept box
    bmin, bmax = bbox_of_points((box0.bmin, box0.bmax, box1.bmin, box1.bmax))

    # fast reject
    if not bbox_intersects_box(bmin, bmax, obstacle):
        return False

    # exact at endpoints
    if boxes_intersect(box0, obstacle) or boxes_intersect(box1, obstacle):
        return True

    # stop recursion
    if (t1 - t0) < tol or depth_limit <= 0:
        return False

    tm = 0.5 * (t0 + t1)
    return (ccd_adaptive_with_box(traj, moving_box, obstacle, t0, tm, tol, depth_limit - 1) or
            ccd_adaptive_with_box(traj, moving_box, obstacle, tm, t1, tol, depth_limit - 1))

# helper: find first collision time via recursive bisection + ccd checks
def find_first_collision_time(traj: Trajectory, moving_box: MovingBox, obstacle: Box,
                              t0: float = 0.0, t1: Optional[float] = None,
                              tol_time: float = 1e-4, max_depth: int = 30) -> Optional[float]:
    if t1 is None:
        t1 = traj.T

    # if no collision in interval, return None
    if not ccd_adaptive_with_box(traj, moving_box, obstacle, t0, t1, tol=1e-4, depth_limit=40):
        return None

    # bisection to locate earliest collision time
    lo, hi = t0, t1
    depth = 0
    while (hi - lo) > tol_time and depth < max_depth:
        mid = 0.5 * (lo + hi)
        if ccd_adaptive_with_box(traj, moving_box, obstacle, lo, mid, tol=1e-6, depth_limit=40):
            hi = mid
        else:
            lo = mid
        depth += 1

    return hi

# ------------------------ Drawing helpers ------------------------

def draw_box_wire(ax, box: Box, color='orange', linewidth=1.0, alpha=1.0):
    x = [box.bmin[0], box.bmax[0]]
    y = [box.bmin[1], box.bmax[1]]
    z = [box.bmin[2], box.bmax[2]]
    # 12 edges
    corners = [
        (x[0], y[0], z[0]), (x[1], y[0], z[0]), (x[1], y[1], z[0]), (x[0], y[1], z[0]),
        (x[0], y[0], z[1]), (x[1], y[0], z[1]), (x[1], y[1], z[1]), (x[0], y[1], z[1]),
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0), # bottom rectangle
        (4,5),(5,6),(6,7),(7,4), # top rectangle
        (0,4),(1,5),(2,6),(3,7)  # vertical edges
    ]
    for (i,j) in edges:
        xs = [corners[i][0], corners[j][0]]
        ys = [corners[i][1], corners[j][1]]
        zs = [corners[i][2], corners[j][2]]
        ax.plot(xs, ys, zs, color=color, linewidth=linewidth, alpha=alpha)

# ------------------------ Demo scene setup ------------------------

def demo():
    # --- Tool geometry (your values converted to meters) ---
    offset_min = (-0.04, -0.04, -1.0)
    offset_max = ( 0.04,  0.04,  0.0)
    tool = MovingBox(offset_min, offset_max)

    # --- Static obstacles (3 boxes) (meters) ---
    box  = Box((0.0, 0.2, 0.2), (0.1, 0.5, 0.3))

    obstacles = [("box", box)]

    # --- Two example trajectories (linear motion) ---
    start = (0.0, 0.0, 0.8)
    target = (0.0, 0.2, 0.8)

    # traj1: moderate speeds (makes T larger)
    speeds1 = (0.1, 0.1, 0.1)  # m/s
    traj1 = make_traj_from_speeds(start, target, speeds1)


    trajs = [("v=0.05,0.05,0.05", traj1)]

    # --- Collision checks and first collision times ---
    print("Collision checks:")
    coll_info = {}
    for name, traj in trajs:
        coll_info[name] = {}
        for obs_name, obs in obstacles:
            coll = ccd_adaptive_with_box(traj, tool, obs, tol=1e-4)
            t_first = None
            if coll:
                t_first = find_first_collision_time(traj, tool, obs, tol_time=1e-4)
            coll_info[name][obs_name] = (coll, t_first)
            print(f"Trajectory {name} collision with {obs_name}? -> {coll}  first_t={t_first}")

    # --- Plot everything ---
    # sample trajectories
    def sample_traj(traj, n=400):
        if traj.T <= 0:
            return np.array([traj.r(0.0)])
        ts = np.linspace(0.0, traj.T, n)
        pts = np.array([traj.r(t) for t in ts])
        return pts, ts

    p1, ts1 = sample_traj(traj1, n=400)
    #p2, ts2 = sample_traj(traj2, n=400)

    fig = plt.figure(figsize=(11,7))
    ax = fig.add_subplot(111, projection='3d')

    # trajectories
    ax.plot(p1[:,0], p1[:,1], p1[:,2], label=trajs[0][0])
    #ax.plot(p2[:,0], p2[:,1], p2[:,2], label=trajs[1][0])

    # draw static boxes
    draw_box_wire(ax, box, color='orange', linewidth=1.2, alpha=1.0)
    #draw_box_wire(ax, box1, color='magenta', linewidth=1.2, alpha=1.0)
    #draw_box_wire(ax, box2, color='red', linewidth=1.2, alpha=1.0)

    # draw sampled moving tool-box positions along traj1 and traj2
    def draw_moving_samples(traj, color='C0', n_samples=12, annotate_collision=False):
        if traj.T <= 0:
            return
        samples = np.linspace(0.0, traj.T, n_samples)
        for s in samples:
            pos = traj.r(s)
            mb = tool.box_at(pos)
            draw_box_wire(ax, mb, color=color, linewidth=0.8, alpha=0.6)
        # if collision, mark first collision pose
        if annotate_collision:
            # check earliest collision against any obstacle
            times = []
            for _, obs in obstacles:
                t = find_first_collision_time(traj, tool, obs, tol_time=1e-4)
                if t is not None:
                    times.append(t)
            if times:
                tmin = min(times)
                pos = traj.r(tmin)
                ax.scatter([pos[0]], [pos[1]], [pos[2]], color='k', s=60, marker='x')
                ax.text(pos[0], pos[1], pos[2], f" first collision t={tmin:.4f}s", color='k')

    draw_moving_samples(traj1, color='C0', n_samples=14, annotate_collision=True)
    #draw_moving_samples(traj2, color='C1', n_samples=14, annotate_collision=True)

    # plot start/target
    ax.scatter([start[0]], [start[1]], [start[2]], color='green', s=60, label='start')
    ax.scatter([target[0]], [target[1]], [target[2]], color='red', s=60, label='target')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_zlim(-1, 1)
    ax.set_title('Box-only collision demo: trajectories, obstacles, moving tool-box')
    ax.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    demo()
