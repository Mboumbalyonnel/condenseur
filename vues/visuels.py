"""Éléments visuels : bandeau d'état, parcours des 3 phases, frise horaire, tuiles de cause,
arbre de décision dessiné."""

from __future__ import annotations

import pandas as pd

from condenseur.diagnostic import ALERTE_GRAVE, ALERTE_LEGERE, NORMAL
from condenseur.moteur import NOMS_PHASES
from vues.composants import fmt
from vues.icones import icone

VAR_NIVEAU = {NORMAL: "var(--ok)", ALERTE_LEGERE: "var(--attention)", ALERTE_GRAVE: "var(--critique)"}
VAR_PHASE = {1: "var(--ok)", 2: "var(--attention)", 3: "var(--critique)"}


def parcours_phases(df: pd.DataFrame) -> str:
    """Barre des 3 phases (largeur proportionnelle à leur durée) avec le curseur de la dernière mesure."""
    n = len(df)
    phase_courante = int(df["PHASE"].iloc[-1])
    segments, noms = [], []
    for phase, g in df.groupby("PHASE"):
        largeur = len(g) / n * 100
        classe = "seg fait" if phase <= phase_courante else "seg"
        segments.append(f'<div class="{classe}" style="width:{largeur:.2f}%;background:{VAR_PHASE[phase]}"></div>')
        noms.append(f'<span style="width:{largeur:.2f}%">Phase {phase} · H{g["HEURE"].min()} à H{g["HEURE"].max()}</span>')
    return (f'<div class="parcours"><div class="lib">{icone("calque", 15)}<span>Chronologie de la simulation</span></div>'
            f'<div style="position:relative;margin-top:.5rem"><div class="barre">{"".join(segments)}</div>'
            f'<div class="curseur" style="left:calc(100% - 3px)"></div></div><div class="noms">{"".join(noms)}</div></div>')


def bandeau(etat: str, niveau: str, sous_titre: str, centre: str, libelle_chiffre: str, chiffre: str, unite: str) -> str:
    return (f'<div class="hero etat-{etat}">'
            f'<div><div class="lib">{icone("sante", 15)}<span>État du condenseur</span></div>'
            f'<div class="grand"><i></i>{niveau}</div><div class="sub">{sous_titre}</div></div>'
            f'<div>{centre}</div>'
            f'<div><div class="lib">{icone("monnaie", 15)}<span>{libelle_chiffre}</span></div>'
            f'<div class="chiffre">{chiffre}<small>{unite}</small></div></div></div>')


def frise_horaire(df: pd.DataFrame) -> str:
    """Une case par heure, colorée selon le niveau d'alerte (survol : détail de l'heure)."""
    cases = "".join(
        f'<b style="background:{VAR_NIVEAU[r.NIVEAU]}" '
        f'title="H{r.HEURE} · {r.TIMESTAMP:%d/%m %H:%M} · ΔTapp {fmt(r.DT_APP_C, 2)} °C · {r.NIVEAU}"></b>'
        for r in df.itertuples())
    axe = "".join(f'<span style="width:{len(g) / len(df) * 100:.2f}%">{NOMS_PHASES[p]}</span>'
                  for p, g in df.groupby("PHASE"))
    legende = "".join(f'<span><i style="background:{c}"></i>{n}</span>' for n, c in VAR_NIVEAU.items())
    return f'<div class="frise">{cases}</div><div class="frise-axe">{axe}</div><div class="legende">{legende}</div>'


CATEGORIES_VISUELLES = [
    ("Hydraulique", "goutte", "Pompe, niveau du bac, pression de pulvérisation"),
    ("Aéraulique", "ventilateur", "Ventilateur et variateur de fréquence"),
    ("Entartrage", "calque", "Encrassement des faisceaux d'échange"),
]


