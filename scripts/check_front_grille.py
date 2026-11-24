"""Check frontal and off-axis visibility of the lower grille on a built scene.

Run with blender -b <scene.blend> --python-exit-code 1 --python scripts/check_front_grille.py.
"""

import bpy
from mathutils import Vector


def main():
    scene = bpy.context.scene
    graph = bpy.context.evaluated_depsgraph_get()
    front = Vector((0.0, -1.0, 0.0))
    checked = 0

    for direction in (front, Vector((0.34, -1.0, 0.0)).normalized()):
        for x in (-0.35, -0.16, 0.0, 0.16, 0.35):
            for z in (0.20, 0.225, 0.25, 0.275):
                origin = Vector((x, 2.35, z)) - direction
                hit, location, _, _, obj, _ = scene.ray_cast(graph, origin, direction)
                assert hit and obj.name.startswith("Trim_Front_Grille_"), (x, z, direction, obj)
                assert location.y < 2.42, (x, z, location)
                checked += 1

    for x, z in ((0.0, 0.155), (0.0, 0.32), (-0.56, 0.23), (0.56, 0.23)):
        hit, _, _, _, obj, _ = scene.ray_cast(graph, Vector((x, 3.0, z)), front)
        assert hit and obj.name == "Body_Front_Bumper", (x, z, obj)
        checked += 1

    print(f"Front fascia: {checked} ray checks passed.")


if __name__ == "__main__":
    main()
