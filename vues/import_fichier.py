"""Import des fichiers Excel de scénarios d'exploitation pour la machine choisie (§1 et §3)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from condenseur.import_donnees import importer
from condenseur.tags import TAGS
from vues import composants as ui
from vues.commun import depot

d = depot()
machine = st.session_state.get("machine")
ui.titre_page("upload", "Import des scénarios", "Fichiers Excel de scénarios d'exploitation temps réel, colonnes A à P.",
              f"<span>Machine <b>{machine.nom}</b></span>" if machine else "")
if machine is None:
    ui.alerte("neutre", "Aucune machine", "Créez d'abord un site et une machine.", "usine")
    st.stop()

with st.expander("Structure attendue des fichiers (dictionnaire des données)"):
    st.dataframe(pd.DataFrame([{"Col": f"Col {t.colonne}", "Variable": t.nom, "Description physique": t.description,
                                "Unité": t.unite} for t in TAGS]), hide_index=True, width="stretch")
    ui.note("Un classeur peut contenir plusieurs feuilles : chacune devient un scénario. Les lignes de titre "
            "au-dessus de l'en-tête sont ignorées ; le titre « SCÉNARIO n : ... » sert à nommer le scénario.")

fichiers = st.file_uploader("Fichiers .xlsx ou .csv", type=["xlsx", "csv"], accept_multiple_files=True)
rapports = []
for f in fichiers or []:
    for r in importer(f, f.name):
        rapports.append((f.name, r))

if rapports:
    ui.section("valide", "Scénarios détectés")
    a_enregistrer = []
    for i, (fichier, r) in enumerate(rapports):
        with st.container(border=True):
            if not r.valide:
                ui.alerte("critique", f"{fichier} : {r.nom}", " ".join(r.erreurs))
                continue
            debut, fin = r.donnees["TIMESTAMP"].iloc[[0, -1]]
            nom = st.text_input("Nom du scénario", r.nom, key=f"nom_{i}")
            ui.note(f"{fichier} · {len(r.donnees)} mesures du {debut:%d/%m/%Y %H:%M} au {fin:%d/%m/%Y %H:%M}.")
            for a in r.avertissements:
                ui.alerte("attention", "Avertissement", a)
            with st.expander("Aperçu des mesures"):
                st.dataframe(r.donnees, hide_index=True, width="stretch")
            a_enregistrer.append((nom, r, fichier))
    if a_enregistrer and st.button(f"Enregistrer {len(a_enregistrer)} scénario(s) pour {machine.nom}", type="primary"):
        for nom, r, fichier in a_enregistrer:
            s = d.enregistrer_scenario(machine.id, nom or r.nom, r.donnees, fichier)
        st.session_state["scenario_id"] = s.id
        st.session_state["import_ok"] = len(a_enregistrer)
        st.rerun()

if n := st.session_state.pop("import_ok", 0):
    ui.alerte("ok", f"{n} scénario(s) enregistré(s)", "Un scénario déjà présent sous le même nom est remplacé.")
    st.page_link("vues/tableau_de_bord.py", label="Voir le tableau de bord")

# ---------------------------------------------------------------- Scénarios de la machine
ui.section("base_donnees", f"Scénarios de {machine.nom}")
scenarios = d.scenarios(machine.id)
if not scenarios:
    st.caption("Aucun scénario importé.")
for s in scenarios:
    a, b, c = st.columns([6, 3, 1])
    a.markdown(f"**{s.nom}**")
    b.caption(f"{s.nb_mesures} mesures · {s.fichier}")
    if c.button("Supprimer", key=f"suppr_{s.id}", icon=":material/delete:", help="Supprimer ce scénario"):
        d.supprimer_scenario(s.id)
        st.rerun()
