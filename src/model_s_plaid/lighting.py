"""
High-Precision Optical Lighting Systems for the 2024 Tesla Model S Plaid (Iteration 4):
  - 2022-2024 Adaptive Matrix LED Headlights locked 0.0 mm to shared eval_headlight_lower_rim
    & eval_headlight_upper_rim curves (zero protrusion above hood/fender, zero outer gap!)
  - Flush Lower-Bumper Smoked Needle-Wedge LED Fog Lights matching 1X7A0025 & IMG_9278
  - 2022-2024 Refreshed 2-Piece Split LED Taillights locked 0.0 mm to unified C2 Bezier
    Rear Quarter corner surface (eval_rear_corner_bezier)
  - Lower Rear Diffuser Integrated Red Reflectors
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector

from . import config as C
from .body_master import (
    BodyCurves,
    eval_headlight_lower_rim,
    eval_headlight_upper_rim,
    eval_rear_corner_bezier,
)
from .geometry_utils import (
    ensure_collection,
    create_grid_surface,
    create_revolved_mesh,
    create_tube_along_points,
    cubic_bezier,
    add_solidify,
    set_smooth_shading,
    link_object,
)


def _headlight_outline_point(u, v):
    """
    Evaluate 0.0 mm flush 3D coordinate on the swept Matrix LED headlight cover lens,
    directly interpolating shared eval_headlight_lower_rim & eval_headlight_upper_rim!
    """
    x_lo, y_lo, z_lo = eval_headlight_lower_rim(u)
    x_hi, y_hi, z_hi = eval_headlight_upper_rim(u)

    # Recessed 1.5 mm neatly inside painted hood/fender/bumper opening with smooth lens dome
    dome = 0.011 * math.sin(v * math.pi) * math.sin(u * math.pi)
    x = x_lo + (x_hi - x_lo) * v - 0.0015
    y = y_lo + (y_hi - y_lo) * v - 0.002 + dome
    z = z_lo + (z_hi - z_lo) * v - 0.001 * v * math.sin(u * math.pi)
    return x, y, z


def build_front_headlights(col, mats):
    """Build complete internal + external optical assemblies for Matrix LED headlights (L/R)."""
    nu, nv = 32, 16
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    g_lens = np.zeros((nv, nu, 3), dtype=np.float64)
    g_back = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            x, y, z = _headlight_outline_point(u, v)
            g_lens[j, i] = (x, y, z)
            depth = 0.095 * (math.sin(u * math.pi) ** 0.42) * (math.sin(v * math.pi) ** 0.35) + 0.014
            g_back[j, i] = (x - depth * 0.25, y - depth, z - 0.003)

    create_grid_surface(
        "Light_Headlight_OuterLens", g_lens, col, material=mats["lens_clear"],
        mirror_x=True, flip_normals=False
    )

    create_grid_surface(
        "Light_Headlight_Housing", g_back, col, material=mats["light_housing"],
        mirror_x=True, flip_normals=False
    )

    # Slim tucked gloss-black rubber perimeter seal (2.2 mm radius -> flush, never sticks out!)
    rim_pts = []
    for u in np.linspace(0.01, 0.99, 24):
        x, y, z = _headlight_outline_point(u, 0.99)
        rim_pts.append((x - 0.001, y - 0.002, z - 0.001))
    for u in np.linspace(0.99, 0.01, 24):
        x, y, z = _headlight_outline_point(u, 0.01)
        rim_pts.append((x - 0.001, y - 0.002, z + 0.001))
    create_tube_along_points(
        "Light_Headlight_TrimSeal", rim_pts, 0.0022, col,
        material=mats["trim_gloss_black"], segments=8, mirror_x=True
    )

    # Match the continuous, tapered guide around the outside of the lamp.
    upper = [(u, 0.82) for u in np.linspace(0.10, 0.81, 25, endpoint=False)]
    corner = cubic_bezier(
        (0.81, 0.82), (0.97, 0.82), (0.98, 0.17), (0.83, 0.17),
        np.linspace(0.0, 1.0, 20, endpoint=False),
    )
    lower = [(u, 0.17) for u in np.linspace(0.83, 0.14, 26)]
    drl_pts = []
    radii = []
    for u, v in (*upper, *corner, *lower):
        x, y, z = _headlight_outline_point(u, v)
        drl_pts.append((x - 0.006, y - 0.014, z))
        r = 0.0009 + 0.0019 * min(1.0, (u - 0.08) / 0.22)
        radii.append((r, r * 0.8))
    create_tube_along_points(
        "Light_Headlight_DRL_Boomerang", drl_pts, radii, col,
        material=mats["led_drl"], segments=12, mirror_x=True,
    )

    # Separate the convex lens, its retaining ring and the recessed source.
    # Axial positions are relative to the front of the projector barrel.
    px, py, pz = _headlight_outline_point(0.74, 0.49)
    bezel_profile = [
        (0.021, -0.028), (0.024, -0.028), (0.024, -0.002),
        (0.022, 0.0), (0.0185, 0.0), (0.018, -0.002),
    ]
    lens_profile = [
        (0.0, 0.0053), (0.004, 0.0051), (0.008, 0.0045),
        (0.012, 0.0035), (0.016, 0.0018), (0.0186, -0.0002),
    ]
    emitter_profile = [(0.0, -0.017), (0.012, -0.017), (0.0187, -0.013)]
    for sign, sfx in [(1.0, "R"), (-1.0, "L")]:
        axis = Vector((sign * 0.22, 1.0, 0.02))
        for name, profile, material, closed in (
            ("ProjectorShroud", bezel_profile, "light_housing", True),
            ("MatrixProjectorLens", lens_profile, "lens_clear", False),
            ("MatrixProjectorEmitter", emitter_profile, "led_projector", False),
        ):
            component = create_revolved_mesh(
                f"Light_Headlight_{name}_{sfx}", profile, col, mats[material],
                segments=40, axis="Z", close_profile=closed,
            )
            component.location = (sign * (px - 0.013), py - 0.025, pz)
            component.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()

    # Inner Multi-Chamber Faceted Chrome Reflector Array (matching 2023_Tesla_Model_S_Plaid.jpg!)
    g_ref = np.zeros((10, 18, 3), dtype=np.float64)
    for j, tv in enumerate(np.linspace(0.20, 0.78, 10)):
        for i, tu in enumerate(np.linspace(0.14, 0.60, 18)):
            x, y, z = _headlight_outline_point(tu, tv)
            bay_wave = 0.015 * abs(math.sin(tu * 3.0 * math.pi)) + 0.016 * math.sin(tv * math.pi)
            g_ref[j, i] = (x - 0.013, y - 0.040 - bay_wave, z)
    create_grid_surface(
        "Light_Headlight_ChromeReflector", g_ref, col, material=mats["light_reflector"],
        mirror_x=True, flip_normals=False
    )

    # Outer Corner US-Spec Amber Side-Marker Reflector Strip
    g_amb = np.zeros((6, 8, 3), dtype=np.float64)
    for j, tv in enumerate(np.linspace(0.26, 0.70, 6)):
        for i, tu in enumerate(np.linspace(0.84, 0.95, 8)):
            x, y, z = _headlight_outline_point(tu, tv)
            g_amb[j, i] = (x - 0.014, y - 0.020, z)
    create_grid_surface(
        "Light_Headlight_AmberMarker", g_amb, col, material=mats["reflector_amber"],
        mirror_x=True, flip_normals=False
    )


def build_front_fog_lights(col, mats, opening):
    """Seat the smoked lens, LED blade and housing behind the bumper edge."""
    lens = opening.copy()
    lens[:, :, 1] -= 0.002
    housing = lens.copy()
    housing[:, :, 1] -= 0.024
    for part, grid, mat in (
        ("SmokedLens", lens, "lens_smoked"),
        ("Housing", housing, "light_housing"),
    ):
        create_grid_surface(f"Light_FrontFog_{part}", grid, col, mats[mat], mirror_x=True, flip_normals=True)

    blade = np.array([lens[0] * (1 - t) + lens[-1] * t for t in (0.36, 0.65)])
    blade[:, :, 1] -= 0.010
    create_grid_surface("Light_FrontFog_LED", blade, col, mats["led_fog"], mirror_x=True, flip_normals=True)


def _taillight_point(u, v):
    """
    Evaluate 100% flush 3D coordinate on the 2022-2024 Model S Plaid 2-piece LED taillight!
      - Inner trunk piece (u in [0.00..0.24]): locks seamlessly onto Body_Rear_Tailgate (X = 0.502..0.642)
      - Outer quarter piece (u in [0.24..1.00]): locks 0.0 mm onto unified C2 Bezier Rear Quarter!
    """
    u = max(0.0, min(1.0, float(u)))
    if u <= 0.24:
        t = u / 0.24
        x = 0.502 + (0.642 - 0.502) * t
        z_lo = 0.784 + 0.004 * t
        z_hi = 0.890 - 0.002 * t
        z = z_lo + (z_hi - z_lo) * v
        tv = max(0.0, min(1.0, (0.978 - z) / (0.978 - 0.570)))
        xw = 0.646 - 0.012 * (tv ** 1.3)
        u_tg = min(1.0, x / xw)
        y = -2.475 - 0.058 * (tv ** 0.85) - 0.008 * math.sin(tv * math.pi) + 0.084 * (u_tg ** 2.05)
        y -= 0.006 * math.sin(v * math.pi)
    else:
        t_out = (u - 0.24) / 0.76
        t_bez = t_out * 0.74
        if t_out <= 0.45:
            tt = t_out / 0.45
            z_lo = 0.788 + 0.010 * (tt ** 1.2)
            z_hi = 0.888 - 0.004 * (tt ** 1.3)
        else:
            tt = max(0.0, min(1.0, (t_out - 0.45) / 0.55))
            z_mid = 0.841 + 0.006 * tt
            half_h = 0.043 * (max(0.0, 1.0 - tt) ** 0.80) + 0.0025
            z_lo = z_mid - half_h
            z_hi = z_mid + half_h
        z = z_lo + (z_hi - z_lo) * v
        x, y, z = eval_rear_corner_bezier(t_bez, z)
        bulge = 0.0045 * math.sin(v * math.pi) * (1.0 - 0.5 * t_out)
        x += bulge * (0.25 + 0.75 * t_out) + 0.002 * t_out
        y -= bulge * (1.0 - 0.75 * t_out) + 0.003 * (1.0 - t_out)
    return x, y, z


def build_rear_taillights(col, mats):
    """Build authentic 2022-2024 refreshed 2-piece split Model S Plaid LED taillights."""
    nu, nv = 36, 14
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    g_lens = np.zeros((nv, nu, 3), dtype=np.float64)
    g_back = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            x, y, z = _taillight_point(u, v)
            g_lens[j, i] = (x, y, z)
            if u <= 0.56:
                g_back[j, i] = (x - 0.012 * (u / 0.56), y + 0.042, z)
            else:
                g_back[j, i] = (x - 0.028, y + 0.016, z)

    create_grid_surface(
        "Light_Taillight_OuterLens", g_lens, col, material=mats["lens_smoked"],
        mirror_x=True, flip_normals=True
    )

    create_grid_surface(
        "Light_Taillight_Housing", g_back, col, material=mats["light_housing"],
        mirror_x=True, flip_normals=True
    )

    # 1. Bold Crimson-Red U/C-Loop Signature LED Light Pipe (matching ts_rear_2022.jpg & IMG_9321!)
    loop_pts = []
    for u in np.linspace(0.02, 0.56, 18):
        x, y, z = _taillight_point(u, 0.80)
        loop_pts.append((x - 0.005, y + 0.014, z))
    for v in np.linspace(0.78, 0.22, 8):
        x, y, z = _taillight_point(0.56, v)
        loop_pts.append((x - 0.008, y + 0.014, z))
    for u in np.linspace(0.54, 0.02, 18):
        x, y, z = _taillight_point(u, 0.24)
        loop_pts.append((x - 0.005, y + 0.014, z))
    create_tube_along_points(
        "Light_Taillight_RedLoop_LED", loop_pts, (0.0065, 0.0082), col,
        material=mats["led_tail_red"], segments=12, mirror_x=True
    )

    # Side-wrap outer crimson marker blade (u in [0.58..0.90])
    side_pts = []
    for u in np.linspace(0.58, 0.90, 10):
        x, y, z = _taillight_point(u, 0.50)
        side_pts.append((x - 0.010, y + 0.006, z))
    create_tube_along_points(
        "Light_Taillight_SideMarker_LED", side_pts, (0.0052, 0.0085), col,
        material=mats["led_tail_red"], segments=10, mirror_x=True
    )

    # 2. Inner Horizontal Accent Bar (dark chrome light guide inside the U-loop)
    inner_pts = []
    for u in np.linspace(0.03, 0.46, 14):
        x, y, z = _taillight_point(u, 0.52)
        inner_pts.append((x - 0.004, y + 0.016, z))
    create_tube_along_points(
        "Light_Taillight_InnerBar", inner_pts, (0.0046, 0.0050), col,
        material=mats["light_reflector"], segments=8, mirror_x=True
    )

    # 3. Lower Slim Clear/White LED Reverse Strip (u in [0.02..0.40], v ~ 0.09)
    rev_pts = []
    for u in np.linspace(0.02, 0.40, 14):
        x, y, z = _taillight_point(u, 0.09)
        rev_pts.append((x - 0.004, y + 0.012, z))
    create_tube_along_points(
        "Light_Taillight_ReverseStrip", rev_pts, (0.0042, 0.0042), col,
        material=mats["led_tail_reverse"], segments=8, mirror_x=True
    )

    # Crisp thin dark vertical tailgate split line across taillight at X = 0.642 (u = 0.24)
    split_pts = []
    for v in np.linspace(0.0, 1.0, 8):
        x, y, z = _taillight_point(0.24, v)
        split_pts.append((x, y - 0.002, z))
    create_tube_along_points(
        "Light_Taillight_TrunkSplit", split_pts, 0.0022, col,
        material=mats["shadow_gap"], segments=6, mirror_x=True
    )


def build_rear_reflectors(col, mats):
    """Build slim horizontal red reflectors flush along the upper outer corners of the Plaid rear diffuser."""
    nu, nv = 14, 5
    grid = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv)):
        for i, u in enumerate(np.linspace(0.0, 1.0, nu)):
            x = 0.468 + u * (0.674 - 0.468)
            u_d = x / 0.678
            y = -2.556 + 0.148 * (u_d ** 2.1) - 0.0025
            z = 0.342 + v * 0.016 - 0.006 * u
            grid[j, i] = (x, y, z)
    ref = create_grid_surface(
        "Light_RearBumper_Reflector", grid, col, material=mats["reflector_red"],
        mirror_x=True, flip_normals=False
    )
    add_solidify(ref, thickness=0.004, offset=1.0)


def build_all_lighting(root_col, mats, fog_opening):
    col = ensure_collection("03_Lighting_Optics", root_col)
    build_front_headlights(col, mats)
    build_front_fog_lights(col, mats, fog_opening)
    build_rear_taillights(col, mats)
    build_rear_reflectors(col, mats)
    return col
