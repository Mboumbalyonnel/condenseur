"""Point d'entrée de l'application : streamlit run app.py"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="TUNIFROID · Suivi énergétique du condenseur évaporatif", layout="wide",
                   page_icon=str(Path(__file__).parent / "vues" / "logo_tunifroid.png"),
                   initial_sidebar_state="expanded")

from vues.commun import barre_laterale  # noqa: E402

st.session_state["machine"], st.session_state["scenario"] = barre_laterale()

pages = {
    "Exploitation": [
        st.Page("vues/tableau_de_bord.py", title="Tableau de bord", icon=":material/monitor_heart:", default=True),
        st.Page("vues/diagnostic.py", title="Diagnostic", icon=":material/account_tree:"),
        st.Page("vues/import_fichier.py", title="Import des scénarios", icon=":material/upload_file:"),
    ],
    "Configuration": [
        st.Page("vues/parametres.py", title="Paramètres de référence", icon=":material/tune:"),
        st.Page("vues/fluides.py", title="Bibliothèque de fluides", icon=":material/science:"),
        st.Page("vues/machines.py", title="Sites et machines", icon=":material/factory:"),
    ],
}
st.navigation(pages).run()
