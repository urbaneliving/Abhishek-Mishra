"""Step reel: animates a numbered false-ceiling site photo into a 9:16 short.

Every frame is a pure function of t. Each project folder holds raw/<photo> and reel.json:
    {"photo": "raw/x.webp", "step": "02", "title": "Board Installation", "days": 2, "start_day": 3, "slug": "board-installation"}
Run from the repo root:
    python3 01-reels/_step-reel/make_step_reel.py 01-reels/<project> [--stills]
"""
import json, math, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[2]
ROOT = Path(next(a for a in sys.argv[1:] if not a.startswith("--"))).resolve()
CFG = json.loads((ROOT / "reel.json").read_text())
STEP, TITLE, DAYS = CFG["step"], CFG["title"], int(CFG["days"])
DAY0 = int(CFG.get("start_day", 1))           # project day this step starts on
W, H, FPS, DUR = 1080, 1920, 30, 10.0

NAVY = (8, 56, 108)          # badge colour from the photo series
RED = (229, 9, 19)           # brand red
WHITE = (255, 255, 255)
FONT_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_M = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
font = lambda path, size: ImageFont.truetype(path, int(size))

# --- source: drop the baked-in badge strip at the top, upscale once ---
src = Image.open(ROOT / CFG["photo"]).convert("RGB")
src = src.crop((0, 180, src.width, src.height))
BIG_H = int(H * 1.18)                                 # headroom for the zoom
BIG = src.resize((round(src.width * BIG_H / src.height), BIG_H), Image.LANCZOS)
BIG = BIG.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

LOGO = Image.open(REPO / "_brand/urbane-living-logo-HD.png").convert("RGBA")
LOGO = LOGO.resize((760, round(760 * LOGO.height / LOGO.width)), Image.LANCZOS)


# --- easing ---
clamp = lambda x: max(0.0, min(1.0, x))
prog = lambda t, s, d: clamp((t - s) / d)
lerp = lambda a, b, k: a + (b - a) * k
ease_io = lambda k: 4 * k**3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2
ease_out = lambda k: 1 - (1 - k) ** 3
def ease_back(k, s=1.7):
    k -= 1
    return 1 + (s + 1) * k**3 + s * k**2


