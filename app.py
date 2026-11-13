"""Point d'entrée de l'application : streamlit run app.py"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Suivi énergétique du condenseur évaporatif", layout="wide",
                   page_icon=str(Path(__file__).parent / "vues" / "favicon.png"), initial_sidebar_state="expanded")

from vues.commun import barre_laterale  # noqa: E402

st.session_state["machine"] = barre_laterale()

pages = {
    "Exploitation": [
        st.Page("vues/vue_globale.py", title="Santé et surcoûts", icon=":material/monitor_heart:", default=True),
        st.Page("vues/diagnostic.py", title="Diagnostic ciblé", icon=":material/troubleshoot:"),
        st.Page("vues/import_fichier.py", title="Import de données", icon=":material/upload_file:"),
    ],
    "Configuration": [
        st.Page("vues/parametres.py", title="Paramètres de référence", icon=":material/tune:"),
        st.Page("vues/machines.py", title="Sites et machines", icon=":material/factory:"),
    ],
}
st.navigation(pages).run()
