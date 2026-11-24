"""
Multi-Angle, Multi-Environment Cycles OIDN Render Suite for the
2024 Tesla Model S Plaid (Ultra Red PR01).

Usage:
  blender -b blend/tesla_model_s_plaid_ultra_red.blend --python scripts/render_suite.py -- \
      --out renders/iterations/iter01 --env studio --views front_3q,rear_3q,side_left,front_pure,rear_pure \
      --res 960x540 --samples 36
"""

import os
import sys
import time
import argparse
import bpy

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from model_s_plaid.environments import (
    setup_environment,
    configure_cycles_render,
    set_camera,
    CAMERA_PRESETS,
)


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(REPO_ROOT, "renders", "iterations", "iter01"))
    parser.add_argument("--env", default="studio", choices=["studio", "daylight", "overcast", "night", "zebra"])
    parser.add_argument("--views", default="front_3q,rear_3q,side_left,front_pure,rear_pure")
    parser.add_argument("--res", default="960x540")
    parser.add_argument("--samples", type=int, default=36)
    parser.add_argument("--prefix", default="")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    res_x, res_y = [int(x) for x in args.res.lower().split("x")]

    setup_environment(args.env)
    configure_cycles_render(res_x=res_x, res_y=res_y, samples=args.samples, use_agx=(args.env != "zebra"))

    views = [v.strip() for v in args.views.split(",") if v.strip()]
    for vname in views:
        if vname not in CAMERA_PRESETS:
            print(f"WARNING: Unknown view '{vname}', skipping.")
            continue
        preset = CAMERA_PRESETS[vname]
        set_camera(f"Cam_{vname}", preset["loc"], preset["tgt"], lens_mm=preset["lens"])
        fname = f"{args.prefix}{args.env}_{vname}.png"
        out_path = os.path.join(args.out, fname)
        bpy.context.scene.render.filepath = out_path
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {fname} ({res_x}x{res_y} @ {args.samples} spp) in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
