"""Gestion des sites industriels et de leurs machines (architecture multi-machines)."""

from __future__ import annotations

import sqlite3

import streamlit as st

from vues import composants as ui
from vues.commun import depot, nombre

d = depot()
ui.titre_page("usine", "Sites et machines",
              "Architecture modulaire : chaque machine a ses paramètres, ses mesures et sa source de données.")

# ---------------------------------------------------------------- Vue d'ensemble
for site in d.sites():
    with st.container(border=True):
        st.markdown(f"**{site.nom}**" + (f" — {site.localisation}" if site.localisation else ""))
        machines = d.machines(site.id)
        if machines:
            st.dataframe([{"Machine": m.nom, "Description": m.description, "Mesures": nombre(d.nombre_mesures(m.id), 0)} for m in machines],
                         hide_index=True, width="stretch")
        else:
            st.caption("Aucune machine.")

st.divider()
onglet_machine, onglet_site, onglet_modifier = st.tabs(["Ajouter une machine", "Ajouter un site", "Modifier ou supprimer"])

with onglet_site:
    with st.form("nouveau_site", clear_on_submit=True):
        nom = st.text_input("Nom du site")
        localisation = st.text_input("Localisation")
        if st.form_submit_button("Créer le site", type="primary"):
            if not nom.strip():
                st.error("Le nom est obligatoire.")
            else:
                try:
                    d.creer_site(nom, localisation)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Un site porte déjà ce nom.")

with onglet_machine:
    sites = d.sites()
    if not sites:
        st.info("Créez d'abord un site.")
    else:
        with st.form("nouvelle_machine", clear_on_submit=True):
            site_id = st.selectbox("Site", [s.id for s in sites], format_func={s.id: s.nom for s in sites}.get)
            nom = st.text_input("Nom de la machine", placeholder="Condenseur évaporatif 2")
            description = st.text_input("Description")
            if st.form_submit_button("Créer la machine", type="primary"):
                if not nom.strip():
                    st.error("Le nom est obligatoire.")
                else:
                    try:
                        m = d.creer_machine(site_id, nom, description)
                        st.session_state["site_id"], st.session_state["machine_id"] = site_id, m.id
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Une machine porte déjà ce nom sur ce site.")

with onglet_modifier:
    sites = d.sites()
    noms_sites = {s.id: s.nom for s in sites}
    toutes = d.machines()
    if toutes:
        st.markdown("**Machine**")
        mid = st.selectbox("Machine à modifier", [m.id for m in toutes],
                           format_func=lambda i: next(f"{noms_sites[m.site_id]} / {m.nom}" for m in toutes if m.id == i))
        m = d.machine(mid)
        with st.form(f"modifier_machine_{mid}"):
            m.nom = st.text_input("Nom", m.nom)
            m.description = st.text_input("Description", m.description)
            m.site_id = st.selectbox("Site", list(noms_sites), index=list(noms_sites).index(m.site_id),
                                     format_func=noms_sites.get)
            if st.form_submit_button("Enregistrer"):
                try:
                    d.enregistrer_machine(m)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Une machine porte déjà ce nom sur ce site.")
        confirmer = st.checkbox(f"Je confirme la suppression de « {m.nom} » et de ses mesures", key=f"conf_m_{mid}")
        if st.button("Supprimer la machine", disabled=not confirmer, icon=":material/delete:"):
            d.supprimer_machine(mid)
            st.rerun()

    if sites:
        st.markdown("**Site**")
        sid = st.selectbox("Site à modifier", list(noms_sites), format_func=noms_sites.get)
        site = next(s for s in sites if s.id == sid)
        with st.form(f"modifier_site_{sid}"):
            site.nom = st.text_input("Nom", site.nom)
            site.localisation = st.text_input("Localisation", site.localisation)
            if st.form_submit_button("Enregistrer"):
                try:
                    d.modifier_site(site)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Un site porte déjà ce nom.")
        confirmer = st.checkbox(f"Je confirme la suppression du site « {site.nom} », de ses machines et de leurs mesures",
                                key=f"conf_s_{sid}")
        if st.button("Supprimer le site", disabled=not confirmer, icon=":material/delete:"):
            d.supprimer_site(sid)
            st.rerun()
