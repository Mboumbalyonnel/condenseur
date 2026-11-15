"""Arbre de décision diagnostique automatisé (cahier des charges, §4.1).

Les branches sont évaluées dans l'ordre du cahier des charges ; la première vérifiée l'emporte.

1. NIV_BAC_OK = 0 + chute P_pulv          -> alerte critique appoint d'eau / risque désamorçage pompe
2. NIV_BAC_OK = 1 + dérive brutale + chute P_pulv -> défaut hydraulique majeur (vanne fermée / panne pompe)
3. NIV_BAC_OK = 1 + défaut aéraulique (DEF_VENT_DI = 1 ou VFD bloqué au minimum) -> sous-ventilation
4. NIV_BAC_OK = 1 + dérive lente + P_pulv normale + Q_pulv faible     -> colmatage des buses
5. NIV_BAC_OK = 1 + dérive lente + P_pulv normale + Q_purge excessive -> purge excessive (SONEDE)
6. NIV_BAC_OK = 1 + dérive lente + P_pulv et débits normaux           -> entartrage des faisceaux

Cinétique : une chute de la pression de pulvérisation coupe l'arrosage et fait monter ΔT_app
brutalement ; à pression normale, la dérive est lente (encrassement, colmatage, purge).
La pression sépare donc les deux cinétiques. La branche 6 exige une dérive de ΔT_app
(seuil d'alerte légère atteint) ; sans dérive, le fonctionnement est nominal.
"""

from __future__ import annotations

from dataclasses import dataclass

from .parametres import Parametres

# Niveaux d'approche thermique (seuils du §2)
NOMINAL = "Nominal"
ALERTE_LEGERE = "Alerte légère"
ALERTE_GRAVE = "Alerte grave"
ALERTE_AERAULIQUE = "Alerte aéraulique"
NIVEAUX = [NOMINAL, ALERTE_LEGERE, ALERTE_GRAVE, ALERTE_AERAULIQUE]

# Gravité d'affichage
OK, ATTENTION, CRITIQUE = "ok", "attention", "critique"


def niveau_approche(dt_app: float, p: Parametres) -> str:
    if dt_app >= p.seuil_aeraulique_c:
        return ALERTE_AERAULIQUE
    if dt_app >= p.seuil_grave_c:
        return ALERTE_GRAVE
    if dt_app >= p.seuil_legere_c:
        return ALERTE_LEGERE
    return NOMINAL


@dataclass(frozen=True)
class Conditions:
    """Grandeurs croisées par l'arbre, évaluées sur une mesure."""
    bac_bas: bool
    chute_p_pulv: bool
    defaut_aeraulique: bool
    q_pulv_faible: bool
    purge_excessive: bool
    derive: bool


@dataclass(frozen=True)
class Diagnostic:
    regle: int            # 0 = nominal, 1 à 6 = branche de l'arbre
    titre: str            # intitulé du scénario d'exploitation reconnu
    gravite: str          # ok | attention | critique
    cause: str
    action: str
    cinetique: str        # « brutale », « lente » ou « aucune »


def evaluer(r, p: Parametres) -> Conditions:
    """r : mesure (dict ou pandas.Series) avec les tags du §3."""
    tol = p.tolerance_pct / 100
    return Conditions(
        bac_bas=int(r["NIV_BAC_OK"]) == 0,
        chute_p_pulv=r["P_PULV_BAR"] < p.p_pulv_nom_bar * (1 - tol),
        defaut_aeraulique=int(r["DEF_VENT_DI"]) == 1 or r["VFD_VENT_HZ"] <= p.vfd_min_hz,
        q_pulv_faible=r["Q_PULV_M3H"] < p.q_pulv_nom_m3h * (1 - tol),
        purge_excessive=r["Q_PURGE_LH"] > p.q_purge_nom_lh * (1 + tol),
        derive=r["DELTA_T_APP_C"] >= p.seuil_legere_c,
    )


def _gravite_derive(niveau: str) -> tuple[str, str]:
    """(gravité, qualificatif) d'une dérive lente selon le niveau d'approche thermique."""
    if niveau in (ALERTE_GRAVE, ALERTE_AERAULIQUE):
        return CRITIQUE, "grave"
    return ATTENTION, "légère"


def conclusion(regle: int, niveau: str) -> Diagnostic:
    """Conclusion de la branche `regle` (0 = nominal) pour un niveau d'approche donné."""
    gravite, qualificatif = _gravite_derive(niveau)
    return {
        1: Diagnostic(1, "Alerte urgente niveau bac", CRITIQUE,
                      "Alerte critique appoint d'eau / Risque de désamorçage pompe",
                      "Arrêt d'urgence pompe et ouverture appoint", "brutale"),
        2: Diagnostic(2, "Alerte grave hydraulique", CRITIQUE,
                      "Défaut hydraulique majeur (vanne fermée / panne pompe)", "Maintenance curative", "brutale"),
        3: Diagnostic(3, "Alerte aéraulique ventilateur", CRITIQUE,
                      "Alerte aéraulique majeure / Sous-ventilation",
                      "Vérification variateur et moteur ventilateur", "brutale"),
        4: Diagnostic(4, f"Alerte {qualificatif} hydraulique", gravite,
                      "Colmatage des buses de pulvérisation", "Nettoyage des rampes", "lente"),
        5: Diagnostic(5, "Alerte hydrique purge", ATTENTION,
                      "Purge excessive (surconsommation SONEDE)", "Réglage de la déconcentration", "lente"),
        6: Diagnostic(6, f"Alerte {qualificatif} entartrage", gravite,
                      "Entartrage thermique classique des faisceaux", "Détartrage chimique", "lente"),
        0: Diagnostic(0, "Fonctionnement nominal", OK,
                      "Installation propre et optimale", "Aucune intervention", "aucune"),
    }[regle]


# Branches de l'arbre dans l'ordre d'évaluation : (n°, condition affichée, attribut de Conditions)
BRANCHES = [
    (1, "NIV_BAC_OK = 0 + chute P_pulv", "bac_bas"),
    (2, "NIV_BAC_OK = 1 + dérive brutale + chute P_pulv", "chute_p_pulv"),
    (3, "NIV_BAC_OK = 1 + défaut aéraulique (DEF_VENT_DI = 1 ou VFD bloqué min)", "defaut_aeraulique"),
    (4, "NIV_BAC_OK = 1 + dérive lente + P_pulv normale + Q_pulv faible", "q_pulv_faible"),
    (5, "NIV_BAC_OK = 1 + dérive lente + P_pulv normale + Q_purge excessive", "purge_excessive"),
    (6, "NIV_BAC_OK = 1 + dérive lente + P_pulv et débits normaux", "derive"),
]


def diagnostiquer(c: Conditions, niveau: str) -> Diagnostic:
    """Première branche vérifiée, sinon fonctionnement nominal."""
    regle = next((n for n, _, attribut in BRANCHES if getattr(c, attribut)), 0)
    return conclusion(regle, niveau)
