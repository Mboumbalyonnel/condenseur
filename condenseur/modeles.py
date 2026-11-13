"""Objets métier : un site industriel regroupe des machines (condenseurs) pilotées
indépendamment, chacune avec ses paramètres de référence et sa source de données."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

from .moteur import Resultat, analyser
from .parametres import Parametres

if TYPE_CHECKING:
    from .sources.base import SourceDonnees


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
    parametres: Parametres = field(default_factory=Parametres)
    source_type: str = "fichier"          # fichier | modbus_tcp | bacnet | opc_ua
    source_config: dict = field(default_factory=dict)

    def analyser(self, mesures: pd.DataFrame) -> Resultat:
        """Applique le moteur de calcul avec les paramètres propres à cette machine."""
        return analyser(mesures, self.parametres)

    def source(self) -> "SourceDonnees":
        """Instancie la source de données temps réel configurée pour cette machine."""
        from .sources import creer_source

        return creer_source(self.source_type, self.source_config)
