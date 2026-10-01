import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / CFG["content_file"]).read_text(encoding="utf-8"))
THEMES = json.loads((ROOT / CFG.get("themes_file", "themes.json")).read_text(encoding="utf-8"))["themes"]


def font(size, bold=False, italic=False):
    candidates = []
    if italic:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "C:/Windows/Fonts/ariali.ttf",
        ]
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgba(hex_color, alpha=255):
    return (*hex_to_rgb(hex_color), alpha)


def blend(a, b, amount):
    ar, ag, ab = hex_to_rgb(a)
    br, bg, bb = hex_to_rgb(b)
    return "#%02X%02X%02X" % (
        int(ar + (br - ar) * amount),
        int(ag + (bg - ag) * amount),
        int(ab + (bb - ab) * amount),
    )


def wrap(draw, text, f, max_width):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=f)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def text_fit(draw, text, max_width, start_size, minimum=20, bold=True):
    size = start_size
    while size > minimum:
        f = font(size, bold=bold)
        if draw.textbbox((0, 0), str(text), font=f)[2] <= max_width:
            return f
        size -= 2
    return font(minimum, bold=bold)


def rounded_card(im, box, fill, outline=None, radius=30, width=2, shadow=False):
    x1, y1, x2, y2 = box
    if shadow:
        shadow_layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=radius, fill=(0, 0, 0, 42))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(9))
        im.alpha_composite(shadow_layer)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_book_logo(d, x, y, scale, theme):
    # Simple vector book/cap mark; no external assets required.
    navy = rgba(theme["dark"])
    accent = rgba(theme["accent"])
    accent2 = rgba(theme["accent2"])
    w = int(58 * scale)
    h = int(46 * scale)
    d.polygon([(x, y + 8 * scale), (x + w / 2, y), (x + w, y + 8 * scale), (x + w, y + h), (x + w / 2, y + h - 7 * scale), (x, y + h)], fill=navy)
    d.polygon([(x + 6 * scale, y + 13 * scale), (x + w / 2 - 2 * scale, y + 8 * scale), (x + w / 2 - 2 * scale, y + h - 12 * scale), (x + 6 * scale, y + h - 8 * scale)], fill=accent)
    d.polygon([(x + w - 6 * scale, y + 13 * scale), (x + w / 2 + 2 * scale, y + 8 * scale), (x + w / 2 + 2 * scale, y + h - 12 * scale), (x + w - 6 * scale, y + h - 8 * scale)], fill=accent2)
    d.polygon([(x + w / 2 - 17 * scale, y - 8 * scale), (x + w / 2 + 17 * scale, y - 8 * scale), (x + w / 2, y - 20 * scale)], fill=navy)


def draw_stopwatch(d, cx, cy, r, theme):
    accent = rgba(theme["accent"])
    dark = rgba(theme["dark"])
    white = rgba("#FFFFFF")
    d.rounded_rectangle((cx - r * .16, cy - r * 1.18, cx + r * .16, cy - r * .82), radius=int(r * .08), fill=dark)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=accent, outline=dark, width=max(2, int(r * .06)))
    d.ellipse((cx - r * .72, cy - r * .72, cx + r * .72, cy + r * .72), fill=white)
    import math
    for deg in range(0, 360, 45):
        rad = math.radians(deg - 90)
        x1 = cx + math.cos(rad) * r * .55
        y1 = cy + math.sin(rad) * r * .55
        x2 = cx + math.cos(rad) * r * .65
        y2 = cy + math.sin(rad) * r * .65
        d.line((x1, y1, x2, y2), fill=accent, width=max(2, int(r * .045)))
    d.line((cx, cy, cx + r * .22, cy - r * .32), fill=dark, width=max(3, int(r * .07)))
    d.line((cx, cy, cx - r * .08, cy + r * .16), fill=dark, width=max(3, int(r * .07)))
    d.ellipse((cx - r * .08, cy - r * .08, cx + r * .08, cy + r * .08), fill=dark)


def draw_calculator(d, x, y, w, h, theme, angle=0):
    # Draw on a small transparent canvas then rotate for a playful editorial accent.
    layer = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    dark = rgba(theme["dark"])
    accent = rgba(theme["accent"])
    accent2 = rgba(theme["accent2"])
    ld.rounded_rectangle((15, 15, w + 15, h + 15), radius=20, fill=dark)
    ld.rounded_rectangle((30, 30, w, 72), radius=10, fill=rgba("#FFFFFF"))
    for row in range(3):
        for col in range(3):
            bx = 30 + col * ((w - 55) / 3)
            by = 88 + row * 42
            bw = (w - 65) / 3
            ld.rounded_rectangle((bx, by, bx + bw, by + 28), radius=6, fill=accent if (row + col) % 2 == 0 else accent2)
    layer = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    base.alpha_composite(layer)
    return base, (x - 15, y - 15)


