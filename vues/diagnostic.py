"""Arbre de décision diagnostique automatisé (cahier des charges, §4.1) appliqué à la mesure courante."""

from __future__ import annotations

import streamlit as st

from condenseur.diagnostic import BRANCHES, conclusion
from vues import composants as ui
from vues.commun import analyse, contexte
from vues.icones import icone

TEINTE = {"ok": "var(--ok)", "attention": "var(--attention)", "critique": "var(--critique)"}


def arbre_svg(niveau: str, regle_active: int) -> str:
    """Les 6 branches du §4.1 dans l'ordre d'évaluation, puis le cas nominal ; la branche retenue est surlignée."""
    lignes = [(texte, conclusion(n, niveau)) for n, texte, _ in BRANCHES]
    lignes.append(("Aucune branche vérifiée", conclusion(0, niveau)))
    active = regle_active if regle_active else len(lignes)          # index 1..7
    pas, h, x_c, w_c, x_r, w_r = 66, 50, 64, 470, 590, 400
    elements = []
    for i, (texte, dg) in enumerate(lignes, start=1):
        y = 12 + (i - 1) * pas
        visite, choisi = i <= active, i == active
        opacite = 1 if choisi else (0.75 if visite else 0.3)
        couleur = TEINTE[dg.gravite] if choisi else "var(--bordure)"
        if i < len(lignes):
            trait = "var(--marine)" if i < active else "var(--bordure)"
            elements.append(f'<line x1="34" y1="{y + h / 2 + 15}" x2="34" y2="{y + pas + h / 2 - 15}" stroke="{trait}" stroke-width="2"/>')
            elements.append(f'<text x="42" y="{y + h + 12}" font-size="10" fill="var(--texte2)" opacity="{opacite}">non</text>')
        rond = "var(--marine)" if visite else "var(--bordure)"
        elements.append(f'<circle cx="34" cy="{y + h / 2}" r="15" fill="{couleur if choisi else rond}" opacity="{1 if visite else .5}"/>')
        elements.append(f'<text x="34" y="{y + h / 2 + 4.5}" font-size="12.5" font-weight="700" fill="#fff" text-anchor="middle">'
                        f'{i if i < len(lignes) else "–"}</text>')
        elements.append(f'<rect x="{x_c}" y="{y}" width="{w_c}" height="{h}" rx="10" fill="var(--panneau)" '
                        f'stroke="{couleur if choisi else "var(--bordure)"}" stroke-width="{2 if choisi else 1}" opacity="{opacite}"/>')
        elements.append(f'<text x="{x_c + 14}" y="{y + h / 2 + 4.5}" font-size="12.5" fill="var(--texte)" '
                        f'font-weight="{700 if choisi else 500}" opacity="{opacite}">{texte}</text>')
        elements.append(f'<line x1="{x_c + w_c}" y1="{y + h / 2}" x2="{x_r}" y2="{y + h / 2}" stroke="{couleur}" '
                        f'stroke-width="{3 if choisi else 1}" stroke-dasharray="{"0" if choisi else "4 4"}" opacity="{opacite}"/>')
        elements.append(f'<text x="{x_c + w_c + 14}" y="{y + h / 2 - 6}" font-size="10" fill="var(--texte2)" opacity="{opacite}">'
                        f'{"oui" if i < len(lignes) else ""}</text>')
        fond = f'fill="{couleur}" fill-opacity="0.1"' if choisi else 'fill="var(--panneau2)"'
        elements.append(f'<g class="{"actif" if choisi else ""}"><rect x="{x_r}" y="{y}" width="{w_r}" height="{h}" rx="10" '
                        f'{fond} stroke="{couleur}" stroke-width="{2 if choisi else 1}" opacity="{opacite}"/></g>')
        elements.append(f'<text x="{x_r + 14}" y="{y + 21}" font-size="12.5" font-weight="700" fill="var(--texte)" '
                        f'opacity="{opacite}">{dg.cause}</text>')
        elements.append(f'<text x="{x_r + 14}" y="{y + 38}" font-size="11.5" fill="var(--texte2)" '
                        f'opacity="{opacite}">Action : {dg.action}</text>')
    hauteur = 12 + len(lignes) * pas
    svg = (f'<svg viewBox="0 0 1000 {hauteur}" width="100%" role="img" aria-label="Arbre de décision diagnostique" '
           f'font-family="Inter, Segoe UI, sans-serif">{"".join(elements)}</svg>')
    return f'<div class="carte arbre">{svg}</div>'


