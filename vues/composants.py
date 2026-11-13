"""Composants d'interface : cartes KPI, jauges, alertes, voyants. Icônes uniquement en SVG."""
from __future__ import annotations

import math

import plotly.graph_objects as go
import streamlit as st

from vues.icones import icone
from vues.theme import couleurs, gabarit_plotly


def html(contenu: str) -> None:
    """Rend du HTML sur une seule ligne logique (évite l'interprétation Markdown des indentations)."""
    st.markdown("".join(ligne.strip() for ligne in contenu.splitlines()), unsafe_allow_html=True)


def fmt(valeur, decimales: int = 1, vide: str = "n/d") -> str:
    """Format français : espace fine pour les milliers, virgule décimale."""
    if valeur is None or (isinstance(valeur, float) and math.isnan(valeur)):
        return vide
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def titre_page(nom_icone: str, titre: str, sous_titre: str = "") -> None:
    html(f'<div class="titre-page">{icone(nom_icone, 26)}<span>{titre}</span></div>'
         + (f'<p class="sous-titre">{sous_titre}</p>' if sous_titre else ""))


def section(nom_icone: str, titre: str) -> None:
    html(f'<div class="section">{icone(nom_icone, 18)}<span>{titre}</span></div>')


def carte_kpi(nom_icone: str, libelle: str, valeur: str, unite: str = "", etat: str = "neutre", sous: str = "") -> None:
    html(f'<div class="kpi etat-{etat}"><div class="lib">{icone(nom_icone, 17)}<span>{libelle}</span></div>'
         f'<div class="val">{valeur}<small>{unite}</small></div><div class="sub">{sous or "&nbsp;"}</div></div>')


def compteur(nom_icone: str, libelle: str, valeur: str, unite: str, sous: str = "") -> None:
    html(f'<div class="compteur"><div class="lib">{icone(nom_icone, 18)}<span>{libelle}</span></div>'
         f'<div class="val">{valeur}<small>{unite}</small></div>'
         + (f'<div class="sub">{sous}</div>' if sous else "") + "</div>")


def voyant(etat: str, texte: str) -> str:
    return f'<span class="voyant etat-{etat}"><i></i>{texte}</span>'


def alerte(etat: str, titre: str, detail: str, nom_icone: str | None = None) -> None:
    ic = nom_icone or {"critique": "alerte", "attention": "alerte", "ok": "valide", "neutre": "info"}[etat]
    html(f'<div class="alerte etat-{etat}">{icone(ic, 20)}<div><b>{titre}</b><span class="d">{detail}</span></div></div>')


def note(texte: str) -> None:
    html(f'<div class="note">{icone("info", 15)}<span>{texte}</span></div>')


def direct(texte: str, etat: str = "ok") -> None:
    html(f'<div class="direct etat-{etat}"><i></i><span>{texte}</span></div>')


def jauge(titre: str, valeur, unite: str, plage: tuple, zones: list, decimales: int = 1, hauteur: int = 210) -> go.Figure:
    """zones : [(debut, fin, 'ok'|'attention'|'critique'), ...]."""
    c = couleurs()
    v = None if valeur is None or (isinstance(valeur, float) and math.isnan(valeur)) else float(valeur)
    teinte = {"ok": c["ok"], "attention": c["attention"], "critique": c["critique"]}
    etat_courant = "ok"
    for a, b, e in zones:
        if v is not None and a <= v <= b:
            etat_courant = e
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=v if v is not None else 0,
        number=dict(suffix=f" {unite}", valueformat=f".{decimales}f", font=dict(size=30, color=c["texte"])),
        title=dict(text=titre, font=dict(size=14, color=c["texte2"])),
        gauge=dict(axis=dict(range=list(plage), tickcolor=c["texte2"], tickfont=dict(size=10)),
                   bar=dict(color=teinte[etat_courant], thickness=0.28), bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[a, b], color=teinte[e] + "33") for a, b, e in zones]),
    ))
    base = gabarit_plotly(hauteur)
    fig.update_layout(height=hauteur, margin=dict(l=35, r=35, t=40, b=5), paper_bgcolor=base["paper_bgcolor"],
                      font=base["font"], separators=", ")
    return fig
