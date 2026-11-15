# TUNIFROID · Suivi énergétique d'un condenseur évaporatif

Application Python (Streamlit + Plotly) réalisée dans le cadre du PPP2 (Université Centrale, Tunis)
en collaboration avec TUNIFROID. Elle lit les scénarios d'exploitation temps réel d'un condenseur
évaporatif, chiffre les surcoûts électriques (STEG) et d'eau (SONEDE) et diagnostique la cause
de la dérive de l'approche thermique par un arbre de décision.

## Lancer

Double-cliquer sur `lancer.bat`, ou :

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py      # http://localhost:8501
.venv\Scripts\python -m pytest -q                 # tests
```

Au premier lancement, l'application crée le site « TUNIFROID — Atelier de démonstration » et importe
les scénarios du dossier `donnees/` :

- **CE-01** (500 kW froid) : les 5 fichiers dédiés `Scenarios_Temps_Reel_*.xlsx` (24 mesures horaires) ;
- **CE-02** (150 kW froid) : le classeur `suivi_energetique_condenseur_6_scenarios.xlsx` (6 feuilles).

## Correspondance avec le cahier des charges

| § | Exigence | Réalisation |
|---|---|---|
| 1 | POO, bibliothèque de fluides modifiable (NH3, CO2, R404a, R134a), multi-sites | `condenseur/modeles.py`, `fluides.py` ; pages « Bibliothèque de fluides » et « Sites et machines » |
| 1 | 6 scénarios Excel | import multi-feuilles ; un scénario par fichier ou par feuille |
| 2 | Tarifs STEG 0,280 DT/kWh et SONEDE 1,250 DT/m³, pression et débits nominaux, VFD, seuils 3,0 / 4,5 / 6,0 / 8,5 °C | `parametres.py`, page « Paramètres de référence » (par machine) |
| 3 | Colonnes A à P | `tags.py`, `import_donnees.py` |
| 4 | Normalisation selon Q0 | P_ref = P_comp_ref × Q0 / Q0_ref |
| 4 | Double affichage financier | STEG = max(0, P_comp − P_ref) × tarif ; SONEDE = max(0, Q_purge − Q_purge_nom) / 1000 × tarif |
| 4.1 | Arbre de décision (6 branches) | `diagnostic.py`, page « Diagnostic » |
| 5 | Graphique unique ΔT_app en fonction du temps | tableau de bord, avec superposition d'autres scénarios pour comparer les cinétiques |

## Choix de modélisation

- **Tc** : équation d'Antoine du fluide de la machine (NH3 : coefficients NIST ; autres fluides :
  ajustement sur les tables de saturation), HP relative + 1,01325 bar.
- **Écart toléré** : ±10 % autour des valeurs nominales de pression et de débits avant de signaler
  une chute, un débit faible ou une purge excessive.
- **Dérive brutale ou lente** : une chute de P_pulv coupe l'arrosage et fait monter ΔT_app
  brutalement ; à P_pulv normale la dérive est lente. La branche « entartrage » exige
  ΔT_app ≥ seuil d'alerte légère.
- Les colonnes O et P des fichiers sont conservées ; l'application recalcule les surcoûts avec les
  tarifs saisis. Sur les fichiers fournis, les deux calculs concordent.

## Organisation

```
app.py                     point d'entrée Streamlit (navigation)
condenseur/                moteur, sans dépendance à l'interface
  fluides.py               bibliothèque de fluides (Antoine)
  parametres.py            paramètres de référence (§2)
  tags.py                  dictionnaire des données (§3)
  moteur.py                normalisation Q0, surcoûts STEG / SONEDE, niveaux, diagnostic
  diagnostic.py            arbre de décision (§4.1)
  import_donnees.py        import .xlsx (multi-feuilles) / .csv
  modeles.py               classes Site, Machine, Scenario
  stockage.py              persistance SQLite (donnees/condenseur.db)
  demo.py                  chargement initial des scénarios fournis
vues/                      pages Streamlit aux couleurs de TUNIFROID
donnees/                   scénarios Excel
tests/                     tests pytest
```