ctx = contexte()
if ctx is None:
    ui.titre_page("cle", "Diagnostic")
    st.stop()
machine, scenario = ctx
resultat = analyse(machine, scenario)
d, p = resultat.courant, machine.parametres
diag, cond = resultat.diagnostic, d["CONDITIONS"]

ui.titre_page("cle", "Diagnostic", f"Arbre de décision automatisé TUNIFROID · {machine.nom}",
              f'{icone("horloge", 15)}<span>{scenario.nom} · <b>{d["TIMESTAMP"]:%d/%m/%Y %H:%M}</b></span>')

ui.alerte(diag.gravite, f"{diag.titre} : {diag.cause}",
          f"Action : {diag.action}. Cinétique de dérive : {diag.cinetique}. "
          f"Approche thermique {ui.fmt(d['DELTA_T_APP_C'], 2)} °C ({d['NIVEAU']}).",
          "valide" if diag.regle == 0 else "alerte")

# ---------------------------------------------------------------- Grandeurs croisées
ui.section("capteur", "Grandeurs croisées par l'arbre")
tol = p.tolerance_pct


def grandeur(nom: str, valeur: str, unite: str, alerte: bool, texte_etat: str, reference: str) -> str:
    return (f'<div class="grandeur"><div class="n">{nom}</div><div class="v">{valeur}<small>{unite}</small></div>'
            f'{ui.voyant("critique" if alerte else "ok", texte_etat)}<div class="r">{reference}</div></div>')


cartes = [
    grandeur("NIV_BAC_OK", str(int(d["NIV_BAC_OK"])), "", cond.bac_bas, "Alerte" if cond.bac_bas else "OK",
             "0 = alerte · 1 = OK"),
    grandeur("P_PULV_BAR", ui.fmt(d["P_PULV_BAR"], 2), "bar", cond.chute_p_pulv,
             "Chute" if cond.chute_p_pulv else "Normale", f"nominale {ui.fmt(p.p_pulv_nom_bar, 2)} bar, -{ui.fmt(tol, 0)} % toléré"),
    grandeur("Q_PULV_M3H", ui.fmt(d["Q_PULV_M3H"], 1), "m³/h", cond.q_pulv_faible,
             "Faible" if cond.q_pulv_faible else "Normal", f"nominal {ui.fmt(p.q_pulv_nom_m3h, 1)} m³/h, -{ui.fmt(tol, 0)} % toléré"),
    grandeur("Q_PURGE_LH", ui.fmt(d["Q_PURGE_LH"], 0), "L/h", cond.purge_excessive,
             "Excessive" if cond.purge_excessive else "Normale", f"nominal {ui.fmt(p.q_purge_nom_lh, 0)} L/h, +{ui.fmt(tol, 0)} % toléré"),
    grandeur("DEF_VENT_DI", str(int(d["DEF_VENT_DI"])), "", int(d["DEF_VENT_DI"]) == 1,
             "Défaut" if int(d["DEF_VENT_DI"]) else "OK", "défaut thermique ventilateur"),
    grandeur("VFD_VENT_HZ", ui.fmt(d["VFD_VENT_HZ"], 1), "Hz", d["VFD_VENT_HZ"] <= p.vfd_min_hz,
             "Bloqué au minimum" if d["VFD_VENT_HZ"] <= p.vfd_min_hz else "En régulation",
             f"plage {ui.fmt(p.vfd_min_hz, 0)} à {ui.fmt(p.vfd_max_hz, 0)} Hz"),
    grandeur("DEF_POMPE_DI", str(int(d["DEF_POMPE_DI"])), "", int(d["DEF_POMPE_DI"]) == 1,
             "Défaut" if int(d["DEF_POMPE_DI"]) else "OK", "défaut thermique pompe"),
    grandeur("DELTA_T_APP_C", ui.fmt(d["DELTA_T_APP_C"], 2), "°C", cond.derive,
             "Dérive" if cond.derive else "Pas de dérive", f"alerte légère à {ui.fmt(p.seuil_legere_c, 1)} °C"),
]
ui.html(f'<div class="grandeurs">{"".join(cartes)}</div>')

# ---------------------------------------------------------------- Arbre
ui.section("calque", "Arbre de décision")
ui.html(arbre_svg(d["NIVEAU"], diag.regle))
ui.note("Les branches sont évaluées dans l'ordre ; la première vérifiée donne le diagnostic. Une chute de P_pulv "
        "provoque une dérive brutale de ΔT_app ; à P_pulv normale, la dérive est lente.")
