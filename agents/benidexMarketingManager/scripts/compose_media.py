#!/usr/bin/env python3
"""Compose un post (image) ou un reel/vidéo (montage animé) à partir de VRAIES photos produit.
Aucun service d'IA : Pillow + ffmpeg. Logo, titre et appel à l'action sont incrustés.

  compose_media.py post --photo P --hook "Titre" --lang fr --size 1080x1350 --out post.jpg
  compose_media.py reel --photo P1 --photo P2 --hook "Titre" --point "Atout 1" --point "Atout 2" \
                        --lang fr --size 1080x1920 --seconds 24 --out reel.mp4

Arabe : nécessite arabic-reshaper et python-bidi (pip install -r requirements.txt).
"""
import argparse, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOGO = os.path.join(ROOT, "assets", "logo-benidex.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BLUE, TURQ, ORANGE = (14, 114, 181), (46, 170, 220), (242, 148, 0)
CTA = {"fr": "Demandez votre devis", "en": "Request your quote", "ar": "اطلب عرض السعر"}  # EN/AR à confirmer par Badr
CONTACT = "contact@benidex.com"


def shape(text, lang):
    if lang != "ar":
        return text
    from PIL import features
    if features.check("raqm"):  # Pillow gère lui-même la forme des lettres et le sens droite-gauche
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        raise RuntimeError("arabic-reshaper / python-bidi manquants : pip install -r requirements.txt")
    return get_display(arabic_reshaper.reshape(text))


def parse_size(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def font(px):
    return ImageFont.truetype(FONT, max(10, int(px)))


def wrap(text, fnt, max_w, lang):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(shape(t, lang)) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(text, lang, max_w, max_h, start, minimum):
    """Plus grande taille de police pour laquelle le texte tient dans max_w x max_h."""
    px = start
    while px >= minimum:
        f = font(px)
        lines = wrap(text, f, max_w, lang)
        if len(lines) * px * 1.25 <= max_h:
            return f, lines, px
        px -= 2
    f = font(minimum)
    return f, wrap(text, f, max_w, lang), minimum


def layout(W, H):
    portrait = H / W > 1.5          # 9:16 : le bas est masqué par l'interface des réseaux
    bottom = int(H * (0.20 if portrait else 0.06))
    top = int(H * (0.11 if portrait else 0.04))
    return portrait, top, bottom


def canvas(photo, W, H, scale=1):
    """Fond flouté aux couleurs Benidex + carte blanche arrondie contenant la photo, entière."""
    W, H = W * scale, H * scale
    src = Image.open(photo).convert("RGB")
    s = max(W / src.width, H / src.height)
    bg = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(26 * scale))
    bg = Image.blend(bg, Image.new("RGB", (W, H), BLUE), 0.55)
    portrait, top, bottom = layout(W // scale, H // scale)
    text_h = int(H * (0.25 if portrait else 0.34))
    logo_bottom = top * scale + int(W * 0.137) + int(W * 0.03)  # pastille du logo + marge
    box = (int(W * 0.06), logo_bottom, int(W * 0.94), H - bottom * scale - text_h)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle(box, radius=int(W * 0.035), fill=(255, 255, 255, 255))
    bg.paste(card, (0, 0), card)
    pad = int(W * 0.03)
    iw, ih = (box[2] - box[0] - 2 * pad), (box[3] - box[1] - 2 * pad)
    k = min(iw / src.width, ih / src.height)
    fg = src.resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
    bg.paste(fg, (box[0] + (box[2] - box[0] - fg.width) // 2, box[1] + (box[3] - box[1] - fg.height) // 2))
    return bg


def overlay(W, H, lang, hook=None, cta=False, cta_text=None):
    """Calque transparent : logo, texte et bouton d'appel à l'action (zones sûres par format)."""
    portrait, top, bottom = layout(W, H)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # dégradé sombre en bas pour la lisibilité
    gh = int(H * 0.42)
    for y in range(gh):
        a = int(210 * (y / gh) ** 1.4)
        d.line([(0, H - gh + y), (W, H - gh + y)], fill=(6, 40, 70, a))
    # logo sur pastille blanche, en haut à gauche
    logo = Image.open(LOGO).convert("RGBA")
    lw = int(W * 0.26)
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    m, p = int(W * 0.04), int(W * 0.018)
    d.rounded_rectangle((m, top, m + lw + 2 * p, top + logo.height + 2 * p), radius=int(W * 0.02), fill=(255, 255, 255, 240))
    ov.paste(logo, (m + p, top + p), logo)
    # bloc texte, ancré au-dessus de la marge basse
    y_end = H - bottom
    if cta:
        label = shape(cta_text or CTA[lang], lang)
        f = font(W * 0.05)
        bw, bh = int(f.getlength(label) + W * 0.10), int(W * 0.10)
        bx, by = (W - bw) // 2, y_end - bh - int(W * 0.045)
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh // 2, fill=ORANGE + (255,))
        d.text((W // 2, by + bh // 2), label, font=f, fill=(255, 255, 255), anchor="mm")
        fc = font(W * 0.034)
        d.text((W // 2, y_end), CONTACT, font=fc, fill=(255, 255, 255), anchor="ms")
        y_end = by - int(W * 0.03)
    if hook:
        max_h = int(H * 0.18)
        f, lines, px = fit_text(hook, lang, int(W * 0.84), max_h, int(W * 0.075), int(W * 0.04))
        y = y_end - len(lines) * int(px * 1.25)
        for ln in lines:
            d.text((W // 2 + 2, y + 2), shape(ln, lang), font=f, fill=(0, 0, 0, 120), anchor="ma")
            d.text((W // 2, y), shape(ln, lang), font=f, fill=(255, 255, 255), anchor="ma")
            y += int(px * 1.25)
    return ov


def post(a):
    W, H = parse_size(a.size)
    img = canvas(a.photo, W, H).convert("RGBA")
    img.alpha_composite(overlay(W, H, a.lang, a.hook, True, a.cta))
    out = img.convert("RGB")
    out.save(a.out, quality=93) if a.out.lower().endswith((".jpg", ".jpeg")) else out.save(a.out)
    print(a.out)


def reel(a):
    W, H = parse_size(a.size)
    photos = a.photo
    texts = [(a.hook, False)] + [(t, False) for t in a.point] + [(None, True)]  # dernier plan = appel à l'action
    n, fps = len(texts), 25
    if len(a.point) < 1:
        raise RuntimeError("au moins un --point est nécessaire (3 plans minimum)")
    dur = a.seconds / n
    F = max(1, int(dur * fps))
    tmp = tempfile.mkdtemp()
    clips = []
    for i, (txt, is_cta) in enumerate(texts):
        cv = os.path.join(tmp, f"cv{i}.png"); ovp = os.path.join(tmp, f"ov{i}.png"); out = os.path.join(tmp, f"c{i}.mp4")
        canvas(photos[i % len(photos)], W, H, scale=2).save(cv)
        ov = overlay(W, H, a.lang, hook=txt if txt else a.hook, cta=is_cta, cta_text=a.cta)
        ov.save(ovp)
        k = i % 3
        if k == 0:
            z, x, y = "min(1.0+0.0018*on,1.14)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif k == 1:
            z, x, y = "max(1.14-0.0018*on,1.0)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        else:
            z, x, y = "1.12", f"(iw-iw/zoom)*on/{F}", "ih/2-(ih/zoom/2)"
        st = max(dur - 0.35, 0)
        fc = (f"[0:v]zoompan=z='{z}':x='{x}':y='{y}':d={F}:s={W}x{H}:fps={fps}[z];"
              f"[z][1:v]overlay=0:0:format=auto,fade=t=in:st=0:d=0.35,fade=t=out:st={st:.2f}:d=0.35,format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", cv, "-loop", "1", "-i", ovp,
                        "-filter_complex", fc, "-map", "[v]", "-frames:v", str(F), "-c:v", "libx264", out], check=True)
        clips.append(out)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{c}'\n" for c in clips)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", str(a.seconds), a.out], check=True)
    print(a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("post", post), ("reel", reel)):
        p = sub.add_parser(name)
        p.add_argument("--hook", required=True); p.add_argument("--lang", choices=["fr", "en", "ar"], default="fr")
        p.add_argument("--size", required=True); p.add_argument("--out", required=True)
        p.add_argument("--cta", help="texte du bouton (sinon texte standard de la langue)")
        if name == "post":
            p.add_argument("--photo", required=True)
        else:
            p.add_argument("--photo", action="append", required=True)
            p.add_argument("--point", action="append", default=[])
            p.add_argument("--seconds", type=int, default=24)
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    try:
        a.fn(a)
    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
