#!/usr/bin/env python3
"""Récupère les photos d'une page produit benidex.com.

  fetch_product_photos.py page  URL --out DOSSIER      lit la page et télécharge les photos du produit
  fetch_product_photos.py download --out DOSSIER URL1 URL2 ...   télécharge des URL d'images déjà connues

Si la page répond 403/404/429 (protection du site), le script s'arrête avec un message clair :
ne pas contourner la protection ; lire la page avec l'outil WebFetch pour trouver les URL d'images
(fichiers sous /wp-content/uploads/), puis utiliser la sous-commande `download`.
Sorties : un chemin de fichier par ligne (photo1.jpg, photo2.jpg…).
"""
import argparse, html, io, os, re, sys
import requests
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SKIP = re.compile(r"logo|icone|icon|favicon|placeholder|banner|bandeau|avatar|sprite", re.I)
IMG = re.compile(r"https?://[^\"'\s)>,]+/wp-content/uploads/[^\"'\s)>,]+?\.(?:jpe?g|png|webp)", re.I)


def original(url):
    """Retire le suffixe de miniature WordPress (-300x300) pour viser l'original."""
    return re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp)$)", "", url, flags=re.I)


def page_images(page_url):
    r = requests.get(page_url, headers=UA, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"page inaccessible (HTTP {r.status_code})")
    t = html.unescape(r.text)
    gallery = re.search(r"woocommerce-product-gallery.*?</figure>\s*</div>|woocommerce-product-gallery.*", t, re.S)
    scope = gallery.group(0) if gallery else t
    urls = IMG.findall(scope)
    og = re.findall(r'property="og:image"\s+content="([^"]+)"', t)
    urls = og + urls
    seen, out = set(), []
    for u in urls:
        o = original(u)
        if SKIP.search(o) or o in seen:
            continue
        seen.add(o)
        out.append(o)
    return out


def download(urls, outdir, limit=8):
    os.makedirs(outdir, exist_ok=True)
    saved = []
    for u in urls:
        if len(saved) >= limit:
            break
        for cand in dict.fromkeys([original(u), u]):  # l'original d'abord, sinon l'URL telle quelle
            try:
                r = requests.get(cand, headers=UA, timeout=60)
                if r.status_code != 200:
                    continue
                im = Image.open(io.BytesIO(r.content))
                if im.width < 400 or im.height < 400:
                    break  # trop petite (miniature)
                path = os.path.join(outdir, f"photo{len(saved)+1}.jpg")
                bg = Image.new("RGB", im.size, (255, 255, 255))  # fond blanc pour les PNG/WebP transparents
                im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[3])
                bg.save(path, quality=93)
                saved.append(path)
                break
            except Exception:
                continue
    return saved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("page"); p.add_argument("url"); p.add_argument("--out", required=True)
    d = sub.add_parser("download"); d.add_argument("urls", nargs="+"); d.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        urls = page_images(a.url) if a.cmd == "page" else a.urls
        saved = download(urls, a.out)
        if not saved:
            raise RuntimeError("aucune photo exploitable (taille minimale 400 px)")
        print("\n".join(saved))
    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
