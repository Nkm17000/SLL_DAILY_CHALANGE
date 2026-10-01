import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / CFG["content_file"]).read_text(encoding="utf-8"))
THEMES = json.loads((ROOT / CFG.get("themes_file", "themes.json")).read_text(encoding="utf-8"))["themes"]

FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def font(size, bold=False):
    for path in (FONT_BOLD if bold else FONT_REG):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgba(value, alpha=255):
    return (*rgb(value), alpha)


def blend(a, b, amount):
    ar, ag, ab = rgb(a)
    br, bg, bb = rgb(b)
    return "#%02X%02X%02X" % (
        int(ar + (br - ar) * amount),
        int(ag + (bg - ag) * amount),
        int(ab + (bb - ab) * amount),
    )


def text_width(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0]


def wrap(draw, text, f, max_width):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if text_width(draw, candidate, f) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def rounded_gradient(im, box, top, bottom, radius):
    x1, y1, x2, y2 = box
    layer = Image.new("RGB", (x2 - x1, y2 - y1), top)
    ld = ImageDraw.Draw(layer)
    c1, c2 = rgb(top), rgb(bottom)
    h = max(1, y2 - y1)
    for y in range(h):
        t = y / (h - 1) if h > 1 else 0
        col = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        ld.line((0, y, layer.width, y), fill=col)
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, layer.width, layer.height), radius=radius, fill=255)
    im.paste(layer, (x1, y1), mask)


