"""Thèmes sombre « salle de contrôle » et clair : variables CSS + gabarit Plotly cohérent."""
from __future__ import annotations

import streamlit as st

THEMES = {
    "sombre": {
        "bg": "#0F151B", "panneau": "#17202A", "panneau2": "#1D2833", "bordure": "#2A3846",
        "texte": "#E4EAF0", "texte2": "#8FA1B3", "accent": "#33C2D6",
        "ok": "#3FBF8A", "attention": "#F0A23B", "critique": "#EF5B5B", "grille": "#26323E",
    },
    "clair": {
        "bg": "#F3F5F8", "panneau": "#FFFFFF", "panneau2": "#EAEEF3", "bordure": "#D3DAE3",
        "texte": "#1B2631", "texte2": "#5B6B7C", "accent": "#0B8FA3",
        "ok": "#1F9D6B", "attention": "#C77A0E", "critique": "#D23C3C", "grille": "#DDE3EA",
    },
}


def theme_courant() -> str:
    return st.session_state.get("theme", "sombre")


def couleurs(theme: str | None = None) -> dict:
    return THEMES.get(theme or theme_courant(), THEMES["sombre"])


def appliquer(theme: str) -> None:
    c = couleurs(theme)
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root {{ --bg:{c['bg']}; --panneau:{c['panneau']}; --panneau2:{c['panneau2']}; --bordure:{c['bordure']};
  --texte:{c['texte']}; --texte2:{c['texte2']}; --accent:{c['accent']}; --ok:{c['ok']};
  --attention:{c['attention']}; --critique:{c['critique']}; }}
html, body, .stApp, [class*="css"] {{ font-family:'IBM Plex Sans','Segoe UI',system-ui,sans-serif; }}
.stApp {{ background:var(--bg); color:var(--texte); }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"] {{ background:var(--panneau); border-right:1px solid var(--bordure); }}
.stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{ color:var(--texte); }}
.stApp [data-baseweb="select"] > div, .stApp input, .stApp textarea {{ background:var(--panneau2) !important; color:var(--texte) !important; border-color:var(--bordure) !important; }}
.stApp .stButton > button, .stApp .stDownloadButton > button, .stApp [data-testid="stFormSubmitButton"] > button {{ background:var(--panneau2); color:var(--texte); border:1px solid var(--bordure); border-radius:6px; }}
.stApp .stButton > button:hover, .stApp .stDownloadButton > button:hover, .stApp [data-testid="stFormSubmitButton"] > button:hover {{ border-color:var(--accent); color:var(--accent); }}
.stApp [data-testid="stForm"], .stApp [data-testid="stExpander"] details {{ background:var(--panneau); border-color:var(--bordure); }}
.stApp [data-testid="stFileUploaderDropzone"] {{ background:var(--panneau); border:1px dashed var(--bordure); }}
.block-container {{ padding-top:1.6rem; max-width:1500px; }}
.ic {{ vertical-align:-0.2em; flex:none; }}
.titre-page {{ display:flex; align-items:center; gap:.7rem; font-size:1.55rem; font-weight:600; margin:0 0 .2rem 0; color:var(--texte); }}
.titre-page .ic {{ color:var(--accent); }}
.sous-titre {{ color:var(--texte2); margin:0 0 1.2rem 0; font-size:.95rem; }}
.section {{ display:flex; align-items:center; gap:.5rem; font-weight:600; font-size:1.02rem; margin:1.2rem 0 .5rem 0; color:var(--texte); }}
.section .ic {{ color:var(--texte2); }}
.kpi {{ background:var(--panneau); border:1px solid var(--bordure); border-left:3px solid var(--etat,var(--accent));
  border-radius:8px; padding:.85rem 1rem; height:100%; }}
