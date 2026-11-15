"""Bibliothèque de fluides frigorigènes modifiable (cahier des charges, §1).

Chaque fluide porte les coefficients de l'équation d'Antoine de sa courbe de saturation :
    log10(P) = A - B / (T + C)      P en bar absolu, T en kelvin.
La haute pression relative mesurée (HP_COND_BAR) donne ainsi la température de condensation
du fluide choisi pour la machine.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

PRESSION_ATM_BAR = 1.01325


@dataclass
class Fluide:
    nom: str
    designation: str
    a: float
    b: float
    c: float
    t_min_c: float          # domaine de validité des coefficients
    t_max_c: float
    source: str = ""

    def temperature_saturation(self, p_abs_bar: float) -> float:
        """Température de saturation (°C) à la pression absolue donnée (bar)."""
        if p_abs_bar <= 0:
            return math.nan
        return self.b / (self.a - math.log10(p_abs_bar)) - self.c - 273.15

    def pression_saturation(self, t_c: float) -> float:
        """Pression de saturation absolue (bar) à la température donnée (°C)."""
        return 10 ** (self.a - self.b / (t_c + 273.15 + self.c))

    def temperature_condensation(self, hp_rel_bar: float) -> float:
        """Température de condensation (°C) à partir de la haute pression relative."""
        return self.temperature_saturation(hp_rel_bar + PRESSION_ATM_BAR)

    def vers_dict(self) -> dict:
        return asdict(self)


# NH3 : coefficients NIST. Autres fluides : ajustement sur les tables de saturation
# (écart inférieur à 0,15 °C sur le domaine de validité ; R404A : courbe de bulle).
FLUIDES_DEFAUT: list[Fluide] = [
    Fluide("NH3", "Ammoniac (R717)", 4.86886, 1113.928, -10.409, -34.0, 98.0, "NIST Chemistry WebBook"),
    Fluide("CO2", "Dioxyde de carbone (R744)", 4.84052, 938.695, 11.48, -40.0, 30.0, "Ajustement sur table de saturation"),
    Fluide("R404A", "R404A (mélange HFC)", 4.38479, 936.953, -13.11, -20.0, 50.0, "Ajustement sur table de saturation"),
    Fluide("R134a", "R134a (HFC)", 4.33558, 951.199, -27.33, -20.0, 60.0, "Ajustement sur table de saturation"),
]