def draw_lightbulb(d, cx, cy, r, theme):
    gold = rgba(theme["accent2"])
    dark = rgba(theme["dark"])
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=gold, outline=dark, width=max(2, int(r * .06)))
    d.arc((cx - r * .62, cy - r * .48, cx + r * .62, cy + r * .75), 190, 350, fill=dark, width=max(3, int(r * .08)))
    d.line((cx - r * .25, cy + r * .72, cx + r * .25, cy + r * .72), fill=dark, width=max(3, int(r * .08)))
    d.line((cx - r * .2, cy + r * .86, cx + r * .2, cy + r * .86), fill=dark, width=max(3, int(r * .08)))


def draw_pi(d, x, y, size, theme):
    f = font(size, True)
    d.text((x, y), "π", font=f, fill=rgba(theme["accent"]))


def draw_hero_badge(d, x, y, w, h, theme):
    # Large rounded hero plaque behind 15 SECOND CHALLENGE.
    d.rounded_rectangle((x, y, x + w, y + h), radius=48, fill=rgba(theme["accent"], 245))
    d.rounded_rectangle((x + 26, y + 22, x + w - 18, y + h + 12), radius=48, fill=rgba(theme["dark"], 255))
    d.rounded_rectangle((x + 18, y + 10, x + w - 30, y + h - 6), radius=48, fill=rgba(theme["accent"], 235))


