"""Éléments partagés par les pages : base de données, barre latérale, analyse du scénario choisi."""

from __future__ import annotations

import streamlit as st

from condenseur.demo import initialiser
from condenseur.diagnostic import ALERTE_AERAULIQUE, ALERTE_GRAVE, ALERTE_LEGERE, NOMINAL
from condenseur.fluides import FLUIDES_DEFAUT
from condenseur.modeles import Machine, Scenario
from condenseur.moteur import Resultat
from condenseur.stockage import Depot
from vues import composants as ui
from vues.theme import LOGO, appliquer

ETAT_NIVEAU = {NOMINAL: "ok", ALERTE_LEGERE: "attention", ALERTE_GRAVE: "critique", ALERTE_AERAULIQUE: "aeraulique"}


@st.cache_resource
def depot() -> Depot:
    d = Depot()
    initialiser(d)
    return d


def _choisir(libelle: str, objets: list, cle: str, format_nom) -> object | None:
    ids = [o.id for o in objets]
    if not ids:
        return None
    if st.session_state.get(cle) not in ids:
        st.session_state[cle] = ids[0]
    noms = {o.id: format_nom(o) for o in objets}
    st.selectbox(libelle, ids, format_func=noms.get, key=cle)
    return next(o for o in objets if o.id == st.session_state[cle])


def barre_laterale() -> tuple[Machine | None, Scenario | None]:
    """Logo, choix du site, de la machine et du scénario. Appelée une fois par app.py."""
    appliquer()
    d = depot()
    st.logo(str(LOGO), size="large")
    with st.sidebar:
        ui.html('<div class="marque-sous">Suivi énergétique du condenseur évaporatif</div>')
        site = _choisir("Site", d.sites(), "site_id", lambda s: s.nom)
        machine = _choisir("Machine", d.machines(site.id), "machine_id", lambda m: m.nom) if site else None
        scenario = (_choisir("Scénario d'exploitation", d.scenarios(machine.id), "scenario_id", lambda s: s.nom)
                    if machine else None)
        st.divider()
    return machine, scenario


def analyse(machine: Machine, scenario: Scenario) -> Resultat:
    d = depot()
    fluide = d.fluide(machine.fluide) or FLUIDES_DEFAUT[0]
    return machine.analyser(d.mesures(scenario.id), fluide)


def contexte() -> tuple[Machine, Scenario] | None:
    """Machine et scénario choisis ; affiche un message et renvoie None s'il en manque un."""
    machine, scenario = st.session_state.get("machine"), st.session_state.get("scenario")
    if machine is None:
        ui.alerte("neutre", "Aucune machine", "Créez un site et une machine dans « Sites et machines ».", "usine")
        return None
    if scenario is None:
        ui.alerte("neutre", "Aucun scénario pour cette machine",
                  f"Importez un fichier Excel de scénario pour « {machine.nom} ».", "upload")
        st.page_link("vues/import_fichier.py", label="Aller à l'import des scénarios")
        return None
    return machine, scenario
