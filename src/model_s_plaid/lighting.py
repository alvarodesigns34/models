"""
High-Precision Optical Lighting Systems for the 2024 Tesla Model S Plaid:
  - 2022-2024 Adaptive Matrix LED Headlights (outer polycarbonate cover lens,
    dark internal bezel, Bi-LED projector dome, multi-chamber chrome reflectors,
    crisp continuous white LED DRL boomerang)
  - Front Lower Bumper Smoked LED Fog/Accent Strips
  - 2022-2024 Refreshed 2-Piece Split LED Taillights (crimson-red U/C LED light
    pipe loop, twin dark smoked inner horizontal bars, clear LED reverse strip,
    smoked-edge polycarbonate cover lens)
  - Lower Rear Diffuser Integrated Red Reflectors
"""

import math
import numpy as np
import bpy
import bmesh

from . import config as C
from .body_master import BodyCurves
from .geometry_utils import (
    ensure_collection,
    create_grid_surface,
    create_tube_along_points,
    add_solidify,
    set_smooth_shading,
    link_object,
)


def _headlight_outline_point(u, v):
    """
    Evaluate flush 3D coordinate on the swept teardrop Matrix LED headlight face (Iter 3 calibrated!).
    u in [0 (inner nose tip) .. 1 (outer fender sweep corner)]
    v in [0 (lower bumper rim) .. 1 (upper hood/fender brow)]
    """
    # Exact 0.0 mm match to Iter 3 Body_Front_Bumper top headlight edge (u_b in [0.34..0.84])
    x_lo = 0.405 + (0.885 - 0.405) * u
    y_lo = 2.263 - (2.263 - 1.868) * (u ** 1.12)
    z_lo = 0.584 + 0.072 * (u ** 1.22) - 0.011 * math.sin(u * math.pi)

    x_hi = 0.405 + (0.885 - 0.405) * (u ** 0.96)
    y_hi = 2.256 - (2.256 - 1.855) * (u ** 1.14)
    # Authentic ~104 mm vertical sculptural opening matching 1X7A0025 & IMG_9278!
    arch = 0.104 * math.sin((u ** 0.70) * math.pi * 0.94)
    z_hi = z_lo + arch

    x = x_lo + (x_hi - x_lo) * v
    y = y_lo + (y_hi - y_lo) * v + 0.015 * math.sin(v * math.pi) * math.sin(u * math.pi)
    z = z_lo + (z_hi - z_lo) * v
    return x, y, z


def build_front_headlights(col, mats):
    """Build complete internal + external optical assemblies for Matrix LED headlights (L/R)."""
    nu, nv = 30, 16
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    # 1. Outer Clear Polycarbonate Cover Lens (flush with hood/bumper/fender!)
    g_lens = np.zeros((nv, nu, 3), dtype=np.float64)
    g_back = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            x, y, z = _headlight_outline_point(u, v)
            g_lens[j, i] = (x, y, z)
            depth = 0.098 * math.sin(u * math.pi) ** 0.4 * math.sin(v * math.pi) ** 0.35 + 0.014
            g_back[j, i] = (x - depth * 0.25, y - depth, z - 0.004)

    create_grid_surface(
        "Light_Headlight_OuterLens", g_lens, col, material=mats["lens_clear"],
        mirror_x=True, flip_normals=True
    )

    # 2. Dark Internal Headlamp Bezel Housing
    create_grid_surface(
        "Light_Headlight_Housing", g_back, col, material=mats["light_housing"],
        mirror_x=True, flip_normals=True
    )

    # Black perimeter seal rim around cover lens
    rim_pts = []
    for u in np.linspace(0.0, 1.0, 24):
        rim_pts.append(_headlight_outline_point(u, 1.0))
    for u in np.linspace(1.0, 0.0, 24):
        rim_pts.append(_headlight_outline_point(u, 0.0))
    create_tube_along_points(
        "Light_Headlight_TrimSeal", rim_pts, 0.0032, col,
        material=mats["trim_gloss_black"], segments=8, mirror_x=True
    )

    # 3. Signature White LED DRL Boomerang Light-Pipe (Top Brow -> Outer Corner -> Lower Edge!)
    drl_pts = []
    for u in np.linspace(0.05, 0.95, 24):
        x, y, z = _headlight_outline_point(u, 0.87)
        drl_pts.append((x - 0.006, y - 0.018, z - 0.002))
    for v in np.linspace(0.84, 0.16, 8):
        x, y, z = _headlight_outline_point(0.95, v)
        drl_pts.append((x - 0.008, y - 0.018, z))
    for u in np.linspace(0.93, 0.32, 16):
        x, y, z = _headlight_outline_point(u, 0.13)
        drl_pts.append((x - 0.006, y - 0.018, z + 0.003))
    create_tube_along_points(
        "Light_Headlight_DRL_Boomerang", drl_pts, (0.0060, 0.0050), col,
        material=mats["led_drl"], segments=12, mirror_x=True
    )

    # 4. Outer Bi-LED Adaptive Matrix Projector Module (L/R)
    px, py, pz = _headlight_outline_point(0.73, 0.50)
    for sign, sfx in [(1.0, "R"), (-1.0, "L")]:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=28, radius=0.027, depth=0.048,
            location=(sign * (px - 0.014), py - 0.050, pz)
        )
        shroud = bpy.context.active_object
        shroud.name = f"Light_Headlight_ProjectorShroud_{sfx}"
        shroud.rotation_euler = (math.radians(90), 0.0, sign * math.radians(-16))
        link_object(shroud, col)
        shroud.data.materials.append(mats["light_housing"])

        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=24, ring_count=16, radius=0.022,
            location=(sign * (px - 0.012), py - 0.032, pz)
        )
        dome = bpy.context.active_object
        dome.name = f"Light_Headlight_MatrixProjector_{sfx}"
        dome.scale = (1.0, 0.65, 1.0)
        link_object(dome, col)
        dome.data.materials.append(mats["led_projector"])

    # 5. Inner Multi-Chamber Faceted Chrome Reflector Array (matching 2023_Tesla_Model_S_Plaid.jpg!)
    g_ref = np.zeros((10, 18, 3), dtype=np.float64)
    for j, tv in enumerate(np.linspace(0.18, 0.80, 10)):
        for i, tu in enumerate(np.linspace(0.14, 0.62, 18)):
            x, y, z = _headlight_outline_point(tu, tv)
            bay_wave = 0.016 * abs(math.sin(tu * 3.0 * math.pi)) + 0.018 * math.sin(tv * math.pi)
            g_ref[j, i] = (x - 0.012, y - 0.042 - bay_wave, z)
    create_grid_surface(
        "Light_Headlight_ChromeReflector", g_ref, col, material=mats["light_reflector"],
        mirror_x=True, flip_normals=True
    )

    # 6. Outer Corner US-Spec Amber Side-Marker Reflector Strip (matching 2023_Tesla_Model_S_Plaid.jpg!)
    g_amb = np.zeros((6, 8, 3), dtype=np.float64)
    for j, tv in enumerate(np.linspace(0.24, 0.72, 6)):
        for i, tu in enumerate(np.linspace(0.86, 0.97, 8)):
            x, y, z = _headlight_outline_point(tu, tv)
            g_amb[j, i] = (x - 0.012, y - 0.020, z)
    create_grid_surface(
        "Light_Headlight_AmberMarker", g_amb, col, material=mats["reflector_amber"],
        mirror_x=True, flip_normals=True
    )


