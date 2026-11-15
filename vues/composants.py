"""Composants d'interface : en-tête, cartes, alertes, voyants. Icônes uniquement en SVG."""
from __future__ import annotations

import math

import streamlit as st

from vues.icones import icone


def html(contenu: str) -> None:
    """Rend du HTML sur une seule ligne logique (évite l'interprétation Markdown des indentations)."""
    st.markdown("".join(ligne.strip() for ligne in contenu.splitlines()), unsafe_allow_html=True)


def fmt(valeur, decimales: int = 1, vide: str = "n/d") -> str:
    """Format français : espace pour les milliers, virgule décimale."""
    if valeur is None or (isinstance(valeur, float) and math.isnan(valeur)):
        return vide
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def titre_page(nom_icone: str, titre: str, sous_titre: str = "", pastille: str = "") -> None:
    droite = f'<div class="pastille-entete">{pastille}</div>' if pastille else ""
    html(f'<div class="entete"><div><div class="titre-page">{icone(nom_icone, 28)}<span>{titre}</span></div>'
         + (f'<div class="sous-titre">{sous_titre}</div>' if sous_titre else "") + f"</div>{droite}</div>")


def section(nom_icone: str, titre: str) -> None:
    html(f'<div class="section">{icone(nom_icone, 19)}<span>{titre}</span></div>')


def carte_kpi(nom_icone: str, libelle: str, valeur: str, unite: str = "", etat: str = "neutre", sous: str = "") -> None:
    html(f'<div class="kpi etat-{etat}"><div class="lib">{icone(nom_icone, 17)}<span>{libelle}</span></div>'
         f'<div class="val">{valeur}<small>{unite}</small></div><div class="sub">{sous or "&nbsp;"}</div></div>')


def voyant(etat: str, texte: str) -> str:
    return f'<span class="voyant etat-{etat}"><i></i>{texte}</span>'


def alerte(etat: str, titre: str, detail: str, nom_icone: str | None = None) -> None:
    ic = nom_icone or {"critique": "alerte", "attention": "alerte", "ok": "valide", "neutre": "info"}.get(etat, "info")
    html(f'<div class="alerte etat-{etat}">{icone(ic, 20)}<div><b>{titre}</b><span class="d">{detail}</span></div></div>')


def note(texte: str) -> None:
    html(f'<div class="note">{icone("info", 15)}<span>{texte}</span></div>')
