"""Éléments partagés par les pages : base de données, barre latérale, analyse, phases."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from condenseur.diagnostic import ALERTE_GRAVE, ALERTE_LEGERE, NORMAL
from condenseur.modeles import Machine
from condenseur.moteur import Resultat
from condenseur.stockage import Depot
from vues import composants as ui
from vues.icones import icone
from vues.theme import appliquer, couleurs

ETAT_NIVEAU = {NORMAL: "ok", ALERTE_LEGERE: "attention", ALERTE_GRAVE: "critique"}
ETAT_PHASE = {1: "ok", 2: "attention", 3: "critique"}


@st.cache_resource
def depot() -> Depot:
    d = Depot()
    if not d.sites():
        site = d.creer_site("Site principal", "")
        d.creer_machine(site.id, "Condenseur évaporatif 1", "Condenseur évaporatif NH3")
    return d


def nombre(valeur: float, decimales: int = 2, unite: str = "") -> str:
    return f"{ui.fmt(valeur, decimales, '-')} {unite}".strip()


def barre_laterale() -> Machine | None:
    """Marque, thème, choix site / machine. Appelée une fois par app.py avant la page."""
    ss = st.session_state
    ss.setdefault("theme", "sombre")
    appliquer(ss["theme"])
    d = depot()
    with st.sidebar:
        ui.html(f'<div class="marque">{icone("thermometre", 24)}<span>Condenseur évaporatif NH3</span></div>')
        st.write("")
        sites = d.sites()
        if not sites:
            st.info("Aucun site. Créez-en un dans « Sites et machines ».")
            machine = None
        else:
            ids_sites = [s.id for s in sites]
            if ss.get("site_id") not in ids_sites:
                ss["site_id"] = ids_sites[0]
            st.selectbox("Site", ids_sites, format_func={s.id: s.nom for s in sites}.get, key="site_id")
            machines = d.machines(ss["site_id"])
            if not machines:
                st.info("Aucune machine sur ce site.")
                machine = None
            else:
                ids = [m.id for m in machines]
                if ss.get("machine_id") not in ids:
                    ss["machine_id"] = ids[0]
                st.selectbox("Machine", ids, format_func={m.id: m.nom for m in machines}.get, key="machine_id")
                machine = d.machine(ss["machine_id"])
        st.radio("Thème", ["sombre", "clair"], horizontal=True, key="theme")
        st.divider()
    return machine


def analyse(machine: Machine) -> Resultat | None:
    mesures = depot().mesures(machine.id)
    if mesures.empty:
        return None
    return machine.analyser(mesures)


def sans_donnees(machine: Machine) -> None:
    ui.alerte("neutre", "Aucune mesure pour cette machine",
              f"Importez le fichier de simulation horaire de « {machine.nom} » depuis la page Import de données.",
              "upload")
    st.page_link("vues/import_fichier.py", label="Aller à l'import de données")


def etat_pression(p_pulv: float, p) -> str:
    ecart = abs(p_pulv - p.p_pulv_consigne_bar) / p.p_pulv_consigne_bar * 100
    if ecart > p.tolerance_pression_pct:
        return "critique"
    if ecart > p.tolerance_pression_pct / 2:
        return "attention"
    return "ok"


def bandes_phases(fig: go.Figure, df: pd.DataFrame, rangee: int | None = None) -> None:
    """Colore le fond de chaque phase (§3) et l'étiquette en haut du graphique."""
    c = couleurs()
    teintes = {1: c["ok"], 2: c["attention"], 3: c["critique"]}
    pas = pd.Timedelta(hours=1)
    for phase, g in df.groupby("PHASE"):
        x0 = g["TIMESTAMP"].iloc[0] - pas / 2
        x1 = g["TIMESTAMP"].iloc[-1] + pas / 2
        options = dict(x0=x0, x1=x1, fillcolor=teintes[phase], opacity=0.07, line_width=0, layer="below")
        if rangee is None:
            fig.add_vrect(**options, annotation_text=f"Phase {phase}", annotation_position="top left",
                          annotation_font=dict(size=11, color=c["texte2"]))
        else:
            fig.add_vrect(**options, row=rangee, col=1)
