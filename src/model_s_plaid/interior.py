"""
Full Photorealistic Cabin Interior for the 2024 Tesla Model S Plaid:
  - 2024 Plaid Sport Seats (perforated vegan leather + Alcantara lateral bolsters +
    integrated headrest + recessed metallic Plaid composite chest emblem!)
  - Steering Yoke (flat-top sculpted leather rim, satin-silver trim, dual scroll wheels, T pad)
  - 17.0" Landscape Central Touchscreen + 12.3" Driver Instrument Cluster + 9.4" Rear Screen
  - Full-width Minimalist Dashboard w/ Matte 2x2 Twill Carbon Fiber Décor & hidden HVAC slot
  - Sweeping Center Console (dual Alcantara wireless chargers, carbon sliding lids, armrest)
  - Contoured Rear 60/40 Bench + Inner Door Cards + Alcantara Pillars/Headliner + Aluminum Pedals
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

from . import config as C
from .body_master import BodyCurves
from .geometry_utils import (
    ensure_collection,
    create_grid_surface,
    create_tube_along_points,
    add_bevel,
    set_smooth_shading,
    link_object,
)


def _create_uv_plane(name, corners_4, col, mat):
    """Create a clean UV-mapped rectangular quad (bl, br, tr, tl) for emissive screens & badges."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(p) for p in corners_4]
    f = bm.faces.new(vs)
    for loop, uv in zip(f.loops, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        loop[uv_layer].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name)
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    link_object(obj, col)
    obj.data.materials.append(mat)
    return obj


def build_cabin_shell_and_headliner(col, mats):
    """Build black carpeted cabin floor, firewall, rear cargo floor, Alcantara pillars & headliner."""
    # 1. Flat EV Cabin Floor & Footwell Carpet (Z = 0.275 m, spanning Y = -1.65..+0.88)
    ys = np.array([-1.85, -1.35, -0.95, -0.45, 0.45, 0.88])
    zs = np.array([0.46,   0.38,  0.29,  0.275, 0.275, 0.48])
    xs = np.array([0.62,   0.72,  0.78,  0.80,  0.80,  0.76])
    grid = np.zeros((len(ys), 6, 3), dtype=np.float64)
    for i in range(len(ys)):
        for j, u in enumerate(np.linspace(0.0, 1.0, 6)):
            grid[i, j] = (u * xs[i], ys[i], zs[i])
    create_grid_surface(
        "Interior_Floor_Carpet", grid, col, material=mats["int_carpet"],
        mirror_x=True, flip_normals=False
    )

    # Rear cargo parcel shelf behind rear seats
    g_shelf = np.zeros((4, 6, 3), dtype=np.float64)
    for i, y in enumerate(np.linspace(-2.05, -1.36, 4)):
        for j, u in enumerate(np.linspace(0.0, 1.0, 6)):
            g_shelf[i, j] = (u * 0.66, y, 0.905 - 0.045 * ((y + 1.36) / -0.69))
    create_grid_surface("Interior_Rear_ParcelShelf", g_shelf, col, material=mats["int_carpet"], mirror_x=True)

    # 2. Inner Alcantara Roof Perimeter Frame (framing the panoramic glass roof cleanly!)
    ny = 32
    ys_h = np.linspace(-1.55, 0.85, ny)
    g_hl = np.zeros((ny, 4, 3), dtype=np.float64)
    for i, y in enumerate(ys_h):
        xg, zg = BodyCurves.glass_edge(max(-1.55, min(0.85, y)))
        xc, zc = BodyCurves.cantrail_outer(max(-1.52, min(0.86, y)))
        g_hl[i, 0] = (xg - 0.035, y, zg - 0.025)
        g_hl[i, 1] = (xg + 0.015, y, zg - 0.022)
        g_hl[i, 2] = (xc - 0.030, y, zc - 0.024)
        g_hl[i, 3] = (xc - 0.022, y, zc - 0.050)
    create_grid_surface("Interior_Headliner_Rails", g_hl, col, material=mats["int_alcantara"], mirror_x=True, flip_normals=True)

    # Front windshield header crossbeam (Alcantara) + Sun Visors + Frameless Rearview Mirror
    pts_hdr = []
    for u in np.linspace(-1.0, 1.0, 16):
        pts_hdr.append((u * 0.58, 0.135, 1.378 - 0.035 * (u * u)))
    create_tube_along_points("Interior_Windshield_Header", pts_hdr, (0.035, 0.022), col, material=mats["int_alcantara"], segments=10)

    # Sun visors (L/R)
    for sign, tag in [(-1.0, "L"), (1.0, "R")]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sign * 0.32, 0.21, 1.325))
        sv = bpy.context.active_object
        sv.name = f"Interior_SunVisor_{tag}"
        sv.scale = (0.34, 0.14, 0.014)
        sv.rotation_euler = (math.radians(-30), 0.0, 0.0)
        link_object(sv, col)
        sv.data.materials.append(mats["int_alcantara"])
        add_bevel(sv, width=0.004, segments=2)

    # Frameless Interior Auto-Dimming Rearview Mirror
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.30, 1.245))
    rvm = bpy.context.active_object
    rvm.name = "Interior_RearviewMirror"
    rvm.scale = (0.21, 0.016, 0.056)
    rvm.rotation_euler = (math.radians(6), 0.0, 0.0)
    link_object(rvm, col)
    rvm.data.materials.append(mats["trim_gloss_black"])
    add_bevel(rvm, width=0.004, segments=2)


