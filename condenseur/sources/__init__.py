"""Sources de données : fichier Excel (mode académique) et connecteurs GTC (mode industriel futur)."""

from __future__ import annotations

from .base import ErreurSource, SourceDonnees
from .futures import SourceBACnet, SourceModbusTCP, SourceOPCUA

# type -> (libellé, classe ; None = import de fichier)
TYPES_SOURCES = {
    "fichier": ("Import de fichier (.xlsx / .csv)", None),
    "modbus_tcp": ("Modbus TCP (mode industriel futur)", SourceModbusTCP),
    "bacnet": ("BACnet/IP (mode industriel futur)", SourceBACnet),
    "opc_ua": ("OPC UA (mode industriel futur)", SourceOPCUA),
}


def creer_source(type_source: str, config: dict | None = None) -> SourceDonnees:
    if type_source not in TYPES_SOURCES:
        raise ErreurSource(f"Type de source inconnu : {type_source}")
    classe = TYPES_SOURCES[type_source][1]
    if classe is None:
        raise ErreurSource("Cette machine est alimentée par import de fichier.")
    return classe(config)


__all__ = ["ErreurSource", "SourceDonnees", "SourceModbusTCP", "SourceBACnet", "SourceOPCUA",
           "TYPES_SOURCES", "creer_source"]
