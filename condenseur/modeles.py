"""Objets métier (conception orientée objet, §1) : un site regroupe des machines (condenseurs
évaporatifs) ; chaque machine a son fluide, ses paramètres de référence et ses scénarios
d'exploitation importés."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .fluides import Fluide
from .moteur import Resultat, analyser
from .parametres import Parametres


@dataclass
class Site:
    id: int
    nom: str
    localisation: str = ""


@dataclass
class Machine:
    id: int
    site_id: int
    nom: str
    description: str = ""
    fluide: str = "NH3"
    parametres: Parametres = field(default_factory=Parametres)

    def analyser(self, mesures: pd.DataFrame, fluide: Fluide) -> Resultat:
        """Applique le moteur de calcul avec les paramètres propres à cette machine."""
        return analyser(mesures, self.parametres, fluide)


@dataclass
class Scenario:
    """Un fichier (ou une feuille) Excel de scénario d'exploitation temps réel."""
    id: int
    machine_id: int
    nom: str
    fichier: str = ""
    nb_mesures: int = 0
