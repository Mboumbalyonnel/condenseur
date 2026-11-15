"""Dictionnaire des données d'entrée : structure des scénarios Excel (cahier des charges, §3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tag:
    colonne: str      # Colonne Excel
    nom: str          # Variable
    description: str
    unite: str
    binaire: bool = False
    mini: float | None = None   # Bornes physiques plausibles (contrôle à l'import)
    maxi: float | None = None


TAGS: list[Tag] = [
    Tag("A", "TIMESTAMP", "Horodatage de la mesure en temps réel", "Date / Heure"),
    Tag("B", "HP_COND_BAR", "Haute pression relative du fluide choisi", "bar (rel)", mini=0, maxi=120),
    Tag("C", "T_EXT_SEC_C", "Température extérieure sèche", "°C", mini=-20, maxi=55),
    Tag("D", "HR_EXT_PCT", "Humidité relative extérieure", "%", mini=0, maxi=100),
    Tag("E", "DELTA_T_APP_C", "Approche thermique mesurée (ΔT_app)", "°C", mini=0, maxi=30),
    Tag("F", "P_PULV_BAR", "Pression de pulvérisation d'eau", "bar", mini=0, maxi=10),
    Tag("G", "Q_PULV_M3H", "Débit réel de pulvérisation d'eau", "m³/h", mini=0, maxi=1000),
    Tag("H", "Q_PURGE_LH", "Débit réel de purge / déconcentration", "L/h", mini=0, maxi=10000),
    Tag("I", "NIV_BAC_OK", "Niveau d'eau du bac (0 = Alerte / 1 = OK)", "-", binaire=True),
    Tag("J", "VFD_VENT_HZ", "Fréquence variateur ventilateur (Min/Max)", "Hz", mini=0, maxi=70),
    Tag("K", "DEF_VENT_DI", "Défaut thermique ventilateur (0 = OK / 1 = Défaut)", "-", binaire=True),
    Tag("L", "DEF_POMPE_DI", "Défaut thermique pompe (0 = OK / 1 = Défaut)", "-", binaire=True),
    Tag("M", "P_ELEC_COMP_KW", "Puissance active compresseur", "kW", mini=0, maxi=10000),
    Tag("N", "Q0_FROID_KW", "Puissance frigorifique produite (Q0)", "kW", mini=0, maxi=50000),
    Tag("O", "SURCOUT_ELEC_DT_H", "Surcoût électrique compresseur (STEG)", "DT/h", mini=0, maxi=10000),
    Tag("P", "SURCOUT_EAU_DT_H", "Surcoût eau de purge (SONEDE)", "DT/h", mini=0, maxi=10000),
]

NOMS = [t.nom for t in TAGS]
MESURES = [t.nom for t in TAGS if t.nom != "TIMESTAMP"]
BINAIRES = [t.nom for t in TAGS if t.binaire]
PAR_NOM = {t.nom: t for t in TAGS}
