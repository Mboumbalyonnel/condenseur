"""Paramètres de référence d'une machine (cahier des charges, §2).

Seuls les paramètres du tableau §2 sont modifiables par l'exploitant. Les autres valeurs
sont des constantes du modèle tirées du cahier des charges (§3) ou des choix de
modélisation validés (règle des 3 %/°C, étalonnage sur la phase nominale).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


@dataclass
class Parametres:
    # --- Paramètres du cahier des charges (§2), modifiables ---
    tarif_kwh_dt: float = 0.340          # Tarif STEG HT/MT (DT/kWh)
    approche_nominale_c: float = 3.0     # ΔTnom constructeur, condenseur propre (°C)
    p_pompe_kw: float = 4.5              # Puissance nominale pompe de pulvérisation (kW)
    p_pulv_consigne_bar: float = 1.85    # Pression de consigne de la rampe d'eau (bar)
    vfd_min_hz: float = 30.0             # Fréquence mini du variateur ventilateur (Hz)
    vfd_max_hz: float = 50.0             # Fréquence maxi du variateur ventilateur (Hz)

    # --- Constantes du modèle (non modifiables dans l'interface) ---
    seuil_alerte_legere_c = 4.5          # §3 : alerte légère, approche de 4,5 à 6,0 °C
    seuil_alerte_grave_c = 6.0           # §3 : alerte grave, approche >= 6,0 °C
    surconso_pct_par_c = 3.0             # Surconsommation compresseur par °C d'approche en excès (%/°C)
    tolerance_pression_pct = 15.0        # Écart toléré sur la pression de pulvérisation (%)
    marge_vfd_hz = 1.0                   # Ventilateur « à pleine vitesse » si VFD >= max - marge (Hz)
    pression_atm_bar = 1.01325           # Pression relative -> absolue
    reference_debut_h = 1                # Étalonnage sur la phase 1 (cas nominal, §3) : H1 à H48
    reference_fin_h = 48
    phase2_debut_h = 49                  # §3 : phase 2 de H49 à H120
    phase3_debut_h = 121                 # §3 : phase 3 de H121 à H168

    def vers_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict | None) -> "Parametres":
        """Construit des paramètres en ignorant les clés inconnues."""
        if not donnees:
            return cls()
        return cls(**{f.name: float(donnees[f.name]) for f in fields(cls) if donnees.get(f.name) is not None})

    def verifier(self) -> list[str]:
        """Renvoie la liste des incohérences (vide si tout va bien)."""
        erreurs = []
        if self.tarif_kwh_dt < 0:
            erreurs.append("Le tarif de l'électricité doit être positif.")
        if not 0 < self.approche_nominale_c < self.seuil_alerte_legere_c:
            erreurs.append(f"L'approche nominale doit être comprise entre 0 et {self.seuil_alerte_legere_c} °C.")
        if self.vfd_min_hz >= self.vfd_max_hz:
            erreurs.append("La fréquence mini du variateur doit être inférieure à la fréquence maxi.")
        if self.p_pulv_consigne_bar <= 0 or self.p_pompe_kw <= 0:
            erreurs.append("La puissance et la pression de la pompe doivent être positives.")
        return erreurs


# Libellés du formulaire de configuration (tableau §2) : (libellé, unité, pas, décimales)
LIBELLES = {
    "tarif_kwh_dt": ("Tarif électricité (STEG)", "DT/kWh", 0.001, 3),
    "approche_nominale_c": ("Approche nominale ΔTnom", "°C", 0.1, 1),
    "p_pompe_kw": ("Pompe de pulvérisation : puissance", "kW", 0.1, 1),
    "p_pulv_consigne_bar": ("Pompe de pulvérisation : pression de consigne", "bar", 0.01, 2),
    "vfd_min_hz": ("Variateur ventilateur : fréquence mini", "Hz", 1.0, 0),
    "vfd_max_hz": ("Variateur ventilateur : fréquence maxi", "Hz", 1.0, 0),
}
