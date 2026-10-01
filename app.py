import argparse
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / CFG["content_file"]).read_text(encoding="utf-8"))
THEMES = json.loads((ROOT / "themes.json").read_text(encoding="utf-8"))["themes"]


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


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


def rounded_gradient(im, box, top, bottom, radius):
    x1, y1, x2, y2 = box
    layer = Image.new("RGB", (x2 - x1, y2 - y1), top)
    px = layer.load()
    from_c = hex_to_rgb(top)
    to_c = hex_to_rgb(bottom)
    height = max(1, y2 - y1)
    for y in range(height):
        t = y / (height - 1) if height > 1 else 0
        col = tuple(int(from_c[i] * (1 - t) + to_c[i] * t) for i in range(3))
        ImageDraw.Draw(layer).line((0, y, x2 - x1, y), fill=col)
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, layer.width, layer.height), radius=radius, fill=255)
    im.paste(layer, (x1, y1), mask)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def blend(a, b, amount):
    ar, ag, ab = hex_to_rgb(a)
    br, bg, bb = hex_to_rgb(b)
    return "#%02X%02X%02X" % (
        int(ar + (br - ar) * amount),
        int(ag + (bg - ag) * amount),
        int(ab + (bb - ab) * amount),
    )


def add_decor(im, theme, W, H, margin):
    d = ImageDraw.Draw(im, "RGBA")
    accent = hex_to_rgb(theme["accent"])
    accent2 = hex_to_rgb(theme["accent2"])

    # Large, subtle watermark numerals.
    watermark = font(360, True)
    number = "%02d" % theme["theme_number"]
    d.text((W - margin - 430, 90), number, font=watermark, fill=(*accent, 18))

    # Decorative glow rings / blobs.
    for cx, cy, r, color, alpha in [
        (W - 120, 130, 210, accent, 24),
        (100, H - 160, 250, accent2, 18),
    ]:
        for width in (5, 3, 1):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*color, alpha), width=width)
            r -= 16

    # Small accent dots.
    for i in range(5):
        x = margin + 18 + i * 22
        d.ellipse((x, H - margin - 70, x + 8, H - margin - 62), fill=(*accent, 160 if i == 0 else 65))


