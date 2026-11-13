"""Import d'un fichier de simulation horaire (.xlsx / .csv) pour une machine (cahier des charges, §3 et §4)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from condenseur.import_donnees import importer
from condenseur.tags import TAGS
from vues import composants as ui
from vues.commun import depot

machine = st.session_state.get("machine")
ui.titre_page("upload", "Import de données",
              "Mode académique : fichier Excel ou CSV de simulation horaire au format des tags GTC normalisés.")
if machine is None:
    st.stop()

nb = depot().nombre_mesures(machine.id)
ui.note(f"Machine : {machine.nom}. {ui.fmt(nb, 0)} mesure(s) déjà enregistrée(s).")

fichier = st.file_uploader("Fichier de simulation horaire", type=["xlsx", "csv"],
                           help="La ligne d'en-tête (TIMESTAMP, HP_COND_BAR, ...) est détectée automatiquement.")

with st.expander("Format attendu : dictionnaire des données (colonnes A à L)"):
    st.dataframe(pd.DataFrame([{"Colonne": t.colonne, "Variable": t.nom, "Description": t.description, "Unité": t.unite}
                               for t in TAGS]), hide_index=True, width="stretch")

if fichier is not None:
    rapport = importer(fichier, fichier.name)
    for erreur in rapport.erreurs:
        ui.alerte("critique", "Import impossible", erreur)
    for avertissement in rapport.avertissements:
        ui.alerte("attention", "Avertissement", avertissement)

    if rapport.valide:
        df = rapport.donnees
        ui.alerte("ok", f"{len(df)} mesures horaires lues",
                  f"Du {df['TIMESTAMP'].min():%d/%m/%Y %H:%M} au {df['TIMESTAMP'].max():%d/%m/%Y %H:%M}.")

        ui.section("base_donnees", "Données lues")
        st.dataframe(df, hide_index=True, width="stretch", height=260,
                     column_config={"TIMESTAMP": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")})

        remplacer = st.checkbox("Remplacer toutes les mesures existantes de cette machine", value=True,
                                help="Sinon, les mesures sont ajoutées (une mesure de même horodatage est écrasée).")
        if st.button("Enregistrer les mesures", type="primary"):
            n = depot().enregistrer_mesures(machine.id, df, remplacer=remplacer)
            ui.alerte("ok", f"{n} mesures enregistrées", f"Machine « {machine.nom} ».")
            st.page_link("vues/vue_globale.py", label="Ouvrir Santé et surcoûts", icon=":material/monitor_heart:")

