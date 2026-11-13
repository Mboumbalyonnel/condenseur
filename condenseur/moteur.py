"""Moteur de calcul : applique à chaque pas horaire la chaîne du cahier des charges (§5).

    HP -> Tc (Antoine inverse) ; Tsec + HR -> Tbh (Stull) ; ΔTapp = Tc - Tbh
    -> rendement relatif, COP global, surconsommation (kW, %, DT) -> diagnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import diagnostic as diag
from .parametres import Parametres
from .thermo import temperature_bulbe_humide, temperature_condensation


@dataclass
class Resultat:
    donnees: pd.DataFrame                  # Mesures + colonnes calculées
    decalage_c: float                      # Décalage d'étalonnage appliqué (°C)
    pas_h: float                           # Pas de temps (h)
    synthese: dict = field(default_factory=dict)


def estimer_decalage(dt_app_brut: pd.Series, p: Parametres) -> float:
    """Décalage d'étalonnage : moyenne de ΔTapp brut sur la période de référence - ΔTnom."""
    reference = dt_app_brut.iloc[p.reference_debut_h - 1 : p.reference_fin_h].dropna()
    if reference.empty:
        return 0.0
    return float(reference.mean() - p.approche_nominale_c)


def pas_de_temps_h(horodatages: pd.Series) -> float:
    ecarts = horodatages.sort_values().diff().dropna()
    if ecarts.empty:
        return 1.0
    pas = ecarts.median().total_seconds() / 3600
    return pas if pas > 0 else 1.0


def analyser(mesures: pd.DataFrame, p: Parametres) -> Resultat:
    """Calcule tous les indicateurs pour un jeu de mesures horaires (colonnes = tags)."""
    df = mesures.sort_values("TIMESTAMP").reset_index(drop=True).copy()
    pas = pas_de_temps_h(df["TIMESTAMP"])

    # Thermodynamique et psychrométrie
    df["TC_C"] = temperature_condensation(df["HP_COND_BAR"], p.pression_atm_bar)
    df["TBH_C"] = temperature_bulbe_humide(df["T_EXT_SEC_C"], df["HR_EXT_PCT"])
    df["DT_APP_BRUT_C"] = df["TC_C"] - df["TBH_C"]

    # Étalonnage : décalage constant estimé sur la phase nominale (H1 à H48)
    decalage = estimer_decalage(df["DT_APP_BRUT_C"], p)
    df["DT_APP_C"] = df["DT_APP_BRUT_C"] - decalage

    # Rendement relatif du condenseur : 100 % tant que ΔTapp <= ΔTnom
    app = df["DT_APP_C"]
    df["ETA_COND_PCT"] = np.where(app > p.approche_nominale_c, 100 * p.approche_nominale_c / app, 100.0)

    # COP global = froid produit / électricité totale
    p_totale = df["P_ELEC_COMP_KW"] + df["P_ELEC_AUX_KW"]
    df["COP"] = np.where(p_totale > 0, df["Q0_FROID_KW"] / p_totale.where(p_totale > 0), np.nan)

    # Surconsommation : +x % de puissance compresseur par °C d'approche au-dessus de ΔTnom
    exces = (app - p.approche_nominale_c).clip(lower=0)
    df["SURCONSO_PCT"] = p.surconso_pct_par_c * exces
    df["P_COMP_REF_KW"] = df["P_ELEC_COMP_KW"] / (1 + df["SURCONSO_PCT"] / 100)
    df["SURCONSO_KW"] = df["P_ELEC_COMP_KW"] - df["P_COMP_REF_KW"]
    df["ENERGIE_PERDUE_KWH"] = df["SURCONSO_KW"] * pas
    df["COUT_H_DT"] = df["ENERGIE_PERDUE_KWH"] * p.tarif_kwh_dt
    df["COUT_CUMULE_DT"] = df["COUT_H_DT"].cumsum()

    # Diagnostic heure par heure
    diagnostics = [
        diag.diagnostiquer(r.DT_APP_C, r.P_PULV_BAR, int(r.NIV_BAC_OK), r.VFD_VENT_HZ,
                           int(r.DEF_VENT_DI), int(r.DEF_POMPE_DI), p)
        for r in df.itertuples()
    ]
    df["NIVEAU"] = [d.niveau for d in diagnostics]
    df["CATEGORIE"] = [d.categorie for d in diagnostics]
    df["CAUSE"] = [d.cause for d in diagnostics]
    df["DETAIL"] = [d.detail for d in diagnostics]
    df["ACTION"] = [d.action for d in diagnostics]

    # Alerte de maintenance préventive : déclenchée par l'encrassement critique (§3)
    df["ALERTE_MAINTENANCE"] = df["NIVEAU"] == diag.ALERTE_GRAVE

    # Phase de la chronologie de simulation (§3), d'après le rang horaire depuis le début
    rang_h = np.arange(1, len(df) + 1)
    df["HEURE"] = rang_h
    df["PHASE"] = np.select([rang_h >= p.phase3_debut_h, rang_h >= p.phase2_debut_h], [3, 2], default=1)

    resultat = Resultat(df, decalage, pas)
    resultat.synthese = synthese(df, p, pas)
    return resultat


NOMS_PHASES = {1: "Phase 1 : cas nominal", 2: "Phase 2 : alerte légère", 3: "Phase 3 : alerte grave"}


def synthese(df: pd.DataFrame, p: Parametres, pas: float) -> dict:
    """Indicateurs globaux pour l'en-tête du tableau de bord."""
    if df.empty:
        return {}
    dernier = df.iloc[-1]
    maintenance = df.index[df["ALERTE_MAINTENANCE"]]
    return {
        "debut": df["TIMESTAMP"].iloc[0],
        "fin": dernier["TIMESTAMP"],
        "nb_heures": len(df),
        "dt_app_actuel": float(dernier["DT_APP_C"]),
        "eta_actuel": float(dernier["ETA_COND_PCT"]),
        "cop_actuel": float(dernier["COP"]),
        "cop_moyen": float(df["COP"].mean()),
        "niveau_actuel": dernier["NIVEAU"],
        "cause_actuelle": dernier["CAUSE"],
        "detail_actuel": dernier["DETAIL"],
        "action_actuelle": dernier["ACTION"],
        "categorie_actuelle": dernier["CATEGORIE"],
        "surconso_kw_actuelle": float(dernier["SURCONSO_KW"]),
        "surconso_pct_actuelle": float(dernier["SURCONSO_PCT"]),
        "cout_total_dt": float(df["COUT_CUMULE_DT"].iloc[-1]),
        "heures_par_niveau": {n: int((df["NIVEAU"] == n).sum() * pas) for n in diag.NIVEAUX},
        "maintenance_active": bool(dernier["ALERTE_MAINTENANCE"]),
        "maintenance_depuis": df.loc[maintenance[0], "TIMESTAMP"] if len(maintenance) else None,
    }