def draw_pill(d, xy, text, fill, text_color, f, outline=None):
    x1, y1, x2, y2 = xy
    d.rounded_rectangle(xy, radius=(y2 - y1) // 2, fill=fill, outline=outline, width=2 if outline else 1)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((x1 + x2 - tw) / 2, (y1 + y2 - th) / 2 - 3), text, font=f, fill=text_color)


def render(c):
    W, H = CFG["image"]["width"], CFG["image"]["height"]
    margin = 70
    inner = 58

    # Consecutive challenges get consecutive themes. After theme 10, the cycle restarts.
    post_number = int(c.get("post_number", 1))
    theme = dict(THEMES[(post_number - 1) % len(THEMES)])
    theme["theme_number"] = ((post_number - 1) % len(THEMES)) + 1

    im = Image.new("RGB", (W, H), theme["background"])
    add_decor(im, theme, W, H, margin)
    d = ImageDraw.Draw(im)

    # Main premium card.
    card = (margin, margin, W - margin, H - margin)
    rounded_gradient(im, card, theme["surface"], theme["surface2"], 54)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(card, radius=54, outline=theme["border"], width=3)

    left = margin + inner
    right = W - margin - inner
    content_width = right - left

    # Header.
    brand_font = font(38, True)
    small_bold = font(22, True)
    tiny = font(19, True)
    title_font = font(56, True)
    hook_font = font(28, False)
    question_font = font(40, True)
    option_font = font(29, False)

    d.text((left, margin + 48), "SMART LEARNING LAB", font=brand_font, fill=theme["text"])
    d.text((left, margin + 96), "LEARN  •  PRACTICE  •  GROW", font=tiny, fill=theme["accent"])

    # Challenge number and category badges.
    badge_y = margin + 155
    draw_pill(
        d,
        (left, badge_y, left + 240, badge_y + 48),
        f"DAILY CHALLENGE  #{post_number:04d}",
        theme["badge"],
        theme["accent"],
        tiny,
        outline=theme["border"],
    )
    category = str(c.get("category", "challenge")).replace("_", " ").upper()
    cat_w = 220
    draw_pill(
        d,
        (right - cat_w, badge_y, right, badge_y + 48),
        category[:18],
        theme["accent"],
        theme["background"],
        tiny,
    )

    y = badge_y + 92

    # Title.
    title_lines = wrap(d, c["title"], title_font, content_width)
    for line in title_lines[:2]:
        d.text((left, y), line, font=title_font, fill=theme["text"])
        y += 66

    # Accent rule.
    y += 14
    d.rounded_rectangle((left, y, left + 130, y + 7), radius=4, fill=theme["accent"])
    d.rounded_rectangle((left + 142, y, left + 190, y + 7), radius=4, fill=theme["accent2"])
    y += 34

    # Hook.
    for line in wrap(d, c["hook"], hook_font, content_width):
        d.text((left, y), line, font=hook_font, fill=theme["muted"])
        y += 39
    y += 28

    # Question card.
    question_lines = wrap(d, c["question"], question_font, content_width - 80)
    q_height = max(150, 72 + len(question_lines) * 52)
    qbox = (left, y, right, y + q_height)
    d.rounded_rectangle(qbox, radius=28, fill=theme["option"], outline=blend(theme["border"], theme["surface"], 0.35), width=2)
    d.text((left + 28, y + 20), "YOUR 15-SECOND CHALLENGE", font=tiny, fill=theme["accent"])
    qy = y + 54
    for line in question_lines:
        d.text((left + 28, qy), line, font=question_font, fill=theme["text"])
        qy += 52
    y = qbox[3] + 28

    # Options as high-contrast tiles.
    option_height = 78
    gap = 18
    option_font = font(29, True)
    for key, value in c["options"].items():
        box = (left, y, right, y + option_height)
        d.rounded_rectangle(box, radius=22, fill=theme["option"], outline=blend(theme["border"], theme["surface"], 0.45), width=2)
        circle = (left + 20, y + 17, left + 62, y + 59)
        d.ellipse(circle, fill=theme["accent"])
        d.text((left + 35, y + 22), key, font=small_bold, fill=theme["background"])
        d.text((left + 82, y + 20), str(value), font=option_font, fill=theme["text"])
        y += option_height + gap

    # Interaction strip.
    strip_y = H - margin - 225
    d.rounded_rectangle((left, strip_y, right, strip_y + 94), radius=28, fill=theme["badge"])
    timer_text = f"⏱ {c['time_limit_seconds']} SEC"
    difficulty = str(c.get("difficulty", "Challenge")).upper()
    d.text((left + 24, strip_y + 25), timer_text, font=small_bold, fill=theme["accent"])
    d.text((right - 270, strip_y + 25), f"{difficulty}", font=small_bold, fill=theme["text"])

    # Footer CTA.
    footer_y = strip_y + 118
    cta = "COMMENT YOUR ANSWER  •  TAG A FRIEND  •  SHARE"
    d.text((left, footer_y), cta, font=small_bold, fill=theme["text"])
    d.text((left, footer_y + 39), "Answer revealed in the caption / next post.", font=tiny, fill=theme["muted"])

    # Theme label is tiny and useful for debugging/content QA, but still looks intentional.
    theme_label = f"THEME {theme['theme_number']}/10  •  {theme['name'].upper()}"
    tb = d.textbbox((0, 0), theme_label, font=tiny)
    d.text((right - (tb[2] - tb[0]), H - margin - 28), theme_label, font=tiny, fill=theme["muted"])

    out_dir = ROOT / CFG["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (c["id"] + ".png")
    im.save(out, format="PNG", optimize=True)
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
        f"#Theme{theme['theme_number']}"
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
        print(f"Generated {path} using theme {theme['theme_number']}: {theme['name']}")


if __name__ == "__main__":
    main()
