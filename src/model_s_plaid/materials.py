"""
Physically based Blender 4.2 Cycles material library for the
2024 Tesla Model S Plaid (Ultra Red PR01).

All shaders use physically plausible IOR, micro-normal variation, metallic flake
layers, multi-layer clearcoat, and Cycles shadow-ray optimized optical glass.
"""

import os
import bpy
from . import config


def _load_image(filename, colorspace="sRGB"):
    path = os.path.join(config.TEXTURE_DIR, filename)
    if not os.path.exists(path):
        return None
    img = bpy.data.images.load(path, check_existing=True)
    try:
        img.colorspace_settings.name = colorspace
    except Exception:
        pass
    try:
        img.pack()
    except Exception:
        pass
    return img


def _new_material(name):
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
        mat.node_tree.nodes.clear()
    else:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
    return mat


def build_ultra_red_paint():
    """
    Tesla Ultra Red Metallic (PR01) — multi-layer automotive tri-coat paint:
      - 3-angle Fresnel/Facing crimson-to-dark-ruby metallic color flop
      - Fine metallic aluminum/crimson micro-flake sparkle (Voronoi 3D object space)
      - High-gloss automotive clearcoat (IOR 1.54, Coat Roughness 0.016)
      - Microscopic clearcoat orange-peel normal variation (scale ~320, subtle strength)
    """
    mat = _new_material("Tesla_Ultra_Red_PR01")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (800, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (450, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Object coordinates for scale-consistent metallic flakes and clearcoat orange peel
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-900, -100)

    # 1. Multi-angle metallic flop via Layer Weight (Facing)
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.location = (-550, 320)
    lw.inputs["Blend"].default_value = 0.42

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-250, 320)
    ramp.color_ramp.interpolation = "B_SPLINE"
    e0 = ramp.color_ramp.elements[0]
    e0.position = 0.0
    e0.color = config.ULTRA_RED_DIRECT  # Direct sunlit vivid crimson
    e1 = ramp.color_ramp.elements[1]
    e1.position = 0.58
    e1.color = config.ULTRA_RED_MID     # Deep rich ruby midtone
    e2 = ramp.color_ramp.elements.new(0.95)
    e2.color = config.ULTRA_RED_FLOP    # Ultra-deep dark wine-burgundy grazing flop
    links.new(lw.outputs["Facing"], ramp.inputs["Fac"])

    # 2. Microscopic metallic flake sparkle layer
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.location = (-550, 40)
    vor.feature = "F1"
    vor.inputs["Scale"].default_value = 2600.0
    vor.inputs["Randomness"].default_value = 1.0
    links.new(tex_coord.outputs["Object"], vor.inputs["Vector"])

    # Flake brightness micro-variation blended subtly into base color
    flake_ramp = nodes.new("ShaderNodeValToRGB")
    flake_ramp.location = (-250, 60)
    flake_ramp.color_ramp.elements[0].position = 0.15
    flake_ramp.color_ramp.elements[0].color = (0.72, 0.72, 0.72, 1.0)
    flake_ramp.color_ramp.elements[1].position = 0.88
    flake_ramp.color_ramp.elements[1].color = (1.35, 1.15, 1.15, 1.0)
    links.new(vor.outputs["Distance"], flake_ramp.inputs["Fac"])

    mix_col = nodes.new("ShaderNodeMix")
    mix_col.data_type = "RGBA"
    mix_col.blend_type = "MULTIPLY"
    mix_col.location = (80, 220)
    mix_col.inputs["Factor"].default_value = 0.32
    links.new(ramp.outputs["Color"], mix_col.inputs[6])
    links.new(flake_ramp.outputs["Color"], mix_col.inputs[7])
    links.new(mix_col.outputs[2], bsdf.inputs["Base Color"])

    # Flake micro-normal perturbation ONLY on the metallic basecoat (Normal input),
    # while Clearcoat gets its own glassy orange-peel normal!
    flake_bump = nodes.new("ShaderNodeBump")
    flake_bump.location = (120, -40)
    flake_bump.inputs["Strength"].default_value = 0.045
    flake_bump.inputs["Distance"].default_value = 0.0004
    links.new(vor.outputs["Distance"], flake_bump.inputs["Height"])
    links.new(flake_bump.outputs["Normal"], bsdf.inputs["Normal"])

    # 3. Clearcoat subtle automotive orange-peel micro-undulation
    peel_noise = nodes.new("ShaderNodeTexNoise")
    peel_noise.location = (-550, -260)
    peel_noise.inputs["Scale"].default_value = 220.0
    peel_noise.inputs["Detail"].default_value = 2.0
    peel_noise.inputs["Roughness"].default_value = 0.45
    links.new(tex_coord.outputs["Object"], peel_noise.inputs["Vector"])

    peel_bump = nodes.new("ShaderNodeBump")
    peel_bump.location = (120, -260)
    peel_bump.inputs["Strength"].default_value = 0.008
    peel_bump.inputs["Distance"].default_value = 0.0005
    links.new(peel_noise.outputs["Fac"], peel_bump.inputs["Height"])
    links.new(peel_bump.outputs["Normal"], bsdf.inputs["Coat Normal"])

    # Metallic basecoat + thick crystal-clear automotive clearcoat
    bsdf.inputs["Metallic"].default_value = 0.78
    bsdf.inputs["Roughness"].default_value = 0.21
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.012
    bsdf.inputs["Coat IOR"].default_value = 1.54
    bsdf.inputs["Coat Tint"].default_value = (1.0, 0.92, 0.92, 1.0)

    return mat


