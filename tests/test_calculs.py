"""Tests : fluides, normalisation selon Q0, surcoûts STEG / SONEDE, arbre de décision, import, stockage."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from condenseur.demo import CLASSEUR_CE02, FICHIERS_CE01, PARAMETRES_CE02, initialiser
from condenseur.diagnostic import (ALERTE_AERAULIQUE, ALERTE_GRAVE, ALERTE_LEGERE, NOMINAL, diagnostiquer, evaluer,
                                   niveau_approche)
from condenseur.fluides import FLUIDES_DEFAUT
from condenseur.import_donnees import importer
from condenseur.moteur import analyser
from condenseur.parametres import Parametres
from condenseur.stockage import Depot
from condenseur.tags import NOMS

NH3 = FLUIDES_DEFAUT[0]
P = Parametres()


def mesure(**ecarts) -> dict:
    """Mesure nominale de l'installation CE-01, modifiable."""
    base = dict(TIMESTAMP=pd.Timestamp("2026-09-01 00:00"), HP_COND_BAR=10.77, T_EXT_SEC_C=26.2, HR_EXT_PCT=70.6,
                DELTA_T_APP_C=3.0, P_PULV_BAR=1.85, Q_PULV_M3H=45.0, Q_PURGE_LH=120.0, NIV_BAC_OK=1,
                VFD_VENT_HZ=39.1, DEF_VENT_DI=0, DEF_POMPE_DI=0, P_ELEC_COMP_KW=119.05, Q0_FROID_KW=500.0,
                SURCOUT_ELEC_DT_H=0.0, SURCOUT_EAU_DT_H=0.0)
    return base | ecarts


def regle(**ecarts) -> int:
    m = mesure(**ecarts)
    return diagnostiquer(evaluer(m, P), niveau_approche(m["DELTA_T_APP_C"], P)).regle


# ------------------------------------------------------------------ Fluides
def test_nh3_antoine():
    # NH3 : 11,67 bar abs à 30 °C (coefficients NIST, écart de l'ordre de 0,3 °C)
    assert NH3.temperature_saturation(11.672) == pytest.approx(30.0, abs=0.4)
    assert NH3.temperature_condensation(10.77) == pytest.approx(30.6, abs=0.2)


@pytest.mark.parametrize("nom, p_abs, t", [("CO2", 34.85, 0.0), ("R404A", 18.27, 40.0), ("R134a", 10.166, 40.0)])
def test_bibliotheque_fluides(nom, p_abs, t):
    f = next(f for f in FLUIDES_DEFAUT if f.nom == nom)
    assert f.temperature_saturation(p_abs) == pytest.approx(t, abs=0.2)
    assert f.pression_saturation(t) == pytest.approx(p_abs, rel=0.01)


# ------------------------------------------------------------------ Seuils
@pytest.mark.parametrize("dt, niveau", [(3.0, NOMINAL), (4.49, NOMINAL), (4.5, ALERTE_LEGERE), (6.0, ALERTE_GRAVE),
                                        (8.49, ALERTE_GRAVE), (8.5, ALERTE_AERAULIQUE)])
def test_seuils(dt, niveau):
    assert niveau_approche(dt, P) == niveau


# ------------------------------------------------------------------ Arbre de décision
def test_arbre_six_branches():
    assert regle() == 0
    assert regle(NIV_BAC_OK=0, P_PULV_BAR=0.4) == 1
    assert regle(P_PULV_BAR=1.2, DELTA_T_APP_C=7.5) == 2
    assert regle(DEF_VENT_DI=1, DELTA_T_APP_C=8.8) == 3
    assert regle(VFD_VENT_HZ=20.0, DELTA_T_APP_C=8.8) == 3          # VFD bloqué au minimum
    assert regle(Q_PULV_M3H=34.0, DELTA_T_APP_C=6.8) == 4
    assert regle(Q_PURGE_LH=280.0, DELTA_T_APP_C=3.2) == 5
    assert regle(DELTA_T_APP_C=5.0) == 6


def test_ordre_des_branches():
    # Bac bas prioritaire sur tout le reste
    assert regle(NIV_BAC_OK=0, P_PULV_BAR=0.4, DEF_VENT_DI=1, Q_PURGE_LH=500.0) == 1
    # Chute de pression prioritaire sur le colmatage
    assert regle(P_PULV_BAR=1.2, Q_PULV_M3H=5.0) == 2


def test_tolerance_pression():
    assert regle(P_PULV_BAR=1.70, Q_PULV_M3H=45.0, DELTA_T_APP_C=5.0) == 6     # -8 % : normale
    assert regle(P_PULV_BAR=1.60, DELTA_T_APP_C=5.0) == 2                      # -13,5 % : chute


# ------------------------------------------------------------------ Normalisation et surcoûts
def test_normalisation_q0_et_surcouts():
    df = pd.DataFrame([mesure(P_ELEC_COMP_KW=125.71, DELTA_T_APP_C=5.0),
                       mesure(TIMESTAMP=pd.Timestamp("2026-09-01 01:00"), P_ELEC_COMP_KW=62.86, Q0_FROID_KW=250.0,
                              Q_PURGE_LH=280.0)])
    r = analyser(df, P, NH3).donnees
    assert r["P_REF_KW"].tolist() == pytest.approx([119.05, 59.525])
    assert r.loc[0, "COUT_ELEC_DT_H"] == pytest.approx(6.66 * 0.280)
    # Même dégradation relative à demi-charge : écart normalisé identique
    assert r.loc[1, "ECART_NORM_PCT"] == pytest.approx(r.loc[0, "ECART_NORM_PCT"], abs=0.01)
    assert r.loc[1, "COUT_EAU_DT_H"] == pytest.approx(0.160 * 1.250)
    assert r.loc[0, "COUT_EAU_DT_H"] == 0


