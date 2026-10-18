"""gen_title.py: the English title screen image (docs/re/graphics.md). Run once; the build reads the PNG it writes.

    python -X utf8 tools/gen_title.py   -> assets/title_en.png (240x160, indexed in the title's own 256-colour palette)

The title is one 8bpp BG image: tiles at ROM 0x31E878 (map = row*32 + col), palette at 0x328878. Steps:
1. Logo mask: split the image into regions bounded by the logo's dark indigo outline, keep the regions of the
   katakana strokes (LOGO, picked by eye from a labelled render), then grow through the connected outline pixels.
2. Background behind it: the egg's silhouette per row (ellipse fitted to the visible edge) and the blue dome
   (circle) split masked pixels into outside / egg rim / shell / dome; each class is filled by diffusion from its
   own visible pixels, and the rim is redrawn dark.
3. "GRANBO" in the project font (tools/font_en.py capitals) at 6x, bold, italic, each letter a little lower than the
   last (the katakana ran down to the right), metallic gradient, indigo outline.
4. Every pixel mapped to the nearest palette colour.
"""
import colorsys
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font_en  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
OUT = ROOT / "assets/title_en.png"
TILES, PAL = 0x31E878, 0x328878
H, W = 160, 240
LOGO = {6, 7, 9, 10, 11, 12, 13, 15, 18, 19, 20}  # region labels of the katakana strokes
DOME = (117.6, -7.4, 45.2)  # centre x, y, radius of the blue dome (fitted to its visible rim)


def load(rom):
    pal = np.array([[(v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31]
                    for v in np.frombuffer(rom[PAL:PAL + 512], "<u2")], float)
    idx = np.zeros((H, W), int)
    for r in range(20):
        for c in range(30):
            o = TILES + (r * 32 + c) * 64
            idx[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = np.frombuffer(rom[o:o + 64], np.uint8).reshape(8, 8)
    return pal, idx


def grow(m, n=1, only=None):
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]  # noqa: E702
        m = g if only is None else m | (g & only)
    return m


def regions(dark):
    lab = -np.ones((H, W), int)
    k = 0
    for y in range(H):
        for x in range(W):
            if lab[y, x] >= 0 or dark[y, x]:
                continue
            stack = [(x, y)]
            lab[y, x] = k
            while stack:
                cx, cy = stack.pop()
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < W and 0 <= ny < H and lab[ny, nx] < 0 and not dark[ny, nx]:
                        lab[ny, nx] = k
                        stack.append((nx, ny))
            k += 1
    return lab


def logo_mask(im):
    hsv = np.array([[colorsys.rgb_to_hsv(*(im[y, x] / 255)) for x in range(W)] for y in range(H)])
    edge = (hsv[..., 2] < 0.62) & (hsv[..., 0] >= 0.55) & (hsv[..., 0] <= 0.78) & (hsv[..., 1] > 0.35)
    lab = regions(edge)
    logo = np.isin(lab, list(LOGO))
    mask = logo | (grow(logo, 3) & (lab < 0))
    dark = (hsv[..., 2] < 0.66) & (hsv[..., 0] > 0.55) & (hsv[..., 0] < 0.8) & (hsv[..., 1] > 0.3)
    return grow(grow(mask, 16, only=dark), 1)


def diffuse(img, fill, known, steps=1500):
    img[fill] = img[known].mean(axis=0)
    ok = np.pad(known | fill, 1)
    for _ in range(steps):
        p = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode="edge")
        acc, n = np.zeros_like(img), np.zeros((H, W))
        for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
            o = ok[dy:dy + H, dx:dx + W]
            acc += p[dy:dy + H, dx:dx + W] * o[..., None]
            n += o
        upd = fill & (n > 0)
        img[upd] = acc[upd] / n[upd][:, None]


