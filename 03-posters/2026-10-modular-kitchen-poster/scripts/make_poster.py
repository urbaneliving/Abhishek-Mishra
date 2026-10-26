"""Modular kitchen poster for Facebook + Instagram feed (1080x1350, 4:5).

Run from the repo root:
    python3 03-posters/2026-10-modular-kitchen-poster/scripts/make_poster.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
W, H = 1080, 1350

NAVY = (8, 56, 108)          # matches the reel series
RED = (229, 9, 19)           # brand red
INK = (24, 28, 36)
GREY = (92, 100, 114)
WHITE = (255, 255, 255)
FONT_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_M = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
font = lambda path, size: ImageFont.truetype(path, size)

PANEL_Y = 905                # white info panel starts here


def cover(img, w, h, focus_y=0.5):
    """Scale to fill w x h, cropping the overflow (vertical crop biased by focus_y)."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = round((img.height - h) * focus_y)
    return img.crop((x, y, x + w, y + h))


def main():
    photo = Image.open(ROOT / "raw/modular-kitchen.jpg").convert("RGB")
    photo = cover(photo, W, PANEL_Y + 60, focus_y=0.45)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=1.5, percent=50, threshold=2))
    c = Image.new("RGBA", (W, H), WHITE)
    c.paste(photo, (0, 0))

    # info panel with a red accent line along its top edge
    d = ImageDraw.Draw(c)
    d.rectangle((0, PANEL_Y, W, H), fill=WHITE)
    d.rectangle((0, PANEL_Y, W, PANEL_Y + 8), fill=RED)

    # logo card, top-left (original logo artwork, untouched)
    logo = Image.open(REPO / "_brand/urbane-living-logo-HD.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    lw = 300
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    pad = 26
    card = (48, 48, 48 + lw + 2 * pad, 48 + logo.height + 2 * pad)
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle((card[0], card[1] + 8, card[2], card[3] + 8), 26, fill=(0, 0, 0, 70))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle(card, 26, fill=WHITE)
    c.alpha_composite(logo, (card[0] + pad, card[1] + pad))

    # tag chip on the photo, above the panel
    tag = "MODULAR KITCHENS"
    f = font(FONT_B, 30)
    tw = f.getlength(tag)
    chip = (60, PANEL_Y - 74, 60 + tw + 56, PANEL_Y - 22)
    d.rounded_rectangle(chip, 26, fill=NAVY)
    d.text(((chip[0] + chip[2]) / 2, (chip[1] + chip[3]) / 2 + 1), tag, font=f, fill=WHITE, anchor="mm")

    # headline + supporting line
    x = 60
    d.text((x, PANEL_Y + 44), "Your Dream Kitchen,", font=font(FONT_B, 68), fill=INK)
    d.text((x, PANEL_Y + 122), "Designed Around You.", font=font(FONT_B, 68), fill=RED)
    d.text((x, PANEL_Y + 218), "Smart storage  •  Premium finishes  •  Built to fit your space",
           font=font(FONT_M, 31), fill=GREY)

    # call to action button
    cta = "Book a Free Design Consultation"
    f = font(FONT_B, 34)
    bw = f.getlength(cta) + 120
    btn = (x, PANEL_Y + 290, x + bw, PANEL_Y + 375)
    d.rounded_rectangle(btn, 42, fill=NAVY)
    d.text(((btn[0] + btn[2]) / 2 - 18, (btn[1] + btn[3]) / 2 + 1), cta, font=f, fill=WHITE, anchor="mm")
    ax, ay = btn[2] - 48, (btn[1] + btn[3]) / 2           # arrow
    d.line((ax - 18, ay, ax + 6, ay), fill=WHITE, width=5)
    d.line((ax - 6, ay - 12, ax + 7, ay), fill=WHITE, width=5)
    d.line((ax - 6, ay + 12, ax + 7, ay), fill=WHITE, width=5)

    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    rgb = c.convert("RGB")
    rgb.save(out / "modular-kitchen-poster-1080x1350.png", optimize=True)
    rgb.save(out / "modular-kitchen-poster-1080x1350.jpg", quality=95, subsampling=0)
    print(out / "modular-kitchen-poster-1080x1350.jpg")


if __name__ == "__main__":
    main()
