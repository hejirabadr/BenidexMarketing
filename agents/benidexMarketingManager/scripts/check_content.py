#!/usr/bin/env python3
"""Vérifie la checklist « Terminé » d'un contenu. Sortie JSON, code 0 si tout est OK.

  check_content.py --text caption.txt --lang fr --output Photo --channel Instagram \
                   --media out/photo.jpg [--hook "..."] [--product-found yes]
Les contrôles qui demandent du jugement (produit présent sur benidex.com, fidélité du visuel)
sont à faire par l'agent ; --product-found yes|no consigne simplement le résultat.
"""
import argparse, json, re, subprocess, sys
from PIL import Image

CTA = {  # TODO Badr : confirmer les formulations anglaise et arabe
    "fr": ["demandez votre devis"],
    "en": ["request your quote", "get your quote", "demandez votre devis"],
    "ar": ["اطلب عرض السعر", "اطلب عرض سعرك", "اطلب عرضك", "demandez votre devis"],
}
PRICE = re.compile(r"(\d[\d\s.,]*\s*(dh|dhs|mad|dirhams?|€|eur|\$|usd)\b)|(\b(prix|price|tarif)\b\s*[:à]?\s*\d)|(\d[\d\s.,]*\s*(درهم))", re.I)
FORBIDDEN = [("benq", "mention de BenQ"), ("meilleur prix au maroc", "formule « meilleur prix au Maroc »"),
             ("best price in morocco", "formule « best price in Morocco »")]
SIZES = {  # (canal, output) -> (largeur, hauteur)
    ("instagram", "photo"): (1080, 1350), ("instagram", "reel"): (1080, 1920), ("instagram", "vidéo"): (1080, 1920),
    ("tiktok", "photo"): (1080, 1920), ("tiktok", "reel"): (1080, 1920), ("tiktok", "vidéo"): (1080, 1920),
    ("facebook", "photo"): (1080, 1350), ("facebook", "reel"): (1080, 1920), ("facebook", "vidéo"): (1920, 1080),
    ("linkedin", "photo"): (1080, 1080), ("linkedin", "reel"): (1920, 1080), ("linkedin", "vidéo"): (1920, 1080),
}


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return d["streams"][0]["width"], d["streams"][0]["height"], float(d["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True); ap.add_argument("--lang", required=True, choices=["fr", "en", "ar"])
    ap.add_argument("--output", required=True, choices=["Photo", "Reel", "Vidéo"])
    ap.add_argument("--channel", required=True, choices=["Instagram", "Facebook", "LinkedIn", "TikTok"])
    ap.add_argument("--media", action="append", default=[]); ap.add_argument("--hook", default="")
    ap.add_argument("--product-found", choices=["yes", "no"], default="no")
    a = ap.parse_args()
    text = open(a.text, encoding="utf-8").read()
    low = (text + " " + a.hook).lower()
    checks = {}
    checks["Aucun prix affiché"] = not PRICE.search(text + " " + a.hook)
    checks["« Demandez votre devis » (ou équivalent) présent"] = any(c in low for c in CTA[a.lang])
    for needle, label in FORBIDDEN:
        checks[f"Pas de {label}"] = needle not in low
    checks["Produit existant sur benidex.com"] = a.product_found == "yes"
    checks["Hook fourni"] = bool(a.hook.strip())
    checks["Légende fournie"] = len(text.strip()) > 0
    checks["Hashtags fournis"] = "#" in text
    checks["Au moins un fichier média"] = len(a.media) > 0
    want = SIZES[(a.channel.lower(), a.output.lower())]
    for m in a.media:
        try:
            if a.output == "Photo":
                im = Image.open(m); got = im.size
                checks[f"{m} : taille {want[0]}x{want[1]}"] = got == want
            else:
                w, h, dur = probe(m)
                checks[f"{m} : taille {want[0]}x{want[1]}"] = (w, h) == want
                if a.output == "Reel" and a.channel != "LinkedIn":
                    checks[f"{m} : durée 15 à 30 s"] = 15 <= dur <= 30.5
                else:
                    checks[f"{m} : durée 20 s maximum"] = dur <= 20.5
        except Exception as e:
            checks[f"{m} : lisible ({e})"] = False
    failed = [k for k, v in checks.items() if not v]
    print(json.dumps({"ok": not failed, "failed": failed, "checks": checks}, ensure_ascii=False, indent=2))
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
