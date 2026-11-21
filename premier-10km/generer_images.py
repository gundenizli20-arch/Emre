"""Génère les images d'annonce (Etsy, Gumroad, Payhip) à partir du PDF.

Usage : python3 generer_images.py  ->  images-annonce/01-couverture.png, etc.
Format 2000 x 1600 px (ratio 5:4, recommandé par Etsy).
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).parent
PDF = ICI / "premier-10km.pdf"
SORTIE = ICI / "images-annonce"
W, H = 2000, 1600
FOND = (255, 241, 234)
NUIT = (28, 43, 57)
ORANGE = (242, 98, 46)
GRIS = (91, 103, 112)
FD = "/usr/share/fonts/truetype/dejavu/"


def police(taille, gras=True):
    return ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if gras else "DejaVuSans.ttf"), taille)


def pages():
    d = Path(tempfile.mkdtemp())
    subprocess.run(["pdftoppm", "-r", "150", "-png", str(PDF), str(d / "p")], check=True)
    return {int(f.stem.split("-")[1]): Image.open(f).convert("RGB") for f in sorted(d.glob("p-*.png"))}


def coller(fond, page, hauteur, xy, angle=0):
    """Colle une page avec une ombre douce, éventuellement inclinée."""
    p = page.resize((int(page.width * hauteur / page.height), hauteur), Image.LANCZOS)
    marge = 60
    calque = Image.new("RGBA", (p.width + 2 * marge, p.height + 2 * marge), (0, 0, 0, 0))
    ombre = Image.new("RGBA", calque.size, (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rectangle([marge + 10, marge + 18, marge + p.width + 10, marge + p.height + 18],
                                    fill=(0, 0, 0, 90))
    ombre = ombre.filter(ImageFilter.GaussianBlur(18))
    calque.alpha_composite(ombre)
    calque.paste(p, (marge, marge))
    if angle:
        calque = calque.rotate(angle, resample=Image.BICUBIC, expand=True)
    x, y = xy
    fond.alpha_composite(calque, (int(x - calque.width / 2), int(y - calque.height / 2)))


def toile(couleur=FOND):
    return Image.new("RGBA", (W, H), couleur + (255,))


def texte(img, xy, t, taille, couleur=NUIT, gras=True, ancre="la"):
    ImageDraw.Draw(img).text(xy, t, font=police(taille, gras), fill=couleur, anchor=ancre)


def pastille(img, xy, t, taille=34):
    d = ImageDraw.Draw(img)
    f = police(taille)
    l, h_ = d.textbbox((0, 0), t, font=f)[2:]
    x, y = xy
    d.rounded_rectangle([x, y, x + l + 50, y + h_ + 30], radius=(h_ + 30) // 2, fill=ORANGE)
    d.text((x + 25, y + 12), t, font=f, fill="white")
    return x + l + 50


def sauver(img, nom):
    img.convert("RGB").save(SORTIE / nom, quality=95)
    print("•", nom)


def main():
    SORTIE.mkdir(exist_ok=True)
    pg = pages()

    # 1. Couverture
    img = toile()
    coller(img, pg[6], 1080, (1600, 840), angle=6)
    coller(img, pg[1], 1200, (1330, 820), angle=-3)
    texte(img, (110, 170), "PLAN PDF À IMPRIMER", 40, ORANGE)
    texte(img, (110, 240), "Mon premier", 92)
    texte(img, (100, 340), "10 km", 190, ORANGE)
    texte(img, (110, 560), "en 8 semaines", 76)
    y = 720
    for l in ["24 séances détaillées", "Calculateur d'allure", "Renfo + nutrition", "Carnet de suivi"]:
        texte(img, (110, y), "✓  " + l, 40, NUIT, gras=False)
        y += 70
    pastille(img, (110, 1380), "Téléchargement immédiat")
    sauver(img, "01-couverture.png")

    # 2. Le plan
    img = toile()
    coller(img, pg[6], 1420, (1430, 820))
    texte(img, (110, 220), "Le plan", 96)
    texte(img, (110, 340), "semaine par", 96)
    texte(img, (110, 460), "semaine", 96, ORANGE)
    y = 660
    for l in ["3 séances par semaine", "Durées en minutes :", "chacun à son rythme", "Semaine allégée", "et affûtage inclus",
              "Cases à cocher"]:
        texte(img, (110, y), l, 42, GRIS, gras=False)
        y += 66
    sauver(img, "02-plan.png")

    # 3. Contenu (3 pages en éventail)
    img = toile(NUIT)
    coller(img, pg[4], 980, (520, 960), angle=6)
    coller(img, pg[8], 980, (1480, 960), angle=-6)
    coller(img, pg[2], 1040, (1000, 930))
    texte(img, (W // 2, 120), "14 pages complètes", 88, (255, 255, 255), ancre="mm")
    texte(img, (W // 2, 230), "Allures · Échauffement · Renfo · Nutrition · Jour J · FAQ", 40, ORANGE, ancre="mm")
    sauver(img, "03-contenu.png")

    # 4. Allures
    img = toile()
    coller(img, pg[4], 1420, (570, 820))
    texte(img, (1100, 300), "Quelle allure", 84)
    texte(img, (1100, 410), "pour votre", 84)
    texte(img, (1100, 520), "objectif ?", 84, ORANGE)
    y = 720
    for l in ["De 50 min à 1 h 15", "Allure au km et vitesse", "Repères par sensations :", "pas besoin de montre GPS"]:
        texte(img, (1100, y), l, 42, GRIS, gras=False)
        y += 66
    sauver(img, "04-allures.png")

    # 5. Carnet de suivi
    img = toile()
    coller(img, pg[13], 1420, (1430, 820))
    texte(img, (110, 300), "Carnet de", 96)
    texte(img, (110, 420), "suivi", 96, ORANGE)
    texte(img, (110, 540), "à imprimer", 96)
    y = 740
    for l in ["Notez chaque séance", "Durée, distance, ressenti", "et voyez vos progrès"]:
        texte(img, (110, y), l, 42, GRIS, gras=False)
        y += 66
    sauver(img, "05-carnet.png")

    # 6. Renfo + nutrition
    img = toile()
    coller(img, pg[8], 1250, (560, 830), angle=-3)
    coller(img, pg[9], 1250, (1440, 830), angle=3)
    texte(img, (W // 2, 110), "Renforcement + nutrition", 76, NUIT, ancre="mm")
    sauver(img, "06-renfo-nutrition.png")


if __name__ == "__main__":
    main()
