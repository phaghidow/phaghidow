"""Identicon deterministe pour un pseudo GitHub (palette teal / violet / bleu)."""
import hashlib, math, os, sys
from PIL import Image, ImageDraw

SEED = sys.argv[1] if len(sys.argv) > 1 else "phaghidow"
BG = (13, 17, 23)
PALETTE = [(45, 212, 191), (192, 132, 252), (88, 166, 255)]   # teal, violet, bleu

def grid(seed):
    """5x5 symetrique : 15 cellules (3 colonnes) -> miroir. Retourne {(row,col): couleur}."""
    for salt in range(50):                       # re-hash tant que le motif est trop vide / trop plein
        h = hashlib.sha256(f"{seed}:{salt}".encode()).digest()
        bits = [(h[i // 8] >> (i % 8)) & 1 for i in range(15)]
        if 8 <= sum(bits) <= 12:
            break
    cells = {}
    for i, on in enumerate(bits):
        r, c = divmod(i, 3)
        if on:
            col = PALETTE[h[15 + i] % 3]
            cells[(r, c)] = col
            cells[(r, 4 - c)] = col               # miroir
    return cells

CELLS = grid(SEED)
S, SIZE = 3, 500
CELL, GAP = 56, 8
SPAN = 5 * CELL + 4 * GAP
OFF = (SIZE - SPAN) // 2

def blend(c, a): return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))

def render(prog=None, fade=1.0):
    """prog: dict cellule -> echelle 0..1 (None = tout affiche)."""
    im = Image.new("RGB", (SIZE * S, SIZE * S), BG)
    dr = ImageDraw.Draw(im)
    for (r, c), col in CELLS.items():
        k = 1.0 if prog is None else prog.get((r, c), 0)
        if k <= 0: continue
        e = 1 - (1 - k) ** 3
        size = CELL * (0.3 + 0.7 * e)
        cx = OFF + c * (CELL + GAP) + CELL / 2
        cy = OFF + r * (CELL + GAP) + CELL / 2
        x0, y0, x1, y1 = [v * S for v in (cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)]
        dr.rounded_rectangle((x0, y0, x1, y1), radius=10 * S * e, fill=blend(col, fade * min(1, k * 1.5)))
    out = im.resize((SIZE, SIZE), Image.LANCZOS); im.close()
    return out

# PNG
final = render()
final.save("avatar-identicon.png")

# apercu rond + petites tailles
prev = Image.new("RGB", (700, 300), (255, 255, 255))
for n, x in ((256, 20), (96, 300), (40, 420)):
    t = final.resize((n, n), Image.LANCZOS)
    m = Image.new("L", (n, n), 0); ImageDraw.Draw(m).ellipse((0, 0, n - 1, n - 1), fill=255)
    prev.paste(t, (x, 20), m)
prev.save("/tmp/identicon_preview.png")

# GIF : cascade depuis le centre, pause, fondu, boucle
order = sorted(CELLS, key=lambda p: (math.dist(p, (2, 2)), p))
N = 360
frames, durs = [], []
steps = len(order) * 2 + 8
for f in range(steps + 1):
    prog = {}
    for idx, cell in enumerate(order):
        start = idx * 1.4
        prog[cell] = max(0, min(1, (f - start) / 6))
    frames.append(render(prog).resize((N, N), Image.LANCZOS)); durs.append(45)
frames.append(final.resize((N, N), Image.LANCZOS)); durs.append(1800)
for a in (0.7, 0.4, 0.15):
    frames.append(render(None, fade=a).resize((N, N), Image.LANCZOS)); durs.append(60)
frames.append(Image.new("RGB", (N, N), BG)); durs.append(250)

mosaic = Image.new("RGB", (N * 4, N * 2))
for i, k in enumerate((len(frames) // 8, len(frames) // 4, len(frames) // 3, len(frames) // 2, len(frames) - 12, len(frames) - 6, len(frames) - 4, len(frames) - 3)):
    mosaic.paste(frames[k], ((i % 4) * N, (i // 4) * N))
pal = mosaic.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save("avatar-identicon.gif", save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)

print("cellules actives:", len(CELLS), "| frames:", len(q))
for r in range(5):
    print("".join("#" if (r, c) in CELLS else "." for c in range(5)))
print("PNG KB", os.path.getsize("avatar-identicon.png") // 1024, "| GIF KB", os.path.getsize("avatar-identicon.gif") // 1024)
