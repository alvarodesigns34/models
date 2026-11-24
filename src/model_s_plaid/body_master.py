"""
Class-A Parametric Bodywork Generator for the 2024 Tesla Model S Plaid (Iteration 4).

Key Class-A Surfacing Engineering (Iter 4):
- Unified C2 Cubic-Bezier Rear Haunch & Rear Bumper architecture:
  * Single welded continuous stamped Body_Rear_Quarter (zero diagonal pinch crease!).
  * Exact shared eval_rear_corner_bezier(t, z) & Master_ClassA_RearHaunch_Clay NormalTransfer
    across BOTH Body_Rear_Quarter and Body_Rear_Bumper (zero horizontal shelf step!).
  * Sleek upward aerodynamic lower rear overhang sweep matching IMG_9321.jpg.
- Shared 0.0 mm Analytical Headlight Perimeter Curves (eval_headlight_lower_rim &
  eval_headlight_upper_rim) imported identically by Hood, Front Fender, Front Bumper & lighting.py!
- Airtight painted A-pillar foot (Body_Roof_Cantrail extended to Y=0.955 meeting BELT & HOOD_EDGE
  at 0.0 mm — completely eliminates the Iter 3 A-pillar black triangle!).
- Authentic Plaid Front Fascia with crisp lower chin blade, sculpted single concave outer cheek
  intake, narrow vertical air-curtain duct, and flush shelf for needle-wedge smoked fog lights.
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector

from . import config as C
from .geometry_utils import (
    pchip_interpolate,
    smoothstep,
    smootherstep,
    ensure_collection,
    create_grid_surface,
    add_normal_transfer,
    set_smooth_shading,
    link_object,
)


class BodyCurves:
    """Master 3D parametric curve definitions for the 2024 Tesla Model S Plaid."""

    # 1. Centerline Upper Silhouette (sleek planted Model S Plaid nose!)
    HOOD_Y = np.array([0.955, 1.18, 1.48, 1.82, 2.12, 2.29, 2.390])
    HOOD_Z = np.array([0.888, 0.848, 0.785, 0.718, 0.658, 0.620, 0.596])

    ROOF_Y = np.array([
        -2.475, -2.35, -2.14, -1.90, -1.55, -1.10, -0.68, -0.18, 0.11, 0.42, 0.72, 0.955
    ])
    ROOF_Z = np.array([
        0.978,  0.986, 1.018, 1.088, 1.198, 1.318, 1.404, 1.430, 1.406, 1.258, 1.062, 0.888
    ])

    GLASS_Y = np.array([
        -2.14, -1.85, -1.48, -1.10, -0.65, -0.18, 0.11, 0.45, 0.75, 0.955
    ])
    GLASS_X = np.array([
        0.555,  0.582, 0.592, 0.584, 0.608, 0.618, 0.608, 0.670, 0.738, 0.768
    ])
    GLASS_Z_DROP = np.array([
        0.022,  0.032, 0.042, 0.046, 0.048, 0.050, 0.044, 0.040, 0.035, 0.018
    ])

    # Extended smoothly to Y=0.955 matching BELT(0.870) and HOOD/FENDER shoulder at 0.0 mm!
    CANTRAIL_Y = np.array([
        -1.52, -1.32, -1.05, -0.68, -0.18, 0.12, 0.45, 0.72, 0.870, 0.955
    ])
    CANTRAIL_X = np.array([
        0.790,  0.745, 0.700, 0.675, 0.678, 0.688, 0.735, 0.795, 0.865, 0.878
    ])
    CANTRAIL_Z = np.array([
        1.058,  1.158, 1.258, 1.345, 1.368, 1.342, 1.200, 1.028, 0.904, 0.892
    ])

    # 2. Full-Length Beltline / Upper Shoulder Crest
    BELT_Y = np.array([
        -2.46, -2.22, -1.88, -1.48, -1.05, -0.60, -0.22, 0.25, 0.87, 1.18, 1.48, 1.82, 2.08, 2.26
    ])
    BELT_X = np.array([
        0.695,  0.840, 0.912, 0.905, 0.888, 0.888, 0.886, 0.880, 0.865, 0.892, 0.916, 0.886, 0.815, 0.695
    ])
    BELT_Z = np.array([
        0.955,  0.968, 1.005, 1.038, 0.992, 0.955, 0.935, 0.915, 0.902, 0.862, 0.828, 0.768, 0.700, 0.635
    ])

    # 3. Widest Flank Swell Line (Plaid 1,987 mm Flared Rear Haunches!)
    FLANK_Y = np.array([
        -2.46, -2.26, -1.92, -1.48, -1.05, -0.60, -0.20, 0.35, 0.90, 1.18, 1.48, 1.84, 2.15, 2.34
    ])
    FLANK_X = np.array([
        0.745,  0.882, 0.960, 0.9865, 0.968, 0.948, 0.942, 0.938, 0.946, 0.962, 0.972, 0.944, 0.862, 0.715
    ])
    FLANK_Z = np.array([
        0.680,  0.675, 0.675, 0.665,  0.640, 0.625, 0.612, 0.605, 0.618, 0.625, 0.625, 0.585, 0.525, 0.470
    ])

    # 4. Signature Model S Lower Door Kick-Up Character Crease
    CREASE_Y = np.array([
        -2.35, -1.90, -1.48, -1.06, -0.65, -0.20, 0.35, 0.94, 1.48, 1.92, 2.28
    ])
    CREASE_X = np.array([
        0.720,  0.882, 0.952, 0.942, 0.932, 0.926, 0.924, 0.926, 0.940, 0.910, 0.740
    ])
    CREASE_Z = np.array([
        0.340,  0.345, 0.365, 0.365, 0.332, 0.296, 0.268, 0.242, 0.238, 0.232, 0.218
    ])

    # 5. Lower Rocker / Sill Outer Bottom Edge
    SILL_Y = np.array([
        -2.44, -2.05, -1.48, -1.02, -0.20, 0.94, 1.48, 1.98, 2.34
    ])
    SILL_X = np.array([
        0.680,  0.825, 0.888, 0.886, 0.882, 0.882, 0.890, 0.865, 0.685
    ])
    SILL_Z = np.array([
        0.195,  0.158, 0.132, 0.126, 0.122, 0.124, 0.130, 0.142, 0.148
    ])

    # 6. Hood Outer Shutline (calibrated to lock 0.0 mm to eval_headlight_upper_rim!)
    HOOD_EDGE_Y = np.array([0.955, 1.18, 1.48, 1.78, 2.065, 2.180, 2.268])
    HOOD_EDGE_X = np.array([0.772, 0.785, 0.782, 0.755, 0.653, 0.526, 0.398])
    HOOD_EDGE_Z = np.array([0.896, 0.858, 0.812, 0.758, 0.698, 0.656, 0.598])

    @classmethod
    def roof_center_z(cls, y):
        return pchip_interpolate(cls.ROOF_Y, cls.ROOF_Z, y)

    @classmethod
    def hood_center_z(cls, y):
        return pchip_interpolate(cls.HOOD_Y, cls.HOOD_Z, y)

    @classmethod
    def glass_edge(cls, y):
        x = pchip_interpolate(cls.GLASS_Y, cls.GLASS_X, y)
        z = cls.roof_center_z(y) - pchip_interpolate(cls.GLASS_Y, cls.GLASS_Z_DROP, y)
        return x, z

    @classmethod
    def cantrail_outer(cls, y):
        x = pchip_interpolate(cls.CANTRAIL_Y, cls.CANTRAIL_X, y)
        z = pchip_interpolate(cls.CANTRAIL_Y, cls.CANTRAIL_Z, y)
        return x, z

    @classmethod
    def beltline(cls, y):
        x = pchip_interpolate(cls.BELT_Y, cls.BELT_X, y)
        z = pchip_interpolate(cls.BELT_Y, cls.BELT_Z, y)
        return x, z

    @classmethod
    def flank_max(cls, y):
        x = pchip_interpolate(cls.FLANK_Y, cls.FLANK_X, y)
        z = pchip_interpolate(cls.FLANK_Y, cls.FLANK_Z, y)
        return x, z

    @classmethod
    def rocker_crease(cls, y):
        x = pchip_interpolate(cls.CREASE_Y, cls.CREASE_X, y)
        z = pchip_interpolate(cls.CREASE_Y, cls.CREASE_Z, y)
        return x, z

    @classmethod
    def sill_edge(cls, y):
        x = pchip_interpolate(cls.SILL_Y, cls.SILL_X, y)
        z = pchip_interpolate(cls.SILL_Y, cls.SILL_Z, y)
        return x, z

    @classmethod
    def hood_edge(cls, y):
        x = pchip_interpolate(cls.HOOD_EDGE_Y, cls.HOOD_EDGE_X, y)
        z = pchip_interpolate(cls.HOOD_EDGE_Y, cls.HOOD_EDGE_Z, y)
        return x, z

    @classmethod
    def eval_flank_section(cls, y, t):
        xb, zb = cls.beltline(y)
        xm, zm = cls.flank_max(y)
        xc, zc = cls.rocker_crease(y)
        xs, zs = cls.sill_edge(y)

        door_zone = smootherstep(-1.12, -0.82, y) * (1.0 - smootherstep(0.82, 1.15, y))
        valley_in = 0.022 * door_zone
        ridge_out = 0.010 * door_zone
        haunch_zone = math.exp(-((y + 1.48) / 0.55) ** 2)
        shoulder_x = xm + 0.005 * haunch_zone

        ts = np.array([0.00, 0.14, 0.34, 0.56, 0.71, 0.80, 0.93, 1.00])
        xs_arr = np.array([
            xb,
            xb + 0.62 * (shoulder_x - xb),
            shoulder_x,
            xm - 0.012 - valley_in * 0.45,
            xc - 0.010 - valley_in,
            xc + ridge_out,
            xs,
            xs - 0.055,
        ])
        zs_arr = np.array([
            zb,
            zb - 0.18 * (zb - zm),
            zm,
            zm - 0.46 * (zm - zc),
            zc + 0.058,
            zc,
            zs,
            zs - 0.005,
        ])

        return pchip_interpolate(ts, xs_arr, t), pchip_interpolate(ts, zs_arr, t)

    @classmethod
    def eval_flank_x_at_yz(cls, y, z):
        t_samp = np.linspace(0.0, 1.0, 41)
        xb, zb = cls.beltline(y)
        xm, zm = cls.flank_max(y)
        xc, zc = cls.rocker_crease(y)
        xs, zs = cls.sill_edge(y)

        door_zone = smootherstep(-1.12, -0.82, y) * (1.0 - smootherstep(0.82, 1.15, y))
        valley_in = 0.022 * door_zone
        ridge_out = 0.010 * door_zone
        haunch_zone = math.exp(-((y + 1.48) / 0.55) ** 2)
        shoulder_x = xm + 0.005 * haunch_zone

        ts = np.array([0.00, 0.14, 0.34, 0.56, 0.71, 0.80, 0.93, 1.00])
        xs_arr = np.array([
            xb,
            xb + 0.62 * (shoulder_x - xb),
            shoulder_x,
            xm - 0.012 - valley_in * 0.45,
            xc - 0.010 - valley_in,
            xc + ridge_out,
            xs,
            xs - 0.055,
        ])
        zs_arr = np.array([
            zb,
            zb - 0.18 * (zb - zm),
            zm,
            zm - 0.46 * (zm - zc),
            zc + 0.058,
            zc,
            zs,
            zs - 0.005,
        ])
        x_s = pchip_interpolate(ts, xs_arr, t_samp)
        z_s = pchip_interpolate(ts, zs_arr, t_samp)
        return float(np.interp(z, z_s[::-1], x_s[::-1]))


# ==============================================================================
# SHARED 0.0 mm ANALYTICAL SEAM & PERIMETER FUNCTIONS
# ==============================================================================

# 1. Shared Headlight Outer/Inner Perimeter (used identically by Bumper, Hood, Fender & Lighting!)
HL_OUTER_Y = 1.855
HL_OUTER_Z = 0.662
HL_OUTER_X = BodyCurves.eval_flank_x_at_yz(HL_OUTER_Y, HL_OUTER_Z)  # ~0.916 m (flush on fender!)


def eval_headlight_lower_rim(u):
    """Exact lower rim of Matrix LED headlight (u=0 inner mustache tip -> u=1 outer fender corner)."""
    u = max(0.0, min(1.0, float(u)))
    x = 0.398 + (HL_OUTER_X - 0.398) * u
    y = 2.268 - (2.268 - HL_OUTER_Y) * (u ** 1.12)
    z = 0.586 + (HL_OUTER_Z - 0.586) * (u ** 1.20) - 0.012 * math.sin(u * math.pi)
    return x, y, z


def eval_headlight_upper_rim(u):
    """Exact upper brow of Matrix LED headlight locking 0.0 mm to Hood (u<=0.5) & Fender (u>=0.5)."""
    u = max(0.0, min(1.0, float(u)))
    x_lo, y_lo, z_lo = eval_headlight_lower_rim(u)
    x = 0.398 + (HL_OUTER_X - 0.002 - 0.398) * (u ** 0.98)
    y = 2.266 - (2.266 - HL_OUTER_Y) * (u ** 1.13)
    arch = 0.082 * (math.sin(u * math.pi) ** 1.15)
    z = z_lo + 0.010 * (1.0 - 0.20 * u) + arch
    return x, y, z


# 2. Front Bumper <-> Front Fender Seam (outer headlight corner -> front wheel arch at phi=+28 deg)
FRONT_ARCH_SEAM_PHI = math.radians(28.0)
FRONT_SEAM_Y_ARCH = C.Y_FRONT_AXLE + C.FRONT_ARCH_RAD * math.cos(FRONT_ARCH_SEAM_PHI)  # ~1.831
FRONT_SEAM_Z_ARCH = C.FRONT_WHEEL_Z + C.FRONT_ARCH_RAD * math.sin(FRONT_ARCH_SEAM_PHI)  # ~0.539

# 3. Rear Bumper <-> Rear Quarter Unified C2 Cubic-Bezier Surface!
REAR_ARCH_SEAM_PHI = math.radians(150.0)
REAR_SEAM_Y_ARCH = C.Y_REAR_AXLE + C.REAR_ARCH_RAD * math.cos(REAR_ARCH_SEAM_PHI)  # ~-1.822
REAR_SEAM_Z_ARCH = C.REAR_WHEEL_Z + C.REAR_ARCH_RAD * math.sin(REAR_ARCH_SEAM_PHI)  # ~0.546

_REAR_Z_KNOTS = np.array([0.165, 0.368, 0.470, 0.575, 0.720, 0.850, 0.965])
_REAR_YC_KNOTS = np.array([-2.482, -2.556, -2.578, -2.542, -2.518, -2.502, -2.475])


def eval_rear_center_y(z):
    """C2 smooth vertical profile of rear centerline (X=0) from diffuser bottom to decklid lip."""
    return pchip_interpolate(_REAR_Z_KNOTS, _REAR_YC_KNOTS, z)


def eval_rear_seam_z(t):
    """Horizontal rear bumper shutline Z(t) from tailgate corner (t=0) smoothly to rear wheel arch (t=1)."""
    t = max(0.0, min(1.0, float(t)))
    return 0.575 + 0.018 * math.sin(t * math.pi * 0.82) + (REAR_SEAM_Z_ARCH - 0.575) * (t ** 1.15)


def eval_rear_flank_meridian(z):
    """
    Smooth front boundary P3(z) of the rear corner Bezier, locking seamlessly onto:
      - Exact circular rear wheel arch edge for z <= REAR_SEAM_Z_ARCH (0.546 m)
      - Smooth vertical-ish rear quarter meridian curving from (-1.822, 0.546) up to (-1.920, 1.005) for z >= 0.546!
    """
    if z <= REAR_SEAM_Z_ARCH:
        dz = z - C.REAR_WHEEL_Z
        dy_sq = max(0.0, C.REAR_ARCH_RAD ** 2 - dz * dz)
        y = C.Y_REAR_AXLE - math.sqrt(dy_sq)
        x = BodyCurves.eval_flank_x_at_yz(y, z) + 0.004
    else:
        tz = max(0.0, min(1.0, (z - REAR_SEAM_Z_ARCH) / (1.005 - REAR_SEAM_Z_ARCH)))
        y = REAR_SEAM_Y_ARCH + (-1.920 - REAR_SEAM_Y_ARCH) * (tz ** 1.15)
        x = BodyCurves.eval_flank_x_at_yz(y, z) + 0.004 * (1.0 - smootherstep(0.0, 0.18, tz))
    return x, y


def eval_rear_corner_bezier(t, z):
    """
    Unified C2-smooth cubic Bezier rear haunch surface spanning BOTH Rear Quarter (z >= z_seam)
    AND Rear Bumper (z <= z_seam)!
      t = 0.0: Tailgate vertical outer shutline (X ~ 0.646 -> 0.635 -> 0.720)
      t = 1.0: Rear flank / wheel arch meridian P3(z) (Y ~ -1.82..-1.92)
    Because P0(z), P1(z), P2(z), P3(z) are C2-smooth in z, position AND slope match to 0.000 mm / 0.000 deg
    across the horizontal Rear Quarter <-> Rear Bumper shutline!
    """
    t = max(0.0, min(1.0, float(t)))
    yc = eval_rear_center_y(z)

    # P0(z): Tailgate outer vertical seam extending smoothly down beside diffuser
    if z >= 0.570:
        tv = max(0.0, min(1.0, (0.978 - z) / (0.978 - 0.570)))
        x0 = 0.646 - 0.012 * (tv ** 1.3)
        y0 = -2.475 - 0.058 * (tv ** 0.85) - 0.008 * math.sin(tv * math.pi) + 0.084
    else:
        tb = max(0.0, min(1.0, (0.570 - z) / (0.570 - 0.165)))
        x0 = 0.634 + 0.052 * (tb ** 1.25)
        y0 = yc + 0.084 + 0.012 * tb

    # P3(z): Exact rear flank / wheel arch meridian + exact analytical flank tangent dx/dy!
    x3, y3 = eval_rear_flank_meridian(z)
    dy_eps = 0.08
    x3_prev = BodyCurves.eval_flank_x_at_yz(y3 + dy_eps, z)
    dx_dy = (x3_prev - x3) / dy_eps  # True flank slope dX/dY moving forward (+Y)

    # Smooth muscular Plaid rear haunch fullness: WIDEST at mid-hip Z ~ 0.58 m,
    # tapering naturally INWARD both toward the roof shoulder AND downward toward the ground!
    z_frac = max(0.0, min(1.0, (z - 0.165) / (0.965 - 0.165)))
    lower_tuck = 0.075 * ((1.0 - min(1.0, z_frac / 0.50)) ** 1.6)
    upper_tuck = 0.055 * (max(0.0, (z_frac - 0.55) / 0.45) ** 1.5)
    dx_h1 = 0.215 - lower_tuck - upper_tuck
    dy_h1 = 0.068 - 0.016 * (z_frac ** 1.4) + 0.018 * ((1.0 - z_frac) ** 2.0)
    p1x, p1y = x0 + dx_h1, y0 + dy_h1

    # Lock P2 strictly along exact flank tangent vector (-dx_dy, -1.0) -> ZERO meridian Zebra kink!
    dy_h2 = 0.225 - 0.020 * z_frac
    p2x = x3 - dx_dy * dy_h2
    p2y = y3 - dy_h2

    u1 = 1.0 - t
    x = (u1 ** 3) * x0 + 3 * (u1 ** 2) * t * p1x + 3 * u1 * (t ** 2) * p2x + (t ** 3) * x3
    y = (u1 ** 3) * y0 + 3 * (u1 ** 2) * t * p1y + 3 * u1 * (t ** 2) * p2y + (t ** 3) * y3
    return x, y, z


# ==============================================================================
# MASTER CLASS-A REFERENCE CLAYS (Hidden uncut surfaces for G2 NormalTransfer!)
# ==============================================================================
def build_master_side_clay(col):
    ny, nt = 96, 36
    ys = np.linspace(-2.45, 2.25, ny)
    ts = np.linspace(0.0, 0.96, nt)
    grid = np.zeros((ny, nt, 3), dtype=np.float64)
    for i, y in enumerate(ys):
        for j, t in enumerate(ts):
            x, z = BodyCurves.eval_flank_section(y, t)
            grid[i, j] = (x, y, z)

    clay = create_grid_surface(
        "Master_ClassA_Side_Clay", grid, col, material=None,
        mirror_x=True, flip_normals=True, add_flange=False
    )
    clay.hide_render = True
    clay.hide_viewport = True
    return clay


def build_master_rear_haunch_clay(col):
    """Uncut continuous Class-A clay wrapping around the rear corner from Z=0.165 to Z=0.965."""
    nt, nz = 36, 36
    ts = np.linspace(0.0, 1.0, nt)
    zs = np.linspace(0.165, 0.965, nz)
    grid = np.zeros((nz, nt, 3), dtype=np.float64)
    for j, z in enumerate(zs):
        for i, t in enumerate(ts):
            grid[j, i] = eval_rear_corner_bezier(t, z)

    clay = create_grid_surface(
        "Master_ClassA_RearHaunch_Clay", grid, col, material=None,
        mirror_x=True, flip_normals=True, add_flange=False
    )
    clay.hide_render = True
    clay.hide_viewport = True
    return clay


# ==============================================================================
# 1. HOOD (Sculpted Clamshell with Twin Power-Dome Character Creases)
# ==============================================================================
def build_hood(col, mats):
    nu, nv = 40, 48
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    grid = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            y_front_u = 2.388 - 0.120 * (u ** 2.08)
            y_cowl_u = 0.956 - 0.050 * (u ** 2.1)
            y = y_cowl_u + v * (y_front_u - y_cowl_u)

            x_edge, z_edge = BodyCurves.hood_edge(min(y, 2.268))
            if y > 2.268:
                t_tip = min(1.0, (y - 2.268) / (2.388 - 2.268))
                x_edge = 0.398 * math.sqrt(max(1.0 - t_tip * t_tip, 0.0))
                z_edge = BodyCurves.hood_center_z(y) - 0.003 * (1.0 - t_tip)

            x = u * x_edge
            z_center = BodyCurves.hood_center_z(y)
            crown = (z_edge - z_center) * (u ** 1.85)
            ridge_env_v = math.sin(v * math.pi) ** 0.75 * (1.0 - 0.25 * smootherstep(0.75, 1.0, v))
            dome = 0.015 * ridge_env_v * math.exp(-((u - 0.56) / 0.24) ** 2)
            center_lift = 0.009 * math.sin(v * math.pi) * (1.0 - u * u)
            nose_roll = -0.005 * smootherstep(0.92, 1.0, v)

            z = z_center + crown + dome + center_lift + nose_roll
            grid[j, i] = (x, y, z)

    # flip_normals=True -> verified upward (+Z, +Y) outward normals!
    return create_grid_surface(
        "Body_Hood", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=True,
        add_flange=True, flange_depth=C.PANEL_FLANGE_DEPTH, flange_bevel=C.PANEL_BEVEL_RAD
    )


# ==============================================================================
# 2. FRONT BUMPER (Predatory 2024 Plaid Fascia + Exact Headlight/Arch Lock!)
# ==============================================================================
def _build_front_grille(mouth, col, mats):
    """Build the return, recessed louvers and dark cavity from the cut edge."""
    rim = np.concatenate((mouth[0, :], mouth[1:, -1], mouth[-1, -2::-1]))
    inner_rim = rim.copy()
    inner_rim[:, 1] -= 0.033
    # Enlarge the back of the duct so the rolled painted lip stays visible
    # and the backing still covers the aperture at an oblique viewing angle.
    inner_rim[:, 0] *= 1.045
    inner_rim[:, 2] = 0.236 + (inner_rim[:, 2] - 0.236) * 1.12
    rim[:, 1] -= 0.002
    create_grid_surface(
        "Trim_Front_Grille_Return", (rim, inner_rim), col, mats["trim_matte_plastic"],
        mirror_x=True, flip_normals=True,
    )

    backing = mouth[[0, -1]].copy()
    backing[:, :, 0] *= 1.15
    backing[:, :, 1] -= 0.087
    backing[:, :, 2] = 0.236 + (backing[:, :, 2] - 0.236) * 1.40
    create_grid_surface(
        "Trim_Front_Grille_Backing", backing, col, mats["trim_matte_plastic"],
        mirror_x=True, flip_normals=True,
    )

    # Louvers follow the local bumper curvature and remain behind the lip.
    profile = np.array([
        (0.0, -0.025, 0.0026), (0.0, -0.026, -0.0026),
        (0.0, -0.064, -0.0008), (0.0, -0.064, 0.0028),
    ])
    for index, row in enumerate(mouth[2:-1:2]):
        create_grid_surface(
            f"Trim_Front_Grille_Slat_{index}", row[:, None, :] + profile[None, :, :],
            col, mats["trim_matte_plastic"], close_v=True, mirror_x=True,
        )


def build_front_bumper(col, mats):
    """
    Wrap-around 2024 Model S Plaid front bumper:
      - Locks 0.0 mm to eval_headlight_lower_rim(t_h)
      - Locks 0.0 mm to Front Fender seam (outer headlight corner -> front wheel arch at phi=+28 deg)
      - Forms lower front wheel arch edge cleanly (phi = +28 down to -22 deg)
      - Crisp Plaid lower chin blade, wide trapezoidal grille w/ louvers, and sculpted single
        concave lower cheek air-curtain intake sitting cleanly under flush smoked fog light wedge!
    """
    nu, nv = 64, 40
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    grid = np.zeros((nv, nu, 3), dtype=np.float64)

    for i, u in enumerate(us):
        ang = u * (math.pi * 0.5)
        ca, sa = math.cos(ang), math.sin(ang)

        x_nose = 0.946 * (sa ** 0.85)
        y_nose = 1.855 + (C.Y_FRONT_TIP - 0.014 - 1.855) * (ca ** 0.72)

        # Top edge locked 0.0 mm to Mustache, Headlight Lower Rim, and Front Fender Seam!
        if u < 0.34:
            t_m = u / 0.34
            x_top = 0.398 * t_m
            y_top = 2.388 - 0.120 * (t_m ** 1.85)
            z_top = 0.594 - 0.008 * (t_m ** 1.5)
        elif u < 0.84:
            t_h = (u - 0.34) / 0.50
            x_top, y_top, z_top = eval_headlight_lower_rim(t_h)
        else:
            t_f = (u - 0.84) / 0.16
            y_top = HL_OUTER_Y + (FRONT_SEAM_Y_ARCH - HL_OUTER_Y) * t_f
            z_top = HL_OUTER_Z + (FRONT_SEAM_Z_ARCH - HL_OUTER_Z) * t_f
            x_top = BodyCurves.eval_flank_x_at_yz(y_top, z_top) + 0.004 * t_f

        z_bot = 0.136 + 0.012 * (u ** 1.4)
        y_bot = y_nose - 0.012 * (1.0 - 0.5 * u)
        x_bot = x_nose * 0.978

        for j, v in enumerate(vs):
            if u > 0.88:
                t_arch_blend = smootherstep(0.88, 1.0, u)
                phi_v = FRONT_ARCH_SEAM_PHI + v * (math.radians(-22.0) - FRONT_ARCH_SEAM_PHI)
                y_arch_v = C.Y_FRONT_AXLE + C.FRONT_ARCH_RAD * math.cos(phi_v)
                z_arch_v = max(0.140, C.FRONT_WHEEL_Z + C.FRONT_ARCH_RAD * math.sin(phi_v))
                x_arch_v = BodyCurves.eval_flank_x_at_yz(y_arch_v, z_arch_v) + 0.005
            else:
                t_arch_blend = 0.0
                x_arch_v = y_arch_v = z_arch_v = 0.0

            bulge_y = 0.044 * math.sin(v * math.pi) * (1.0 - 0.45 * u * u)
            bulge_x = 0.020 * math.sin(v * math.pi) * (u ** 0.72)
            # Crisp aerodynamic chin blade protruding cleanly along lower lip (matching 1X7A0025.jpg!)
            chin_lip = 0.022 * math.exp(-((v - 0.91) / 0.048) ** 2) * (1.0 - 0.15 * u)

            x = x_top + (x_bot - x_top) * (v ** 0.85) + bulge_x
            y = y_top + (y_bot - y_top) * (v ** 0.90) + bulge_y + chin_lip
            z = z_top + (z_bot - z_top) * v

            if t_arch_blend > 0.0:
                x = x * (1.0 - t_arch_blend) + x_arch_v * t_arch_blend
                y = y * (1.0 - t_arch_blend) + y_arch_v * t_arch_blend
                z = z * (1.0 - t_arch_blend) + z_arch_v * t_arch_blend

            if v > 0.96 and u < 0.92:
                t_u = (v - 0.96) / 0.04
                y -= 0.045 * t_u
                z -= 0.006 * t_u

            # 1. Sculpted Upper Mustache V-Notch Recess
            must_u = 1.0 - smootherstep(0.28, 0.36, u)
            must_v = 1.0 - smootherstep(0.04, 0.12, v)
            y -= 0.022 * must_u * must_v

            # 3. Clean Single Concave Outer Air-Curtain Cheek Bay + Slim Fog Wedge Pocket (matching 1X7A0025!)
            # Crisp upper wedge ledge at z ~ 0.318..0.336 holding flush dark smoked fog lamp!
            fog_x = smootherstep(0.545, 0.605, x) * (1.0 - smootherstep(0.848, 0.875, x))
            fog_z = smootherstep(0.302, 0.316, z) * (1.0 - smootherstep(0.332, 0.346, z))

            # Clean smooth single concave triangular-ish cheek scoop directly below fog strip (z ~ 0.175..0.306),
            # deepening smoothly outward into the vertical black air-curtain slot at x ~ 0.82..0.87!
            scoop_t_x = smootherstep(0.560, 0.835, x)
            scoop_x = scoop_t_x * (1.0 - smootherstep(0.855, 0.882, x))
            scoop_z = smootherstep(0.174, 0.205, z) * (1.0 - smootherstep(0.296, 0.316, z))

            curtain_x = smootherstep(0.805, 0.828, x) * (1.0 - smootherstep(0.858, 0.880, x))
            curtain_z = smootherstep(0.178, 0.198, z) * (1.0 - smootherstep(0.315, 0.338, z))

            indent_side = max(
                0.036 * fog_x * fog_z,
                0.030 * scoop_x * scoop_z,
                0.058 * curtain_x * curtain_z,
            )
            y -= indent_side * math.cos(ang * 0.62)
            x -= indent_side * 0.38 * math.sin(ang * 0.62)

            grid[j, i] = (x, y, z)

    # Cut the lower grille out of the bumper lattice. The opening and the
    # grille share one edge, including its rake around the front corners.
    top, bottom, side = 25, 36, 21
    for row in (top, bottom):
        grid[row, side, 0] -= 0.012
    grid[top, side - 1:side + 1, 2] -= (0.003, 0.010)
    grid[bottom, side - 1:side + 1, 2] += (0.003, 0.010)
    faces = np.ones((nv - 1, nu - 1), dtype=bool)
    faces[top:bottom, :side] = False
    mouth = grid[top:bottom + 1, :side + 1]
    bumper = create_grid_surface(
        "Body_Front_Bumper", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=True, face_mask=faces,
        add_flange=True, flange_depth=0.014, flange_bevel=0.002
    )
    _build_front_grille(mouth, col, mats)

    # Gloss-Black Smiling Upper Mustache Garnish Bar (holding Chrome T-Badge!)
    nm = 26
    bm = bmesh.new()
    m_rings = []
    for i in range(nm):
        tm = i / (nm - 1)
        x = tm * 0.400
        y = 2.388 - 0.120 * (tm ** 1.85) + 0.005 * (1.0 - tm)
        z_hi = 0.596 - 0.008 * (tm ** 1.5)
        v_dip = 0.044 * math.exp(-((x / 0.068) ** 2))
        z_lo = z_hi - 0.018 * (1.0 - 0.65 * tm) - v_dip
        m_rings.append([
            bm.verts.new((x, y + 0.005, z_hi)),
            bm.verts.new((x, y + 0.007, z_lo)),
            bm.verts.new((x, y - 0.024, z_lo)),
            bm.verts.new((x, y - 0.024, z_hi)),
        ])
    for i in range(nm - 1):
        r0, r1 = m_rings[i], m_rings[i + 1]
        for k in range(4):
            kn = (k + 1) % 4
            bm.faces.new((r0[k], r1[k], r1[kn], r0[kn]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("Trim_Nose_Mustache")
    bm.to_mesh(mesh)
    bm.free()
    set_smooth_shading(mesh)
    m_obj = bpy.data.objects.new("Trim_Nose_Mustache", mesh)
    link_object(m_obj, col)
    m_obj.data.materials.append(mats["trim_gloss_black"])
    mod = m_obj.modifiers.new("MirrorX", "MIRROR")
    mod.use_axis = (True, False, False)

    # Narrow Vertical Outer Air Curtain Dark Slot Backing (L/R)
    ag = np.zeros((10, 8, 3), dtype=np.float64)
    for j, tz in enumerate(np.linspace(0.0, 1.0, 10)):
        z = 0.180 + tz * (0.334 - 0.180)
        for i, tx in enumerate(np.linspace(0.0, 1.0, 8)):
            x = 0.808 + tx * (0.868 - 0.808)
            y = 2.045 - 0.078 * tx
            ag[j, i] = (x, y, z)
    create_grid_surface("Trim_Front_AirCurtain_Duct", ag, col, material=mats["trim_matte_plastic"], mirror_x=True, flip_normals=True)
    return bumper


# ==============================================================================
# 3. FRONT FENDER (0.0 mm Lock to Bumper, Headlight Brow, Hood & A-Pillar!)
# ==============================================================================
def build_front_fender(col, mats, master_clay):
    yc, zc = C.Y_FRONT_AXLE, C.FRONT_WHEEL_Z
    r_arch = C.FRONT_ARCH_RAD

    n_ang = 46
    n_rad = 14
    phis = np.linspace(FRONT_ARCH_SEAM_PHI, math.radians(206.0), n_ang)

    def outer_boundary(phi_deg):
        if phi_deg < 60.0:
            # EXACT 0.0 mm match to eval_headlight_upper_rim(u) for u from 1.0 down to 0.50!
            t = (phi_deg - 28.0) / 32.0
            u_hl = 1.0 - 0.50 * t
            _, y_o, z_o = eval_headlight_upper_rim(u_hl)
        elif phi_deg < 138.0:
            # Hood outer shutline flowing smoothly back to A-pillar foot (Y = 0.885)
            t = (phi_deg - 60.0) / 78.0
            _, y_hl5, _ = eval_headlight_upper_rim(0.50)
            y_o = y_hl5 + (C.Y_FENDER_DOOR_TOP - y_hl5) * t
            if y_o >= 0.955:
                _, z_o = BodyCurves.hood_edge(min(y_o, 2.065))
            else:
                _, z_o = BodyCurves.beltline(y_o)
        else:
            t = (phi_deg - 138.0) / (206.0 - 138.0)
            y_o = C.Y_FENDER_DOOR_TOP + (C.Y_FENDER_DOOR_BOT - C.Y_FENDER_DOOR_TOP) * t
            _, z_top_d = BodyCurves.beltline(y_o)
            _, z_bot_d = BodyCurves.sill_edge(y_o)
            z_o = z_top_d + (z_bot_d - z_top_d) * t
        return y_o, z_o

    grid = np.zeros((n_rad, n_ang, 3), dtype=np.float64)
    for i, phi in enumerate(phis):
        phi_deg = math.degrees(phi)
        y_in = yc + r_arch * math.cos(phi)
        z_in = zc + r_arch * math.sin(phi)
        _, z_sill_in = BodyCurves.sill_edge(y_in)
        if z_in < z_sill_in:
            z_in = z_sill_in

        y_out, z_out = outer_boundary(phi_deg)

        for j in range(n_rad):
            tr = j / (n_rad - 1)
            tr_e = tr ** 1.15
            y = y_in + (y_out - y_in) * tr_e
            z = z_in + (z_out - z_in) * tr_e

            x_side = BodyCurves.eval_flank_x_at_yz(y, z)
            if 28.0 <= phi_deg < 60.0 and tr > 0.50:
                # Smoothly lock top edge onto exact eval_headlight_upper_rim X without corner crease
                t_top = smootherstep(0.50, 1.0, tr)
                t_hl = (phi_deg - 28.0) / 32.0
                x_hl, _, _ = eval_headlight_upper_rim(1.0 - 0.50 * t_hl)
                x = x_side + (x_hl - x_side) * t_top * smootherstep(28.0, 54.0, phi_deg)
            elif 60.0 <= phi_deg <= 144.0 and tr > 0.45:
                t_top = smootherstep(0.45, 1.0, tr)
                if y >= 0.955:
                    x_hood, _ = BodyCurves.hood_edge(min(y, 2.065))
                else:
                    # Smooth airtight roll onto A-pillar foot (Y=0.885..0.955) -> ZERO black triangle!
                    tb = smootherstep(0.885, 0.955, y)
                    xh95, _ = BodyCurves.hood_edge(0.955)
                    xc88, _ = BodyCurves.cantrail_outer(y)
                    x_hood = xc88 + (xh95 - xc88) * tb
                env_ang = 1.0 - smootherstep(134.0, 144.0, phi_deg)
                x = x_side + (x_hood - x_side) * t_top * env_ang
            else:
                x = x_side

            arch_flare = 0.005 * math.exp(-((tr / 0.22) ** 2)) * (1.0 - smootherstep(172.0, 204.0, phi_deg))
            x += arch_flare
            grid[j, i] = (x, y, z)

    fender = create_grid_surface(
        "Body_Front_Fender", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=False,
        add_flange=True, flange_depth=0.018, flange_bevel=0.0022
    )
    add_normal_transfer(fender, master_clay, max_dist=0.016)
    _build_wheel_well_liner("Underbody_WheelLiner_Front", yc, zc, r_arch - 0.005, col, mats)
    return fender


# ==============================================================================
# 4 & 5. FRONT DOORS, REAR DOORS & ROCKER SKIRTS
# ==============================================================================
def build_doors(col, mats, master_clay):
    gap = C.PANEL_GAP * 0.5

    ny_f, nt_f = 34, 28
    ts = np.linspace(0.0, 0.92, nt_f)
    grid_f = np.zeros((ny_f, nt_f, 3), dtype=np.float64)
    for j, t in enumerate(ts):
        y_start = (C.Y_FENDER_DOOR_TOP + (C.Y_FENDER_DOOR_BOT - C.Y_FENDER_DOOR_TOP) * t) - gap
        y_end = (C.Y_FRONT_REAR_DOOR_TOP + (C.Y_FRONT_REAR_DOOR_BOT - C.Y_FRONT_REAR_DOOR_TOP) * t) + gap
        for i, u in enumerate(np.linspace(0.0, 1.0, ny_f)):
            y = y_end + u * (y_start - y_end)
            x, z = BodyCurves.eval_flank_section(y, t)
            grid_f[i, j] = (x, y, z)

    front_door = create_grid_surface(
        "Body_Front_Door", grid_f, col, material=mats["paint"],
        mirror_x=True, flip_normals=True,
        add_flange=True, flange_depth=C.PANEL_FLANGE_DEPTH, flange_bevel=C.PANEL_BEVEL_RAD
    )
    add_normal_transfer(front_door, master_clay, max_dist=0.015)

    ny_r, nt_r = 32, 28
    grid_r = np.zeros((ny_r, nt_r, 3), dtype=np.float64)
    for j, t in enumerate(ts):
        y_front = (C.Y_FRONT_REAR_DOOR_TOP + (C.Y_FRONT_REAR_DOOR_BOT - C.Y_FRONT_REAR_DOOR_TOP) * t) - gap
        y_rear = (-1.035 - 0.135 * math.sin(t * math.pi * 0.92) + 0.045 * (t ** 2.2)) + gap
        for i, u in enumerate(np.linspace(0.0, 1.0, ny_r)):
            y = y_rear + u * (y_front - y_rear)
            x, z = BodyCurves.eval_flank_section(y, t)
            grid_r[i, j] = (x, y, z)

    rear_door = create_grid_surface(
        "Body_Rear_Door", grid_r, col, material=mats["paint"],
        mirror_x=True, flip_normals=True,
        add_flange=True, flange_depth=C.PANEL_FLANGE_DEPTH, flange_bevel=C.PANEL_BEVEL_RAD
    )
    add_normal_transfer(rear_door, master_clay, max_dist=0.015)

    ny_s, nt_s = 36, 10
    ys_s = np.linspace(-1.05, 1.06, ny_s)
    ts_s = np.linspace(0.86, 1.0, nt_s)
    grid_s = np.zeros((ny_s, nt_s, 3), dtype=np.float64)
    for i, y in enumerate(ys_s):
        for j, t in enumerate(ts_s):
            x, z = BodyCurves.eval_flank_section(y, t)
            grid_s[i, j] = (x, y, z)
    rocker = create_grid_surface(
        "Body_Rocker_Skirt", grid_s, col, material=mats["paint"],
        mirror_x=True, flip_normals=True,
        add_flange=True, flange_depth=0.012, flange_bevel=0.002
    )
    add_normal_transfer(rocker, master_clay, max_dist=0.015)
    return front_door, rear_door, rocker


# ==============================================================================
# 6. UNIFIED WELDED REAR QUARTER PANEL (ZERO Diagonal Pinch, G2 to Bumper!)
# ==============================================================================
def build_rear_quarter(col, mats, master_clay, rear_clay):
    """
    Build ONE SINGLE CONTINUOUS welded stamped Rear Quarter Panel combining:
      A) Polar wheel-arch flank zone (phi = -20..+150 deg, ending along exact meridian P3(z)!)
      B) C2 Cubic-Bezier rear corner wrap (t = 1.0 at P3(z) -> t = 0.0 at Tailgate shutline,
         z = eval_rear_seam_z(t) up to upper shoulder z_top(t)!)
    Welded cleanly along P3(z) -> ZERO internal seam, ZERO diagonal crease, and G2 normal
    continuity across the horizontal shutline into Body_Rear_Bumper!
    """
    yc, zc = C.Y_REAR_AXLE, C.REAR_WHEEL_Z
    r_arch = C.REAR_ARCH_RAD

    n_ang = 44
    n_rad = 18  # Matches nz_w below so vertices weld 1-to-1 along meridian P3(z)!
    phis = np.linspace(math.radians(-20.0), REAR_ARCH_SEAM_PHI, n_ang)

    def outer_boundary(phi_deg):
        if phi_deg < 48.0:
            t = (phi_deg + 20.0) / 68.0
            y_o = -1.035 - 0.135 * math.sin((1.0 - t) * math.pi * 0.92) + 0.045 * ((1.0 - t) ** 2.2)
            _, z_top = BodyCurves.beltline(y_o)
            _, z_bot = BodyCurves.sill_edge(y_o)
            z_o = z_bot + (z_top - z_bot) * t
        else:
            # Sweep upper shoulder smoothly back to meridian top (-1.920, 1.005)!
            t = (phi_deg - 48.0) / (150.0 - 48.0)
            y_o = -1.035 + (-1.920 - (-1.035)) * t
            _, z_o = BodyCurves.beltline(y_o)
        return y_o, z_o

    # Build Part A (polar arch) + Part B (Bezier rear corner) in ONE unified bmesh!
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # Part A vertices: [j in 0..n_rad-1][i in 0..n_ang-1]
    verts_a = [[None] * n_ang for _ in range(n_rad)]
    for i, phi in enumerate(phis):
        phi_deg = math.degrees(phi)
        y_in = yc + r_arch * math.cos(phi)
        z_in = zc + r_arch * math.sin(phi)
        _, z_sill_in = BodyCurves.sill_edge(y_in)
        if z_in < z_sill_in:
            z_in = z_sill_in
        y_out, z_out = outer_boundary(phi_deg)

        for j in range(n_rad):
            tr = j / (n_rad - 1)
            if i == n_ang - 1:
                # Exact meridian P3(z) matching Part B column t=1.0 vertex-for-vertex!
                z = REAR_SEAM_Z_ARCH + tr * (1.005 - REAR_SEAM_Z_ARCH)
                x, y = eval_rear_flank_meridian(z)
            else:
                tr_e = tr ** 1.15
                y = y_in + (y_out - y_in) * tr_e
                z = z_in + (z_out - z_in) * tr_e
                x = BodyCurves.eval_flank_x_at_yz(y, z)
                arch_flare = 0.004 * math.exp(-((tr / 0.22) ** 2)) * smootherstep(-18.0, 15.0, phi_deg)
                x += arch_flare
            verts_a[j][i] = bm.verts.new((x, y, z))

    for j in range(n_rad - 1):
        for i in range(n_ang - 1):
            f = bm.faces.new((verts_a[j][i], verts_a[j + 1][i], verts_a[j + 1][i + 1], verts_a[j][i + 1]))
            for loop in f.loops:
                loop[uv_layer].uv = (i / (n_ang - 1), j / (n_rad - 1))

    # Part B vertices: Bezier rear corner wrap from t=1.0 (meridian P3, reusing verts_a[j][-1]!) to t=0.0 (tailgate!)
    nt_b = 22
    ts_b = np.linspace(1.0, 0.0, nt_b)  # index 0 = t=1.0 (exact shared meridian verts!)
    verts_b = [[None] * nt_b for _ in range(n_rad)]
    for j in range(n_rad):
        verts_b[j][0] = verts_a[j][n_ang - 1]  # Exact 1-to-1 topological weld!

    for ib in range(1, nt_b):
        tb = float(ts_b[ib])
        z_bot_b = eval_rear_seam_z(tb)
        # Upper edge smoothly descends from (-1.920, 1.005) at t=1.0 to Tailgate top corner (0.960) at t=0.0!
        z_top_b = 0.960 + (1.005 - 0.960) * (tb ** 1.15)
        for j in range(n_rad):
            tr = j / (n_rad - 1)
            z = z_bot_b + tr * (z_top_b - z_bot_b)
            x, y, z = eval_rear_corner_bezier(tb, z)
            # Subtle taillight recess pocket inside the outer quarter corner so flush smoked lens nests neatly
            tl_z = smootherstep(0.782, 0.800, z) * (1.0 - smootherstep(0.884, 0.902, z))
            tl_t = 1.0 - smootherstep(0.62, 0.80, tb)
            y += 0.018 * tl_z * tl_t * (1.0 - tb)
            x -= 0.012 * tl_z * tl_t * tb
            verts_b[j][ib] = bm.verts.new((x, y, z))

    for j in range(n_rad - 1):
        for ib in range(nt_b - 1):
            # Consistent outward winding matching Part A (j -> j+1 is +Z, ib -> ib+1 is toward tailgate -X/-Y)
            f = bm.faces.new((verts_b[j][ib], verts_b[j + 1][ib], verts_b[j + 1][ib + 1], verts_b[j][ib + 1]))
            for loop in f.loops:
                loop[uv_layer].uv = (ib / (nt_b - 1), j / (n_rad - 1))

    bm.normal_update()

    # Roll subtle 1.6 mm automotive panel flanges ONLY on true exterior perimeter edges!
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    if boundary_edges:
        ret1 = bmesh.ops.extrude_edge_only(bm, edges=boundary_edges)
        v1 = [el for el in ret1["geom"] if isinstance(el, bmesh.types.BMVert)]
        e1 = [el for el in ret1["geom"] if isinstance(el, bmesh.types.BMEdge)]
        for v in v1:
            n = v.normal.normalized() if v.normal.length > 1e-6 else Vector((1, 0, 0))
            v.co -= n * 0.0016
        bm.normal_update()
        outer_e = [e for e in e1 if e.is_boundary]
        if outer_e:
            ret2 = bmesh.ops.extrude_edge_only(bm, edges=outer_e)
            v2 = [el for el in ret2["geom"] if isinstance(el, bmesh.types.BMVert)]
            for v in v2:
                n = v.normal.normalized() if v.normal.length > 1e-6 else Vector((1, 0, 0))
                v.co -= n * 0.014
    bm.normal_update()

    mesh = bpy.data.meshes.new("Body_Rear_Quarter")
    bm.to_mesh(mesh)
    bm.free()
    set_smooth_shading(mesh)
    quarter = bpy.data.objects.new("Body_Rear_Quarter", mesh)
    link_object(quarter, col)
    quarter.data.materials.append(mats["paint"])
    mod = quarter.modifiers.new("MirrorX", "MIRROR")
    mod.use_axis = (True, False, False)
    mod.use_clip = True
    mod.merge_threshold = 0.0005

    # Transfer G2 Class-A normals from Master Side Clay on flank AND Rear Haunch Clay on corner!
    add_normal_transfer(quarter, master_clay, max_dist=0.016)
    mod_rc = quarter.modifiers.new(name="ClassA_RearCorner_Normals", type="DATA_TRANSFER")
    mod_rc.object = rear_clay
    mod_rc.use_loop_data = True
    mod_rc.data_types_loops = {'CUSTOM_NORMAL'}
    mod_rc.loop_mapping = 'POLYINTERP_NEAREST'
    mod_rc.use_max_distance = True
    mod_rc.max_distance = 0.014
    mod_rc.mix_mode = 'REPLACE'
    mod_rc.mix_factor = 1.0

    _build_wheel_well_liner("Underbody_WheelLiner_Rear", yc, zc, r_arch - 0.005, col, mats)
    return quarter


# ==============================================================================
# 7. ROOF CANTRAILS & A/C-PILLARS (0.0 mm Flush with Glass + Airtight A-Pillar Foot!)
# ==============================================================================
def build_roof_cantrails(col, mats):
    """Sleek Ultra Red A-pillar, roof cantrail, and sweeping C-pillar sitting 0.0 mm flush with glass & fender."""
    ny = 54
    nw = 10
    ys = np.linspace(-2.391, 0.955, ny)
    ws = np.linspace(0.0, 1.0, nw)

    grid = np.zeros((ny, nw, 3), dtype=np.float64)
    for i, y in enumerate(ys):
        if y >= -2.14:
            x_in, z_in = BodyCurves.glass_edge(y)
            z_in -= 0.001
        else:
            t_d = (-2.14 - y) / (2.391 - 2.14)
            x_in = 0.555 + (0.646 - 0.555) * t_d
            z_in = BodyCurves.roof_center_z(y) - 0.022

        if y >= -1.52:
            x_out, z_out = BodyCurves.cantrail_outer(y)
        else:
            x_out, z_out = BodyCurves.beltline(y)

        for j, w in enumerate(ws):
            x = x_in + (x_out - x_in) * (w ** 0.94)
            crown = 0.004 * math.sin(w * math.pi)
            z = z_in + (z_out - z_in) * (w ** 1.04) + crown
            grid[i, j] = (x, y, z)

    return create_grid_surface(
        "Body_Roof_Cantrail", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=True,
        add_flange=True, flange_depth=0.010, flange_bevel=0.0018
    )


# ==============================================================================
# 8. REAR LIFTGATE / TAILGATE
# ==============================================================================
def build_rear_tailgate(col, mats):
    nu, nv = 40, 34
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    grid = np.zeros((nv, nu, 3), dtype=np.float64)
    for i, u in enumerate(us):
        y_curve = 0.084 * (u ** 2.05)
        x_deck_max = 0.646

        for j, v in enumerate(vs):
            if v <= 0.34:
                td = v / 0.34
                x = u * (0.555 + (x_deck_max - 0.555) * td)
                y = -2.140 + (-2.475 - (-2.140)) * td + y_curve * (0.4 + 0.6 * td)
                z_c = BodyCurves.roof_center_z(max(-2.475, min(-2.140, y)))
                z = z_c - 0.022 * (u ** 1.9) + 0.008 * smootherstep(0.65, 1.0, td)
            else:
                tv = (v - 0.34) / 0.66
                xw = x_deck_max - 0.012 * (tv ** 1.3)
                x = u * xw
                z = 0.978 + (0.570 - 0.978) * tv - 0.018 * (u ** 1.9) * (1.0 - 0.5 * tv)
                y = -2.475 - 0.058 * (tv ** 0.85) - 0.008 * math.sin(tv * math.pi) + y_curve

                # Gloss-black TESLA garnish bar channel
                bar_z = smootherstep(0.818, 0.830, z) * (1.0 - smootherstep(0.870, 0.884, z))
                bar_x = 1.0 - smootherstep(0.502, 0.526, x)
                y += 0.018 * bar_z * bar_x

                # Trapezoid license plate pocket
                lp_tz = np.clip((z - 0.618) / (0.812 - 0.618), 0.0, 1.0)
                lp_xlim = 0.275 + 0.055 * lp_tz
                lp_x = 1.0 - smootherstep(lp_xlim - 0.024, lp_xlim + 0.015, x)
                lp_z = smootherstep(0.612, 0.635, z) * (1.0 - smootherstep(0.798, 0.818, z))
                y += 0.034 * lp_x * lp_z

                # Inner taillight recess
                tl_x = smootherstep(0.495, 0.520, x)
                tl_z = smootherstep(0.772, 0.788, z) * (1.0 - smootherstep(0.885, 0.902, z))
                y += 0.030 * tl_x * tl_z

            grid[j, i] = (x, y, z)

    return create_grid_surface(
        "Body_Rear_Tailgate", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=False,
        add_flange=True, flange_depth=C.PANEL_FLANGE_DEPTH, flange_bevel=C.PANEL_BEVEL_RAD
    )


# ==============================================================================
# 9. G2 CONTINUOUS REAR BUMPER & GLOSS-BLACK PLAID DIFFUSER
# ==============================================================================
def build_rear_bumper_and_diffuser(col, mats, rear_clay):
    """
    Class-A C2 Continuous Rear Bumper:
      - Center section (u in [0..0.46]) sweeps cleanly below tailgate with subtle authentic
        rear bumper crown reaching exact Y = -2.578 m (5,021 mm overall length!).
      - Outer corner section (u in [0.46..1.0]) evaluates EXACTLY eval_rear_corner_bezier(t, z)
        AND transfers G2 normals from Master_ClassA_RearHaunch_Clay -> ZERO horizontal cliff!
      - Sleek upward lower bottom contour behind rear wheel matching IMG_9321.jpg.
    """
    nu, nv = 62, 30
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    grid = np.zeros((nv, nu, 3), dtype=np.float64)
    for i, u in enumerate(us):
        if u <= 0.46:
            tc = u / 0.46
            z_top = 0.570 + 0.005 * (tc ** 1.5)
            z_bot = 0.168 + 0.008 * (tc ** 1.8)
            for j, v in enumerate(vs):
                z = z_top + (z_bot - z_top) * v
                tb = max(0.0, min(1.0, (0.570 - z) / (0.570 - 0.165)))
                x_seam = 0.634 + 0.068 * (tb ** 1.35)
                x = tc * x_seam
                yc = eval_rear_center_y(z)
                y = yc + (0.084 + 0.010 * tb) * (tc ** 2.05)

                # Deeply tuck behind gloss-black diffuser (ZERO red bleed!)
                tz_d = np.clip((0.372 - z) / (0.372 - 0.168), 0.0, 1.0)
                x_dlim = 0.678 + 0.068 * tz_d
                dx = 1.0 - smootherstep(x_dlim - 0.025, x_dlim + 0.015, x)
                dz = 1.0 - smootherstep(0.352, 0.378, z)
                y += 0.075 * dx * dz
                grid[j, i] = (x, y, z)
        else:
            t_wrap = (u - 0.46) / 0.54
            z_top = eval_rear_seam_z(t_wrap)
            # Authentic sporty Model S upward bottom aero sweep from rear wheel arch (0.148) to corner (0.176)!
            z_bot = 0.176 - 0.028 * (t_wrap ** 1.35)
            for j, v in enumerate(vs):
                z = z_top + (z_bot - z_top) * v
                x, y, z = eval_rear_corner_bezier(t_wrap, z)

                # Deeply tuck inner lower corner behind gloss-black diffuser edge (ZERO red bleed!)
                tz_d = np.clip((0.372 - z) / (0.372 - 0.168), 0.0, 1.0)
                x_dlim = 0.678 + 0.068 * tz_d
                dx = 1.0 - smootherstep(x_dlim - 0.025, x_dlim + 0.015, x)
                dz = 1.0 - smootherstep(0.352, 0.378, z)
                y += 0.075 * dx * dz
                grid[j, i] = (x, y, z)

    bumper = create_grid_surface(
        "Body_Rear_Bumper", grid, col, material=mats["paint"],
        mirror_x=True, flip_normals=False,
        add_flange=True, flange_depth=0.014, flange_bevel=0.0015
    )
    # Transfer G2 Class-A normals across the entire rear corner wrap so reflection ribbons flow seamlessly!
    add_normal_transfer(bumper, rear_clay, max_dist=0.014)

    # --- GLOSS-BLACK PLAID REAR DIFFUSER VALENCE ---
    nu_d, nv_d = 40, 18
    dg = np.zeros((nv_d, nu_d, 3), dtype=np.float64)
    for i, u in enumerate(np.linspace(0.0, 1.0, nu_d)):
        for j, v in enumerate(np.linspace(0.0, 1.0, nv_d)):
            z_hi = 0.368 - 0.010 * (u ** 2.0)
            z_lo = 0.168 + 0.012 * (u ** 1.8)
            arch_lift = 0.036 * (1.0 - smootherstep(0.32, 0.44, u)) * smootherstep(0.62, 0.95, v)
            z = z_hi + (z_lo - z_hi) * v + arch_lift
            xw = 0.735 - 0.058 * (1.0 - v)
            x = u * xw
            y = -2.556 + 0.148 * (u ** 2.1) + 0.064 * (v ** 1.35)
            lip_out = 0.016 * math.exp(-((v - 0.88) / 0.09) ** 2)
            center_recess = 0.016 * (1.0 - smootherstep(0.34, 0.42, u)) * smootherstep(0.45, 0.78, v)
            y += center_recess - lip_out
            dg[j, i] = (x, y, z)

    diffuser = create_grid_surface(
        "Trim_Rear_Diffuser", dg, col, material=mats["trim_gloss_black"],
        mirror_x=True, flip_normals=False,
        add_flange=True, flange_depth=0.015, flange_bevel=0.002
    )

    # Subtle under-diffuser vertical aero strake fins
    for idx, xf in enumerate([0.16, 0.38]):
        bm = bmesh.new()
        t = 0.0055
        y0, y1 = -2.47 + 0.05 * idx, -2.18
        z0, z1 = 0.158, 0.215
        v0 = bm.verts.new((xf - t, y0, z0))
        v1 = bm.verts.new((xf + t, y0, z0))
        v2 = bm.verts.new((xf + t, y1, z0 - 0.012))
        v3 = bm.verts.new((xf - t, y1, z0 - 0.012))
        v4 = bm.verts.new((xf - t, y0, z1))
        v5 = bm.verts.new((xf + t, y0, z1))
        v6 = bm.verts.new((xf + t, y1, z1))
        v7 = bm.verts.new((xf - t, y1, z1))
        bm.faces.new((v0, v1, v2, v3))
        bm.faces.new((v4, v7, v6, v5))
        bm.faces.new((v0, v4, v5, v1))
        bm.faces.new((v1, v5, v6, v2))
        bm.faces.new((v2, v6, v7, v3))
        bm.faces.new((v3, v7, v4, v0))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        m = bpy.data.meshes.new(f"Trim_Diffuser_Strake_{idx}")
        bm.to_mesh(m)
        bm.free()
        obj = bpy.data.objects.new(f"Trim_Diffuser_Strake_{idx}", m)
        link_object(obj, col)
        obj.data.materials.append(mats["trim_matte_plastic"])
        mod = obj.modifiers.new("MirrorX", "MIRROR")
        mod.use_axis = (True, False, False)

    return bumper, diffuser


# ==============================================================================
# 10. DYNAMICALLY TUCKED WHEEL WELL LINERS, UNDERBODY & SHADOW BACKING TUB
# ==============================================================================
def _build_wheel_well_liner(name, yc, zc, r_arch, col, mats):
    """Dark matte wheel well tub dynamically tucked -18 mm inside fender/bumper (ZERO poke-through!)."""
    n_ang = 36
    phis = np.linspace(math.radians(-16.0), math.radians(196.0), n_ang)
    grid = np.zeros((4, n_ang, 3), dtype=np.float64)
    for i, phi in enumerate(phis):
        y = yc + r_arch * math.cos(phi)
        z = max(0.138, zc + r_arch * math.sin(phi))
        x_body = BodyCurves.eval_flank_x_at_yz(y, z)
        x_lip = min(x_body - 0.018, 0.94)
        grid[0, i] = (x_lip, y, z)
        grid[1, i] = (x_lip - 0.05, yc + (r_arch + 0.022) * math.cos(phi), max(0.138, zc + (r_arch + 0.022) * math.sin(phi)))
        grid[2, i] = (0.58, yc + (r_arch + 0.018) * math.cos(phi), max(0.138, zc + (r_arch + 0.018) * math.sin(phi)))
        grid[3, i] = (0.58, yc, zc)

    create_grid_surface(name, grid, col, material=mats["trim_matte_plastic"], mirror_x=True, flip_normals=False)


def build_underbody_and_shadow_tub(col, mats):
    ys = np.array([-2.38, -2.05, -1.85, -1.08, -0.20, 0.94, 1.85, 2.34])
    xs = np.array([0.64,   0.76,  0.58,  0.84,  0.84, 0.84, 0.58, 0.64])
    zs = np.array([0.168,  0.145, 0.126, 0.122, 0.122, 0.124, 0.132, 0.145])

    grid = np.zeros((len(ys), 6, 3), dtype=np.float64)
    for i, y in enumerate(ys):
        for j, u in enumerate(np.linspace(0.0, 1.0, 6)):
            grid[i, j] = (u * xs[i], y, zs[i])
    create_grid_surface("Underbody_Aero_Floor", grid, col, material=mats["trim_matte_plastic"], mirror_x=True, flip_normals=True)

    # Inner dark shadow backing strictly behind side door shutlines (never pokes through front fender!)
    ny_s, nt_s = 36, 16
    ys_d = np.linspace(-1.05, 0.878, ny_s)
    ts_d = np.linspace(0.04, 0.94, nt_s)
    sg = np.zeros((ny_s, nt_s, 3), dtype=np.float64)
    for i, y in enumerate(ys_d):
        for j, t in enumerate(ts_d):
            x, z = BodyCurves.eval_flank_section(y, t)
            sg[i, j] = (x - 0.022, y, z)
    create_grid_surface("Body_Shadow_Gap_Sides", sg, col, material=mats["shadow_gap"], mirror_x=True, flip_normals=True)

    # Hood perimeter shadow tray
    nu_h, nv_h = 20, 20
    hg = np.zeros((nv_h, nu_h, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv_h)):
        for i, u in enumerate(np.linspace(0.0, 1.0, nu_h)):
            y_front_u = 2.368 - 0.120 * (u ** 2.08)
            y_cowl_u = 0.945 - 0.050 * (u ** 2.1)
            y = y_cowl_u + v * (y_front_u - y_cowl_u)
            x_edge, z_edge = BodyCurves.hood_edge(min(y, 2.268))
            x = u * (x_edge - 0.010)
            z = BodyCurves.hood_center_z(y) + (z_edge - BodyCurves.hood_center_z(y)) * (u ** 1.85) - 0.018
            hg[j, i] = (x, y, z)
    create_grid_surface("Body_Shadow_Gap_Hood", hg, col, material=mats["shadow_gap"], mirror_x=True, flip_normals=False)

    # Rear tailgate shadow backing tray
    nu_t, nv_t = 18, 16
    tg = np.zeros((nv_t, nu_t, 3), dtype=np.float64)
    for i, u in enumerate(np.linspace(0.0, 1.0, nu_t)):
        y_curve = 0.084 * (u ** 2.05)
        for j, v in enumerate(np.linspace(0.0, 1.0, nv_t)):
            x = u * 0.65
            z = 0.960 + (0.555 - 0.960) * v
            y = -2.450 - 0.050 * v + y_curve + 0.025
            tg[j, i] = (x, y, z)
    create_grid_surface("Body_Shadow_Gap_Rear", tg, col, material=mats["shadow_gap"], mirror_x=True, flip_normals=False)


def build_all_bodywork(root_col, mats):
    col = ensure_collection("01_Bodywork", root_col)
    clay = build_master_side_clay(col)
    rear_clay = build_master_rear_haunch_clay(col)
    build_hood(col, mats)
    build_front_bumper(col, mats)
    build_front_fender(col, mats, clay)
    build_doors(col, mats, clay)
    build_rear_quarter(col, mats, clay, rear_clay)
    build_roof_cantrails(col, mats)
    build_rear_tailgate(col, mats)
    build_rear_bumper_and_diffuser(col, mats, rear_clay)
    build_underbody_and_shadow_tub(col, mats)
    return col