def background(im, mask):
    green = (im[..., 1] > im[..., 0] + 40) & (im[..., 1] > im[..., 2] + 40)
    blue = (im[..., 2] > im[..., 0] + 80) & (im[..., 2] > im[..., 1] + 40)
    xl, xr = np.full(H, np.nan), np.full(H, np.nan)  # egg silhouette per row, where it is visible
    for y in range(H):
        ng = np.nonzero(~green[y])[0]
        if len(ng):
            if not mask[y, max(ng[0] - 2, 0):ng[0] + 3].any():
                xl[y] = ng[0]
            if not mask[y, ng[-1] - 2:ng[-1] + 3].any():
                xr[y] = ng[-1]
    pts = np.array([(xl[y], y) for y in range(150) if not np.isnan(xl[y])]
                   + [(xr[y], y) for y in range(150) if not np.isnan(xr[y])], float)
    a, b, c, d, e = np.linalg.lstsq(np.c_[pts[:, 0] ** 2, pts[:, 0] * pts[:, 1], pts[:, 1] ** 2, pts[:, 0],
                                          pts[:, 1]], np.ones(len(pts)), rcond=None)[0]
    for y in range(H):  # a x^2 + (b y + d) x + (c y^2 + e y - 1) = 0
        qb, qc = b * y + d, c * y * y + e * y - 1
        disc = qb * qb - 4 * a * qc
        if disc >= 0:
            r1, r2 = sorted(((-qb - disc ** 0.5) / (2 * a), (-qb + disc ** 0.5) / (2 * a)))
            xl[y] = r1 if np.isnan(xl[y]) else xl[y]
            xr[y] = r2 if np.isnan(xr[y]) else xr[y]
    ys = np.arange(H)
    for arr in (xl, xr):
        ok = ~np.isnan(arr)
        arr[~ok] = np.interp(ys[~ok], ys[ok], arr[ok])
    xs = np.arange(W)[None, :]
    outside = (xs < xl[:, None]) | (xs > xr[:, None])
    mask = mask | (grow(mask, 8) & ((xs < xl[:, None] - 1) | (xs > xr[:, None] + 1)) & ~green & (ys[:, None] < 120))
    rim = ~outside & ((xs < xl[:, None] + 2) | (xs > xr[:, None] - 2))
    yy, xx = np.mgrid[0:H, 0:W]
    dome = ((xx - DOME[0]) ** 2 + (yy - DOME[1]) ** 2 < DOME[2] ** 2) & ~outside & ~rim
    shell = ~outside & ~rim & ~dome
    img = im.copy()
    src = {0: green, 2: ~green & ~blue & (im.sum(-1) >= 300), 3: blue & (yy < 60)}
    for cls, region in ((0, outside), (2, shell), (3, dome)):
        diffuse(img, mask & region, ~mask & src[cls])
    img[mask & rim] = (24, 24, 88)
    return img


def letters(img):
    S, X0, Y0, GAP, SHEAR, DROP = 6, 14, 18, 3, 0.30, 7
    fill, t = np.zeros((H, W), bool), np.zeros((H, W))
    x = X0
    for i, ch in enumerate("GRANBO"):
        art = font_en.ART[ch]
        top, hgt = Y0 + DROP * i, len(art) * S
        m = np.zeros((H, W), bool)
        for gy, row in enumerate(art):
            for gx, c in enumerate(row):
                if c != "#":
                    continue
                for yy in range(S):
                    y = top + gy * S + yy
                    for xx in range(S):
                        sx = x + gx * S + xx + int(SHEAR * (top + hgt - y))
                        if 0 <= y < H and 0 <= sx < W:
                            m[y, sx] = True
        m = grow(m)
        t[m] = ((np.arange(H)[:, None] - top + 1) / (hgt + 2) * np.ones((1, W)))[m]
        fill |= m
        x += font_en.width(ch) * S + GAP
    stops = [(0.0, (200, 200, 236)), (0.3, (248, 248, 255)), (0.45, (190, 188, 226)), (0.75, (150, 148, 210)),
             (1.0, (104, 100, 184))]
    for y, xx in zip(*np.nonzero(fill)):
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if t[y, xx] <= b:
                k = (t[y, xx] - a) / (b - a)
                img[y, xx] = np.array(ca) * (1 - k) + np.array(cb) * k
                break
    outline = grow(fill, 2) & ~fill
    img[outline] = (48, 32, 120)
    img[grow(outline) & ~outline & ~fill & grow(fill, 4)] = (24, 16, 72)


def main():
    rom = ROM.read_bytes()
    pal, idx = load(rom)
    im = pal[idx]
    img = background(im, logo_mask(im))
    letters(img)
    # changed pixels take the nearest colour among the palette's blues, lavenders, whites and greens (the reds and
    # yellows of the eye and trim made pink and tan specks); untouched pixels keep their index
    hsv = np.array([colorsys.rgb_to_hsv(*(c / 255)) for c in pal])
    cand = np.nonzero(~(((hsv[:, 0] < 0.2) | (hsv[:, 0] > 0.9)) & (hsv[:, 1] > 0.15)))[0]
    near = cand[((img[:, :, None, :] - pal[cand][None, None]) ** 2).sum(-1).argmin(-1)]
    near = np.where((np.abs(img - im).sum(-1) < 1), idx, near)
    out = Image.fromarray(near.astype(np.uint8)).convert("P")
    out.putpalette([int(v) for v in pal.flatten()])
    OUT.parent.mkdir(exist_ok=True)
    out.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
