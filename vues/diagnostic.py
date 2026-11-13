"""Indicateurs de diagnostic ciblé (cahier des charges, §5 et §6) : cause hydraulique,
aéraulique ou entartrage des faisceaux, issue de l'arbre de décision."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from condenseur.diagnostic import AUCUNE, PART_BASSE_VFD
from condenseur.moteur import NOMS_PHASES
from vues import composants as ui
from vues.commun import ETAT_NIVEAU, ETAT_PHASE, analyse, bandes_phases, sans_donnees
from vues.theme import couleurs, gabarit_plotly
from vues.visuels import arbre_svg, tuiles_categories

machine = st.session_state.get("machine")
ui.titre_page("alerte", "Diagnostic ciblé",
              "Croisement de ΔTapp avec la pulvérisation, le ventilateur et les défauts digitaux pour isoler la cause.")
if machine is None:
    st.stop()
resultat = analyse(machine)
if resultat is None:
    sans_donnees(machine)
    st.stop()

df, p, c = resultat.donnees, machine.parametres, couleurs()
d = df.iloc[-1]
etat = ETAT_NIVEAU[d["NIVEAU"]]
p_basse = p.p_pulv_consigne_bar * (1 - p.tolerance_pression_pct / 100)
p_haute = p.p_pulv_consigne_bar * (1 + p.tolerance_pression_pct / 100)
bas_plage = p.vfd_min_hz + PART_BASSE_VFD * (p.vfd_max_hz - p.vfd_min_hz)
pression_ok = p_basse <= d["P_PULV_BAR"] <= p_haute
ventilo_max = d["VFD_VENT_HZ"] >= p.vfd_max_hz - p.marge_vfd_hz

ui.direct(f"Dernière mesure H{len(df)} · {d['TIMESTAMP']:%d/%m/%Y %H:%M} · {NOMS_PHASES[int(d['PHASE'])]}",
          ETAT_PHASE[int(d["PHASE"])])

# ---------------------------------------------------------------- Cause identifiée
ui.html(tuiles_categories(d["CATEGORIE"], etat))
if d["CATEGORIE"] == AUCUNE:
    ui.alerte("ok", "Aucune cause de dégradation", d["DETAIL"])
else:
    ui.alerte(etat, f"Cause {d['CATEGORIE'].lower()} : {d['CAUSE']}",
              f"{d['DETAIL']}<br><b>Action recommandée</b> : {d['ACTION']}", "cle")

# ---------------------------------------------------------------- Grandeurs croisées
ui.section("capteur", "Grandeurs croisées par l'arbre de décision")
ui.html("".join([
    ui.voyant(etat, f"Approche : ΔTapp {ui.fmt(d['DT_APP_C'], 2)} °C"),
    ui.voyant("ok" if pression_ok else "critique", f"Pulvérisation : {ui.fmt(d['P_PULV_BAR'], 2)} bar "
              f"(consigne {ui.fmt(p.p_pulv_consigne_bar, 2)})"),
    ui.voyant("attention" if ventilo_max else "ok", f"Ventilateur : {ui.fmt(d['VFD_VENT_HZ'], 1)} Hz "
              f"(plage {ui.fmt(p.vfd_min_hz, 0)} à {ui.fmt(p.vfd_max_hz, 0)})"),
    ui.voyant("critique" if not d["NIV_BAC_OK"] else "ok", f"Bac : {'niveau bas' if not d['NIV_BAC_OK'] else 'niveau correct'}"),
    ui.voyant("critique" if d["DEF_VENT_DI"] else "ok", f"Défaut ventilateur : {int(d['DEF_VENT_DI'])}"),
    ui.voyant("critique" if d["DEF_POMPE_DI"] else "ok", f"Défaut pompe : {int(d['DEF_POMPE_DI'])}"),
]))

# ---------------------------------------------------------------- Arbre de décision
ui.section("cycle", "Arbre de décision diagnostique")
etapes = [
    ("Défaut thermique de la pompe ?", bool(d["DEF_POMPE_DI"]), "Hydraulique : défaut pompe"),
    ("Niveau d'eau du bac bas ?", not d["NIV_BAC_OK"], "Hydraulique : manque d'eau"),
    ("Défaut thermique du ventilateur ?", bool(d["DEF_VENT_DI"]), "Aéraulique : défaut ventilateur"),
    (f"Pression de pulvérisation < {ui.fmt(p_basse, 2)} bar ?", d["P_PULV_BAR"] < p_basse, "Hydraulique : pression basse"),
    (f"Pression de pulvérisation > {ui.fmt(p_haute, 2)} bar ?", d["P_PULV_BAR"] > p_haute, "Hydraulique : buses obstruées"),
    (f"Ventilateur sous {ui.fmt(p.vfd_min_hz, 0)} Hz ?", d["VFD_VENT_HZ"] < p.vfd_min_hz, "Aéraulique : ventilateur sous plage"),
    (f"ΔTapp < {ui.fmt(p.seuil_alerte_legere_c)} °C ?", d["DT_APP_C"] < p.seuil_alerte_legere_c, "Fonctionnement normal"),
    (f"Ventilateur bloqué sous {ui.fmt(bas_plage, 0)} Hz ?", d["VFD_VENT_HZ"] < bas_plage, "Aéraulique : régulation"),
    ("Ventilateur sous sa pleine vitesse ?", not ventilo_max, "Entartrage progressif"),
    ("Ventilateur à pleine vitesse", True, "Entartrage confirmé"),
]
ui.html(arbre_svg(etapes, "ok" if d["CATEGORIE"] == AUCUNE else etat))

# ---------------------------------------------------------------- Courbes de diagnostic
ui.section("graphique", "Évolution des grandeurs de diagnostic")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.4, 0.4, 0.2],
                    subplot_titles=("Pression de pulvérisation (bar)", "Fréquence du variateur ventilateur (Hz)",
                                    "Défauts digitaux"))
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["P_PULV_BAR"], name="Pulvérisation", line=dict(color=c["accent"], width=2),
                         hovertemplate="%{y:.2f} bar"), 1, 1)
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["VFD_VENT_HZ"], name="Variateur", line=dict(color=c["attention"], width=2),
                         hovertemplate="%{y:.1f} Hz"), 2, 1)
signaux = {"Pompe": df["DEF_POMPE_DI"], "Ventilateur": df["DEF_VENT_DI"], "Bac bas": 1 - df["NIV_BAC_OK"]}
fig.add_trace(go.Heatmap(x=df["TIMESTAMP"], y=list(signaux), z=[list(v) for v in signaux.values()], zmin=0, zmax=1,
                         colorscale=[[0, c["panneau2"]], [1, c["critique"]]], showscale=False, ygap=3,
                         hovertemplate="%{y} : %{z}<extra></extra>"), 3, 1)
# Repères ajoutés après les courbes (Plotly ignore les sous-graphiques encore vides)
fig.add_hrect(y0=p_basse, y1=p_haute, fillcolor=c["ok"], opacity=0.10, line_width=0, row=1, col=1)
fig.add_hline(y=p.p_pulv_consigne_bar, line=dict(color=c["ok"], dash="dash", width=1), row=1, col=1)
for y in (p.vfd_min_hz, p.vfd_max_hz):
    fig.add_hline(y=y, line=dict(color=c["texte2"], dash="dash", width=1), row=2, col=1)
for r in (1, 2):
    bandes_phases(fig, df, r)
fig.update_layout(**gabarit_plotly(600))
fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), showlegend=False)
fig.update_xaxes(gridcolor=c["grille"], tickformat="%d/%m")
fig.update_yaxes(gridcolor=c["grille"])
fig.update_yaxes(range=[0, max(df["P_PULV_BAR"].max(), p_haute) * 1.15], row=1, col=1)
fig.update_yaxes(range=[0, max(df["VFD_VENT_HZ"].max(), p.vfd_max_hz) * 1.12], row=2, col=1)
st.plotly_chart(fig, width="stretch")
ui.note("Bande verte : consigne de pulvérisation ± 15 %. Pointillés : plage du variateur. "
        "Rouge dans la dernière bande : défaut actif.")
