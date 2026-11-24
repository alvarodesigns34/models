"""
Automotive Glazing, Ceramic Frit, B-Pillar Autopilot Camera, and Satin-Black
DLO Window Trim for the 2024 Tesla Model S Plaid.
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


def _eval_top_glass_surface(y_start, y_end, nu=32, nv=24, z_offset=-0.002):
    """Evaluate smoothly arched top glazing surface (windshield, panoramic roof, or hatch glass)."""
    ys = np.linspace(y_start, y_end, nv)
    us = np.linspace(0.0, 1.0, nu)
    grid = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, y in enumerate(ys):
        zc = BodyCurves.roof_center_z(y)
        xe, ze = BodyCurves.glass_edge(y)
        for i, u in enumerate(us):
            x = u * xe
            # Smooth automotive cylindrical-spherical glass curvature
            z = zc + (ze - zc) * (u ** 1.92) + z_offset
            # Windshield base curves slightly forward at center in plan view
            y_adj = y
            if y > 0.72:
                tf = (y - 0.72) / (0.955 - 0.72)
                y_adj = y - 0.055 * (u ** 2.1) * tf
            grid[j, i] = (x, y_adj, z)
    return grid


def build_top_glazing(col, mats):
    """Build Windshield, Panoramic All-Glass Roof, Rear Fastback Hatch Glass, and Frit/Camera details."""
    # 1. Laminated Windshield (Y = +0.115 to +0.955) — flip_normals=True for verified upward (+Z) outward normals!
    g_ws = _eval_top_glass_surface(0.115, 0.955, nu=30, nv=24, z_offset=-0.002)
    create_grid_surface(
        "Glass_Windshield", g_ws, col, material=mats["glass_windshield"],
        mirror_x=True, flip_normals=True
    )

    # Windshield black ceramic frit perimeter band + top Autopilot HW4 triple-camera bezel
    g_frit_top = _eval_top_glass_surface(0.115, 0.195, nu=24, nv=6, z_offset=-0.006)
    create_grid_surface("Glass_Windshield_FritTop", g_frit_top, col, material=mats["glass_frit"], mirror_x=True, flip_normals=True)
    g_frit_bot = _eval_top_glass_surface(0.875, 0.955, nu=24, nv=6, z_offset=-0.006)
    create_grid_surface("Glass_Windshield_FritBot", g_frit_bot, col, material=mats["glass_frit"], mirror_x=True, flip_normals=True)

    # Autopilot HW4 Forward Triple-Camera Trapezoid Housing (behind upper-center windshield!)
    bm = bmesh.new()
    pts_top = [(-0.095, 0.16, 1.375), (0.095, 0.16, 1.375), (0.072, 0.30, 1.312), (-0.072, 0.30, 1.312)]
    pts_bot = [(-0.088, 0.14, 1.345), (0.088, 0.14, 1.345), (0.065, 0.28, 1.285), (-0.065, 0.28, 1.285)]
    vt = [bm.verts.new(p) for p in pts_top]
    vb = [bm.verts.new(p) for p in pts_bot]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    for k in range(4):
        kn = (k + 1) % 4
        bm.faces.new((vt[k], vt[kn], vb[kn], vb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m_cam = bpy.data.meshes.new("Sensor_Autopilot_FrontCameraPod")
    bm.to_mesh(m_cam)
    bm.free()
    set_smooth_shading(m_cam)
    cam_pod = bpy.data.objects.new("Sensor_Autopilot_FrontCameraPod", m_cam)
    link_object(cam_pod, col)
    cam_pod.data.materials.append(mats["trim_matte_plastic"])

    for idx, x_lens in enumerate([-0.036, 0.0, 0.036]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.008, depth=0.012, location=(x_lens, 0.245, 1.325))
        lens = bpy.context.active_object
        lens.name = f"Sensor_HW4_FrontLens_{idx}"
        lens.rotation_euler = (math.radians(62), 0.0, 0.0)
        link_object(lens, col)
        lens.data.materials.append(mats["camera_lens"])

    # 2. Panoramic All-Glass Roof (Y = -1.095 to +0.108)
    g_roof = _eval_top_glass_surface(-1.095, 0.108, nu=30, nv=24, z_offset=-0.001)
    create_grid_surface(
        "Glass_Panoramic_Roof", g_roof, col, material=mats["glass_roof"],
        mirror_x=True, flip_normals=True
    )

    for sname, y_seam in [("Seal_Roof_Front", 0.111), ("Seal_Roof_Rear", -1.098)]:
        pts = []
        zc = BodyCurves.roof_center_z(y_seam)
        xe, ze = BodyCurves.glass_edge(y_seam)
        for u in np.linspace(0.0, 1.0, 20):
            pts.append((u * xe, y_seam, zc + (ze - zc) * (u ** 1.92) - 0.003))
        create_tube_along_points(sname, pts, 0.0035, col, material=mats["trim_satin_black"], segments=10, mirror_x=True)

    # 3. Fastback Rear Hatch Glass (Y = -2.138 to -1.102)
    g_rear = _eval_top_glass_surface(-2.138, -1.102, nu=30, nv=24, z_offset=-0.002)
    create_grid_surface(
        "Glass_Rear_Hatch", g_rear, col, material=mats["glass_rear"],
        mirror_x=True, flip_normals=True
    )

    pts_chmsl = []
    y_ch = -1.145
    zc_ch = BodyCurves.roof_center_z(y_ch)
    xe_ch, ze_ch = BodyCurves.glass_edge(y_ch)
    for u in np.linspace(0.0, 0.24, 10):
        pts_chmsl.append((u * xe_ch, y_ch, zc_ch + (ze_ch - zc_ch) * (u ** 1.92) - 0.010))
    create_tube_along_points("Light_CHMSL_ThirdBrake", pts_chmsl, (0.005, 0.004), col, material=mats["reflector_red"], segments=8, mirror_x=True)

    # Cowl plenum satin-black tray tucked cleanly inside hood/windshield boundary
    g_cowl = _eval_top_glass_surface(0.925, 0.995, nu=28, nv=8, z_offset=-0.018)
    create_grid_surface("Trim_Windshield_Cowl", g_cowl, col, material=mats["trim_matte_plastic"], mirror_x=True, flip_normals=True)


def _eval_side_window_surface(y0, y1, ny=22, nv=12, x_inset=0.007):
    """Evaluate curved frameless side window glass between beltline and cantrail DLO arch."""
    ys = np.linspace(y0, y1, ny)
    vs = np.linspace(0.0, 1.0, nv)
    grid = np.zeros((ny, nv, 3), dtype=np.float64)
    for i, y in enumerate(ys):
        xb, zb = BodyCurves.beltline(y)
        xc, zc = BodyCurves.cantrail_outer(max(-1.515, min(0.865, y)))
        if zc < zb + 0.010:
            zc = zb + 0.010
        for j, v in enumerate(vs):
            bow = 0.013 * math.sin(v * math.pi)
            x = xb + (xc - xb) * (v ** 1.05) + bow - x_inset
            z = zb + (zc - zb) * v
            grid[i, j] = (x, y, z)
    return grid


def build_side_glazing_and_dlo(col, mats):
    """
    Build Frameless Front Door Glass, Rear Door Glass, C-Pillar Quarter Glass,
    Flush Gloss-Black B-Pillar Glass w/ Autopilot Camera, and Satin-Black DLO Window Trim.
    """
    # 1. Front Door Window (Y = -0.175 to +0.835)
    g_fw = _eval_side_window_surface(-0.175, 0.835, ny=24, nv=14, x_inset=0.006)
    fw = create_grid_surface(
        "Glass_Front_Door", g_fw, col, material=mats["glass_side"],
        mirror_x=True, flip_normals=False
    )

    # 2. Flush Gloss-Black B-Pillar Glass Applique (Y = -0.268 to -0.172)
    g_bp = _eval_side_window_surface(-0.268, -0.172, ny=8, nv=14, x_inset=0.003)
    bp = create_grid_surface(
        "Trim_B_Pillar_GlossBlack", g_bp, col, material=mats["trim_gloss_black"],
        mirror_x=True, flip_normals=False
    )
    add_solidify(bp, thickness=0.006, offset=-1.0)

    # Embedded circular B-Pillar Autopilot Camera Lens (L/R) near top of B-pillar!
    xb, zb = BodyCurves.beltline(-0.220)
    xc, zc = BodyCurves.cantrail_outer(-0.220)
    v_cam = 0.72
    cam_x = xb + (xc - xb) * (v_cam ** 1.05) + 0.013 * math.sin(v_cam * math.pi) - 0.003
    cam_z = zb + (zc - zb) * v_cam
    for sign, side_name in [(1.0, "R"), (-1.0, "L")]:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24, radius=0.011, depth=0.005,
            location=(sign * cam_x, -0.220, cam_z)
        )
        bcam = bpy.context.active_object
        bcam.name = f"Sensor_B_Pillar_Camera_{side_name}"
        bcam.rotation_euler = (0.0, sign * math.radians(74), 0.0)
        link_object(bcam, col)
        bcam.data.materials.append(mats["camera_lens"])

    # 3. Rear Door Window (Y = -1.035 to -0.270)
    g_rw = _eval_side_window_surface(-1.035, -0.270, ny=20, nv=14, x_inset=0.006)
    rw = create_grid_surface(
        "Glass_Rear_Door", g_rw, col, material=mats["glass_side"],
        mirror_x=True, flip_normals=False
    )

    # Thin gloss-black division bar between rear door glass & C-pillar quarter glass
    g_div = _eval_side_window_surface(-1.062, -1.032, ny=4, nv=10, x_inset=0.004)
    create_grid_surface("Trim_Rear_Quarter_Divider", g_div, col, material=mats["trim_gloss_black"], mirror_x=True)

    # 4. C-Pillar Fixed Quarter Glass (Y = -1.505 to -1.060)
    g_qw = _eval_side_window_surface(-1.505, -1.060, ny=16, nv=10, x_inset=0.006)
    qw = create_grid_surface(
        "Glass_Quarter_Window", g_qw, col, material=mats["glass_side"],
        mirror_x=True, flip_normals=False
    )

    # 5. Continuous Satin-Black DLO Window Surround Molding (OEM Chrome-Delete!)
    pts_upper = []
    for y in np.linspace(0.855, -1.515, 42):
        xc, zc = BodyCurves.cantrail_outer(y)
        pts_upper.append((xc + 0.001, y, zc - 0.004))
    create_tube_along_points(
        "Trim_DLO_Upper_Arch", pts_upper, (0.0085, 0.011), col,
        material=mats["trim_satin_black"], segments=12, mirror_x=True
    )

    pts_lower = []
    for y in np.linspace(0.855, -1.515, 42):
        xb, zb = BodyCurves.beltline(y)
        pts_lower.append((xb + 0.002, y, zb + 0.003))
    create_tube_along_points(
        "Trim_DLO_Lower_Belt", pts_lower, (0.0085, 0.010), col,
        material=mats["trim_satin_black"], segments=12, mirror_x=True
    )


def build_all_glazing(root_col, mats):
    col = ensure_collection("02_Glazing_And_DLO", root_col)
    build_top_glazing(col, mats)
    build_side_glazing_and_dlo(col, mats)
    return col
