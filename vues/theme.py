"""Charte TUNIFROID : bleu marine et rouge du logo, surfaces blanches. Variables CSS + gabarit Plotly."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).parent / "logo_tunifroid.png"

COULEURS = {
    "bg": "#F2F5F9", "panneau": "#FFFFFF", "panneau2": "#EDF2F7", "bordure": "#D5DEE8",
    "texte": "#0E2236", "texte2": "#5A6B7E",
    "marine": "#0A365C", "marine2": "#164B7A", "rouge": "#DE0C15", "ciel": "#2E86C1",
    "ok": "#1E9E6A", "attention": "#E08A00", "critique": "#C8141B", "aeraulique": "#6A4BC4",
    "grille": "#E3E9F0",
}


def couleurs() -> dict:
    return COULEURS


def appliquer() -> None:
    c = COULEURS
    variables = "".join(f"--{k}:{v};" for k, v in c.items())
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {{ {variables} --accent:var(--marine); }}
html, body, .stApp, [class*="css"] {{ font-family:'Inter','Segoe UI',system-ui,sans-serif; }}
.stApp {{ background:var(--bg); color:var(--texte); }}
[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:1.4rem; max-width:1480px; }}

/* Barre latérale marine */
[data-testid="stSidebar"] {{ background:linear-gradient(180deg, var(--marine) 0%, #072845 100%); border-right:none; }}
[data-testid="stSidebar"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:4px; background:var(--rouge); }}
[data-testid="stSidebar"] * {{ color:#E6EEF6; }}
[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{ border-color:rgba(255,255,255,.15); }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{ border-radius:8px; }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {{ background:rgba(255,255,255,.08); }}
[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{ background:rgba(255,255,255,.14);
  box-shadow:inset 3px 0 0 var(--rouge); }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] {{ background:#fff; border-color:transparent; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] input, [data-testid="stSidebar"] [data-testid="stSelectbox"] button {{
  color:var(--texte) !important; -webkit-text-fill-color:var(--texte); font-weight:500; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {{ color:#B9CBDD; font-size:.8rem; }}
[data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,.15); }}
[data-testid="stSidebarHeader"] {{ height:auto; padding-top:1.2rem; }}
[data-testid="stSidebarHeader"] img[data-testid="stSidebarLogo"], [data-testid="stSidebarHeader"] img {{
  height:auto !important; max-height:none; width:170px; background:#fff; border-radius:12px; padding:.45rem .8rem;
  box-shadow:0 6px 18px rgba(0,0,0,.3); }}
.marque-sous {{ font-size:.8rem; color:#B9CBDD !important; margin:-.4rem 0 .4rem 0; }}

/* Contenu */
.stApp .stButton > button, .stApp [data-testid="stFormSubmitButton"] > button {{ border-radius:8px; }}
.stApp [data-testid="stForm"], .stApp [data-testid="stExpander"] details {{ background:var(--panneau); border-color:var(--bordure); border-radius:12px; }}
.ic {{ vertical-align:-0.2em; flex:none; }}
.entete {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:0 0 1.1rem 0; padding-bottom:.8rem;
  border-bottom:1px solid var(--bordure); position:relative; }}
.entete::after {{ content:""; position:absolute; left:0; bottom:-1px; width:72px; height:3px; background:var(--rouge); border-radius:2px; }}
.titre-page {{ display:flex; align-items:center; gap:.7rem; font-size:1.55rem; font-weight:700; color:var(--marine); }}
.titre-page .ic {{ color:var(--rouge); }}
.sous-titre {{ color:var(--texte2); font-size:.93rem; margin-top:.15rem; }}
.pastille-entete {{ display:inline-flex; align-items:center; gap:.45rem; background:var(--panneau); border:1px solid var(--bordure);
  border-radius:999px; padding:.3rem .8rem; font-size:.82rem; color:var(--texte2); white-space:nowrap; }}
.pastille-entete b {{ color:var(--marine); }}
.section {{ display:flex; align-items:center; gap:.5rem; font-weight:700; font-size:1.02rem; margin:1.4rem 0 .6rem 0; color:var(--marine); }}
.section .ic {{ color:var(--ciel); }}
.etat-ok {{ --etat:var(--ok); }} .etat-attention {{ --etat:var(--attention); }} .etat-critique {{ --etat:var(--critique); }}
.etat-aeraulique {{ --etat:var(--aeraulique); }} .etat-neutre {{ --etat:var(--marine); }}

.kpi {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:14px; padding:.95rem 1.05rem; height:100%;
  box-shadow:0 1px 2px rgba(10,54,92,.05); position:relative; overflow:hidden; }}
.kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--etat,var(--marine)); }}
.kpi .lib {{ display:flex; align-items:center; gap:.45rem; color:var(--texte2); font-size:.83rem; font-weight:500; }}
.kpi .lib .ic {{ color:var(--etat,var(--marine)); }}
.kpi .val {{ font-size:1.85rem; font-weight:700; font-variant-numeric:tabular-nums; line-height:1.3; color:var(--texte); }}
.kpi .val small {{ font-size:.9rem; font-weight:500; color:var(--texte2); margin-left:.25rem; }}
.kpi .sub {{ color:var(--texte2); font-size:.8rem; }}

.hero {{ display:grid; grid-template-columns:1.25fr 1.6fr 1fr; gap:1.5rem; align-items:center; color:#fff;
  background:radial-gradient(120% 140% at 0% 0%, var(--marine2) 0%, var(--marine) 45%, #061f36 100%);
  border-radius:18px; padding:1.3rem 1.6rem; margin-bottom:1rem; position:relative; overflow:hidden;
  box-shadow:0 10px 30px rgba(10,54,92,.25); }}
.hero::after {{ content:""; position:absolute; right:-60px; top:-60px; width:220px; height:220px; border-radius:50%;
  border:28px solid rgba(255,255,255,.04); }}
.hero .lib {{ font-size:.8rem; color:#B9CBDD; display:flex; gap:.4rem; align-items:center; text-transform:none; }}
.hero .grand {{ font-size:1.6rem; font-weight:700; line-height:1.2; display:flex; align-items:center; gap:.6rem; margin-top:.2rem; color:#fff; }}
.hero .grand i {{ width:.85rem; height:.85rem; border-radius:50%; background:var(--etat); flex:none;
  box-shadow:0 0 0 0 var(--etat); animation: halo 1.8s ease-out infinite; }}
.hero .sub {{ color:#B9CBDD; font-size:.84rem; margin-top:.35rem; }}
.hero .badge {{ display:inline-block; margin-top:.55rem; padding:.18rem .65rem; border-radius:999px; font-size:.78rem; font-weight:600;
  background:var(--etat); color:#fff; }}
.hero .chiffre {{ font-size:2.4rem; font-weight:700; font-variant-numeric:tabular-nums; line-height:1.1; color:#fff; }}
.hero .chiffre small {{ font-size:1rem; color:#B9CBDD; margin-left:.3rem; font-weight:500; }}
@keyframes halo {{ 0% {{ box-shadow:0 0 0 0 color-mix(in srgb, var(--etat) 80%, transparent); }} 100% {{ box-shadow:0 0 0 13px transparent; }} }}

.echelle .val {{ font-size:2.3rem; font-weight:700; font-variant-numeric:tabular-nums; color:#fff; line-height:1.1; }}
.echelle .val small {{ font-size:1rem; color:#B9CBDD; margin-left:.3rem; font-weight:500; }}
.echelle .piste {{ position:relative; display:flex; height:12px; border-radius:6px; overflow:hidden; margin-top:.7rem; }}
.echelle .piste span {{ height:100%; }}
.echelle .curseur {{ position:absolute; top:-6px; width:4px; height:24px; background:#fff; border-radius:2px;
  box-shadow:0 0 0 2px var(--marine), 0 0 12px rgba(255,255,255,.8); transition:left .6s; }}
.echelle .graduations {{ position:relative; height:1.1rem; margin-top:.3rem; font-size:.72rem; color:#B9CBDD; }}
.echelle .graduations b {{ position:absolute; transform:translateX(-50%); font-weight:500; }}

.finance {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.facture {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:16px; padding:1.1rem 1.3rem;
  display:grid; grid-template-columns:auto 1fr auto; gap:1rem; align-items:center; box-shadow:0 1px 2px rgba(10,54,92,.05); }}
.facture .pictogramme {{ width:54px; height:54px; border-radius:14px; display:grid; place-items:center;
  background:color-mix(in srgb, var(--teinte) 12%, #fff); color:var(--teinte); }}
.facture .t {{ font-weight:700; color:var(--marine); }}
.facture .d {{ color:var(--texte2); font-size:.82rem; margin-top:.15rem; }}
.facture .montant {{ text-align:right; font-size:2rem; font-weight:700; font-variant-numeric:tabular-nums; color:var(--teinte); line-height:1.1; }}
.facture .montant small {{ display:block; font-size:.8rem; color:var(--texte2); font-weight:500; }}

.alerte {{ display:flex; gap:.8rem; align-items:flex-start; background:var(--panneau); border:1px solid var(--bordure);
  border-left:4px solid var(--etat); border-radius:12px; padding:.8rem 1rem; margin-bottom:.6rem; }}
.alerte .ic {{ color:var(--etat); margin-top:.1rem; }}
.alerte b {{ color:var(--texte); }} .alerte span.d {{ color:var(--texte2); font-size:.88rem; display:block; }}
.voyant {{ display:inline-flex; align-items:center; gap:.45rem; padding:.22rem .7rem; border-radius:999px;
  background:color-mix(in srgb, var(--etat) 10%, #fff); color:var(--etat); font-size:.8rem; font-weight:600; }}
.voyant i {{ width:.5rem; height:.5rem; border-radius:50%; background:var(--etat); display:inline-block; }}
.note {{ color:var(--texte2); font-size:.83rem; display:flex; gap:.45rem; align-items:flex-start; margin:.2rem 0; }}
.carte {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:16px; padding:.6rem; }}

.grandeurs {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem; }}
.grandeur {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:12px; padding:.7rem .85rem; }}
.grandeur .n {{ font-size:.75rem; color:var(--texte2); font-weight:600; }}
.grandeur .v {{ font-size:1.25rem; font-weight:700; color:var(--texte); font-variant-numeric:tabular-nums; margin:.1rem 0 .35rem 0; }}
.grandeur .v small {{ font-size:.8rem; color:var(--texte2); font-weight:500; margin-left:.2rem; }}
.grandeur .r {{ font-size:.75rem; color:var(--texte2); margin-top:.35rem; }}

.arbre .actif {{ animation: pulse 1.6s ease-in-out infinite; }}
@keyframes pulse {{ 50% {{ opacity:.55; }} }}
@keyframes tourne {{ to {{ transform: rotate(360deg); }} }}
@keyframes coule-v {{ to {{ stroke-dashoffset: -20; }} }}
@keyframes coule-h {{ to {{ stroke-dashoffset: -32; }} }}
@keyframes vague {{ 50% {{ transform: translateX(-12px); }} }}
.synoptique .tourne {{ animation: tourne 2s linear infinite; }}
.synoptique .coule-v {{ animation: coule-v 1s linear infinite; }}
.synoptique .coule-h {{ animation: coule-h 1.5s linear infinite; }}
.synoptique .vague {{ animation: vague 3s ease-in-out infinite; }}
.synoptique .pulse {{ animation: pulse 1.2s ease-in-out infinite; }}
@media (max-width: 1000px) {{ .hero, .finance {{ grid-template-columns:1fr; }} .grandeurs {{ grid-template-columns:repeat(2,1fr); }}
  .entete {{ flex-direction:column; align-items:flex-start; }} }}
@media (prefers-reduced-motion: reduce) {{ .synoptique *, .hero i, .arbre * {{ animation:none !important; }} }}
</style>""", unsafe_allow_html=True)


def gabarit_plotly(hauteur: int = 360) -> dict:
    c = COULEURS
    return dict(
        height=hauteur, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=c["texte"], size=12),
        xaxis=dict(gridcolor=c["grille"], zerolinecolor=c["grille"], linecolor=c["bordure"]),
        yaxis=dict(gridcolor=c["grille"], zerolinecolor=c["grille"], linecolor=c["bordure"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#fff", font_color=c["texte"], bordercolor=c["bordure"]),
        hovermode="x unified", separators=", ",
    )
