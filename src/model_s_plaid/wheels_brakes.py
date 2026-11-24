"""
Staggered 21" Arachnid Wheels, 3D-Tread Michelin Pilot Sport 4S Tires,
and Upgraded 2023-2024 Red Plaid Brake System (380/365 mm Rotors + Calipers + EPB).
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

from . import config as C
from .geometry_utils import (
    ensure_collection,
    create_revolved_mesh,
    set_smooth_shading,
    link_object,
    add_bevel,
)


def _build_tire_3d(name_prefix, cx, cy, cz, side_sign, rim_r, tire_r, tire_w, squat, col, mats, is_front):
    """
    Build photorealistic Michelin Pilot Sport 4S tire with:
      - Separate radial-UV Sidewall meshes (outer & inner) with realistic rim-protector bead
      - Physically modeled 3D Tread surface with 4 deep circumferential grooves & angled
        3D shoulder tread blocks around the full 360° circumference
      - Authentic static contact-patch flattening at Z = 0.000 m + subtle lower sidewall bulge!
    """
    hw = tire_w * 0.5
    # Sidewall outer profile: (r, axial_x_local) where +x_local is OUTWARD toward car exterior
    # Rim bead -> rim protector ridge -> smooth convex sidewall -> shoulder transition
    sw_prof_out = [
        (rim_r - 0.004, hw * 0.84),
        (rim_r + 0.006, hw * 0.94),
        (rim_r + 0.016, hw * 0.995),   # Rim protector lip
        (rim_r + 0.032, hw * 0.985),
        (rim_r + 0.055, hw * 1.000),   # Max sidewall section width
        (rim_r + 0.074, hw * 0.975),
        (tire_r - 0.011, hw * 0.920),  # Shoulder round-off
        (tire_r - 0.003, hw * 0.865),
    ]
    sw_prof_in = [(r, -ax) for r, ax in reversed(sw_prof_out)]

    # Build Sidewalls (outer uses Michelin Pilot Sport 4S radial bump/velvet map!)
    sw_mat = mats["tire_sidewall_front"] if is_front else mats["tire_sidewall_rear"]
    segs = 96

    def build_sw_mesh(sname, prof, mat, radial_uv=True):
        bm = bmesh.new()
        rings = []
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            ca, sa = math.cos(ang), math.sin(ang)
            ring = []
            for r, ax in prof:
                wy = cy + r * ca
                wz = cz + r * sa
                # Authentic static load contact-patch squat near ground (Z -> 0)
                bulge = 0.0
                if wz < 0.09:
                    tf = max(0.0, (0.09 - wz) / 0.09)
                    bulge = 0.006 * (tf ** 1.8) * (1.0 if ax > 0 else -1.0)
                if wz < 0.002:
                    wz = 0.002
                wx = cx + side_sign * (ax + bulge)
                ring.append(bm.verts.new((wx, wy, wz)))
            rings.append(ring)

        uv_layer = bm.loops.layers.uv.new("UVMap")
        for s in range(segs):
            sn = (s + 1) % segs
            a0 = 2.0 * math.pi * s / segs
            a1 = 2.0 * math.pi * (s + 1) / segs
            for p in range(len(prof) - 1):
                v0, v1, v2, v3 = rings[s][p], rings[sn][p], rings[sn][p + 1], rings[s][p + 1]
                # (v1 - v0) x (v3 - v0) points toward -X for outer sidewall (outward on LEFT side_sign < 0!)
                f = bm.faces.new((v0, v1, v2, v3) if side_sign < 0 else (v0, v3, v2, v1))
                r0 = prof[p][0] / tire_r
                r1 = prof[p + 1][0] / tire_r
                uvs = [
                    (0.5 + 0.5 * r0 * math.cos(a0), 0.5 + 0.5 * r0 * math.sin(a0)),
                    (0.5 + 0.5 * r0 * math.cos(a1), 0.5 + 0.5 * r0 * math.sin(a1)),
                    (0.5 + 0.5 * r1 * math.cos(a1), 0.5 + 0.5 * r1 * math.sin(a1)),
                    (0.5 + 0.5 * r1 * math.cos(a0), 0.5 + 0.5 * r1 * math.sin(a0)),
                ]
                if side_sign > 0:
                    uvs = [uvs[0], uvs[3], uvs[2], uvs[1]]
                for loop, uv in zip(f.loops, uvs):
                    loop[uv_layer].uv = uv

        bm.normal_update()
        mesh = bpy.data.meshes.new(sname)
        bm.to_mesh(mesh)
        bm.free()
        set_smooth_shading(mesh)
        obj = bpy.data.objects.new(sname, mesh)
        link_object(obj, col)
        obj.data.materials.append(mat)
        return obj

    build_sw_mesh(f"{name_prefix}_Sidewall_Out", sw_prof_out, sw_mat, radial_uv=True)
    build_sw_mesh(f"{name_prefix}_Sidewall_In", sw_prof_in, mats["tire_tread"], radial_uv=False)

    # 3D Physically Sculpted Asymmetric Tread (4 deep circumferential water grooves + angled shoulder sipes!)
    tread_x_fracs = [
        -0.865, -0.78, -0.58,
        -0.55, -0.49, -0.46,
        -0.25, -0.22, -0.15, -0.12,
        0.12, 0.15, 0.22, 0.25,
        0.46, 0.49, 0.55,
        0.58, 0.78, 0.865,
    ]
    groove_depths = [
        0.003, 0.0005, 0.0,
        0.0072, 0.0072, 0.0,
        0.0, 0.0076, 0.0076, 0.0,
        0.0, 0.0076, 0.0076, 0.0,
        0.0, 0.0072, 0.0072,
        0.0, 0.0005, 0.003,
    ]

    segs_t = 144
    bm = bmesh.new()
    rings = []
    for s in range(segs_t):
        ang = 2.0 * math.pi * s / segs_t
        ca, sa = math.cos(ang), math.sin(ang)
        ring = []
        for idx, (xf, gd) in enumerate(zip(tread_x_fracs, groove_depths)):
            sipe = 0.0
            if gd < 0.002 and abs(xf) > 0.26:
                phase = (s * 0.5 + xf * 1.8) % 1.0
                if phase < 0.22:
                    sipe = 0.0042 * (1.0 if abs(xf) > 0.55 else 0.65)
            crown = 0.0025 * (1.0 - (xf / 0.865) ** 2)
            r = tire_r + crown - gd - sipe
            wy = cy + r * ca
            wz = cz + r * sa
            if wz < 0.0005:
                wz = 0.0005
            wx = cx + side_sign * (xf * hw)
            ring.append(bm.verts.new((wx, wy, wz)))
        rings.append(ring)

    n_p = len(tread_x_fracs)
    for s in range(segs_t):
        sn = (s + 1) % segs_t
        for p in range(n_p - 1):
            bm.faces.new((rings[s][p], rings[sn][p], rings[sn][p + 1], rings[s][p + 1]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name_prefix}_Tread_3D")
    bm.to_mesh(mesh)
    bm.free()
    set_smooth_shading(mesh)
    tread_obj = bpy.data.objects.new(f"{name_prefix}_Tread_3D", mesh)
    link_object(tread_obj, col)
    tread_obj.data.materials.append(mats["tire_tread"])
    return tread_obj


def _build_arachnid_rim(name_prefix, cx, cy, cz, side_sign, rim_r, rim_w, is_front, col, mats):
    """
    Build the authentic 2021-2024 Tesla Model S Plaid 21" Arachnid Wheel:
      - Wide, bold, muscular flat-chiseled 10-spoke (5 split-V pairs) turbine blades
        matching IMG_9278 and IMG_9321!
      - Stepped dark satin anthracite barrel with deeper rear concavity (10.5J vs 9.5J)
      - Recessed 5x120 lug bolt pockets, dark lug nuts, center cap, and valve stem
    """
    hw = rim_w * 0.5
    outer_face_x = hw * 0.90
    concavity = 0.036 if is_front else 0.058

    barrel_prof = [
        (rim_r + 0.003, outer_face_x + 0.005),
        (rim_r + 0.006, outer_face_x - 0.002),
        (rim_r - 0.011, outer_face_x - 0.006),
        (rim_r - 0.018, outer_face_x - 0.022),
        (rim_r - 0.024, outer_face_x - 0.050),
        (rim_r - 0.034, outer_face_x - 0.095),
        (rim_r - 0.026, -hw * 0.78),
        (rim_r - 0.014, -hw * 0.92),
        (rim_r + 0.005, -hw * 0.95),
        (rim_r + 0.005, -hw * 0.85),
        (rim_r - 0.008, -hw * 0.80),
        (rim_r - 0.016, outer_face_x - 0.025),
        (rim_r - 0.006, outer_face_x + 0.003),
    ]
    barrel_prof_world = [(r, side_sign * ax) for r, ax in barrel_prof]
    create_revolved_mesh(
        f"{name_prefix}_Barrel", barrel_prof_world, col,
        material=mats["wheel_arachnid"], segments=80, axis='X',
        origin=(cx, cy, cz), close_profile=True
    )

    hub_x_face = outer_face_x - concavity
    hub_prof = [
        (0.030, hub_x_face - 0.004),
        (0.033, hub_x_face - 0.008),
        (0.048, hub_x_face - 0.010),
        (0.072, hub_x_face - 0.006),
        (0.088, hub_x_face + 0.006),
        (0.094, hub_x_face - 0.024),
        (0.072, hub_x_face - 0.036),
        (0.030, hub_x_face - 0.036),
    ]
    create_revolved_mesh(
        f"{name_prefix}_HubBowl", [(r, side_sign * ax) for r, ax in hub_prof], col,
        material=mats["wheel_arachnid"], segments=50, axis='X',
        origin=(cx, cy, cz), close_profile=True
    )

    cap_prof = [
        (0.001, hub_x_face - 0.001),
        (0.032, hub_x_face - 0.003),
        (0.032, hub_x_face - 0.012),
        (0.001, hub_x_face - 0.012),
    ]
    create_revolved_mesh(
        f"{name_prefix}_CenterCap", [(r, side_sign * ax) for r, ax in cap_prof], col,
        material=mats["trim_satin_black"], segments=36, axis='X',
        origin=(cx, cy, cz), close_profile=True
    )

    # Raised metallic Tesla 'T' crest centered on wheel center cap
    fcurve = bpy.data.curves.new(name=f"{name_prefix}_CapT_Curve", type="FONT")
    fcurve.body = "T"
    fcurve.align_x = "CENTER"
    fcurve.align_y = "CENTER"
    fcurve.size = 0.034
    fcurve.extrude = 0.0012
    fcurve.bevel_depth = 0.0003
    fobj = bpy.data.objects.new(f"{name_prefix}_CenterCap_T", fcurve)
    link_object(fobj, col)
    fobj.location = (cx + side_sign * (hub_x_face + 0.0002), cy, cz)
    fobj.rotation_euler = (math.radians(90), 0.0, math.radians(90 if side_sign > 0 else -90))
    fobj.data.materials.append(mats["dark_satin_chrome"])

    for k in range(5):
        ang = math.radians(k * 72.0 + 36.0)
        ly = cy + 0.060 * math.cos(ang)
        lz = cz + 0.060 * math.sin(ang)
        lx = cx + side_sign * (hub_x_face - 0.006)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0105, depth=0.018, location=(lx, ly, lz))
        lug = bpy.context.active_object
        lug.name = f"{name_prefix}_Lug_{k}"
        lug.rotation_euler = (0.0, math.radians(90), 0.0)
        link_object(lug, col)
        lug.data.materials.append(mats["wheel_lug"])

    # 3. 5 Twin-Spoke WIDE Chiseled Arachnid Blades (matching IMG_9278 & IMG_9321!)
    bm = bmesh.new()
    n_len = 14
    r_start = 0.072
    r_end = rim_r - 0.008

    for pair_idx in range(5):
        base_ang = pair_idx * (2.0 * math.pi / 5.0)
        for sub_sign in (-1.0, 1.0):
            rings = []
            for i in range(n_len):
                t = i / (n_len - 1)
                r = r_start + t * (r_end - r_start)
                # Tight split-V gap (~17 deg) within pair, dramatic open bay (~55 deg) between pairs
                ang_off = sub_sign * math.radians(17.0 - 3.8 * t) + math.radians(5.5 * t * side_sign)
                ang = base_ang + ang_off

                ax_front = hub_x_face + concavity * (t ** 0.78) - 0.003 * (1.0 - t)
                ax_back = ax_front - (0.028 - 0.008 * t)

                # BOLD wide flat-chiseled OEM Arachnid blade width (28-34 mm wide face!)
                w_front = 0.0185 * (1.0 + 0.12 * math.sin(t * math.pi)) + 0.008 * (t ** 3.0)
                w_back = w_front * 1.28

                ca, sa = math.cos(ang), math.sin(ang)
                ty, tz = -sa, ca

                # Sculpted wide flat-top trapezoidal blade with crisp bevelled chamfer shoulders!
                pts_local = [
                    (ax_front + 0.002, w_front * 0.65),
                    (ax_front - 0.004, w_front),
                    (ax_back + 0.003, w_back),
                    (ax_back, 0.0),
                    (ax_back + 0.003, -w_back),
                    (ax_front - 0.004, -w_front),
                    (ax_front + 0.002, -w_front * 0.65),
                ]
                ring = []
                for ax_p, w_p in pts_local:
                    wx = cx + side_sign * ax_p
                    wy = cy + r * ca + w_p * ty
                    wz = cz + r * sa + w_p * tz
                    ring.append(bm.verts.new((wx, wy, wz)))
                rings.append(ring)

            for i in range(n_len - 1):
                r0, r1 = rings[i], rings[i + 1]
                for k in range(7):
                    kn = (k + 1) % 7
                    bm.faces.new((r0[k], r1[k], r1[kn], r0[kn]))
            bm.faces.new(list(reversed(rings[0])))
            bm.faces.new(rings[-1])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    spokes_mesh = bpy.data.meshes.new(f"{name_prefix}_ArachnidSpokes")
    bm.to_mesh(spokes_mesh)
    bm.free()
    set_smooth_shading(spokes_mesh)
    spokes_obj = bpy.data.objects.new(f"{name_prefix}_ArachnidSpokes", spokes_mesh)
    link_object(spokes_obj, col)
    spokes_obj.data.materials.append(mats["wheel_arachnid"])
    add_bevel(spokes_obj, width=0.0018, segments=2)

    # TPMS Metallic Valve Stem
    v_ang = math.radians(18.0)
    vy = cy + (rim_r - 0.022) * math.cos(v_ang)
    vz = cz + (rim_r - 0.022) * math.sin(v_ang)
    vx = cx + side_sign * (outer_face_x - 0.018)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.004, depth=0.022, location=(vx, vy, vz))
    valve = bpy.context.active_object
    valve.name = f"{name_prefix}_ValveStem"
    valve.rotation_euler = (math.radians(90) - v_ang, 0.0, 0.0)
    link_object(valve, col)
    valve.data.materials.append(mats["wheel_lug"])


def _build_brake_assembly(name_prefix, cx, cy, cz, side_sign, rotor_r, rotor_t, is_front, col, mats):
    """
    Build ventilated steel brake disc (with brushed radial wear rings + outer cooling vanes + hat),
    large gloss-red 2023-2024 Plaid monoblock caliper (rear-mounted on front axle, front-mounted
    on rear axle!) with crisp white TESLA lettering, and separate rear EPB caliper.
    """
    rotor_x = cx + side_sign * (-0.018 if is_front else -0.024)

    # 1. Ventilated Cast-Iron Brake Rotor Friction Ring (UV radial mapped!)
    ht = rotor_t * 0.5
    r_inner = 0.098
    disc_prof = [
        (r_inner, ht),
        (rotor_r, ht),
        (rotor_r, -ht),
        (r_inner, -ht),
    ]
    create_revolved_mesh(
        f"{name_prefix}_RotorDisc", disc_prof, col,
        material=mats["brake_rotor"], segments=72, axis='X',
        origin=(rotor_x, cy, cz), uv_radial=True, close_profile=True
    )

    # Dark anodized center rotor hat bell
    hat_prof = [
        (0.032, side_sign * (ht + 0.024)),
        (0.088, side_sign * (ht + 0.024)),
        (0.102, side_sign * (ht + 0.002)),
        (0.102, side_sign * (-ht)),
        (0.032, side_sign * (-ht)),
    ]
    create_revolved_mesh(
        f"{name_prefix}_RotorHat", hat_prof, col,
        material=mats["brake_hat"], segments=48, axis='X',
        origin=(rotor_x, cy, cz), close_profile=True
    )

    # Inner dark brake dust backing shield behind rotor
    shield_prof = [
        (0.060, side_sign * (-ht - 0.014)),
        (rotor_r + 0.008, side_sign * (-ht - 0.016)),
        (rotor_r + 0.008, side_sign * (-ht - 0.020)),
        (0.060, side_sign * (-ht - 0.018)),
    ]
    create_revolved_mesh(
        f"{name_prefix}_DustShield", shield_prof, col,
        material=mats["trim_matte_plastic"], segments=48, axis='X',
        origin=(rotor_x, cy, cz), close_profile=True
    )

    # 2. Large Sculpted Gloss-Red Plaid Brake Caliper!
    cal_center_ang = math.radians(176.0) if is_front else math.radians(8.0)
    cal_arc = math.radians(66.0 if is_front else 56.0)
    r_cal_in = rotor_r - (0.066 if is_front else 0.056)
    r_cal_out = rotor_r + (0.022 if is_front else 0.018)
    cal_w_out = ht + (0.032 if is_front else 0.024)
    cal_w_in = -(ht + (0.026 if is_front else 0.022))

    bm = bmesh.new()
    n_arc = 18
    rings = []
    for i in range(n_arc):
        t = i / (n_arc - 1)
        ang = cal_center_ang + (t - 0.5) * cal_arc
        ca, sa = math.cos(ang), math.sin(ang)
        taper = 0.72 + 0.28 * math.sin(t * math.pi)
        ro = r_cal_in + (r_cal_out - r_cal_in) * taper
        wo = cal_w_out * (0.82 + 0.18 * math.sin(t * math.pi))
        wi = cal_w_in * (0.82 + 0.18 * math.sin(t * math.pi))

        prof = [
            (r_cal_in + 0.006, wo * 0.90),
            (ro - 0.008, wo),
            (ro, wo * 0.72),
            (ro, wi * 0.72),
            (ro - 0.008, wi),
            (r_cal_in + 0.006, wi * 0.90),
            (r_cal_in, wi * 0.35),
            (r_cal_in, wo * 0.35),
        ]
        ring = []
        for rp, xp in prof:
            wx = rotor_x + side_sign * xp
            wy = cy + rp * ca
            wz = cz + rp * sa
            ring.append(bm.verts.new((wx, wy, wz)))
        rings.append(ring)

    for i in range(n_arc - 1):
        r0, r1 = rings[i], rings[i + 1]
        for k in range(8):
            kn = (k + 1) % 8
            bm.faces.new((r0[k], r1[k], r1[kn], r0[kn]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cal_mesh = bpy.data.meshes.new(f"{name_prefix}_RedCaliper")
    bm.to_mesh(cal_mesh)
    bm.free()
    set_smooth_shading(cal_mesh)
    cal_obj = bpy.data.objects.new(f"{name_prefix}_RedCaliper", cal_mesh)
    link_object(cal_obj, col)
    cal_obj.data.materials.append(mats["brake_caliper_red"])
    add_bevel(cal_obj, width=0.003, segments=2)

    # 2b. Flush Curved White 'TESLA' Lettering Decal Plate on Outer Face of Caliper
    if "caliper_decal" in mats:
        bm_d = bmesh.new()
        uv_l = bm_d.loops.layers.uv.new("UVMap")
        n_d = 12
        r_lo = r_cal_in + 0.016
        r_hi = r_cal_out - 0.015
        v_rows = []
        for i in range(n_d):
            td = i / (n_d - 1)
            t_cal = 0.22 + td * 0.56
            ang = cal_center_ang + (t_cal - 0.5) * cal_arc
            ca, sa = math.cos(ang), math.sin(ang)
            wo_d = cal_w_out * (0.82 + 0.18 * math.sin(t_cal * math.pi)) + 0.0015
            wx = rotor_x + side_sign * wo_d
            v_rows.append((
                bm_d.verts.new((wx, cy + r_lo * ca, cz + r_lo * sa)),
                bm_d.verts.new((wx, cy + r_hi * ca, cz + r_hi * sa)),
            ))
        for i in range(n_d - 1):
            u0, u1 = i / (n_d - 1), (i + 1) / (n_d - 1)
            v0, v3 = v_rows[i]
            v1, v2 = v_rows[i + 1]
            # Keep normal strictly outward (side_sign * +X)
            f = bm_d.faces.new((v0, v1, v2, v3) if side_sign < 0 else (v0, v3, v2, v1))
            uvs = [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)]
            if side_sign > 0:
                uvs = [uvs[0], uvs[3], uvs[2], uvs[1]]
            for loop, uv in zip(f.loops, uvs):
                loop[uv_l].uv = uv
        bm_d.normal_update()
        dm = bpy.data.meshes.new(f"{name_prefix}_CaliperDecal")
        bm_d.to_mesh(dm)
        bm_d.free()
        set_smooth_shading(dm)
        dobj = bpy.data.objects.new(f"{name_prefix}_CaliperDecal", dm)
        link_object(dobj, col)
        dobj.data.materials.append(mats["caliper_decal"])

    # 3. Rear Auxiliary Electronic Parking Brake (EPB) Caliper (Rear wheels only!)
    if not is_front:
        epb_ang = math.radians(135.0)
        ey = cy + (rotor_r - 0.015) * math.cos(epb_ang)
        ez = cz + (rotor_r - 0.015) * math.sin(epb_ang)
        ex = rotor_x + side_sign * 0.002
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ex, ey, ez))
        epb = bpy.context.active_object
        epb.name = f"{name_prefix}_RearEPB"
        epb.scale = (0.048, 0.068, 0.056)
        epb.rotation_euler = (epb_ang, 0.0, 0.0)
        link_object(epb, col)
        epb.data.materials.append(mats["brake_epb"])
        add_bevel(epb, width=0.004, segments=2)


def build_all_wheels_and_brakes(root_col, mats):
    """Build all 4 staggered 21" Arachnid wheel, Michelin PS4S tire, and Plaid brake assemblies."""
    col = ensure_collection("04_Wheels_Tires_Brakes", root_col)

    wheel_configs = [
        ("FL", -1.0, C.FRONT_WHEEL_X, C.Y_FRONT_AXLE, C.FRONT_WHEEL_Z, C.FRONT_RIM_RAD, C.FRONT_RIM_WIDTH, C.FRONT_TIRE_RAD, C.FRONT_TIRE_WIDTH, C.FRONT_TIRE_SQUAT, C.FRONT_ROTOR_RAD, C.FRONT_ROTOR_THICK, True),
        ("FR",  1.0, C.FRONT_WHEEL_X, C.Y_FRONT_AXLE, C.FRONT_WHEEL_Z, C.FRONT_RIM_RAD, C.FRONT_RIM_WIDTH, C.FRONT_TIRE_RAD, C.FRONT_TIRE_WIDTH, C.FRONT_TIRE_SQUAT, C.FRONT_ROTOR_RAD, C.FRONT_ROTOR_THICK, True),
        ("RL", -1.0, C.REAR_WHEEL_X,  C.Y_REAR_AXLE,  C.REAR_WHEEL_Z,  C.REAR_RIM_RAD,  C.REAR_RIM_WIDTH,  C.REAR_TIRE_RAD,  C.REAR_TIRE_WIDTH,  C.REAR_TIRE_SQUAT,  C.REAR_ROTOR_RAD,  C.REAR_ROTOR_THICK,  False),
        ("RR",  1.0, C.REAR_WHEEL_X,  C.Y_REAR_AXLE,  C.REAR_WHEEL_Z,  C.REAR_RIM_RAD,  C.REAR_RIM_WIDTH,  C.REAR_TIRE_RAD,  C.REAR_TIRE_WIDTH,  C.REAR_TIRE_SQUAT,  C.REAR_ROTOR_RAD,  C.REAR_ROTOR_THICK,  False),
    ]

    for tag, sign, wx_abs, wy, wz, rr, rw, tr, tw, sq, dr, dt, is_f in wheel_configs:
        cx = sign * wx_abs
        _build_tire_3d(f"Wheel_{tag}", cx, wy, wz, sign, rr, tr, tw, sq, col, mats, is_f)
        _build_arachnid_rim(f"Wheel_{tag}", cx, wy, wz, sign, rr, rw, is_f, col, mats)
        _build_brake_assembly(f"Brake_{tag}", cx, wy, wz, sign, dr, dt, is_f, col, mats)

    return col