def build_front_fog_lights(col, mats):
    """Build sleek lower-bumper recessed needle-wedge horizontal LED fog strips (matching 1X7A0025.jpg!)."""
    nu, nv = 16, 6
    g_lens = np.zeros((nv, nu, 3), dtype=np.float64)
    g_led = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv)):
        for i, u in enumerate(np.linspace(0.0, 1.0, nu)):
            x = 0.580 + u * (0.842 - 0.580)
            y = 2.238 - 0.175 * (u ** 1.25) - 0.010 * v
            # Slim needle-wedge height tapering cleanly toward inner grille
            h = 0.008 + 0.014 * (u ** 0.85)
            z_base = 0.316 - 0.012 * u
            z = z_base + v * h
            g_lens[j, i] = (x, y, z)
            g_led[j, i] = (x - 0.005, y - 0.015, z_base + (0.25 + 0.5 * v) * h)

    create_grid_surface(
        "Light_FrontFog_SmokedLens", g_lens, col, material=mats["lens_smoked"],
        mirror_x=True, flip_normals=True
    )

    create_grid_surface(
        "Light_FrontFog_LED", g_led, col, material=mats["led_fog"],
        mirror_x=True, flip_normals=True
    )


def _taillight_point(u, v):
    """
    Evaluate 100% flush 3D coordinate on the 2022-2024 Model S Plaid 2-piece LED taillight!
    Inner rear face (u in [0..0.58]) locks seamlessly to Body_Rear_Tailgate & Rear Corner Wrap;
    outer side wrap (u in [0.58..1.0]) locks seamlessly to BodyCurves.eval_flank_x_at_yz!
    """
    if u <= 0.58:
        t = u / 0.58
        x = 0.502 + (0.816 - 0.502) * (t ** 0.92)
        y = -2.455 + 0.118 * (t ** 1.55)
        z_lo = 0.782 + 0.012 * (t ** 1.25)
        z_hi = 0.892 - 0.005 * (t ** 1.45)
        z = z_lo + (z_hi - z_lo) * v
        bulge = 0.008 * math.sin(v * math.pi)
        y -= bulge * (1.0 - 0.45 * t)
        x += bulge * 0.35 * t
    else:
        t = max(0.0, min(1.0, (u - 0.58) / 0.42))
        y = -2.337 + 0.205 * t
        z_mid = 0.840 + 0.006 * t
        half_h = 0.047 * (max(0.0, 1.0 - t) ** 0.78) + 0.003
        z_lo = z_mid - half_h
        z_hi = z_mid + half_h
        z = z_lo + (z_hi - z_lo) * v
        # Dynamically lock X onto exact Class-A Rear Quarter surface (ZERO protrusion!)
        x_flank = BodyCurves.eval_flank_x_at_yz(y, z)
        bulge = 0.004 * math.sin(v * math.pi) * (1.0 - 0.6 * t)
        x = x_flank + 0.002 + bulge
    return x, y, z


