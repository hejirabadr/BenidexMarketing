#!/usr/bin/env python3
"""Met un visuel aux dimensions exactes du canal et ajoute le logo Benidex en haut à gauche.

  finalize_media.py image --in A.png --out B.jpg --size 1080x1350
  finalize_media.py video --in A.mp4 --out B.mp4 --size 1080x1920 --max-seconds 24
  finalize_media.py slideshow --in 1.png --in 2.png --in 3.png --out B.mp4 --size 1080x1920 --seconds 24
    (montage animé : zoom lent + fondus, utilisé quand la génération vidéo directe n'est pas disponible)
"""
import argparse, os, subprocess, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOGO = os.path.join(ROOT, "assets", "logo-benidex.png")


def parse_size(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def image(a):
    w, h = parse_size(a.size)
    im = Image.open(a.inp).convert("RGB")
    scale = max(w / im.width, h / im.height)  # remplissage puis recadrage centré
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((left, top, left + w, top + h))
    if not a.no_logo:
        logo = Image.open(LOGO).convert("RGBA")
        lw = round(w * 0.22)
        logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
        m = round(w * 0.04)
        im.paste(logo, (m, m), logo)
    ext = os.path.splitext(a.out)[1].lower()
    im.save(a.out, quality=92) if ext in (".jpg", ".jpeg") else im.save(a.out)
    print(a.out)


def video(a):
    w, h = parse_size(a.size)
    lw, m = round(w * 0.22), round(w * 0.04)
    vf = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[bg]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.inp]
    if a.no_logo:
        fc = vf.replace("[bg]", "[v]")
    else:
        cmd += ["-i", LOGO]
        fc = f"{vf};[1:v]scale={lw}:-1[lg];[bg][lg]overlay={m}:{m}[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-t", str(a.max_seconds),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(a.out)


def slideshow(a):
    import tempfile
    w, h = parse_size(a.size)
    n, fps = len(a.inps), 25
    dur = a.seconds / n
    frames = int(dur * fps)
    tmp = tempfile.mkdtemp()
    clips = []
    for i, src in enumerate(a.inps):
        out = os.path.join(tmp, f"c{i}.mp4")
        zoom = "min(zoom+0.0012,1.15)" if i % 2 == 0 else "if(eq(on,1),1.15,max(zoom-0.0012,1.0))"
        vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
              f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps},"
              f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(dur-0.4,0):.2f}:d=0.4,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", src, "-vf", vf,
                        "-frames:v", str(frames), "-c:v", "libx264", out], check=True)
        clips.append(out)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{c}'\n" for c in clips)
    raw = os.path.join(tmp, "raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", raw], check=True)
    a.inp, a.max_seconds = raw, a.seconds
    video(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("image", image), ("video", video)):
        p = sub.add_parser(name)
        p.add_argument("--in", dest="inp", required=True); p.add_argument("--out", required=True)
        p.add_argument("--size", required=True); p.add_argument("--no-logo", action="store_true")
        if name == "video":
            p.add_argument("--max-seconds", type=float, default=20)
        p.set_defaults(fn=fn)
    sl = sub.add_parser("slideshow")
    sl.add_argument("--in", dest="inps", action="append", required=True)
    sl.add_argument("--out", required=True); sl.add_argument("--size", required=True)
    sl.add_argument("--seconds", type=float, required=True); sl.add_argument("--no-logo", action="store_true")
    sl.set_defaults(fn=slideshow)
    a = ap.parse_args()
    try:
        a.fn(a)
    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
