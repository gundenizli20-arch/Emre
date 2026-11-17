# Emre
Prince

## clipper.py — clips courts (TikTok / Shorts / Reels)

Découpe des passages d'une vidéo longue (stream, podcast…) en clips verticaux 9:16.

**Prérequis :** `ffmpeg`. Optionnel : `pip install faster-whisper` pour les sous-titres auto.

```bash
# Clips manuels (debut-fin [titre])
python3 clipper.py stream.mp4 -c 01:20-01:45 -c "12:03-12:40 Le fail"

# Depuis un fichier (une ligne par clip, # = commentaire)
python3 clipper.py stream.mp4 -f clips.txt

# Détection automatique des 5 moments les plus forts (volume audio), 30 s chacun
python3 clipper.py stream.mp4 --auto 5 --duree 30

# Avec sous-titres automatiques style TikTok, en français
python3 clipper.py stream.mp4 -f clips.txt --sous-titres --langue fr
```

| Option | Effet |
|---|---|
| `--format fit` (défaut) | 9:16, vidéo entière au centre + fond flouté |
| `--format crop` | 9:16, recadrage au centre |
| `--format original` | garde le format d'origine |
| `-o DOSSIER` | dossier de sortie (défaut `clips/`) |
| `--crf`, `--preset` | qualité / vitesse d'encodage x264 |
| `--modele` | modèle Whisper (`tiny`, `base`, `small`, `medium`…) |