def build_dashboard_and_screens(col, mats):
    """
    Build sweeping minimalist Model S Plaid dashboard with:
      - Soft-touch upper vegan leather dash pad
      - Matte 2x2 twill Carbon Fiber Décor full-width inlay
      - Recessed 12.3" Driver Instrument Cluster binnacle
      - Floating 17.0" Landscape Central Touchscreen
      - Sculpted Center Console w/ dual Alcantara wireless phone pads, Carbon Fiber lids,
        armrest, and 9.4" Rear Touchscreen!
    """
    # 1. Upper Dashboard Main Pad (sculpted wrap-around sweep X = ±0.78, Y = 0.44..0.88)
    nu, nv = 28, 12
    g_dash = np.zeros((nv, nu, 3), dtype=np.float64)
    for i, u in enumerate(np.linspace(-1.0, 1.0, nu)):
        x = u * 0.775
        # Subtle driver binnacle dome rise on left side (x ~ -0.37)
        binnacle = 0.048 * math.exp(-((x + 0.37) / 0.21) ** 2)
        for j, v in enumerate(np.linspace(0.0, 1.0, nv)):
            # v=0: front near windshield base -> v=1: cabin-facing brow lip & underside
            y_front = 0.875 - 0.065 * (u * u)
            y_rear = 0.445 - 0.055 * (u * u) - 0.035 * math.exp(-((x + 0.37) / 0.22) ** 2)
            if v <= 0.65:
                t = v / 0.65
                y = y_front + (y_rear - y_front) * t
                z = 0.885 + 0.025 * math.sin(t * math.pi * 0.85) + binnacle * (t ** 0.8) - 0.015 * (u * u)
            else:
                t = (v - 0.65) / 0.35
                y = y_rear + 0.055 * t
                z = (0.898 + binnacle - 0.015 * (u * u)) - 0.145 * t
            g_dash[j, i] = (x, y, z)
    create_grid_surface("Interior_Dashboard_Upper", g_dash, col, material=mats["int_leather"], flip_normals=False)

    # 2. Full-Width Matte 2x2 Twill Carbon Fiber Décor Fascia Strip!
    g_cf = np.zeros((8, 28, 3), dtype=np.float64)
    for i, u in enumerate(np.linspace(-1.0, 1.0, 28)):
        x = u * 0.770
        y_base = 0.470 - 0.055 * (u * u)
        for j, v in enumerate(np.linspace(0.0, 1.0, 8)):
            z = 0.720 + v * 0.118 - 0.012 * (u * u)
            y = y_base - 0.014 * math.sin(v * math.pi)
            g_cf[j, i] = (x, y, z)
    create_grid_surface(
        "Interior_Dashboard_CarbonDecor", g_cf, col, material=mats["carbon_int"],
        flip_normals=True, uv_scale=(4.0, 0.8)
    )

    # 3. 12.3" Driver Instrument Cluster Screen recessed cleanly inside driver binnacle (visible over Yoke!)
    cl_w, cl_h = 0.285, 0.106
    cx, cy, cz = -0.370, 0.462, 0.848
    tilt = math.radians(10.0)
    # Dark binnacle bezel framing the 12.3" cluster cleanly
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy + 0.008, cz))
    cbez = bpy.context.active_object
    cbez.name = "Interior_Screen_Cluster12in_Bezel"
    cbez.scale = (cl_w + 0.016, 0.012, cl_h + 0.016)
    cbez.rotation_euler = (-tilt, 0.0, 0.0)
    link_object(cbez, col)
    cbez.data.materials.append(mats["trim_satin_black"])

    dh_y = (cl_h * 0.5) * math.sin(tilt)
    dh_z = (cl_h * 0.5) * math.cos(tilt)
    _create_uv_plane(
        "Interior_Screen_Cluster12in",
        [
            (cx - cl_w * 0.5, cy - dh_y, cz - dh_z),
            (cx + cl_w * 0.5, cy - dh_y, cz - dh_z),
            (cx + cl_w * 0.5, cy + dh_y, cz + dh_z),
            (cx - cl_w * 0.5, cy + dh_y, cz + dh_z),
        ],
        col, mats["screen_cluster"]
    )

    # 4. Floating 17.0" Landscape Central Touchscreen (384 mm x 226 mm, slim dark bezel — ZERO clipping!)
    sc_w, sc_h = 0.384, 0.226
    sy, sz = 0.398, 0.764
    stilt = math.radians(14.0)
    # Note: (-stilt) tilts top toward +Y and bottom toward -Y, matching display plane 100%!
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, sy + 0.010, sz))
    bez = bpy.context.active_object
    bez.name = "Interior_Screen_Center17in_Bezel"
    bez.scale = (sc_w + 0.016, 0.014, sc_h + 0.016)
    bez.rotation_euler = (-stilt, 0.0, 0.0)
    link_object(bez, col)
    bez.data.materials.append(mats["trim_satin_black"])
    add_bevel(bez, width=0.003, segments=2)

    dy = (sc_h * 0.5) * math.sin(stilt)
    dz = (sc_h * 0.5) * math.cos(stilt)
    _create_uv_plane(
        "Interior_Screen_Center17in_Display",
        [
            (-sc_w * 0.5, sy - dy, sz - dz),
            ( sc_w * 0.5, sy - dy, sz - dz),
            ( sc_w * 0.5, sy + dy, sz + dz),
            (-sc_w * 0.5, sy + dy, sz + dz),
        ],
        col, mats["screen_center"]
    )

    # 5. Sweeping Center Console (Y = -0.42..+0.55, X = ±0.165)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.04, 0.455))
    cons = bpy.context.active_object
    cons.name = "Interior_CenterConsole_Body"
    cons.scale = (0.315, 0.94, 0.34)
    link_object(cons, col)
    cons.data.materials.append(mats["int_leather"])
    add_bevel(cons, width=0.022, segments=3)

    # Dual Angled Alcantara Wireless Phone Charger Pad directly under 17" screen
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.375, 0.592))
    chg = bpy.context.active_object
    chg.name = "Interior_WirelessCharger_Alcantara"
    chg.scale = (0.255, 0.175, 0.018)
    chg.rotation_euler = (math.radians(-38.0), 0.0, 0.0)
    link_object(chg, col)
    chg.data.materials.append(mats["int_alcantara"])
    add_bevel(chg, width=0.006, segments=2)

    # Matte 2x2 Twill Carbon Fiber Center Console Sliding Storage Lid (middle bay, raised proud to catch highlights!)
    g_lid = np.zeros((10, 10, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, 10)):
        y = -0.02 + v * 0.30
        z = 0.634 + 0.014 * (v ** 1.2)
        for i, u in enumerate(np.linspace(-1.0, 1.0, 10)):
            crown = 0.005 * (1.0 - u * u)
            g_lid[j, i] = (u * 0.132, y, z + crown)
    create_grid_surface(
        "Interior_Console_CarbonLid", g_lid, col, material=mats["carbon_int"],
        flip_normals=True, uv_scale=(1.4, 2.0)
    )

    # Organically Contoured Padded Vegan Leather Center Armrest (smoothly crowned cushion, NOT a sharp box!)
    nu_a, nv_a = 16, 18
    g_arm = np.zeros((nv_a, nu_a, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv_a)):
        y = -0.39 + v * 0.37
        end_drop = -0.026 * ((2.0 * v - 1.0) ** 4.0)
        for i, u in enumerate(np.linspace(-1.0, 1.0, nu_a)):
            x = u * 0.144
            side_drop = -0.032 * (u ** 4.0)
            z = 0.676 + end_drop + side_drop
            g_arm[j, i] = (x, y, z)
    create_grid_surface(
        "Interior_Console_Armrest", g_arm, col, material=mats["int_leather"],
        flip_normals=True, add_flange=True, flange_depth=0.028, flange_bevel=0.008
    )

    # 9.4" Rear Passenger Touchscreen (facing rearward at Y = -0.435, Z = 0.545)
    rw, rh = 0.215, 0.122
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.430, 0.545))
    rbez = bpy.context.active_object
    rbez.name = "Interior_Screen_Rear9in_Bezel"
    rbez.scale = (rw + 0.014, 0.014, rh + 0.014)
    rbez.rotation_euler = (math.radians(-12.0), 0.0, 0.0)
    link_object(rbez, col)
    rbez.data.materials.append(mats["trim_satin_black"])

    _create_uv_plane(
        "Interior_Screen_Rear9in_Display",
        [
            (-rw * 0.5, -0.440, 0.545 - rh * 0.5),
            ( rw * 0.5, -0.440, 0.545 - rh * 0.5),
            ( rw * 0.5, -0.436, 0.545 + rh * 0.5),
            (-rw * 0.5, -0.436, 0.545 + rh * 0.5),
        ],
        col, mats["screen_rear"]
    )


