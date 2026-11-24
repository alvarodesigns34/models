"""Compare projected headlamp outlines to manually marked reference pixels."""

from collections import Counter
from pathlib import Path
import sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model_s_plaid.environments import CAMERA_PRESETS, set_camera


REFERENCES = (
    (
        "ref_2024_blue", (1920, 832), -1,
        # Top brow, outside tip and lower edge of the near lamp.
        ((501, 499), (547, 479), (608, 460), (665, 451), (729, 449), (796, 446),
         (756, 482), (711, 507), (654, 518), (608, 515), (547, 515)),
    ),
    (
        "ref_ulm_front", (1920, 1278), 1,
        # An independent angle, marked after the contours were fitted.
        ((894, 691), (978, 705), (1061, 724), (1168, 749), (1279, 794),
         (1190, 807), (1066, 799), (1020, 798), (967, 783), (929, 753)),
    ),
)


def measure_outline(segments, points):
    origins = segments[:, 0]
    spans = segments[:, 1] - origins
    spans_sq = (spans ** 2).sum(axis=1)
    distance = []
    for point in points:
        relative = point - origins
        along = np.clip((relative * spans).sum(axis=1) / np.maximum(spans_sq, 1e-10), 0, 1)
        distance.append(np.linalg.norm(relative - spans * along[:, None], axis=1).min())
    return np.mean(distance), max(distance)


def main():
    scene = bpy.context.scene
    lens = bpy.data.objects["Light_Headlight_OuterLens"]
    edges = Counter(edge for face in lens.data.polygons for edge in face.edge_keys)
    perimeter = np.array([edge for edge, count in edges.items() if count == 1])

    for name, (width, height), side, reference in REFERENCES:
        scene.render.resolution_x, scene.render.resolution_y = width, height
        preset = CAMERA_PRESETS[name]
        camera = set_camera(
            f"Cam_{name}", preset["loc"], preset["tgt"], lens_mm=preset["lens"],
            shift=preset["shift"], roll=preset["roll"],
        )
        bpy.context.view_layer.update()

        projected = []
        for vertex in lens.data.vertices:
            point = lens.matrix_world @ vertex.co
            p = world_to_camera_view(scene, camera, Vector((side * abs(point.x), point.y, point.z)))
            projected.append((p.x * width, (1 - p.y) * height))

        mean, maximum = measure_outline(np.asarray(projected)[perimeter], np.array(reference))
        print(f"{name}: {len(reference)} marks, mean distance {mean:.1f}px, maximum {maximum:.1f}px")


if __name__ == "__main__":
    main()