def build_rear_taillights(col, mats):
    """
    Build authentic 2022-2024 refreshed 2-piece split Model S Plaid LED taillights.
    """
    nu, nv = 34, 14
    us = np.linspace(0.0, 1.0, nu)
    vs = np.linspace(0.0, 1.0, nv)

    g_lens = np.zeros((nv, nu, 3), dtype=np.float64)
    g_back = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            x, y, z = _taillight_point(u, v)
            g_lens[j, i] = (x, y, z)
            if u <= 0.58:
                g_back[j, i] = (x - 0.010 * (u / 0.58), y + 0.044, z)
            else:
                g_back[j, i] = (x - 0.032, y + 0.018, z)

    create_grid_surface(
        "Light_Taillight_OuterLens", g_lens, col, material=mats["lens_smoked"],
        mirror_x=True, flip_normals=False
    )

    create_grid_surface(
        "Light_Taillight_Housing", g_back, col, material=mats["light_housing"],
        mirror_x=True, flip_normals=False
    )

    # 1. Bold Crimson-Red U/C-Loop Signature LED Light Pipe (matching ts_rear_2022.jpg & IMG_9321!)
    loop_pts = []
    for u in np.linspace(0.02, 0.56, 18):
        x, y, z = _taillight_point(u, 0.80)
        loop_pts.append((x - 0.004, y + 0.015, z))
    for v in np.linspace(0.78, 0.22, 8):
        x, y, z = _taillight_point(0.56, v)
        loop_pts.append((x - 0.006, y + 0.015, z))
    for u in np.linspace(0.54, 0.02, 18):
        x, y, z = _taillight_point(u, 0.24)
        loop_pts.append((x - 0.004, y + 0.015, z))
    create_tube_along_points(
        "Light_Taillight_RedLoop_LED", loop_pts, (0.0065, 0.0085), col,
        material=mats["led_tail_red"], segments=12, mirror_x=True
    )

    # Side-wrap outer crimson marker fin (u in [0.60..0.90])
    side_pts = []
    for u in np.linspace(0.60, 0.90, 10):
        x, y, z = _taillight_point(u, 0.50)
        side_pts.append((x - 0.012, y + 0.008, z))
    create_tube_along_points(
        "Light_Taillight_SideMarker_LED", side_pts, (0.0055, 0.009), col,
        material=mats["led_tail_red"], segments=10, mirror_x=True
    )

    # 2. Inner Horizontal Accent Bar (metallic light guide inside the U-loop)
    inner_pts = []
    for u in np.linspace(0.04, 0.46, 14):
        x, y, z = _taillight_point(u, 0.52)
        inner_pts.append((x - 0.003, y + 0.018, z))
    create_tube_along_points(
        "Light_Taillight_InnerBar", inner_pts, (0.0048, 0.0052), col,
        material=mats["light_reflector"], segments=8, mirror_x=True
    )

    # 3. Lower Slim Clear/White LED Reverse Strip (u in [0.02..0.40], v ~ 0.09)
    rev_pts = []
    for u in np.linspace(0.02, 0.40, 14):
        x, y, z = _taillight_point(u, 0.09)
        rev_pts.append((x - 0.003, y + 0.013, z))
    create_tube_along_points(
        "Light_Taillight_ReverseStrip", rev_pts, (0.0042, 0.0042), col,
        material=mats["led_tail_reverse"], segments=8, mirror_x=True
    )

    # Crisp thin dark vertical tailgate split line across taillight at X ~ 0.642 (u ~ 0.255)
    split_pts = []
    for v in np.linspace(0.0, 1.0, 8):
        x, y, z = _taillight_point(0.255, v)
        split_pts.append((x, y - 0.002, z))
    create_tube_along_points(
        "Light_Taillight_TrunkSplit", split_pts, 0.0024, col,
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
            # Flush 2.5 mm proud of Iter 3 Trim_Rear_Diffuser upper outer lip!
            y = -2.556 + 0.148 * (u_d ** 2.1) - 0.0025
            z = 0.342 + v * 0.016 - 0.006 * u
            grid[j, i] = (x, y, z)
    ref = create_grid_surface(
        "Light_RearBumper_Reflector", grid, col, material=mats["reflector_red"],
        mirror_x=True, flip_normals=False
    )
    add_solidify(ref, thickness=0.004, offset=1.0)


def build_all_lighting(root_col, mats):
    col = ensure_collection("03_Lighting_Optics", root_col)
    build_front_headlights(col, mats)
    build_front_fog_lights(col, mats)
    build_rear_taillights(col, mats)
    build_rear_reflectors(col, mats)
    return col