def render(c):
    W, H = CFG["image"]["width"], CFG["image"]["height"]
    post_number = int(c.get("post_number", 1))
    theme = dict(THEMES[(post_number - 1) % len(THEMES)])
    theme["theme_number"] = ((post_number - 1) % len(THEMES)) + 1

    im = Image.new("RGBA", (W, H), rgba(theme["background"]))
    d = ImageDraw.Draw(im)

    # Soft background blobs / confetti.
    for cx, cy, r, color, alpha in [
        (0, 180, 155, theme["accent"], 42),
        (W, 70, 175, theme["accent2"], 34),
        (W + 30, H - 260, 220, theme["accent"], 32),
        (-30, H - 100, 210, theme["accent2"], 26),
    ]:
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=rgba(color, alpha))

    margin = 60
    # Main page frame.
    rounded_card(im, (margin, 24, W - margin, H - 24), rgba(theme["surface"]), outline=rgba(theme["border"]), radius=44, width=3, shadow=True)
    d = ImageDraw.Draw(im)
    left, right = 105, W - 105

    # Header.
    draw_book_logo(d, left, 70, 1.15, theme)
    brand_f = font(38, True)
    sub_f = font(18, True)
    d.text((left + 78, 72), "SMART LEARNING LAB", font=brand_f, fill=rgba(theme["text"]))
    d.text((left + 78, 116), "L E A R N   •   P R A C T I C E   •   G R O W", font=sub_f, fill=rgba(theme["accent"]))

    daily_f = font(58, True, italic=True)
    d.text((W - 470, 54), "Daily", font=daily_f, fill=rgba(theme["accent"]))
    d.text((W - 425, 108), "Challenge", font=daily_f, fill=rgba(theme["accent"]))
    d.arc((W - 430, 147, W - 185, 205), 10, 165, fill=rgba(theme["accent"]), width=5)

    # Hero.
    hero_x, hero_y, hero_w, hero_h = 265, 215, 1065, 205
    draw_hero_badge(d, hero_x, hero_y, hero_w, hero_h, theme)
    draw_stopwatch(d, 185, 315, 94, theme)
    f15 = font(155, True)
    d.text((hero_x + 60, hero_y + 20), "15", font=f15, fill=rgba("#FFFFFF"))
    second_f = font(70, True)
    challenge_f = font(70, True)
    d.text((hero_x + 330, hero_y + 43), "SECOND", font=second_f, fill=rgba("#FFFFFF"))
    d.text((hero_x + 330, hero_y + 110), "CHALLENGE", font=challenge_f, fill=rgba(theme["accent2"]))
    # Hero tagline ribbon.
    d.rounded_rectangle((470, 390, 1090, 470), radius=38, fill=rgba(theme["dark"]))
    tagline_f = font(36, False, italic=True)
    d.text((520, 408), "No searching. Your turn!", font=tagline_f, fill=rgba("#FFFFFF"))
    d.line((890, 456, 1040, 456), fill=rgba(theme["accent"]), width=4)

    # Metadata row.
    meta_y = 500
    meta_f = font(24, True)
    draw_pill = lambda box, text, fill, tc: (d.rounded_rectangle(box, radius=28, fill=fill), d.text((box[0] + 28, box[1] + 13), text, font=meta_f, fill=tc))
    draw_pill((left, meta_y, left + 390, meta_y + 58), f"DAILY CHALLENGE   #{post_number:04d}", rgba("#FFFFFF"), rgba(theme["text"]))
    cat = str(c.get("category", "challenge")).replace("_", " ").upper()
    cat_w = 245
    draw_pill((right - cat_w, meta_y, right, meta_y + 58), f"▣  {cat[:14]}", rgba(theme["accent"]), rgba("#FFFFFF"))

    # Question card.
    q_y = 590
    q_box = (left, q_y, right, q_y + 250)
    rounded_card(im, q_box, rgba(theme["surface"]), outline=rgba(theme["border"]), radius=34, width=3, shadow=True)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((left + 38, q_y + 28, left + 280, q_y + 76), radius=24, fill=rgba(theme["soft"]))
    d.text((left + 60, q_y + 38), "Q U E S T I O N", font=font(21, True), fill=rgba(theme["accent"]))
    qf = text_fit(d, c["question"], right - left - 100, 60, minimum=34, bold=True)
    qlines = wrap(d, c["question"], qf, right - left - 90)
    qyy = q_y + 105
    for line in qlines[:2]:
        d.text((left + 48, qyy), line, font=qf, fill=rgba(theme["text"]))
        qyy += qf.size + 8
    draw_pi(d, right - 145, q_y + 80, 120, theme)

    # Options 2x2.
    option_top = 880
    gap_x, gap_y = 28, 24
    ow = (right - left - gap_x) // 2
    oh = 150
    option_f = text_fit(d, "999999999999999999", ow - 150, 42, minimum=28, bold=True)
    for idx, (key, value) in enumerate(c["options"].items()):
        row, col = divmod(idx, 2)
        x1 = left + col * (ow + gap_x)
        y1 = option_top + row * (oh + gap_y)
        x2 = x1 + ow
        y2 = y1 + oh
        rounded_card(im, (x1, y1, x2, y2), rgba(theme["surface"]), outline=rgba(theme["border"]), radius=30, width=3, shadow=True)
        d = ImageDraw.Draw(im)
        d.ellipse((x1 + 30, y1 + 34, x1 + 104, y1 + 108), fill=rgba(theme["accent"]))
        kf = font(40, True)
        kb = d.textbbox((0, 0), key, font=kf)
        d.text((x1 + 67 - (kb[2]-kb[0])/2, y1 + 45), key, font=kf, fill=rgba("#FFFFFF"))
        vf = text_fit(d, str(value), ow - 150, 43, minimum=27, bold=True)
        d.text((x1 + 132, y1 + 46), str(value), font=vf, fill=rgba(theme["text"]))

    # Info strip.
    info_y = 1260
    rounded_card(im, (left, info_y, right, info_y + 125), rgba(theme["surface"]), outline=rgba(theme["border"]), radius=32, width=3, shadow=True)
    d = ImageDraw.Draw(im)
    draw_stopwatch(d, left + 82, info_y + 62, 38, theme)
    d.text((left + 155, info_y + 25), "TIME LIMIT", font=font(25, True), fill=rgba(theme["text"]))
    d.text((left + 155, info_y + 63), f"{c['time_limit_seconds']} SECONDS", font=font(34, True), fill=rgba(theme["accent"]))
    d.line((W // 2, info_y + 28, W // 2, info_y + 98), fill=rgba(theme["border"]), width=3)
    # difficulty bars
    diff = str(c.get("difficulty", "MEDIUM")).upper()
    d.text((W // 2 + 95, info_y + 25), "DIFFICULTY", font=font(25, True), fill=rgba(theme["text"]))
    bars = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(diff, 2)
    for i in range(3):
        bx = W // 2 + 95 + i * 40
        by = info_y + 92 - (i + 1) * 17
        d.rounded_rectangle((bx, by, bx + 26, info_y + 92), radius=6, fill=rgba(theme["accent"] if i < bars else theme["soft"]))
    d.text((W // 2 + 235, info_y + 62), diff, font=font(34, True), fill=rgba(theme["accent"]))

    # CTA bar.
    cta_y = 1415
    rounded_card(im, (left, cta_y, right, cta_y + 112), rgba(theme["accent"]), radius=38, shadow=True)
    d = ImageDraw.Draw(im)
    cta_f = font(28, True)
    segments = [("●", "COMMENT\nYOUR ANSWER"), ("●", "TAG A FRIEND"), ("➜", "SHARE")]
    seg_w = (right - left) // 3
    for i, (icon, label) in enumerate(segments):
        cx = left + i * seg_w + seg_w // 2
        if i:
            d.line((left + i * seg_w, cta_y + 25, left + i * seg_w, cta_y + 87), fill=rgba("#FFFFFF", 150), width=2)
        if "\n" in label:
            l1, l2 = label.split("\n")
            d.text((cx - 115, cta_y + 23), icon, font=font(28, True), fill=rgba("#FFFFFF"))
            d.text((cx - 75, cta_y + 17), l1, font=cta_f, fill=rgba("#FFFFFF"))
            d.text((cx - 75, cta_y + 49), l2, font=cta_f, fill=rgba("#FFFFFF"))
        else:
            d.text((cx - 95, cta_y + 35), icon, font=font(34, True), fill=rgba("#FFFFFF"))
            d.text((cx - 48, cta_y + 38), label, font=cta_f, fill=rgba("#FFFFFF"))

    # Footer editorial line and illustrations.
    calc, calc_pos = draw_calculator(d, 65, 1585, 180, 240, theme, -8)
    im.alpha_composite(calc, calc_pos)
    d = ImageDraw.Draw(im)
    draw_lightbulb(d, W - 150, 1650, 65, theme)
    draw_pi(d, 300, 1640, 85, theme)
    quote_f = font(40, True, italic=True)
    d.text((560, 1600), "Small Questions", font=quote_f, fill=rgba(theme["text"]))
    d.text((590, 1650), "Big Progress", font=quote_f, fill=rgba(theme["text"]))
    d.line((650, 1710, 880, 1710), fill=rgba(theme["accent"]), width=5)
    note_f = font(27, True, italic=True)
    d.text((1040, 1605), "Practice", font=note_f, fill=rgba(theme["dark"]))
    d.text((1040, 1640), "Today", font=note_f, fill=rgba(theme["dark"]))
    d.text((1040, 1675), "Grow", font=note_f, fill=rgba(theme["dark"]))
    d.text((1040, 1710), "Tomorrow", font=note_f, fill=rgba(theme["accent"]))

    # Small QA label.
    label = f"THEME {theme['theme_number']}/10  •  {theme['name'].upper()}"
    lf = font(16, True)
    tb = d.textbbox((0, 0), label, font=lf)
    d.text((right - (tb[2] - tb[0]), H - 48), label, font=lf, fill=rgba(theme["muted"]))

    out_dir = ROOT / CFG["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (c["id"] + ".png")
    im.convert("RGB").save(out, format="PNG", optimize=True)
    return out, theme


def make_caption(c, theme):
    tags = " ".join(c["hashtags"]) if CFG["caption"]["include_hashtags"] else ""
    return (
        f"{c['hook']}\n\n"
        f"{c['question']}\n\n"
        f"A. {c['options']['A']}\n"
        f"B. {c['options']['B']}\n"
        f"C. {c['options']['C']}\n"
        f"D. {c['options']['D']}\n\n"
        f"⏱ {c['time_limit_seconds']} seconds  |  {c['difficulty']}\n"
        f"{c['cta']}\n\n"
        f"{tags}\n\n"
        f"#DailyChallenge #SmartLearningLab #Theme{theme['theme_number']}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int)
    ap.add_argument("--id")
    ap.add_argument("--count", type=int, default=1)
    args = ap.parse_args()

    if args.id:
        chosen = [x for x in DATA["challenges"] if x["id"] == args.id]
    else:
        idx = (args.index or 1) - 1
        chosen = DATA["challenges"][idx:idx + args.count]

    for challenge in chosen:
        path, theme = render(challenge)
        path.with_suffix(".txt").write_text(make_caption(challenge, theme), encoding="utf-8")
        print(f"Generated {path} using premium theme {theme['theme_number']}: {theme['name']}")


if __name__ == "__main__":
    main()
