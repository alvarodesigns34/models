"""
Precision Exterior Details for the 2024 Tesla Model S Plaid:
  - Sculpted Aerodynamic Side Mirrors (sail, curved arm, satin-black lower shell,
    Ultra Red upper cap, auto-dimming mirror glass)
  - 4x Flush Satin-Black Retractable Door Handles w/ shadow recess bezel
  - Front Fender HW4 Side Repeater Camera Pods w/ red-tinted lens
  - Sculpted 3D Front Chrome Tesla 'T' Emblem
  - Rear Gloss-Black Tailgate Garnish Bar + Individually Modeled 3D 'T E S L A' Letters
  - Rear Metallic Geometric Plaid Warp Emblem
  - Matte 2x2 Twill Carbon Fiber Rear Decklid Lip Spoiler
  - Dual Concealed Windshield Wipers + Rearview Backup Camera
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import config as C
from .body_master import BodyCurves, eval_front_garnish_upper
from .geometry_utils import (
    ensure_collection,
    create_grid_surface,
    create_tube_along_points,
    add_bevel,
    set_smooth_shading,
    link_object,
)


def build_side_mirrors(col, mats):
    """
    Build sculpted aerodynamic 2024 Model S Plaid side mirrors (reaching exact 2,189 mm tip-to-tip!):
    Crisp flat-bottomed wing profile with beveled shoulder crease matching 1X7A0025 & 2024_Blue.
    """
    for sign, tag in [(1.0, "R"), (-1.0, "L")]:
        # 1. Triangular satin-black door-shoulder mounting sail
        bm = bmesh.new()
        sail_pts = [
            (0.848, 0.855, 0.904),
            (0.866, 0.675, 0.910),
            (0.822, 0.695, 1.002),
            (0.848, 0.845, 0.936),
        ]
        v_out = [bm.verts.new((sign * (p[0] + 0.011), p[1], p[2])) for p in sail_pts]
        v_in = [bm.verts.new((sign * (p[0] - 0.012), p[1], p[2])) for p in sail_pts]
        bm.faces.new(v_out)
        bm.faces.new(list(reversed(v_in)))
        for k in range(4):
            kn = (k + 1) % 4
            bm.faces.new((v_out[k], v_out[kn], v_in[kn], v_in[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ms = bpy.data.meshes.new(f"Mirror_Sail_{tag}")
        bm.to_mesh(ms)
        bm.free()
        set_smooth_shading(ms)
        sail = bpy.data.objects.new(f"Mirror_Sail_{tag}", ms)
        link_object(sail, col)
        sail.data.materials.append(mats["trim_satin_black"])

        # 2. Muscular sculpted aerodynamic mirror stalk neck extending cleanly into lower shell
        arm_pts = [
            (sign * 0.858, 0.742, 0.920),
            (sign * 0.905, 0.720, 0.934),
            (sign * 0.955, 0.702, 0.946),
        ]
        create_tube_along_points(
            f"Mirror_Arm_{tag}", arm_pts, (0.026, 0.013), col,
            material=mats["trim_satin_black"], segments=12
        )

        # 3. Sculpted Flat-Bottomed Angular Model S Mirror Housing (X = 0.892 .. 1.0945 m!)
        nu, nv = 26, 18
        us = np.linspace(0.0, 1.0, nu)
        vs = np.linspace(0.0, 1.0, nv)

        g_top = np.zeros((nv, nu, 3), dtype=np.float64)
        g_bot = np.zeros((nv, nu, 3), dtype=np.float64)
        for i, u in enumerate(us):
            x_span = 0.892 + u * (C.WIDTH_MIRRORS * 0.5 - 0.892)
            y_rear = 0.658 - 0.048 * (u ** 1.15)
            # Wider sculpted trapezoidal wing silhouette (fuller inner-mid crown, crisp outer tip!)
            env_top = (math.sin(u * math.pi) ** 0.42) * (1.0 - 0.24 * (u ** 1.8))
            env_bot = (math.sin(u * math.pi) ** 0.38) * (1.0 - 0.12 * u)
            depth = 0.136 * (0.14 + 0.86 * (math.sin(u * math.pi) ** 0.45))
            h_up = 0.074 * env_top
            h_dn = 0.032 * env_bot
            # Slight sporty upward sweep along flat lower crease line
            z_mid = 0.972 + 0.014 * u

            for j, v in enumerate(vs):
                ang = v * (math.pi * 0.5)
                y = y_rear + depth * (math.sin(ang) ** 0.88)
                # Slightly flatter squared-off crown + crisp horizontal lower satin-black chin
                z_top = z_mid + h_up * (math.cos(ang) ** 0.82)
                z_bot = z_mid - h_dn * (math.cos(ang) ** 0.72)
                g_top[j, i] = (sign * x_span, y, z_top)
                g_bot[j, i] = (sign * x_span, y, z_bot)

        create_grid_surface(
            f"Mirror_UpperCap_{tag}", g_top, col, material=mats["paint"],
            flip_normals=(sign > 0)
        )
        create_grid_surface(
            f"Mirror_LowerShell_{tag}", g_bot, col, material=mats["trim_satin_black"],
            flip_normals=(sign < 0)
        )

        # 4. Watertight Rear Bezel Backing + Auto-Dimming Mirror Glass Pane
        g_back = np.zeros((10, nu, 3), dtype=np.float64)
        g_gl = np.zeros((8, 16, 3), dtype=np.float64)
        for i, u in enumerate(us):
            x_span = 0.892 + u * (C.WIDTH_MIRRORS * 0.5 - 0.892)
            y_rear = 0.658 - 0.048 * (u ** 1.15)
            h_up = 0.074 * (math.sin(u * math.pi) ** 0.42) * (1.0 - 0.24 * (u ** 1.8))
            h_dn = 0.032 * (math.sin(u * math.pi) ** 0.38) * (1.0 - 0.12 * u)
            z_mid = 0.972 + 0.014 * u
            for j, v in enumerate(np.linspace(0.0, 1.0, 10)):
                z = (z_mid - h_dn) + v * (h_up + h_dn)
                g_back[j, i] = (sign * x_span, y_rear + 0.004, z)
        create_grid_surface(
            f"Mirror_RearBezel_{tag}", g_back, col, material=mats["trim_satin_black"],
            flip_normals=(sign < 0)
        )

        for i, u in enumerate(np.linspace(0.08, 0.92, 16)):
            x_span = 0.892 + u * (C.WIDTH_MIRRORS * 0.5 - 0.892)
            y_rear = 0.657 - 0.048 * (u ** 1.15)
            h_up = 0.062 * (math.sin(u * math.pi) ** 0.42) * (1.0 - 0.24 * (u ** 1.8))
            h_dn = 0.025 * (math.sin(u * math.pi) ** 0.38) * (1.0 - 0.12 * u)
            z_mid = 0.972 + 0.014 * u
            for j, v in enumerate(np.linspace(0.0, 1.0, 8)):
                z = (z_mid - h_dn) + v * (h_up + h_dn)
                g_gl[j, i] = (sign * x_span, y_rear, z)
        create_grid_surface(
            f"Mirror_Glass_{tag}", g_gl, col, material=mats["glass_mirror"],
            flip_normals=(sign < 0)
        )


def build_micro_body_seams(col, mats):
    """Build OEM front bumper circular tow-eye cover seam ring (matching 1X7A0025.jpg)."""
    # Located on driver-left side of front bumper (X = -0.365, Z = 0.415, diameter ~52 mm)
    pts = []
    cx, cz, rad = -0.365, 0.415, 0.025
    bumper = bpy.data.objects["Body_Front_Bumper"]
    bpy.context.view_layer.update()
    surface = BVHTree.FromObject(bumper, bpy.context.evaluated_depsgraph_get())
    for k in range(25):
        ang = 2.0 * math.pi * k / 24.0
        px = cx + rad * math.cos(ang)
        pz = cz + rad * math.sin(ang)
        point, normal, _, _ = surface.ray_cast((px, 3.0, pz), (0.0, -1.0, 0.0))
        if point is None:
            raise ValueError("Tow-eye cover lies outside the front bumper")
        pts.append(point + normal * 0.0003)
    create_tube_along_points(
        "Detail_FrontBumper_TowEyeSeam", pts, 0.0014, col,
        material=mats["shadow_gap"], segments=6, cap_ends=False
    )


def build_flush_door_handles(col, mats):
    """Build 4 flush satin-black chrome-delete Model S retractable door handles."""
    handle_specs = [
        ("Front", 0.04, 0.795),
        ("Rear", -0.82, 0.848),
    ]
    for label, yc, zc in handle_specs:
        # Handle is ~172 mm long x 29 mm tall, curved smoothly onto exact door surface
        nu, nv = 12, 5
        g_h = np.zeros((nv, nu, 3), dtype=np.float64)
        g_bez = np.zeros((nv, nu, 3), dtype=np.float64)
        for j, v in enumerate(np.linspace(-0.5, 0.5, nv)):
            z = zc + v * 0.028
            for i, u in enumerate(np.linspace(-0.5, 0.5, nu)):
                y = yc + u * 0.170
                x = BodyCurves.eval_flank_x_at_yz(y, z)
                # Flush with 1.5 mm crisp metallic standout + dark surround bezel
                g_h[j, i] = (x + 0.0022, y, z)
                g_bez[j, i] = (x + 0.0008, yc + u * 0.178, zc + v * 0.034)

        h_obj = create_grid_surface(
            f"Trim_DoorHandle_{label}", g_h, col, material=mats["trim_satin_black"],
            mirror_x=True, flip_normals=True, add_flange=True, flange_depth=0.006, flange_bevel=0.001
        )
        create_grid_surface(
            f"Trim_DoorHandle_Bezel_{label}", g_bez, col, material=mats["shadow_gap"],
            mirror_x=True, flip_normals=True
        )


def build_side_repeater_cameras(col, mats):
    """Build iconic front-fender triangular satin-black HW4 side repeater camera pods (L/R)."""
    # Positioned on front fender behind wheel arch, just forward of front door seam (Y ~ 0.96..1.16, Z ~ 0.73)
    for sign, tag in [(1.0, "R"), (-1.0, "L")]:
        bm = bmesh.new()
        y_f, y_r = 1.155, 0.965
        z_t, z_b = 0.748, 0.708
        x_base = BodyCurves.eval_flank_x_at_yz(1.06, 0.73)

        # Sleek sculpted aerodynamic triangular wedge protruding ~18 mm at rear camera end
        p_out = [
            (sign * (x_base + 0.004), y_f, z_t - 0.008),       # Sharp forward nose tip
            (sign * (x_base + 0.017), y_r + 0.012, z_t),       # Upper rear corner
            (sign * (x_base + 0.020), y_r, z_b + 0.014),       # Rear camera face
            (sign * (x_base + 0.014), y_r + 0.035, z_b),       # Lower angled edge
        ]
        p_in = [
            (sign * (x_base - 0.008), y_f, z_t - 0.008),
            (sign * (x_base - 0.008), y_r + 0.012, z_t),
            (sign * (x_base - 0.008), y_r, z_b + 0.014),
            (sign * (x_base - 0.008), y_r + 0.035, z_b),
        ]
        vo = [bm.verts.new(p) for p in p_out]
        vi = [bm.verts.new(p) for p in p_in]
        bm.faces.new(vo)
        bm.faces.new(list(reversed(vi)))
        for k in range(4):
            kn = (k + 1) % 4
            bm.faces.new((vo[k], vo[kn], vi[kn], vi[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        m = bpy.data.meshes.new(f"Sensor_SideRepeater_{tag}")
        bm.to_mesh(m)
        bm.free()
        set_smooth_shading(m)
        pod = bpy.data.objects.new(f"Sensor_SideRepeater_{tag}", m)
        link_object(pod, col)
        pod.data.materials.append(mats["trim_satin_black"])
        add_bevel(pod, width=0.002, segments=2)

        # Rear-facing HW4 camera dome lens inside pod
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16, ring_count=10, radius=0.0075,
            location=(sign * (x_base + 0.013), y_r + 0.004, z_b + 0.018)
        )
        cl = bpy.context.active_object
        cl.name = f"Sensor_SideRepeater_Lens_{tag}"
        link_object(cl, col)
        cl.data.materials.append(mats["camera_lens"])


def build_front_t_emblem(col, mats):
    """Build true sculpted 3D chrome Tesla 'T' emblem nested in the Iter 3 front mustache V-notch."""
    bm = bmesh.new()
    _, y0, z0 = eval_front_garnish_upper(0.0)
    y0 += 0.006
    z0 -= 0.023
    thick = 0.0038

    # 1. Upper curved Tesla crest bar (sweeping gently down at ends)
    n_arc = 14
    bar_front, bar_back = [], []
    for i in range(n_arc):
        t = (i / (n_arc - 1)) * 2.0 - 1.0  # -1..+1
        x = t * 0.044
        z_hi = z0 + 0.016 - 0.007 * (t * t)
        z_lo = z_hi - (0.0045 - 0.0018 * (t * t))
        y_c = y0 - 0.004 * (t * t)
        bar_front.append((bm.verts.new((x, y_c + thick, z_hi)), bm.verts.new((x, y_c + thick, z_lo))))
        bar_back.append((bm.verts.new((x, y_c, z_hi)), bm.verts.new((x, y_c, z_lo))))
    for i in range(n_arc - 1):
        f0h, f0l = bar_front[i]
        f1h, f1l = bar_front[i + 1]
        b0h, b0l = bar_back[i]
        b1h, b1l = bar_back[i + 1]
        bm.faces.new((f0h, f1h, f1l, f0l))
        bm.faces.new((b0l, b1l, b1h, b0h))
        bm.faces.new((b0h, b1h, f1h, f0h))
        bm.faces.new((f0l, f1l, b1l, b0l))

    # 2. Iconic tapered Tesla lower 'T' stem with upper gull-wing shoulders and V-notch
    stem_xz = [
        (0.0, z0 - 0.045),        # Sharp bottom tip
        (0.011, z0 + 0.001),      # Right mid-stem
        (0.036, z0 + 0.004),      # Right wing tip
        (0.040, z0 + 0.009),      # Right wing upper corner
        (0.012, z0 + 0.010),      # Right V-notch shoulder
        (0.0, z0 + 0.0055),       # Center top V-notch
        (-0.012, z0 + 0.010),     # Left V-notch shoulder
        (-0.040, z0 + 0.009),     # Left wing upper corner
        (-0.036, z0 + 0.004),     # Left wing tip
        (-0.011, z0 + 0.001),     # Left mid-stem
    ]
    vf = [bm.verts.new((px, y0 + thick - 0.003 * (px / 0.04) ** 2, pz)) for px, pz in stem_xz]
    vb = [bm.verts.new((px, y0 - 0.003 * (px / 0.04) ** 2, pz)) for px, pz in stem_xz]
    bm.faces.new(vf)
    bm.faces.new(list(reversed(vb)))
    n_p = len(stem_xz)
    for k in range(n_p):
        kn = (k + 1) % n_p
        bm.faces.new((vf[k], vb[k], vb[kn], vf[kn]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("Emblem_Front_Tesla_T")
    bm.to_mesh(mesh)
    bm.free()
    set_smooth_shading(mesh)
    obj = bpy.data.objects.new("Emblem_Front_Tesla_T", mesh)
    link_object(obj, col)
    obj.data.materials.append(mats["chrome"])
    add_bevel(obj, width=0.0008, segments=2)


def _eval_tailgate_y(x, z):
    """Exact outer painted Y-surface of Iter 3 Body_Rear_Tailgate at (x, z) outside recesses."""
    tv = max(0.0, min(1.0, (0.978 - z) / (0.978 - 0.570)))
    xw = 0.646 - 0.012 * (tv ** 1.3)
    u = min(1.0, abs(x) / xw)
    y_curve = 0.084 * (u ** 2.05)
    return -2.475 - 0.058 * (tv ** 0.85) - 0.008 * math.sin(tv * math.pi) + y_curve


def build_rear_garnish_letters_and_plaid_badge(col, mats):
    """
    Build the authentic 2022-2024 Model S Plaid Rear Tailgate Details:
      - Gloss-black horizontal applique bar cleanly terminating at inner taillight edge (X = ±0.502)
      - Raised individually spaced 3D 'T E S L A' lettering in bright dark-satin chrome
      - Crisp bevelled metallic geometric Plaid warp badge flush on lower-right tailgate
      - Rearview backup camera pod tucked under the black bar
    """
    # 1. Gloss-Black Horizontal Tailgate Garnish Bar (X = ±0.502, Z = 0.826..0.876)
    nu, nv = 24, 6
    bg = np.zeros((nv, nu, 3), dtype=np.float64)
    for j, v in enumerate(np.linspace(0.0, 1.0, nv)):
        z = 0.826 + v * (0.876 - 0.826)
        for i, u in enumerate(np.linspace(0.0, 1.0, nu)):
            x = u * 0.502
            y = _eval_tailgate_y(x, z) - 0.003 - 0.005 * math.sin(v * math.pi)
            bg[j, i] = (x, y, z)
    create_grid_surface(
        "Trim_Rear_GarnishBar", bg, col, material=mats["trim_gloss_black"],
        mirror_x=True, flip_normals=False, add_flange=True, flange_depth=0.015, flange_bevel=0.002
    )

    # 2. Spaced 3D 'T E S L A' Wordmark Letters (crisp beveled 3D mesh flush on garnish bar!)
    letters = [("T", -0.232), ("E", -0.116), ("S", 0.0), ("L", 0.116), ("A", 0.232)]
    for ch, lx in letters:
        fcurve = bpy.data.curves.new(name=f"Letter_Rear_{ch}", type="FONT")
        fcurve.body = ch
        fcurve.align_x = "CENTER"
        fcurve.align_y = "CENTER"
        fcurve.size = 0.029
        fcurve.extrude = 0.0028
        fcurve.bevel_depth = 0.0006
        fcurve.bevel_resolution = 2
        fobj = bpy.data.objects.new(f"Emblem_Rear_TESLA_{ch}", fcurve)
        link_object(fobj, col)
        ly = _eval_tailgate_y(lx, 0.851) - 0.0095
        fobj.location = (lx, ly, 0.851)
        fobj.rotation_euler = (math.radians(90), 0.0, 0.0)
        fobj.data.materials.append(mats["dark_satin_chrome"])

    # 3. Rear Metallic Geometric Plaid Warp Badge (Lower-Right Tailgate: X = +0.445, Z = 0.684!)
    # Matches ts_plaid_badge.jpg & IMG_9321 (72 mm wide x 34 mm tall x 4.0 mm proud bevelled plaque)
    bw, bh, bd = 0.072, 0.034, 0.0040
    bx, bz = 0.445, 0.684
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    x0, x1 = bx - bw * 0.5, bx + bw * 0.5
    z0, z1 = bz - bh * 0.5, bz + bh * 0.5
    # Exact outer painted tailgate surface at all 4 badge corners -> 100% flush, ZERO burial!
    y00 = _eval_tailgate_y(x0, z0)
    y10 = _eval_tailgate_y(x1, z0)
    y11 = _eval_tailgate_y(x1, z1)
    y01 = _eval_tailgate_y(x0, z1)
    vf = [
        bm.verts.new((x0, y00 - bd, z0)),
        bm.verts.new((x1, y10 - bd, z0)),
        bm.verts.new((x1, y11 - bd, z1)),
        bm.verts.new((x0, y01 - bd, z1)),
    ]
    vb = [
        bm.verts.new((x0, y00 + 0.004, z0)),
        bm.verts.new((x1, y10 + 0.004, z0)),
        bm.verts.new((x1, y11 + 0.004, z1)),
        bm.verts.new((x0, y01 + 0.004, z1)),
    ]
    f_front = bm.faces.new((vf[0], vf[3], vf[2], vf[1]))
    uv_coords = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    for loop, uv in zip(f_front.loops, uv_coords):
        loop[uv_layer].uv = uv
    bm.faces.new((vb[0], vb[1], vb[2], vb[3]))
    for k in range(4):
        kn = (k + 1) % 4
        bm.faces.new((vf[k], vf[kn], vb[kn], vb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    pm = bpy.data.meshes.new("Emblem_Rear_Plaid_Badge")
    bm.to_mesh(pm)
    bm.free()
    pobj = bpy.data.objects.new("Emblem_Rear_Plaid_Badge", pm)
    link_object(pobj, col)
    pobj.data.materials.append(mats["plaid_badge"])

    # 4. Rearview Backup Camera tucked under center of black garnish bar
    bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.009, depth=0.016, location=(0.0, -2.502, 0.818))
    rcam = bpy.context.active_object
    rcam.name = "Sensor_Rear_BackupCamera"
    rcam.rotation_euler = (math.radians(65), 0.0, 0.0)
    link_object(rcam, col)
    rcam.data.materials.append(mats["camera_lens"])


def build_carbon_rear_spoiler(col, mats):
    """
    Build the standard Model S Plaid Matte 2x2 Twill Carbon Fiber Rear Decklid Lip Spoiler!
    Follows exact Iter 3 rear decklid trailing curve (X = ±0.642, Y = -2.478 + 0.084*u^2.05).
    """
    nu = 38
    us = np.linspace(0.0, 1.0, nu)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    rings = []

    for i, u in enumerate(us):
        x = u * 0.642
        y_trail = -2.478 + 0.084 * (u ** 2.05)
        z_base = 0.980 - 0.020 * (u ** 1.9)
        taper = 1.0 - 0.68 * (u ** 3.2)
        chord = 0.098 * (0.45 + 0.55 * taper)
        lift = 0.026 * taper

        pts = [
            (x, y_trail + chord, z_base + 0.004),
            (x, y_trail + chord * 0.52, z_base + 0.012 * taper + 0.004),
            (x, y_trail + 0.008, z_base + lift + 0.006),
            (x, y_trail - 0.004, z_base + lift),
            (x, y_trail + 0.014, z_base + lift * 0.35 - 0.003),
            (x, y_trail + chord * 0.72, z_base - 0.002),
        ]
        rings.append([bm.verts.new(p) for p in pts])

    for i in range(nu - 1):
        r0, r1 = rings[i], rings[i + 1]
        u0, u1 = i / (nu - 1), (i + 1) / (nu - 1)
        for k in range(6):
            kn = (k + 1) % 6
            f = bm.faces.new((r0[k], r1[k], r1[kn], r0[kn]))
            v0, v1 = k / 6.0, (k + 1) / 6.0
            for loop, uv in zip(f.loops, [(u0 * 4.0, v0), (u1 * 4.0, v0), (u1 * 4.0, v1), (u0 * 4.0, v1)]):
                loop[uv_layer].uv = uv
    bm.faces.new(rings[-1])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sm = bpy.data.meshes.new("Aero_CarbonFiber_RearSpoiler")
    bm.to_mesh(sm)
    bm.free()
    set_smooth_shading(sm)
    sobj = bpy.data.objects.new("Aero_CarbonFiber_RearSpoiler", sm)
    link_object(sobj, col)
    sobj.data.materials.append(mats["carbon_ext"])
    mod = sobj.modifiers.new("MirrorX", "MIRROR")
    mod.use_axis = (True, False, False)
    mod.use_clip = True
    add_bevel(sobj, width=0.0018, segments=2)


def build_windshield_wipers(col, mats):
    """Build concealed dual matte-black windshield wipers nestled neatly in the cowl recess."""
    # Driver wiper (left) + passenger wiper (right)
    wipers = [
        ("Driver", [(-0.08, 0.962, 0.880), (-0.36, 0.942, 0.888), (-0.66, 0.910, 0.896)]),
        ("Passenger", [(0.56, 0.922, 0.892), (0.28, 0.948, 0.885), (-0.02, 0.960, 0.878)]),
    ]
    for label, pts in wipers:
        create_tube_along_points(
            f"Detail_Wiper_{label}", pts, (0.008, 0.006), col,
            material=mats["trim_satin_black"], segments=8
        )


def build_all_exterior_details(root_col, mats):
    col = ensure_collection("05_Exterior_Details", root_col)
    build_side_mirrors(col, mats)
    build_flush_door_handles(col, mats)
    build_side_repeater_cameras(col, mats)
    build_front_t_emblem(col, mats)
    build_rear_garnish_letters_and_plaid_badge(col, mats)
    build_carbon_rear_spoiler(col, mats)
    build_windshield_wipers(col, mats)
    build_micro_body_seams(col, mats)
    return col
