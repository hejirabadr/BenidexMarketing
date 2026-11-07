#!/usr/bin/env python3
"""Retire un macaron, logo ou filigrane de tiers d'une photo (retouche locale par remplissage).

  clean_photo.py --in A.jpg --out B.jpg --circle 0.86,0.865,0.135     # centre x,y et rayon en fraction de la largeur
  clean_photo.py --in A.jpg --out B.jpg --rect 0.70,0.80,1.00,1.00    # x0,y0,x1,y1 en fractions

À utiliser seulement pour retirer une marque de tiers (macaron de prix, filigrane de revendeur), jamais pour
modifier le produit. Toujours regarder le résultat ensuite (outil Read) : s'il reste une trace visible, écarter la photo.
"""
import argparse, sys
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--circle"); ap.add_argument("--rect")
    a = ap.parse_args()
    try:
        import cv2
        im = np.array(Image.open(a.inp).convert("RGB"))
        h, w = im.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        if a.circle:
            cx, cy, r = (float(v) for v in a.circle.split(","))
            cv2.circle(mask, (int(cx * w), int(cy * h)), int(r * w), 255, -1)
        if a.rect:
            x0, y0, x1, y1 = (float(v) for v in a.rect.split(","))
            mask[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
        if not mask.any():
            raise RuntimeError("préciser --circle ou --rect")
        out = cv2.inpaint(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), mask, 9, cv2.INPAINT_TELEA)
        Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).save(a.out, quality=93)
        print(a.out)
    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
