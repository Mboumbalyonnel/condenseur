"""Dictionnaire des données d'entrée : tags GTC normalisés (cahier des charges, §4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tag:
    colonne: str      # Colonne Excel
    nom: str          # Variable interne
    description: str
    unite: str
    binaire: bool = False
    mini: float | None = None   # Bornes physiques plausibles (contrôle à l'import)
    maxi: float | None = None


TAGS: list[Tag] = [
    Tag("A", "TIMESTAMP", "Horodatage de la mesure (pas horaire)", "Date / Heure"),
    Tag("B", "HP_COND_BAR", "Haute pression relative NH3", "bar (rel)", mini=0, maxi=25),
    Tag("C", "T_EXT_SEC_C", "Température extérieure sèche", "°C", mini=-20, maxi=55),
    Tag("D", "HR_EXT_PCT", "Humidité relative extérieure", "%", mini=0, maxi=100),
    Tag("E", "P_PULV_BAR", "Pression de pulvérisation d'eau", "bar", mini=0, maxi=10),
    Tag("F", "NIV_BAC_OK", "Niveau d'eau du bac (contact 0 / 1)", "-", binaire=True),
    Tag("G", "VFD_VENT_HZ", "Fréquence variateur ventilateur", "Hz", mini=0, maxi=70),
    Tag("H", "DEF_VENT_DI", "Défaut thermique ventilateur (0 / 1)", "-", binaire=True),
    Tag("I", "DEF_POMPE_DI", "Défaut thermique pompe (0 / 1)", "-", binaire=True),
    Tag("J", "P_ELEC_COMP_KW", "Puissance active compresseur", "kW", mini=0, maxi=10000),
    Tag("K", "P_ELEC_AUX_KW", "Puissance active auxiliaires (pompe + ventilateur)", "kW", mini=0, maxi=2000),
    Tag("L", "Q0_FROID_KW", "Puissance frigorifique produite", "kW", mini=0, maxi=50000),
]

NOMS = [t.nom for t in TAGS]
MESURES = [t.nom for t in TAGS if t.nom != "TIMESTAMP"]
BINAIRES = [t.nom for t in TAGS if t.binaire]
PAR_NOM = {t.nom: t for t in TAGS}