.kpi .lib {{ display:flex; align-items:center; gap:.45rem; color:var(--texte2); font-size:.84rem; }}
.kpi .val {{ font-size:1.9rem; font-weight:600; font-variant-numeric:tabular-nums; line-height:1.25; color:var(--texte); }}
.kpi .val small {{ font-size:.9rem; font-weight:400; color:var(--texte2); margin-left:.25rem; }}
.kpi .sub {{ color:var(--texte2); font-size:.8rem; }}
.kpi .lib .ic {{ color:var(--etat,var(--accent)); }}
.etat-ok {{ --etat:var(--ok); }} .etat-attention {{ --etat:var(--attention); }} .etat-critique {{ --etat:var(--critique); }}
.etat-neutre {{ --etat:var(--accent); }}
.compteur {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:10px; padding:1.1rem 1.3rem; height:100%; }}
.compteur .val {{ font-size:3rem; font-weight:600; font-variant-numeric:tabular-nums; color:var(--critique); line-height:1.1; }}
.compteur .val small {{ font-size:1.1rem; color:var(--texte2); margin-left:.4rem; }}
.compteur .lib {{ color:var(--texte2); font-size:.9rem; display:flex; gap:.45rem; align-items:center; }}
.compteur .sub {{ color:var(--texte2); font-size:.85rem; margin-top:.3rem; }}
.alerte {{ display:flex; gap:.75rem; align-items:flex-start; background:var(--panneau); border:1px solid var(--bordure);
  border-left:3px solid var(--etat); border-radius:8px; padding:.7rem .9rem; margin-bottom:.5rem; }}
.alerte .ic {{ color:var(--etat); margin-top:.1rem; }}
.alerte b {{ color:var(--texte); }} .alerte span.d {{ color:var(--texte2); font-size:.88rem; display:block; }}
.voyant {{ display:inline-flex; align-items:center; gap:.45rem; padding:.2rem .65rem; border-radius:999px;
  border:1px solid var(--etat); color:var(--etat); font-size:.82rem; font-weight:500; margin:0 .4rem .4rem 0; }}
.voyant i {{ width:.55rem; height:.55rem; border-radius:50%; background:var(--etat); display:inline-block; }}
.note {{ color:var(--texte2); font-size:.84rem; display:flex; gap:.45rem; align-items:flex-start; margin:.15rem 0; }}
.synoptique {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:10px; padding:.4rem; }}
.marque {{ display:flex; align-items:center; gap:.6rem; font-weight:600; font-size:1.05rem; color:var(--texte); }}
.marque .ic {{ color:var(--accent); }}
.phases {{ display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; }}
.phase {{ background:var(--panneau); border:1px solid var(--bordure); border-top:3px solid var(--etat); border-radius:8px; padding:.8rem 1rem; }}
.phase .t {{ font-weight:600; color:var(--texte); }} .phase .h {{ color:var(--texte2); font-size:.82rem; margin-bottom:.5rem; }}
.phase table {{ width:100%; border-collapse:collapse; font-size:.86rem; }}
.phase td {{ padding:.18rem 0; color:var(--texte2); border:none; }}
.phase td.v {{ text-align:right; color:var(--texte); font-variant-numeric:tabular-nums; font-weight:500; }}
@media (max-width: 900px) {{ .phases {{ grid-template-columns:1fr; }} }}
.hero {{ display:grid; grid-template-columns:1.1fr 2fr 1fr; gap:1.2rem; align-items:center; background:
  linear-gradient(120deg, color-mix(in srgb, var(--etat) 16%, var(--panneau)) 0%, var(--panneau) 55%);
  border:1px solid var(--bordure); border-left:4px solid var(--etat); border-radius:12px; padding:1.1rem 1.4rem; margin-bottom:1rem; }}
.hero .lib {{ color:var(--texte2); font-size:.82rem; display:flex; gap:.4rem; align-items:center; }}
.hero .grand {{ font-size:1.7rem; font-weight:600; color:var(--etat); line-height:1.2; display:flex; align-items:center; gap:.55rem; }}
.hero .grand i {{ width:.8rem; height:.8rem; border-radius:50%; background:var(--etat); display:inline-block;
  box-shadow:0 0 0 0 var(--etat); animation: halo 1.8s ease-out infinite; }}
.hero .sub {{ color:var(--texte2); font-size:.85rem; margin-top:.2rem; }}
.hero .chiffre {{ font-size:2.3rem; font-weight:600; font-variant-numeric:tabular-nums; color:var(--texte); line-height:1.1; }}
.hero .chiffre small {{ font-size:1rem; color:var(--texte2); margin-left:.3rem; font-weight:400; }}
@keyframes halo {{ 0% {{ box-shadow:0 0 0 0 color-mix(in srgb, var(--etat) 70%, transparent); }} 100% {{ box-shadow:0 0 0 12px transparent; }} }}
.parcours {{ position:relative; }}
.parcours .barre {{ display:flex; gap:3px; height:12px; border-radius:6px; overflow:hidden; }}
.parcours .seg {{ height:100%; opacity:.35; }}
.parcours .seg.fait {{ opacity:1; }}
.parcours .noms {{ display:flex; gap:3px; margin-top:.35rem; font-size:.76rem; color:var(--texte2); }}
.parcours .noms span {{ overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }}
.parcours .curseur {{ position:absolute; top:-5px; width:3px; height:22px; background:var(--texte); border-radius:2px;
  box-shadow:0 0 8px var(--texte); }}
