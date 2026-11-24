"""
Procedural high-resolution texture generator for the 2024 Tesla Model S Plaid.
Run with system Python 3 (Pillow) to generate all crisp PNG textures in textures/.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TEXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "textures"))


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_plaid_badge():
    """
    Generate the authentic 2022-2024 Tesla Model S Plaid geometric warp emblem
    (black enamel base + metallic silver/white perspective lines + red stripes).
    """
    w, h = 1024, 512
    img = Image.new("RGB", (w, h), (14, 15, 18))
    draw = ImageDraw.Draw(img)

    cx, cy = w * 0.5, h * 0.5

    # Concentric perspective tunnel rectangles converging to center
    depths = [0.05, 0.11, 0.18, 0.26, 0.35, 0.45, 0.56, 0.68, 0.81, 0.94]
    for idx, d in enumerate(depths):
        rx = cx * d * 0.85
        ry = cy * d * 0.96
        x0, y0 = cx - rx, cy - ry
        x1, y1 = cx + rx, cy + ry
        # Outer alternating silver & crimson rectangles
        if idx in (2, 5, 8):
            col = (210, 32, 28)
            width = max(3, int(6 * d + 2))
        else:
            col = (215, 220, 228)
            width = max(2, int(5 * d + 2))
        draw.rectangle([x0, y0, x1, y1], outline=col, width=width)

    # Perspective radial warp rays from center to perimeter
    # Horizontal-ish fan rays (left & right)
    for frac in [-0.82, -0.58, -0.34, -0.11, 0.11, 0.34, 0.58, 0.82]:
        y_edge = cy + frac * cy
        draw.line([(cx, cy), (0, y_edge)], fill=(212, 218, 226), width=5)
        draw.line([(cx, cy), (w, y_edge)], fill=(212, 218, 226), width=5)

    # Vertical-ish perspective rays (top & bottom)
    for frac in [-0.72, -0.50, -0.28, -0.10, 0.10, 0.28, 0.50, 0.72]:
        x_edge = cx + frac * cx
        col = (212, 32, 28) if abs(abs(frac) - 0.50) < 0.05 else (208, 214, 222)
        draw.line([(cx, cy), (x_edge, 0)], fill=col, width=4)
        draw.line([(cx, cy), (x_edge, h)], fill=col, width=4)

    # Outer bold vertical side bands (matching real Plaid badge edge bars)
    bar_specs = [
        (0.055, 10, (190, 196, 205)),
        (0.088, 16, (218, 32, 28)),
        (0.125, 8, (185, 192, 202)),
        (0.155, 14, (210, 215, 224)),
        (0.195, 7, (175, 182, 192)),
    ]
    for fx, bw, col in bar_specs:
        # Left side
        x = int(fx * w)
        draw.rectangle([x - bw // 2, 0, x + bw // 2, h], fill=col)
        # Right side mirrored
        xr = w - x
        draw.rectangle([xr - bw // 2, 0, xr + bw // 2, h], fill=col)

    # Crisp thin horizontal white/silver warp stripes across outer wings
    for fy in [0.22, 0.34, 0.44, 0.56, 0.66, 0.78]:
        y = int(fy * h)
        draw.line([(0, y), (int(w * 0.26), int(cy + (y - cy) * 0.62))], fill=(215, 220, 228), width=5)
        draw.line([(w, y), (int(w * 0.74), int(cy + (y - cy) * 0.62))], fill=(215, 220, 228), width=5)

    # Subtle dark bevel border
    draw.rectangle([0, 0, w - 1, h - 1], outline=(35, 38, 44), width=8)
    img.save(os.path.join(TEXTURE_DIR, "plaid_badge.png"))

    # Also save metallic mask (bright where stripes are, dark on black enamel)
    gray = img.convert("L")
    mask = gray.point(lambda p: 240 if p > 55 else 25)
    mask.save(os.path.join(TEXTURE_DIR, "plaid_badge_metal.png"))
    print("Generated plaid_badge.png & plaid_badge_metal.png")


def generate_carbon_fiber_weave():
    """
    Generate tileable 1024x1024 2x2 twill carbon fiber albedo, height, and roughness maps.
    """
    size = 1024
    cells = 64  # 16 px per tow -> 16 complete 4x4 twill repeats per tile
    step = size // cells

    col_img = Image.new("RGB", (size, size), (18, 19, 21))
    h_img = Image.new("L", (size, size), 128)
    r_img = Image.new("L", (size, size), 90)

    px_col = col_img.load()
    px_h = h_img.load()
    px_r = r_img.load()

    for y in range(size):
        cy = (y // step) % 4
        vy = (y % step) / float(step)
        for x in range(size):
            cx = (x // step) % 4
            vx = (x % step) / float(step)
            # 2x2 twill weave condition: (cx + cy) % 4 < 2 => horizontal tow on top, else vertical tow on top
            horiz_top = ((cx + cy) % 4) < 2
            if horiz_top:
                # Arch profile across horizontal tow
                arch = math.sin(vy * math.pi)
                along = 0.72 + 0.28 * math.sin(((x % (step * 2)) / float(step * 2)) * math.pi)
                # Fine micro-filament striations along X
                fil = 0.92 + 0.08 * math.sin(vy * 14.0 * math.pi)
                val = arch * along * fil
                c = int(14 + 34 * val)
                hval = int(95 + 145 * arch * (0.75 + 0.25 * along))
                rval = int(68 + 42 * (1.0 - val))
            else:
                # Vertical tow on top (slightly different anisotropic reflectance!)
                arch = math.sin(vx * math.pi)
                along = 0.72 + 0.28 * math.sin(((y % (step * 2)) / float(step * 2)) * math.pi)
                fil = 0.92 + 0.08 * math.sin(vx * 14.0 * math.pi)
                val = arch * along * fil
                c = int(11 + 23 * val)
                hval = int(95 + 145 * arch * (0.75 + 0.25 * along))
                rval = int(85 + 48 * (1.0 - val))

            # Tiny dark gap between tows
            edge_dist = min(vx, 1.0 - vx, vy, 1.0 - vy)
            if edge_dist < 0.06:
                f = edge_dist / 0.06
                c = int(c * (0.4 + 0.6 * f))
                hval = int(hval * (0.55 + 0.45 * f))

            px_col[x, y] = (c, c + 1, c + 2)
            px_h[x, y] = max(0, min(255, hval))
            px_r[x, y] = max(0, min(255, rval))

    h_img = h_img.filter(ImageFilter.GaussianBlur(radius=0.8))
    col_img.save(os.path.join(TEXTURE_DIR, "carbon_weave_color.png"))
    h_img.save(os.path.join(TEXTURE_DIR, "carbon_weave_height.png"))
    r_img.save(os.path.join(TEXTURE_DIR, "carbon_weave_rough.png"))
    print("Generated carbon_weave_{color,height,rough}.png")


def draw_curved_text(canvas, text, center, radius, start_angle_deg, step_deg, font, fill=245):
    """Draw bold typography along a circular arc for authentic tire sidewall markings."""
    cx, cy = center
    angle = start_angle_deg
    for ch in text:
        if ch != " ":
            glyph = Image.new("L", (140, 140), 0)
            gd = ImageDraw.Draw(glyph)
            bbox = gd.textbbox((0, 0), ch, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            gd.text((70 - tw // 2, 70 - th // 2), ch, font=font, fill=fill)
            rot = glyph.rotate(-angle - 90, resample=Image.BICUBIC, expand=False)
            rad = math.radians(angle)
            px = int(cx + radius * math.cos(rad) - 70)
            py = int(cy + radius * math.sin(rad) - 70)
            # Composite max
            region = canvas.crop((px, py, px + 140, py + 140))
            from PIL import ImageChops
            canvas.paste(ImageChops.lighter(region, rot), (px, py))
        angle += step_deg


def generate_tire_sidewall(filename_prefix, size_label):
    """
    Generate 2048x2048 Michelin Pilot Sport 4S radial tire sidewall bump & velvet roughness maps.
    Includes iconic Michelin checkered velvet ring segments, concentric molding ribs,
    and crisp raised sidewall lettering (MICHELIN / PILOT SPORT 4S / size).
    """
    S = 2048
    cx, cy = S // 2, S // 2
    bump = Image.new("L", (S, S), 115)
    velvet = Image.new("L", (S, S), 165)  # higher = rougher satin rubber; lower = dark velvet micro-texture
    bd = ImageDraw.Draw(bump)
    vd = ImageDraw.Draw(velvet)

    # Normalized radii: rim bead at r=0.735*R_max, tire outer shoulder at r=0.985*R_max
    R = S * 0.5
    r_inner = int(R * 0.742)
    r_mid = int(R * 0.858)
    r_outer = int(R * 0.960)

    # Concentric sidewall molding rings (bead ridge + shoulder ring)
    for rf, col, w in [(0.750, 175, 10), (0.768, 95, 5), (0.938, 170, 8), (0.955, 90, 5)]:
        rr = int(R * rf)
        bd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col, width=w)

    # Iconic Michelin Pilot Sport 4S checkered velvet bands (placed cleanly in gaps between lettering!)
    for arc_start, arc_len in [(28, 32), (116, 24), (212, 32), (306, 26)]:
        for a_step in range(0, arc_len, 2):
            ang = math.radians(arc_start + a_step)
            for ring_i in range(4):
                r0 = R * (0.812 + ring_i * 0.024)
                r1 = r0 + R * 0.020
                is_dark = ((a_step // 2) + ring_i) % 2 == 0
                c_b = 148 if is_dark else 108
                c_v = 235 if is_dark else 145
                x0, y0 = cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)
                x1, y1 = cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)
                bd.line([(x0, y0), (x1, y1)], fill=c_b, width=10)
                vd.line([(x0, y0), (x1, y1)], fill=c_v, width=10)

    # Radial fine shoulder sipes near outer rim of sidewall
    for deg in range(0, 360, 3):
        ang = math.radians(deg)
        x0, y0 = cx + R * 0.945 * math.cos(ang), cy + R * 0.945 * math.sin(ang)
        x1, y1 = cx + R * 0.990 * math.cos(ang), cy + R * 0.990 * math.sin(ang)
        bd.line([(x0, y0), (x1, y1)], fill=80, width=4)

    # Raised bold sidewall typography
    f_big = load_font(76, bold=True)
    f_med = load_font(56, bold=True)
    f_sm = load_font(40, bold=False)

    draw_curved_text(bump, "MICHELIN", (cx, cy), r_mid, -22, 5.4, f_big, fill=242)
    draw_curved_text(bump, "PILOT SPORT 4S", (cx, cy), r_mid, 146, 4.3, f_med, fill=236)
    draw_curved_text(bump, size_label, (cx, cy), r_mid, 68, 3.6, f_sm, fill=224)
    draw_curved_text(bump, "EXTRA LOAD   T0", (cx, cy), r_mid, 250, 3.3, f_sm, fill=215)

    # Velvet highlight behind main brand text
    draw_curved_text(velvet, "MICHELIN", (cx, cy), r_mid, -22, 5.4, f_big, fill=95)
    draw_curved_text(velvet, "PILOT SPORT 4S", (cx, cy), r_mid, 146, 4.3, f_med, fill=100)

    bump = bump.filter(ImageFilter.GaussianBlur(radius=1.0))
    bump.save(os.path.join(TEXTURE_DIR, f"{filename_prefix}_bump.png"))
    velvet.save(os.path.join(TEXTURE_DIR, f"{filename_prefix}_rough.png"))
    print(f"Generated {filename_prefix}_{{bump,rough}}.png")


def generate_brake_rotor_texture():
    """Generate 1024x1024 radial brushed cast-iron brake disc sweep texture."""
    S = 1024
    cx, cy = S // 2, S // 2
    img = Image.new("L", (S, S), 145)
    draw = ImageDraw.Draw(img)

    # Concentric fine brake pad wear grooves
    import random
    rng = random.Random(42)
    for r in range(180, 510, 2):
        val = int(128 + 38 * math.sin(r * 0.37) + rng.randint(-18, 18))
        val = max(65, min(225, val))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=val, width=2)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img.save(os.path.join(TEXTURE_DIR, "brake_rotor_radial.png"))
    print("Generated brake_rotor_radial.png")


def generate_caliper_logo():
    """Generate crisp white T E S L A caliper decal texture (transparent background)."""
    w, h = 1024, 256
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(120, bold=True)
    text = "T E S L A"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2 - 12), text, font=font, fill=(248, 248, 250, 255))
    img.save(os.path.join(TEXTURE_DIR, "caliper_tesla.png"))
    print("Generated caliper_tesla.png")


def generate_tesla_screens():
    """Generate authentic dark-mode Tesla Model S Plaid UI textures for all 3 screens."""
    # 1. Center 17" Touchscreen (1920x1080)
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (16, 18, 22))
    d = ImageDraw.Draw(img)

    # Left vehicle status pane (x: 0..620)
    d.rectangle([0, 0, 620, h - 100], fill=(22, 24, 30))
    # Subtle garage floor glow & red Model S top/3-4 silhouette card
    d.ellipse([120, 380, 500, 680], fill=(40, 22, 26))
    d.rounded_rectangle([185, 340, 435, 670], radius=95, fill=(145, 16, 22), outline=(220, 50, 55), width=3)
    d.rounded_rectangle([215, 420, 405, 585], radius=45, fill=(18, 22, 28))  # Glass roof
    f_lg = load_font(62, bold=True)
    f_md = load_font(34, bold=False)
    f_sm = load_font(26, bold=False)
    d.text((38, 32), "P", font=f_lg, fill=(245, 248, 252))
    d.text((100, 50), "R   N   D", font=f_md, fill=(95, 102, 115))
    d.text((430, 48), "94%", font=f_md, fill=(235, 240, 245))
    d.rounded_rectangle([518, 56, 582, 82], radius=5, outline=(180, 188, 198), width=3)
    d.rectangle([523, 61, 574, 77], fill=(64, 210, 102))
    d.text((160, 730), "MODEL S PLAID", font=f_md, fill=(215, 220, 228))
    d.text((225, 778), "Track Mode Ready", font=f_sm, fill=(215, 52, 56))

    # Right dark-mode navigation map pane (x: 622..1920)
    d.rectangle([622, 0, w, h - 100], fill=(24, 28, 36))
    # Clean dark map roads & bay coastline
    d.polygon([(1480, 0), (1920, 0), (1920, 980), (1620, 980), (1540, 620)], fill=(18, 32, 48))
    for rx in range(660, 1600, 110):
        d.line([(rx, 0), (rx + 60, 980)], fill=(38, 44, 56), width=5)
    for ry in range(70, 960, 95):
        d.line([(622, ry), (1680, ry + 35)], fill=(38, 44, 56), width=5)
    # Major highway + blue navigation route
    d.line([(720, 960), (980, 620), (1180, 410), (1440, 110)], fill=(58, 68, 86), width=16)
    d.line([(980, 620), (1180, 410), (1320, 240)], fill=(45, 138, 255), width=11)
    # Car blue navigation arrow
    d.polygon([(980, 585), (1002, 640), (980, 626), (958, 640)], fill=(70, 165, 255))
    # Search card
    d.rounded_rectangle([660, 32, 1060, 96], radius=14, fill=(32, 36, 46), outline=(55, 62, 76), width=2)
    d.text((688, 48), "Navigate", font=f_md, fill=(175, 184, 198))

    # Bottom dock bar
    d.rectangle([0, h - 100, w, h], fill=(12, 14, 18))
    d.text((760, h - 72), "68°", font=load_font(44, bold=True), fill=(240, 244, 248))
    d.text((1110, h - 72), "68°", font=load_font(44, bold=True), fill=(240, 244, 248))
    d.text((925, h - 66), "AUTO", font=f_sm, fill=(130, 140, 155))
    # App icons in dock
    for idx, col in enumerate([(225, 45, 50), (50, 185, 90), (55, 135, 245), (245, 165, 35), (160, 85, 230)]):
        bx = 320 + idx * 74
        d.rounded_rectangle([bx, h - 76, bx + 48, h - 28], radius=10, fill=col)

    img.save(os.path.join(TEXTURE_DIR, "screen_center_ui.png"))

    # 2. Driver 12.3" Instrument Cluster (1920x720)
    cw, ch = 1920, 720
    cimg = Image.new("RGB", (cw, ch), (12, 14, 18))
    cd = ImageDraw.Draw(cimg)
    # Center Autopilot road lanes
    cd.polygon([(700, 720), (885, 260), (1035, 260), (1220, 720)], fill=(22, 26, 34))
    cd.line([(700, 720), (885, 260)], fill=(55, 145, 255), width=7)
    cd.line([(1220, 720), (1035, 260)], fill=(55, 145, 255), width=7)
    # Red Plaid silhouette on cluster road
    cd.rounded_rectangle([895, 470, 1025, 650], radius=38, fill=(155, 18, 24), outline=(220, 50, 55), width=3)
    # Speed readout
    cd.text((915, 70), "0", font=load_font(128, bold=True), fill=(246, 248, 252))
    cd.text((930, 206), "MPH", font=load_font(30, bold=False), fill=(130, 138, 152))
    # Left range & battery
    cd.text((120, 110), "328 mi", font=load_font(48, bold=True), fill=(235, 240, 248))
    cd.rounded_rectangle([120, 180, 260, 212], radius=6, outline=(160, 168, 180), width=3)
    cd.rectangle([126, 186, 248, 206], fill=(56, 212, 100))
    # Right power meter & gear
    cd.text((1600, 110), "PLAID", font=load_font(44, bold=True), fill=(220, 42, 46))
    cd.text((1620, 175), "P  R  N  D", font=load_font(34, bold=False), fill=(150, 158, 172))
    cimg.save(os.path.join(TEXTURE_DIR, "screen_cluster_ui.png"))

    # 3. Rear 9.4" Touchscreen (1280x720)
    rw, rh = 1280, 720
    rimg = Image.new("RGB", (rw, rh), (16, 18, 24))
    rd = ImageDraw.Draw(rimg)
    rd.rounded_rectangle([60, 60, rw - 60, rh - 140], radius=24, fill=(24, 28, 38))
    rd.text((430, 260), "MODEL S PLAID", font=load_font(54, bold=True), fill=(230, 235, 242))
    rd.text((540, 340), "68°  AUTO", font=load_font(40, bold=False), fill=(120, 170, 245))
    rimg.save(os.path.join(TEXTURE_DIR, "screen_rear_ui.png"))
    print("Generated screen_{center,cluster,rear}_ui.png")


def generate_all():
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    generate_plaid_badge()
    generate_carbon_fiber_weave()
    generate_tire_sidewall("tire_sidewall_front", "265/35 ZR 21")
    generate_tire_sidewall("tire_sidewall_rear", "295/30 ZR 21")
    generate_brake_rotor_texture()
    generate_caliper_logo()
    generate_tesla_screens()


if __name__ == "__main__":
    generate_all()
