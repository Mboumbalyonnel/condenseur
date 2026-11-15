"""Import des fichiers Excel de scénarios d'exploitation (.xlsx, une ou plusieurs feuilles) et .csv
(cahier des charges, §1 et §3).

- Chaque feuille contenant les colonnes A à P devient un scénario.
- La ligne d'en-tête (TIMESTAMP, HP_COND_BAR, ...) est cherchée automatiquement ; la ligne de titre
  au-dessus (« SCÉNARIO 2 : ALERTE LÉGÈRE ... ») sert à nommer le scénario.
- Sans en-tête reconnu, les colonnes A à P sont lues dans l'ordre du dictionnaire.
- Les valeurs sont contrôlées (manquantes, hors bornes, contacts non binaires).
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .tags import BINAIRES, MESURES, NOMS, PAR_NOM

LIGNES_EXPLOREES = 30


@dataclass
class RapportImport:
    nom: str
    donnees: pd.DataFrame
    erreurs: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    @property
    def valide(self) -> bool:
        return not self.erreurs and not self.donnees.empty


def _normaliser(valeur) -> str:
    return str(valeur).strip().upper().replace(" ", "_")


def _ligne_entete(brut: pd.DataFrame) -> int | None:
    """Indice de la première ligne qui contient au moins la moitié des noms de colonnes."""
    attendus = set(NOMS)
    for i in range(min(LIGNES_EXPLOREES, len(brut))):
        cellules = {_normaliser(v) for v in brut.iloc[i].tolist()}
        if len(attendus & cellules) >= len(attendus) // 2:
            return i
    return None


def _feuilles(source, nom_fichier: str) -> dict[str, pd.DataFrame]:
    """Lit le fichier sans interpréter d'en-tête : {nom de feuille: cellules brutes}."""
    extension = Path(nom_fichier).suffix.lower()
    if extension in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(source, header=None, sheet_name=None)
    if extension == ".csv":
        contenu = source.read() if hasattr(source, "read") else Path(source).read_bytes()
        for encodage in ("utf-8-sig", "cp1252"):
            try:
                texte = contenu.decode(encodage)
                break
            except UnicodeDecodeError:
                continue
        lignes = texte.splitlines()
        echantillon = "\n".join(lignes[:LIGNES_EXPLOREES])
        separateur = ";" if echantillon.count(";") >= echantillon.count(",") / 2 else ","
        # Nombre de colonnes imposé : sinon pandas le déduit d'une éventuelle ligne de titre
        nb_colonnes = max((ligne.count(separateur) + 1 for ligne in lignes), default=1)
        return {Path(nom_fichier).stem: pd.read_csv(io.StringIO(texte), header=None, sep=separateur, dtype=str,
                                                    names=range(nb_colonnes), engine="python")}
    raise ValueError(f"Format non pris en charge : {extension} (attendu : .xlsx ou .csv)")


def _nom_scenario(titre: str | None, feuille: str, nom_fichier: str) -> str:
    """« SCÉNARIO 2 : ALERTE LÉGÈRE — DÉBUT D'ENTARTRAGE » -> « 2 · Alerte légère — début d'entartrage »."""
    numero = None
    libelle = None
    if titre:
        m = re.search(r"SC[ÉE]NARIO\s+(\d+)", titre, re.IGNORECASE)
        numero = m.group(1) if m else None
        libelle = re.split(r"\s:\s|TEMPS R[ÉE]EL\s*[—-]\s*", titre, maxsplit=1)[-1].strip(" :—-")
    if numero is None:
        for texte in (feuille, Path(nom_fichier).stem):
            m = re.search(r"(?:^|_)(\d)(?:_|$)", texte)
            if m:
                numero = m.group(1)
                break
    if not libelle:
        libelle = feuille if feuille and not feuille.startswith("Feuil") else Path(nom_fichier).stem
        libelle = re.sub(r"^\d+_", "", libelle).replace("_", " ")
    libelle = libelle[:1].upper() + libelle[1:].lower()
    return f"{numero} · {libelle}" if numero else libelle


def _vers_nombre(serie: pd.Series) -> pd.Series:
    if not pd.api.types.is_numeric_dtype(serie):
        serie = serie.astype(str).str.strip().str.replace(" ", "").str.replace(",", ".")
    return pd.to_numeric(serie, errors="coerce")


