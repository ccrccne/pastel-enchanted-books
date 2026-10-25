"""Pastel Enchanted Books: un libro encantado distinto para cada encantamiento y nivel.

Uso: python build.py  -> dist/pastel-enchanted-books-<versión>+26.3.zip
- Parte del libro encantado original (leído del juego, no se guarda en el repo) y solo cambia sus colores:
  tapa pastel, páginas crema, cinta de color y broche dorado. El brillo encantado lo pone el juego.
- El color de la tapa dice la familia (armadura, armas, herramientas...), cada encantamiento tiene su tono
  y los puntitos dorados del borde de la tapa dicen el nivel.
- Los libros con varios encantamientos usan un libro arcoíris pastel.
Funciona sin mods en 26.3: el juego elige el modelo según el componente stored_enchantments.
"""
import colorsys
import io
import json
import pathlib
import zipfile

from PIL import Image

VERSION = "1.0.0"
ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"
NS = "pastelbooks"

# Familias: (nombre, color de la tapa)
FAMILIES = {
    "armor": ("Armadura", (176, 186, 240)),
    "melee": ("Armas", (246, 168, 190)),
    "tools": ("Herramientas", (250, 222, 140)),
    "ranged": ("Arco y ballesta", (160, 226, 186)),
    "water": ("Agua", (140, 214, 234)),
    "movement": ("Movimiento", (250, 194, 160)),
    "mace": ("Maza", (210, 176, 240)),
    "special": ("Especiales", (180, 240, 220)),
    "curse": ("Maldiciones", (78, 46, 88)),
}

ENCHANTS = {
    "protection": ("armor", 4, "Protección"), "fire_protection": ("armor", 4, "Protección contra el fuego"),
    "blast_protection": ("armor", 4, "Protección contra explosiones"),
    "projectile_protection": ("armor", 4, "Protección contra proyectiles"), "thorns": ("armor", 3, "Espinas"),
    "feather_falling": ("movement", 4, "Caída de pluma"), "respiration": ("water", 3, "Respiración"),
    "aqua_affinity": ("water", 1, "Afinidad acuática"), "depth_strider": ("water", 3, "Agilidad acuática"),
    "frost_walker": ("movement", 2, "Paso helado"), "soul_speed": ("movement", 3, "Velocidad de alma"),
    "swift_sneak": ("movement", 3, "Sigilo rápido"),
    "sharpness": ("melee", 5, "Filo"), "smite": ("melee", 5, "Castigo"),
    "bane_of_arthropods": ("melee", 5, "Perdición de los artrópodos"), "knockback": ("melee", 2, "Empuje"),
    "fire_aspect": ("melee", 2, "Aspecto ígneo"), "looting": ("melee", 3, "Botín"),
    "sweeping_edge": ("melee", 3, "Filo arrasador"),
    "breach": ("mace", 4, "Brecha"), "density": ("mace", 5, "Densidad"), "wind_burst": ("mace", 3, "Ráfaga de viento"),
    "lunge": ("melee", 3, "Embestida"),
    "efficiency": ("tools", 5, "Eficiencia"), "fortune": ("tools", 3, "Fortuna"), "silk_touch": ("tools", 1, "Toque de seda"),
    "unbreaking": ("special", 3, "Irrompibilidad"), "mending": ("special", 1, "Reparación"),
    "power": ("ranged", 5, "Poder"), "punch": ("ranged", 2, "Retroceso"), "flame": ("ranged", 1, "Fuego"),
    "infinity": ("ranged", 1, "Infinidad"), "multishot": ("ranged", 1, "Multidisparo"),
    "piercing": ("ranged", 4, "Perforación"), "quick_charge": ("ranged", 3, "Carga rápida"),
    "loyalty": ("water", 3, "Lealtad"), "riptide": ("water", 3, "Propulsión acuática"),
    "channeling": ("water", 1, "Conductividad"), "impaling": ("water", 5, "Empalamiento"),
    "luck_of_the_sea": ("water", 3, "Suerte marina"), "lure": ("water", 3, "Atracción"),
    "binding_curse": ("curse", 1, "Maldición de ligamiento"), "vanishing_curse": ("curse", 1, "Maldición de desaparición"),
}