def tuiles_categories(categorie: str, etat: str) -> str:
    tuiles = []
    for nom, ic, description in CATEGORIES_VISUELLES:
        active = " active" if nom == categorie else ""
        tuiles.append(f'<div class="tuile etat-{etat}{active}">{icone(ic, 26)}<div class="t">{nom}</div>'
                      f'<div class="d">{description}</div></div>')
    return f'<div class="tuiles">{"".join(tuiles)}</div>'


def arbre_svg(etapes: list[tuple[str, bool, str]], etat: str) -> str:
    """Arbre de décision dessiné : questions en colonne, conclusion « oui » à droite.

    etapes : [(question, réponse, conclusion si oui)], parcourues jusqu'au premier « oui ».
    """
    couleur = {"ok": "var(--ok)", "attention": "var(--attention)", "critique": "var(--critique)"}[etat]
    actif = next(i for i, (_, rep, _) in enumerate(etapes) if rep)
    h_noeud, pas, x_q, w_q, x_c, w_c = 34, 50, 20, 380, 500, 300
    hauteur = 20 + pas * len(etapes)
    elements = []
    for i, (question, _, conclusion) in enumerate(etapes):
        y = 14 + i * pas
        visite, choisi = i <= actif, i == actif
        trait_q = "var(--accent)" if visite else "var(--bordure)"
        opacite = 1 if visite else 0.35
        if i < len(etapes) - 1:
            couleur_non = "var(--accent)" if i < actif else "var(--bordure)"
            elements.append(f'<line x1="{x_q + 24}" y1="{y + h_noeud}" x2="{x_q + 24}" y2="{y + pas}" '
                            f'stroke="{couleur_non}" stroke-width="2"/>')
            elements.append(f'<text x="{x_q + 32}" y="{y + h_noeud + 12}" font-size="10" fill="var(--texte2)" '
                            f'opacity="{opacite}">non</text>')
        elements.append(f'<rect x="{x_q}" y="{y}" width="{w_q}" height="{h_noeud}" rx="7" fill="var(--panneau2)" '
                        f'stroke="{trait_q}" stroke-width="{2 if choisi else 1.2}" opacity="{opacite}"/>')
        elements.append(f'<text x="{x_q + 14}" y="{y + 22}" font-size="12.5" fill="var(--texte)" opacity="{opacite}" '
                        f'font-weight="{600 if choisi else 400}">{question}</text>')
        c_concl = couleur if choisi else "var(--bordure)"
        elements.append(f'<line x1="{x_q + w_q}" y1="{y + h_noeud / 2}" x2="{x_c}" y2="{y + h_noeud / 2}" '
                        f'stroke="{c_concl}" stroke-width="{2.5 if choisi else 1}" '
                        f'stroke-dasharray="{"0" if choisi else "4 4"}" opacity="{1 if choisi else 0.35}"/>')
        elements.append(f'<text x="{x_q + w_q + 12}" y="{y + h_noeud / 2 - 5}" font-size="10" fill="var(--texte2)" '
                        f'opacity="{1 if choisi else 0.35}">oui</text>')
        elements.append(f'<g class="{"actif" if choisi else ""}"><rect x="{x_c}" y="{y}" width="{w_c}" height="{h_noeud}" '
                        f'rx="7" fill="{c_concl if choisi else "var(--panneau)"}" fill-opacity="{0.22 if choisi else 1}" '
                        f'stroke="{c_concl}" stroke-width="{2 if choisi else 1}" opacity="{1 if choisi else 0.35}"/></g>')
        elements.append(f'<text x="{x_c + 14}" y="{y + 22}" font-size="12.5" fill="var(--texte)" '
                        f'font-weight="{600 if choisi else 400}" opacity="{1 if choisi else 0.35}">{conclusion}</text>')
    svg = (f'<svg viewBox="0 0 820 {hauteur}" width="100%" role="img" aria-label="Arbre de décision diagnostique" '
           f'font-family="IBM Plex Sans, Segoe UI, sans-serif">{"".join(elements)}</svg>')
    return f'<div class="arbre">{svg}</div>'
