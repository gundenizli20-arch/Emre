#!/usr/bin/env python3
"""clipper — découpe des clips courts (TikTok / Shorts / Reels) depuis une vidéo longue.

Dépendance obligatoire : ffmpeg (et ffprobe) dans le PATH.
Dépendance optionnelle : `pip install faster-whisper` pour les sous-titres automatiques.

Exemples :
  # Clips manuels, format vertical 9:16 avec fond flouté
  python3 clipper.py stream.mp4 -c 00:01:20-00:01:45 -c 12:03-12:40 --format fit

  # Clips listés dans un fichier (une ligne : "debut-fin [titre]")
  python3 clipper.py stream.mp4 -f clips.txt --format crop

  # Détection auto des 5 moments les plus forts (audio), 30 s chacun, avec sous-titres
  python3 clipper.py stream.mp4 --auto 5 --duree 30 --format fit --sous-titres
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

OUT_W, OUT_H = 1080, 1920  # 9:16


# ---------------------------------------------------------------- utilitaires

def parse_time(s: str) -> float:
    """'90', '1:30', '00:01:30.5' -> secondes."""
    s = s.strip()
    parts = s.split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"horodatage invalide : {s!r}")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    return total


def fmt_time(t: float, sep: str = ".") -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", sep)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:50] or "clip"


def run(cmd: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, capture_output=quiet, text=True)
    if res.returncode != 0:
        msg = res.stderr[-2000:] if quiet and res.stderr else ""
        raise RuntimeError(f"échec de la commande : {' '.join(cmd[:6])} ...\n{msg}")
    return res


def probe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(path)]).stdout
    return float(json.loads(out)["format"]["duration"])


def has_audio(path: Path) -> bool:
    out = run(["ffprobe", "-v", "error", "-select_streams", "a",
               "-show_entries", "stream=index", "-of", "csv=p=0", str(path)]).stdout
    return bool(out.strip())


# ---------------------------------------------------------------- clips

@dataclass
class Clip:
    start: float
    end: float
    title: str = ""

    @property
    def duration(self) -> float:
        return self.end - self.start


def parse_clip_spec(spec: str) -> Clip:
    """'01:20-01:45 Mon titre' -> Clip."""
    spec = spec.strip()
    m = re.match(r"^([\d:.]+)\s*-\s*([\d:.]+)\s*(.*)$", spec)
    if not m:
        raise ValueError(f"clip invalide : {spec!r} (attendu : debut-fin [titre])")
    start, end = parse_time(m.group(1)), parse_time(m.group(2))
    if end <= start:
        raise ValueError(f"la fin doit être après le début : {spec!r}")
    return Clip(start, end, m.group(3).strip())


def read_clip_file(path: Path) -> list[Clip]:
    clips = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            clips.append(parse_clip_spec(line))
    return clips


def auto_highlights(path: Path, count: int, duration: float, total: float) -> list[Clip]:
    """Repère les passages les plus forts en volume (rires, cris, hype…)."""
    print("Analyse audio pour trouver les temps forts…", file=sys.stderr)
    res = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
        "-af", "aresample=8000,asetnsamples=n=8000,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
        "-f", "null", "-",
    ])
    levels: list[float] = []
    for line in res.stdout.splitlines():
        if "RMS_level=" in line:
            v = line.split("=", 1)[1]
            levels.append(-100.0 if v in ("-inf", "inf", "nan") else float(v))
    if not levels:
        raise RuntimeError("impossible d'analyser l'audio")

    # Score = volume moyen sur une fenêtre de `duration` secondes (une valeur / seconde).
    win = max(1, int(duration))
    scores = []
    acc = sum(levels[:win])
    for i in range(0, max(1, len(levels) - win + 1)):
        if i > 0:
            acc += levels[i + win - 1] - levels[i - 1]
        scores.append((acc / win, i))
    scores.sort(reverse=True)

    picked: list[Clip] = []
    for _, start in scores:
        s, e = float(start), min(float(start + win), total)
        if all(e <= c.start or s >= c.end for c in picked):
            picked.append(Clip(s, e, f"highlight {len(picked) + 1}"))
        if len(picked) >= count:
            break
    return sorted(picked, key=lambda c: c.start)


# ---------------------------------------------------------------- sous-titres

def make_subtitles(src: Path, clip: Clip, workdir: Path, model_name: str, lang: str | None) -> Path | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        print("  ! faster-whisper non installé (pip install faster-whisper) : pas de sous-titres",
              file=sys.stderr)
        return None

    wav = workdir / "clip.wav"
    run(["ffmpeg", "-y", "-ss", f"{clip.start}", "-t", f"{clip.duration}", "-i", str(src),
         "-vn", "-ac", "1", "-ar", "16000", str(wav)])

    global _MODEL
    if "_MODEL" not in globals():
        print(f"  Chargement du modèle Whisper « {model_name} »…", file=sys.stderr)
        _MODEL = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, _ = _MODEL.transcribe(str(wav), language=lang, word_timestamps=True)

    # Style « TikTok » : 3-4 mots à la fois, gros et centrés.
    lines: list[tuple[float, float, str]] = []
    for seg in segments:
        words = list(seg.words or [])
        for i in range(0, len(words), 3):
            chunk = words[i:i + 3]
            text = "".join(w.word for w in chunk).strip()
            if text:
                lines.append((chunk[0].start, chunk[-1].end, text.upper()))

    srt = workdir / "clip.srt"
    with srt.open("w", encoding="utf-8") as f:
        for n, (s, e, t) in enumerate(lines, 1):
            f.write(f"{n}\n{fmt_time(s, ',')} --> {fmt_time(e, ',')}\n{t}\n\n")
    return srt if lines else None


def escape_filter_path(p: Path) -> str:
    return str(p).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


# ---------------------------------------------------------------- rendu

def build_video_filter(fmt: str, srt: Path | None, vertical: bool) -> str:
    if fmt == "crop":
        # Recadrage centré en 9:16.
        vf = (f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
              f"scale={OUT_W}:{OUT_H},setsar=1")
    elif fmt == "fit":
        # Vidéo entière au centre + fond flouté qui remplit l'écran.
        vf = (f"split[a][b];"
              f"[a]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
              f"crop={OUT_W}:{OUT_H},boxblur=20:5[bg];"
              f"[b]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    else:
        vf = "null"
    if srt:
        size = 16 if vertical else 22
        margin = 120 if vertical else 40
        style = (f"FontName=DejaVu Sans,FontSize={size},Bold=1,PrimaryColour=&H00FFFFFF,"
                 f"OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,"
                 f"Alignment=2,MarginV={margin}")
        vf += f",subtitles='{escape_filter_path(srt)}':force_style='{style}'"
    return vf


def render_clip(src: Path, clip: Clip, out: Path, args, audio: bool) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        srt = make_subtitles(src, clip, Path(tmp), args.modele, args.langue) if args.sous_titres else None
        vf = build_video_filter(args.format, srt, args.format != "original")

        fade = min(0.3, clip.duration / 4)
        afilter = f"afade=t=in:d={fade},afade=t=out:st={clip.duration - fade}:d={fade}"

        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-ss", f"{clip.start}", "-t", f"{clip.duration}", "-i", str(src),
               "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]"]
        if audio:
            cmd += ["-map", "0:a:0", "-af", afilter, "-c:a", "aac", "-b:a", "160k"]
        cmd += ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
        run(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description="Découpe des clips courts depuis une vidéo.")
    ap.add_argument("video", type=Path, help="vidéo source")
    ap.add_argument("-c", "--clip", action="append", default=[],
                    help="clip 'debut-fin [titre]', ex. 01:20-01:45 (répétable)")
    ap.add_argument("-f", "--fichier", type=Path, help="fichier texte de clips (une ligne par clip)")
    ap.add_argument("--auto", type=int, metavar="N", help="détecte N temps forts automatiquement")
    ap.add_argument("--duree", type=float, default=30, help="durée des clips auto (s, défaut 30)")
    ap.add_argument("--format", choices=["original", "crop", "fit"], default="fit",
                    help="original | crop (9:16 recadré) | fit (9:16 fond flouté, défaut)")
    ap.add_argument("--sous-titres", action="store_true", help="sous-titres auto (faster-whisper)")
    ap.add_argument("--modele", default="small", help="modèle Whisper (tiny/base/small/medium…)")
    ap.add_argument("--langue", default=None, help="langue forcée, ex. fr (auto par défaut)")
    ap.add_argument("-o", "--sortie", type=Path, default=Path("clips"), help="dossier de sortie")
    ap.add_argument("--crf", type=int, default=20, help="qualité x264 (plus bas = meilleur)")
    ap.add_argument("--preset", default="medium", help="preset x264 (ultrafast…veryslow)")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            ap.error(f"{tool} introuvable : installe ffmpeg")
    if not args.video.is_file():
        ap.error(f"fichier introuvable : {args.video}")

    total = probe_duration(args.video)
    clips = [parse_clip_spec(s) for s in args.clip]
    if args.fichier:
        clips += read_clip_file(args.fichier)
    if args.auto:
        clips += auto_highlights(args.video, args.auto, args.duree, total)
    if not clips:
        ap.error("aucun clip : utilise -c, -f ou --auto")

    args.sortie.mkdir(parents=True, exist_ok=True)
    audio = has_audio(args.video)
    stem = args.video.stem
    for i, clip in enumerate(clips, 1):
        if clip.start >= total:
            print(f"[{i}/{len(clips)}] ignoré : commence après la fin de la vidéo", file=sys.stderr)
            continue
        clip.end = min(clip.end, total)
        name = f"{stem}_{i:02d}" + (f"_{slugify(clip.title)}" if clip.title else "") + ".mp4"
        out = args.sortie / name
        print(f"[{i}/{len(clips)}] {fmt_time(clip.start)} → {fmt_time(clip.end)}  {out}",
              file=sys.stderr)
        render_clip(args.video, clip, out, args, audio)

    print(f"Terminé : {len(clips)} clip(s) dans {args.sortie}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)
