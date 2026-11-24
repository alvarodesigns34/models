"""Check that the tip of both front fenders presents an outward painted face."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model_s_plaid.environments import CAMERA_PRESETS, set_camera


def main():
    scene = bpy.context.scene
    width, height = 768, 432
    scene.render.resolution_x, scene.render.resolution_y = width, height
    preset = CAMERA_PRESETS["closeup_headlight"]
    camera = set_camera("Cam_Join_QA", preset["loc"], preset["tgt"], preset["lens"])
    bpy.context.view_layer.update()
    frame = camera.data.view_frame(scene=scene)
    left, right = min(v.x for v in frame), max(v.x for v in frame)
    bottom, top = min(v.y for v in frame), max(v.y for v in frame)
    rotation = camera.matrix_world.to_quaternion()
    graph = bpy.context.evaluated_depsgraph_get()

    # Target the wedge where the old geometry showed the reverse of the fender.
    probes = ((680, 190), (684, 197), (692, 204), (696, 204), (700, 204), (704, 204))
    for x, y in probes:
        local = Vector((
            left + (right - left) * (x + 0.5) / width,
            top - (top - bottom) * (y + 0.5) / height,
            frame[0].z,
        ))
        direction = rotation @ local.normalized()
        for side in (1.0, -1.0):
            mirrored_origin = Vector((side * camera.location.x, camera.location.y, camera.location.z))
            mirrored_direction = Vector((side * direction.x, direction.y, direction.z))
            hit, _, normal, _, obj, _ = scene.ray_cast(graph, mirrored_origin, mirrored_direction)
            assert hit and obj.name == "Body_Front_Fender", (side, x, y, obj)
            assert normal.dot(-mirrored_direction) > 0.1, (side, x, y, normal)

    print(f"Headlight joins: {2 * len(probes)} outward-face checks passed.")


if __name__ == "__main__":
    main()
