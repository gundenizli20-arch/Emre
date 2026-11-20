"""Atelier de clipping Shortcut Studio.

Usage :
  python clipper.py transcribe VIDEO            -> VIDEO.words.json + transcription lisible (minutages)
  python clipper.py clip VIDEO START END OUT.mp4 [ACCROCHE]
       -> clip vertical 1080x1920, sous-titres mot à mot (style TikTok), accroche en haut.
"""
import json, subprocess, sys, os

def ts(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"

def transcribe(video):
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    import numpy as np
    raw = subprocess.run(["ffmpeg","-v","error","-i",video,"-map","0:a:0","-af","loudnorm=I=-16","-ac","1","-ar","16000","-f","s16le","-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, language="fr", word_timestamps=True, vad_filter=True)
    words, lines = [], []
    for s in segs:
        lines.append(f"[{ts(s.start)} - {ts(s.end)}] {s.text.strip()}")
        for w in s.words:
            words.append({"w": w.word.strip(), "s": w.start, "e": w.end})
    json.dump(words, open(video + ".words.json", "w"), ensure_ascii=False)
    open(video + ".transcript.txt", "w").write("\n".join(lines))
    print("\n".join(lines))

def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def esc(t):
    return t.replace("\\", "").replace("{", "").replace("}", "")

def build_ass(words, start, end, hook, path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,560,1
Style: Hook,Inter,64,&H00000000,&H00000000,&H00136AFF,&H00136AFF,-1,0,0,0,100,100,0,0,3,18,0,8,90,90,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if hook:
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(end-start)},Hook,,0,0,0,,{esc(hook.upper())}")
    ws = [w for w in words if w["s"] >= start - 0.05 and w["e"] <= end + 0.05]
    # groupes de 3 mots ; le mot prononcé passe en orange
    for i in range(0, len(ws), 3):
        grp = ws[i:i+3]
        for j, cur in enumerate(grp):
            s0 = cur["s"] - start
            e0 = (grp[j+1]["s"] if j + 1 < len(grp) else cur["e"]) - start
            txt = " ".join(
                ("{\\c&H00136AFF&}" + esc(w["w"].upper()) + "{\\c&H00FFFFFF&}") if k == j else esc(w["w"].upper())
                for k, w in enumerate(grp))
            ev.append(f"Dialogue: 0,{ass_time(max(s0,0))},{ass_time(max(e0,s0+0.05))},Cap,,0,0,0,,{txt}")
    open(path, "w").write(head + "\n".join(ev) + "\n")

def clip(video, start, end, out, hook=""):
    start, end = float(start), float(end)
    wj = video + ".words.json"
    words = json.load(open(wj)) if os.path.exists(wj) else []
    ass = out + ".ass"
    build_ass(words, start, end, hook, ass)
    vf = ("scale=-2:1920,crop=1080:1920,setsar=1,"
          f"subtitles='{ass}'")
    # si la vidéo est trop étroite pour être recadrée en hauteur, on la met sur fond flou
    probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,color_transfer","-of","csv=p=0",video],capture_output=True,text=True).stdout.strip().split(",")
    w, h = int(probe[0]), int(probe[1])
    # vidéos HDR de l'iPhone (HLG / PQ) -> conversion SDR pour TikTok/Reels
    hdr = len(probe) > 2 and probe[2] in ("arib-std-b67", "smpte2084")
    tm = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
          "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,") if hdr else ""
    vf = tm + vf
    if w / h < 9 / 16:
        vf = tm + (f"split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];"
              f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,subtitles='{ass}'")
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(start),"-to",str(end),"-i",video,
                    "-vf",vf,"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-map","0:v:0","-map","0:a:0","-af","loudnorm=I=-14:TP=-1.5","-c:a","aac","-b:a","160k",
                    "-movflags","+faststart",out], check=True)
    print("OK", out)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "transcribe": transcribe(sys.argv[2])
    elif cmd == "clip": clip(*sys.argv[2:6], *(sys.argv[6:7] or [""]))
