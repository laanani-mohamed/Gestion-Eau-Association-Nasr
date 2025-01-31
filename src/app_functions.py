import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# Obtenez le répertoire du script actuel
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construisez le chemin relatif vers les images
logo_sidebar_path = os.path.join(script_dir, "assets", "logo", "logo_sidebar.png")
id_card_logo_path = os.path.join(script_dir, "assets", "logo", "id-card.png")
liste_logo_path = os.path.join(script_dir, "assets", "logo", "liste.png")
saisie_logo_path = os.path.join(script_dir, "assets", "logo", "saisie.png")
pay_logo_path = os.path.join(script_dir, "assets", "logo", "pay.png")
pay2_logo_path = os.path.join(script_dir, "assets", "logo", "pay2.png")
historique_logo_path = os.path.join(script_dir, "assets", "logo", "historique.png")
warehouse_logo_path = os.path.join(script_dir, "assets", "logo", "warehouse.png")
budget_logo_path = os.path.join(script_dir, "assets", "logo", "budget.png")
mechanic_logo_path = os.path.join(script_dir, "assets", "logo", "mechanic.png")
facture_logo_path = os.path.join(script_dir, "assets", "logo", "facture.png")
caisse_logo_path = os.path.join(script_dir, "assets", "logo", "caisse.png")
verification_logo_path = os.path.join(script_dir, "assets", "logo", "verification.png")
vue_stock_logo_path = os.path.join(script_dir, "assets", "logo", "vue_stock.png")
calendar_logo_path = os.path.join(script_dir, "assets", "logo", "calendar.png")
describe_logo_path = os.path.join(script_dir, "assets", "logo", "describe.png")
worker_logo_path = os.path.join(script_dir, "assets", "logo", "worker.png")
money_logo_path = os.path.join(script_dir, "assets", "logo", "money.png")
materiel_logo_path = os.path.join(script_dir, "assets", "logo", "materiel.png")
debt_logo_path = os.path.join(script_dir, "assets", "logo", "debt.png")
pay3_logo_path = os.path.join(script_dir, "assets", "logo", "pay3.png")
facture_logo_path = os.path.join(script_dir, "assets", "logo", "facture.png")



