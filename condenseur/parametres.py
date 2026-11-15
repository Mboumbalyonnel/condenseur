"""Paramètres de référence d'une machine, saisis dans l'interface (cahier des charges, §2)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


@dataclass
class Parametres:
    # Tarifs énergie et eau
    tarif_elec_dt_kwh: float = 0.280        # STEG
    tarif_eau_dt_m3: float = 1.250          # SONEDE
    # Caractéristiques hydrauliques et aérauliques
    p_pulv_nom_bar: float = 1.85            # pression nominale de pulvérisation
    q_pulv_nom_m3h: float = 45.0            # débit nominal de pulvérisation Q_pulv_nom
    q_purge_nom_lh: float = 120.0           # débit nominal de purge Q_purge_nom
    vfd_min_hz: float = 20.0                # fréquences du variateur ventilateur
    vfd_max_hz: float = 50.0
    # Seuils d'alerte sur l'approche thermique ΔT_app
    dt_app_nominal_c: float = 3.0
    seuil_legere_c: float = 4.5
    seuil_grave_c: float = 6.0
    seuil_aeraulique_c: float = 8.5
    # Point de référence pour la normalisation selon Q0 (§4)
    p_comp_ref_kw: float = 119.05           # puissance compresseur de l'installation propre...
    q0_ref_kw: float = 500.0                # ...à cette puissance frigorifique

    # Écart toléré autour des valeurs nominales (pression, débits) avant de signaler
    # une chute ou un excès dans l'arbre de décision.
    tolerance_pct = 10.0

    def vers_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, valeurs: dict) -> "Parametres":
        noms = {f.name for f in fields(cls)}
        return cls(**{k: float(v) for k, v in valeurs.items() if k in noms})

    def verifier(self) -> list[str]:
        erreurs = []
        for f in fields(self):
            if getattr(self, f.name) < 0:
                erreurs.append(f"{LIBELLES[f.name][0]} : valeur négative.")
        if self.vfd_min_hz >= self.vfd_max_hz:
            erreurs.append("La fréquence minimale du variateur doit être inférieure à la fréquence maximale.")
        if not self.dt_app_nominal_c < self.seuil_legere_c < self.seuil_grave_c < self.seuil_aeraulique_c:
            erreurs.append("Les seuils doivent être croissants : nominal < légère < grave < aéraulique.")
        if self.q0_ref_kw <= 0 or self.p_comp_ref_kw <= 0:
            erreurs.append("Le point de référence de normalisation doit être strictement positif.")
        return erreurs


# nom -> (libellé, unité, pas de saisie, décimales)
LIBELLES = {
    "tarif_elec_dt_kwh": ("Tarif électricité STEG", "DT/kWh", 0.001, 3),
    "tarif_eau_dt_m3": ("Tarif eau industrielle SONEDE", "DT/m³", 0.001, 3),
    "p_pulv_nom_bar": ("Pression nominale de pulvérisation", "bar", 0.05, 2),
    "q_pulv_nom_m3h": ("Débit nominal de pulvérisation Q_pulv_nom", "m³/h", 0.5, 1),
    "q_purge_nom_lh": ("Débit nominal de purge Q_purge_nom", "L/h", 1.0, 0),
    "vfd_min_hz": ("Fréquence VFD ventilateur minimale", "Hz", 1.0, 0),
    "vfd_max_hz": ("Fréquence VFD ventilateur maximale", "Hz", 1.0, 0),
    "dt_app_nominal_c": ("ΔT_app nominal", "°C", 0.1, 1),
    "seuil_legere_c": ("Seuil d'alerte légère", "°C", 0.1, 1),
    "seuil_grave_c": ("Seuil d'alerte grave", "°C", 0.1, 1),
    "seuil_aeraulique_c": ("Seuil d'alerte aéraulique", "°C", 0.1, 1),
    "p_comp_ref_kw": ("Puissance compresseur de référence", "kW", 0.5, 2),
    "q0_ref_kw": ("Puissance frigorifique de référence Q0", "kW", 1.0, 0),
}
