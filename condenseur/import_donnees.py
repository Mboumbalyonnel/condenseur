"""Importation des fichiers de simulation horaire (.xlsx / .csv) (cahier des charges, §3 et §4).

- La ligne d'en-tête (TIMESTAMP, HP_COND_BAR, ...) est cherchée automatiquement :
  les lignes de titre au-dessus sont ignorées.
- Sans en-tête reconnu, les colonnes A à L sont lues dans l'ordre du dictionnaire.
- Les valeurs sont contrôlées (manquantes, hors bornes, contacts non binaires, pas horaire).
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .tags import BINAIRES, MESURES, NOMS, PAR_NOM

LIGNES_EXPLOREES = 30


@dataclass
class RapportImport:
    donnees: pd.DataFrame
    erreurs: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    @property
    def valide(self) -> bool:
        return not self.erreurs and not self.donnees.empty


def _normaliser(valeur) -> str:
    return str(valeur).strip().upper().replace(" ", "_")


def _ligne_entete(brut: pd.DataFrame) -> int | None:
    """Indice de la première ligne qui contient au moins la moitié des noms de tags."""
    attendus = set(NOMS)
    for i in range(min(LIGNES_EXPLOREES, len(brut))):
        cellules = {_normaliser(v) for v in brut.iloc[i].tolist()}
        if len(attendus & cellules) >= len(attendus) // 2:
            return i
    return None


def _lire_brut(source, nom_fichier: str) -> pd.DataFrame:
    """Lit le fichier sans interpréter d'en-tête (toutes les cellules brutes)."""
    extension = Path(nom_fichier).suffix.lower()
    if extension in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(source, header=None)
    if extension == ".csv":
        contenu = source.read() if hasattr(source, "read") else Path(source).read_bytes()
        for encodage in ("utf-8-sig", "cp1252"):
            try:
                texte = contenu.decode(encodage)
                break
            except UnicodeDecodeError:
                continue
        # Séparateur : « ; » (Excel français) ou « , »
        lignes = texte.splitlines()
        echantillon = "\n".join(lignes[:LIGNES_EXPLOREES])
        separateur = ";" if echantillon.count(";") >= echantillon.count(",") / 2 else ","
        # Nombre de colonnes imposé : sinon pandas le déduit d'une éventuelle ligne de titre
        nb_colonnes = max((ligne.count(separateur) + 1 for ligne in lignes), default=1)
        return pd.read_csv(io.StringIO(texte), header=None, sep=separateur, dtype=str,
                           names=range(nb_colonnes), engine="python")
    raise ValueError(f"Format non pris en charge : {extension} (attendu : .xlsx ou .csv)")


def _vers_nombre(serie: pd.Series) -> pd.Series:
    if not pd.api.types.is_numeric_dtype(serie):
        serie = serie.astype(str).str.strip().str.replace(" ", "").str.replace(",", ".")
    return pd.to_numeric(serie, errors="coerce")


def _vers_horodatage(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    numerique = pd.to_numeric(serie, errors="coerce")
    if numerique.notna().mean() > 0.9:
        # Numéro de série Excel (jours depuis le 30/12/1899)
        return pd.to_datetime(numerique, unit="D", origin="1899-12-30").dt.round("s")
    return pd.to_datetime(serie, errors="coerce", dayfirst=True)


def importer(source, nom_fichier: str) -> RapportImport:
    """Importe un fichier .xlsx ou .csv. `source` : chemin ou objet fichier (upload Streamlit)."""
    try:
        brut = _lire_brut(source, nom_fichier)
    except Exception as exc:  # fichier illisible
        return RapportImport(pd.DataFrame(), erreurs=[f"Lecture impossible : {exc}"])

    rapport = RapportImport(pd.DataFrame())
    brut = brut.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)

    entete = _ligne_entete(brut)
    if entete is not None:
        colonnes = [_normaliser(v) for v in brut.iloc[entete].tolist()]
        df = brut.iloc[entete + 1 :].copy()
        df.columns = colonnes
        manquantes = [n for n in NOMS if n not in colonnes]
        if manquantes:
            rapport.erreurs.append("Colonnes manquantes : " + ", ".join(manquantes))
            return rapport
        df = df[NOMS]
    elif brut.shape[1] >= len(NOMS):
        rapport.avertissements.append(
            "En-tête non reconnu : colonnes A à L lues dans l'ordre du dictionnaire des données.")
        df = brut.iloc[:, : len(NOMS)].copy()
        df.columns = NOMS
    else:
        rapport.erreurs.append(
            f"En-tête non reconnu et seulement {brut.shape[1]} colonnes (12 attendues, A à L).")
        return rapport

    # Conversion des types
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

    # Contrôles de vraisemblance (avertissements seulement : les données sont conservées)
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
    if len(df) > 1:
        ecarts = df["TIMESTAMP"].diff().dropna()
        irreguliers = int((ecarts != pd.Timedelta(hours=1)).sum())
        if irreguliers:
            rapport.avertissements.append(f"Pas de temps non horaire à {irreguliers} endroit(s).")
    if df.empty:
        rapport.erreurs.append("Aucune ligne exploitable dans le fichier.")

    rapport.donnees = df
    return rapport
