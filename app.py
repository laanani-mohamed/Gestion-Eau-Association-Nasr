import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# Connexion à la base de données
#db_path = 'Gestion_eau.db'
db_path = os.path.join(os.path.dirname(__file__), 'Gestion_eau.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Utilisation de la barre latérale pour le menu de sélection
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


def champs_remplis(*args):
    return all(arg not in ("", None) for arg in args)


##################################################################################################################
# Requête SQL pour obtenir les données nécessaires pour Consommation Historique & Payement
query1 = '''
    SELECT 
        q.N_contrat,
        strftime('%Y-%m', q.Date_consome) AS Mois_Consome,
        q.Date_consome,
        q.Quantite AS Index_m3,
        COALESCE(q.Quantite - LAG(q.Quantite) OVER (PARTITION BY q.N_contrat ORDER BY q.Date_consome), q.Quantite) AS Qte_Consomme_m3,
        (COALESCE(q.Quantite - LAG(q.Quantite) OVER (PARTITION BY q.N_contrat ORDER BY q.Date_consome), q.Quantite) * 7) AS Montant_dh
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
df_merged['Crédit'] = df_merged['Montant_dh'] - df_merged['Montant_paye'].where(df_merged['Montant_paye'].notna(), 0)

# Affichage du DataFrame d'origine
data_f = df_merged[['N_contrat', 'Mois_Consome', 'Date_réglement', 'N_recue', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Montant_paye','Crédit']]
data_ff = df_merged[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Montant_paye','Crédit']]
##################################################################################################################


# Ajouter un nouveau abonné
if option == "Ajouter un nouveau abonné":
    st.subheader("Ajouter un nouveau abonné")
    N_contrat = st.text_input("Nº de contrat :")
    Nom = st.text_input("Nom Complet :")
    N_conpteur_B = st.selectbox("Nº compteur Block :", list(range(1, 16)))
    N_conpteur_P = st.text_input("Nª compteur Personnel :")
    Mnt_due = st.number_input("Frais d'adhision :", min_value=0.0)
    Date_Adhesion = st.date_input("Date d'adhision : ")
    Adresse = st.text_input("Adresse :")
    
    if st.button("Enregistrer"):
        if champs_remplis(N_contrat, N_conpteur_B, N_conpteur_P, Nom, Mnt_due, Date_Adhesion, Adresse):
            cursor.execute('''
                INSERT INTO info_personne (N_contrat, N_conpteur_B, N_conpteur_P, Nom, Mnt_due, Date_Adhesion, Adresse)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (N_contrat, N_conpteur_B, N_conpteur_P, Nom, Mnt_due, Date_Adhesion, Adresse))
            conn.commit()
            st.success("Nouveau abonné ajouté avec succès !")
        else:
            st.warning("Il y a des informations manquantes. Veuillez remplir tous les champs.")

