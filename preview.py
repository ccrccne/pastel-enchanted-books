"""Imágenes de vista previa: catálogo de todos los libros y los niveles."""
import pathlib

from PIL import Image, ImageDraw, ImageFont

import build

OUT = build.ROOT / "images"
FONT = "C:/Windows/Fonts/segoeuib.ttf"
INK = (74, 58, 96)
FAMILY_NAMES = {
    "armor": "Armor", "melee": "Weapons", "tools": "Tools", "ranged": "Bows & Crossbows",
    "water": "Water", "movement": "Movement", "mace": "Mace & Spear", "special": "Special", "curse": "Curses",
}


def background(w, h):
    bg = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=build.mix((236, 228, 255), (255, 232, 242), y / h))
    return bg


def sparkle(d, x, y, r, color=(255, 214, 120)):
    d.polygon([(x, y - r), (x + r // 4, y - r // 4), (x + r, y), (x + r // 4, y + r // 4),
               (x, y + r), (x - r // 4, y + r // 4), (x - r, y), (x - r // 4, y - r // 4)], fill=color)


def label(key):
    return key.replace("_", " ").title()


def catalog(files):
    """Todos los encantamientos en su nivel máximo, agrupados por familia."""
    groups = {}
    for key, (fam, max_level, _) in build.ENCHANTS.items():
        groups.setdefault(fam, []).append((key, max_level))
    S, cell_w, cols = 80, 150, 8
    title_f, fam_f, name_f = (ImageFont.truetype(FONT, s) for s in (54, 26, 15))
    rows = sum((len(v) + cols - 1) // cols for v in groups.values())
    w = 60 + cols * cell_w
    h = 170 + len(groups) * 50 + rows * (S + 40) + 30
    bg = background(w, h)
    d = ImageDraw.Draw(bg)
    d.text((w // 2, 70), "Pastel Enchanted Books", font=title_f, fill=INK, anchor="mm")
    d.text((w // 2, 120), "Every enchantment gets its own pastel book · 26.3",
           font=ImageFont.truetype(FONT, 20), fill=(140, 120, 170), anchor="mm")
    for x, y, r in ((90, 70, 18), (w - 90, 70, 18), (150, 40, 9), (w - 150, 100, 9)):
        sparkle(d, x, y, r)
    y = 160
    for fam, items in groups.items():
        color = build.FAMILIES[fam][1]
        d.rounded_rectangle([30, y, 30 + 18, y + 18], 5, fill=color)
        d.text((58, y + 9), FAMILY_NAMES[fam], font=fam_f, fill=INK, anchor="lm")
        y += 44
        for i, (key, lvl) in enumerate(items):
            cx = 30 + (i % cols) * cell_w + cell_w // 2
            if i and i % cols == 0:
                y += S + 40
            im = files[f"assets/{build.NS}/textures/item/{key}_{lvl}.png"].resize((S, S), Image.NEAREST)
            bg.paste(im, (cx - S // 2, y), im)
            d.text((cx, y + S + 14), label(key), font=name_f, fill=INK, anchor="mm")
        y += S + 46
    return bg


def levels(files):
    """Los niveles de Filo y Protección, más el libro arcoíris."""
    S = 128
    title_f, name_f = ImageFont.truetype(FONT, 44), ImageFont.truetype(FONT, 20)
    w, h = 1000, 800
    bg = background(w, h)
    d = ImageDraw.Draw(bg)
    d.text((w // 2, 60), "Gold dots show the level", font=title_f, fill=INK, anchor="mm")
    for row, (key, top) in enumerate((("sharpness", 5), ("protection", 4))):
        y = 120 + row * 210
        n = top
        for lvl in range(1, n + 1):
            cx = w // 2 + (lvl - 1 - (n - 1) / 2) * 170
            im = files[f"assets/{build.NS}/textures/item/{key}_{lvl}.png"].resize((S, S), Image.NEAREST)
            bg.paste(im, (int(cx - S // 2), y), im)
            roman = ["I", "II", "III", "IV", "V"][lvl - 1]
            d.text((cx, y + S + 22), f"{label(key)} {roman}", font=name_f, fill=INK, anchor="mm")
    im = files[f"assets/{build.NS}/textures/item/mixed.png"].resize((S, S), Image.NEAREST)
    bg.paste(im, (w // 2 - S // 2 - 190, 580), im)
    d.text((w // 2 - 100, 644), "Several enchantments → rainbow book", font=name_f, fill=INK, anchor="lm")
    for x, y, r in ((70, 60, 16), (w - 70, 60, 16)):
        sparkle(d, x, y, r)
    return bg


if __name__ == "__main__":
    _, files = build.build()
    OUT.mkdir(exist_ok=True)
    catalog(files).save(OUT / "catalogo.png")
    levels(files).save(OUT / "niveles.png")
    print("ok")
