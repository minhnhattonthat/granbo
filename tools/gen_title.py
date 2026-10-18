"""gen_title.py: the English title screen image (docs/re/graphics.md). Run once; the build reads the PNG it writes.

    python -X utf8 tools/gen_title.py   -> assets/title_en.png (240x160, indexed in the title's own 256-colour palette)

The title is one 8bpp BG image: tiles at ROM 0x31E878 (map = row*32 + col), palette at 0x328878. Steps:
1. Logo mask: split the image into regions bounded by the logo's dark indigo outline, keep the regions of the
   katakana strokes (LOGO, picked by eye from a labelled render), then grow through the connected outline pixels.
2. Background behind it: the egg's silhouette per row (ellipse fitted to the visible edge) and the blue dome
   (circle) split masked pixels into outside / egg rim / shell / dome; each class is filled by diffusion from its
   own visible pixels, and the rim is redrawn dark.
3. Custom polygon lettering on one rising baseline: clipped corners, open counters, silver bevels, a pale
   keyline and an indigo extruded outline. Rasterised at native resolution so every edge stays crisp.
4. Every pixel mapped to the nearest palette colour.
"""
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

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


# Original lettering, in a 31x51 design grid. First contour is the face; the rest are counters.
# The asymmetric G, diagonal R leg and tapered A make this a wordmark rather than enlarged UI text.
GLYPHS = {
    "G": [[(8, 0), (30, 0), (30, 10), (13, 10), (9, 14), (9, 37), (12, 40), (21, 40),
           (21, 31), (16, 31), (16, 22), (30, 22), (30, 43), (23, 50), (7, 50), (0, 43), (0, 8)]],
    "R": [[(0, 0), (23, 0), (30, 7), (30, 23), (23, 30), (31, 50), (20, 50), (12, 32),
           (9, 32), (9, 50), (0, 50)],
          [(9, 10), (19, 10), (21, 12), (21, 20), (19, 22), (9, 22)]],
    "A": [[(0, 50), (5, 8), (12, 0), (25, 0), (31, 50), (21, 50), (20, 37), (10, 37), (9, 50)],
          [(13, 11), (18, 11), (19, 27), (11, 27)]],
    "N": [[(0, 0), (9, 0), (22, 29), (22, 0), (30, 0), (30, 50), (21, 50), (8, 21),
           (8, 50), (0, 50)]],
    "B": [[(0, 0), (22, 0), (29, 7), (29, 20), (24, 25), (30, 31), (30, 43), (23, 50), (0, 50)],
          [(9, 10), (18, 10), (20, 12), (20, 18), (18, 20), (9, 20)],
          [(9, 30), (18, 30), (21, 33), (21, 38), (18, 41), (9, 41)]],
    "O": [[(8, 0), (23, 0), (30, 7), (30, 42), (22, 50), (7, 50), (0, 43), (0, 8)],
          [(12, 10), (18, 10), (21, 13), (21, 37), (18, 40), (12, 40), (9, 37), (9, 13)]],
}


def shift(mask, dx, dy):
    """Translate a mask without wrapping pixels at the screen edge."""
    out = np.zeros_like(mask)
    x0, x1, y0, y1 = max(0, dx), min(W, W + dx), max(0, dy), min(H, H + dy)
    out[y0:y1, x0:x1] = mask[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return out


def letters(img):
    # One continuous upward sweep, with a small forward lean. The eye and the menu stay clear.
    fill = np.zeros((H, W), bool)
    yy, xx = np.mgrid[:H, :W]
    for i, ch in enumerate("GRANBO"):
        face = Image.new("1", (W, H))
        draw = ImageDraw.Draw(face)
        for j, contour in enumerate(GLYPHS[ch]):
            points = []
            for x, y in contour:
                u = 12 + i * 34 + x + 0.20 * (50 - y)
                points.append((round(u), round(40 + y - 0.045 * (u - 12))))
            draw.polygon(points, fill=int(j == 0))
        fill |= np.asarray(face)

    # A solid dark silhouette around the extruded body anchors it against both shell and grass.
    border = grow(fill, 3)
    body = border.copy()
    for depth in range(1, 7):
        body |= shift(border, -depth // 2, depth)
    img[grow(body)] = (24, 16, 72)
    img[body] = (56, 40, 128)
    img[body & ~shift(body, -1, -1)] = (104, 88, 184)
    img[border] = (32, 24, 96)
    img[grow(fill)] = (208, 208, 248)

    # A hard reflection across the middle gives the broad faces the original logo's metal finish.
    t = np.clip((yy - 40 + 0.045 * (xx - 12)) / 50, 0, 1)
    stops = [0, 0.18, 0.44, 0.46, 0.72, 1]
    colors = [(208, 208, 240), (248, 248, 255), (224, 224, 248), (128, 120, 192),
              (168, 160, 216), (208, 200, 240)]
    for channel in range(3):
        ramp = np.interp(t, stops, [c[channel] for c in colors])
        img[..., channel][fill] = ramp[fill]
    # Two-pixel bevel: light from upper left, indigo on bottom/right (including counter walls).
    img[fill & ~shift(fill, -2, -2)] = (96, 80, 168)
    img[fill & ~shift(fill, 2, 2)] = (248, 248, 255)


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
