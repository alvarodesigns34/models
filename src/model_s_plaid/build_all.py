"""
Master Build Orchestrator for the 2024 Tesla Model S Plaid (Ultra Red PR01).

Usage (from repository root):
  /home/antigravity/tools/blender-4.2.23-linux-x64/blender -b --python src/model_s_plaid/build_all.py
"""

import os
import sys
import math
import bpy
from mathutils import Vector

# Ensure repo src/ is on sys.path when invoked via Blender --python
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from model_s_plaid import config as C
from model_s_plaid.geometry_utils import ensure_collection
from model_s_plaid.materials import create_all_materials
from model_s_plaid.body_master import build_all_bodywork
from model_s_plaid.glazing import build_all_glazing
from model_s_plaid.lighting import build_all_lighting
from model_s_plaid.wheels_brakes import build_all_wheels_and_brakes
from model_s_plaid.exterior_details import build_all_exterior_details
from model_s_plaid.interior import build_all_interior
from model_s_plaid.environments import setup_environment, configure_cycles_render, set_camera, CAMERA_PRESETS


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def verify_vehicle_dimensions():
    """Measure exact bounding box of all rendered vehicle meshes and verify against official Plaid specs."""
    deps = bpy.context.evaluated_depsgraph_get()
    min_x = min_y = min_z = 1e9
    max_x = max_y = max_z = -1e9
    body_max_x = 0.0
    total_verts = 0
    total_polys = 0
    obj_count = 0

    for obj in bpy.data.objects:
        if obj.type not in ("MESH", "FONT") or obj.hide_render:
            continue
        if obj.name.startswith("Env_"):
            continue
        ev = obj.evaluated_get(deps)
        mesh = ev.to_mesh()
        total_verts += len(mesh.vertices)
        total_polys += len(mesh.polygons)
        obj_count += 1
        mw = obj.matrix_world
        for v in mesh.vertices:
            co = mw @ v.co
            min_x = min(min_x, co.x)
            max_x = max(max_x, co.x)
            min_y = min(min_y, co.y)
            max_y = max(max_y, co.y)
            min_z = min(min_z, co.z)
            max_z = max(max_z, co.z)
            if not obj.name.startswith("Mirror_"):
                body_max_x = max(body_max_x, abs(co.x))
        ev.to_mesh_clear()

    length = max_y - min_y
    width_mirrors = max_x - min_x
    width_body = body_max_x * 2.0
    height = max_z - min_z

    print("\n================ TESLA MODEL S PLAID GEOMETRY AUDIT ================")
    print(f"Objects: {obj_count} | Vertices: {total_verts:,} | Polygons: {total_polys:,}")
    print(f"Length          : {length*1000:.1f} mm  (Target: {C.LENGTH*1000:.1f} mm | Diff: {(length-C.LENGTH)*1000:+.1f} mm)")
    print(f"Width (body)    : {width_body*1000:.1f} mm  (Target: {C.WIDTH_BODY*1000:.1f} mm | Diff: {(width_body-C.WIDTH_BODY)*1000:+.1f} mm)")
    print(f"Width (mirrors) : {width_mirrors*1000:.1f} mm  (Target: {C.WIDTH_MIRRORS*1000:.1f} mm | Diff: {(width_mirrors-C.WIDTH_MIRRORS)*1000:+.1f} mm)")
    print(f"Height          : {height*1000:.1f} mm  (Target: {C.HEIGHT*1000:.1f} mm | Diff: {(height-C.HEIGHT)*1000:+.1f} mm)")
    print(f"Ground Z Min    : {min_z*1000:+.1f} mm  (Target: 0.0 mm)")
    print("====================================================================\n")


def build_vehicle(save_blend=True):
    clear_scene()
    root_col = ensure_collection("Tesla_Model_S_Plaid_2024_UltraRed")

    mats = create_all_materials()
    _, fog_opening = build_all_bodywork(root_col, mats)
    build_all_glazing(root_col, mats)
    build_all_lighting(root_col, mats, fog_opening)
    build_all_wheels_and_brakes(root_col, mats)
    build_all_exterior_details(root_col, mats)
    build_all_interior(root_col, mats)

    # Default Studio lighting & hero 3/4 camera ready on open
    setup_environment("studio")
    configure_cycles_render(res_x=1920, res_y=1080, samples=128)
    preset = CAMERA_PRESETS["front_3q"]
    set_camera("Camera_Hero", preset["loc"], preset["tgt"], lens_mm=preset["lens"])

    verify_vehicle_dimensions()

    if save_blend:
        os.makedirs(C.BLEND_DIR, exist_ok=True)
        out_path = os.path.join(C.BLEND_DIR, "tesla_model_s_plaid_ultra_red.blend")
        bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
        print(f"Saved master editable Blender scene: {out_path}")


if __name__ == "__main__":
    build_vehicle(save_blend=True)
