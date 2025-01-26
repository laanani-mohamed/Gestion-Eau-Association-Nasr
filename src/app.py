import os
import streamlit as st
from utils.auth import authenticate_user
from app_functions import get_to_app

def main():
    st.set_page_config(page_title="Gestion d'eau", page_icon=":droplet:", layout="wide")

    # Chemin relatif pour l'image
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_path = os.path.join(script_dir, "assets", "logo", "user.png")

    # Formulaire de connexion
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col2:
            st.image(user_path, width=250)

        col4, col5, col6 = st.columns([2, 2, 2])
        with col5:
            username = st.text_input("Nom d'utilisateur")

        col7, col8, col9 = st.columns([2, 2, 2])
        with col8:
            password = st.text_input("Mot de passe", type="password")

        col10, col11, col12 = st.columns([2, 2, 2])
        with col11:
            if st.button("Se connecter"):
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect")
    else:
        get_to_app()

if __name__ == "__main__":
    main()