# Liste des abonnés avec colonne "Credit" calculée
if option == "Liste des abonnés":
    st.subheader("Liste des abonnés ")
    
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
    st.dataframe(data)

    # Ajout des filtres dynamiques en bas
    st.markdown("## Filtrer")
    filtered_data = data.copy()  # Copie du DataFrame pour appliquer les filtres
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
    st.title("Saisir une consommation")
    option2 = st.selectbox("Choisissez une option :", ["Consommation Abonné","Consommation Block"])
    
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
            INSERT INTO Qte_Consommation (N_contrat, Date_consome, Quantite)
            VALUES (?, ?, ?)
            '''
            # Exécution de la requête avec les valeurs saisies
            conn.execute(insert_query, (N_contrat, Date_consome, Quantite))
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
    st.subheader("Paiement d'abonnement")
    
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
        st.error(f"Montant payé dépasse crédit {Credit:.2f} dh. Veuillez corriger.")
    Date_payement = st.date_input("Date de régelement :")
    if st.button("Enregistrer paiement"):
        if champs_remplis(N_contrat, N_recue, Mnt_paye, Date_payement):
            cursor.execute('''
                INSERT INTO Abonnement (N_contrat, N_recue, Mnt_paye, Date_payement)
                VALUES (?, ?, ?, ?)
            ''', (N_contrat, N_recue, Mnt_paye, Date_payement))
            conn.commit()
            st.success("Paiement d'abonnement enregistré avec succès !")
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
    st.subheader("Paiement de consommation")
    
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
            INSERT INTO Pay_Consommation (N_contrat, Mnt_paye, N_recue, Date_paye, Date_payement)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(insert_query, (N_contrat, Mnt_paye, N_recue, Date_paye, Date_payement))
            conn.commit()
            st.success("Le paiement a été enregistré avec succès.")
        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")


    # Filtrer pour N_contrat sélectionné et Crédit != 0
    df_filtered = data_ff[(df_merged['N_contrat'] == N_contrat) & (df_merged['Crédit'] != 0)]
    df_grouped = df_filtered.groupby(['N_contrat', 'Mois_Consome', 'Montant_dh']).agg({
    'Montant_paye': 'sum'
    }).reset_index()

    # Calculer le crédit restant par mois en fonction des paiements
    df_grouped['Crédit_rest'] = df_grouped['Montant_dh'] - df_grouped['Montant_paye']
    df_grouped = df_grouped[df_grouped['Crédit_rest'] != 0]  # Garde les factures non payées

    # Joindre pour obtenir le détail complet des colonnes originales
    df_final = df_filtered.merge(df_grouped[['N_contrat', 'Mois_Consome', 'Crédit_rest']], on=['N_contrat', 'Mois_Consome'], how='inner')

    N_mois = df_final['Mois_Consome'].nunique()
    # Afficher l'historique de consommation avec le crédit différent de 0
    col1,col2 = st.columns(2)
    if not df_final.empty:
        st.write("### Les factures Non payées :")
        st.dataframe(df_final[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Montant_paye', 'Crédit_rest']])
        Sum_credit = df_final['Crédit_rest'].sum()
        col1.warning(f"Crédit Totale = {Sum_credit} dh")
        col2.warning(f"Nº mois Non Payé : {N_mois}")
    else:
        col1.warning("L'abonné est à jour.")

# Section Historique de consommation & Paiement
if option == "Historique consommation & Paiment":
    st.subheader("Historique de consommation & Paiment")

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
                FROM Achat
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
        date_utilise = st.date_input("Date d'utilisation", value=datetime.today())
        quantite_utilise = st.number_input("Quantité Utilisée", min_value=0.0, format="%.2f")
        Description = st.text_input("Déscription")

        # Bouton de soumission
        submit = st.button("Enregistrer l'achat")

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
    st.subheader("Situation Avec ONEP")
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

    option = st.selectbox("Choisissez une option :", ["Payer ONEP", "Crédit ONEP"])
    
    if option == "Payer ONEP":
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
    st.title("Gestion de la Maintenance")

    # Option d'insertion d'une nouvelle opération de maintenance
    st.subheader("Nouvelle Opération de Maintenance")

    # Saisie des informations principales pour l'opération de maintenance
    date_operation = st.date_input("Date de l'opération", value=datetime.today())
    description = st.text_area("Description de l'opération")
    nom_ouvrier = st.text_input("Nom de l'ouvrier")
    mnt_ouvrier = st.number_input("Montant payé à l'ouvrier (DH)", min_value=0.0, format="%.2f")

    # Saisie des produits utilisés et des quantités associées
    st.subheader("Produits Utilisés")

    # Récupérer les noms de produits depuis la table Produit
    cursor.execute("SELECT Nom_Produit FROM Produit")
    produits = [row[0] for row in cursor.fetchall()]  # Extraire les noms de produits dans une liste

    # Initialisation des listes pour les noms et quantités de produits
    # Stockage de la liste des produits utilisés dans la session
    if 'produits_utilises' not in st.session_state:
        st.session_state.produits_utilises = []

    # Interface pour ajouter des produits et quantités à l'opération
    nom_produit = st.selectbox("Nom du produit", options=produits)
    quantite_produit = st.number_input("Quantité utilisée", min_value=0.0, format="%.2f")
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
    st.title("Générer une facture de paiement")
    def generer_facture_pdf(n_contrat):
        # Requête pour obtenir les détails des consommations pour le contrat donné
        query = f'''
            SELECT N_contrat, Date_consome, Quantite
            FROM Qte_Consommation
            WHERE n_contrat = '{n_contrat}'
            ORDER BY Date_consome DESC
            LIMIT 1
        '''
        result = cursor.execute(query).fetchall()
        
        # Requête pour obtenir le montant d'adhésion et le crédit restant
        query_adhision = f'''
            SELECT 
                info_personne.N_contrat,
                info_personne.Mnt_due AS Montant_Adhision,
                COALESCE(info_personne.Mnt_due - SUM(Abonnement.Mnt_paye), info_personne.Mnt_due) AS Credit        
            FROM 
                info_personne
            LEFT JOIN 
                Abonnement 
            ON 
                info_personne.N_contrat = Abonnement.N_contrat
            WHERE 
                info_personne.N_contrat = '{n_contrat}'
            GROUP BY 
                info_personne.N_contrat, info_personne.Mnt_due
        '''
        result_adhidion = cursor.execute(query_adhision).fetchall()

        if result_adhidion:
            credit_Adhision, credit = result_adhidion[0][1], result_adhidion[0][2]  # Extraire les valeurs
        else:
            credit_Adhision, credit = 0, 0  # Valeurs par défaut si aucune donnée

        if result:
            previous_quantity = 0
            total_quantity_consumed = 0
            details = []
            
            # Traitement des données pour calculer les quantités consommées
            for i, (date_consomation, quantity) in enumerate(result):
                date_consomation = datetime.strptime(date_consomation, '%Y-%m-%d').strftime('%m/%Y')
                
                if previous_quantity is not None:
                    quantity_consumed = quantity - previous_quantity
                    total_quantity_consumed += quantity_consumed
                    details.append((date_consomation, previous_quantity, quantity, quantity_consumed))
                
                previous_quantity = quantity

            # Calcul du montant à payer
            amount_to_pay = (7 * total_quantity_consumed) + 15

            # Création de la facture avec ReportLab
            pdf = FPDF()
            pdf.add_page()

            # Titre de la facture
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Facture de Paiement", ln=True, align='C')

            # Détails du contrat et du montant
            pdf.set_font("Arial", '', 12)
            pdf.ln(10)  # Espacement
            pdf.cell(100, 10, f"N° Contrat : {n_contrat}")
            pdf.ln(10)
            pdf.cell(100, 10, f"N° Recu : {n_recu}")
            pdf.ln(10)
            pdf.cell(100, 10, f"Mois de consommation : {date_consomation} ")
            pdf.ln(10)
            pdf.cell(100, 10, f"Quantité Consommée : {total_quantity_consumed}")
            pdf.ln(10)
            pdf.cell(100, 10, f"Montant à Payer : {amount_to_pay} dh")
            pdf.ln(10)
            pdf.cell(100, 10, f"Crédit Adhision : {credit} dh")
            pdf.ln(10)
            pdf.cell(100, 10, f"Crédit Adhision à payé : {credit_Adhision_a_paye} dh")
            pdf.ln(10)
            pdf.cell(100, 10, f"Crédit de consommation à payé : {credit_consommation_a_paye} dh")
            pdf.ln(10)
            
            # Sauvegarder le fichier PDF
            pdf.output(f"facture_{n_contrat}.pdf")

            # Afficher un message de succès et permettre le téléchargement du fichier
            st.success(f"La facture a été générée avec succès : facture_{n_contrat}.pdf")
            st.download_button(f'Télécharger la facture_{n_contrat}', data=open(f'facture_{n_contrat}.pdf', 'rb'), file_name=f'facture_{n_contrat}.pdf')

        else:
            st.error("Aucune consommation trouvée pour ce numéro de contrat.")

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
    n_recu = st.selectbox("Nº Reçu :", list(range(1, 201)))
    credit_consommation_a_paye = st.number_input("Crédit consommation à payé :")
    credit_Adhision_a_paye = st.number_input("Crédit adhision à payé :")
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


    if st.button("Générer la facture"):
        generer_facture_pdf(n_contrat)

# Mouvement de caise
if option == "Mouvement de la caisse":
    st.header("Mouvements de la Caisse")

# Création de la vue Mouvements_Caisse
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS Mouvements_Caisse AS
    SELECT N_contrat AS ID, Date_payement AS Date_Mouvement, 'Adhision' AS Motif, Mnt_paye AS Montant
    FROM Abonnement
    UNION ALL
    SELECT N_contrat AS ID, Date_payement AS Date_Mouvement, 'Consommation' AS Motif, Mnt_paye AS Montant
    FROM Pay_Consommation
    UNION ALL
    SELECT ID_Payment AS ID, Date_Reglement AS Date_Mouvement, 'ONEP' AS Motif, Mnt_paye AS Montant
    FROM ONEP_Payment
    UNION ALL
    SELECT ID_Maintenance AS ID, Date_operation AS Date_Mouvement, 'Maintenance' AS Motif, Mnt_ouvrier AS Montant 
    FROM Maintenance
    UNION ALL
    SELECT ID_Achat AS ID, Date_Achat AS Date_Mouvement, 'Charge Materiel' AS Motif, -Montant_total AS Montant
    FROM Produit_Acheter
    ''')

    # Récupérer les données de la vue Mouvements_Caisse, classées par date
    query = "SELECT * FROM Mouvements_Caisse ORDER BY Date_Mouvement ASC"
    mouvements = pd.read_sql_query(query, conn)

    # Convertir la colonne de date en format datetime et enlever l'heure
    mouvements['Date_Mouvement'] = pd.to_datetime(mouvements['Date_Mouvement']).dt.date

    # Affichage initial des mouvements
    st.dataframe(mouvements, height=400)

    # Calcule de entre et sortie et difference
    col1,col2,col3 = st.columns(3)
    # Calcul de l'Entrée (montants positifs), Sortie (montants négatifs), et Différence
    entre_1 = mouvements[mouvements['Montant'] >= 0]['Montant'].sum()
    sortie_1 = abs(mouvements[mouvements['Montant'] < 0]['Montant'].sum())
    difference_1 = entre_1 - sortie_1

    # Affichage des résultats dans les colonnes
    col1.info(f"Entrée : {entre_1:.2f}")
    col2.info(f"Sortie : {sortie_1:.2f}")
    col3.warning(f"Différence : {difference_1:.2f}")


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
    st.dataframe(mouvements_filtrees)

    col1,col2,col3 = st.columns(3)
    # Calcul de l'Entrée (montants positifs), Sortie (montants négatifs), et Différence
    entre = mouvements_filtrees[mouvements_filtrees['Montant'] >= 0]['Montant'].sum()
    sortie = abs(mouvements_filtrees[mouvements_filtrees['Montant'] < 0]['Montant'].sum())
    difference = entre - sortie

    # Affichage des résultats dans les colonnes
    col1.info(f"Entrée : {entre:.2f}")
    col2.info(f"Sortie : {sortie:.2f}")
    col3.warning(f"Différence : {difference:.2f}")

# Comparer comsomation du nlock avec les abonnes
if option == "Vérification Consommation":
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