def build_steering_yoke(col, mats):
    """
    Build the iconic Tesla Model S Plaid Steering Yoke (flat-top sculpted U/trapezoid rim,
    satin-silver accent spokes, dual knurled aluminum scroll wheels, center airbag horn pad w/ T).
    """
    cx, cy, cz = -0.370, 0.285, 0.778
    tilt = math.radians(22.0)

    def yoke_to_world(lx, ly, lz):
        wy = cy + ly * math.cos(tilt) - lz * math.sin(tilt)
        wz = cz + ly * math.sin(tilt) + lz * math.cos(tilt)
        return (cx + lx, wy, wz)

    local_rim = [
        (-0.158, 0.0,  0.072),
        (-0.175, 0.0,  0.048),
        (-0.184, 0.0,  0.005),
        (-0.182, 0.0, -0.052),
        (-0.165, 0.0, -0.095),
        (-0.115, 0.0, -0.106),
        ( 0.000, 0.0, -0.108),
        ( 0.115, 0.0, -0.106),
        ( 0.165, 0.0, -0.095),
        ( 0.182, 0.0, -0.052),
        ( 0.184, 0.0,  0.005),
        ( 0.175, 0.0,  0.048),
        ( 0.158, 0.0,  0.072),
    ]
    rim_pts = [yoke_to_world(*p) for p in local_rim]
    create_tube_along_points(
        "Interior_Yoke_Rim", rim_pts, (0.0185, 0.0165), col,
        material=mats["int_leather"], segments=18, cap_ends=True
    )

    for sign, tag in [(-1.0, "L"), (1.0, "R")]:
        sp_pts = [yoke_to_world(sign * x, 0.004, -0.012) for x in [0.052, 0.115, 0.174]]
        create_tube_along_points(
            f"Interior_Yoke_Spoke_{tag}", sp_pts, (0.022, 0.012), col,
            material=mats["trim_gloss_black"], segments=12
        )
        sx, sy, sz = yoke_to_world(sign * 0.118, -0.012, -0.010)
        bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.0085, depth=0.011, location=(sx, sy, sz))
        sw = bpy.context.active_object
        sw.name = f"Interior_Yoke_ScrollWheel_{tag}"
        sw.rotation_euler = (0.0, math.radians(90), 0.0)
        link_object(sw, col)
        sw.data.materials.append(mats["int_satin_silver"])

    for sign, tag in [(-1.0, "L"), (1.0, "R")]:
        st_pts = [yoke_to_world(sign * 0.032, 0.002, -0.045), yoke_to_world(sign * 0.045, 0.002, -0.104)]
        create_tube_along_points(
            f"Interior_Yoke_SilverStrut_{tag}", st_pts, (0.010, 0.008), col,
            material=mats["int_satin_silver"], segments=10
        )

    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.068, depth=0.042, location=(cx, cy + 0.015, cz - 0.006))
    hub = bpy.context.active_object
    hub.name = "Interior_Yoke_AirbagHub"
    hub.scale = (1.18, 1.0, 0.88)
    hub.rotation_euler = (math.radians(90) + tilt, 0.0, 0.0)
    link_object(hub, col)
    hub.data.materials.append(mats["int_leather"])
    add_bevel(hub, width=0.008, segments=2)

    tx, ty, tz = yoke_to_world(0.0, -0.010, -0.005)
    fcurve = bpy.data.curves.new(name="Interior_Yoke_T_Curve", type="FONT")
    fcurve.body = "T"
    fcurve.align_x = "CENTER"
    fcurve.align_y = "CENTER"
    fcurve.size = 0.038
    fcurve.extrude = 0.0018
    fcurve.bevel_depth = 0.0004
    tobj = bpy.data.objects.new("Interior_Yoke_TeslaT", fcurve)
    link_object(tobj, col)
    tobj.location = (tx, ty, tz)
    tobj.rotation_euler = (math.radians(90) + tilt, 0.0, 0.0)
    tobj.data.materials.append(mats["int_satin_silver"])

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.046, depth=0.22, location=(cx, cy + 0.135, cz + 0.042))
    col_shroud = bpy.context.active_object
    col_shroud.name = "Interior_SteeringColumn"
    col_shroud.rotation_euler = (math.radians(90) + tilt, 0.0, 0.0)
    link_object(col_shroud, col)
    col_shroud.data.materials.append(mats["trim_satin_black"])


