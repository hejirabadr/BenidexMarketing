#!/usr/bin/env python3
"""Photo Benidex 4:5 (1080x1350) : vraie photo produit (benidex.com) + habillage de marque.
Usage : python3 tools/make_photo.py <id_produit_WordPress> [sortie.png] [--titre "Titre"]
Aucun prix. CTA : « Demandez votre devis ». Zéro coût (Pillow uniquement).
"""
import argparse, html, io, json, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BLEU_CLAIR, BLEU, ORANGE = "#2EAADC", "#0E72B5", "#F29400"
W, H = 1080, 1350
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BenidexMarketing/1.0"})
    return urllib.request.urlopen(req, timeout=30).read()

def produit(pid):
    p = json.loads(get(f"https://benidex.com/wp-json/wp/v2/product/{pid}?_fields=title,link,featured_media"))
    m = json.loads(get(f"https://benidex.com/wp-json/wp/v2/media/{p['featured_media']}?_fields=source_url"))
    return html.unescape(p["title"]["rendered"]), p["link"], get(m["source_url"])

def wrap(d, texte, font, largeur):
    lignes, cur = [], ""
    for mot in texte.split():
        t = (cur + " " + mot).strip()
        if d.textlength(t, font=font) <= largeur: cur = t
        else: lignes.append(cur); cur = mot
    return lignes + [cur]

def compose(titre, img_bytes):
    im = Image.new("RGB", (W, H), "#F4FAFD")
    d = ImageDraw.Draw(im)
    # bandeau haut
    d.rectangle([0, 0, W, 150], fill="white")
    logo = Image.open(ROOT / "assets/logo-benidex.png").convert("RGBA")
    logo.thumbnail((300, 110)); im.paste(logo, (60, 150 // 2 - logo.height // 2), logo)
    d.rectangle([0, 150, W, 158], fill=BLEU_CLAIR)
    # carte photo (produit entier, jamais déformé ni rogné)
    cx0, cy0, cx1, cy1 = 60, 200, W - 60, 960
    d.rounded_rectangle([cx0, cy0, cx1, cy1], 28, fill="white")
    p = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    bw_, bh_ = cx1 - cx0 - 60, cy1 - cy0 - 60
    k = min(bw_ / p.width, bh_ / p.height)  # ajuste à la carte, agrandit si besoin (sans déformer)
    p = p.resize((round(p.width * k), round(p.height * k)), Image.LANCZOS)
    im.paste(p, ((W - p.width) // 2, (cy0 + cy1) // 2 - p.height // 2))
    # bloc bas
    d.rectangle([0, 1000, W, H], fill=BLEU)
    f_t = ImageFont.truetype(FONT.format("Bold"), 54)
    y = 1040
    for l in wrap(d, titre, f_t, W - 120)[:2]:
        d.text((60, y), l, font=f_t, fill="white"); y += 68
    f_b = ImageFont.truetype(FONT.format("SemiBold"), 38)
    bw = int(d.textlength("Demandez votre devis", font=f_b)) + 90
    d.rounded_rectangle([60, 1215, 60 + bw, 1295], 40, fill=ORANGE)
    d.text((60 + 45, 1255), "Demandez votre devis", font=f_b, fill="white", anchor="lm")
    f_s = ImageFont.truetype(FONT.format("Medium"), 30)
    d.text((W - 60, 1255), "benidex.com", font=f_s, fill="white", anchor="rm")
    return im

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("id"); a.add_argument("sortie", nargs="?", default="photo.png"); a.add_argument("--titre")
    r = a.parse_args()
    titre, lien, img = produit(r.id)
    compose(r.titre or titre, img).save(r.sortie)
    print("OK", r.sortie, "|", titre, "|", lien)