def camera(t):
    """Pan from the left worker to the right one, then ease back to a wider frame."""
    pan = ease_io(prog(t, 0.0, 7.2))
    zoom = lerp(1.18, 1.0, ease_io(prog(t, 4.5, 3.5)))  # 1.0 == BIG fits frame height
    ch = BIG_H / zoom
    cw = ch * W / H
    cx = lerp(cw / 2 + 40, BIG.width - cw / 2 - 40, pan)
    cy = lerp(BIG_H * .52, BIG_H / 2, ease_io(prog(t, 4.5, 3.5)))
    cy = min(max(cy, ch / 2), BIG_H - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return BIG.resize((W, H), Image.BICUBIC, box=box)


def badge(c, t):
    """Step badge: circle pops, pill slides out, text rises."""
    kc = prog(t, 0.6, 0.5)
    if kc <= 0:
        return
    out = prog(t, 7.0, 0.4)                               # exits before the outro
    x0, y0, R = 70, 150, 105
    shift = -700 * ease_out(out) ** 2
    # pill
    kp = ease_out(prog(t, 0.95, 0.5))
    if kp > 0:
        pw = lerp(0, max(560, font(FONT_B, 64).getlength(TITLE) + 120), kp)
        pill = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(pill)
        d.rounded_rectangle((x0 + R + shift, y0 - 78, x0 + R + pw + shift, y0 + 78), 30,
                            fill=(255, 255, 255, 240))
        c.alpha_composite(pill)
        kt = ease_out(prog(t, 1.25, 0.45))
        ks = ease_out(prog(t, 1.5, 0.45))
        clip = Image.new("RGBA", (W, H))
        dc = ImageDraw.Draw(clip)
        dc.text((x0 + R + 70 + shift, y0 - 62 + 40 * (1 - kt)), TITLE,
                font=font(FONT_B, 64), fill=NAVY + (int(255 * kt),))
        dc.text((x0 + R + 72 + shift, y0 + 14 + 30 * (1 - ks)), f"Duration: {DAYS} day{'s' * (DAYS != 1)}",
                font=font(FONT_M, 44), fill=NAVY + (int(255 * ks),))
        mask = Image.new("L", (W, H))
        ImageDraw.Draw(mask).rectangle((x0 + R + shift, y0 - 78, x0 + R + pw + shift, y0 + 78), 255)
        clip.putalpha(ImageChops.multiply(clip.getchannel("A"), mask))
        c.alpha_composite(clip)
    # circle
    s = ease_back(kc) * R
    d = ImageDraw.Draw(c)
    cx = x0 + R * .55 + shift
    d.ellipse((cx - s - 8, y0 - s - 8, cx + s + 8, y0 + s + 8), fill=WHITE)
    d.ellipse((cx - s, y0 - s, cx + s, y0 + s), fill=NAVY)
    if kc > .4:
        f = font(FONT_B, 100 * min(1, s / R))
        d.text((cx, y0 + 4), STEP, font=f, fill=WHITE, anchor="mm")


def timeline_bar(c, t):
    """Bottom card: first → last project day progress line that fills with the pan."""
    k = ease_out(prog(t, 1.6, 0.6)) * (1 - ease_out(prog(t, 7.0, 0.4)))
    if k <= 0:
        return
    y = H - 230 + 80 * (1 - k)
    a = int(255 * k)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((70, y - 75, W - 70, y + 75), 36, fill=(255, 255, 255, int(235 * k)))
    fill = ease_io(prog(t, 2.0, 4.8))
    x1, x2 = 260, W - 260
    d.line((x1, y, x2, y), fill=(200, 208, 220, a), width=10)
    d.line((x1, y, lerp(x1, x2, fill), y), fill=RED + (a,), width=10)
    for i, (xx, label) in enumerate(((x1, f"Day {DAY0}"), (x2, f"Day {DAY0 + max(DAYS, 2) - 1}"))):
        on = fill >= i
        r = 18
        d.ellipse((xx - r, y - r, xx + r, y + r), fill=(RED if on else (200, 208, 220)) + (a,))
        tx = 150 if i == 0 else W - 150
        d.text((tx, y), label, font=font(FONT_B, 40), fill=NAVY + (a,), anchor="mm")
    c.alpha_composite(layer)


def outro(c, t):
    """White panel wipes up with the logo and tagline."""
    k = ease_io(prog(t, 7.3, 0.7))
    if k <= 0:
        return
    top = lerp(H, 0, k)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    d.rectangle((0, top, W, H), fill=(255, 255, 255, 255))
    d.rectangle((0, top, W, top + 14), fill=RED + (255,))
    c.alpha_composite(layer)
    kl = ease_back(prog(t, 7.9, 0.6))
    if kl > 0:
        lw = max(1, int(LOGO.width * kl))
        logo = LOGO.resize((lw, max(1, int(LOGO.height * kl))), Image.LANCZOS)
        c.alpha_composite(logo, (W // 2 - logo.width // 2, 840 - logo.height // 2))
    d = ImageDraw.Draw(c)
    for i, (txt, f, col, yy, s) in enumerate((
        (f"Step {STEP} · {TITLE}", font(FONT_B, 52), NAVY, 1160, 8.4),
        ("False ceiling, done right.", font(FONT_M, 44), (90, 100, 115), 1240, 8.7),
    )):
        kt = ease_out(prog(t, s, 0.5))
        if kt > 0:
            txt_l = Image.new("RGBA", (W, H))
            ImageDraw.Draw(txt_l).text((W / 2, yy + 30 * (1 - kt)), txt, font=f,
                                       fill=col + (int(255 * kt),), anchor="mm")
            c.alpha_composite(txt_l)


def frame(t):
    c = camera(t).convert("RGBA")
    # soft top/bottom gradient so the cards read cleanly
    c.alpha_composite(GRAD)
    badge(c, t)
    timeline_bar(c, t)
    outro(c, t)
    fade = prog(t, 0, 0.4)
    img = c.convert("RGB")
    if fade < 1:
        img = Image.blend(Image.new("RGB", (W, H), NAVY), img, ease_out(fade))
    return img


def _grad():
    a = np.zeros((H, W, 4), np.uint8)
    y = np.arange(H)[:, None]
    top = np.clip(1 - y / 420, 0, 1) * 110
    bot = np.clip((y - (H - 520)) / 520, 0, 1) * 120
    a[..., 3] = np.maximum(top, bot).astype(np.uint8)
    return Image.fromarray(a, "RGBA")
GRAD = _grad()


def audio(path):
    """Gentle pad + whoosh/pop SFX on the key moves (synthesised, copyright-free)."""
    sr = 48000
    n = int(sr * DUR)
    tt = np.arange(n) / sr
    rng = np.random.default_rng(1)
    out = np.zeros(n)
    env = np.clip(tt / 1.0, 0, 1) * np.clip((DUR - tt) / 1.2, 0, 1)
    for f in (130.81, 196.0, 261.63, 329.63):            # C major pad
        out += 0.05 * np.sin(2 * np.pi * f * tt + 0.3 * np.sin(2 * np.pi * 0.2 * tt)) * env
    out += 0.03 * np.sin(2 * np.pi * 65.4 * tt) * env
    def whoosh(at, dur, gain):
        i, m = int(at * sr), int(dur * sr)
        nz = rng.standard_normal(m)
        nz = np.convolve(nz, np.ones(24) / 24, "same")
        e = np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        out[i:i + m] += gain * nz * e
    def pop(at, f, gain):
        i, m = int(at * sr), int(0.18 * sr)
        x = np.arange(m) / sr
        out[i:i + m] += gain * np.sin(2 * np.pi * f * x * (1 + 2 * np.exp(-x * 40))) * np.exp(-x * 25)
    pop(0.6, 520, 0.35); whoosh(0.9, 0.5, 0.5); pop(1.6, 660, 0.25)
    whoosh(7.0, 0.7, 0.6); pop(7.95, 440, 0.4); pop(8.4, 660, 0.2); pop(8.7, 880, 0.15)
    out = out / np.max(np.abs(out)) * 0.8
    pcm = (np.repeat(out[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def main():
    work, out = ROOT / "work", ROOT / "out"
    work.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    if "--stills" in sys.argv:
        for t in (0.3, 1.0, 2.5, 5.0, 7.2, 9.5):
            frame(t).save(work / f"still_{t:04.1f}.jpg", quality=90)
        return
    audio(work / "sfx.wav")
    dst = out / f"{CFG['slug']}-reel-9x16.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(work / "sfx.wav"),
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5",
         "-movflags", "+faststart", "-shortest", str(dst)], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    print(dst)


if __name__ == "__main__":
    main()