def shadowed_roundrect(im, box, radius, fill, outline=None, width=1, shadow=(0, 10, 30, 34)):
    x1, y1, x2, y2 = box
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ox, oy, blur, alpha = shadow
    ld.rounded_rectangle((x1 + ox, y1 + oy, x2 + ox, y2 + oy), radius=radius, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_stopwatch(d, cx, cy, r, color):
    c = rgb(color)
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*c, 255), outline=(255, 255, 255, 225), width=max(3, r // 12))
    d.ellipse((cx-r+18, cy-r+18, cx+r-18, cy+r-18), fill=(255, 255, 255, 245))
    d.line((cx, cy, cx-r//3, cy-r//3), fill=(*c, 255), width=max(5, r//12))
    d.line((cx, cy, cx+r//3, cy+r//5), fill=(*c, 255), width=max(5, r//12))
    d.ellipse((cx-8, cy-8, cx+8, cy+8), fill=(*c, 255))
    d.rounded_rectangle((cx-28, cy-r-30, cx+28, cy-r-8), radius=8, fill=(*c, 255))
    d.line((cx+r//2, cy-r//2, cx+r//2+18, cy-r//2-18), fill=(*c, 255), width=8)


def draw_lightbulb(d, cx, cy, r, color, glow):
    c = rgb(color)
    gc = rgb(glow)
    for extra, alpha in [(35, 25), (22, 45), (10, 70)]:
        d.ellipse((cx-r-extra, cy-r-extra, cx+r+extra, cy+r+extra), fill=(*gc, alpha))
    d.ellipse((cx-r, cy-r, cx+r, cy+r+18), fill=(*c, 245), outline=(255, 255, 255, 200), width=4)
    d.rectangle((cx-r//2, cy+r-2, cx+r//2, cy+r+28), fill=(*c, 255))
    d.line((cx-r//3, cy+r+10, cx+r//3, cy+r+10), fill=(255, 255, 255, 210), width=4)
    d.line((cx-r//3, cy+r+20, cx+r//3, cy+r+20), fill=(255, 255, 255, 210), width=4)


def draw_calculator(d, x, y, w, h, color, dark):
    d.rounded_rectangle((x, y, x+w, y+h), radius=22, fill=rgb(color), outline=(255, 255, 255, 180), width=4)
    d.rounded_rectangle((x+22, y+22, x+w-22, y+86), radius=12, fill=rgb(dark))
    for row in range(3):
        for col in range(3):
            xx = x + 28 + col * 48
            yy = y + 112 + row * 48
            d.rounded_rectangle((xx, yy, xx+30, yy+30), radius=8, fill=rgb(dark))


def draw_pi(d, cx, cy, size, color):
    f = font(size, True)
    d.text((cx, cy), "π", font=f, fill=rgb(color), anchor="mm")


def add_background(im, theme, W, H):
    d = ImageDraw.Draw(im, "RGBA")
    # Large soft blobs make each theme feel like a distinct campaign, not just a recolor.
    for cx, cy, r, col, alpha in theme.get("blobs", []):
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*rgb(col), alpha))
    # Fine dot field.
    dot = rgb(theme["accent"])
    for row in range(7):
        for col in range(8):
            x = W - 320 + col * 32
            y = 250 + row * 32
            if x < W - 45 and y < 540:
                d.ellipse((x, y, x+7, y+7), fill=(*dot, 55))
    # Corner arcs.
    for i in range(3):
        r = 190 + i * 28
        d.arc((W-r-90, H-r-60, W+90, H+60), 175, 270, fill=(*rgb(theme["accent2"]), 38), width=5)


def draw_badge(d, box, text, fill, fg, outline=None, f=None):
    f = f or font(21, True)
    d.rounded_rectangle(box, radius=(box[3]-box[1])//2, fill=rgb(fill), outline=rgb(outline) if outline else None, width=3 if outline else 1)
    tw = text_width(d, text, f)
    d.text(((box[0]+box[2]-tw)/2, box[1] + (box[3]-box[1]-f.size)//2 - 4), text, font=f, fill=rgb(fg))


def render(c):
    W, H = CFG["image"]["width"], CFG["image"]["height"]
    post_number = int(c.get("post_number", 1))
    idx = (post_number - 1) % len(THEMES)
    theme = dict(THEMES[idx])
    theme["theme_number"] = idx + 1

    im = Image.new("RGBA", (W, H), rgb(theme["background"]) + (255,))
    add_background(im, theme, W, H)
    d = ImageDraw.Draw(im, "RGBA")

    # Main canvas / frame.
    M = 58
    d.rounded_rectangle((M, M, W-M, H-M), radius=42, fill=rgb(theme["canvas"]), outline=(*rgb(theme["border"]), 255), width=5)

    L, R = 105, W-105
    content_w = R-L

    brand = font(34, True)
    micro = font(18, True)
    small = font(23, True)
    body = font(26, False)
    title = font(49, True)
    hero_big = font(126, True)
    hero_word = font(54, True)
    question_font = font(53, True)
    option_font = font(34, True)
    stat_value = font(34, True)
    footer = font(21, True)

    # Brand header.
    d.text((L, 94), "SMART LEARNING LAB", font=brand, fill=rgb(theme["ink"]))
    d.text((L, 139), "L E A R N   •   P R A C T I C E   •   G R O W", font=micro, fill=rgb(theme["accent"]))

    # Daily Challenge script-like lockup using italic-ish slant via a small dark panel.
    daily_x = W - 420
    d.text((daily_x, 90), "Daily", font=font(64, False), fill=rgb(theme["hero"]))
    d.text((daily_x+8, 150), "Challenge", font=font(56, True), fill=rgb(theme["hero"]))
    d.line((daily_x+8, 216, daily_x+250, 216), fill=rgb(theme["hero"]), width=7)

    # Hero banner.
    hero_y = 245
    hero_h = 245
    shadowed_roundrect(im, (L+105, hero_y+8, R-30, hero_y+hero_h+8), 62, (*rgb(theme["hero"]), 255), shadow=(0, 18, 32, 48))
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((L+75, hero_y+28, R-55, hero_y+hero_h-20), radius=58, fill=(*rgb(theme["hero2"]), 255))
    d.rounded_rectangle((L+105, hero_y, R-30, hero_y+hero_h-28), radius=62, fill=(*rgb(theme["hero"]), 255))

    secs = int(c.get("time_limit_seconds", 15))
    draw_stopwatch(d, L+135, hero_y+122, 72, theme["hero_dark"])
    d.text((L+225, hero_y+42), str(secs), font=hero_big, fill=rgb(theme["hero_text"]))
    d.text((L+420, hero_y+75), "SECOND", font=hero_word, fill=rgb(theme["hero_text"]))
    d.text((L+420, hero_y+132), "CHALLENGE", font=hero_word, fill=rgb(theme["highlight"]))

    # Hook ribbon.
    hook = str(c.get("hook", "No searching. Your turn."))
    hook_text = hook if len(hook) <= 44 else hook[:41] + "..."
    ribbon_y = hero_y + 205
    d.rounded_rectangle((L+420, ribbon_y, R-150, ribbon_y+72), radius=34, fill=rgb(theme["ribbon"]))
    d.text((L+455, ribbon_y+17), hook_text, font=font(25, False), fill=rgb(theme["ribbon_text"]))

    # Challenge + category pills.
    pill_y = 535
    draw_badge(d, (L, pill_y, L+390, pill_y+62), f"DAILY CHALLENGE   #{post_number:04d}", theme["canvas"], theme["hero"], theme["border"], small)
    category = str(c.get("category", "challenge")).replace("_", " ").upper()
    cat_text = category[:14]
    draw_badge(d, (R-270, pill_y, R, pill_y+62), cat_text, theme["hero"], theme["hero_text"], None, small)

    # Title.
    y = 640
    title_lines = wrap(d, c["title"], title, content_w)
    for line in title_lines[:2]:
        d.text((L, y), line, font=title, fill=rgb(theme["ink"]))
        y += 60
    d.rounded_rectangle((L, y+10, L+130, y+18), radius=4, fill=rgb(theme["hero"]))
    d.rounded_rectangle((L+142, y+10, L+190, y+18), radius=4, fill=rgb(theme["accent2"]))
    y += 44

    # Question card.
    q_top = y
    q_lines = wrap(d, c["question"], question_font, content_w-100)
    q_h = max(175, 92 + len(q_lines)*62)
    shadowed_roundrect(im, (L, q_top, R, q_top+q_h), 32, (*rgb(theme["question_bg"]), 255), outline=(*rgb(theme["border"]), 185), width=3, shadow=(0, 10, 25, 25))
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((L+42, q_top+30, L+235, q_top+78), radius=24, fill=rgb(theme["question_label"]))
    d.text((L+67, q_top+40), "QUESTION", font=micro, fill=rgb(theme["ink"]))
    qy = q_top + 88
    for line in q_lines:
        d.text((L+42, qy), line, font=question_font, fill=rgb(theme["ink"]))
        qy += 62
    # Watermark question mark.
    d.text((R-135, q_top+38), "?", font=font(150, True), fill=(*rgb(theme["hero"]), 24))

    # Options: two-column premium tiles.
    y = q_top + q_h + 28
    gap = 22
    col_w = (content_w-gap)//2
    option_h = 112
    keys = list(c["options"].items())[:4]
    for i, (key, value) in enumerate(keys):
        row, col = divmod(i, 2)
        x = L + col*(col_w+gap)
        yy = y + row*(option_h+gap)
        shadowed_roundrect(im, (x, yy, x+col_w, yy+option_h), 32, (*rgb(theme["option_bg"]), 255), outline=(*rgb(theme["border"]), 185), width=3, shadow=(0, 7, 20, 22))
        d = ImageDraw.Draw(im, "RGBA")
        d.ellipse((x+26, yy+25, x+88, yy+87), fill=rgb(theme["hero"]))
        d.text((x+57, yy+35), key, font=small, fill=rgb(theme["hero_text"]), anchor="mm")
        d.text((x+120, yy+34), str(value), font=option_font, fill=rgb(theme["ink"]))

    # Stats strip.
    stats_y = y + 2*(option_h+gap) + 28
    shadowed_roundrect(im, (L, stats_y, R, stats_y+122), 30, (*rgb(theme["stats_bg"]), 255), outline=(*rgb(theme["border"]), 120), width=2, shadow=(0, 7, 18, 18))
    d = ImageDraw.Draw(im, "RGBA")
    # Hourglass / bars icon.
    d.text((L+38, stats_y+27), "TIME LIMIT", font=small, fill=rgb(theme["muted"]))
    d.text((L+38, stats_y+65), f"{secs} SECONDS", font=stat_value, fill=rgb(theme["hero"]))
    d.line((W//2, stats_y+28, W//2, stats_y+94), fill=(*rgb(theme["border"]), 160), width=3)
    difficulty = str(c.get("difficulty", "Challenge")).upper()
    d.text((W//2+65, stats_y+27), "DIFFICULTY", font=small, fill=rgb(theme["muted"]))
    d.text((W//2+65, stats_y+65), difficulty, font=stat_value, fill=rgb(theme["hero"]))

    # CTA strip.
    cta_y = stats_y + 150
    d.rounded_rectangle((L, cta_y, R, cta_y+105), radius=34, fill=rgb(theme["cta"]))
    third = content_w/3
    items = [("COMMENT", "YOUR ANSWER"), ("TAG A FRIEND", ""), ("SHARE", "")]
    for i, (a, b) in enumerate(items):
        x = L + i*third + 36
        if i:
            d.line((L+i*third, cta_y+25, L+i*third, cta_y+80), fill=(255,255,255,160), width=2)
        d.ellipse((x, cta_y+27, x+48, cta_y+75), fill=(255,255,255,235))
        d.text((x+24, cta_y+51), ["…", "•", "→"][i], font=font(30, True), fill=rgb(theme["cta"]) , anchor="mm")
        d.text((x+65, cta_y+23), a, font=small, fill=rgb(theme["cta_text"]))
        if b:
            d.text((x+65, cta_y+51), b, font=small, fill=rgb(theme["cta_text"]))

    # Lower campaign area: keep the feed card visually full without crowding the challenge.
    rule_y = 1490
    d.rounded_rectangle((L, rule_y, R, rule_y+92), radius=28, fill=rgb(theme["stats_bg"]), outline=(*rgb(theme["border"]), 95), width=2)
    d.text((L+30, rule_y+18), "THE DAILY RULE", font=micro, fill=rgb(theme["hero"]))
    d.text((L+30, rule_y+48), "Think first  •  Solve fast  •  Comment your answer", font=small, fill=rgb(theme["ink"]))

    # Decorative mini illustrations inspired by the uploaded reference.
    base_y = 1640
    d.text((L+455, base_y), "Small", font=font(38, False), fill=rgb(theme["ink"]))
    d.text((L+455, base_y+42), "Questions", font=font(38, True), fill=rgb(theme["hero"]))
    d.text((L+455, base_y+84), "Big Progress", font=font(38, True), fill=rgb(theme["ink"]))
    draw_calculator(d, L+5, 1605, 175, 175, theme["hero"], theme["hero_dark"])
    draw_lightbulb(d, R-100, 1690, 55, theme["highlight"], theme["accent2"])
    draw_pi(d, R-270, 1695, 105, theme["accent2"])

    # Bottom edge details.
    d.line((L+300, 1850, R-300, 1850), fill=(*rgb(theme["border"]), 90), width=2)
    d.text((L+420, 1870), "LEARN  •  PRACTICE  •  GROW", font=small, fill=rgb(theme["accent"]))
    theme_label = f"THEME {theme['theme_number']}/10  •  {theme['name'].upper()}"
    d.text((R-360, H-68), theme_label, font=micro, fill=rgb(theme["muted"]))

    out_dir = ROOT / CFG["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{c['id']}.png"
    im.convert("RGB").save(out, format="PNG", optimize=True)
    return out, theme


def make_caption(c, theme):
    tags = " ".join(c.get("hashtags", [])) if CFG["caption"].get("include_hashtags", True) else ""
    return (
        f"{c['hook']}\n\n{c['question']}\n\n"
        f"A. {c['options']['A']}\nB. {c['options']['B']}\nC. {c['options']['C']}\nD. {c['options']['D']}\n\n"
        f"⏱ {c['time_limit_seconds']} seconds | {c['difficulty']}\n"
        f"{c['cta']}\n\n{tags}\n\n#Theme{theme['theme_number']}"
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
        start = max(0, (args.index or 1) - 1)
        chosen = DATA["challenges"][start:start + args.count]

    for c in chosen:
        out, theme = render(c)
        caption = make_caption(c, theme)
        cap_path = out.with_suffix(".txt")
        cap_path.write_text(caption, encoding="utf-8")
        print(f"Generated {out} using Theme {theme['theme_number']}: {theme['name']}")


if __name__ == "__main__":
    main()
