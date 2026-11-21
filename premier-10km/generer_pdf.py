"""Génère le guide PDF « Mon premier 10 km en 8 semaines ».

Usage : python3 generer_pdf.py   ->  produit premier-10km.pdf dans ce dossier.
Pour personnaliser : modifiez AUTEUR, SITE et les textes ci-dessous.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

AUTEUR = "[Votre nom]"
SITE = "[votre-site.fr / @votre_compte]"
SORTIE = Path(__file__).with_name("premier-10km.pdf")

# ---------- Polices & couleurs ----------
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold",
                              italic="Sans", boldItalic="Sans-Bold")

ORANGE = colors.HexColor("#F2622E")
NUIT = colors.HexColor("#1C2B39")
GRIS = colors.HexColor("#5B6770")
CLAIR = colors.HexColor("#FFF1EA")
VERT = colors.HexColor("#2E9E6B")
BLEU = colors.HexColor("#2F6FB3")
LIGNE = colors.HexColor("#E3E6E8")

W, H = A4
MARGE = 20 * mm

# ---------- Styles ----------
def st(name, **kw):
    base = dict(fontName="Sans", fontSize=10.5, leading=15.5, textColor=NUIT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    "h1": st("h1", fontName="Sans-Bold", fontSize=22, leading=27, textColor=NUIT, spaceAfter=4),
    "kicker": st("kicker", fontName="Sans-Bold", fontSize=9, leading=12, textColor=ORANGE, spaceAfter=2),
    "h2": st("h2", fontName="Sans-Bold", fontSize=13.5, leading=18, textColor=ORANGE, spaceBefore=10, spaceAfter=4),
    "p": st("p", spaceAfter=6),
    "small": st("small", fontSize=8.5, leading=12, textColor=GRIS),
    "cell": st("cell", fontSize=9, leading=12.5),
    "cellb": st("cellb", fontName="Sans-Bold", fontSize=9, leading=12.5),
    "cellw": st("cellw", fontName="Sans-Bold", fontSize=9, leading=12.5, textColor=colors.white),
    "box": st("box", fontSize=10, leading=14.5),
    "center": st("center", alignment=TA_CENTER),
}


def P(t, s="p"):
    return Paragraph(t, S[s])


def bullets(items, s="p"):
    return [Paragraph(f"<font color='#F2622E'>●</font>&nbsp;&nbsp;{i}", S[s]) for i in items]


def encadre(titre, contenu, fond=CLAIR, bord=ORANGE):
    """Petit encadré coloré (conseil, attention…)."""
    corps = [Paragraph(f"<b>{titre}</b>", S["box"])]
    corps += [Paragraph(c, S["box"]) for c in contenu]
    t = Table([[corps]], colWidths=[W - 2 * MARGE])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fond),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bord),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 8)])


def tableau(data, largeurs, entete=ORANGE, zebra=True):
    rows = []
    for i, row in enumerate(data):
        style = "cellw" if i == 0 else "cell"
        rows.append([c if not isinstance(c, str) else Paragraph(c, S[style]) for c in row])
    t = Table(rows, colWidths=largeurs, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), entete),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGNE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if zebra:
        for r in range(2, len(rows), 2):
            cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F7F8F9")))
    t.setStyle(TableStyle(cmds))
    return t


def titre_page(kicker, titre):
    return [P(kicker.upper(), "kicker"), P(titre, "h1"), Spacer(1, 6)]


# ---------- Décor des pages ----------
def couverture(c, doc):
    c.saveState()
    c.setFillColor(NUIT)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # bandes de « piste »
    c.setFillColor(ORANGE)
    c.rect(0, H * 0.36, W, 16 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#F58A5F"))
    c.rect(0, H * 0.36 + 16 * mm, W, 3 * mm, fill=1, stroke=0)
    c.setStrokeColor(colors.white)
    c.setLineWidth(1.2)
    c.setDash(10, 8)
    c.line(0, H * 0.36 + 8 * mm, W, H * 0.36 + 8 * mm)
    c.setDash()
    # titre
    c.setFillColor(ORANGE)
    c.setFont("Sans-Bold", 12)
    c.drawString(MARGE, H - 45 * mm, "GUIDE D'ENTRAÎNEMENT · COURSE À PIED")
    c.setFillColor(colors.white)
    c.setFont("Sans-Bold", 44)
    c.drawString(MARGE, H - 72 * mm, "Mon premier")
    c.setFont("Sans-Bold", 80)
    c.setFillColor(ORANGE)
    c.drawString(MARGE - 3, H - 105 * mm, "10 km")
    c.setFillColor(colors.white)
    c.setFont("Sans-Bold", 30)
    c.drawString(MARGE, H - 125 * mm, "en 8 semaines")
    c.setFont("Sans", 13)
    c.setFillColor(colors.HexColor("#C9D2DA"))
    y = H - 143 * mm
    for ligne in ["Le plan pas à pas pour passer de 20 minutes de course",
                  "à la ligne d'arrivée d'un 10 km, sans vous blesser."]:
        c.drawString(MARGE, y, ligne)
        y -= 7 * mm
    # points clés
    c.setFont("Sans-Bold", 11)
    c.setFillColor(colors.white)
    y = H * 0.36 - 18 * mm
    for txt in ["✓  24 séances détaillées, 3 par semaine",
                "✓  Calculateur d'allure selon votre objectif",
                "✓  Renforcement, nutrition, jour J",
                "✓  Carnet de suivi à imprimer"]:
        c.drawString(MARGE, y, txt)
        y -= 8 * mm
    c.setFont("Sans", 10)
    c.setFillColor(colors.HexColor("#8D9AA6"))
    c.drawString(MARGE, 18 * mm, f"Par {AUTEUR}  ·  {SITE}")
    c.restoreState()


def page_normale(c, doc):
    c.saveState()
    c.setFillColor(ORANGE)
    c.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
    c.setFont("Sans", 8)
    c.setFillColor(GRIS)
    c.drawString(MARGE, 12 * mm, "Mon premier 10 km en 8 semaines")
    c.drawRightString(W - MARGE, 12 * mm, f"{doc.page}")
    c.setStrokeColor(LIGNE)
    c.line(MARGE, 16 * mm, W - MARGE, 16 * mm)
    c.restoreState()


# ---------- Contenu ----------
def contenu():
    s = [NextPageTemplate("normale"), PageBreak()]

    # Sommaire
    s += titre_page("Bienvenue", "Sommaire")
    somm = [
        ("1", "Avant de commencer", "Le test de départ et les règles d'or"),
        ("2", "Comprendre les allures", "Endurance, allure 10 km, sensations"),
        ("3", "L'échauffement type", "10 minutes à faire avant chaque séance"),
        ("4", "Le plan semaine par semaine", "Les 24 séances détaillées"),
        ("5", "Renforcement musculaire", "15 minutes, 2 fois par semaine"),
        ("6", "Nutrition & hydratation", "Manger pour courir mieux"),
        ("7", "Équipement", "L'essentiel, sans se ruiner"),
        ("8", "Le jour J", "Check-list et stratégie de course"),
        ("9", "Questions fréquentes", "Douleurs, séance ratée, météo…"),
        ("10", "Carnet de suivi", "À imprimer et remplir"),
    ]
    rows = [[Paragraph(f"<font color='#F2622E'><b>{n}</b></font>", S["h2"]),
             Paragraph(f"<b>{t}</b><br/><font color='#5B6770' size='9'>{d}</font>", S["p"])]
            for n, t, d in somm]
    t = Table(rows, colWidths=[16 * mm, W - 2 * MARGE - 16 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, LIGNE),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    s += [t, Spacer(1, 14)]
    s.append(encadre("Avertissement santé", [
        "Ce guide propose des conseils généraux d'entraînement et ne remplace pas l'avis d'un "
        "professionnel de santé. Consultez votre médecin avant de commencer, surtout si vous avez "
        "plus de 40 ans, des antécédents cardiaques, une pathologie ou si vous reprenez le sport "
        "après une longue pause. En France, un certificat médical (ou un PPS) est en général demandé "
        "pour participer à une course officielle. Arrêtez-vous en cas de douleur thoracique, "
        "d'essoufflement anormal ou de vertige."], fond=colors.HexColor("#EEF3F8"), bord=BLEU))
    s.append(PageBreak())

    # 1. Avant de commencer
    s += titre_page("Chapitre 1", "Avant de commencer")
    s.append(P("Ce plan s'adresse aux coureurs débutants qui savent déjà <b>courir 20 minutes sans "
               "s'arrêter</b>, même lentement. En 8 semaines, à raison de 3 séances par semaine, "
               "vous allez progressivement doubler puis tripler ce temps de course, apprendre à "
               "gérer votre allure, et franchir la ligne d'un 10 km en pleine forme."))
    s.append(P("Le test de départ", "h2"))
    s.append(P("Avant la semaine 1, faites ce test simple : courez <b>20 minutes</b> à un rythme "
               "où vous pouvez encore parler en phrases courtes."))
    s += bullets([
        "<b>Réussi facilement ?</b> Parfait, commencez le plan dès la semaine prochaine.",
        "<b>Réussi mais difficile ?</b> Commencez quand même, en ralentissant franchement lors des footings.",
        "<b>Pas réussi ?</b> Faites d'abord 2 à 3 semaines d'alternance course/marche "
        "(par ex. 3 min de course / 1 min de marche × 6), puis refaites le test.",
    ])
    s.append(P("Les 7 règles d'or", "h2"))
    regles = [
        ("Lentement, c'est bien.", "80 % de vos séances doivent se faire à allure facile, où vous pouvez parler."),
        ("Jamais deux jours de suite.", "Laissez au moins un jour de repos (ou de marche) entre deux séances."),
        ("Régularité avant intensité.", "Trois séances moyennes valent mieux qu'une séance héroïque."),
        ("Le temps, pas la distance.", "Les séances sont exprimées en minutes : chacun avance à son rythme."),
        ("Écoutez la douleur.", "Une gêne qui augmente pendant la course est un signal d'arrêt."),
        ("Dormez.", "La progression se fait pendant la récupération, pas pendant l'effort."),
        ("Notez tout.", "Le carnet de suivi en fin de guide vous montrera vos progrès."),
    ]
    rows = [[Paragraph(f"<b>{i}</b>", S["cellw"]), Paragraph(f"<b>{a}</b> {b}", S["cell"])]
            for i, (a, b) in enumerate(regles, 1)]
    t = Table(rows, colWidths=[10 * mm, W - 2 * MARGE - 10 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), ORANGE),
                           ("ALIGN", (0, 0), (0, -1), "CENTER"),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LINEBELOW", (0, 0), (-1, -1), 2, colors.white),
                           ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F7F8F9")),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s.append(t)
    s.append(P("Organiser sa semaine", "h2"))
    s.append(tableau([
        ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        ["Repos", "<b>Séance 1</b><br/>Footing", "Renfo<br/>ou repos", "<b>Séance 2</b><br/>Qualité",
         "Repos", "Renfo<br/>ou repos", "<b>Séance 3</b><br/>Sortie longue"],
    ], [(W - 2 * MARGE) / 7] * 7, zebra=False))
    s.append(P("Exemple à adapter à votre emploi du temps : l'important est d'espacer les séances.", "small"))
    s.append(PageBreak())

    # 2. Allures
    s += titre_page("Chapitre 2", "Comprendre les allures")
    s.append(P("Dans le plan, vous trouverez trois types d'allures. Pas besoin de montre GPS : "
               "vos <b>sensations</b> suffisent. Une montre ou une application (Strava, Nike Run "
               "Club…) peut toutefois vous aider à vérifier votre rythme."))
    s.append(tableau([
        ["Allure", "Sensation (sur 10)", "Test de la parole", "Usage"],
        ["<b>EF</b> – Endurance fondamentale", "3 à 4 / 10 — facile", "Vous tenez une conversation",
         "Footings, sortie longue, échauffement"],
        ["<b>A10</b> – Allure 10 km", "6 à 7 / 10 — soutenu", "Quelques mots seulement",
         "Fractionnés, simulation de course"],
        ["<b>Vif</b> – Lignes droites", "8 / 10 — rapide mais relâché", "Impossible de parler",
         "Accélérations de 15 à 20 secondes"],
    ], [42 * mm, 38 * mm, 40 * mm, W - 2 * MARGE - 120 * mm]))
    s.append(P("Quel objectif de temps choisir ?", "h2"))
    s.append(P("Pour un premier 10 km, l'objectif numéro 1 est de <b>finir en forme</b>. Si vous "
               "voulez un repère chiffré, utilisez ce tableau. L'allure EF est environ 1 min à "
               "1 min 30 plus lente au kilomètre que l'allure 10 km."))
    s.append(tableau([
        ["Objectif 10 km", "Allure 10 km (A10)", "Vitesse", "Allure EF (approx.)"],
        ["1 h 15", "7 min 30 / km", "8,0 km/h", "8 min 30 – 9 min / km"],
        ["1 h 10", "7 min 00 / km", "8,6 km/h", "8 min 00 – 8 min 30 / km"],
        ["1 h 05", "6 min 30 / km", "9,2 km/h", "7 min 30 – 8 min 00 / km"],
        ["1 h 00", "6 min 00 / km", "10,0 km/h", "7 min 00 – 7 min 30 / km"],
        ["55 min", "5 min 30 / km", "10,9 km/h", "6 min 30 – 7 min 00 / km"],
        ["50 min", "5 min 00 / km", "12,0 km/h", "6 min 00 – 6 min 30 / km"],
    ], [38 * mm, 42 * mm, 30 * mm, W - 2 * MARGE - 110 * mm]))
    s.append(Spacer(1, 6))
    s.append(encadre("Comment choisir votre objectif", [
        "Regardez votre test de 20 minutes : si vous avez parcouru environ 2,5 km, visez 1 h 10 à "
        "1 h 15 ; environ 3 km, visez 1 h à 1 h 05 ; 3,5 km ou plus, visez 55 min. "
        "Ajustez en semaine 5 selon vos sensations."]))
    s.append(PageBreak())

    # 3. Échauffement
    s += titre_page("Chapitre 3", "L'échauffement type")
    s.append(P("À faire avant les séances de <b>qualité</b> (séance 2) et le jour de la course. "
               "Pour les footings, les 5 à 10 premières minutes très lentes suffisent."))
    s.append(tableau([
        ["Durée", "Exercice", "Comment faire"],
        ["5 min", "Marche rapide puis trot", "Commencez en marchant, puis trottinez très lentement."],
        ["30 s", "Montées de genoux", "Sur place ou en avançant, genoux à hauteur des hanches."],
        ["30 s", "Talons-fesses", "Petites foulées, talons qui viennent toucher les fesses."],
        ["30 s", "Pas chassés", "15 secondes de chaque côté, bras relâchés."],
        ["1 min", "Cercles articulaires", "Chevilles, genoux, hanches, épaules : 10 cercles chacun."],
        ["10 balanc.", "Balancés de jambe", "Debout, appuyé à un mur, avant-arrière puis latéral."],
        ["2 × 15 s", "Accélérations progressives", "Accélérez doucement jusqu'à l'allure 10 km, puis relâchez."],
    ], [22 * mm, 46 * mm, W - 2 * MARGE - 68 * mm]))
    s.append(Spacer(1, 8))
    s.append(P("Le retour au calme", "h2"))
    s.append(P("Après chaque séance : <b>5 minutes de trot ou de marche</b>, puis quelques étirements "
               "doux et sans à-coups (mollets, quadriceps, ischio-jambiers, fessiers), 20 à 30 "
               "secondes chacun. Pas d'étirements forcés juste après une séance intense."))
    s.append(encadre("Astuce", [
        "Buvez un grand verre d'eau et mangez une collation (banane, yaourt, poignée d'amandes) "
        "dans l'heure qui suit la séance : votre récupération sera meilleure."]))
    s.append(PageBreak())

    # 4. Plan
    s += titre_page("Chapitre 4", "Le plan semaine par semaine")
    s.append(P("Chaque semaine contient trois séances. Les durées <b>incluent</b> l'échauffement et "
               "le retour au calme. « Récup » signifie trottiner très lentement (ou marcher si besoin). "
               "Cochez chaque séance réalisée !"))
    plan = [
        ("Semaine 1", "Prise de rythme", "1 h 20",
         ["25 min EF", "20 min EF + 4 lignes droites de 15 s (récup 45 s)", "30 min EF"]),
        ("Semaine 2", "Premiers changements de rythme", "1 h 30",
         ["25 min EF", "Échauffement 10 min + 6 × (1 min A10 / 2 min récup) + 5 min calme", "35 min EF"]),
        ("Semaine 3", "On allonge", "1 h 40",
         ["30 min EF", "Échauffement 10 min + 5 × (2 min A10 / 2 min récup) + 5 min calme", "40 min EF"]),
        ("Semaine 4", "Semaine allégée — on assimile", "1 h 25",
         ["25 min EF", "20 min EF + 4 lignes droites de 20 s", "35 min EF"]),
        ("Semaine 5", "Le cœur du plan", "1 h 55",
         ["30 min EF", "Échauffement 10 min + 4 × (4 min A10 / 2 min récup) + 5 min calme", "45 min EF"]),
        ("Semaine 6", "Montée en endurance", "2 h 10",
         ["35 min EF", "Échauffement 10 min + 3 × (6 min A10 / 2 min récup) + 5 min calme",
          "55 min EF (marchez 1 min à mi-parcours si besoin)"]),
        ("Semaine 7", "La semaine la plus longue", "2 h 20",
         ["35 min EF", "Échauffement 15 min + 15 min continu à A10 + 5 min calme",
          "1 h 05 EF — vous approchez de la distance du 10 km !"]),
        ("Semaine 8", "Affûtage & jour J", "Course",
         ["30 min EF + 4 lignes droites (début de semaine)",
          "20 min EF dont 2 × 4 min A10 (2 à 3 jours avant la course)",
          "<b>COURSE : votre premier 10 km !</b>"]),
    ]
    larg = W - 2 * MARGE
    for nom, theme, vol, seances in plan:
        couleur = VERT if nom == "Semaine 4" else (NUIT if nom == "Semaine 8" else ORANGE)
        rows = [[Paragraph(f"<b>{nom.upper()}</b> · {theme}", S["cellw"]),
                 Paragraph(f"<b>{vol}</b>", S["cellw"])]]
        for i, se in enumerate(seances, 1):
            label = ["Footing", "Qualité", "Sortie longue"][i - 1] if nom != "Semaine 8" else \
                ["Footing", "Rappel", "Jour J"][i - 1]
            rows.append([Paragraph(f"☐&nbsp;&nbsp;<b>S{i} · {label}</b> — {se}", S["cell"]), ""])
        t = Table(rows, colWidths=[larg - 26 * mm, 26 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), couleur),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("SPAN", (0, 1), (1, 1)), ("SPAN", (0, 2), (1, 2)), ("SPAN", (0, 3), (1, 3)),
            ("BOX", (0, 0), (-1, -1), 0.6, LIGNE),
            ("LINEBELOW", (0, 1), (-1, -2), 0.4, LIGNE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        s.append(KeepTogether([t, Spacer(1, 9)]))
    s.append(P("Volume total de la semaine indiqué à droite. En vert : semaine allégée, "
               "volontairement plus facile pour laisser le corps s'adapter.", "small"))
    s.append(Spacer(1, 6))
    s.append(encadre("Et si je rate une séance ?", [
        "Pas de panique. Ne cherchez pas à « rattraper » en doublant les séances. Sautez-la et "
        "reprenez le plan normalement. Si vous ratez une semaine entière, refaites la semaine "
        "précédente avant de continuer."]))
    s.append(PageBreak())

    # 5. Renfo
    s += titre_page("Chapitre 5", "Renforcement musculaire")
    s.append(P("15 minutes, 2 fois par semaine, à la maison et sans matériel. Le renforcement "
               "réduit le risque de blessure et rend votre foulée plus efficace. Faites "
               "<b>2 à 3 tours</b> du circuit, avec 1 minute de pause entre les tours."))
    s.append(tableau([
        ["Exercice", "Durée / Répét.", "Consignes"],
        ["<b>Squat</b>", "15 répétitions", "Pieds largeur des hanches, descendez comme pour vous asseoir, dos droit."],
        ["<b>Fentes avant</b>", "10 par jambe", "Grand pas en avant, genou arrière vers le sol, buste droit."],
        ["<b>Pont fessier</b>", "15 répétitions", "Allongé sur le dos, montez le bassin en serrant les fessiers."],
        ["<b>Gainage ventral (planche)</b>", "30 secondes", "Sur les avant-bras, corps aligné, ne creusez pas le dos."],
        ["<b>Gainage latéral</b>", "20 s par côté", "Sur un avant-bras, hanches hautes, corps bien droit."],
        ["<b>Montées sur pointes</b>", "20 répétitions", "Sur une marche, montez sur la pointe des pieds puis redescendez lentement."],
        ["<b>Équilibre unipodal</b>", "30 s par pied", "Debout sur un pied, genou légèrement fléchi. Yeux fermés pour corser."],
    ], [48 * mm, 32 * mm, W - 2 * MARGE - 80 * mm]))
    s.append(Spacer(1, 8))
    s.append(P("Progression", "h2"))
    s += bullets([
        "<b>Semaines 1 à 3 :</b> 2 tours, au rythme indiqué.",
        "<b>Semaines 4 à 6 :</b> 3 tours, gainage porté à 45 secondes.",
        "<b>Semaines 7 et 8 :</b> 2 tours, et aucun renforcement dans les 3 jours avant la course.",
    ])
    s.append(encadre("Bon à savoir", [
        "Des courbatures légères sont normales les premières semaines. Une douleur vive ou "
        "articulaire ne l'est pas : arrêtez l'exercice concerné."]))
    s.append(PageBreak())

    # 6. Nutrition
    s += titre_page("Chapitre 6", "Nutrition & hydratation")
    s.append(P("Pas besoin de régime spécial pour courir 10 km. Une alimentation variée et "
               "quelques bons réflexes suffisent."))
    s.append(P("Au quotidien", "h2"))
    s += bullets([
        "<b>Des glucides à chaque repas</b> : pâtes, riz, pain complet, pommes de terre, flocons d'avoine.",
        "<b>Des protéines</b> pour réparer les muscles : œufs, poisson, viande, légumineuses, produits laitiers, tofu.",
        "<b>Des fruits et légumes</b> à volonté pour les vitamines et minéraux.",
        "<b>Boire régulièrement</b> : environ 1,5 à 2 litres d'eau par jour, plus s'il fait chaud.",
    ])
    s.append(P("Autour des séances", "h2"))
    s.append(tableau([
        ["Moment", "Quoi manger", "Exemples"],
        ["2 à 3 h avant", "Un repas léger et digeste", "Riz + poulet + légumes cuits ; pâtes + jambon"],
        ["30 à 60 min avant", "Une petite collation si besoin", "Une banane, une compote, une tranche de pain + miel"],
        ["Pendant (< 1 h 15)", "De l'eau si soif", "Pas besoin de gel ni de boisson sucrée"],
        ["Après (dans l'heure)", "Glucides + protéines", "Yaourt + fruit ; verre de lait + tartine ; omelette + pain"],
    ], [36 * mm, 50 * mm, W - 2 * MARGE - 86 * mm]))
    s.append(P("La veille de la course", "h2"))
    s.append(P("Un repas « classique » riche en glucides (par exemple des pâtes), sans excès et "
               "sans nouveauté. Évitez les plats très gras, épicés ou riches en fibres, et "
               "l'alcool. Ne testez <b>rien de nouveau</b> la veille ou le jour J."))
    s.append(encadre("Petit-déjeuner type du jour J (3 h avant le départ)", [
        "Pain ou flocons d'avoine, un peu de confiture ou de miel, une banane, un thé ou café si "
        "vous en avez l'habitude, et un grand verre d'eau. Testez-le avant votre sortie longue de "
        "la semaine 7 !"]))
    s.append(PageBreak())

    # 7. Équipement
    s += titre_page("Chapitre 7", "Équipement")
    s.append(P("La course à pied est l'un des sports les moins chers. Voici l'essentiel."))
    s.append(tableau([
        ["Élément", "Priorité", "Conseil"],
        ["<b>Chaussures de running</b>", "Indispensable",
         "Essayez-les en magasin en fin de journée, avec vos chaussettes de sport. Prenez du confort, pas du style. Comptez 60 à 120 €."],
        ["<b>Chaussettes techniques</b>", "Très utile", "Sans coton, pour éviter les ampoules."],
        ["<b>Tenue respirante</b>", "Utile", "T-shirt et short en matière synthétique. Habillez-vous comme s'il faisait 10 °C de plus."],
        ["<b>Brassière de sport</b>", "Indispensable (femmes)", "Maintien adapté à un sport à fort impact."],
        ["<b>Montre GPS / appli</b>", "Optionnel", "Une application gratuite sur téléphone suffit pour débuter."],
        ["<b>Gilet réfléchissant / lampe</b>", "Sécurité", "Indispensable si vous courez de nuit ou au bord des routes."],
    ], [46 * mm, 32 * mm, W - 2 * MARGE - 78 * mm]))
    s.append(Spacer(1, 8))
    s.append(encadre("À éviter", [
        "Courir avec de vieilles baskets usées ou des chaussures « de ville ». Et ne jamais "
        "étrenner des chaussures neuves le jour de la course : faites-les d'abord sur 3 ou 4 sorties."]))
    s.append(PageBreak())

    # 8. Jour J
    s += titre_page("Chapitre 8", "Le jour J")
    s.append(P("La check-list de la veille", "h2"))
    for item in ["Dossard et épingles (ou ceinture porte-dossard)", "Certificat médical / PPS si demandé",
                 "Tenue testée à l'entraînement, adaptée à la météo", "Chaussures déjà portées",
                 "Montre ou téléphone chargé", "Bouteille d'eau et collation d'après-course",
                 "Vêtement chaud à mettre avant le départ (un vieux sweat à abandonner)",
                 "Heure de réveil calculée : petit-déjeuner 3 h avant le départ"]:
        s.append(P(f"☐&nbsp;&nbsp;{item}"))
    s.append(P("La stratégie de course", "h2"))
    s.append(tableau([
        ["Portion", "Stratégie"],
        ["<b>Avant le départ</b>", "Arrivez 45 min en avance. Échauffement léger 10 min (chapitre 3). Placez-vous plutôt à l'arrière du peloton."],
        ["<b>Km 0 à 3</b>", "<b>Partez lentement !</b> L'erreur n°1 des débutants est de partir trop vite, porté par l'ambiance. Restez un peu plus lent que votre allure objectif."],
        ["<b>Km 3 à 7</b>", "Trouvez votre allure 10 km et installez-vous. Buvez au ravitaillement si vous en avez besoin (marcher pour boire est autorisé !)."],
        ["<b>Km 7 à 9</b>", "C'est là que ça devient dur : c'est normal. Concentrez-vous sur votre respiration et restez relâché des épaules."],
        ["<b>Dernier km</b>", "S'il vous reste de l'énergie, accélérez progressivement. Profitez de l'arrivée !"],
    ], [34 * mm, W - 2 * MARGE - 34 * mm]))
    s.append(Spacer(1, 8))
    s.append(encadre("Après la course", [
        "Marchez 10 minutes, buvez, mangez. Prenez 3 à 5 jours de repos ou de marche avant de "
        "recourir tranquillement. Et notez votre temps : c'est votre premier record personnel !"],
        fond=colors.HexColor("#EAF6F0"), bord=VERT))
    s.append(PageBreak())

    # 9. FAQ
    s += titre_page("Chapitre 9", "Questions fréquentes")
    faq = [
        ("J'ai un point de côté, que faire ?",
         "Ralentissez, expirez longuement et appuyez doucement sur la zone. Évitez de manger juste avant de courir."),
        ("J'ai mal aux tibias / aux genoux.",
         "Réduisez le volume, privilégiez des surfaces plus souples (chemins, herbe) et vérifiez l'usure de vos chaussures. "
         "Si la douleur persiste plus de quelques jours, consultez un médecin ou un kinésithérapeute."),
        ("Je n'arrive pas à finir une séance.",
         "Ralentissez : la plupart du temps, on court trop vite. Vous pouvez aussi marcher 1 minute puis repartir. "
         "Finir la durée prévue est plus important que l'allure."),
        ("Puis-je courir sur tapis ?",
         "Oui. Réglez une inclinaison de 1 % pour compenser l'absence de vent. Faites tout de même la sortie longue dehors si possible."),
        ("Il pleut / il fait très chaud.",
         "La pluie n'empêche pas de courir. Par forte chaleur, courez tôt le matin ou le soir, ralentissez et emportez de l'eau."),
        ("Je suis malade.",
         "Rhume léger sans fièvre : footing très doux possible. Fièvre, courbatures générales ou symptômes sous le cou : repos complet."),
        ("Et après le 10 km ?",
         "Vous pouvez chercher à améliorer votre temps sur 10 km, ou viser le semi-marathon (21,1 km) dans 3 à 4 mois."),
    ]
    for q, r in faq:
        s.append(KeepTogether([P(f"<b>{q}</b>", "h2"), P(r)]))
    s.append(PageBreak())

    # 10. Carnet
    s += titre_page("Chapitre 10", "Carnet de suivi")
    s.append(P("Imprimez cette page et notez chaque séance. Ressenti : de 1 (très facile) à 10 (épuisant)."))
    data = [["Sem", "Séance", "Date", "Durée", "Distance", "Ressenti", "Remarques"]]
    for sem in range(1, 9):
        for se in range(1, 4):
            data.append([str(sem) if se == 1 else "", f"S{se}", "", "", "", "/10", ""])
    t = tableau(data, [13 * mm, 18 * mm, 20 * mm, 17 * mm, 20 * mm, 20 * mm, W - 2 * MARGE - 108 * mm])
    t.setStyle(TableStyle([("TOPPADDING", (0, 1), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 1), (-1, -1), 2.2)]))
    s.append(t)
    s.append(PageBreak())

    # Fin
    s.append(Spacer(1, 50 * mm))
    s.append(P("Félicitations !", "h1"))
    s.append(P("Si vous lisez cette page après votre course, vous faites désormais partie des "
               "coureurs qui ont bouclé un 10 km. Bravo pour votre régularité et votre persévérance."))
    s.append(Spacer(1, 10))
    s.append(encadre("Partagez votre réussite", [
        f"Envoyez-moi votre temps ou une photo de votre arrivée : {SITE}",
        "Votre avis m'aide énormément : si ce guide vous a plu, laissez une évaluation sur la "
        "plateforme où vous l'avez acheté."]))
    s.append(Spacer(1, 20))
    s.append(P(f"© 2026 {AUTEUR}. Tous droits réservés. Ce guide est destiné à un usage personnel. "
               "Toute reproduction, revente ou diffusion, même partielle, sans autorisation est interdite.",
               "small"))
    return s


def main():
    doc = BaseDocTemplate(str(SORTIE), pagesize=A4, leftMargin=MARGE, rightMargin=MARGE,
                          topMargin=20 * mm, bottomMargin=22 * mm,
                          title="Mon premier 10 km en 8 semaines", author=AUTEUR)
    cadre = Frame(MARGE, 22 * mm, W - 2 * MARGE, H - 42 * mm, id="f")
    doc.addPageTemplates([
        PageTemplate("couverture", [Frame(0, 0, W, H, id="c")], onPage=couverture),
        PageTemplate("normale", [cadre], onPage=page_normale),
    ])
    doc.build(contenu())
    print("PDF généré :", SORTIE)


if __name__ == "__main__":
    main()
