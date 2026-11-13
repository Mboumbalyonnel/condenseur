"""Tests du moteur thermodynamique, du diagnostic, de l'import et du stockage."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from condenseur import diagnostic as diag
from condenseur.import_donnees import importer
from condenseur.moteur import analyser
from condenseur.parametres import Parametres
from condenseur.sources import ErreurSource, creer_source
from condenseur.stockage import Depot
from condenseur.tags import NOMS
from condenseur.thermo import pression_saturation_nh3, temperature_bulbe_humide, temperature_condensation

FICHIER_REEL = Path(__file__).resolve().parent.parent / "Simulation_Condenseur_7_Jours_168h.xlsx"


# ------------------------------------------------------------------ Thermodynamique
@pytest.mark.parametrize("t_c, p_abs_tables", [(25.0, 10.03), (35.0, 13.50), (40.0, 15.55)])
def test_antoine_proche_des_tables_nh3(t_c, p_abs_tables):
    assert pression_saturation_nh3(t_c) == pytest.approx(p_abs_tables, rel=0.02)


def test_antoine_inverse_est_la_reciproque():
    for t in (20.0, 30.0, 45.0):
        hp_rel = pression_saturation_nh3(t) - 1.01325
        assert temperature_condensation(hp_rel) == pytest.approx(t, abs=1e-9)


def test_stull_valeur_de_reference():
    # Exemple de l'article de Stull (2011) : T = 20 °C, HR = 50 % -> Tw = 13,7 °C
    assert temperature_bulbe_humide(20.0, 50.0) == pytest.approx(13.7, abs=0.1)
    # À saturation, bulbe humide ≈ bulbe sec
    assert temperature_bulbe_humide(25.0, 99.0) == pytest.approx(25.0, abs=0.4)


# ------------------------------------------------------------------ Jeu de mesures synthétique
def jeu(approches: list[float], p_pulv=1.85, vfd=50.0, **defauts) -> pd.DataFrame:
    """Mesures cohérentes : HP calculée pour obtenir exactement l'approche voulue."""
    n = len(approches)
    t_sec, hr = 30.0, 50.0
    tbh = float(temperature_bulbe_humide(t_sec, hr))
    hp = [float(pression_saturation_nh3(tbh + a)) - 1.01325 for a in approches]
    return pd.DataFrame({
        "TIMESTAMP": pd.date_range("2026-07-01", periods=n, freq="h"),
        "HP_COND_BAR": hp, "T_EXT_SEC_C": t_sec, "HR_EXT_PCT": hr,
        "P_PULV_BAR": p_pulv, "NIV_BAC_OK": defauts.get("niv", 1), "VFD_VENT_HZ": vfd,
        "DEF_VENT_DI": defauts.get("vent", 0), "DEF_POMPE_DI": defauts.get("pompe", 0),
        "P_ELEC_COMP_KW": 100.0, "P_ELEC_AUX_KW": 10.0, "Q0_FROID_KW": 400.0,
    })


P0 = Parametres()
REF = [3.0] * 48   # phase nominale : sert à l'étalonnage (décalage nul ici)


def test_indicateurs_cas_nominal():
    r = analyser(jeu([3.0] * 5), P0)
    d = r.donnees
    assert d["DT_APP_C"].to_numpy() == pytest.approx(3.0)
    assert (d["ETA_COND_PCT"] == 100).all()
    assert (d["SURCONSO_KW"] == 0).all()
    assert d["COP"].iloc[0] == pytest.approx(400 / 110)
    assert (d["NIVEAU"] == diag.NORMAL).all()


def test_surconsommation_regle_3_pct_par_degre():
    r = analyser(jeu(REF + [7.0]), P0)
    ligne = r.donnees.iloc[-1]
    assert ligne["SURCONSO_PCT"] == pytest.approx(12.0)              # 3 %/°C x 4 °C
    assert ligne["P_COMP_REF_KW"] == pytest.approx(100 / 1.12)
    assert ligne["COUT_H_DT"] == pytest.approx((100 - 100 / 1.12) * 0.340)
    assert ligne["ETA_COND_PCT"] == pytest.approx(100 * 3 / 7)


def test_etalonnage_automatique_retire_le_decalage():
    r = analyser(jeu([8.0] * 48 + [10.0]), P0)
    assert r.decalage_c == pytest.approx(5.0)
    assert r.donnees["DT_APP_C"].iloc[-1] == pytest.approx(5.0)


def test_alerte_maintenance_et_phases():
    r = analyser(jeu(REF + [5.0] * 72 + [7.0] * 48), P0)
    d = r.donnees
    assert d["PHASE"].tolist() == [1] * 48 + [2] * 72 + [3] * 48
    assert not d["ALERTE_MAINTENANCE"].iloc[:120].any()
    assert d["ALERTE_MAINTENANCE"].iloc[120:].all()


# ------------------------------------------------------------------ Arbre de diagnostic
P = Parametres()


