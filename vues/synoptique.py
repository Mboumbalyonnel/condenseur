"""Synoptique SVG animé du condenseur évaporatif, piloté par les tags GTC du cahier des charges.

- Ventilateur : vitesse de rotation proportionnelle à VFD_VENT_HZ ; arrêté et rouge si DEF_VENT_DI.
- Rampe d'eau : vitesse des gouttes selon P_PULV_BAR ; arrêtée si défaut pompe ou bac vide.
- Bac : niveau bas et rouge si NIV_BAC_OK = 0.
- Serpentin NH3 : couleur selon le niveau d'alerte, débit animé selon P_ELEC_COMP_KW.
"""
from __future__ import annotations

from vues.composants import fmt


def _duree(reference: float, valeur: float, bas: float, haut: float) -> float:
    """Durée d'un cycle d'animation : plus la mesure est grande, plus c'est rapide."""
    return min(max(reference / max(valeur, 1e-6), bas), haut)


def synoptique(v: dict) -> str:
    """v : ligne de résultats du moteur (dict) + 'etat' (ok|attention|critique) + 'etat_pression'."""
    etat = v.get("etat", "ok")
    couleur = {"ok": "var(--ok)", "attention": "var(--attention)", "critique": "var(--critique)"}[etat]
    def_vent, def_pompe, bac_ok = int(v["DEF_VENT_DI"]), int(v["DEF_POMPE_DI"]), int(v["NIV_BAC_OK"])
    vfd, p_pulv, p_comp = float(v["VFD_VENT_HZ"]), float(v["P_PULV_BAR"]), float(v["P_ELEC_COMP_KW"])

    d_vent = 0 if def_vent or vfd <= 1 else _duree(25.0, vfd, 0.3, 4.0)
    arrosage = not def_pompe and bac_ok and p_pulv > 0.1
    d_eau = _duree(1.6, p_pulv, 0.4, 3.0) if arrosage else 0
    d_fluide = _duree(160.0, p_comp, 0.5, 4.0) if p_comp > 1 else 0
    d_pompe = 0.7 if arrosage else 0

    def anim(classe: str, duree: float) -> str:
        return f'class="{classe}" style="animation-duration:{duree:.2f}s"' if duree else ""

    def rot(duree: float) -> str:
        return f'class="tourne" style="transform-origin:0 0;animation-duration:{duree:.2f}s"' if duree else ""

    c_vent = "var(--critique)" if def_vent else "var(--accent)"
    c_pompe = "var(--critique)" if def_pompe else "var(--accent)"
    c_bac = "var(--critique)" if not bac_ok else "var(--accent)"
    c_pression = {"ok": "var(--texte)", "attention": "var(--attention)", "critique": "var(--critique)"}[v.get("etat_pression", "ok")]
    niveau_bac_y = 274 if bac_ok else 282

    lames = "".join(f'<path d="M0 0 C 4 -14 14 -22 26 -18 C 20 -10 10 -4 0 0z" transform="rotate({a})" '
                    f'fill="{c_vent}" fill-opacity="0.45" stroke="{c_vent}" stroke-width="1"/>' for a in (0, 120, 240))
    serpentin = ("M 200 150 H 440 Q 456 150 456 164 Q 456 178 440 178 H 200 Q 184 178 184 192 Q 184 206 200 206 H 440 "
                 "Q 456 206 456 220 Q 456 234 440 234 H 200")
    gouttes = "".join(
        f'<path d="M{x} 128 v34" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="3 7" '
        f'opacity="{0.9 if arrosage else 0.2}" {anim("coule-v", d_eau)}/>' for x in range(210, 440, 24))

    def txt(x, y, s, taille=12, poids=500, ancre="start", fill="var(--texte)", classe=""):
        c = f' class="{classe}"' if classe else ""
        return (f'<text x="{x}" y="{y}" font-size="{taille}" font-weight="{poids}" text-anchor="{ancre}" fill="{fill}"{c} '
                f'font-family="IBM Plex Sans, Segoe UI, sans-serif">{s}</text>')

    pulse = "pulse" if etat == "critique" else ""
    svg = f"""
<svg viewBox="0 0 800 330" width="100%" role="img" aria-label="Synoptique animé du condenseur évaporatif">
  <rect x="150" y="96" width="340" height="190" rx="6" fill="var(--panneau2)" stroke="var(--bordure)" stroke-width="1.5"/>
  <rect x="150" y="262" width="340" height="24" rx="4" fill="{c_bac}" fill-opacity="0.18" stroke="{c_bac}" stroke-width="1"/>
  <path d="M 160 {niveau_bac_y} q 20 -6 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0 t 40 0" fill="none" stroke="{c_bac}" stroke-width="1.5" opacity="0.6" {anim("vague", 3.0)}/>
  <path d="{serpentin}" fill="none" stroke="{couleur}" stroke-width="5" stroke-linecap="round"/>
  <path d="{serpentin}" fill="none" stroke="var(--texte)" stroke-width="2" stroke-linecap="round" stroke-dasharray="4 16" opacity="0.8" {anim("coule-h", d_fluide)}/>
  {gouttes}
  <path d="M 170 120 H 470" stroke="var(--texte2)" stroke-width="3"/>
  <g transform="translate(320 66)">
    <circle r="30" fill="var(--panneau)" stroke="{c_vent}" stroke-width="1.5"/>
    <g {rot(d_vent)}>{lames}</g>
    <circle r="3.5" fill="var(--texte)"/>
  </g>
  <path d="M 120 150 H 184" stroke="{couleur}" stroke-width="4" fill="none"/>
  <path d="M 200 234 H 120 V 280 H 90" stroke="var(--texte2)" stroke-width="4" fill="none" stroke-linejoin="round"/>
  <path d="M 520 272 H 568" stroke="var(--accent)" stroke-width="3"/>
  <path d="M 590 250 V 120 H 470" stroke="var(--accent)" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <path d="M 590 250 V 120 H 470" stroke="var(--bg)" stroke-width="1.5" fill="none" stroke-linejoin="round" stroke-dasharray="6 12" opacity="0.9" {anim("coule-h", d_eau)}/>
  <circle cx="590" cy="272" r="22" fill="var(--panneau)" stroke="{c_pompe}" stroke-width="2"/>
  <g transform="translate(590 272)"><g {rot(d_pompe)}><path d="M0 0 L 12 -10" stroke="{c_pompe}" stroke-width="2.5" stroke-linecap="round"/><path d="M0 0 L -12 10" stroke="{c_pompe}" stroke-width="2.5" stroke-linecap="round" opacity="0.5"/></g></g>
  {txt(22, 120, "Vapeur NH3 HP", 12, 500, "start", "var(--texte2)")}
  {txt(22, 140, f"{fmt(v['HP_COND_BAR'], 2)} bar rel", 13, 600)}
  {txt(22, 188, "Compresseur", 11, 500, "start", "var(--texte2)")}
  {txt(22, 206, f"{fmt(p_comp)} kW", 13, 600)}
  {txt(22, 224, f"Froid {fmt(v['Q0_FROID_KW'], 0)} kW", 11, 400, "start", "var(--texte2)")}
  {txt(22, 298, "Liquide NH3", 12, 500, "start", "var(--texte2)")}
  {txt(366, 52, "Ventilateur" + (" : DÉFAUT" if def_vent else ""), 11, 500, "start", c_vent if def_vent else "var(--texte2)")}
  {txt(366, 72, f"{fmt(vfd)} Hz", 13, 600)}
  {txt(165, 255, "Bac d'eau" + (" : NIVEAU BAS" if not bac_ok else ""), 11, 500, "start", c_bac if not bac_ok else "var(--texte2)")}
  {txt(620, 256, "Pompe" + (" : DÉFAUT" if def_pompe else ""), 11, 500, "start", c_pompe if def_pompe else "var(--texte2)")}
  {txt(620, 276, f"{fmt(p_pulv, 2)} bar", 13, 600, "start", c_pression)}
  {txt(620, 294, f"Aux. {fmt(v['P_ELEC_AUX_KW'])} kW", 11, 400, "start", "var(--texte2)")}
  <g>
    {txt(620, 34, f"Tc  {fmt(v['TC_C'])} °C", 15, 600, "start", "var(--texte)")}
    {txt(620, 58, f"ΔTapp  {fmt(v['DT_APP_C'], 2)} °C", 15, 600, "start", couleur, pulse)}
    {txt(620, 82, f"ηcond  {fmt(v['ETA_COND_PCT'], 0)} %", 13, 500, "start", couleur)}
    {txt(620, 104, f"Tbh  {fmt(v['TBH_C'])} °C", 12, 400, "start", "var(--texte2)")}
    {txt(620, 124, f"Tsec  {fmt(v['T_EXT_SEC_C'])} °C  HR {fmt(v['HR_EXT_PCT'], 0)} %", 12, 400, "start", "var(--texte2)")}
  </g>
</svg>"""
    return f'<div class="synoptique">{svg}</div>'
