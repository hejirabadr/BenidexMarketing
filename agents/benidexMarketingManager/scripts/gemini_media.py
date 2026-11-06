#!/usr/bin/env python3
"""Génération d'images et de vidéos via l'API Gemini de Google (REST).

ATTENTION : écrit sans clé API disponible, donc NON TESTÉ contre l'API réelle.
Premier réflexe : `python3 gemini_media.py models` pour voir les modèles autorisés,
puis passer --model si les noms par défaut ont changé.

Clé : variable GEMINI_API_KEY, OU secret réseau injecté par le proxy (aucun en-tête à ajouter).
Ne jamais afficher la clé.

Sous-commandes :
  models                                  liste les modèles image/vidéo disponibles
  image --prompt P --out F [--ref R ...] [--aspect 4:5] [--model M]
  video --prompt P [--prompt P2 ...] --out F --seconds 20 [--aspect 9:16] [--ref R] [--model M]
"""
import argparse, base64, json, math, mimetypes, os, subprocess, sys, tempfile, time
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
DEFAULT_VIDEO_MODEL = os.environ.get("GEMINI_VIDEO_MODEL", "veo-3.0-generate-001")
CLIP_SECONDS = 8  # durée d'un clip Veo


def headers():
    h = {"Content-Type": "application/json"}
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        h["x-goog-api-key"] = key
    return h


def call(method, url, **kw):
    """Requête avec 3 essais sur 429/5xx. Lève RuntimeError avec un message lisible."""
    last = None
    for attempt in range(3):
        r = requests.request(method, url, headers=headers(), timeout=300, **kw)
        if r.status_code in (429, 500, 502, 503, 504):
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
        return r
    raise RuntimeError(last or "échec réseau")


def load_ref(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        return {"mime": mime, "b64": base64.b64encode(f.read()).decode()}


def cmd_models(_):
    r = call("GET", f"{BASE}/models?pageSize=200")
    for m in r.json().get("models", []):
        name = m["name"].replace("models/", "")
        if any(k in name for k in ("image", "imagen", "veo")):
            print(name, m.get("supportedGenerationMethods", []))


def cmd_image(a):
    parts = [{"text": a.prompt}]
    for p in a.ref or []:
        ref = load_ref(p)
        parts.append({"inlineData": {"mimeType": ref["mime"], "data": ref["b64"]}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                                 "imageConfig": {"aspectRatio": a.aspect}}}
    r = call("POST", f"{BASE}/models/{a.model}:generateContent", json=body)
    for cand in r.json().get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data")
            if data:
                with open(a.out, "wb") as f:
                    f.write(base64.b64decode(data["data"]))
                print(a.out)
                return
    raise RuntimeError("aucune image dans la réponse : " + r.text[:300])


def veo_clip(model, prompt, aspect, ref, out):
    inst = {"prompt": prompt}
    if ref:
        inst["image"] = {"bytesBase64Encoded": ref["b64"], "mimeType": ref["mime"]}
    body = {"instances": [inst],
            "parameters": {"aspectRatio": aspect, "durationSeconds": CLIP_SECONDS}}
    try:
        op = call("POST", f"{BASE}/models/{model}:predictLongRunning", json=body).json()
    except RuntimeError as e:
        if ref and "HTTP 400" in str(e):
            print("AVERTISSEMENT : image de référence refusée, essai en texte seul", file=sys.stderr)
            del inst["image"]
            op = call("POST", f"{BASE}/models/{model}:predictLongRunning", json=body).json()
        else:
            raise
    name = op["name"]
    for _ in range(90):  # 15 minutes max
        time.sleep(10)
        st = call("GET", f"{BASE}/{name}").json()
        if st.get("done"):
            if "error" in st:
                raise RuntimeError("Veo : " + json.dumps(st["error"])[:300])
            resp = st.get("response", {})
            samples = (resp.get("generateVideoResponse", {}).get("generatedSamples")
                       or resp.get("videos") or [])
            if not samples:
                raise RuntimeError("Veo : aucune vidéo (filtre de sécurité ?) " + json.dumps(resp)[:300])
            uri = samples[0].get("video", {}).get("uri")
            v = call("GET", uri, allow_redirects=True)
            with open(out, "wb") as f:
                f.write(v.content)
            return
    raise RuntimeError("Veo : délai dépassé (15 min)")


def cmd_video(a):
    n = max(1, math.ceil(a.seconds / CLIP_SECONDS))
    prompts = a.prompt
    ref = load_ref(a.ref) if a.ref else None
    tmp = tempfile.mkdtemp()
    clips = []
    for i in range(n):
        p = prompts[i] if i < len(prompts) else f"{prompts[-1]} (partie {i+1}/{n}, même produit, même décor)"
        out = os.path.join(tmp, f"clip{i}.mp4")
        veo_clip(a.model, p, a.aspect, ref, out)
        clips.append(out)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{c}'\n" for c in clips)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-t", str(a.seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", a.out], check=True)
    print(a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models").set_defaults(fn=cmd_models)
    i = sub.add_parser("image")
    i.add_argument("--prompt", required=True); i.add_argument("--out", required=True)
    i.add_argument("--ref", action="append"); i.add_argument("--aspect", default="1:1")
    i.add_argument("--model", default=DEFAULT_IMAGE_MODEL); i.set_defaults(fn=cmd_image)
    v = sub.add_parser("video")
    v.add_argument("--prompt", required=True, action="append"); v.add_argument("--out", required=True)
    v.add_argument("--seconds", type=int, required=True); v.add_argument("--aspect", default="9:16")
    v.add_argument("--ref"); v.add_argument("--model", default=DEFAULT_VIDEO_MODEL)
    v.set_defaults(fn=cmd_video)
    a = ap.parse_args()
    try:
        a.fn(a)
    except Exception as e:  # message court pour la colonne « Explication échec »
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
