"""Paramètres de référence et saisie manuelle (cahier des charges, §2), propres à chaque machine."""

from __future__ import annotations

import streamlit as st

from condenseur.parametres import LIBELLES, Parametres
from vues import composants as ui
from vues.commun import depot

machine = st.session_state.get("machine")
ui.titre_page("reglages", "Paramètres de référence", "Saisie manuelle des tarifs, caractéristiques nominales et seuils.",
              f"<span>Machine <b>{machine.nom}</b></span>" if machine else "")
if machine is None:
    st.stop()

GROUPES = [
    ("monnaie", "Tarifs énergie et eau", ["tarif_elec_dt_kwh", "tarif_eau_dt_m3"]),
    ("goutte", "Caractéristiques hydrauliques et aérauliques",
     ["p_pulv_nom_bar", "q_pulv_nom_m3h", "q_purge_nom_lh", "vfd_min_hz", "vfd_max_hz"]),
    ("alerte", "Seuils d'alerte sur l'approche thermique ΔT_app",
     ["dt_app_nominal_c", "seuil_legere_c", "seuil_grave_c", "seuil_aeraulique_c"]),
    ("cycle", "Référence pour la normalisation selon Q0", ["p_comp_ref_kw", "q0_ref_kw"]),
]

d = depot()
p = machine.parametres
fluides = [f.nom for f in d.fluides()]
with st.form(f"parametres_{machine.id}"):
    fluide = st.selectbox("Fluide frigorigène (bibliothèque de fluides)", fluides,
                          index=fluides.index(machine.fluide) if machine.fluide in fluides else 0)
    valeurs = {}
    for ic, titre, noms in GROUPES:
        ui.section(ic, titre)
        colonnes = st.columns(3)
        for i, nom in enumerate(noms):
            libelle, unite, pas, decimales = LIBELLES[nom]
            valeurs[nom] = colonnes[i % 3].number_input(f"{libelle} ({unite})", value=float(getattr(p, nom)),
                                                        step=float(pas), format=f"%.{decimales}f", key=f"{nom}_{machine.id}")
        if ic == "goutte":
            ui.note("Niveau du bac : signal NIV_BAC_OK du scénario (0 = alerte, 1 = OK). Un écart de "
                    f"{ui.fmt(p.tolerance_pct, 0)} % autour des valeurs nominales est toléré avant de signaler une chute ou un excès.")
        if ic == "cycle":
            ui.note("Puissance de référence = puissance compresseur de référence × Q0 mesurée / Q0 de référence.")
    a, b = st.columns(2)
    enregistrer = a.form_submit_button("Enregistrer", type="primary")
    reinitialiser = b.form_submit_button("Revenir aux valeurs par défaut")

if enregistrer or reinitialiser:
    nouveaux = Parametres() if reinitialiser else Parametres.depuis_dict(valeurs)
    erreurs = nouveaux.verifier()
    for e in erreurs:
        ui.alerte("critique", "Valeur incohérente", e)
    if not erreurs:
        machine.parametres = nouveaux
        machine.fluide = fluide
        d.enregistrer_machine(machine)
        for nom in valeurs:
            st.session_state.pop(f"{nom}_{machine.id}", None)
        st.session_state["parametres_enregistres"] = True
        st.rerun()

if st.session_state.pop("parametres_enregistres", False):
    ui.alerte("ok", "Paramètres enregistrés", "Les indicateurs et le diagnostic sont recalculés avec les nouvelles valeurs.")
