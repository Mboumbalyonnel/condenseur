"""Fonctions thermodynamiques et psychrométriques (cahier des charges, §5).

Fonctions pures, vectorisées : elles acceptent des scalaires ou des séries pandas /
tableaux numpy.
"""

from __future__ import annotations

import numpy as np

# Coefficients d'Antoine de l'ammoniac R717 (NIST Chemistry WebBook, Stull 1947) :
#   log10(P) = A - B / (T + C)    avec P en bar absolu et T en kelvin
#   Domaine de validité : 239,6 K à 371,5 K (-33,6 °C à 98,4 °C)
ANTOINE_A = 4.86886
ANTOINE_B = 1113.928
ANTOINE_C = -10.409
T_MIN_VALIDITE_C = 239.6 - 273.15
T_MAX_VALIDITE_C = 371.5 - 273.15


def pression_saturation_nh3(t_c):
    """Pression de saturation de l'ammoniac (bar absolu) à la température t_c (°C)."""
    t_k = np.asarray(t_c, dtype=float) + 273.15
    return 10 ** (ANTOINE_A - ANTOINE_B / (t_k + ANTOINE_C))


def temperature_condensation(hp_rel_bar, pression_atm_bar: float = 1.01325):
    """Équation d'Antoine inverse : haute pression relative (bar) -> Tc (°C).

        T = B / (A - log10(P_abs)) - C
    """
    p_abs = np.asarray(hp_rel_bar, dtype=float) + pression_atm_bar
    with np.errstate(divide="ignore", invalid="ignore"):
        t_k = ANTOINE_B / (ANTOINE_A - np.log10(np.where(p_abs > 0, p_abs, np.nan))) - ANTOINE_C
    return t_k - 273.15


def temperature_bulbe_humide(t_sec_c, hr_pct):
    """Température de bulbe humide (°C) par la formule de Stull (2011).

    Validité : HR de 5 % à 99 %, T de -20 °C à 50 °C, à pression atmosphérique
    normale. Erreur typique inférieure à 0,3 °C.
    """
    t = np.asarray(t_sec_c, dtype=float)
    hr = np.clip(np.asarray(hr_pct, dtype=float), 0.0, 100.0)
    return (
        t * np.arctan(0.151977 * np.sqrt(hr + 8.313659))
        + np.arctan(t + hr)
        - np.arctan(hr - 1.676331)
        + 0.00391838 * hr**1.5 * np.arctan(0.023101 * hr)
        - 4.686035
    )