def _build_plaid_sport_seat(name_prefix, x_center, y_hip, z_base, col, mats):
    """
    Build one organically contoured 2024 Model S Plaid Sport Seat matching interior_tesla-model-s-sport-seats.jpeg:
      - Deeply bucketed perforated vegan leather seat pan + smoothly tapered Alcantara thigh bolsters
      - Track-sculpted backrest with organically tapered wrap-around Alcantara lateral wings (zero flat tube caps!)
      - Integrated tapered headrest + flush recessed metallic Plaid chest emblem
    """
    # 1. Contoured Seat Pan Cushion (perforated vegan leather + subtle horizontal stitched pleats)
    nu, nv = 20, 18
    g_pan = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv)):
        y = y_hip + v * 0.49
        z_slope = z_base + 0.042 * v + 0.024 * math.sin(v * math.pi)
        pleat = 0.004 * abs(math.sin(v * 4.0 * math.pi))
        for i, u in enumerate(np.linspace(-1.0, 1.0, nu)):
            x = x_center + u * 0.245
            # Deep sculpted side thigh bolsters smoothly integrated into cushion edges!
            bolster_up = 0.056 * (abs(u) ** 2.6) * math.sin(v * math.pi) ** 0.55
            center_dip = -0.015 * (1.0 - u * u)
            g_pan[j, i] = (x, y, z_slope + center_dip + bolster_up + pleat)
    create_grid_surface(
        f"{name_prefix}_Cushion_Perf", g_pan, col, material=mats["int_leather_perf"],
        flip_normals=True, add_flange=True, flange_depth=0.055, flange_bevel=0.012
    )

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_center, y_hip + 0.22, z_base - 0.042))
    plinth = bpy.context.active_object
    plinth.name = f"{name_prefix}_Plinth"
    plinth.scale = (0.48, 0.48, 0.11)
    link_object(plinth, col)
    plinth.data.materials.append(mats["int_leather"])
    add_bevel(plinth, width=0.025, segments=3)

    # Smoothly tapered charcoal Alcantara outer thigh wing pads (radius tapers smoothly to 0.012 at ends -> zero sausage caps!)
    for s_side, stag in [(-1.0, "L"), (1.0, "R")]:
        pts_tb = []
        rads_tb = []
        for k, v in enumerate(np.linspace(0.05, 0.94, 9)):
            env = math.sin(v * math.pi) ** 0.55
            pts_tb.append((
                x_center + s_side * (0.215 + 0.028 * env),
                y_hip + v * 0.48,
                z_base + 0.040 + 0.046 * env + 0.025 * v,
            ))
            rads_tb.append((0.016 + 0.036 * env, 0.016 + 0.038 * env))
        create_tube_along_points(
            f"{name_prefix}_ThighBolster_{stag}", pts_tb, rads_tb, col,
            material=mats["int_alcantara"], segments=16
        )

    # 2. Sculpted Sport Backrest + Integrated Tapered Headrest (reclined ~21 deg!)
    recline = math.radians(21.0)
    ny_b, nu_b = 28, 22
    g_back_front = np.zeros((ny_b, nu_b, 3), dtype=np.float64)
    g_back_shell = np.zeros((ny_b, nu_b, 3), dtype=np.float64)

    for j, v in enumerate(np.linspace(0.0, 1.0, ny_b)):
        h = v * 0.805
        if v < 0.62:
            hw = 0.252 + 0.025 * math.sin((v / 0.62) * math.pi)
        elif v < 0.78:
            t_sh = (v - 0.62) / 0.16
            hw = 0.252 + (0.118 - 0.252) * (t_sh ** 1.1)
        else:
            t_hd = (v - 0.78) / 0.22
            hw = 0.118 * (1.0 - 0.30 * (t_hd ** 1.5))

        yc = y_hip - h * math.sin(recline)
        zc = z_base + 0.035 + h * math.cos(recline)
        yc += 0.034 * max(0.0, (v - 0.68) / 0.32) ** 1.5

        for i, u in enumerate(np.linspace(-1.0, 1.0, nu_b)):
            x = x_center + u * hw
            bolster_env = math.sin(min(v / 0.72, 1.0) * math.pi) ** 0.78
            # Deep ergonomic track lateral wrap built directly into the continuous backrest!
            wrap_fwd = 0.095 * (abs(u) ** 2.2) * bolster_env
            lumbar = 0.022 * math.exp(-((v - 0.25) / 0.18) ** 2) * (1.0 - u * u)
            pleat = 0.0035 * abs(math.sin(v * 6.0 * math.pi)) * (1.0 - abs(u)) * (1.0 if v < 0.60 else 0.0)
            y_front = yc + wrap_fwd + lumbar + pleat
            y_rear = yc - 0.075 * (1.0 - 0.45 * (u * u)) * (1.0 - 0.25 * v)
            g_back_front[j, i] = (x, y_front, zc)
            g_back_shell[j, i] = (x, y_rear, zc)

    create_grid_surface(
        f"{name_prefix}_Backrest_Front", g_back_front, col, material=mats["int_leather_perf"],
        flip_normals=True, add_flange=True, flange_depth=0.045, flange_bevel=0.012
    )
    create_grid_surface(f"{name_prefix}_Backrest_Shell", g_back_shell, col, material=mats["int_leather"], flip_normals=False)

    # Organically Tapered Charcoal Alcantara Torso Bolster Pads (blending smoothly into shoulder & waist -> ZERO flat ends!)
    for s_side, stag in [(-1.0, "L"), (1.0, "R")]:
        pts_sb = []
        rads_sb = []
        for v in np.linspace(0.06, 0.68, 12):
            tv = (v - 0.06) / (0.68 - 0.06)
            env = math.sin(tv * math.pi) ** 0.65
            h = v * 0.805
            hw = 0.242 + 0.024 * math.sin(min(v / 0.62, 1.0) * math.pi)
            yc = y_hip - h * math.sin(recline) + 0.082 * (math.sin(min(v / 0.72, 1.0) * math.pi) ** 0.78)
            zc = z_base + 0.035 + h * math.cos(recline)
            pts_sb.append((x_center + s_side * (hw - 0.018), yc, zc))
            rads_sb.append((0.010 + 0.030 * env, 0.010 + 0.036 * env))
        create_tube_along_points(
            f"{name_prefix}_TorsoBolster_{stag}", pts_sb, rads_sb, col,
            material=mats["int_alcantara"], segments=16
        )

    # Flush Sleek Recessed 2024 Sport Seat Metallic Plaid Chest Emblem (v ~ 0.64, sits flush with backrest!)
    h_em = 0.635 * 0.805
    ye = y_hip - h_em * math.sin(recline) + 0.002
    ze = z_base + 0.035 + h_em * math.cos(recline)
    ew, eh = 0.108, 0.025
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_center, ye - 0.003, ze))
    ebez = bpy.context.active_object
    ebez.name = f"{name_prefix}_PlaidEmblem_Bezel"
    ebez.scale = (ew + 0.014, 0.010, eh + 0.008)
    ebez.rotation_euler = (-recline, 0.0, 0.0)
    link_object(ebez, col)
    ebez.data.materials.append(mats["trim_gloss_black"])

    eh_y = (eh * 0.5) * math.sin(recline)
    eh_z = (eh * 0.5) * math.cos(recline)
    _create_uv_plane(
        f"{name_prefix}_PlaidEmblem_Insert",
        [
            (x_center + ew * 0.5, ye + 0.004 + eh_y, ze - eh_z),
            (x_center - ew * 0.5, ye + 0.004 + eh_y, ze - eh_z),
            (x_center - ew * 0.5, ye + 0.004 - eh_y, ze + eh_z),
            (x_center + ew * 0.5, ye + 0.004 - eh_y, ze + eh_z),
        ],
        col, mats["plaid_badge"]
    )