def test_pas_de_surcout_negatif():
    r = analyser(pd.DataFrame([mesure(P_ELEC_COMP_KW=110.0, Q_PURGE_LH=90.0)]), P, NH3).donnees
    assert r.loc[0, "COUT_ELEC_DT_H"] == 0 and r.loc[0, "COUT_EAU_DT_H"] == 0


# ------------------------------------------------------------------ Fichiers fournis
ATTENDUS_CE01 = {"1": 0, "2": 6, "3": 4, "4": 5, "5": 1}
ATTENDUS_CE02 = {"1": 0, "2": 6, "3": 2, "4": 5, "5": 1, "6": 3}


@pytest.mark.skipif(not FICHIERS_CE01, reason="fichiers de scénarios absents")
def test_fichiers_dedies():
    for fichier in FICHIERS_CE01:
        (r,) = importer(fichier, fichier.name)
        assert r.valide and len(r.donnees) == 24 and not r.avertissements
        res = analyser(r.donnees, P, NH3).donnees
        assert set(res["REGLE"]) == {ATTENDUS_CE01[r.nom[0]]}, r.nom
        # Surcoûts recalculés = colonnes O et P du fichier
        assert res["COUT_ELEC_DT_H"].to_numpy() == pytest.approx(res["SURCOUT_ELEC_DT_H"].to_numpy(), abs=0.002)
        assert res["COUT_EAU_DT_H"].to_numpy() == pytest.approx(res["SURCOUT_EAU_DT_H"].to_numpy(), abs=0.002)


@pytest.mark.skipif(not CLASSEUR_CE02.exists(), reason="classeur des 6 scénarios absent")
def test_classeur_six_scenarios():
    rapports = importer(CLASSEUR_CE02, CLASSEUR_CE02.name)
    assert len(rapports) == 6
    for r in rapports:
        assert r.valide, r.erreurs
        res = analyser(r.donnees, PARAMETRES_CE02, NH3).donnees
        assert set(res["REGLE"]) == {ATTENDUS_CE02[r.nom[0]]}, r.nom
        assert res["COUT_EAU_DT_H"].to_numpy() == pytest.approx(res["SURCOUT_EAU_DT_H"].to_numpy(), abs=0.005)


# ------------------------------------------------------------------ Import
def test_import_csv_virgule_decimale(tmp_path: Path):
    lignes = ["SCÉNARIO 9 : ESSAI CSV", ";".join(NOMS)]
    for h in range(3):
        m = mesure()
        valeurs = [f"01/09/2026 0{h}:00"] + [str(m[n]).replace(".", ",") for n in NOMS[1:]]
        lignes.append(";".join(valeurs))
    chemin = tmp_path / "essai.csv"
    chemin.write_text("\n".join(lignes), encoding="utf-8")
    (r,) = importer(chemin, chemin.name)
    assert r.valide and len(r.donnees) == 3
    assert r.nom == "9 · Essai csv"
    assert r.donnees["P_PULV_BAR"].iloc[0] == pytest.approx(1.85)


def test_import_colonne_manquante(tmp_path: Path):
    df = pd.DataFrame([mesure()]).drop(columns="Q_PURGE_LH")
    chemin = tmp_path / "incomplet.xlsx"
    df.to_excel(chemin, index=False)
    (r,) = importer(chemin, chemin.name)
    assert not r.valide and "Q_PURGE_LH" in r.erreurs[0]


# ------------------------------------------------------------------ Stockage
def test_depot_et_initialisation(tmp_path: Path):
    d = Depot(tmp_path / "essai.db")
    assert {f.nom for f in d.fluides()} == {"NH3", "CO2", "R404A", "R134a"}
    initialiser(d)
    (site,) = d.sites()
    machines = d.machines(site.id)
    assert len(machines) == 2
    nb = {m.nom: len(d.scenarios(m.id)) for m in machines}
    if FICHIERS_CE01 and CLASSEUR_CE02.exists():
        assert sorted(nb.values()) == [5, 6]
    # Un fluide utilisé par une machine ne peut pas être retiré
    with pytest.raises(ValueError):
        d.enregistrer_fluides([f for f in d.fluides() if f.nom != "NH3"])
    # Réimport sous le même nom : remplacement
    m = machines[0]
    s = d.enregistrer_scenario(m.id, "Essai", pd.DataFrame([mesure()]))
    s2 = d.enregistrer_scenario(m.id, "Essai", pd.DataFrame([mesure(), mesure(TIMESTAMP=pd.Timestamp("2026-09-01 01:00"))]))
    assert s2.id == s.id and len(d.mesures(s.id)) == 2
    initialiser(d)                       # sans effet sur une base déjà remplie
    assert len(d.sites()) == 1


def test_parametres_verifier():
    assert Parametres().verifier() == []
    assert Parametres(seuil_grave_c=4.0).verifier()
    assert Parametres(vfd_min_hz=60).verifier()
    assert Parametres.depuis_dict({"tarif_elec_dt_kwh": "0.3", "inconnu": 1}).tarif_elec_dt_kwh == 0.3