def build_automotive_glass(name, tint_rgb, shadow_rgb, roughness=0.005, ior=1.52,
                           transmission=0.92, dark_reflect=False):
    """
    Physically accurate thin-sheet automotive laminated glass (Cycles architectural glass):
      - Crisp mirror Fresnel reflections (IOR 1.52) via Layer Weight + Glossy BSDF
      - Crystal-clear physically tinted transmission via Transparent BSDF (zero milky
        double-wall TIR artifacts, 2.5x faster Cycles rendering, crisp cabin visibility!)
      - Clean soft tinted shadow transmission into interior cabin.
    """
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)

    # Glass reflection vs tint balance
    fresnel = nodes.new("ShaderNodeLayerWeight")
    fresnel.location = (-220, 260)
    fresnel.inputs["Blend"].default_value = 0.24 if dark_reflect else 0.16

    glossy = nodes.new("ShaderNodeBsdfGlossy")
    glossy.location = (60, 140)
    glossy.inputs["Color"].default_value = (0.94, 0.96, 0.98, 1.0)
    glossy.inputs["Roughness"].default_value = roughness

    transp_vis = nodes.new("ShaderNodeBsdfTransparent")
    transp_vis.location = (60, -60)
    # Darken glass tint naturally according to VLT
    transp_vis.inputs["Color"].default_value = (*tint_rgb, 1.0)

    mix_glass = nodes.new("ShaderNodeMixShader")
    mix_glass.location = (340, 80)
    links.new(fresnel.outputs["Fresnel"], mix_glass.inputs["Fac"])
    links.new(transp_vis.outputs["BSDF"], mix_glass.inputs[1])
    links.new(glossy.outputs["BSDF"], mix_glass.inputs[2])

    # Shadow ray pass-through so interior seats/dash stay realistically lit
    transp_sh = nodes.new("ShaderNodeBsdfTransparent")
    transp_sh.location = (340, -160)
    transp_sh.inputs["Color"].default_value = (*shadow_rgb, 1.0)

    lp = nodes.new("ShaderNodeLightPath")
    lp.location = (340, 280)

    mix_final = nodes.new("ShaderNodeMixShader")
    mix_final.location = (560, 0)
    links.new(lp.outputs["Is Shadow Ray"], mix_final.inputs["Fac"])
    links.new(mix_glass.outputs["Shader"], mix_final.inputs[1])
    links.new(transp_sh.outputs["BSDF"], mix_final.inputs[2])
    links.new(mix_final.outputs["Shader"], out.inputs["Surface"])

    return mat


