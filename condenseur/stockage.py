"""Persistance SQLite : sites, machines (avec leurs paramètres et leur source) et mesures."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from .modeles import Machine, Site
from .parametres import Parametres
from .tags import MESURES, NOMS

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    localisation TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    parametres TEXT NOT NULL DEFAULT '{}',
    source_type TEXT NOT NULL DEFAULT 'fichier',
    source_config TEXT NOT NULL DEFAULT '{}',
    UNIQUE (site_id, nom)
);
CREATE TABLE IF NOT EXISTS mesures (
    machine_id INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
""" + ",\n".join(f"    {nom} REAL NOT NULL" for nom in MESURES) + """,
    PRIMARY KEY (machine_id, timestamp)
);
"""

CHEMIN_DEFAUT = Path(__file__).resolve().parent.parent / "donnees" / "condenseur.db"


class Depot:
    """Accès à la base SQLite. Une connexion par opération (compatible avec Streamlit)."""

    def __init__(self, chemin: str | Path = CHEMIN_DEFAUT):
        self.chemin = Path(chemin)
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        with self._connexion() as cx:
            cx.executescript(SCHEMA)

    @contextmanager
    def _connexion(self):
        cx = sqlite3.connect(self.chemin)
        cx.row_factory = sqlite3.Row
        cx.execute("PRAGMA foreign_keys = ON")
        try:
            yield cx
            cx.commit()
        finally:
            cx.close()

    # ------------------------------------------------------------------ Sites
    def sites(self) -> list[Site]:
        with self._connexion() as cx:
            return [Site(**dict(r)) for r in cx.execute("SELECT * FROM sites ORDER BY nom")]

    def creer_site(self, nom: str, localisation: str = "") -> Site:
        with self._connexion() as cx:
            cur = cx.execute("INSERT INTO sites (nom, localisation) VALUES (?, ?)", (nom.strip(), localisation.strip()))
            return Site(cur.lastrowid, nom.strip(), localisation.strip())

    def modifier_site(self, site: Site) -> None:
        with self._connexion() as cx:
            cx.execute("UPDATE sites SET nom = ?, localisation = ? WHERE id = ?", (site.nom, site.localisation, site.id))

    def supprimer_site(self, site_id: int) -> None:
        with self._connexion() as cx:
            cx.execute("DELETE FROM sites WHERE id = ?", (site_id,))

    # --------------------------------------------------------------- Machines
    @staticmethod
    def _machine(r: sqlite3.Row) -> Machine:
        return Machine(
            id=r["id"], site_id=r["site_id"], nom=r["nom"], description=r["description"],
            parametres=Parametres.depuis_dict(json.loads(r["parametres"])),
            source_type=r["source_type"], source_config=json.loads(r["source_config"]),
        )

    def machines(self, site_id: int | None = None) -> list[Machine]:
        with self._connexion() as cx:
            if site_id is None:
                lignes = cx.execute("SELECT * FROM machines ORDER BY nom")
            else:
                lignes = cx.execute("SELECT * FROM machines WHERE site_id = ? ORDER BY nom", (site_id,))
            return [self._machine(r) for r in lignes]

    def machine(self, machine_id: int) -> Machine | None:
        with self._connexion() as cx:
            r = cx.execute("SELECT * FROM machines WHERE id = ?", (machine_id,)).fetchone()
            return self._machine(r) if r else None

    def creer_machine(self, site_id: int, nom: str, description: str = "",
                      parametres: Parametres | None = None) -> Machine:
        parametres = parametres or Parametres()
        with self._connexion() as cx:
            cur = cx.execute(
                "INSERT INTO machines (site_id, nom, description, parametres) VALUES (?, ?, ?, ?)",
                (site_id, nom.strip(), description.strip(), json.dumps(parametres.vers_dict())),
            )
        return self.machine(cur.lastrowid)

    def enregistrer_machine(self, m: Machine) -> None:
        with self._connexion() as cx:
            cx.execute(
                "UPDATE machines SET site_id = ?, nom = ?, description = ?, parametres = ?, "
                "source_type = ?, source_config = ? WHERE id = ?",
                (m.site_id, m.nom, m.description, json.dumps(m.parametres.vers_dict()),
                 m.source_type, json.dumps(m.source_config), m.id),
            )

    def supprimer_machine(self, machine_id: int) -> None:
        with self._connexion() as cx:
            cx.execute("DELETE FROM machines WHERE id = ?", (machine_id,))

    # ---------------------------------------------------------------- Mesures
    def enregistrer_mesures(self, machine_id: int, df: pd.DataFrame, remplacer: bool = False) -> int:
        """Insère (ou met à jour) des mesures. Renvoie le nombre de lignes écrites."""
        lignes = [
            (machine_id, pd.Timestamp(r["TIMESTAMP"]).isoformat(sep=" "), *(float(r[n]) for n in MESURES))
            for _, r in df[NOMS].iterrows()
        ]
        colonnes = ", ".join(["machine_id", "timestamp", *MESURES])
        marques = ", ".join("?" * (len(MESURES) + 2))
        with self._connexion() as cx:
            if remplacer:
                cx.execute("DELETE FROM mesures WHERE machine_id = ?", (machine_id,))
            cx.executemany(f"INSERT OR REPLACE INTO mesures ({colonnes}) VALUES ({marques})", lignes)
        return len(lignes)

    def mesures(self, machine_id: int, debut=None, fin=None) -> pd.DataFrame:
        requete = "SELECT * FROM mesures WHERE machine_id = ?"
        args: list = [machine_id]
        if debut is not None:
            requete += " AND timestamp >= ?"
            args.append(pd.Timestamp(debut).isoformat(sep=" "))
        if fin is not None:
            requete += " AND timestamp <= ?"
            args.append(pd.Timestamp(fin).isoformat(sep=" "))
        with self._connexion() as cx:
            df = pd.read_sql_query(requete + " ORDER BY timestamp", cx, params=args)
        df = df.drop(columns="machine_id").rename(columns={"timestamp": "TIMESTAMP"})
        df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
        for nom in ("NIV_BAC_OK", "DEF_VENT_DI", "DEF_POMPE_DI"):
            df[nom] = df[nom].astype(int)
        return df

    def nombre_mesures(self, machine_id: int) -> int:
        with self._connexion() as cx:
            return cx.execute("SELECT COUNT(*) FROM mesures WHERE machine_id = ?", (machine_id,)).fetchone()[0]

    def supprimer_mesures(self, machine_id: int) -> None:
        with self._connexion() as cx:
            cx.execute("DELETE FROM mesures WHERE machine_id = ?", (machine_id,))