.frise {{ display:flex; gap:1px; height:34px; margin:.2rem 0 .3rem 0; }}
.frise b {{ flex:1; border-radius:2px; opacity:.9; transition:transform .15s, opacity .15s; }}
.frise b:hover {{ transform:scaleY(1.25); opacity:1; }}
.frise-axe {{ display:flex; font-size:.76rem; color:var(--texte2); }}
.frise-axe span {{ border-left:1px solid var(--bordure); padding-left:.35rem; }}
.legende {{ display:flex; gap:1rem; flex-wrap:wrap; font-size:.8rem; color:var(--texte2); margin-top:.4rem; }}
.legende i {{ width:.7rem; height:.7rem; border-radius:2px; display:inline-block; margin-right:.35rem; vertical-align:-1px; }}
.tuiles {{ display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin-bottom:1rem; }}
.tuile {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:10px; padding:1rem 1.1rem; opacity:.45; }}
.tuile .ic {{ color:var(--texte2); }}
.tuile .t {{ font-weight:600; font-size:1.05rem; color:var(--texte); margin-top:.4rem; }}
.tuile .d {{ color:var(--texte2); font-size:.82rem; }}
.tuile.active {{ opacity:1; border-color:var(--etat); box-shadow:0 0 0 1px var(--etat), 0 0 22px color-mix(in srgb, var(--etat) 25%, transparent); }}
.tuile.active .ic {{ color:var(--etat); }}
.arbre {{ background:var(--panneau); border:1px solid var(--bordure); border-radius:10px; padding:.6rem; }}
.arbre .actif {{ animation: pulse 1.6s ease-in-out infinite; }}
@media (max-width: 900px) {{ .hero, .tuiles {{ grid-template-columns:1fr; }} }}
@keyframes tourne {{ to {{ transform: rotate(360deg); }} }}
@keyframes coule-v {{ to {{ stroke-dashoffset: -20; }} }}
@keyframes coule-h {{ to {{ stroke-dashoffset: -32; }} }}
@keyframes vague {{ 50% {{ transform: translateX(-12px); }} }}
@keyframes pulse {{ 50% {{ opacity: .35; }} }}
@keyframes clignote {{ 50% {{ opacity: .25; }} }}
.synoptique .tourne {{ animation: tourne 2s linear infinite; }}
.synoptique .coule-v {{ animation: coule-v 1s linear infinite; }}
.synoptique .coule-h {{ animation: coule-h 1.5s linear infinite; }}
.synoptique .vague {{ animation: vague 3s ease-in-out infinite; }}
.synoptique .pulse {{ animation: pulse 1.2s ease-in-out infinite; }}
.direct {{ display:inline-flex; align-items:center; gap:.5rem; color:var(--texte2); font-size:.85rem; margin-bottom:.8rem; }}
.direct i {{ width:.6rem; height:.6rem; border-radius:50%; background:var(--etat,var(--ok)); display:inline-block; animation: clignote 1.4s ease-in-out infinite; }}
@media (prefers-reduced-motion: reduce) {{ .synoptique *, .direct i, .hero i, .arbre * {{ animation:none !important; }} }}
</style>""", unsafe_allow_html=True)


def gabarit_plotly(hauteur: int = 320, theme: str | None = None) -> dict:
    c = couleurs(theme)
    return dict(
        height=hauteur, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", color=c["texte"], size=12),
        xaxis=dict(gridcolor=c["grille"], zerolinecolor=c["grille"], linecolor=c["bordure"],
                   tickformat="%d/%m", hoverformat="%d/%m/%Y %H:%M"),
        yaxis=dict(gridcolor=c["grille"], zerolinecolor=c["grille"], linecolor=c["bordure"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=c["panneau2"], font_color=c["texte"]),
        hovermode="x unified", separators=", ",
    )
