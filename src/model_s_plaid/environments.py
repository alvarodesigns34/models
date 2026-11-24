"""
Physically Based Photographic Lighting Environments & Camera Rig for the
2024 Tesla Model S Plaid (Ultra Red PR01):
  1. studio   : Automotive press cyclorama sweep + overhead ribbon softbox + side highlight strips
  2. daylight : Physically based Nishita atmospheric sun/sky + textured asphalt road & curb
  3. overcast : Diffused overcast sky dome + damp asphalt courtyard (surface truth test!)
  4. night    : Urban twilight dusk + streetlamp rim light + boosted active headlights/taillights
  5. zebra    : High-contrast Zebra-Stripe curvature continuity diagnostic studio
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector

from .geometry_utils import ensure_collection, create_grid_surface, link_object, set_smooth_shading


def _clear_environment_collection():
    if "07_Environment_Lights" in bpy.data.collections:
        col = bpy.data.collections["07_Environment_Lights"]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = ensure_collection("07_Environment_Lights")
    return col


def _set_light_strengths(drl=10.0, proj=4.5, fog=2.5, tail=8.5, screens=1.4):
    """Adjust vehicle lighting emission intensities smoothly for daylight vs studio vs night."""
    mapping = {
        "LED_DRL_White": drl,
        "LED_Matrix_Projector": proj,
        "LED_Fog_Strip": fog,
        "LED_Taillight_Crimson": tail,
        "Screen_Center_17in": screens,
        "Screen_Cluster_12in": screens * 0.9,
        "Screen_Rear_9in": screens * 0.8,
    }
    for mname, val in mapping.items():
        if mname in bpy.data.materials:
            mat = bpy.data.materials[mname]
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Emission Strength"].default_value = val


def _add_area_light(name, location, target, size_x, size_y, energy, color, col, spread_deg=110.0):
    ldata = bpy.data.lights.new(name=name, type="AREA")
    ldata.shape = "RECTANGLE"
    ldata.size = size_x
    ldata.size_y = size_y
    ldata.energy = energy
    ldata.color = color
    if hasattr(ldata, "spread"):
        ldata.spread = math.radians(spread_deg)
    lobj = bpy.data.objects.new(name=name, object_data=ldata)
    link_object(lobj, col)
    lobj.location = location
    direction = Vector(target) - Vector(location)
    lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return lobj


def _build_asphalt_road_ground(col, wet=False):
    """Procedural photorealistic dark asphalt road ground plane with subtle micro-aggregate & roughness variation."""
    bpy.ops.mesh.primitive_plane_add(size=120.0, location=(0.0, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "Env_Asphalt_Ground"
    link_object(ground, col)

    mat_name = "Env_Asphalt_Wet" if wet else "Env_Asphalt_Dry"
    if mat_name in bpy.data.materials:
        mat = bpy.data.materials[mat_name]
        mat.node_tree.nodes.clear()
    else:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        mat.node_tree.nodes.clear()

    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nodes.new("ShaderNodeTexCoord")
    # Macro variation (damp patches / tire wear tracks)
    n_macro = nodes.new("ShaderNodeTexNoise")
    n_macro.inputs["Scale"].default_value = 0.45
    n_macro.inputs["Detail"].default_value = 6.0
    n_macro.inputs["Roughness"].default_value = 0.65
    links.new(tc.outputs["Object"], n_macro.inputs["Vector"])

    # Fine asphalt aggregate stones
    n_fine = nodes.new("ShaderNodeTexNoise")
    n_fine.inputs["Scale"].default_value = 55.0
    n_fine.inputs["Detail"].default_value = 10.0
    n_fine.inputs["Roughness"].default_value = 0.72
    links.new(tc.outputs["Object"], n_fine.inputs["Vector"])

    # Color variation
    ramp_c = nodes.new("ShaderNodeValToRGB")
    ramp_c.color_ramp.elements[0].position = 0.25
    ramp_c.color_ramp.elements[0].color = (0.018, 0.019, 0.021, 1.0) if wet else (0.042, 0.044, 0.048, 1.0)
    ramp_c.color_ramp.elements[1].position = 0.78
    ramp_c.color_ramp.elements[1].color = (0.048, 0.050, 0.054, 1.0) if wet else (0.088, 0.090, 0.094, 1.0)
    links.new(n_fine.outputs["Fac"], ramp_c.inputs["Fac"])
    links.new(ramp_c.outputs["Color"], bsdf.inputs["Base Color"])

    # Roughness variation (damp courtyard shows gorgeous subtle car reflections!)
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.30
    mr.inputs["From Max"].default_value = 0.72
    mr.inputs["To Min"].default_value = 0.14 if wet else 0.56
    mr.inputs["To Max"].default_value = 0.52 if wet else 0.88
    links.new(n_macro.outputs["Fac"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22 if wet else 0.32
    bump.inputs["Distance"].default_value = 0.004
    links.new(n_fine.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Specular IOR Level"].default_value = 0.55 if wet else 0.40
    ground.data.materials.append(mat)
    return ground


def _build_studio_cyclorama(col):
    """Build infinite matte charcoal-slate automotive photography studio floor + smooth cyclorama bowl."""
    # Large smooth bowl rising smoothly at r > 12 m so every horizon line is seamless from any 360° camera!
    segs = 64
    r_steps = [0.0, 4.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 26.0]
    z_steps = [0.0, 0.0, 0.0, 0.05, 0.45, 1.45, 3.20, 6.00, 11.0]
    grid = np.zeros((len(r_steps), segs, 3), dtype=np.float64)
    for j, (r, z) in enumerate(zip(r_steps, z_steps)):
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            grid[j, i] = (r * math.cos(ang), r * math.sin(ang), z)
    cyc = create_grid_surface("Env_Studio_Cyclorama", grid, col, close_v=True, flip_normals=False)

    mat = bpy.data.materials.new("Env_Studio_Floor_Mat") if "Env_Studio_Floor_Mat" not in bpy.data.materials else bpy.data.materials["Env_Studio_Floor_Mat"]
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Clean matte-satin architectural dark charcoal studio concrete
    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 5.0
    links.new(tc.outputs["Object"], noise.inputs["Vector"])

    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.30
    mr.inputs["To Max"].default_value = 0.50
    links.new(noise.outputs["Fac"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    bsdf.inputs["Base Color"].default_value = (0.052, 0.055, 0.062, 1.0)
    bsdf.inputs["Specular IOR Level"].default_value = 0.42
    cyc.data.materials.append(mat)
    return cyc


def setup_environment(mode="studio"):
    """
    Configure world shader, physical studio/outdoor lights, ground geometry, and AgX exposure.
    mode in {'studio', 'daylight', 'overcast', 'night', 'zebra'}.
    """
    col = _clear_environment_collection()
    scene = bpy.context.scene

    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    world = scene.world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    w_out = wnodes.new("ShaderNodeOutputWorld")
    w_bg = wnodes.new("ShaderNodeBackground")
    wlinks.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

    if mode != "zebra" and "Tesla_Ultra_Red_PR01" in bpy.data.materials:
        paint = bpy.data.materials["Tesla_Ultra_Red_PR01"]
        for obj in bpy.data.objects:
            if obj.name.startswith("Body_") or obj.name.startswith("Mirror_UpperCap"):
                if len(obj.data.materials) > 0 and obj.data.materials[0].name == "Zebra_Diagnostic_Mat":
                    obj.data.materials[0] = paint

    if mode == "studio":
        _build_studio_cyclorama(col)
        w_bg.inputs["Color"].default_value = (0.032, 0.035, 0.042, 1.0)
        w_bg.inputs["Strength"].default_value = 0.65

        # Sculptural Press-Studio Lighting (designed for liquid deep Ultra Red with razor specular ribbons!)
        # 1. Elevated Narrow Overhead Ceiling Softbox Ribbon (carves sleek highlight along hood, roof & rear haunch
        #    without harsh rectangular clipping in the front windshield!)
        _add_area_light("Studio_Overhead_Main", (0.0, -0.35, 5.2), (0.0, -0.15, 0.7), 1.6, 6.2, 1280.0, (1.0, 0.99, 0.98), col, spread_deg=82)
        # 2. High-Angle Sculpting Side Strips (positioned ABOVE door shoulder to graze flanks, NEVER wash them pink!)
        _add_area_light("Studio_SideStrip_R", (4.8, 0.1, 2.85), (0.0, 0.0, 0.65), 6.8, 0.65, 520.0, (0.98, 0.99, 1.0), col, spread_deg=72)
        _add_area_light("Studio_SideStrip_L", (-4.8, 0.1, 2.85), (0.0, 0.0, 0.65), 6.8, 0.65, 480.0, (1.0, 0.98, 0.96), col, spread_deg=72)
        # 3. Low Subtle Wheel/Rocker Accent Rim Strips (gentle bounce illuminating Arachnid wheels & red calipers)
        _add_area_light("Studio_LowRim_L", (-5.5, 0.0, 0.62), (0.0, 0.0, 0.35), 5.6, 0.45, 175.0, (0.97, 0.98, 1.0), col, spread_deg=85)
        _add_area_light("Studio_LowRim_R", (5.5, 0.0, 0.62), (0.0, 0.0, 0.35), 5.6, 0.45, 155.0, (0.97, 0.98, 1.0), col, spread_deg=85)
        # 4. Front 3/4 Key & Rear 3/4 Rim Kicker
        _add_area_light("Studio_FrontFill", (-3.2, 6.2, 2.6), (0.0, 1.4, 0.6), 3.2, 1.4, 620.0, (1.0, 0.99, 0.97), col, spread_deg=75)
        _add_area_light("Studio_RearRim", (3.0, -6.2, 2.5), (0.0, -1.6, 0.7), 3.4, 1.4, 580.0, (0.96, 0.98, 1.0), col, spread_deg=75)
        # 5. Soft Cyclorama Wall Wash Lights (creates seamless luxury dark charcoal-grey studio horizon gradient!)
        _add_area_light("Studio_WallWash_Back", (0.0, -9.5, 5.5), (0.0, -24.0, 3.2), 14.0, 3.0, 3200.0, (0.94, 0.96, 1.0), col, spread_deg=110)
        _add_area_light("Studio_WallWash_Front", (0.0, 9.5, 5.5), (0.0, 24.0, 3.2), 14.0, 3.0, 3200.0, (0.94, 0.96, 1.0), col, spread_deg=110)
        _add_area_light("Studio_WallWash_Right", (9.5, 0.0, 5.5), (24.0, 0.0, 3.2), 14.0, 3.0, 3000.0, (0.94, 0.96, 1.0), col, spread_deg=110)
        # 6. Subtle Cabin Interior Soft Dome Fill so Sport Seats & Yoke read crisply through dark glass
        _add_area_light("Studio_CabinFill", (0.0, 0.1, 1.28), (0.0, -0.1, 0.6), 0.75, 0.95, 22.0, (0.98, 0.99, 1.0), col, spread_deg=120)

        _set_light_strengths(drl=14.0, proj=4.5, fog=2.5, tail=11.0, screens=2.0)
        scene.view_settings.exposure = -0.15

    elif mode == "daylight":
        _build_asphalt_road_ground(col, wet=False)
        sky = wnodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        sky.sun_disc = True
        sky.sun_size = math.radians(0.65)
        sky.sun_intensity = 1.0
        sky.sun_elevation = math.radians(24.0)
        sky.sun_rotation = math.radians(132.0)
        sky.altitude = 120.0
        sky.air_density = 1.15
        sky.dust_density = 1.10
        sky.ozone_density = 1.2
        wlinks.new(sky.outputs["Color"], w_bg.inputs["Color"])
        w_bg.inputs["Strength"].default_value = 0.22

        _set_light_strengths(drl=18.0, proj=2.0, fog=1.0, tail=12.0, screens=1.5)
        scene.view_settings.exposure = -1.75

    elif mode == "overcast":
        _build_asphalt_road_ground(col, wet=True)
        tc = wnodes.new("ShaderNodeTexCoord")
        sep = wnodes.new("ShaderNodeSeparateXYZ")
        wlinks.new(tc.outputs["Generated"], sep.inputs["Vector"])
        ramp = wnodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.14, 0.15, 0.17, 1.0)
        e1 = ramp.color_ramp.elements.new(0.08)
        e1.color = (0.42, 0.45, 0.50, 1.0)
        ramp.color_ramp.elements[2].position = 0.65
        ramp.color_ramp.elements[2].color = (0.85, 0.88, 0.92, 1.0)
        wlinks.new(sep.outputs["Z"], ramp.inputs["Fac"])
        wlinks.new(ramp.outputs["Color"], w_bg.inputs["Color"])
        w_bg.inputs["Strength"].default_value = 2.4

        _set_light_strengths(drl=16.0, proj=3.0, fog=2.0, tail=11.0, screens=1.6)
        scene.view_settings.exposure = -0.45

    elif mode == "night":
        _build_asphalt_road_ground(col, wet=True)
        tc = wnodes.new("ShaderNodeTexCoord")
        sep = wnodes.new("ShaderNodeSeparateXYZ")
        wlinks.new(tc.outputs["Generated"], sep.inputs["Vector"])
        ramp = wnodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.012, 0.016, 0.028, 1.0)
        e1 = ramp.color_ramp.elements.new(0.18)
        e1.color = (0.024, 0.036, 0.068, 1.0)
        ramp.color_ramp.elements[2].position = 0.70
        ramp.color_ramp.elements[2].color = (0.008, 0.012, 0.026, 1.0)
        wlinks.new(sep.outputs["Z"], ramp.inputs["Fac"])
        wlinks.new(ramp.outputs["Color"], w_bg.inputs["Color"])
        w_bg.inputs["Strength"].default_value = 0.9

        _add_area_light("Night_StreetLamp_Front", (4.5, 4.8, 5.2), (0.0, 0.5, 0.5), 1.8, 0.8, 1200.0, (1.0, 0.86, 0.68), col, spread_deg=85)
        _add_area_light("Night_StreetLamp_Rear", (-4.8, -5.0, 4.8), (0.0, -1.0, 0.6), 1.8, 0.8, 950.0, (0.72, 0.84, 1.0), col, spread_deg=85)
        for sign, tag in [(-1.0, "L"), (1.0, "R")]:
            sdata = bpy.data.lights.new(f"Night_HeadlightBeam_{tag}", type="SPOT")
            sdata.energy = 650.0
            sdata.color = (0.94, 0.97, 1.0)
            sdata.spot_size = math.radians(48.0)
            sdata.spot_blend = 0.45
            sobj = bpy.data.objects.new(f"Night_HeadlightBeam_{tag}", sdata)
            link_object(sobj, col)
            sobj.location = (sign * 0.68, 2.15, 0.66)
            sobj.rotation_euler = (math.radians(82.0), 0.0, sign * math.radians(-6.0))
        _add_area_light("Night_CabinGlow", (0.0, 0.25, 0.88), (0.0, -0.35, 0.72), 0.35, 0.20, 6.5, (0.68, 0.82, 1.0), col, spread_deg=110)

        _set_light_strengths(drl=28.0, proj=24.0, fog=12.0, tail=24.0, screens=3.0)
        scene.view_settings.exposure = 0.25

    elif mode == "zebra":
        _build_studio_cyclorama(col)
        w_bg.inputs["Color"].default_value = (0.18, 0.18, 0.18, 1.0)
        w_bg.inputs["Strength"].default_value = 1.0
        zebra_mat = bpy.data.materials.get("Zebra_Diagnostic_Mat")
        if zebra_mat:
            for obj in bpy.data.objects:
                if obj.name.startswith("Body_") or obj.name.startswith("Mirror_UpperCap"):
                    if len(obj.data.materials) > 0:
                        obj.data.materials[0] = zebra_mat
        scene.view_settings.exposure = 0.0


def configure_cycles_render(res_x=960, res_y=540, samples=40, use_agx=True):
    """Configure Blender 4.2 Cycles CPU + OpenImageDenoise + AgX Punchy color management."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.022 if samples <= 64 else 0.012
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 4
    scene.cycles.transparent_max_bounces = 6
    scene.cycles.sample_clamp_indirect = 8.0

    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    if use_agx:
        scene.view_settings.view_transform = "AgX"
        try:
            scene.view_settings.look = "AgX - Punchy"
        except Exception:
            try:
                scene.view_settings.look = "AgX - Medium High Contrast"
            except Exception:
                scene.view_settings.look = "None"
    scene.view_settings.gamma = 1.0


