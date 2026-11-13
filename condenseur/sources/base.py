"""Interface commune des sources de données temps réel (mode industriel, GTC)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from ..tags import MESURES


class ErreurSource(Exception):
    """Erreur de communication avec l'équipement."""


class SourceDonnees(ABC):
    """Une source fournit une mesure instantanée de tous les tags GTC."""

    nom: str = "source"

    @abstractmethod
    def lire_mesures(self) -> dict[str, float]:
        """Lit une valeur pour chaque tag de MESURES (sans TIMESTAMP)."""

    def tester(self) -> str:
        """Teste la connexion ; renvoie un message lisible ou lève ErreurSource."""
        valeurs = self.lire_mesures()
        return f"Connexion réussie : {len(valeurs)} tags lus."

    def acquerir(self, horodatage: datetime | None = None) -> pd.DataFrame:
        """Lit une mesure et la renvoie sous la forme d'une ligne horodatée."""
        valeurs = self.lire_mesures()
        manquants = [n for n in MESURES if n not in valeurs]
        if manquants:
            raise ErreurSource("Tags non lus : " + ", ".join(manquants))
        # Arrondi : un flottant 32 bits ne porte qu'environ 7 chiffres significatifs
        ligne = {"TIMESTAMP": pd.Timestamp(horodatage or datetime.now()).floor("s"),
                 **{k: round(float(v), 4) for k, v in valeurs.items()}}
        for nom in ("NIV_BAC_OK", "DEF_VENT_DI", "DEF_POMPE_DI"):
            ligne[nom] = int(round(ligne[nom]))
        return pd.DataFrame([ligne])
