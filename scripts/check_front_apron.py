"""Check that the lower lamp and air curtain are exposed through the bumper."""

import bpy
from mathutils import Vector


def main():
    scene = bpy.context.scene
    graph = bpy.context.evaluated_depsgraph_get()
    direction = Vector((0, -1, 0))
    probes = (
        (0.61, 0.37, "Light_FrontFog_SmokedLens"),
        (0.67, 0.39, "Light_FrontFog_SmokedLens"),
        (0.73, 0.40, "Light_FrontFog_SmokedLens"),
        (0.82, 0.42, "Light_FrontFog_SmokedLens"),
        (0.84, 0.23, "Trim_Front_AirCurtain_Duct"),
        (0.86, 0.38, "Trim_Front_AirCurtain_Duct"),
        (0.65, 0.35, "Body_Front_Bumper"),
        (0.90, 0.25, "Body_Front_Bumper"),
    )

    for side in (-1, 1):
        for x, z, expected in probes:
            hit, _, normal, _, obj, _ = scene.ray_cast(graph, Vector((side * x, 3, z)), direction)
            assert hit and obj.name == expected, (side * x, z, expected, obj)
            assert normal.y > 0.25, (side * x, z, normal)

    print(f"Front apron: {2 * len(probes)} exposed face checks passed.")


if __name__ == "__main__":
    main()
