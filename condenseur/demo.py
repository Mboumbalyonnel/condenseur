"""Premier lancement : crée le site TUNIFROID et ses deux condenseurs, puis importe les scénarios
d'exploitation fournis dans le dossier donnees/ (§1 : 6 scénarios)."""

from __future__ import annotations

from pathlib import Path

from .import_donnees import importer
from .parametres import Parametres
from .stockage import Depot

DOSSIER = Path(__file__).resolve().parent.parent / "donnees"

# Fichiers dédiés (un scénario par fichier) : installation de 500 kW froid
FICHIERS_CE01 = sorted(DOSSIER.glob("Scenarios_Temps_Reel_*.xlsx"))
PARAMETRES_CE01 = Parametres()

# Classeur des 6 scénarios (une feuille par scénario) : installation de 150 kW froid
CLASSEUR_CE02 = DOSSIER / "suivi_energetique_condenseur_6_scenarios.xlsx"
PARAMETRES_CE02 = Parametres(p_pulv_nom_bar=2.5, q_pulv_nom_m3h=12.0, q_purge_nom_lh=150.0,
                             p_comp_ref_kw=45.0, q0_ref_kw=150.0)


def _importer_fichiers(d: Depot, machine_id: int, fichiers: list[Path]) -> None:
    for fichier in fichiers:
        for rapport in importer(fichier, fichier.name):
            if rapport.valide:
                d.enregistrer_scenario(machine_id, rapport.nom, rapport.donnees, fichier.name)


def initialiser(d: Depot) -> None:
    """Ne fait rien si la base contient déjà un site."""
    if d.sites():
        return
    site = d.creer_site("TUNIFROID — Atelier de démonstration", "Tunis")
    ce01 = d.creer_machine(site.id, "Condenseur évaporatif CE-01", "Installation NH3 de 500 kW froid",
                           "NH3", PARAMETRES_CE01)
    _importer_fichiers(d, ce01.id, FICHIERS_CE01)
    ce02 = d.creer_machine(site.id, "Condenseur évaporatif CE-02", "Installation NH3 de 150 kW froid",
                           "NH3", PARAMETRES_CE02)
    if CLASSEUR_CE02.exists():
        _importer_fichiers(d, ce02.id, [CLASSEUR_CE02])
