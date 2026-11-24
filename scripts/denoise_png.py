"""Denoise display-referred Cycles PNGs with the standalone OIDN CPU executable."""

import argparse
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image


def denoise(executable, source, target, threads):
    with Image.open(source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    height, width = rgb.shape[:2]

    with TemporaryDirectory() as workdir:
        noisy = Path(workdir) / "noisy.pfm"
        clean = Path(workdir) / "clean.pfm"
        with noisy.open("wb") as stream:
            stream.write(f"PF\n{width} {height}\n-1.0\n".encode("ascii"))
            rgb[::-1].astype("<f4").tofile(stream)

        subprocess.run(
            [executable, "--device", "cpu", "--threads", str(threads), "--ldr", str(noisy),
             "--srgb", "--quality", "high", "--output", str(clean)],
            check=True,
        )

        with clean.open("rb") as stream:
            if stream.readline().strip() != b"PF" or tuple(map(int, stream.readline().split())) != (width, height):
                raise ValueError("OIDN output is not a color PFM with the source dimensions")
            scale = float(stream.readline())
            clean_rgb = np.fromfile(stream, dtype="<f4" if scale < 0 else ">f4")
        if clean_rgb.size != width * height * 3 or not np.isfinite(clean_rgb).all():
            raise ValueError("OIDN output has missing or invalid pixels")

    encoded = clean_rgb.reshape(height, width, 3)[::-1] * abs(scale)
    output = np.clip(np.rint(encoded * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(output).save(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oidn", default="oidnDenoise", help="Path to the Open Image Denoise executable")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True, help="Directory for the denoised PNGs")
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for source in args.inputs:
        target = args.out / source.name
        if target.resolve() == source.resolve():
            parser.error("the output directory must preserve the source PNGs")
        denoise(args.oidn, source, target, args.threads)


if __name__ == "__main__":
    main()
