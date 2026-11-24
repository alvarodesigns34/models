"""Check that both painted panels reach the arch seam and the lens stays exposed."""

from collections import Counter
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_point_line

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model_s_plaid.body_master import eval_front_fender_bumper_join
from model_s_plaid.lighting import _headlight_outline_point


def boundary_segments(object_name):
    mesh = bpy.data.objects[object_name].data
    uses = Counter(key for polygon in mesh.polygons for key in polygon.edge_keys)
    return [(mesh.vertices[a].co, mesh.vertices[b].co) for (a, b), count in uses.items() if count == 1]


def boundary_distance(point, segments):
    distances = []
    for a, b in segments:
        _, factor = intersect_point_line(point, a, b)
        distances.append((point - a.lerp(b, max(0.0, min(1.0, factor)))).length)
    return min(distances)


def main():
    for name in ("Body_Front_Fender", "Body_Front_Bumper"):
        segments = boundary_segments(name)
        for step in range(17):
            point = Vector(eval_front_fender_bumper_join(step / 16))
            distance = boundary_distance(point, segments)
            assert distance < 0.0025, (name, step, distance)

    graph = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    origin = Vector((0.0, 7.60, 0.94))
    for side in (-1, 1):
        for u in (0.25, 0.52, 0.76):
            for v in (0.30, 0.66):
                x, y, z = _headlight_outline_point(u, v)
                direction = (Vector((side * x, y, z)) - origin).normalized()
                hit, _, normal, _, obj, _ = scene.ray_cast(graph, origin, direction)
                assert hit and obj.name == "Light_Headlight_OuterLens", (side, u, v, obj)
                assert normal.dot(-direction) > 0.05, (side, u, v, normal)

    print("Headlight joins: 34 mesh-edge checks and 12 exposed lens checks passed.")


if __name__ == "__main__":
    main()
