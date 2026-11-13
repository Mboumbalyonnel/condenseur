"""Paramètres de référence et saisie manuelle (cahier des charges, §2)."""

from __future__ import annotations

import streamlit as st

from condenseur.parametres import LIBELLES, Parametres
from vues import composants as ui
from vues.commun import depot

machine = st.session_state.get("machine")
ui.titre_page("reglages", "Paramètres de référence",
              "Seuils et caractéristiques nominales ajustables par l'exploitant, propres à chaque machine.")
if machine is None:
    st.stop()
ui.note(f"Machine : {machine.nom}.")

p = machine.parametres
with st.form(f"parametres_{machine.id}"):
    valeurs = {}
    colonnes = st.columns(2)
    for i, (nom, (libelle, unite, pas, decimales)) in enumerate(LIBELLES.items()):
        valeurs[nom] = colonnes[i % 2].number_input(f"{libelle} ({unite})", value=float(getattr(p, nom)),
                                                    step=float(pas), format=f"%.{decimales}f")
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
        depot().enregistrer_machine(machine)
        st.session_state["parametres_enregistres"] = True
        st.rerun()

if st.session_state.pop("parametres_enregistres", False):
    ui.alerte("ok", "Paramètres enregistrés", "Les indicateurs sont recalculés avec les nouvelles valeurs.")
