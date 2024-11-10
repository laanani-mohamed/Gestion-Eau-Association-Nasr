import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Connexion à la base de données
db_path = 'Gestion_eau.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Menu de sélection pour l'utilisateur
option = st.selectbox("Choisissez une option :", [
    "Ajouter un nouveau abonné",
    "Liste des abonnés",
    "Saisir une consommation",
    "Paiement d'abonnement",
    "Paiement de consommation",
    "Historique consommation & Paiment",
    "Stock",
    "ONEP",
    "Charge Maintenance"
])

# Fonction pour vérifier si tous les champs sont remplis
def champs_remplis(*args):
    return all(arg not in ("", None) for arg in args)

#sns.barplot(data=my_data, x='YEAR', y='APPEARANCES')
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
data_f = df_merged[['N_contrat', 'Mois_Consome', 'Date_réglement', 'N_recue', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Crédit']]
data_ff = df_merged[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Crédit']]
##################################################################################################################


# Ajouter un nouveau abonné
if option == "Ajouter un nouveau abonné":
    st.subheader("Ajouter un nouveau abonné")
    N_contrat = st.text_input("Nº de contrat :")
    N_conpteur_B = st.text_input("Nº compteur Block :")
    N_conpteur_P = st.text_input("Nª compteur Personnel :")
    Nom = st.text_input("Nom Complet :")
    Mnt_due = st.number_input("Frais d'abonnement :", min_value=0.0)
    Date_Adhesion = st.date_input("Date d'adhésion : ")
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
elif option == "Saisir une consommation":
    st.subheader("Saisir une consommation")

    # Requête pour récupérer les N_contrat et les Noms associés
    query = '''
    SELECT N_contrat, Nom FROM info_personne
    '''
    # Charger les données dans un DataFrame
    data = pd.read_sql_query(query, conn)

    # Afficher uniquement le sélecteur pour le N_contrat
    N_contrat = st.selectbox("Nº de contrat :", data['N_contrat'].tolist())
    col1, col2 = st.columns(2)
    # Afficher le nom associé au N_contrat sélectionné
    selected_name = data[data['N_contrat'] == N_contrat]['Nom'].iloc[0]
    col1.info(f"Nom de l'abonné : {selected_name}")

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
        col2.info(f"Index précedent : {last_index} m³ pour {last_date.strftime('%m - %Y')}")
    else:
        col2.info("Aucune consommation enregistrée.")
    # Saisie de la quantité consommée
    Quantite = st.number_input("Nouveau Index :", min_value=0.0)

    # Saisie de la date de consommation
    Date_consome = st.date_input("Date de consommation :")


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

# Paiement d'abonnement
elif option == "Paiement d'abonnement":
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
elif option == "Paiement de consommation":
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

    # Afficher l'historique de consommation avec le crédit différent de 0
    if not df_filtered.empty:
        st.write("### Les factures Non payées :")
        st.dataframe(df_filtered[['N_contrat', 'Mois_Consome', 'Index_m3', 'Qte_Consomme_m3', 'Montant_dh', 'Crédit']])
        Sum_credit = df_filtered['Crédit'].sum()
        st.warning(f"Crédit Totale = {Sum_credit} dh")
    else:
        st.warning("L'abonné est à jour.")

# Section Historique de consommation & Paiement
elif option == "Historique consommation & Paiment":
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
elif option == "Stock":
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
elif option == "ONEP":
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
elif option == "Charge Maintenance":
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




# Fermer la connexion à la base de données
conn.close()
