"""Arbre de décision diagnostique (cahier des charges, §5).

Croise l'approche thermique ΔTapp avec la pression de pulvérisation, la fréquence du
ventilateur et les défauts digitaux pour isoler la cause : hydraulique, aéraulique
ou entartrage des faisceaux.

    Défaut thermique pompe ?          oui -> HYDRAULIQUE
    Niveau du bac bas ?               oui -> HYDRAULIQUE
    Défaut thermique ventilateur ?    oui -> AÉRAULIQUE
    Pression de pulvérisation basse ? oui -> HYDRAULIQUE (filtre, pompe, fuite)
    Pression de pulvérisation haute ? oui -> HYDRAULIQUE (buses obstruées)
    Ventilateur sous sa fréquence mini ? oui -> AÉRAULIQUE
    ΔTapp sous le seuil d'alerte ?    oui -> AUCUNE (fonctionnement normal)
    Ventilateur bloqué en bas de plage alors que ΔTapp se dégrade ?
                                      oui -> AÉRAULIQUE (régulation / variateur)
    Ventilateur en cours de montée    -> ENTARTRAGE progressif (la régulation compense)
    Ventilateur à pleine vitesse      -> ENTARTRAGE confirmé (eau et air conformes)
"""

from __future__ import annotations

from dataclasses import dataclass

from .parametres import Parametres

NORMAL = "Normal"
ALERTE_LEGERE = "Alerte légère"
ALERTE_GRAVE = "Alerte grave"
NIVEAUX = [NORMAL, ALERTE_LEGERE, ALERTE_GRAVE]

AUCUNE = "Aucune"
HYDRAULIQUE = "Hydraulique"
AERAULIQUE = "Aéraulique"
ENTARTRAGE = "Entartrage"
CATEGORIES = [AUCUNE, HYDRAULIQUE, AERAULIQUE, ENTARTRAGE]

# Part basse de la plage du variateur considérée comme « ventilateur qui ne réagit pas »
PART_BASSE_VFD = 0.25


def _f(valeur: float, decimales: int) -> str:
    """Nombre au format français (virgule décimale)."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


@dataclass(frozen=True)
class Diagnostic:
    niveau: str
    categorie: str
    cause: str     # Libellé fixe (regroupable)
    detail: str    # Valeurs mesurées qui justifient le diagnostic
    action: str


def niveau_alerte(dt_app: float, p: Parametres) -> str:
    if dt_app >= p.seuil_alerte_grave_c:
        return ALERTE_GRAVE
    if dt_app >= p.seuil_alerte_legere_c:
        return ALERTE_LEGERE
    return NORMAL


def diagnostiquer(
    dt_app: float,
    p_pulv_bar: float,
    niv_bac_ok: int,
    vfd_hz: float,
    def_vent: int,
    def_pompe: int,
    p: Parametres,
) -> Diagnostic:
    """Parcourt l'arbre de décision pour une heure de mesures.

    Ordre des tests : d'abord les défauts francs (contacts digitaux), puis les écarts
    hydrauliques mesurés, puis la ventilation et enfin, par élimination,
    l'entartrage des faisceaux.
    """
    niveau = niveau_alerte(dt_app, p)
    p_basse = p.p_pulv_consigne_bar * (1 - p.tolerance_pression_pct / 100)
    p_haute = p.p_pulv_consigne_bar * (1 + p.tolerance_pression_pct / 100)
    app = f"ΔTapp = {_f(dt_app, 2)} °C"

    def d(categorie, cause, detail, action):
        return Diagnostic(niveau, categorie, cause, detail, action)

    # 1. Défauts digitaux : ils priment, quel que soit ΔTapp.
    if def_pompe:
        return d(HYDRAULIQUE, "Défaut thermique de la pompe de pulvérisation", f"DEF_POMPE_DI = 1 ; {app}",
                 "Contrôler le moteur de la pompe et son relais thermique, puis réarmer.")
    if not niv_bac_ok:
        return d(HYDRAULIQUE, "Niveau d'eau du bac insuffisant", f"NIV_BAC_OK = 0 ; {app}",
                 "Vérifier l'appoint d'eau (flotteur, électrovanne) et les fuites du bac.")
    if def_vent:
        return d(AERAULIQUE, "Défaut thermique du ventilateur", f"DEF_VENT_DI = 1 ; {app}",
                 "Contrôler le moteur du ventilateur, le variateur et le relais thermique.")

    # 2. Hydraulique : pression de pulvérisation hors tolérance.
    if p_pulv_bar < p_basse:
        return d(HYDRAULIQUE, "Pression de pulvérisation basse",
                 f"{_f(p_pulv_bar, 2)} bar pour une consigne de {_f(p.p_pulv_consigne_bar, 2)} bar "
                 f"(mini toléré {_f(p_basse, 3)} bar) ; {app}",
                 "Nettoyer le filtre d'aspiration, contrôler l'usure de la pompe et rechercher "
                 "une fuite sur la rampe.")
    if p_pulv_bar > p_haute:
        return d(HYDRAULIQUE, "Pression de pulvérisation haute",
                 f"{_f(p_pulv_bar, 2)} bar pour une consigne de {_f(p.p_pulv_consigne_bar, 2)} bar "
                 f"(maxi toléré {_f(p_haute, 3)} bar) ; {app}",
                 "Buses de pulvérisation obstruées : démonter et détartrer les buses.")

    # 3. Aéraulique : ventilateur sous sa plage de régulation.
    if vfd_hz < p.vfd_min_hz:
        return d(AERAULIQUE, "Ventilateur sous sa fréquence mini",
                 f"{_f(vfd_hz, 1)} Hz pour une plage de {_f(p.vfd_min_hz, 0)} à {_f(p.vfd_max_hz, 0)} Hz ; {app}",
                 "Vérifier la marche du ventilateur et le paramétrage du variateur.")

    if niveau == NORMAL:
        return d(AUCUNE, "Fonctionnement normal", app, "Aucune action requise.")

    # 4. Échange dégradé alors que l'eau est conforme : on regarde le ventilateur.
    bas_de_plage = p.vfd_min_hz + PART_BASSE_VFD * (p.vfd_max_hz - p.vfd_min_hz)
    if vfd_hz < bas_de_plage:
        return d(AERAULIQUE, "Ventilateur bloqué en bas de plage malgré la dégradation",
                 f"{_f(vfd_hz, 1)} Hz (bas de plage < {_f(bas_de_plage, 1)} Hz) ; {app}",
                 "Vérifier la consigne de régulation HP, le variateur, les courroies et les "
                 "pare-gouttelettes.")
    if vfd_hz < p.vfd_max_hz - p.marge_vfd_hz:
        return d(ENTARTRAGE, "Encrassement progressif des faisceaux (ventilateur en compensation)",
                 f"Eau conforme ; ventilateur à {_f(vfd_hz, 1)} Hz, réserve de "
                 f"{_f(p.vfd_max_hz - vfd_hz, 1)} Hz ; {app}",
                 "Programmer une inspection des tubes et contrôler le traitement d'eau (TH, purge).")

    # 5. Par élimination : eau et air conformes, ventilateur à fond, échange dégradé.
    return d(ENTARTRAGE, "Entartrage des faisceaux confirmé (ventilateur à pleine vitesse)",
             f"Eau conforme ; ventilateur à {_f(vfd_hz, 1)} Hz, plus de réserve ; {app}",
             "Planifier un détartrage des tubes et contrôler le traitement d'eau "
             "(TH, purge de déconcentration).")
