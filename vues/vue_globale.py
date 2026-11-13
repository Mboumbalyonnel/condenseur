"""Indicateurs globaux (cahier des charges, §6) : santé de la machine et surcoûts financiers."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from condenseur.diagnostic import NORMAL
from vues import composants as ui
from vues.commun import ETAT_NIVEAU, analyse, bandes_phases, etat_pression, sans_donnees
from vues.synoptique import synoptique
from vues.visuels import bandeau, frise_horaire, parcours_phases
from vues.theme import couleurs, gabarit_plotly

machine = st.session_state.get("machine")
ui.titre_page("sante", "Santé et surcoûts",
              "Indicateurs globaux : santé du condenseur et surcoût financier de l'encrassement.")
if machine is None:
    st.stop()
resultat = analyse(machine)
if resultat is None:
    sans_donnees(machine)
    st.stop()

df, p, c = resultat.donnees, machine.parametres, couleurs()
d = df.iloc[-1]
etat = ETAT_NIVEAU[d["NIVEAU"]]
ui.html(bandeau(etat, d["NIVEAU"],
                f"ΔTapp {ui.fmt(d['DT_APP_C'], 2)} °C · H{len(df)} · {d['TIMESTAMP']:%d/%m/%Y %H:%M}",
                parcours_phases(df), "Surcoût cumulé", ui.fmt(d["COUT_CUMULE_DT"], 2), "DT"))
if d["ALERTE_MAINTENANCE"]:
    ui.alerte("critique", "Alerte de maintenance préventive",
              f"Encrassement critique : ΔTapp ≥ {ui.fmt(p.seuil_alerte_grave_c)} °C. Intervention à planifier.", "cle")

# ---------------------------------------------------------------- Cartes
k = st.columns(5)
with k[0]:
    ui.carte_kpi("thermometre", "Approche ΔTapp", ui.fmt(d["DT_APP_C"], 2), "°C", etat,
                 f"nominal {ui.fmt(p.approche_nominale_c)} °C")
with k[1]:
    ui.carte_kpi("sante", "Rendement ηcond", ui.fmt(d["ETA_COND_PCT"], 1), "%", etat, "100 % = condenseur propre")
with k[2]:
    ui.carte_kpi("cycle", "COP global", ui.fmt(d["COP"], 2), "", etat, "Q0 / (P comp + P aux)")
with k[3]:
    ui.carte_kpi("eclair", "Surconsommation", ui.fmt(d["SURCONSO_KW"], 1), "kW", etat,
                 f"+{ui.fmt(d['SURCONSO_PCT'], 1)} % compresseur")
with k[4]:
    ui.carte_kpi("monnaie", "Coût horaire", ui.fmt(d["COUT_H_DT"], 3), "DT/h", etat,
                 f"tarif {ui.fmt(p.tarif_kwh_dt, 3)} DT/kWh")

# ---------------------------------------------------------------- Jauges et synoptique
ui.section("tableau", "Santé de la machine")
g = st.columns(3)
app_max = p.seuil_alerte_grave_c * 1.5
eta_legere = 100 * p.approche_nominale_c / p.seuil_alerte_legere_c
eta_grave = 100 * p.approche_nominale_c / p.seuil_alerte_grave_c
s_legere = p.surconso_pct_par_c * (p.seuil_alerte_legere_c - p.approche_nominale_c)
s_grave = p.surconso_pct_par_c * (p.seuil_alerte_grave_c - p.approche_nominale_c)
with g[0]:
    st.plotly_chart(ui.jauge("Rendement relatif ηcond", d["ETA_COND_PCT"], "%", (0, 100), [
        (0, eta_grave, "critique"), (eta_grave, eta_legere, "attention"), (eta_legere, 100, "ok")], 0), width="stretch")
with g[1]:
    st.plotly_chart(ui.jauge("Approche ΔTapp", d["DT_APP_C"], "°C", (0, app_max), [
        (0, p.seuil_alerte_legere_c, "ok"), (p.seuil_alerte_legere_c, p.seuil_alerte_grave_c, "attention"),
        (p.seuil_alerte_grave_c, app_max, "critique")], 2), width="stretch")
with g[2]:
    st.plotly_chart(ui.jauge("Surconsommation compresseur", d["SURCONSO_PCT"], "%", (0, 20), [
        (0, s_legere, "ok"), (s_legere, s_grave, "attention"), (s_grave, 20, "critique")], 1), width="stretch")

ui.section("horloge", "Chronologie horaire des alertes")
ui.html(frise_horaire(df))

ui.section("cycle", "Synoptique de l'installation")
ui.html(synoptique({**d.to_dict(), "etat": etat, "etat_pression": etat_pression(d["P_PULV_BAR"], p)}))

# ---------------------------------------------------------------- Surcoût financier
ui.section("monnaie", "Surcoût financier")
fig = go.Figure(go.Scatter(x=df["TIMESTAMP"], y=df["COUT_CUMULE_DT"], fill="tozeroy", name="Surcoût cumulé",
                           line=dict(color=c["critique"], width=2.5), fillcolor=c["critique"] + "26",
                           hovertemplate="%{y:.2f} DT"))
fig.add_annotation(x=d["TIMESTAMP"], y=d["COUT_CUMULE_DT"], text=f"<b>{ui.fmt(d['COUT_CUMULE_DT'], 2)} DT</b>",
                   showarrow=True, arrowcolor=c["critique"], ax=-60, ay=-25, font=dict(color=c["texte"], size=13))
bandes_phases(fig, df)
fig.update_layout(**gabarit_plotly(300), yaxis_title="DT cumulés")
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- Évolution
ui.section("graphique", "Évolution sur les 3 phases")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                    subplot_titles=("Approche thermique ΔTapp (°C)", "Surconsommation du compresseur (kW)", "COP global"))
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["DT_APP_C"], name="ΔTapp", line=dict(color=c["accent"], width=2),
                         hovertemplate="%{y:.2f} °C"), 1, 1)
for y, couleur in [(p.approche_nominale_c, c["ok"]), (p.seuil_alerte_legere_c, c["attention"]),
                   (p.seuil_alerte_grave_c, c["critique"])]:
    fig.add_hline(y=y, line=dict(color=couleur, dash="dash", width=1), row=1, col=1)
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["SURCONSO_KW"], name="Surconsommation",
                         line=dict(color=c["attention"], width=2), hovertemplate="%{y:.2f} kW"), 2, 1)
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["COP"], name="COP", line=dict(color=c["ok"], width=2),
                         hovertemplate="%{y:.2f}"), 3, 1)
for r in (1, 2, 3):
    bandes_phases(fig, df, r)
fig.update_layout(**gabarit_plotly(640))
fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), showlegend=False)
fig.update_xaxes(gridcolor=c["grille"], tickformat="%d/%m")
fig.update_yaxes(gridcolor=c["grille"])
fig.update_yaxes(range=[0, max(app_max, df["DT_APP_C"].max() + 0.5)], row=1, col=1)
st.plotly_chart(fig, width="stretch")
ui.note("Fond vert, orange, rouge : phases 1, 2 et 3. Pointillés : ΔTnom, seuil d'alerte légère (4,5 °C) "
        "et seuil d'alerte grave (6,0 °C).")