def get_to_app():
    # Connexion à la base de données
    db_path = os.path.join(os.path.dirname(__file__), 'Gestion_eau.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Utilisation de la barre latérale pour le menu de sélection
    col1, col2 = st.columns([1, 10])
    with col1:
        st.sidebar.image(logo_sidebar_path, width=100)
    with col2:
        st.sidebar.title("Association Gestion d'eau")
    
    option = st.sidebar.radio("Choisissez une option :", [
            "Ajouter un nouveau abonné",
            "Liste des abonnés",
            "Saisir une consommation",
            "Paiement d'abonnement",
            "Paiement de consommation",
            "Historique consommation & Paiment",
            "Stock",
            "ONEP",
            "Charge Maintenance",
            "Générer une facture de paiement",
            "Mouvement de la caisse",
            "Vérification Consommation"
        ])
    
    
##################################################################################################################
    def champs_remplis(*args):
            return all(arg not in ("", None) for arg in args)
    
    # Requête SQL pour obtenir les données nécessaires pour Consommation Historique & Payement   
    query1 = '''
    SELECT 
        q.N_contrat,
        strftime('%Y-%m', q.Date_consome) AS Mois_Consome,
        q.Date_consome,
        q.Quantite AS Index_m3,
        q.Quantite - q.Index_precedent AS Qte_Consomme_m3,
        (q.Quantite - q.Index_precedent)*7 AS Montant_base_dh,
        q.gestion AS Gestion_dh,
        q.perte AS Perte_dh,
        (q.Quantite - q.Index_precedent)*7 + q.gestion + q.perte AS Total
    FROM 
        Qte_Consommation q;
'''
    df1 = pd.read_sql_query(query1, conn)

    query2 = '''
            SELECT 
                p.N_contrat,
                strftime('%Y-%m', p.Date_paye) AS Mois_Payement,
                p.Date_payement AS Date_réglement,
                p.N_recue,
                p.Mnt_paye AS Montant_paye
            FROM 
                Pay_consommation p
            WHERE 
                p.Date_payement IS NOT NULL;
            '''
    df2 = pd.read_sql_query(query2, conn)

        # Jointure des DataFrames
    df_merged = pd.merge(df1, df2, how='left', left_on=['N_contrat', 'Mois_Consome'], right_on=['N_contrat', 'Mois_Payement'])

        # Calculer la colonne Crédit
    df_merged['Crédit'] = df_merged['Total'] - df_merged['Montant_paye'].where(df_merged['Montant_paye'].notna(), 0)

        # Affichage du DataFrame d'origine
    data_f = df_merged[['N_contrat', 'Mois_Consome', 'Date_réglement', 'N_recue', 'Index_m3', 'Qte_Consomme_m3', 'Montant_base_dh', 'Gestion_dh', 'Perte_dh', 'Total', 'Montant_paye','Crédit']]
    data_ff = df_merged[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Total', 'Montant_paye','Crédit']]
##################################################################################################################



    # Ajouter un nouveau abonné
    if option == "Ajouter un nouveau abonné":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(id_card_logo_path, width=100)
            with col2:
                st.title("Ajouter un nouveau abonné")
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            col5, col6 = st.columns(2)
            N_contrat = col1.text_input("Nº de contrat :")
            CIN = col2.text_input("Nº CIN :")
            Nom = st.text_input("Nom Complet :")
            N_conpteur_B = col3.selectbox("Nº compteur Block :", list(range(1, 16)))
            N_conpteur_P = col4.text_input("Nº compteur Personnel :")
            Mnt_due = col5.number_input("Frais d'adhision :", min_value=0.0)
            Date_Adhesion = col6.date_input("Date d'adhision : ")
            Adresse = st.text_input("Adresse :")
            
            if st.button("Enregistrer"):
                if champs_remplis(N_contrat, CIN, N_conpteur_B, Nom, Mnt_due, Date_Adhesion, Adresse):
                    # Vérification si le numéro de contrat existe déjà
                    cursor.execute("SELECT COUNT(*) FROM info_personne WHERE N_contrat = ?", (N_contrat,))
                    existe = cursor.fetchone()[0]
                    
                    if existe > 0:
                        st.error("Le numéro de contrat existe déjà.")
                    else:
                        # Insérer un nouvel abonné si le numéro de contrat est unique
                        cursor.execute('''
                            INSERT INTO info_personne (N_contrat, Cin, N_conpteur_B, N_conpteur_P, Nom, Mnt_due, Date_Adhesion, Adresse)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (N_contrat, CIN, N_conpteur_B, N_conpteur_P, Nom, Mnt_due, Date_Adhesion, Adresse))
                        conn.commit()
                        st.success("Nouveau abonné ajouté avec succès !")
                else:
                    st.warning("Il y a des informations manquantes. Veuillez remplir tous les champs.")

    # Liste des abonnés avec colonne "Credit" calculée
    if option == "Liste des abonnés":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(liste_logo_path, width=100)
            with col2:
                st.title("Liste des abonnés ")
            
            # Requête SQL pour obtenir le montant dû et la somme des paiements
            query = '''
            SELECT 
                info_personne.N_contrat,
                info_personne.N_conpteur_B,
                info_personne.N_conpteur_P,
                info_personne.Nom,
                info_personne.Mnt_due AS Montant_Adhision,
                COALESCE(info_personne.Mnt_due - SUM(Abonnement.Mnt_paye), info_personne.Mnt_due) AS Credit,
                info_personne.Date_Adhesion,
                info_personne.Adresse
            FROM 
                info_personne
            LEFT JOIN 
                Abonnement 
            ON 
                info_personne.N_contrat = Abonnement.N_contrat
            GROUP BY 
                info_personne.N_contrat
            '''
            # Charger les données dans un DataFrame
            data = pd.read_sql_query(query, conn)

            # Afficher le DataFrame complet par défaut
            data = data.sort_values(by='N_contrat')
            st.dataframe(data)

            # Ajout des filtres dynamiques en bas
            st.markdown("## Filtrer")
            filtered_data = data.sort_values(by='N_contrat').copy()  # Copie du DataFrame pour appliquer les filtres
            # Création de filtres alignés horizontalement
            with st.container():
                col1, col2 = st.columns([1, 1])
                
                # Filtre pour N_contrat
                with col1:
                    unique_contrat = filtered_data['N_contrat'].dropna().unique()
                    selected_contrat = st.multiselect("Par Nº Contrat", unique_contrat)
                    if selected_contrat:
                        filtered_data = filtered_data[filtered_data['N_contrat'].isin(selected_contrat)]
                
                # Filtre pour N_conpteur_B
                with col2:
                    unique_compteur_b = filtered_data['N_conpteur_B'].dropna().unique()
                    selected_compteur_b = st.multiselect("Par Nº Block", unique_compteur_b)
                    if selected_compteur_b:
                        filtered_data = filtered_data[filtered_data['N_conpteur_B'].isin(selected_compteur_b)]
            
            credit_filter = st.radio("Sélectionner le solde du crédit", ("Tous", "Credit = 0", "Credit > 0"))
            if credit_filter == "Credit = 0":
                filtered_data = filtered_data[filtered_data["Credit"] == 0]
            elif credit_filter == "Credit > 0":
                filtered_data = filtered_data[filtered_data["Credit"] > 0]

            # Afficher le DataFrame filtré après sélection
            st.subheader("Résultats Filtrés")
            st.dataframe(filtered_data)

    # Saisir une consommation
    if option == "Saisir une consommation":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(saisie_logo_path, width=100)
            with col2:
                st.title("Saisir une consommation")
            col1,col2 = st.columns(2)
            option2 = col1.selectbox("Choisissez une option :", ["Consommation Abonné","Consommation Block"])
            
            if option2 == "Consommation Abonné":
                st.subheader("Ajouter Consommation à un Abonné")
                # Requête pour récupérer les N_contrat et les Noms associés
                query = '''
                SELECT N_contrat, Nom FROM info_personne
                '''
                # Charger les données dans un DataFrame
                data = pd.read_sql_query(query, conn)

                # Afficher uniquement le sélecteur pour le N_contrat
                N_contrat = st.selectbox("Nº de contrat :", data['N_contrat'].tolist())
                col1, col2, col3 = st.columns(3)
                # Afficher le nom associé au N_contrat sélectionné
                selected_name = data[data['N_contrat'] == N_contrat]['Nom'].iloc[0]
                col1.info(f"{selected_name}")

                # Récupérer la dernière consommation pour le N_contrat sélectionné
                query_consumption = '''
                SELECT Date_consome, Quantite 
                FROM Qte_consommation 
                WHERE N_contrat = ? 
                ORDER BY Date_consome DESC 
                LIMIT 1
                '''
                last_consumption = pd.read_sql_query(query_consumption, conn, params=(N_contrat,))
                # Afficher la dernière consommation et la date
                if not last_consumption.empty:
                    last_date = last_consumption['Date_consome'].iloc[0]
                    last_index = last_consumption['Quantite'].iloc[0]
                    last_date = datetime.strptime(last_date, '%Y-%m-%d')
                    col2.info(f"{last_index} m³")
                    col3.info(f"{last_date.strftime('%m - %Y')}")
                else:
                    col2.info("Aucune consommation enregistrée.")
                # Saisie de la quantité consommée
                Quantite = st.number_input("Nouveau Index :", min_value=0.0)

                # Saisie de la date de consommation
                Date_consome = st.date_input("Mois de consommation :")


                # Bouton pour enregistrer la consommation
                if st.button("Enregistrer"):
                    # Code pour enregistrer la consommation dans la base de données
                    # Exemple d'insertion dans la table (à adapter selon votre schéma)
                    
                    insert_query = '''
                    INSERT INTO Qte_Consommation (N_contrat, Date_consome, Quantite, Index_precedent, gestion, perte)
                    VALUES (?, ?, ?, ?, 10, 5)
                    '''
                    # Exécution de la requête avec les valeurs saisies
                    conn.execute(insert_query, (N_contrat, Date_consome, Quantite, last_index))
                    conn.commit()
                    st.success("Consommation enregistrée avec succès !")

            if option2 == "Consommation Block":
                st.subheader("Ajouter Consommation à un Block")
                # Colonnes pour saisir les informations
                Block_ID = st.selectbox("Nº Block :", list(range(1, 16)))
                # Récupérer la dernière consommation pour le N_contrat sélectionné
                query_block = '''
                SELECT Date_consome, Index_m3 
                FROM Blocks
                WHERE Block_ID = ? 
                ORDER BY Date_consome DESC 
                LIMIT 1
                '''
                Block = pd.read_sql_query(query_block, conn, params=(Block_ID,))
                col1,col2 = st.columns(2)
                # Afficher la dernière consommation et la date
                if not Block.empty:
                    last_date = Block['Date_consome'].iloc[0]
                    last_date = datetime.strptime(last_date, '%Y-%m-%d')
                    last_index = Block['Index_m3'].iloc[0]
                    col1.info(f"{last_index} m³")
                    col2.info(f"{last_date.strftime('%m - %Y')}")
                else:
                    st.warning("Aucune consommation enregistrée.")
                    

                Index_m3 = st.number_input("Index m3 :", min_value=0.0, format="%.2f")
                Date_consome = st.date_input("Date de consommation :", value=datetime.today())

                # Bouton pour insérer les données
                if st.button("Ajouter"):
                    try:
                        # Insérer les données dans la table
                        cursor.execute('''
                        INSERT INTO Blocks (Block_ID, Index_m3, Date_consome)
                        VALUES (?, ?, ?)
                        ''', (Block_ID, Index_m3, Date_consome))
                        conn.commit()
                        st.success("Données ajoutées avec succès !")
                    except Exception as e:
                        st.error(f"Une erreur s'est produite : {e}")

                # Calculer la quantité consommée avec gestion des valeurs manquantes
                st.header("Suivi des Blocks")
                query = '''
                SELECT 
                    Block_ID,
                    strftime('%m-%Y', Date_consome) AS Mois_Annee,
                    Index_m3,
                    Index_m3 - COALESCE(
                        LAG(Index_m3) OVER (
                            PARTITION BY Block_ID
                            ORDER BY strftime('%Y-%m', Date_consome)
                        ), 0
                    ) AS Qte_consome
                FROM Blocks
                '''
                blocks_df = pd.read_sql_query(query, conn)

                # Afficher les données dans Streamlit
                st.dataframe(blocks_df)

    # Paiement d'abonnement
    if option == "Paiement d'abonnement":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(pay_logo_path, width=100)
            with col2:
                st.title("Paiement d'abonnement")
            
            # Requête pour récupérer les N_contrat et les Noms associés, ainsi que le crédit
            query = '''
            SELECT 
                ip.N_contrat,
                ip.Nom,
                ip.Mnt_due AS Montant_Adhision,
                COALESCE(ip.Mnt_due - SUM(ab.Mnt_paye), ip.Mnt_due) AS Credit
            FROM 
                info_personne ip
            LEFT JOIN 
                Abonnement ab
            ON 
                ip.N_contrat = ab.N_contrat
            GROUP BY 
                ip.N_contrat, ip.Nom, ip.Mnt_due
            '''
            
            # Charger les données dans un DataFrame
            data = pd.read_sql_query(query, conn)

            # Afficher uniquement le sélecteur pour le N_contrat
            N_contrat = st.selectbox("Nº de contrat :", data['N_contrat'].tolist())
            
            col1, col2 = st.columns(2)
            # Afficher le nom associé au N_contrat sélectionné
            selected_name = data[data['N_contrat'] == N_contrat]['Nom'].iloc[0]
            col1.info(f"Nom de l'abonné : {selected_name}")

            # Récupérer le crédit associé au N_contrat sélectionné
            Credit = data[data['N_contrat'] == N_contrat]['Credit'].iloc[0]
            col2.info(f"Crédit : {Credit:.2f} dh")

            N_recue = st.selectbox("Nº de reçu : ", list(range(1, 2001)))
            Mnt_paye = st.number_input("Montant payé :", min_value=0.0)
            if Mnt_paye > Credit:
                st.warning(f"Montant dépasse crédit {Credit:.2f} dh. Veuillez corriger.")
            Date_payement = st.date_input("Date de régelement :")
            if st.button("Enregistrer paiement"):
                if champs_remplis(N_contrat, N_recue, Mnt_paye, Date_payement):
                    if Mnt_paye <= Credit:
                        # Insérer le paiement dans la base de données
                        cursor.execute('''
                            INSERT INTO Abonnement (N_contrat, N_recue, Mnt_paye, Date_payement)
                            VALUES (?, ?, ?, ?)
                        ''', (N_contrat, N_recue, Mnt_paye, Date_payement))
                        conn.commit()
                        st.success("Paiement d'abonnement enregistré avec succès !")
                    else:
                        st.error(f"Montant {Mnt_paye:.2f} dh dépasse crédit {Credit:.2f} dh.")
                else:
                    st.warning("Il y a des informations manquantes. Veuillez remplir tous les champs.")

            st.subheader("Historique des paiements des frais d'adhésion")
            
            # Requête pour récupérer les données de la table Abonnement
            query1 = "SELECT * FROM Abonnement WHERE N_contrat = ?"
            data1 = pd.read_sql_query(query1, conn, params=(N_contrat,))

            # Assurez-vous que 'Date_payement' est bien converti en datetime
            data1['Date_payement'] = pd.to_datetime(data1['Date_payement'], errors='coerce').dt.date

            # Afficher le DataFrame complet filtré par N_contrat
            if not data1.empty:  # Vérifie si le DataFrame est vide ou non
                st.dataframe(data1)
            else:
                st.warning("Aucun Historique de paiement trouvé")

    # Paiement de consommation
    if option == "Paiement de consommation":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(pay2_logo_path, width=100)
            with col2:
                st.title("Paiement de consommation")
            
            # Requête pour récupérer les N_contrat et les Noms associés
            query = '''
            SELECT N_contrat, Nom FROM info_personne
            '''
            # Charger les données dans un DataFrame
            data = pd.read_sql_query(query, conn)

            # Afficher uniquement le sélecteur pour le N_contrat
            N_contrat = st.selectbox("Nº de contrat :", data['N_contrat'].tolist())

            # Afficher le nom associé au N_contrat sélectionné
            col1, col2 = st.columns(2)
            selected_name = data[data['N_contrat'] == N_contrat]['Nom'].iloc[0]
            col1.info(f"Nom de l'abonné : {selected_name}")

            # Saisie du montant payé
            Mnt_paye = st.number_input("Montant payé", min_value=0.0)

            # Sélection du numéro de reçu
            N_recue = st.selectbox("Nº de reçu :", list(range(1, 201)))

            # Saisie des dates
            Date_paye = st.date_input("Mois à régler :")
            Date_payement = st.date_input("Date de règlement :")

            # Bouton pour soumettre le paiement
            if st.button("Enregistrer le paiement"):
                try:
                    # Insertion dans la table Pay_Consommation
                    insert_query = '''
                    INSERT INTO Pay_Consommation (N_contrat, Mnt_paye, N_recue, Date_paye, Date_payement, Gestion, Perte)
                    VALUES (?, ?, ?, ?, ?, 10, 5)
                    '''
                    cursor.execute(insert_query, (N_contrat, Mnt_paye, N_recue, Date_paye, Date_payement))
                    conn.commit()
                    st.success("Le paiement a été enregistré avec succès.")
                except Exception as e:
                    st.error(f"Une erreur s'est produite : {e}")


            # Filtrer pour N_contrat sélectionné et Crédit != 0
            df_filtered = data_ff[(df_merged['N_contrat'] == N_contrat) & (df_merged['Crédit'] != 0)]
            df_grouped = df_filtered.groupby(['N_contrat', 'Mois_Consome', 'Total']).agg({
            'Montant_paye': 'sum'
            }).reset_index()

            # Calculer le crédit restant par mois en fonction des paiements
            df_grouped['Crédit_rest'] = df_grouped['Total'] - df_grouped['Montant_paye']
            df_grouped = df_grouped[df_grouped['Crédit_rest'] != 0]  # Garde les factures non payées

            # Joindre pour obtenir le détail complet des colonnes originales
            df_final = df_filtered.merge(df_grouped[['N_contrat', 'Mois_Consome', 'Crédit_rest']], on=['N_contrat', 'Mois_Consome'], how='inner')

            N_mois = df_final['Mois_Consome'].nunique()
            # Afficher l'historique de consommation avec le crédit différent de 0
            col1,col2 = st.columns(2)
            if not df_final.empty:
                st.write("### Les factures Non payées :")
                st.dataframe(df_final[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Total', 'Montant_paye', 'Crédit_rest']])
                Sum_credit = df_final['Crédit_rest'].sum()
                col1.warning(f"Crédit Totale = {Sum_credit} dh")
                col2.warning(f"Nº mois Non Payé : {N_mois}")
            else:
                col1.warning("L'abonné est à jour.")

    # Section Historique de consommation & Paiement
    if option == "Historique consommation & Paiment":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(historique_logo_path, width=100)
            with col2:
                st.title("Historique: consommation & Paiment")

            st.dataframe(data_f)

            # Section Filtrage des données
            st.markdown("## Filtrer les données")

            # Disposition avec des colonnes pour les filtres
            col1, col2, col3 = st.columns(3)

            with col1:
                contrat_filter = st.multiselect("Par Nº Contrat", data_f['N_contrat'].unique())
                if contrat_filter:
                    data_f = data_f[data_f['N_contrat'].isin(contrat_filter)]

            with col2:
                mois_filter = st.selectbox("Par Mois", ['Aucun'] + list(data_f['Mois_Consome'].unique()))
                if mois_filter != 'Aucun':
                    data_f = data_f[data_f['Mois_Consome'] == mois_filter]

            with col3:
                recue_filter = st.multiselect("Par Nº Reçu", data_f['N_recue'].dropna().unique())
                if recue_filter:
                    data_f = data_f[data_f['N_recue'].isin(recue_filter)]

            # Affichage des options de filtre pour Qte_Consomme_m3 et Crédit
            col4, col5 = st.columns(2)

            with col4:
                qte_filter = st.radio("Filtrer par Qte Consommée (m3)", ('Tous', 'Égal à 0', 'Différent de 0'))
                if qte_filter == 'Différent de 0':
                    data_f = data_f[data_f['Qte_Consomme_m3'] != 0]
                elif qte_filter == 'Égal à 0':
                    data_f = data_f[data_f['Qte_Consomme_m3'] == 0]

            with col5:
                credit_filter = st.radio("Filtrer par Crédit", ('Tous', 'Égal à 0', 'Différent de 0'))
                if credit_filter == 'Différent de 0':
                    data_f = data_f[data_f['Crédit'] != 0]
                elif credit_filter == 'Égal à 0':
                    data_f = data_f[data_f['Crédit'] == 0]

            # Afficher les données filtrées
            st.dataframe(data_f)

    # Gestion du Stock
    if option == "Stock":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(warehouse_logo_path, width=100)
            with col2:
                st.title("Gestion du Stock")
            # Options de gestion du stock
            option = st.selectbox(
                "Sélectionnez une option :",
                ("Produit Acheter", "Produit Utiliser", "Vue sur le stock")
            )
            # Formulaire d'achat dans Streamlit
            if option == "Produit Acheter":
                st.subheader("Ajouter des Produits au stock")

                # Création des champs du formulaire pour l'achat
                Nom_produit = st.selectbox("Nom du Produit", options=[row[0] for row in cursor.execute("SELECT Nom_Produit FROM Produit").fetchall()], help="Sélectionnez un produit existant")
                date_achat = st.date_input("Date d'Achat", value=datetime.today(), help="Date de l'achat")
                quantite_achetee = st.number_input("Quantité achetée", min_value=0.0, format="%.2f", help="Quantité achetée du produit")
                prix_unitaire = st.number_input("Prix unitaire", min_value=0.0, format="%.2f", help="Prix unitaire du produit")
                n_recu = st.text_input("Numéro de reçu", help="Numéro de reçu ou facture de l'achat")
                fournisseur = st.text_input("Fournisseur", help="Nom du fournisseur")

                # Calcul du montant total
                montant_total = quantite_achetee * prix_unitaire

                # Bouton de soumission
                submit = st.button("Enregistrer l'achat")

                # Traitement de l'insertion dans la base de données
                if submit:
                    # Vérifier que tous les champs sont remplis
                    if not Nom_produit or not date_achat or not quantite_achetee or not prix_unitaire or not n_recu or not fournisseur:
                        st.error("Données manquantes : Veuillez remplir toutes les informations.")
                    else:
                        try:
                            # Insertion des données dans la table Achat
                            cursor.execute('''
                                INSERT INTO Produit_Acheter (Nom_Produit, Date_Achat, Quantite_achetee, Prix_unitaire, N_recu, Fournisseur)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (Nom_produit, date_achat, quantite_achetee, prix_unitaire, n_recu, fournisseur))
                            conn.commit()

                            # Message de confirmation
                            st.success("Achat enregistré avec succès !")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erreur lors de l'enregistrement de l'achat : {e}")

                # Affichage de l'historique des achats
                st.subheader("Historique des Achats")

                # Récupération des achats dans la base de données
                achats = cursor.execute('''
                        SELECT Nom_Produit, Date_Achat, Quantite_achetee, Prix_unitaire, Montant_total, N_recu, Fournisseur
                        FROM Produit_Acheter
                        ORDER BY Date_Achat DESC
                    ''').fetchall()

                # Si des achats ont été enregistrés
                if achats:
                    # Création d'un tableau pour afficher les achats
                    achats_df = pd.DataFrame(achats, columns=["Nom du Produit", "Date d'Achat", "Quantité", "Prix Unitaire", "Montant Total", "Numéro de Reçu", "Fournisseur"])                
                    # Affichage du tableau
                    st.dataframe(achats_df)
                else:
                    st.write("Aucun achat enregistré pour le moment.")

            elif option == "Produit Utiliser":
                st.subheader("Retirer des Produits du stock")
                # Création des champs du formulaire pour produit utiliser
                Nom_produit = st.selectbox("Nom du Produit", options=[row[0] for row in cursor.execute("SELECT Nom_Produit FROM Produit").fetchall()])
                stock_query = """
                    SELECT 
                        p.Nom_Produit, 
                        COALESCE(SUM(pa.Quantite_achetee), 0) - COALESCE(SUM(pu.Quantite_utuli), 0) AS Stock_Restant
                    FROM 
                        Produit p
                    LEFT JOIN 
                        Produit_Acheter pa ON p.Nom_Produit = pa.Nom_Produit
                    LEFT JOIN 
                        Produit_Utiliser pu ON p.Nom_Produit = pu.Nom_Produit
                    WHERE 
                        p.Nom_Produit = ?
                    GROUP BY 
                        p.Nom_Produit;
                    """
                stock_result = cursor.execute(stock_query, (Nom_produit,)).fetchone()
                stock_rest = stock_result[1]
                st.warning(f"Quantité disponible : {int(stock_rest)}")
                
                date_utilise = st.date_input("Date d'utilisation", value=datetime.today())
                quantite_utilise = st.number_input("Quantité Utilisée", min_value=0.0, format="%.2f")
                Description = st.text_input("Déscription")

                # Bouton de soumission
                submit = st.button("Enregistrer l'utilisation")

                # Traitement de l'insertion dans la base de données
                if submit:
                    # Vérifier que tous les champs sont remplis
                    if not Nom_produit or not date_utilise or not quantite_utilise or not Description:
                        st.error("Données manquantes : Veuillez remplir toutes les informations.")
                    else:
                        try:
                            # Insertion des données dans la table Achat
                            cursor.execute('''
                                INSERT INTO Produit_utiliser (Nom_Produit, date_utils, quantite_utuli, Description)
                                VALUES (?, ?, ?, ?)
                            ''', (Nom_produit, date_utilise, quantite_utilise, Description))
                            conn.commit()

                            # Message de confirmation
                            st.success("Produit Retirer  avec succès !")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erreur : {e}")

                # Affichage de l'historique des achats
                st.subheader("Historique des Utilisations")

                # Récupération des achats dans la base de données
                utuliser = cursor.execute('''
                        SELECT Nom_Produit, Date_utils, Quantite_utuli, Description
                        FROM Produit_Utiliser
                        ORDER BY Date_utils DESC
                    ''').fetchall()

                # Si des achats ont été enregistrés
                if utuliser:
                    # Création d'un tableau pour afficher les achats
                    utilisation_df = pd.DataFrame(utuliser, columns=["Nom du Produit", "Date d'utulisation", "Quantité", "Description"])                
                    # Affichage du tableau
                    st.dataframe(utilisation_df)
                else:
                    st.write("Aucune Utilisation enregistré pour le moment.")

            elif option == "Vue sur le stock":
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.image(vue_stock_logo_path, width=100)
                with col2:
                    st.subheader("Vue sur le stock actuel")
                
                # Effectuer la requête SQL pour obtenir les données de stock
                stock_query = """
                SELECT 
                    p.Nom_Produit, 
                    COALESCE(SUM(pa.Quantite_achetee), 0) - COALESCE(SUM(pu.Quantite_utuli), 0) AS Stock_Restant
                FROM 
                    Produit p
                LEFT JOIN 
                    Produit_Acheter pa ON p.Nom_Produit = pa.Nom_Produit
                LEFT JOIN 
                    Produit_Utiliser pu ON p.Nom_Produit = pu.Nom_Produit
                GROUP BY 
                    p.Nom_Produit;
                """

                # Exécuter la requête et charger les données dans un DataFrame
                stock_df = pd.read_sql_query(stock_query, conn)
                
                # Afficher le DataFrame dans Streamlit
                st.write(stock_df)

    # Situation avec ONEP
    if option == "ONEP":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(budget_logo_path, width=100)
            with col2:
                st.title("Situation Avec ONEP")
            query = '''
            SELECT 
                c.Mois_consome, 
                c.Quantite_Consome AS Index_m3, 
                c.Mnt_a_paye,
                c.Facture AS Facture_Consommation, 
                p.Date_Reglement, 
                p.Recu, 
                (c.Mnt_a_paye - COALESCE(p.Mnt_paye, 0)) AS Credit
            FROM 
                ONEP_Credit c
            LEFT JOIN 
                ONEP_Payment p
            ON 
                c.Mois_consome = p.Mois_consome
        '''

            # Exécuter la requête et récupérer les résultats dans un DataFrame
            data = pd.read_sql_query(query, conn)

            # Vérifier si des données ont été récupérées
            if not data.empty:
                # Afficher les résultats sous forme de tableau dans Streamlit
                st.dataframe(data)
            else:
                st.write("Aucune intéraction trouvée entre l'association et l'ONEP.")
            col1, col2 = st.columns(2)
            #Afficher Credit total
            Credit_total = data['Credit'].sum()
            col1.info(f"Crédit Totale = {Credit_total} dh")
            Mois_nn_paye = data['Recu'].isnull().sum()
            col2.info(f"Nº Mois Non payé = {Mois_nn_paye} ")

            col3,col4 = st.columns(2)
            option = col3.selectbox("Choisissez une option :", ["Payer ONEP", "Crédit ONEP"])
            
            if option == "Payer ONEP":
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.image(pay3_logo_path, width=100)
                with col2:
                    st.subheader("Payer ONEP")
                Mois_consome = st.date_input("Mois consommé :", value=datetime.today())
                N_Recu = st.text_input("Nº Recu")
                Date_Reglement = st.date_input("Date du Regelement", value=datetime.today())
                Montant_paye = st.number_input("Montant Paye à ONEP", min_value=0.0, format="%.2f")
                # Bouton pour enregistrer l'achat
                submit_paiement = st.button("Enregistrer le paiement")
                
                if submit_paiement:
                    # Vérifier que toutes les informations sont complètes
                    if not Mois_consome or not  Montant_paye or not N_Recu or not Date_Reglement:
                        st.error("Données manquantes : Veuillez remplir toutes les informations.")
                    else:
                        try:
                            # Insérer les données dans la table ONEP_Payment
                            cursor.execute('''
                                INSERT INTO ONEP_Payment (Mois_consome, Mnt_paye, Recu, Date_Reglement)
                                VALUES (?, ?, ?, ?)
                            ''', (Mois_consome.strftime('%B %Y'), Montant_paye, N_Recu, Date_Reglement))
                            conn.commit()

                            st.success("Paiement ONEP enregistré avec succès !")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erreur lors de l'enregistrement du paiement : {e}")

            elif option == "Crédit ONEP":
                # Pour la gestion du crédit ONEP
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.image(debt_logo_path, width=100)
                with col2:
                    st.subheader("Crédit ONEP")
                
                # Entrée pour le mois de consommation
                Mois_consome = st.date_input("Mois consommé :", value=datetime.today())
                Montant_du_credit = st.number_input("Montant du crédit ONEP", min_value=0.0, format="%.2f")
                Quantite_Consome = st.number_input("Quantite Consomé :", min_value=0.0, format="%.2f")
                Facture = st.text_input("Nº Facture : ")
                # Bouton pour enregistrer le crédit ONEP
                submit_credit = st.button("Enregistrer le crédit ONEP")
                
                if submit_credit:
                    # Vérifier que les informations sont complètes
                    if not Mois_consome or not Montant_du_credit:
                        st.error("Données manquantes : Veuillez remplir toutes les informations.")
                    else:
                        try:
                            # Insérer les données dans la table ONEP_Charge (ou toute autre table de gestion des crédits)
                            cursor.execute('''
                                INSERT INTO ONEP_Credit (Mois_consome, Mnt_a_paye, Facture, Quantite_Consome)
                                VALUES (?, ?, ?, ?)
                            ''', (Mois_consome.strftime('%B %Y'), Montant_du_credit, Facture, Quantite_Consome))
                            conn.commit()

                            st.success("Crédit ONEP enregistré avec succès !")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erreur lors de l'enregistrement du crédit ONEP : {e}")

    # Charge Maintenance
    if option == "Charge Maintenance":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(mechanic_logo_path, width=100)
            with col2:
                st.title("Gestion de la Maintenance")

            # Option d'insertion d'une nouvelle opération de maintenance
            st.subheader("Nouvelle Opération de Maintenance")

            # Saisie des informations principales pour l'opération de maintenance
            col1, col2 = st.columns([1, 15])
            with col1:
                st.image(calendar_logo_path, width=100)
            with col2:
                date_operation = st.date_input("Date de l'opération", value=datetime.today())
            
            col1, col2 = st.columns([1, 15])
            with col1:
                st.image(describe_logo_path, width=100)
            with col2:
                description = st.text_area("Description de l'opération")
            
            col1, col2 = st.columns([1, 15])
            with col1:
                st.image(worker_logo_path, width=100)
            with col2:
                nom_ouvrier = st.text_input("Nom de l'ouvrier")
                
                
            col1, col2 = st.columns([1, 15])
            with col1:
                st.image(money_logo_path, width=100)
            with col2:
                mnt_ouvrier = st.number_input("Montant payé à l'ouvrier (DH)", min_value=0.0, format="%.2f")

            # Récupérer les noms de produits depuis la table Produit
            cursor.execute("SELECT Nom_Produit FROM Produit")
            produits = [row[0] for row in cursor.fetchall()]  # Extraire les noms de produits dans une liste

            # Initialisation des listes pour les noms et quantités de produits
            # Stockage de la liste des produits utilisés dans la session
            if 'produits_utilises' not in st.session_state:
                st.session_state.produits_utilises = []

            # Interface pour ajouter des produits et quantités à l'opération
            col1, col2 = st.columns([1, 15])
            with col1:
                st.image(materiel_logo_path, width=100)
            with col2:
                col6,col7= st.columns(2)    
                nom_produit = col6.selectbox("Nom du matériels", options=produits)
                quantite_produit = col7.number_input("Quantité utilisée", min_value=0.0, format="%.2f")
                ajouter_produit = st.button("Ajouter le produit")

            # Ajouter le produit et afficher le message de succès
            if ajouter_produit:
                # Ajouter le produit et la quantité dans la session
                st.session_state.produits_utilises.append({"Nom": nom_produit, "Quantité": quantite_produit})
                st.success(f"Produit '{nom_produit}' ajouté avec succès avec une quantité de {quantite_produit}!")

            # Afficher les produits ajoutés
            st.write("Produits utilisés pour cette opération:")
            for produit in st.session_state.produits_utilises:
                st.info(f"- {produit['Nom']}: {produit['Quantité']} unités")

            # Bouton de soumission pour enregistrer l'opération de maintenance et les produits associés
            if st.button("Enregistrer l'opération de maintenance"):
                if description and nom_ouvrier and mnt_ouvrier >= 0 and st.session_state.produits_utilises:
                    try:
                        # Insertion de l'opération principale dans la table Maintenance
                        cursor.execute('''
                            INSERT INTO Maintenance (Date_operation, Description, Nom_ouvrier, Mnt_ouvrier)
                            VALUES (?, ?, ?, ?)
                        ''', (date_operation, description, nom_ouvrier, mnt_ouvrier))
                        maintenance_id = cursor.lastrowid  # Récupère l'ID de l'opération ajoutée

                        # Insertion des détails des produits pour cette opération
                        for produit in st.session_state.produits_utilises:
                            cursor.execute('''
                                INSERT INTO Maintenance_Details (ID_Maintenance, Nom_produit, Quantite_produit)
                                VALUES (?, ?, ?)
                            ''', (maintenance_id, produit["Nom"], produit["Quantité"]))
                        
                        conn.commit()  # Valide les transactions
                        st.success("Opération de maintenance enregistrée avec succès.")
                        
                        # Réinitialiser les produits ajoutés
                        st.session_state.produits_utilises.clear()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Erreur lors de l'enregistrement : {e}")
                else:
                    st.warning("Veuillez remplir toutes les informations et ajouter au moins un produit.")
            st.title("Historique de Maintenance")

            # Sélection du mois
            unique_key = "date_operation_input"
            date_choisie = st.date_input("Date de l'opération", value=datetime.today(), key=unique_key)
            Mois_choisi = str(date_choisie.month).zfill(2)  # Format en deux chiffres

            # Requête SQL pour récupérer l'historique par mois
            query = """
            SELECT M.ID_Maintenance, M.Date_operation, M.Description, M.Nom_ouvrier, M.Mnt_ouvrier,
                D.Nom_produit, D.Quantite_produit
            FROM Maintenance AS M
            JOIN Maintenance_Details AS D ON M.ID_Maintenance = D.ID_Maintenance
            WHERE substr(date(M.Date_operation), 6, 2) = ?
            ORDER by M.ID_Maintenance
            """


            # Exécution de la requête avec le mois choisi comme paramètre
            cursor.execute(query, (Mois_choisi,))

            # Récupérer les résultats
            Historique = cursor.fetchall()

            # Affichage des résultats dans un tableau
            if Historique:
                # Création d'un DataFrame pour afficher dans un tableau
                df = pd.DataFrame(Historique, columns=[
                "ID Maintenance", "Date de l'opération", "Description", "Nom ouvrier", "Montant ouvrier",
                "Nom produit", "Quantité utilisée"])
                st.dataframe(df)  # Utilisation de st.dataframe() pour afficher le tableau
            else:
                st.info("Aucune opération de maintenance trouvée pour ce mois.")

    # Generer les facture
    if option == "Générer une facture de paiement":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(facture_logo_path, width=100)
            with col2:
                st.title("Générer une facture de paiement")

            def generer_facture_pdf(n_contrat, selected_name, date_facture, mois_consommation, Credit_abnmt, Sum_credit, credit_adhision_a_paye, credit_consommation_a_paye, quantite_consommee):
                pdf = FPDF()
                pdf.add_page()

                # Réduire les marges pour gagner de l'espace
                pdf.set_auto_page_break(auto=True, margin=5)  # Marge de 5 mm en bas
                pdf.set_margins(left=5, top=5, right=5)  # Marges gauche, droite et haut à 5 mm

                # En-tête
                pdf.set_font("Arial", 'B', 12)  # Taille de police réduite
                pdf.cell(0, 6, "Association Gestion d'Eau", ln=True, align='C')
                pdf.set_font("Arial", '', 8)  # Taille de police réduite
                pdf.ln(3)  # Espacement réduit

                # Informations de la facture
                pdf.set_font("Arial", 'B', 10)  # Taille de police réduite
                pdf.cell(0, 5, "Facture de Paiement", ln=True, align='C')
                pdf.ln(3)  # Espacement réduit

                pdf.set_font("Arial", '', 8)  # Taille de police réduite
                pdf.cell(0, 5, f"Date de la facture : {date_facture}", ln=True)
                pdf.cell(0, 5, f"N° de contrat : {n_contrat}", ln=True)
                pdf.cell(0, 5, f"Nom : {selected_name}", ln=True)
                pdf.cell(0, 5, f"Mois de consommation : {mois_consommation}", ln=True)
                pdf.cell(0, 5, f"Nº Recue : ", ln=True)
                pdf.ln(3)  # Espacement réduit

                # Onglet Crédit
                pdf.set_font("Arial", 'B', 10)  # Taille de police réduite
                pdf.cell(0, 5, "Info sur Crédit", ln=True)
                pdf.ln(2)  # Espacement réduit

                pdf.set_font("Arial", 'B', 7)  # Taille de police réduite
                pdf.cell(50, 5, "Description", border=1)
                pdf.cell(20, 5, "Montant", border=1)
                pdf.cell(20, 5, "Montant à Payer", border=1, ln=True)

                pdf.set_font("Arial", '', 8)  # Taille de police réduite
                pdf.cell(50, 5, "Crédit Abonnement Total :", border=1)
                pdf.cell(20, 5, f"{round(Credit_abnmt, 2)}", border=1)
                pdf.cell(20, 5, f"{round(credit_adhision_a_paye, 2)}", border=1, ln=True)

                pdf.cell(50, 5, "Crédit Consommation Total :", border=1)
                pdf.cell(20, 5, f"{round(Sum_credit, 2)}", border=1)
                pdf.cell(20, 5, f"{round(credit_consommation_a_paye, 2)}", border=1, ln=True)

                pdf.set_font("Arial", 'B', 8)  # Taille de police réduite
                pdf.cell(50, 5, "Total :", border=1)
                pdf.cell(20, 5, f"{round(Credit_abnmt + Sum_credit, 2)}", border=1)
                pdf.cell(20, 5, f"{round(credit_adhision_a_paye + credit_consommation_a_paye, 2)}", border=1, ln=True)
                pdf.ln(3)  # Espacement réduit

                # Onglet Consommation
                pdf.set_font("Arial", 'B', 10)  # Taille de police réduite
                pdf.cell(0, 5, "Info sur Consommation", ln=True)
                pdf.ln(2)  # Espacement réduit

                pdf.set_font("Arial", 'B', 8)  # Taille de police réduite
                pdf.cell(50, 5, "Détails", border=1)
                pdf.cell(40, 5, "Valeur", border=1, ln=True)

                pdf.set_font("Arial", '', 8)  # Taille de police réduite
                pdf.cell(50, 5, "Quantité Consommée (m³)", border=1)
                pdf.cell(40, 5, f"{quantite_consommee}", border=1, ln=True)

                pdf.cell(50, 5, "Redevance :", border=1)
                pdf.cell(40, 5, "10.00", border=1, ln=True)

                pdf.cell(50, 5, "Perte :", border=1)
                pdf.cell(40, 5, "5.00", border=1, ln=True)

                pdf.set_font("Arial", 'B', 8)  # Taille de police réduite
                pdf.cell(50, 5, "Total à Payer :", border=1)
                pdf.cell(40, 5, f"{round(quantite_consommee * 7 + 15, 2)}", border=1, ln=True)
                pdf.ln(3)  # Espacement réduit

                # Pied de page
                pdf.set_font("Arial", '', 7)  # Taille de police réduite
                pdf.cell(0, 5, "Téléphone : 01 23 45 67 89", ln=True)
                pdf.ln(2)  # Espacement réduit
                pdf.multi_cell(0, 5, "Remarque : Merci de régler cette facture dans les 30 jours. Tout retard entraînera des frais supplémentaires.")

                # Enregistrement du PDF
                pdf_file_name = f"facture_{n_contrat}_{mois_consommation}.pdf"
                pdf.output(pdf_file_name)
                return pdf_file_name

            query_abnmt = '''
            SELECT 
                ip.N_contrat,
                ip.Nom,
                ip.Mnt_due AS Montant_Adhision,
                COALESCE(ip.Mnt_due - SUM(ab.Mnt_paye), ip.Mnt_due) AS Credit
            FROM 
                info_personne ip
            LEFT JOIN 
                Abonnement ab
            ON 
                ip.N_contrat = ab.N_contrat
            GROUP BY 
                ip.N_contrat, ip.Nom, ip.Mnt_due
            '''
            
            # Charger les données dans un DataFrame
            df_abnmt = pd.read_sql_query(query_abnmt, conn)

            # Requête pour récupérer les N_contrat et les Noms associés
            query_contrat = '''
            SELECT N_contrat, Nom FROM info_personne
                '''
            # Charger les données dans un DataFrame
            df = pd.read_sql_query(query_contrat, conn)

            # Gestion des options du menu
            
            n_contrat = st.selectbox("Nº de contrat :", df['N_contrat'].tolist())
            st.subheader("Détail sur l'abonné")
            # Filtrer pour N_contrat sélectionné et Crédit != 0
            df_filtered = data_ff[(df_merged['N_contrat'] == n_contrat) & (df_merged['Crédit'] != 0)]
            df_grouped = df_filtered.groupby(['N_contrat', 'Mois_Consome', 'Montant_dh']).agg({
            'Montant_paye': 'sum'
            }).reset_index()

            # Calculer le crédit restant par mois en fonction des paiements
            df_grouped['Crédit_rest'] = df_grouped['Montant_dh'] - df_grouped['Montant_paye']
            df_grouped = df_grouped[df_grouped['Crédit_rest'] != 0]  # Garde les factures non payées

            # Joindre pour obtenir le détail complet des colonnes originales
            df_final = df_filtered.merge(df_grouped[['N_contrat', 'Mois_Consome', 'Crédit_rest']], on=['N_contrat', 'Mois_Consome'], how='inner')

            N_mois = df_final['Mois_Consome'].nunique()
            col3, col4 = st.columns(2)
            # Afficher le nom associé au N_contrat sélectionné
            selected_name = df_abnmt[df_abnmt['N_contrat'] == n_contrat]['Nom'].iloc[0]

            # Récupérer le crédit associé au N_contrat sélectionné
            Credit_abnmt = df_abnmt[df_abnmt['N_contrat'] == n_contrat]['Credit'].iloc[0]

            # Afficher l'historique de consommation avec le crédit différent de 0
            col1,col2 = st.columns(2)
            if not df_final.empty:
                st.write("### Les factures Non payées :")
                st.dataframe(df_final[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Montant_paye', 'Crédit_rest']])
                Sum_credit = df_final['Crédit_rest'].sum()
                col1.warning(f"Crédit Consommation = {Sum_credit} dh")
                col2.info(f"Nº mois Non Payé : {N_mois}")
                col3.info(f"Nom de l'abonné : {selected_name}")
                col4.warning(f"Crédit Adhision: {Credit_abnmt:.2f} dh")
            else:
                col1.warning("L'abonné est à jour.")

            credit_consommation_a_paye = st.number_input("Crédit consommation à payé :")
            credit_adhision_a_paye = st.number_input("Crédit adhision à payé :")
            date_facture = datetime.now().strftime("%Y-%m-%d")
            mois_consommation = st.selectbox("Mois à payer (consommation) :", df_final['Mois_Consome'].unique())
            quantite_consommee = df_final[df_final['Mois_Consome'] == mois_consommation]['Qte_Consomme_m3'].sum()

            if st.button("Générer la facture"):
                # Générer le fichier PDF
                pdf_file_name = generer_facture_pdf(n_contrat, selected_name, date_facture, mois_consommation, Credit_abnmt, Sum_credit, credit_adhision_a_paye, credit_consommation_a_paye, quantite_consommee)

                # Chemin du dossier Factures
                factures_dir = "Factures/2025"
                
                # Vérifier si le dossier existe, sinon le créer
                if not os.path.exists(factures_dir):
                    os.makedirs(factures_dir)
                
                # Chemin complet du fichier PDF à enregistrer
                pdf_file_path = os.path.join(factures_dir, pdf_file_name)
                
                # Lire le fichier PDF généré
                with open(pdf_file_name, "rb") as file:
                    pdf_bytes = file.read()
                
                # Enregistrer le fichier PDF dans le dossier Factures
                with open(pdf_file_path, "wb") as file:
                    file.write(pdf_bytes)
                
                # Bouton de téléchargement
                st.download_button(
                    label="Télécharger la facture en PDF",
                    data=pdf_bytes,
                    file_name=pdf_file_name,
                    mime="application/pdf"
                )

                # Titre de la page
                st.title("Facture")

                # Onglet Crédit
                st.subheader("Info sur Crédit")
                credit_data = {
                    "Description": ["Crédit Abonnement Total :", "Crédit Consommation Total :", "Total :"],
                    "Montant (dh)": [round(Credit_abnmt, 2), round(Sum_credit, 2), round(Credit_abnmt + Sum_credit, 2)],
                    "Montant à Payer (dh)": [round(credit_adhision_a_paye, 2), round(credit_consommation_a_paye, 2), round(credit_adhision_a_paye + credit_consommation_a_paye, 2)]
                }
                credit_df = pd.DataFrame(credit_data)
                st.table(credit_df)

                # Espacement
                st.write("\n")

                # Onglet Consommation
                st.subheader("Info sur Consommation")
                consommation_data = {
                    "Détails": [
                        "Quantité Consommée (m³)",
                        "Redevance :",
                        "Perte :",
                        "Total à Payer :"
                    ],
                    "Valeur": [quantite_consommee, 10, 5, round(quantite_consommee * 7 + 15, 2)]
                }
                consommation_df = pd.DataFrame(consommation_data)
                st.table(consommation_df)

                # Message de confirmation
                st.success(f"La facture a été enregistrée dans le dossier '{factures_dir}' sous le nom '{pdf_file_name}'.")
    
    # Mouvement de caise
    if option == "Mouvement de la caisse":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(caisse_logo_path, width=100)
            with col2:
                st.header("Mouvements de la Caisse")

            # Création de la vue Mouvements_Caisse
            cursor.execute('''
            CREATE VIEW IF NOT EXISTS Mouvements_Caisse AS
            SELECT 
                N_contrat AS ID, 
                Date_payement AS Date_Mouvement, 
                'Adhision' AS Motif, 
                Mnt_paye AS Montant,
                NULL AS Gestion,  -- Ajout de la colonne Gestion avec NULL pour les autres tables
                NULL AS Perte     -- Ajout de la colonne Perte avec NULL pour les autres tables
            FROM Abonnement
            UNION ALL
            SELECT 
                N_contrat AS ID, 
                Date_payement AS Date_Mouvement, 
                'Consommation' AS Motif, 
                Mnt_paye AS Montant,
                Gestion,  -- Colonne Gestion de Pay_Consommation
                Perte     -- Colonne Perte de Pay_Consommation
            FROM Pay_Consommation
            UNION ALL
            SELECT 
                ID_Payment AS ID, 
                Date_Reglement AS Date_Mouvement, 
                'ONEP' AS Motif, 
                Mnt_paye AS Montant,
                NULL AS Gestion,  -- Ajout de la colonne Gestion avec NULL pour les autres tables
                NULL AS Perte     -- Ajout de la colonne Perte avec NULL pour les autres tables
            FROM ONEP_Payment
            UNION ALL
            SELECT 
                ID_Maintenance AS ID, 
                Date_operation AS Date_Mouvement, 
                'Maintenance' AS Motif, 
                Mnt_ouvrier AS Montant,
                NULL AS Gestion,  -- Ajout de la colonne Gestion avec NULL pour les autres tables
                NULL AS Perte     -- Ajout de la colonne Perte avec NULL pour les autres tables
            FROM Maintenance
            UNION ALL
            SELECT 
                ID_Achat AS ID, 
                Date_Achat AS Date_Mouvement, 
                'Charge Materiel' AS Motif, 
                abs(Montant_total) AS Montant,
                NULL AS Gestion,  -- Ajout de la colonne Gestion avec NULL pour les autres tables
                NULL AS Perte     -- Ajout de la colonne Perte avec NULL pour les autres tables
            FROM Produit_Acheter
            ''')

            # Récupérer les données de la vue Mouvements_Caisse, classées par date
            query = "SELECT * FROM Mouvements_Caisse ORDER BY Date_Mouvement ASC"
            mouvements = pd.read_sql_query(query, conn)
            
            # Convertir la colonne de date en format datetime et enlever l'heure
            mouvements['Date_Mouvement'] = pd.to_datetime(mouvements['Date_Mouvement']).dt.date

            # Ajouter les colonnes 'Débit' et 'Crédit' au DataFrame
            mouvements['Débit'] = mouvements.apply(
                lambda row: row['Montant'] if row['Motif'] in ['Adhision', 'Consommation'] else None,
                axis=1
            )

            mouvements['Crédit'] = mouvements.apply(
                lambda row: abs(row['Montant']) if row['Motif'] not in ['Adhision', 'Consommation'] else None,
                axis=1
            )

            # Remplacer les valeurs None par des zéros pour une meilleure lisibilité
            #mouvements['Débit'] = mouvements['Débit'].fillna(0)
            #mouvements['Crédit'] = mouvements['Crédit'].fillna(0)

            # Supprimer la colonne Montant, car elle n'est plus nécessaire
            mouvements = mouvements.drop(columns=['Montant'])

            # Afficher le tableau modifié avec Streamlit
            st.dataframe(mouvements[['Date_Mouvement','Motif','Débit','Crédit']], height=400)

            col4,col5,col6 = st.columns(3)
            Gestion_total = mouvements['Gestion'].fillna(0).sum()
            Perte_total = mouvements['Perte'].fillna(0).sum()

            # Calcule de entre et sortie et difference
            col1,col2,col3 = st.columns(3)
            # Calcul de l'Entrée (montants positifs), Sortie (montants négatifs), et Différence
            Débit = (mouvements['Débit'] - mouvements['Gestion'].fillna(0) - mouvements['Perte'].fillna(0)).sum()
            Crédit = mouvements['Crédit'].sum()
            Solde = Débit +Gestion_total +Perte_total -Crédit



            # Affichage des résultats dans les colonnes
            col1.success(f"💰 Débit : {Débit:,.2f} MAD")
            col2.error(f"📤 Crédit : {Crédit:,.2f} MAD")
            col3.warning(f"⚖️ Solde : {Solde:,.2f} MAD")
            col4.info(f"🔄 Gestion : {Gestion_total:,.2f} MAD")
            col5.info(f"❌ Perte : {Perte_total:,.2f} MAD")

            st.subheader("Filtrages")
            col1,col2,col3 = st.columns(3)

            # Filtre pour le mois et l'année
            annees = mouvements['Date_Mouvement'].apply(lambda x: x.year).unique()
            mois = ["Tous"] + list(range(1, 13))  # Ajout de l'option "Tous" pour les mois

            annee_selection = col1.selectbox("Sélectionnez une année", sorted(annees), index=0)
            mois_selection = col2.selectbox("Sélectionnez un mois", mois, index=0, format_func=lambda x: "Tous" if x == "Tous" else f"{x:02d}")

            # Filtrage des données en fonction de l'année, le mois et le motif
            mouvements_filtrees = mouvements[mouvements['Date_Mouvement'].apply(lambda x: x.year) == annee_selection]

            # Appliquer le filtre de mois uniquement si un mois spécifique est sélectionné
            if mois_selection != "Tous":
                mouvements_filtrees = mouvements_filtrees[mouvements_filtrees['Date_Mouvement'].apply(lambda x: x.month) == mois_selection]

            # Filtre pour le motif
            motifs = mouvements['Motif'].unique()
            motif_selection = col3.selectbox("Sélectionnez un motif", ["Tous"] + list(motifs), index=0)
            
            if motif_selection != "Tous":
                mouvements_filtrees = mouvements_filtrees[mouvements_filtrees['Motif'] == motif_selection]

            # Affichage du tableau filtré
            st.dataframe(mouvements_filtrees[['Date_Mouvement','Motif','Débit','Crédit']])

            col4,col5,col6 = st.columns(3)
            Gestion_total_f = mouvements_filtrees['Gestion'].sum()
            Perte_total_f = mouvements_filtrees['Perte'].sum()
            
            col1,col2,col3 = st.columns(3)
            # Calcul de l'Entrée (montants positifs), Sortie (montants négatifs), et Différence
            Débit_f = (mouvements_filtrees['Débit'] - mouvements_filtrees['Gestion'].fillna(0) - mouvements_filtrees['Perte'].fillna(0)).sum()
            Crédit_f = mouvements_filtrees['Crédit'].sum()
            Solde_f = Débit_f +Gestion_total_f +Perte_total_f -Crédit_f

            

            # Affichage des résultats dans les colonnes
            col1.success(f"💰 Débit : {Débit_f:,.2f} MAD")
            col2.error(f"📤 Crédit : {Crédit_f:,.2f} MAD")
            col3.info(f"⚖️ Différence : {Solde_f:,.2f} MAD")
            col4.info(f"🔄 Gestion : {Gestion_total_f:,.2f} MAD")
            col5.info(f"❌ Perte : {Perte_total_f:,.2f} MAD")

    # Comparer comsomation du nlock avec les abonnes
    if option == "Vérification Consommation":
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(verification_logo_path, width=100)
            with col2:
                st.title("Consommation Par Block")
            
            # Colonnes pour les sélections utilisateur
            col1, col2 = st.columns(2)
            N_Block = col1.selectbox("Nº Block :", list(range(1, 16)))
            
            # Ajouter l'option "Tous" dans la sélection des mois
            mois_options = ['Tous'] + [f'{month:02d}-{datetime.now().year}' for month in range(1, 13)]
            Mois_choisi = col2.selectbox("Mois de consommation :", mois_options)
            
            # Préparer les conditions SQL en fonction de l'option choisie
            mois_condition = ""
            params = [N_Block]
            
            if Mois_choisi != "Tous":
                mois_condition = "AND strftime('%m-%Y', Date_consome) = ?"
                params.append(Mois_choisi)
            
            # Requête SQL pour les données du block
            blocks_query = f'''
                SELECT 
                    Block_ID AS N_Block,
                    strftime('%m-%Y', Date_consome) AS Mois_Annee,
                    Index_m3,
                    Index_m3 - COALESCE(
                        LAG(Index_m3) OVER (
                            PARTITION BY Block_ID
                            ORDER BY strftime('%Y-%m', Date_consome)
                        ), 0
                    ) AS Qte_consome
                FROM Blocks
            WHERE 
                Block_ID = ?
                {mois_condition}
            '''
            blocks_df = pd.read_sql_query(blocks_query, conn, params=params)
            
            # Requête SQL pour les données des abonnés
            conso_query = f'''
            SELECT 
                qc.N_contrat,
                ip.Nom,
                ip.N_conpteur_B AS N_Block,
                strftime('%m-%Y', qc.Date_consome) AS Mois_Consome,
                qc.Quantite AS Index_m3,
                qc.Quantite - COALESCE(
                    LAG(qc.Quantite) OVER (
                        PARTITION BY qc.N_contrat
                        ORDER BY strftime('%Y-%m', qc.Date_consome)
                    ), 0
                ) AS Qte_consome
            FROM 
                Qte_Consommation qc
            JOIN 
                info_personne ip ON ip.N_contrat = qc.N_contrat
            WHERE 
                ip.N_conpteur_B = ?
                {mois_condition}
            '''
            df2 = pd.read_sql_query(conso_query, conn, params=params)
        
            # Affichage des données
            st.dataframe(df2)
            
            # Calculs et affichage des résultats
            col1, col2 = st.columns(2)
            index_block = blocks_df['Index_m3'].sum() if not blocks_df.empty else 0
            sum_index_abonne = df2['Qte_consome'].sum() if not df2.empty else 0
            col1.info(f"Qte Compteur Block = {index_block} m3")
            col2.info(f"Consommation Totale = {sum_index_abonne} m3")

    # Fermer la connexion à la base de données
    conn.close()