GOLD = (255, 222, 120)
VANILLA = pathlib.Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client.jar"
TEXTURE = "assets/minecraft/textures/item/enchanted_book.png"
# Colores del libro original: cinta roja, broche dorado y páginas grises
RIBBON = {(197, 19, 57), (164, 44, 43), (137, 33, 32), (157, 27, 55), (108, 23, 23), (97, 20, 20)}
CLASP = {(211, 162, 22): (255, 226, 120), (212, 150, 26): (246, 190, 84)}
PAGES = {(214, 214, 214): (255, 252, 240), (183, 183, 183): (250, 240, 222), (153, 153, 153): (228, 210, 190),
         (91, 91, 91): (168, 140, 128)}
# Puntitos del nivel, sobre el borde de arriba de la tapa
LEVEL_DOTS = [(9, 3), (10, 4), (11, 5), (12, 6), (8, 2)]


def vanilla_book():
    with zipfile.ZipFile(VANILLA) as z:
        return Image.open(io.BytesIO(z.read(TEXTURE))).convert("RGBA")


def shade(c, f):
    return tuple(max(0, min(255, round(v * f))) for v in c)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def tweak(base, key):
    """Cada encantamiento de una familia tiene un tono un poco distinto, para que no sean iguales."""
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in base))
    names = [k for k, v in ENCHANTS.items() if v[0] == ENCHANTS[key][0]]
    i = names.index(key)
    h = (h + (i - len(names) / 2) * 0.03) % 1
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return round(r * 255), round(g * 255), round(b * 255)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def ramp(stops, t):
    t = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)


def hue_shift(c, dh, l=None, s=None):
    h, l0, s0 = colorsys.rgb_to_hls(*(v / 255 for v in c))
    r, g, b = colorsys.hls_to_rgb((h + dh) % 1, l0 if l is None else l, s0 if s is None else s)
    return round(r * 255), round(g * 255), round(b * 255)


def book(src, cover, level, curse=False, rainbow=False):
    """El libro original con su forma, cinta y broche, recoloreado en tonos pastel."""
    im = src.copy()
    px = im.load()
    # Cada tono café del original pasa a un tono de la tapa, con el mismo contraste
    deep = shade(hue_shift(cover, 0, s=min(1, colorsys.rgb_to_hls(*(v / 255 for v in cover))[2] * 1.15)), .94)
    ink = (34, 22, 44)
    tones = {(22, 16, 5): ink, (49, 33, 4): mix(shade(deep, .3), ink, .45),
             (68, 37, 10): shade(deep, .5), (82, 46, 16): shade(deep, .58), (68, 51, 16): shade(deep, .55),
             (84, 62, 19): shade(deep, .8), (101, 75, 23): deep}
    # Cinta rosada como la roja del original; más oscura en las tapas rosadas para que se note
    pinkish = colorsys.rgb_to_hls(*(v / 255 for v in cover))[0] > .85 or colorsys.rgb_to_hls(*(v / 255 for v in cover))[0] < .08
    ribbon = (178, 230, 120) if curse else (186, 52, 104) if pinkish else (232, 92, 128)
    for y in range(16):
        for x in range(16):
            c = px[x, y]
            if c[3] == 0:
                continue
            rgb = c[:3]
            if rgb in PAGES:
                new = PAGES[rgb] if not curse else shade(PAGES[rgb], .8)
            elif rgb in CLASP:
                new = CLASP[rgb]
            elif rgb in RIBBON:
                new = ramp([shade(ribbon, .55), shade(ribbon, .8), ribbon, mix(ribbon, (255, 255, 255), .3)],
                           (lum(rgb) - 35) / 50)
            else:
                new = tones.get(rgb) or shade(deep, lum(rgb) / 80)
                if rainbow and lum(rgb) > 40:
                    # Tapa arcoíris pastel; el contorno oscuro se queda
                    r, g, b = colorsys.hls_to_rgb(((x + y * .4) / 18) % 1, .5 + .3 * lum(rgb) / 80, .7)
                    new = (round(r * 255), round(g * 255), round(b * 255))
                elif rainbow:
                    new = mix(ink, (90, 70, 120), (lum(rgb) - 15) / 30)
            px[x, y] = (*new, 255)
    for x, y in LEVEL_DOTS[:level]:
        px[x, y] = (*(GOLD if not curse else (200, 170, 230)), 255)
    return im