def build_carbon_fiber(name="Carbon_Fiber_Satin", coat_weight=0.55, coat_rough=0.14, uv_repeat=14.0):
    """2x2 twill carbon fiber with textured albedo, height bump, and satin clearcoat."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (650, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-750, 0)
    mp = nodes.new("ShaderNodeMapping")
    mp.location = (-520, 0)
    mp.inputs["Scale"].default_value = (uv_repeat, uv_repeat, uv_repeat)
    links.new(tc.outputs["UV"], mp.inputs["Vector"])

    img_col = _load_image("carbon_weave_color.png", "sRGB")
    img_h = _load_image("carbon_weave_height.png", "Non-Color")
    img_r = _load_image("carbon_weave_rough.png", "Non-Color")

    if img_col:
        t_col = nodes.new("ShaderNodeTexImage")
        t_col.location = (-220, 220)
        t_col.image = img_col
        links.new(mp.outputs["Vector"], t_col.inputs["Vector"])
        links.new(t_col.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.025, 0.026, 0.028, 1.0)

    if img_r:
        t_r = nodes.new("ShaderNodeTexImage")
        t_r.location = (-220, -20)
        t_r.image = img_r
        links.new(mp.outputs["Vector"], t_r.inputs["Vector"])
        mr = nodes.new("ShaderNodeMapRange")
        mr.location = (40, -20)
        mr.inputs["To Min"].default_value = 0.22
        mr.inputs["To Max"].default_value = 0.44
        links.new(t_r.outputs["Color"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = 0.30

    if img_h:
        t_h = nodes.new("ShaderNodeTexImage")
        t_h.location = (-220, -280)
        t_h.image = img_h
        links.new(mp.outputs["Vector"], t_h.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump")
        bump.location = (50, -240)
        bump.inputs["Strength"].default_value = 0.28
        bump.inputs["Distance"].default_value = 0.001
        links.new(t_h.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Metallic"].default_value = 0.18
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    bsdf.inputs["Coat Weight"].default_value = coat_weight
    bsdf.inputs["Coat Roughness"].default_value = coat_rough
    bsdf.inputs["Coat IOR"].default_value = 1.50
    return mat


def build_simple_pbr(name, color, metallic=0.0, roughness=0.35, coat=0.0,
                     coat_rough=0.05, spec=0.5, sheen=0.0, noise_bump=0.0,
                     noise_scale=250.0, emission=None, emission_strength=0.0):
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (450, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (120, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (*color[:3], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = spec
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_rough
    bsdf.inputs["Sheen Weight"].default_value = sheen
    bsdf.inputs["Sheen Roughness"].default_value = 0.45

    if emission is not None and emission_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*emission[:3], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    if noise_bump > 0.0:
        tc = nodes.new("ShaderNodeTexCoord")
        tc.location = (-550, -180)
        n = nodes.new("ShaderNodeTexNoise")
        n.location = (-320, -180)
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 6.0
        n.inputs["Roughness"].default_value = 0.65
        links.new(tc.outputs["Object"], n.inputs["Vector"])
        b = nodes.new("ShaderNodeBump")
        b.location = (-100, -180)
        b.inputs["Strength"].default_value = noise_bump
        b.inputs["Distance"].default_value = 0.001
        links.new(n.outputs["Fac"], b.inputs["Height"])
        links.new(b.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def build_tire_sidewall_mat(name, bump_file, rough_file):
    """Deep vulcanized Michelin Pilot Sport 4S 'Premium Touch' velvet sidewall w/ raised lettering."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (640, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Low effective dielectric specular keeps flat sidewall deep jet-black even under bright studio lights!
    bsdf.inputs["Specular IOR Level"].default_value = 0.075

    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-640, 0)

    img_b = _load_image(bump_file, "Non-Color")
    img_r = _load_image(rough_file, "Non-Color")

    if img_r:
        tr = nodes.new("ShaderNodeTexImage")
        tr.location = (-320, 140)
        tr.image = img_r
        links.new(tc.outputs["UV"], tr.inputs["Vector"])

        # Darker jet-black inside Michelin laser-etched velvet checkers vs smooth rubber rings!
        col_mix = nodes.new("ShaderNodeMix")
        col_mix.data_type = "RGBA"
        col_mix.location = (20, 260)
        col_mix.inputs[6].default_value = (0.0058, 0.0062, 0.0070, 1.0)
        col_mix.inputs[7].default_value = (0.0020, 0.0022, 0.0025, 1.0)
        links.new(tr.outputs["Color"], col_mix.inputs["Factor"])
        links.new(col_mix.outputs[2], bsdf.inputs["Base Color"])

        mr = nodes.new("ShaderNodeMapRange")
        mr.location = (20, 80)
        mr.inputs["To Min"].default_value = 0.56
        mr.inputs["To Max"].default_value = 0.94
        links.new(tr.outputs["Color"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.0040, 0.0042, 0.0048, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.72

    if img_b:
        tb = nodes.new("ShaderNodeTexImage")
        tb.location = (-320, -180)
        tb.image = img_b
        links.new(tc.outputs["UV"], tb.inputs["Vector"])
        bump = nodes.new("ShaderNodeBump")
        bump.location = (40, -180)
        bump.inputs["Strength"].default_value = 0.68
        bump.inputs["Distance"].default_value = 0.0030
        links.new(tb.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def build_brake_rotor_mat():
    """Brushed lathe-turned steel/cast-iron brake disc with radial wear rings."""
    mat = _new_material("Brake_Rotor_Steel")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (280, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (0.48, 0.49, 0.52, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.96
    bsdf.inputs["Anisotropic"].default_value = 0.72

    img = _load_image("brake_rotor_radial.png", "Non-Color")
    if img:
        tc = nodes.new("ShaderNodeTexCoord")
        tc.location = (-550, 0)
        ti = nodes.new("ShaderNodeTexImage")
        ti.location = (-280, 0)
        ti.image = img
        links.new(tc.outputs["UV"], ti.inputs["Vector"])

        mr = nodes.new("ShaderNodeMapRange")
        mr.location = (20, 120)
        mr.inputs["To Min"].default_value = 0.18
        mr.inputs["To Max"].default_value = 0.36
        links.new(ti.outputs["Color"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

        b = nodes.new("ShaderNodeBump")
        b.location = (20, -140)
        b.inputs["Strength"].default_value = 0.16
        b.inputs["Distance"].default_value = 0.0005
        links.new(ti.outputs["Color"], b.inputs["Height"])
        links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        bsdf.inputs["Roughness"].default_value = 0.25

    return mat


def build_plaid_badge_mat():
    """Metallic/enamel geometric Plaid warp badge with crisp contrast and controlled clear coat."""
    mat = _new_material("Plaid_Badge_Mat")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (260, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-550, 0)

    img_col = _load_image("plaid_badge.png", "sRGB")
    img_met = _load_image("plaid_badge_metal.png", "Non-Color")

    if img_col:
        t1 = nodes.new("ShaderNodeTexImage")
        t1.location = (-250, 140)
        t1.image = img_col
        links.new(tc.outputs["UV"], t1.inputs["Vector"])
        links.new(t1.outputs["Color"], bsdf.inputs["Base Color"])

    if img_met:
        t2 = nodes.new("ShaderNodeTexImage")
        t2.location = (-250, -140)
        t2.image = img_met
        links.new(tc.outputs["UV"], t2.inputs["Vector"])
        links.new(t2.outputs["Color"], bsdf.inputs["Metallic"])

    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Coat Weight"].default_value = 0.42
    bsdf.inputs["Coat Roughness"].default_value = 0.06
    return mat


def build_screen_mat(name, image_file, strength=1.4):
    """Emissive automotive OLED/LCD screen behind anti-reflective glossy cover glass."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (550, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (220, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.04
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.01
    bsdf.inputs["Emission Strength"].default_value = strength

    img = _load_image(image_file, "sRGB")
    if img:
        tc = nodes.new("ShaderNodeTexCoord")
        tc.location = (-450, 0)
        ti = nodes.new("ShaderNodeTexImage")
        ti.location = (-180, 0)
        ti.image = img
        links.new(tc.outputs["UV"], ti.inputs["Vector"])
        links.new(ti.outputs["Color"], bsdf.inputs["Emission Color"])

    return mat


def build_perforated_leather_mat():
    """Black perforated vegan leather for 2024 Plaid Sport Seat centers."""
    mat = _new_material("Interior_Vegan_Leather_Perforated")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (620, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (280, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-650, 0)

    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.location = (-360, 140)
    vor.inputs["Scale"].default_value = 180.0
    vor.inputs["Randomness"].default_value = 0.05
    links.new(tc.outputs["Object"], vor.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-120, 140)
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.24
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(vor.outputs["Distance"], ramp.inputs["Fac"])

    mix_col = nodes.new("ShaderNodeMix")
    mix_col.data_type = "RGBA"
    mix_col.location = (80, 220)
    mix_col.inputs[6].default_value = (0.0015, 0.0015, 0.002, 1.0)
    mix_col.inputs[7].default_value = (0.011, 0.0115, 0.013, 1.0)
    links.new(ramp.outputs["Color"], mix_col.inputs["Factor"])
    links.new(mix_col.outputs[2], bsdf.inputs["Base Color"])

    bump = nodes.new("ShaderNodeBump")
    bump.location = (60, -120)
    bump.inputs["Strength"].default_value = 0.42
    bump.inputs["Distance"].default_value = 0.0012
    links.new(ramp.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Specular IOR Level"].default_value = 0.34
    bsdf.inputs["Sheen Weight"].default_value = 0.03
    return mat


def build_zebra_diagnostic_mat():
    """Automotive Class-A Zebra-Stripe surface curvature inspection shader."""
    mat = _new_material("Zebra_Diagnostic_Mat")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    em = nodes.new("ShaderNodeEmission")
    em.location = (350, 0)
    links.new(em.outputs["Emission"], out.inputs["Surface"])

    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-550, 0)
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-80, 0)
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 7.0
    wave.inputs["Distortion"].default_value = 0.0
    links.new(tc.outputs["Reflection"], wave.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (140, 0)
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1.0)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1.0)
    links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], em.inputs["Color"])
    mat.use_fake_user = True
    return mat


def create_all_materials():
    """Build and return dictionary of all physically based materials for the vehicle."""
    mats = {}

    # Primary Paint & Exterior Trims
    mats["paint"] = build_ultra_red_paint()
    mats["carbon_ext"] = build_carbon_fiber("Carbon_Fiber_Exterior", coat_weight=0.65, coat_rough=0.12, uv_repeat=12.0)
    mats["carbon_int"] = build_carbon_fiber("Carbon_Fiber_Interior", coat_weight=0.35, coat_rough=0.22, uv_repeat=16.0)
    mats["trim_satin_black"] = build_simple_pbr("Trim_Satin_Black", (0.007, 0.0075, 0.0085), metallic=0.05, roughness=0.30, coat=0.12, coat_rough=0.20, spec=0.35, noise_bump=0.012, noise_scale=800.0)
    mats["trim_gloss_black"] = build_simple_pbr("Trim_Gloss_Black", (0.005, 0.0055, 0.0065), metallic=0.04, roughness=0.03, coat=1.0, coat_rough=0.012)
    mats["trim_matte_plastic"] = build_simple_pbr("Trim_Matte_Underbody", (0.010, 0.0105, 0.0115), metallic=0.0, roughness=0.64, spec=0.22, noise_bump=0.035, noise_scale=600.0)
    mats["shadow_gap"] = build_simple_pbr("Body_Shadow_Gap", (0.002, 0.002, 0.0025), metallic=0.0, roughness=0.90, spec=0.02)
    mats["chrome"] = build_simple_pbr("Chrome_Emblem", (0.86, 0.87, 0.89), metallic=1.0, roughness=0.04)
    mats["dark_satin_chrome"] = build_simple_pbr("Dark_Satin_Chrome", (0.38, 0.40, 0.43), metallic=0.96, roughness=0.15)
    mats["plaid_badge"] = build_plaid_badge_mat()

    # Glazing & Optics (Crystal-clear thin-sheet automotive glass with authentic outward normals!)
    mats["glass_windshield"] = build_automotive_glass("Glass_Windshield", (0.50, 0.56, 0.56), (0.80, 0.84, 0.84), roughness=0.005, dark_reflect=False)
    mats["glass_roof"] = build_automotive_glass("Glass_Panoramic_Roof", (0.04, 0.045, 0.055), (0.35, 0.38, 0.42), roughness=0.005, dark_reflect=True)
    mats["glass_side"] = build_automotive_glass("Glass_Side_Window", (0.14, 0.17, 0.18), (0.58, 0.62, 0.62), roughness=0.005, dark_reflect=True)
    mats["glass_rear"] = build_automotive_glass("Glass_Rear_Hatch", (0.07, 0.085, 0.095), (0.42, 0.45, 0.48), roughness=0.005, dark_reflect=True)
    mats["glass_frit"] = build_simple_pbr("Glass_Black_Frit", (0.004, 0.004, 0.005), metallic=0.0, roughness=0.04, coat=1.0, coat_rough=0.01)
    mats["glass_mirror"] = build_simple_pbr("Glass_Mirror", (0.85, 0.88, 0.89), metallic=1.0, roughness=0.012)
    mats["camera_lens"] = build_simple_pbr("Camera_HW4_Lens", (0.08, 0.012, 0.016), metallic=0.3, roughness=0.02, coat=1.0, coat_rough=0.01)

    # Lighting Optics
    mats["lens_clear"] = build_automotive_glass("Optic_Clear_Polycarbonate", (0.90, 0.92, 0.94), (0.96, 0.97, 0.98), roughness=0.005, ior=1.58, dark_reflect=False)
    mats["lens_smoked"] = build_automotive_glass("Optic_Smoked_Polycarbonate", (0.18, 0.18, 0.20), (0.72, 0.72, 0.74), roughness=0.006, ior=1.58, dark_reflect=True)
    mats["lens_red"] = build_automotive_glass("Optic_Red_Taillight_Lens", (0.52, 0.015, 0.012), (0.72, 0.14, 0.12), roughness=0.008, ior=1.58, dark_reflect=True)
    mats["light_housing"] = build_simple_pbr("Light_Housing_Black", (0.008, 0.009, 0.011), metallic=0.08, roughness=0.20, coat=0.4, coat_rough=0.08)
    mats["light_reflector"] = build_simple_pbr("Light_Chrome_Reflector", (0.92, 0.93, 0.95), metallic=1.0, roughness=0.03)
    mats["led_drl"] = build_simple_pbr("LED_DRL_White", (0.96, 0.97, 1.0), roughness=0.12, emission=(0.95, 0.97, 1.0), emission_strength=14.0)
    mats["led_projector"] = build_simple_pbr("LED_Matrix_Projector", (0.95, 0.96, 1.0), roughness=0.05, coat=1.0, emission=(0.94, 0.96, 1.0), emission_strength=5.5)
    mats["led_fog"] = build_simple_pbr("LED_Fog_Strip", (0.90, 0.92, 0.96), roughness=0.15, emission=(0.92, 0.95, 1.0), emission_strength=3.0)
    mats["led_tail_red"] = build_simple_pbr("LED_Taillight_Crimson", (0.72, 0.010, 0.006), roughness=0.08, coat=0.9, coat_rough=0.02, emission=(0.98, 0.015, 0.005), emission_strength=11.0)
    mats["led_tail_reverse"] = build_simple_pbr("LED_Taillight_Reverse", (0.85, 0.87, 0.90), metallic=0.5, roughness=0.12)
    mats["reflector_red"] = build_simple_pbr("Reflector_Bumper_Red", (0.50, 0.010, 0.008), metallic=0.15, roughness=0.12, coat=1.0, coat_rough=0.02, emission=(0.35, 0.004, 0.003), emission_strength=0.20)
    mats["reflector_amber"] = build_simple_pbr("Reflector_Headlight_Amber", (0.82, 0.24, 0.005), metallic=0.20, roughness=0.12, coat=1.0, coat_rough=0.02)

    # Wheels, Tires & Brakes
    mats["wheel_arachnid"] = build_simple_pbr("Wheel_Arachnid_Anthracite", (0.024, 0.026, 0.030), metallic=0.86, roughness=0.28, coat=0.25, coat_rough=0.20)
    mats["wheel_lug"] = build_simple_pbr("Wheel_Lug_Dark_Steel", (0.055, 0.058, 0.064), metallic=0.92, roughness=0.24)
    mats["tire_tread"] = build_simple_pbr("Tire_Rubber_Tread", (0.008, 0.0085, 0.0095), metallic=0.0, roughness=0.76, spec=0.15, noise_bump=0.06, noise_scale=1200.0)
    mats["tire_sidewall_front"] = build_tire_sidewall_mat("Tire_Sidewall_Front", "tire_sidewall_front_bump.png", "tire_sidewall_front_rough.png")
    mats["tire_sidewall_rear"] = build_tire_sidewall_mat("Tire_Sidewall_Rear", "tire_sidewall_rear_bump.png", "tire_sidewall_rear_rough.png")
    mats["brake_rotor"] = build_brake_rotor_mat()
    mats["brake_hat"] = build_simple_pbr("Brake_Rotor_Hat", (0.065, 0.068, 0.074), metallic=0.85, roughness=0.34)
    mats["brake_caliper_red"] = build_simple_pbr("Brake_Caliper_Plaid_Red", (0.62, 0.010, 0.010), metallic=0.22, roughness=0.14, coat=1.0, coat_rough=0.03)
    mats["brake_epb"] = build_simple_pbr("Brake_EPB_Caliper", (0.03, 0.032, 0.035), metallic=0.4, roughness=0.38)
    mats["caliper_text"] = build_simple_pbr("Caliper_White_Text", (0.95, 0.95, 0.96), metallic=0.0, roughness=0.25)

    # Textured Red Caliper Outer Badge w/ Crisp White 'TESLA' Lettering
    cal_dec = _new_material("Brake_Caliper_Tesla_Decal")
    cnt = cal_dec.node_tree
    cn, cl = cnt.nodes, cnt.links
    cout = cn.new("ShaderNodeOutputMaterial")
    cbsdf = cn.new("ShaderNodeBsdfPrincipled")
    cl.new(cbsdf.outputs["BSDF"], cout.inputs["Surface"])
    cbsdf.inputs["Metallic"].default_value = 0.16
    cbsdf.inputs["Roughness"].default_value = 0.14
    cbsdf.inputs["Coat Weight"].default_value = 1.0
    cbsdf.inputs["Coat Roughness"].default_value = 0.03
    c_img = _load_image("caliper_tesla.png", "sRGB")
    if c_img:
        ctc = cn.new("ShaderNodeTexCoord")
        cti = cn.new("ShaderNodeTexImage")
        cti.image = c_img
        cl.new(ctc.outputs["UV"], cti.inputs["Vector"])
        cmix = cn.new("ShaderNodeMix")
        cmix.data_type = "RGBA"
        cmix.inputs[6].default_value = (0.62, 0.010, 0.010, 1.0)
        cmix.inputs[7].default_value = (0.96, 0.96, 0.97, 1.0)
        cl.new(cti.outputs["Alpha"], cmix.inputs["Factor"])
        cl.new(cmix.outputs[2], cbsdf.inputs["Base Color"])
    else:
        cbsdf.inputs["Base Color"].default_value = (0.62, 0.010, 0.010, 1.0)
    mats["caliper_decal"] = cal_dec

    # Interior Materials (Authentic Rich Tesla All-Black Premium Cabin — zero washed-out grey sheen!)
    mats["int_leather"] = build_simple_pbr("Interior_Vegan_Leather_Black", (0.010, 0.0105, 0.012), metallic=0.0, roughness=0.40, spec=0.34, sheen=0.03, noise_bump=0.028, noise_scale=950.0)
    mats["int_leather_perf"] = build_perforated_leather_mat()
    mats["int_alcantara"] = build_simple_pbr("Interior_Alcantara_Charcoal", (0.008, 0.0085, 0.010), metallic=0.0, roughness=0.88, spec=0.10, sheen=0.14, noise_bump=0.06, noise_scale=1800.0)
    mats["int_carpet"] = build_simple_pbr("Interior_Carpet_Black", (0.006, 0.006, 0.007), metallic=0.0, roughness=0.94, spec=0.06, sheen=0.08, noise_bump=0.14, noise_scale=1400.0)
    mats["int_satin_silver"] = build_simple_pbr("Interior_Satin_Silver", (0.64, 0.66, 0.69), metallic=0.94, roughness=0.22)
    mats["int_speaker_mesh"] = build_simple_pbr("Interior_Speaker_Mesh", (0.035, 0.037, 0.042), metallic=0.65, roughness=0.36, noise_bump=0.12, noise_scale=1600.0)
    mats["screen_center"] = build_screen_mat("Screen_Center_17in", "screen_center_ui.png", strength=1.8)
    mats["screen_cluster"] = build_screen_mat("Screen_Cluster_12in", "screen_cluster_ui.png", strength=1.7)
    mats["screen_rear"] = build_screen_mat("Screen_Rear_9in", "screen_rear_ui.png", strength=1.4)

    # Diagnostic Shader
    mats["zebra"] = build_zebra_diagnostic_mat()

    return mats