@pytest.mark.parametrize("args, categorie", [
    (dict(dt_app=3.0, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=40, def_vent=0, def_pompe=0), diag.AUCUNE),
    (dict(dt_app=3.0, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=40, def_vent=0, def_pompe=1), diag.HYDRAULIQUE),
    (dict(dt_app=5.0, p_pulv_bar=1.85, niv_bac_ok=0, vfd_hz=50, def_vent=0, def_pompe=0), diag.HYDRAULIQUE),
    (dict(dt_app=5.0, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=50, def_vent=1, def_pompe=0), diag.AERAULIQUE),
    (dict(dt_app=6.5, p_pulv_bar=1.40, niv_bac_ok=1, vfd_hz=50, def_vent=0, def_pompe=0), diag.HYDRAULIQUE),
    (dict(dt_app=6.5, p_pulv_bar=2.30, niv_bac_ok=1, vfd_hz=50, def_vent=0, def_pompe=0), diag.HYDRAULIQUE),
    (dict(dt_app=6.5, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=32, def_vent=0, def_pompe=0), diag.AERAULIQUE),
    (dict(dt_app=5.0, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=45, def_vent=0, def_pompe=0), diag.ENTARTRAGE),
    (dict(dt_app=6.5, p_pulv_bar=1.85, niv_bac_ok=1, vfd_hz=50, def_vent=0, def_pompe=0), diag.ENTARTRAGE),
])
def test_arbre_de_decision(args, categorie):
    assert diag.diagnostiquer(**args, p=P).categorie == categorie


def test_niveaux_alerte():
    assert diag.niveau_alerte(4.49, P) == diag.NORMAL
    assert diag.niveau_alerte(4.5, P) == diag.ALERTE_LEGERE
    assert diag.niveau_alerte(6.0, P) == diag.ALERTE_GRAVE


# ------------------------------------------------------------------ Import
def test_import_csv_francais_avec_lignes_de_titre(tmp_path):
    df = jeu([3.0, 3.1])
    chemin = tmp_path / "mesures.csv"
    contenu = "Titre du fichier\n\n" + df.to_csv(index=False, sep=";", decimal=",", date_format="%d/%m/%Y %H:%M")
    chemin.write_text(contenu, encoding="cp1252")
    r = importer(chemin, chemin.name)
    assert r.valide, r.erreurs
    assert len(r.donnees) == 2
    assert r.donnees["HP_COND_BAR"].iloc[0] == pytest.approx(df["HP_COND_BAR"].iloc[0], abs=1e-6)
    assert r.donnees["TIMESTAMP"].iloc[1] == pd.Timestamp("2026-07-01 01:00")


def test_import_sans_entete_lit_par_position(tmp_path):
    chemin = tmp_path / "brut.xlsx"
    jeu([3.0, 3.0]).to_excel(chemin, index=False, header=False)
    r = importer(chemin, chemin.name)
    assert r.valide and any("En-tête non reconnu" in a for a in r.avertissements)


def test_import_colonne_manquante(tmp_path):
    chemin = tmp_path / "incomplet.xlsx"
    jeu([3.0]).drop(columns="Q0_FROID_KW").to_excel(chemin, index=False)
    r = importer(chemin, chemin.name)
    assert not r.valide and "Q0_FROID_KW" in r.erreurs[0]


@pytest.mark.skipif(not FICHIER_REEL.exists(), reason="fichier de simulation absent")
def test_fichier_de_simulation_168h():
    r = importer(FICHIER_REEL, FICHIER_REEL.name)
    assert r.valide and len(r.donnees) == 168
    res = analyser(r.donnees, Parametres())
    d = res.donnees
    assert d["DT_APP_C"].iloc[:48].mean() == pytest.approx(3.0)
    assert (d["NIVEAU"].iloc[:48] == diag.NORMAL).all()
    assert d["NIVEAU"].iloc[-1] == diag.ALERTE_GRAVE
    assert d["ALERTE_MAINTENANCE"].iloc[-1]


# ------------------------------------------------------------------ Stockage et Modbus
def test_depot_aller_retour(tmp_path):
    depot = Depot(tmp_path / "test.db")
    site = depot.creer_site("Usine A")
    m = depot.creer_machine(site.id, "Condenseur 1")
    m.parametres.tarif_kwh_dt = 0.5
    depot.enregistrer_machine(m)
    assert depot.machine(m.id).parametres.tarif_kwh_dt == 0.5

    df = jeu([3.0, 4.0, 5.0])
    assert depot.enregistrer_mesures(m.id, df) == 3
    relu = depot.mesures(m.id)
    pd.testing.assert_frame_equal(relu[NOMS], df[NOMS], check_dtype=False)
    depot.enregistrer_mesures(m.id, df.iloc[[0]])           # même horodatage : écrasé
    assert depot.nombre_mesures(m.id) == 3
    depot.supprimer_site(site.id)                            # suppression en cascade
    assert depot.nombre_mesures(m.id) == 0


def test_connecteurs_gtc_prets_mais_non_actifs():
    for type_source in ("modbus_tcp", "bacnet", "opc_ua"):
        with pytest.raises(ErreurSource):
            creer_source(type_source).lire_mesures()


def test_parametres_depuis_dict_tolere_les_cles_inconnues():
    p = Parametres.depuis_dict({"tarif_kwh_dt": "0.4", "seuil_alerte_grave_c": 9, "inconnu": 1})
    assert p.tarif_kwh_dt == 0.4 and p.seuil_alerte_grave_c == 6.0
    assert np.isclose(p.approche_nominale_c, 3.0)