def _vers_horodatage(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    numerique = pd.to_numeric(serie, errors="coerce")
    if numerique.notna().mean() > 0.9:
        # Numéro de série Excel (jours depuis le 30/12/1899)
        return pd.to_datetime(numerique, unit="D", origin="1899-12-30").dt.round("s")
    texte = serie.astype(str).str.strip()
    iso = pd.to_datetime(texte, errors="coerce", format="ISO8601")
    if iso.notna().mean() > 0.9:
        return iso
    return pd.to_datetime(texte, errors="coerce", dayfirst=True, format="mixed")


def _lire_feuille(brut: pd.DataFrame, feuille: str, nom_fichier: str) -> RapportImport | None:
    brut = brut.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    if brut.empty:
        return None
    entete = _ligne_entete(brut)
    titre = None
    if entete:
        cellules = [str(v) for v in brut.iloc[:entete].stack().tolist() if str(v).strip()]
        titre = next((c for c in cellules if re.search(r"SC[ÉE]NARIO", c, re.IGNORECASE)), None)
    rapport = RapportImport(_nom_scenario(titre, feuille, nom_fichier), pd.DataFrame())

    if entete is not None:
        colonnes = [_normaliser(v) for v in brut.iloc[entete].tolist()]
        df = brut.iloc[entete + 1:].copy()
        df.columns = colonnes
        manquantes = [n for n in NOMS if n not in colonnes]
        if manquantes:
            rapport.erreurs.append("Colonnes manquantes : " + ", ".join(manquantes))
            return rapport
        df = df[NOMS]
    elif brut.shape[1] >= len(NOMS):
        rapport.avertissements.append("En-tête non reconnu : colonnes A à P lues dans l'ordre du dictionnaire.")
        df = brut.iloc[:, :len(NOMS)].copy()
        df.columns = NOMS
    else:
        rapport.erreurs.append(f"En-tête non reconnu et seulement {brut.shape[1]} colonnes (16 attendues, A à P).")
        return rapport

    df["TIMESTAMP"] = _vers_horodatage(df["TIMESTAMP"])
    for nom in MESURES:
        df[nom] = _vers_nombre(df[nom])

    sans_date = int(df["TIMESTAMP"].isna().sum())
    if sans_date:
        rapport.avertissements.append(f"{sans_date} ligne(s) sans horodatage valide ignorée(s).")
        df = df[df["TIMESTAMP"].notna()]

    incompletes = df[MESURES].isna().any(axis=1)
    if incompletes.any():
        rapport.avertissements.append(
            f"{int(incompletes.sum())} ligne(s) avec des valeurs manquantes ou non numériques ignorée(s).")
        df = df[~incompletes]

    doublons = df["TIMESTAMP"].duplicated(keep="last")
    if doublons.any():
        rapport.avertissements.append(f"{int(doublons.sum())} horodatage(s) en double : dernière valeur conservée.")
        df = df[~doublons]

    for nom in BINAIRES:
        hors = ~df[nom].isin([0, 1])
        if hors.any():
            rapport.avertissements.append(f"{nom} : {int(hors.sum())} valeur(s) autres que 0/1, arrondies.")
            df[nom] = df[nom].round().clip(0, 1)
        df[nom] = df[nom].astype(int)
    for nom in MESURES:
        tag = PAR_NOM[nom]
        if tag.mini is None:
            continue
        hors = (df[nom] < tag.mini) | (df[nom] > tag.maxi)
        if hors.any():
            rapport.avertissements.append(
                f"{nom} : {int(hors.sum())} valeur(s) hors de la plage plausible [{tag.mini} ; {tag.maxi}] {tag.unite}.")

    df = df.sort_values("TIMESTAMP").reset_index(drop=True)
    if df.empty:
        rapport.erreurs.append("Aucune ligne exploitable.")
    rapport.donnees = df
    return rapport


def importer(source, nom_fichier: str) -> list[RapportImport]:
    """Importe un fichier .xlsx (toutes ses feuilles) ou .csv. Un rapport par scénario trouvé."""
    try:
        feuilles = _feuilles(source, nom_fichier)
    except Exception as exc:  # fichier illisible
        return [RapportImport(Path(nom_fichier).stem, pd.DataFrame(), erreurs=[f"Lecture impossible : {exc}"])]
    rapports = [r for nom, brut in feuilles.items() if (r := _lire_feuille(brut, str(nom), nom_fichier))]
    if not rapports:
        return [RapportImport(Path(nom_fichier).stem, pd.DataFrame(), erreurs=["Fichier vide."])]
    return rapports
