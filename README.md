# Suivi énergétique d'un condenseur évaporatif (NH3 / R717)

Application Python (Streamlit + Plotly) qui importe les mesures horaires d'une installation
frigorifique, calcule l'approche thermique du condenseur évaporatif, chiffre la surconsommation
en dinars et diagnostique la cause de la dégradation (hydraulique, aéraulique, entartrage).

## Lancer

Double-cliquer sur `lancer.bat`, ou :

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py      # http://localhost:8501
.venv\Scripts\python -m pytest -q                 # tests
```

Au premier lancement, un site et une machine sont créés. Importer ensuite
`Simulation_Condenseur_7_Jours_168h.xlsx` depuis la page « Import de données ».

## Organisation

```
app.py                     point d'entrée Streamlit (navigation)
condenseur/                moteur, sans dépendance à l'interface
  parametres.py            paramètres de référence d'une machine (§2 du cahier des charges)
  tags.py                  dictionnaire des tags GTC (§4)
  thermo.py                Antoine inverse R717, bulbe humide de Stull (§5)
  moteur.py                calcul horaire : ΔTapp, ηcond, COP, surconsommation, coûts, alertes
  diagnostic.py            arbre de décision (hydraulique / aéraulique / entartrage)
  import_donnees.py        import .xlsx / .csv avec contrôles (§3)
  modeles.py               classes Site et Machine (POO, multi-machines)
  stockage.py              persistance SQLite (donnees/condenseur.db)
  sources/                 mode industriel : interface SourceDonnees, Modbus TCP,
                           BACnet et OPC UA (mode industriel futur)
vues/                      pages Streamlit (thème, cartes, jauges, synoptique animé)
tests/                     tests pytest
```

## Choix de modélisation

- **Tc** : équation d'Antoine du NH3 (NIST : A = 4,86886 ; B = 1113,928 ; C = −10,409 ;
  P en bar absolu, T en K), inversée. HP relative + 1,01325 bar.
- **Tbh** : formule de Stull (2011).
- **Étalonnage** : avec la vraie loi d'Antoine, le fichier de simulation fournit ΔTapp ≈ 8,4 °C
  en phase propre, au lieu de 3,0 °C : il y a un décalage constant d'environ 5,46 °C (la pente
  HP/Tc est pourtant correcte). L'application retire ce décalage, calculé sur la période de
  référence H1 à H48 (phase nominale). On obtient alors ΔTapp ≈ 3,0 °C en phase 1,
  de 3 à 5,1 °C en phase 2 et de 5,4 à 6,75 °C en phase 3. La puissance compresseur mesurée
  (+10,5 %) concorde avec la règle des 3 %/°C (+11,3 %).
- **ηcond** = ΔTnom / ΔTapp, plafonné à 100 %. **COP** = Q0 / (P_comp + P_aux).
- **Surconsommation** : +3 % de puissance compresseur par °C d'approche au-dessus de ΔTnom
  (constante du modèle). P_ref = P_comp / (1 + s), surconsommation = P_comp − P_ref,
  coût horaire = surconsommation × 1 h × tarif, cumulé en dinars.
- **Alertes** (§3) : légère à partir de 4,5 °C, grave à partir de 6,0 °C ; l'alerte grave déclenche
  l'alerte de maintenance préventive. Seuls les paramètres du §2 sont modifiables dans l'interface. Sur le fichier fourni, l'alerte légère arrive
  à H85 et l'alerte grave à H131 (encrassement progressif).

## Interface

- **Santé et surcoûts** : indicateurs globaux (ΔTapp, ηcond, COP, surconsommation, coût horaire),
  jauges, synoptique animé, surcoût cumulé en DT, évolution sur les 3 phases.
- **Diagnostic ciblé** : cause (hydraulique, aéraulique, entartrage), grandeurs croisées par l'arbre.
- **Import de données** (§3, §4), **Paramètres de référence** (§2), **Sites et machines** (§1).

## Mode industriel (futur)

Conformément au §1, l'architecture est prête pour une connexion temps réel : `condenseur/sources/`
définit l'interface `SourceDonnees` et les classes Modbus TCP, BACnet/IP et OPC UA à compléter.
