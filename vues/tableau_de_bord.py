"""Tableau de bord du scénario choisi : état, double affichage financier STEG / SONEDE (§4),
indicateurs normalisés selon Q0 et graphique unique de l'approche thermique (§5)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from vues import composants as ui
from vues.commun import analyse, contexte, depot
from vues.icones import icone
from vues.synoptique import synoptique
from vues.theme import couleurs, gabarit_plotly

ctx = contexte()
if ctx is None:
    ui.titre_page("tableau", "Tableau de bord")
    st.stop()
machine, scenario = ctx
resultat = analyse(machine, scenario)
df, p, c = resultat.donnees, machine.parametres, couleurs()
d = resultat.courant
diag = resultat.diagnostic

ui.titre_page("tableau", "Tableau de bord", f"{machine.nom} · fluide {resultat.fluide.nom}",
              f'{icone("horloge", 15)}<span>Scénario <b>{scenario.nom}</b></span>')

# ---------------------------------------------------------------- Bandeau d'état
haut = max(10.0, p.seuil_aeraulique_c * 1.25)
bornes = [(0, p.seuil_legere_c, "ok"), (p.seuil_legere_c, p.seuil_grave_c, "attention"),
          (p.seuil_grave_c, p.seuil_aeraulique_c, "critique"), (p.seuil_aeraulique_c, haut, "aeraulique")]
piste = "".join(f'<span style="width:{(b - a) / haut * 100:.2f}%;background:var(--{e})"></span>' for a, b, e in bornes)
graduations = "".join(f'<b style="left:{v / haut * 100:.2f}%">{ui.fmt(v, 1)}</b>'
                      for v in (p.dt_app_nominal_c, p.seuil_legere_c, p.seuil_grave_c, p.seuil_aeraulique_c))
position = min(max(d["DELTA_T_APP_C"] / haut * 100, 0), 99.5)
echelle = (f'<div class="echelle"><div class="lib">{icone("thermometre", 15)}<span>Approche thermique ΔT_app</span></div>'
           f'<div class="val">{ui.fmt(d["DELTA_T_APP_C"], 2)}<small>°C · {d["NIVEAU"]}</small></div>'
           f'<div style="position:relative"><div class="piste">{piste}</div>'
           f'<div class="curseur" style="left:calc({position:.2f}% - 2px)"></div></div>'
           f'<div class="graduations">{graduations}</div></div>')
ui.html(f'<div class="hero etat-{diag.gravite}">'
        f'<div><div class="lib">{icone("sante", 15)}<span>Diagnostic à {d["TIMESTAMP"]:%d/%m/%Y %H:%M}</span></div>'
        f'<div class="grand"><i></i>{diag.titre}</div><div class="sub">{diag.cause}</div>'
        f'<span class="badge">Action : {diag.action}</span></div>'
        f'{echelle}'
        f'<div><div class="lib">{icone("monnaie", 15)}<span>Surcoût total</span></div>'
        f'<div class="chiffre">{ui.fmt(d["COUT_TOTAL_DT_H"], 3)}<small>DT/h</small></div>'
        f'<div class="sub">STEG + SONEDE</div></div></div>')

# ---------------------------------------------------------------- Double affichage financier
ui.section("monnaie", "Surcoûts financiers")
teinte_elec = c["critique"] if d["COUT_ELEC_DT_H"] > 0.005 else c["ok"]
teinte_eau = c["attention"] if d["COUT_EAU_DT_H"] > 0.005 else c["ok"]
ui.html(f'<div class="finance">'
        f'<div class="facture" style="--teinte:{teinte_elec}"><div class="pictogramme">{icone("eclair", 28)}</div>'
        f'<div><div class="t">Surcoût électrique compresseur · STEG</div>'
        f'<div class="d">Surconsommation {ui.fmt(d["SURCONSO_KW"], 2)} kW au-dessus de la référence '
        f'× {ui.fmt(p.tarif_elec_dt_kwh, 3)} DT/kWh</div></div>'
        f'<div class="montant">{ui.fmt(d["COUT_ELEC_DT_H"], 3)}<small>DT/h</small></div></div>'
        f'<div class="facture" style="--teinte:{teinte_eau}"><div class="pictogramme">{icone("goutte", 28)}</div>'
        f'<div><div class="t">Surcoût eau de purge · SONEDE</div>'
        f'<div class="d">Excès de purge {ui.fmt(d["EXCES_PURGE_LH"], 0)} L/h au-delà de {ui.fmt(p.q_purge_nom_lh, 0)} L/h '
        f'× {ui.fmt(p.tarif_eau_dt_m3, 3)} DT/m³</div></div>'
        f'<div class="montant">{ui.fmt(d["COUT_EAU_DT_H"], 3)}<small>DT/h</small></div></div></div>')

# ---------------------------------------------------------------- Indicateurs normalisés selon Q0
ui.section("cycle", "Indicateurs normalisés selon la charge frigorifique Q0")
k = st.columns(4)
with k[0]:
    ui.carte_kpi("compresseur", "Puissance compresseur", ui.fmt(d["P_ELEC_COMP_KW"], 2), "kW", "neutre",
                 "colonne M du scénario")
with k[1]:
    ui.carte_kpi("capteur", "Référence normalisée P_ref", ui.fmt(d["P_REF_KW"], 2), "kW", "neutre",
                 f"{ui.fmt(p.p_comp_ref_kw, 2)} kW × Q0 / {ui.fmt(p.q0_ref_kw, 0)} kW")
with k[2]:
    ecart = d["ECART_NORM_PCT"]
    ui.carte_kpi("tendance_haut", "Écart normalisé", ("+" if ecart > 0 else "") + ui.fmt(ecart, 1), "%",
                 "ok" if ecart <= 0.5 else diag.gravite if diag.gravite != "ok" else "attention",
                 "indépendant de la charge")
with k[3]:
    ui.carte_kpi("thermometre", "Puissance frigorifique Q0", ui.fmt(d["Q0_FROID_KW"], 0), "kW", "neutre",
                 f"Tc {resultat.fluide.nom} : {ui.fmt(d['TC_C'], 1)} °C")

# ---------------------------------------------------------------- Synoptique
ui.section("ventilateur", "Synoptique de l'installation")
cond = d["CONDITIONS"]
ui.html(synoptique(d.to_dict(), resultat.fluide.nom, diag.gravite,
                   {"pression": cond.chute_p_pulv, "pulv": cond.q_pulv_faible, "purge": cond.purge_excessive}))

# ---------------------------------------------------------------- Graphique unique (§5)
ui.section("graphique", "Évolution de l'approche thermique ΔT_app")
autres = [s for s in depot().scenarios(machine.id) if s.id != scenario.id]
comparer = st.multiselect("Comparer la cinétique avec d'autres scénarios de la machine", [s.id for s in autres],
                          format_func={s.id: s.nom for s in autres}.get, placeholder="Aucun scénario de comparaison")

fig = go.Figure()
y_max = max(haut, df["DELTA_T_APP_C"].max() + 0.5)
for a, b, e in [(0, p.seuil_legere_c, "ok"), (p.seuil_legere_c, p.seuil_grave_c, "attention"),
                (p.seuil_grave_c, p.seuil_aeraulique_c, "critique"), (p.seuil_aeraulique_c, y_max, "aeraulique")]:
    fig.add_hrect(y0=a, y1=b, fillcolor=c[e], opacity=0.06, line_width=0, layer="below")
palette = ["#2E86C1", "#13A89E", "#8E6C8A", "#B07D2B", "#7A8B99"]
for i, sid in enumerate(comparer):
    s = next(s for s in autres if s.id == sid)
    autre = analyse(machine, s).donnees
    fig.add_trace(go.Scatter(x=autre["TIMESTAMP"], y=autre["DELTA_T_APP_C"], name=s.nom, mode="lines",
                             line=dict(color=palette[i % len(palette)], width=2, dash="dot"),
                             hovertemplate="%{y:.2f} °C"))
fig.add_trace(go.Scatter(x=df["TIMESTAMP"], y=df["DELTA_T_APP_C"], name=scenario.nom, mode="lines+markers",
                         line=dict(color=c["marine"], width=3), marker=dict(size=8, color=c["marine"],
                                                                             line=dict(color="#fff", width=2)),
                         hovertemplate="%{y:.2f} °C"))
for y, nom, e in [(p.dt_app_nominal_c, "Nominal", "ok"), (p.seuil_legere_c, "Alerte légère", "attention"),
                  (p.seuil_grave_c, "Alerte grave", "critique"), (p.seuil_aeraulique_c, "Alerte aéraulique", "aeraulique")]:
    fig.add_hline(y=y, line=dict(color=c[e], dash="dash", width=1.3),
                  annotation_text=f"{nom} {ui.fmt(y, 1)} °C", annotation_position="top left",
                  annotation_font=dict(size=11, color=c[e]))
fig.update_layout(**gabarit_plotly(440), showlegend=True, yaxis_title="ΔT_app (°C)", xaxis_title="Temps")
fig.update_yaxes(range=[0, y_max])
fig.update_xaxes(hoverformat="%d/%m/%Y %H:%M", tickformat="%d/%m %H:%M")
st.plotly_chart(fig, width="stretch")
ui.note("Une montée brutale de ΔT_app accompagne une perte d'arrosage (chute de P_pulv, bac vide, ventilation) ; "
        "une dérive lente signale un encrassement progressif (entartrage, buses, purge).")
