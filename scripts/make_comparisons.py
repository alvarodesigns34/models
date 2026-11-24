"""
Build high-resolution labeled visual comparison sheets comparing our Blender
Cycles renders side-by-side against authentic Tesla Model S Plaid photographs.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fit_box(img, target_w, target_h):
    """Aspect-preserving center-crop fill into (target_w, target_h)."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - target_w) // 2
    y0 = (nh - target_h) // 2
    return resized.crop((x0, y0, x0 + target_w, y0 + target_h))


def make_side_by_side(pairs, out_path, title="Tesla Model S Plaid — Visual Reference Comparison"):
    """
    pairs: list of (left_img_path, left_label, right_img_path, right_label)
    """
    cell_w, cell_h = 840, 480
    pad = 16
    header_h = 56
    label_h = 32
    rows = len(pairs)

    canvas_w = pad * 3 + cell_w * 2
    canvas_h = header_h + rows * (cell_h + label_h + pad) + pad
    canvas = Image.new("RGB", (canvas_w, canvas_h), (16, 17, 20))
    draw = ImageDraw.Draw(canvas)
    f_title = load_font(24)
    f_lbl = load_font(18)

    draw.text((pad, 14), title, font=f_title, fill=(240, 242, 246))

    for r, (lp, ll, rp, rl) in enumerate(pairs):
        y_top = header_h + r * (cell_h + label_h + pad)
        for col_idx, (path, label) in enumerate([(lp, ll), (rp, rl)]):
            x_left = pad + col_idx * (cell_w + pad)
            draw.text((x_left + 4, y_top + 4), label, font=f_lbl, fill=(205, 210, 220))
            if os.path.exists(path):
                im = Image.open(path).convert("RGB")
                fitted = fit_box(im, cell_w, cell_h)
                canvas.paste(fitted, (x_left, y_top + label_h))
            else:
                draw.rectangle([x_left, y_top + label_h, x_left + cell_w, y_top + label_h + cell_h], outline=(180, 40, 40), width=2)
                draw.text((x_left + 20, y_top + label_h + 20), f"Missing: {os.path.basename(path)}", font=f_lbl, fill=(220, 80, 80))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path, quality=95)
    print(f"Saved comparison sheet: {out_path}")


if __name__ == "__main__":
    render_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "renders", "final")
    out_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO_ROOT, "renders", "comparisons", "comparison_real_vs_render.jpg")
    prefix = sys.argv[3] if len(sys.argv) > 3 else "studio_"

    ref_wiki = os.path.join(REPO_ROOT, "references", "wikimedia")
    pairs = [
        (
            os.path.join(render_dir, f"{prefix}front_3q.png"),
            "Blender Cycles 4.2 — 2024 Model S Plaid (Ultra Red) Front 3/4",
            os.path.join(ref_wiki, "Tesla_Model_S_Plaid_Autofrühling_Ulm_IMG_9278.jpg"),
            "Real Photo Reference — 2023 Model S Plaid Front 3/4 (Wikimedia CC)",
        ),
        (
            os.path.join(render_dir, f"{prefix}rear_3q.png"),
            "Blender Cycles 4.2 — 2024 Model S Plaid (Ultra Red) Rear 3/4",
            os.path.join(ref_wiki, "Tesla_Model_S_Plaid_Autofrühling_Ulm_IMG_9321.jpg"),
            "Real Photo Reference — 2023 Model S Plaid Rear 3/4 (Wikimedia CC)",
        ),
        (
            os.path.join(render_dir, f"{prefix}side_left.png"),
            "Blender Cycles 4.2 — 2024 Model S Plaid (Ultra Red) Side Profile",
            os.path.join(ref_wiki, "Tesla_Model_S_2024_Blue.jpg"),
            "Real Photo Reference — 2024 Model S Side Silhouette (Wikimedia CC)",
        ),
        (
            os.path.join(render_dir, f"{prefix}front_pure.png"),
            "Blender Cycles 4.2 — 2024 Model S Plaid (Ultra Red) Front Fascia",
            os.path.join(ref_wiki, "Tesla_Model_S_2023_Motorworld_Munich_1X7A0025.jpg"),
            "Real Photo Reference — 2023 Model S Front Fascia & Matrix Headlights (Wikimedia CC)",
        ),
    ]
    make_side_by_side(pairs, out_file)

    # Also build optional detail sheet when close-up renders exist
    hl_path = os.path.join(render_dir, f"{prefix}closeup_headlight.png")
    wh_path = os.path.join(render_dir, f"{prefix}closeup_wheel.png")
    if os.path.exists(hl_path) and os.path.exists(wh_path):
        detail_out = os.path.join(os.path.dirname(out_file), "comparison_details_vs_real.jpg")
        detail_pairs = [
            (
                hl_path,
                "Blender Cycles 4.2 — Matrix LED Headlight & Front Air-Curtain Close-Up",
                os.path.join(ref_wiki, "2023_Tesla_Model_S_Plaid.jpg"),
                "Real Photo Reference — 2023 Model S Plaid Matrix LED & Arachnid Detail (Wikimedia CC)",
            ),
            (
                wh_path,
                "Blender Cycles 4.2 — 21\" Arachnid Wheel, Michelin PS4S & Red Plaid Caliper",
                os.path.join(ref_wiki, "Tesla_Model_S_Plaid_Autofrühling_Ulm_IMG_9278.jpg"),
                "Real Photo Reference — 21\" Arachnid Wheel & Red Caliper Stance (Wikimedia CC)",
            ),
        ]
        make_side_by_side(detail_pairs, detail_out, title="Tesla Model S Plaid — Optical & Mechanical Detail Comparison")
