"""Synoptique SVG animé du condenseur évaporatif, piloté par les colonnes du scénario (§3).

- Ventilateur : vitesse proportionnelle à VFD_VENT_HZ ; arrêté et rouge si DEF_VENT_DI = 1.
- Rampe : débit des gouttes selon Q_PULV_M3H ; arrêtée si défaut pompe ou bac en alerte.
- Bac : niveau bas et rouge si NIV_BAC_OK = 0. Purge : animée selon Q_PURGE_LH.
- Serpentin du fluide : couleur selon le diagnostic, débit animé selon P_ELEC_COMP_KW.
"""
from __future__ import annotations

from vues.composants import fmt

TEINTES = {"ok": "var(--ok)", "attention": "var(--attention)", "critique": "var(--critique)",
           "aeraulique": "var(--aeraulique)"}


def _duree(reference: float, valeur: float, bas: float, haut: float) -> float:
    """Durée d'un cycle d'animation : plus la mesure est grande, plus c'est rapide."""
    return min(max(reference / max(valeur, 1e-6), bas), haut)


def synoptique(v: dict, fluide: str, etat: str, alertes: dict) -> str:
    """v : mesure + colonnes calculées ; alertes : {'pression', 'pulv', 'purge'} -> bool (hors nominal)."""
    couleur = TEINTES[etat]
    def_vent, def_pompe, bac_ok = int(v["DEF_VENT_DI"]), int(v["DEF_POMPE_DI"]), int(v["NIV_BAC_OK"])
    vfd, q_pulv, q_purge = float(v["VFD_VENT_HZ"]), float(v["Q_PULV_M3H"]), float(v["Q_PURGE_LH"])
    p_comp = float(v["P_ELEC_COMP_KW"])

    d_vent = 0 if def_vent or vfd <= 1 else _duree(25.0, vfd, 0.3, 4.0)
    arrosage = not def_pompe and bac_ok and q_pulv > 0.1
    d_eau = _duree(30.0, q_pulv, 0.4, 3.0) if arrosage else 0
    d_purge = _duree(150.0, q_purge, 0.3, 3.0) if q_purge > 0 else 0
    d_fluide = _duree(160.0, p_comp, 0.5, 4.0) if p_comp > 1 else 0
    d_pompe = 0.7 if arrosage else 0

    def anim(classe: str, duree: float) -> str:
        return f'class="{classe}" style="animation-duration:{duree:.2f}s"' if duree else ""

    def rot(duree: float) -> str:
        return f'class="tourne" style="transform-origin:0 0;animation-duration:{duree:.2f}s"' if duree else ""

    rouge, eau, marine = "var(--critique)", "var(--ciel)", "var(--marine)"
    c_vent = rouge if def_vent or vfd <= 1 else marine
    c_pompe = rouge if def_pompe else marine
    c_bac = rouge if not bac_ok else eau
    c_p = rouge if alertes["pression"] else "var(--texte)"
    c_q = rouge if alertes["pulv"] else "var(--texte)"
    c_purge = "var(--attention)" if alertes["purge"] else eau
    niveau_bac_y = 274 if bac_ok else 283

    lames = "".join(f'<path d="M0 0 C 4 -14 14 -22 26 -18 C 20 -10 10 -4 0 0z" transform="rotate({a})" '
                    f'fill="{c_vent}" fill-opacity="0.35" stroke="{c_vent}" stroke-width="1"/>' for a in (0, 120, 240))
    serpentin = ("M 200 150 H 440 Q 456 150 456 164 Q 456 178 440 178 H 200 Q 184 178 184 192 Q 184 206 200 206 H 440 "
                 "Q 456 206 456 220 Q 456 234 440 234 H 200")
    gouttes = "".join(
        f'<path d="M{x} 128 v34" stroke="{eau}" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="3 7" '
        f'opacity="{0.9 if arrosage else 0.15}" {anim("coule-v", d_eau)}/>' for x in range(210, 440, 24))

    def txt(x, y, s, taille=12, poids=500, fill="var(--texte)", classe=""):
        c = f' class="{classe}"' if classe else ""
        return (f'<text x="{x}" y="{y}" font-size="{taille}" font-weight="{poids}" fill="{fill}"{c} '
                f'font-family="Inter, Segoe UI, sans-serif">{s}</text>')

    gris = "var(--texte2)"
    pulse = "pulse" if etat in ("critique", "aeraulique") else ""
    svg = f"""
<svg viewBox="0 0 800 340" width="100%" role="img" aria-label="Synoptique animé du condenseur évaporatif">
  <rect x="150" y="96" width="340" height="190" rx="8" fill="var(--panneau2)" stroke="var(--bordure)" stroke-width="1.5"/>
  <rect x="150" y="262" width="340" height="24" rx="4" fill="{c_bac}" fill-opacity="0.15" stroke="{c_bac}" stroke-width="1"/>
  <path d="M 160 {niveau_bac_y} q 20 -6 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0" fill="none" stroke="{c_bac}" stroke-width="1.5" opacity="0.6" {anim("vague", 3.0)}/>
  <path d="{serpentin}" fill="none" stroke="{couleur}" stroke-width="5" stroke-linecap="round"/>
  <path d="{serpentin}" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-dasharray="4 16" opacity="0.9" {anim("coule-h", d_fluide)}/>
  {gouttes}
  <path d="M 170 120 H 470" stroke="{marine}" stroke-width="3"/>
  <g transform="translate(320 66)">
    <circle r="30" fill="var(--panneau)" stroke="{c_vent}" stroke-width="1.5"/>
    <g {rot(d_vent)}>{lames}</g>
    <circle r="3.5" fill="{marine}"/>
  </g>
  <path d="M 120 150 H 184" stroke="{couleur}" stroke-width="4" fill="none"/>
  <path d="M 200 234 H 120 V 280 H 90" stroke="{gris}" stroke-width="4" fill="none" stroke-linejoin="round"/>
  <path d="M 490 274 H 568" stroke="{eau}" stroke-width="3"/>
  <path d="M 590 250 V 120 H 470" stroke="{eau}" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <path d="M 590 250 V 120 H 470" stroke="#fff" stroke-width="1.5" fill="none" stroke-dasharray="6 12" opacity="0.9" {anim("coule-h", d_eau)}/>
  <circle cx="590" cy="274" r="22" fill="var(--panneau)" stroke="{c_pompe}" stroke-width="2"/>
  <g transform="translate(590 274)"><g {rot(d_pompe)}><path d="M0 0 L 12 -10" stroke="{c_pompe}" stroke-width="2.5" stroke-linecap="round"/><path d="M0 0 L -12 10" stroke="{c_pompe}" stroke-width="2.5" stroke-linecap="round" opacity="0.5"/></g></g>
  <path d="M 320 286 V 322 H 470" stroke="{c_purge}" stroke-width="3" fill="none"/>
  <path d="M 320 286 V 322 H 470" stroke="#fff" stroke-width="1.5" fill="none" stroke-dasharray="4 10" opacity="0.9" {anim("coule-h", d_purge)}/>
  {txt(22, 120, f"Vapeur {fluide} HP", 12, 500, gris)}
  {txt(22, 140, f"{fmt(v['HP_COND_BAR'], 2)} bar rel", 13, 700)}
  {txt(22, 188, "Compresseur", 11, 500, gris)}
  {txt(22, 206, f"{fmt(p_comp)} kW", 13, 700)}
  {txt(22, 224, f"Q0 {fmt(v['Q0_FROID_KW'], 0)} kW froid", 11, 400, gris)}
  {txt(22, 298, f"Liquide {fluide}", 12, 500, gris)}
  {txt(366, 52, "Ventilateur" + (" : DÉFAUT" if def_vent else ""), 11, 600, c_vent if def_vent else gris)}
  {txt(366, 72, f"{fmt(vfd)} Hz", 13, 700, c_vent if c_vent == rouge else "var(--texte)")}
  {txt(165, 256, "Bac d'eau" + (" : NIVEAU BAS" if not bac_ok else ""), 11, 600, c_bac if not bac_ok else gris)}
  {txt(620, 244, "Pompe" + (" : DÉFAUT" if def_pompe else ""), 11, 600, c_pompe if def_pompe else gris)}
  {txt(620, 266, f"{fmt(float(v['P_PULV_BAR']), 2)} bar", 13, 700, c_p)}
  {txt(620, 286, f"{fmt(q_pulv, 1)} m³/h", 13, 700, c_q)}
  {txt(480, 318, f"Purge {fmt(q_purge, 0)} L/h", 12, 700, c_purge if alertes["purge"] else "var(--texte)")}
  <g>
    {txt(620, 34, f"Tc  {fmt(v['TC_C'])} °C", 15, 700)}
    {txt(620, 58, f"ΔT_app  {fmt(v['DELTA_T_APP_C'], 2)} °C", 15, 700, couleur, pulse)}
    {txt(620, 82, f"T sèche  {fmt(v['T_EXT_SEC_C'])} °C", 12, 400, gris)}
    {txt(620, 100, f"HR  {fmt(v['HR_EXT_PCT'], 0)} %", 12, 400, gris)}
  </g>
</svg>"""
    return f'<div class="carte synoptique">{svg}</div>'
