"""Connecteurs GTC du mode industriel futur (cahier des charges, §1).

L'architecture est prête : chaque protocole est une classe dérivée de SourceDonnees.
Il suffira d'implémenter `lire_mesures()` (pymodbus, BAC0, asyncua) en associant chaque
tag GTC normalisé (§4) à un registre Modbus, un objet BACnet ou un nœud OPC UA.
"""

from __future__ import annotations

from .base import ErreurSource, SourceDonnees


class _SourceFuture(SourceDonnees):
    CONFIG_DEFAUT: dict = {}

    def __init__(self, config: dict | None = None):
        self.config = {**self.CONFIG_DEFAUT, **(config or {})}

    def lire_mesures(self) -> dict[str, float]:
        raise ErreurSource(f"Connecteur {self.nom} prévu pour le mode industriel futur, non implémenté.")


class SourceModbusTCP(_SourceFuture):
    nom = "Modbus TCP"
    CONFIG_DEFAUT = {"hote": "192.168.1.10", "port": 502, "esclave": 1, "registres": {}}


class SourceBACnet(_SourceFuture):
    nom = "BACnet/IP"
    CONFIG_DEFAUT = {"adresse": "192.168.1.10", "device_id": 1001, "objets": {}}


class SourceOPCUA(_SourceFuture):
    nom = "OPC UA"
    CONFIG_DEFAUT = {"url": "opc.tcp://192.168.1.10:4840", "noeuds": {}}
