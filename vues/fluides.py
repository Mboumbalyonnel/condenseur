"""Bibliothèque de fluides modifiable (cahier des charges, §1)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from condenseur.fluides import FLUIDES_DEFAUT, Fluide
from vues import composants as ui
from vues.commun import depot

d = depot()
ui.titre_page("livre", "Bibliothèque de fluides",
              "Courbes de saturation des fluides frigorigènes : log10(P) = A - B / (T + C), P en bar absolu, T en K.")

COLONNES = {"nom": "Fluide", "designation": "Désignation", "a": "A", "b": "B", "c": "C",
            "t_min_c": "T min (°C)", "t_max_c": "T max (°C)", "source": "Source"}

table = pd.DataFrame([f.vers_dict() for f in d.fluides()]).rename(columns=COLONNES)
modifiee = st.data_editor(table, num_rows="dynamic", hide_index=True, width="stretch", key="fluides",
                          column_config={"A": st.column_config.NumberColumn(format="%.5f"),
                                         "B": st.column_config.NumberColumn(format="%.3f"),
                                         "C": st.column_config.NumberColumn(format="%.3f")})

a, b = st.columns([1, 3])
if a.button("Enregistrer la bibliothèque", type="primary"):
    lignes = modifiee.rename(columns={v: k for k, v in COLONNES.items()}).dropna(subset=["nom", "a", "b", "c"])
    lignes = lignes[lignes["nom"].astype(str).str.strip() != ""]
    try:
        fluides = [Fluide(nom=str(r.nom).strip(), designation=str(r.designation or ""), a=float(r.a), b=float(r.b),
                          c=float(r.c), t_min_c=float(r.t_min_c if pd.notna(r.t_min_c) else -50),
                          t_max_c=float(r.t_max_c if pd.notna(r.t_max_c) else 100), source=str(r.source or ""))
                   for r in lignes.itertuples()]
        if len({f.nom for f in fluides}) != len(fluides):
            raise ValueError("Deux fluides portent le même nom.")
        d.enregistrer_fluides(fluides)
        st.session_state.pop("fluides", None)
        ui.alerte("ok", "Bibliothèque enregistrée", f"{len(fluides)} fluide(s).")
    except ValueError as exc:
        ui.alerte("critique", "Enregistrement impossible", str(exc))
if b.button("Restaurer les fluides par défaut"):
    try:
        d.enregistrer_fluides(FLUIDES_DEFAUT + [f for f in d.fluides() if f.nom not in {g.nom for g in FLUIDES_DEFAUT}])
        st.session_state.pop("fluides", None)
        st.rerun()
    except ValueError as exc:
        ui.alerte("critique", "Restauration impossible", str(exc))

# ---------------------------------------------------------------- Vérification
ui.section("thermometre", "Température de condensation selon la haute pression relative")
hp = st.slider("Haute pression relative (bar)", 0.0, 80.0, 12.0, 0.5)
ui.html('<div class="grandeurs">' + "".join(
    f'<div class="grandeur"><div class="n">{f.nom}</div><div class="v">{ui.fmt(t, 1)}<small>°C</small></div>'
    + (ui.voyant("ok", "Dans le domaine") if f.t_min_c <= t <= f.t_max_c else ui.voyant("attention", "Hors domaine"))
    + f'<div class="r">{f.designation}</div></div>'
    for f in d.fluides() if (t := f.temperature_condensation(hp)) == t) + "</div>")