def set_camera(name, location, target, lens_mm=50.0, ortho=False, ortho_scale=6.0, fstop=4.0, dof=False):
    """Create or update a photographic camera aimed cleanly at target."""
    if name in bpy.data.objects:
        cam_obj = bpy.data.objects[name]
        cam_data = cam_obj.data
    else:
        cam_data = bpy.data.cameras.new(name)
        cam_obj = bpy.data.objects.new(name, cam_data)
        col = ensure_collection("08_Cameras")
        link_object(cam_obj, col)

    cam_obj.location = Vector(location)
    direction = Vector(target) - Vector(location)
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    cam_data.type = "ORTHO" if ortho else "PERSP"
    cam_data.lens = lens_mm
    cam_data.sensor_width = 36.0
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_start = 0.05
    cam_data.clip_end = 250.0
    cam_data.dof.use_dof = dof
    if dof:
        cam_data.dof.focus_distance = direction.length
        cam_data.dof.aperture_fstop = fstop

    bpy.context.scene.camera = cam_obj
    return cam_obj


# Standard Automotive Photographic Camera Presets (Full-Vehicle Commercial Framing!)
CAMERA_PRESETS = {
    "front_3q":      {"loc": (-5.10,  5.55, 1.38), "tgt": ( 0.0, -0.05, 0.64), "lens": 52.0},
    "front_3q_low":  {"loc": ( 4.65,  5.35, 0.92), "tgt": ( 0.0,  0.00, 0.62), "lens": 50.0},
    "rear_3q":       {"loc": (-5.15, -5.65, 1.42), "tgt": ( 0.0, -0.10, 0.66), "lens": 52.0},
    "side_left":     {"loc": (-10.8, -0.06, 0.80), "tgt": ( 0.0, -0.06, 0.68), "lens": 64.0},
    "front_pure":    {"loc": ( 0.00,  7.60, 0.78), "tgt": ( 0.0,  0.00, 0.66), "lens": 68.0},
    "rear_pure":     {"loc": ( 0.00, -7.80, 0.82), "tgt": ( 0.0,  0.00, 0.68), "lens": 68.0},
    "top_plan":      {"loc": ( 0.00, -0.06, 9.60), "tgt": ( 0.0, -0.06, 0.50), "lens": 56.0},
    "closeup_headlight": {"loc": (-1.75, 3.25, 0.78), "tgt": (-0.64, 2.05, 0.64), "lens": 70.0},
    "closeup_wheel":     {"loc": (-2.25, 1.55, 0.44), "tgt": (-0.85, 1.48, 0.36), "lens": 70.0},
    "closeup_rear_detail": {"loc": (0.95, -3.75, 0.88), "tgt": (0.35, -2.48, 0.78), "lens": 68.0},
    "interior_cockpit":  {"loc": (0.28, -0.68, 1.12), "tgt": (-0.22, 0.45, 0.76), "lens": 26.0},
    "interior_seats":    {"loc": (-0.72, 0.15, 1.06), "tgt": (0.20, -0.35, 0.78), "lens": 28.0},
}