def build_rear_bench_and_door_cards(col, mats):
    """Build contoured Rear 60/40 Bench (3 headrests + armrest), Inner Door Cards, and Pedals."""
    # 1. Rear Bench Seat Cushion (Y = -1.24..-0.76, X = ±0.68, Z = 0.44)
    g_rb = np.zeros((10, 22, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, 10)):
        y = -1.24 + v * 0.48
        z_s = 0.435 + 0.042 * v + 0.025 * math.sin(v * math.pi)
        for i, u in enumerate(np.linspace(-1.0, 1.0, 22)):
            x = u * 0.68
            # Two comfortable sculpted outer buckets + slightly raised center position
            dip = -0.022 * (math.exp(-((abs(x) - 0.42) / 0.19) ** 2))
            g_rb[j, i] = (x, y, z_s + dip)
    create_grid_surface("Interior_RearBench_Cushion", g_rb, col, material=mats["int_leather_perf"])

    # Rear Bench Backrest (reclined cleanly under rear hatch)
    g_rback = np.zeros((12, 22, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, 12)):
        y = -1.22 - v * 0.24
        z = 0.45 + v * 0.52
        for i, u in enumerate(np.linspace(-1.0, 1.0, 22)):
            x = u * 0.68
            bolster = 0.032 * (math.exp(-((abs(x) - 0.62) / 0.11) ** 2)) * math.sin(v * math.pi)
            g_rback[j, i] = (x, y + bolster, z)
    create_grid_surface("Interior_RearBench_Backrest", g_rback, col, material=mats["int_leather"], flip_normals=True)

    # 3 Rear Headrests
    for idx, hx in enumerate([-0.42, 0.0, 0.42]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, -1.42, 1.02 if idx != 1 else 0.99))
        hr = bpy.context.active_object
        hr.name = f"Interior_RearHeadrest_{idx}"
        hr.scale = (0.21 if idx != 1 else 0.18, 0.095, 0.17 if idx != 1 else 0.13)
        hr.rotation_euler = (math.radians(-20), 0.0, 0.0)
        link_object(hr, col)
        hr.data.materials.append(mats["int_leather"])
        add_bevel(hr, width=0.026, segments=3)

    # 2. Inner Door Cards (L/R via MirrorX) with Carbon Fiber Inlay Strip & Armrest
    ny_d, nz_d = 24, 10
    g_dc = np.zeros((ny_d, nz_d, 3), dtype=np.float64)
    for i, y in enumerate(np.linspace(-1.05, 0.84, ny_d)):
        xb, zb = BodyCurves.beltline(y)
        for j, v in enumerate(np.linspace(0.0, 1.0, nz_d)):
            z = zb - 0.02 - v * (zb - 0.30)
            # Sculpted armrest bulge around v ~ 0.45
            arm_in = 0.068 * math.exp(-((v - 0.46) / 0.16) ** 2)
            x = xb - 0.075 - arm_in
            g_dc[i, j] = (x, y, z)
    create_grid_surface("Interior_DoorCards", g_dc, col, material=mats["int_leather"], mirror_x=True, flip_normals=False)

    # Carbon Fiber accent band wrapping smoothly across both front & rear inner door cards
    g_dcf = np.zeros((18, 5, 3), dtype=np.float64)
    for i, y in enumerate(np.linspace(-0.98, 0.78, 18)):
        xb, zb = BodyCurves.beltline(y)
        for j, v in enumerate(np.linspace(0.0, 1.0, 5)):
            z = zb - 0.08 - v * 0.065
            g_dcf[i, j] = (xb - 0.088, y, z)
    create_grid_surface(
        "Interior_DoorCards_CarbonTrim", g_dcf, col, material=mats["carbon_int"],
        mirror_x=True, flip_normals=False, uv_scale=(4.0, 0.4)
    )

    # 3. Aluminum Performance Pedals in Driver Footwell (Left side: X ~ -0.45..-0.22, Y ~ 0.78, Z ~ 0.36)
    pedals = [
        ("Accelerator", -0.24, 0.79, 0.35, (0.048, 0.012, 0.135)),
        ("Brake",       -0.37, 0.76, 0.38, (0.095, 0.014, 0.068)),
        ("DeadPedal",   -0.58, 0.78, 0.36, (0.068, 0.012, 0.165)),
    ]
    for pname, px, py, pz, pscale in pedals:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, pz))
        p = bpy.context.active_object
        p.name = f"Interior_Pedal_{pname}"
        p.scale = pscale
        p.rotation_euler = (math.radians(-26.0), 0.0, 0.0)
        link_object(p, col)
        p.data.materials.append(mats["int_satin_silver"])
        add_bevel(p, width=0.003, segments=2)


def build_all_interior(root_col, mats):
    col = ensure_collection("06_Interior_Cabin", root_col)
    build_cabin_shell_and_headliner(col, mats)
    build_dashboard_and_screens(col, mats)
    build_steering_yoke(col, mats)
    # Front 2024 Plaid Sport Seats (Driver Left X=-0.385, Passenger Right X=+0.385)
    _build_plaid_sport_seat("Interior_SportSeat_Driver", -0.385, -0.34, 0.415, col, mats)
    _build_plaid_sport_seat("Interior_SportSeat_Passenger", 0.385, -0.34, 0.415, col, mats)
    build_rear_bench_and_door_cards(col, mats)
    return col