def pack_icon(files):
    """Tres libros en abanico sobre un fondo lila con estrellitas."""
    tex = lambda n: files[f"assets/{NS}/textures/item/{n}.png"]
    bg = Image.new("RGBA", (32, 32))
    px = bg.load()
    for y in range(32):
        for x in range(32):
            # Esquinas redondeadas
            if min(x, 31 - x) + min(y, 31 - y) < 3:
                continue
            px[x, y] = (*mix((200, 186, 246), (250, 196, 222), y / 31), 255)
    for x, y in ((4, 5), (27, 8), (25, 26), (6, 24)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = (255, 250, 210, 255) if (dx, dy) == (0, 0) else (255, 236, 160, 255)
    bg.alpha_composite(tex("protection_4"), (3, 10))
    bg.alpha_composite(tex("sharpness_5"), (13, 10))
    bg.alpha_composite(tex("mending_1"), (8, 6))
    return bg.resize((128, 128), Image.NEAREST)


def build():
    files = {}
    cases = []
    src = vanilla_book()
    for key, (fam, max_level, _) in ENCHANTS.items():
        cover = FAMILIES[fam][1]
        if fam != "curse":
            cover = tweak(cover, key)
        for lvl in range(1, max_level + 1):
            name = f"{key}_{lvl}"
            files[f"assets/{NS}/textures/item/{name}.png"] = book(src, cover, lvl, curse=fam == "curse")
            cases.append({"when": {f"minecraft:{key}": lvl}, "model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}})
    files[f"assets/{NS}/textures/item/mixed.png"] = book(src, (255, 255, 255), 0, rainbow=True)
    models = {f"assets/{NS}/models/item/{p.split('/')[-1][:-4]}.json":
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{p.split('/')[-1][:-4]}"}}
              for p in files}
    item = {"model": {"type": "minecraft:select", "property": "minecraft:component",
                      "component": "minecraft:stored_enchantments", "cases": cases,
                      "fallback": {"type": "minecraft:model", "model": f"{NS}:item/mixed"}}}
    icon = pack_icon(files)
    mcmeta = {"pack": {"description": "§dPastel Enchanted Books §e✦\n§7por ccrccne", "min_format": 97, "max_format": 97}}
    DIST.mkdir(exist_ok=True)
    out = DIST / f"pastel-enchanted-books-{VERSION}+26.3.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps(mcmeta, ensure_ascii=False, indent=4))
        z.write(ROOT / "LICENSE", "LICENSE.txt")
        z.writestr("assets/minecraft/items/enchanted_book.json", json.dumps(item, indent=1))
        for rel, data in models.items():
            z.writestr(rel, json.dumps(data))
        for rel, im in files.items():
            buf = io.BytesIO()
            im.save(buf, "PNG")
            z.writestr(rel, buf.getvalue())
        buf = io.BytesIO()
        icon.save(buf, "PNG")
        z.writestr("pack.png", buf.getvalue())
    return out, files


if __name__ == "__main__":
    out, files = build()
    print(out.name, len(files), "texturas")
