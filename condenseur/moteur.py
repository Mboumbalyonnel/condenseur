"""Moteur de calcul (cahier des charges, §4).

Pour chaque mesure d'un scénario :
- Tc : température de condensation du fluide choisi, tirée de HP_COND_BAR (bibliothèque de fluides) ;
- normalisation selon Q0 : P_ref = P_comp_ref × Q0 / Q0_ref. La puissance de référence suit la charge
  frigorifique, si bien que l'écart de puissance reste comparable quelle que soit la charge ;
- surcoût électrique STEG (DT/h) = max(0, P_comp - P_ref) × tarif STEG ;
- surcoût eau SONEDE (DT/h) = max(0, Q_purge - Q_purge_nom) / 1000 × tarif SONEDE ;
- niveau d'approche thermique (seuils du §2) et diagnostic (arbre du §4.1).

Les colonnes O et P du fichier (surcoûts déjà calculés) sont conservées telles quelles ;
l'application les recalcule avec les tarifs et les valeurs nominales saisis dans l'interface.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .diagnostic import Diagnostic, diagnostiquer, evaluer, niveau_approche
from .fluides import Fluide
from .parametres import Parametres


@dataclass
class Resultat:
    donnees: pd.DataFrame          # mesures + colonnes calculées
    fluide: Fluide

    @property
    def courant(self) -> pd.Series:
        """Dernière mesure du scénario (instant affiché)."""
        return self.donnees.iloc[-1]

    @property
    def diagnostic(self) -> Diagnostic:
        return self.courant["DIAGNOSTIC"]


def analyser(mesures: pd.DataFrame, p: Parametres, fluide: Fluide) -> Resultat:
    df = mesures.sort_values("TIMESTAMP").reset_index(drop=True).copy()

    df["TC_C"] = [fluide.temperature_condensation(hp) for hp in df["HP_COND_BAR"]]

    # Normalisation selon Q0
    df["P_REF_KW"] = p.p_comp_ref_kw * df["Q0_FROID_KW"] / p.q0_ref_kw
    df["SURCONSO_KW"] = np.maximum(0.0, df["P_ELEC_COMP_KW"] - df["P_REF_KW"])
    df["ECART_NORM_PCT"] = np.where(df["P_REF_KW"] > 0,
                                    (df["P_ELEC_COMP_KW"] / df["P_REF_KW"] - 1) * 100, np.nan)

    # Double affichage financier
    df["COUT_ELEC_DT_H"] = df["SURCONSO_KW"] * p.tarif_elec_dt_kwh
    df["EXCES_PURGE_LH"] = np.maximum(0.0, df["Q_PURGE_LH"] - p.q_purge_nom_lh)
    df["COUT_EAU_DT_H"] = df["EXCES_PURGE_LH"] / 1000 * p.tarif_eau_dt_m3
    df["COUT_TOTAL_DT_H"] = df["COUT_ELEC_DT_H"] + df["COUT_EAU_DT_H"]

    # Seuils et arbre de décision
    df["NIVEAU"] = [niveau_approche(v, p) for v in df["DELTA_T_APP_C"]]
    lignes = df.to_dict("records")
    conditions = [evaluer(r, p) for r in lignes]
    df["CONDITIONS"] = conditions
    df["DIAGNOSTIC"] = [diagnostiquer(c, r["NIVEAU"]) for c, r in zip(conditions, lignes)]
    df["REGLE"] = [d.regle for d in df["DIAGNOSTIC"]]
    df["GRAVITE"] = [d.gravite for d in df["DIAGNOSTIC"]]
    return Resultat(df, fluide)
