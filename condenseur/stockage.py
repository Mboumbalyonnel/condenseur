"""Persistance SQLite : bibliothèque de fluides, sites, machines, scénarios et mesures."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from .fluides import FLUIDES_DEFAUT, Fluide
from .modeles import Machine, Scenario, Site
from .parametres import Parametres
from .tags import BINAIRES, MESURES, NOMS

SCHEMA = """
CREATE TABLE IF NOT EXISTS fluides (
    nom TEXT PRIMARY KEY,
    designation TEXT NOT NULL DEFAULT '',
    a REAL NOT NULL, b REAL NOT NULL, c REAL NOT NULL,
    t_min_c REAL NOT NULL, t_max_c REAL NOT NULL,
    source TEXT NOT NULL DEFAULT ''
);
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
    fluide TEXT NOT NULL DEFAULT 'NH3',
    parametres TEXT NOT NULL DEFAULT '{}',
    UNIQUE (site_id, nom)
);
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    fichier TEXT NOT NULL DEFAULT '',
    UNIQUE (machine_id, nom)
);
CREATE TABLE IF NOT EXISTS mesures (
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
""" + ",\n".join(f"    {nom} REAL NOT NULL" for nom in MESURES) + """,
    PRIMARY KEY (scenario_id, timestamp)
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
            if cx.execute("SELECT COUNT(*) FROM fluides").fetchone()[0] == 0:
                for f in FLUIDES_DEFAUT:
                    self._ecrire_fluide(cx, f)

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

    # ---------------------------------------------------------------- Fluides
    @staticmethod
    def _ecrire_fluide(cx, f: Fluide) -> None:
        cx.execute("INSERT OR REPLACE INTO fluides (nom, designation, a, b, c, t_min_c, t_max_c, source) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (f.nom.strip(), f.designation, f.a, f.b, f.c, f.t_min_c, f.t_max_c, f.source))

    def fluides(self) -> list[Fluide]:
        with self._connexion() as cx:
            return [Fluide(**dict(r)) for r in cx.execute("SELECT * FROM fluides ORDER BY nom")]

    def fluide(self, nom: str) -> Fluide | None:
        with self._connexion() as cx:
            r = cx.execute("SELECT * FROM fluides WHERE nom = ?", (nom,)).fetchone()
            return Fluide(**dict(r)) if r else None

    def enregistrer_fluides(self, fluides: list[Fluide]) -> None:
        """Remplace toute la bibliothèque. Un fluide utilisé par une machine ne peut pas disparaître."""
        noms = {f.nom.strip() for f in fluides}
        utilises = {m.fluide for m in self.machines()}
        manquants = utilises - noms
        if manquants:
            raise ValueError("Fluide(s) utilisé(s) par une machine : " + ", ".join(sorted(manquants)))
        with self._connexion() as cx:
            cx.execute("DELETE FROM fluides")
            for f in fluides:
                self._ecrire_fluide(cx, f)

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
        return Machine(id=r["id"], site_id=r["site_id"], nom=r["nom"], description=r["description"],
                       fluide=r["fluide"], parametres=Parametres.depuis_dict(json.loads(r["parametres"])))

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

    def creer_machine(self, site_id: int, nom: str, description: str = "", fluide: str = "NH3",
                      parametres: Parametres | None = None) -> Machine:
        parametres = parametres or Parametres()
        with self._connexion() as cx:
            cur = cx.execute(
                "INSERT INTO machines (site_id, nom, description, fluide, parametres) VALUES (?, ?, ?, ?, ?)",
                (site_id, nom.strip(), description.strip(), fluide, json.dumps(parametres.vers_dict())))
        return self.machine(cur.lastrowid)

    def enregistrer_machine(self, m: Machine) -> None:
        with self._connexion() as cx:
            cx.execute("UPDATE machines SET site_id = ?, nom = ?, description = ?, fluide = ?, parametres = ? "
                       "WHERE id = ?",
                       (m.site_id, m.nom.strip(), m.description.strip(), m.fluide,
                        json.dumps(m.parametres.vers_dict()), m.id))

    def supprimer_machine(self, machine_id: int) -> None:
        with self._connexion() as cx:
            cx.execute("DELETE FROM machines WHERE id = ?", (machine_id,))

    # -------------------------------------------------------------- Scénarios
    def scenarios(self, machine_id: int) -> list[Scenario]:
        with self._connexion() as cx:
            lignes = cx.execute(
                "SELECT s.*, (SELECT COUNT(*) FROM mesures m WHERE m.scenario_id = s.id) AS nb_mesures "
                "FROM scenarios s WHERE machine_id = ? ORDER BY s.nom", (machine_id,))
            return [Scenario(**dict(r)) for r in lignes]

    def enregistrer_scenario(self, machine_id: int, nom: str, df: pd.DataFrame, fichier: str = "") -> Scenario:
        """Crée le scénario (ou remplace ses mesures s'il existe déjà sous ce nom)."""
        nom = nom.strip()
        lignes = [(pd.Timestamp(r["TIMESTAMP"]).isoformat(sep=" "), *(float(r[n]) for n in MESURES))
                  for _, r in df[NOMS].iterrows()]
        colonnes = ", ".join(["scenario_id", "timestamp", *MESURES])
        marques = ", ".join("?" * (len(MESURES) + 2))
        with self._connexion() as cx:
            r = cx.execute("SELECT id FROM scenarios WHERE machine_id = ? AND nom = ?", (machine_id, nom)).fetchone()
            if r:
                sid = r["id"]
                cx.execute("UPDATE scenarios SET fichier = ? WHERE id = ?", (fichier, sid))
                cx.execute("DELETE FROM mesures WHERE scenario_id = ?", (sid,))
            else:
                sid = cx.execute("INSERT INTO scenarios (machine_id, nom, fichier) VALUES (?, ?, ?)",
                                 (machine_id, nom, fichier)).lastrowid
            cx.executemany(f"INSERT OR REPLACE INTO mesures ({colonnes}) VALUES ({marques})",
                           [(sid, *l) for l in lignes])
        return Scenario(sid, machine_id, nom, fichier, len(lignes))

    def supprimer_scenario(self, scenario_id: int) -> None:
        with self._connexion() as cx:
            cx.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))

    def mesures(self, scenario_id: int) -> pd.DataFrame:
        with self._connexion() as cx:
            df = pd.read_sql_query("SELECT * FROM mesures WHERE scenario_id = ? ORDER BY timestamp", cx,
                                   params=[scenario_id])
        df = df.drop(columns="scenario_id").rename(columns={"timestamp": "TIMESTAMP"})
        df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
        for nom in BINAIRES:
            df[nom] = df[nom].astype(int)
        return df
