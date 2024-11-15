import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy.stats import kstest, norm, ttest_1samp, shapiro
import scipy.stats

# data_URL = " https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data "

# Pour eviter tous les erreurs des plots
st.set_option('deprecation.showPyplotGlobalUse', False)

# Fonction pour verifier si la nature de la col est valide pour les mesures statistiques
def is_valid_column_for_statistic(data, selected_column):
    try:
        # Un essai pour calculer une mesure si ca marche ->True Sinn un msg erreur
        _ = data[selected_column].mean()
        return True
    except Exception:
        return False

# Fonction pour verifier si la nature de la col est valide pour les graphes
def is_valid_columns_for_chart(data, selected_x_column, selected_y_column):
    try:
        # Un essai pour creer un graphe si ca marche ->True Sinn un msg erreur
        plt.scatter(data[selected_x_column], data[selected_y_column])
        plt.close()  # Close the plot to avoid displaying it
        return True
    except Exception:
        return False

# Fonction pour verifier si la nature des cols sont valide pour heatmap
def are_valid_columns_for_heatmap(data, selected_columns):
    valid_columns = []
    invalid_columns = []
    for column in selected_columns:
        try:
            # Vérifier si la colonne est numérique (quantitative)
            if pd.api.types.is_numeric_dtype(data[column]):
                # Tentative de récupération des valeurs uniques pour vérifier la compatibilité
                unique_values = data[column].unique()
                valid_columns.append(column)
            else:
                invalid_columns.append(column)
        except Exception:
            invalid_columns.append(column)

    if not valid_columns:
        return [], [], "Aucune colonne valide pour le heatmap."
    elif len(valid_columns) < 2:
        message = f"Sélectionnez au moins deux colonnes pour le graphe."
        if invalid_columns:
            if len(invalid_columns)>= 2:
                message = f"Les colonnes {', '.join(invalid_columns)} ne sont pas compatibles avec le graphe. "
            else:
                message = f"La colonne {', '.join(invalid_columns)} n'est pas compatible avec le graphe. "            
                
        return [], [], message
    elif invalid_columns:
        if len(invalid_columns)>= 2:
            message = f"Les colonnes {', '.join(invalid_columns)} ne sont pas compatibles avec le graphe. "
        else:
            message = f"La colonne {', '.join(invalid_columns)} n'est pas compatible avec le graphe. "            
        return valid_columns, invalid_columns, message
    else:
        return valid_columns, invalid_columns, ""

# Fonction pour filtrer et afficher et retourner un tab filtree
def filtrer_et_afficher(result_data):
    # Initialiser un dictionnaire pour stocker les choix de filtrage
    filters = {}

    # Créer des widgets de sélection pour chaque colonne
    for column in result_data.columns:
        unique_values = result_data[column].unique()
        
        should_filter = st.checkbox(f"Filtrer par #{column}. ")
        
        if should_filter:
            selected_value = st.selectbox(f"Sélectionnez une valeur pour  #{column}:", unique_values)
            filters[column] = selected_value

    # Appliquer le filtre
    filtered_data = result_data
    for column, value in filters.items():
        filtered_data = filtered_data[filtered_data[column] == value]

    # Afficher les données filtrées
    if not filtered_data.empty:
        st.subheader("Affichage des lignes filtrées :")
        return filtered_data
    else:
        st.warning("Aucune ligne correspondant aux critères de filtrage n'a été trouvée.")

# Fonction pour le choix du test
def choisir_test(data):
    # Déterminer la taille de l'échantillon
    taille_echantillon = len(data)
    if taille_echantillon >= 30:
        return "Z"
    else:
        return "T"

# Fonction du test_Z
def test_Z(echantillon, moyenne_population, ecart_type_population_Z, alpha, alternative):
    # Calcul de la moyenne et de l'écart-type de l'échantillon
    moyenne_echantillon = np.mean(echantillon)
    # Taille de l'échantillon
    taille_echantillon = len(echantillon)
    # Calcul de la valeur Z
    Z = round((moyenne_echantillon - moyenne_population) / (ecart_type_population_Z / np.sqrt(taille_echantillon)), 4)
    
    # Calcul de la valeur critique (seuil de significativité)
    if alternative == "Bilatéral":
        Z_critic = round(scipy.stats.norm.ppf(1 - alpha/2), 4)
    elif alternative == "à Droite":
        Z_critic = round(scipy.stats.norm.ppf(1 - alpha), 4)
    elif alternative == "à Gauche":
        Z_critic = round(-scipy.stats.norm.ppf(1 - alpha), 4)
    else:
        raise ValueError("L'argument alternative doit être 'Bilatéral' , 'à Droite' , 'à Gauche'")
    
    # Détermination de la région d'acceptation et de rejet
    if alternative == "Bilatéral":
        if abs(Z) <= Z_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    elif alternative == "à Droite":
        if Z <= Z_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    elif alternative == "à Gauche":
        if Z >= Z_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    
    return Z, Z_critic, result

# Fonction du test_T
def test_T(echantillon, moyenne_population, ecart_type_population_T, alpha, alternative):
    # Calcul de la moyenne et de l'écart-type de l'échantillon
    moyenne_echantillon = np.mean(echantillon)
    # Taille de l'échantillon
    taille_echantillon = len(echantillon)
    # Calcul de la valeur T
    T = round((moyenne_echantillon - moyenne_population) / (ecart_type_population_T / np.sqrt(taille_echantillon)), 4)
    
    # Calcul de la valeur critique (seuil de significativité)
    if alternative == "Bilatéral":
        T_critic = round(scipy.stats.t.ppf(1 - alpha/2, df=taille_echantillon-1), 4)
    elif alternative == "à Droite":
        T_critic = round(scipy.stats.t.ppf(1 - alpha, df=taille_echantillon-1), 4)
    elif alternative == "à Gauche":
        T_critic = round(-scipy.stats.t.ppf(1 - alpha, df=taille_echantillon-1), 4)
    else:
        raise ValueError("L'argument 'alternative' doit être 'Bilatéral' , 'à Droite' , 'à Gauche'")
    
    # Détermination de la région d'acceptation et de rejet
    if alternative == "Bilatéral":
        if abs(T) <= T_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    elif alternative == "à Droite":
        if T <= T_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    elif alternative == "à Gauche":
        if T >= T_critic:
            result = "Accepter"
        else:
            result = "Rejeter"
    
    return T, T_critic, result


# Interface Streamlit
def main():
    st.markdown("<h1 style='text-align: center;'>Analyse Intéractive des données </h1>", unsafe_allow_html=True)

####Choix de la source de données (Téléchargement ou Lien)
    data_source = st.radio("Source de données :", ('Téléchargement', 'Lien'))

    if data_source == 'Téléchargement':
        # Créer deux colonnes pour afficher les éléments en colonne
        col1, col2 = st.columns([2, 1])

        # Sélection du type de fichier (CSV, XLSX, ou TXT)
        file_type = col1.selectbox("Sélectionnez le type de fichier :", ['CSV', 'XLSX', 'TXT'])

        # Si c'est un fichier texte, permettre la sélection du séparateur
        if file_type in ['CSV', 'TXT']:
            # Entrez le séparateur (par défaut: ,)
            separator = col2.text_input("Entrez le séparateur (par défaut: ,)", ",")

        # Téléchargement du fichier
        uploaded_file = st.file_uploader(f"Téléchargez un fichier {file_type}", type=[file_type.lower()])

        # Charger les données du fichier si disponible
        if uploaded_file is not None:
            try:
                if file_type == 'CSV':
                    data = pd.read_csv(uploaded_file, sep=separator)
                elif file_type == 'XLSX':
                    sheet_names = pd.ExcelFile(uploaded_file).sheet_names
                    selected_sheet_name = st.selectbox("Sélectionnez le nom de la page :", sheet_names, index=0)
                    data = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=selected_sheet_name)
                elif file_type == 'TXT':
                    data = pd.read_csv(uploaded_file, sep=separator)

                process_data(data)

            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier : {e}")

    elif data_source == 'Lien':
        col1, col2 = st.columns([2,1])
        # Saisie du lien vers les données
        data_url = col1.text_input("Entrez le lien vers les données :")
        separator = col2.text_input("Entrez le séparateur (par défaut: ,)", ",")
        if data_url:
                    try:
                        data = pd.read_csv(data_url, sep=separator)
                        process_data(data)
                    except Exception as e:
                        st.error(f"Erreur lors du chargement des données depuis le lien : {e}")

def process_data(data):
    st.write(3*"-")
    st.markdown("<h1 style='text-align: center;'>Explorez les données télechargés :</h1>", unsafe_allow_html=True)

#### Sélection des colonnes et lignes
    col1,col2 = st.columns(2)
    selected_columns = col1.multiselect("Sélectionnez les colonnes :", data.columns)
    selected_rows = col2.multiselect("Sélectionnez les lignes :", data.index)
    
    # Vérifier si les listes de colonnes et de lignes sont vides
    if not selected_columns:
        selected_columns = data.columns  # Afficher toutes les colonnes si aucune colonne n'est sélectionnée
    if not selected_rows:
        selected_rows = data.index  # Afficher toutes les lignes si aucune ligne n'est sélectionnée
        # Affichage du tableau résultant
    result_data = data.loc[selected_rows, selected_columns]
    st.write("Résultat du tableau :")
    st.write(result_data)
    st.write(3*"-")
    # Side Bare
    st.sidebar.subheader("Explorez vos données :")
    Choix = st.sidebar.radio('',['Filtrage des données', 'Mesures statistiques', 'Visualisez vos données', 'Tests Statistiques', 'Prédiction avec droite de regression simple']) 
    
    if Choix == 'Filtrage des données':
        st.markdown("<h1 style='text-align: center;'>Filtrage :</h1>", unsafe_allow_html=True)
        st.subheader("Choisire les filtres:")
        st.write(filtrer_et_afficher(result_data))


    elif Choix == 'Mesures statistiques':
        st.markdown("<h1 style='text-align: center;'>Calcule statistique :</h1>", unsafe_allow_html=True)
        
        col1,col2 = st.columns(2)
        col3,col4 = st.columns([2,1])

        # Sélecteur de mesures statistiques
        selected_statistics = col1.multiselect("Sélectionnez les mesures statistiques :", ('Moyenne', 'Mediane', 'Écart type', 'Min', 'Max', 'Étendue', 'Quartiles', 'Skewness'), key="selected_statistics")

        # Sélecteur de colonnes pour les mesures statistiques
        selected_statistic_columns = col2.multiselect("Sélectionnez les colonnes :", data.columns, key="selected_statistic_columns")

        # Sélecteur de colonnes catégoriques pour le filtre
        colonnes_categoriques = [''] + [colonne for colonne in data.columns if pd.api.types.is_object_dtype(data[colonne])]
        catg_filtre = col3.selectbox("Choix du filtre :", colonnes_categoriques)

        # Sélecteur des valeurs uniques dans la colonne catégorique pour le filtre
        if catg_filtre:
            selected_value = col4.selectbox("Choix de valeur :", data[catg_filtre].unique(), key="selected_value")
            # Appliquer le filtre
            data = data[data[catg_filtre] == selected_value]
            selected_rows = data.index
        else:
            selected_value = None
            selected_rows = data.index

        if not selected_statistic_columns:
            st.warning("Veuillez sélectionner au moins une colonne pour appliquer les mesures statistiques.")
        else:
            # Initialiser le DataFrame global pour stocker les résultats
            global_results = pd.DataFrame()

            for selected_statistic_column in selected_statistic_columns:
                if not is_valid_column_for_statistic(data, selected_statistic_column):
                    st.warning(f"La colonne #{selected_statistic_column} n'est pas valide pour les mesures statistiques.")
                else:
                    # Si aucune mesure statistique n'est sélectionnée, afficher toutes les mesures disponibles
                    if not selected_statistics:
                        selected_statistics = ['Moyenne', 'Mediane', 'Écart type', 'Min', 'Max', 'Étendue', 'Quartiles', 'Skewness']

                    results = {}

                    for selected_statistic in selected_statistics:
                        try:
                            if selected_statistic == 'Moyenne':
                                results['Moyenne'] = data.loc[selected_rows, selected_statistic_column].mean().round(2)
                            elif selected_statistic == 'Mediane':
                                results['Mediane'] = data.loc[selected_rows, selected_statistic_column].median()
                            elif selected_statistic == 'Écart type':
                                results['Écart type'] = data.loc[selected_rows, selected_statistic_column].std()
                            elif selected_statistic == 'Min':
                                results['Min'] = data.loc[selected_rows, selected_statistic_column].min()
                            elif selected_statistic == 'Max':
                                results['Max'] = data.loc[selected_rows, selected_statistic_column].max()
                            elif selected_statistic == 'Étendue':
                                results['Étendue'] = data.loc[selected_rows, selected_statistic_column].max() - data.loc[selected_rows, selected_statistic_column].min()
                            elif selected_statistic == 'Quartiles':
                                q1 = data[selected_statistic_column].quantile(0.25).round(2)
                                q2 = data[selected_statistic_column].quantile(0.5).round(2)
                                q3 = data[selected_statistic_column].quantile(0.75).round(2)
                                results['Q1 (25%)'] = q1
                                results['Q2 (50%)'] = q2
                                results['Q3 (75%)'] = q3
                            elif selected_statistic == 'Skewness':
                                results['Skewness'] = data.loc[selected_rows, selected_statistic_column].skew()

                        except Exception:
                            st.warning(f"Erreur : les valeurs présentes dans la colonne '{selected_statistic_column}' ne correspondent pas aux critères requis pour la mesure")

                    # Mettre à jour le DataFrame global
                    global_results = pd.concat([global_results, pd.DataFrame(results, index=[selected_statistic_column])])

            # Afficher les résultats dans un seul tableau
            st.subheader("Résultats:")
            st.table(global_results)


    elif Choix == 'Visualisez vos données':
        st.markdown("<h1 style='text-align: center;'>Visualisation :</h1>", unsafe_allow_html=True)
        
        Col,Coll = st.columns([100,1])
        # Sélection du type de graphique
        selected_chart_type = Col.selectbox("Sélectionnez le type de graphique :", ['Nuage des points', 'Barplot', 'Histogramme', 'Heatmap', 'Courbe', 'Boxplot', 'Pieplot'])
        
        # Saisie des colonnes pour les graphes
        if selected_chart_type == 'Heatmap':
            selected_x_columns = st.multiselect("Sélectionnez les colonnes pour l'axe X :", data.columns, key="heatmap_selected_x_columns")
        
        elif selected_chart_type == 'Courbe':
            ch = st.radio("Choisir:", ['Courbe à une variable', 'Courbe à deux variables'])
            numeric_columns = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col])] 
            if ch == 'Courbe à une variable':
                selected_x_column = st.selectbox("Saisissez la colonne X :", numeric_columns)   
            elif ch == 'Courbe à deux variables':  
                col1,col2 = st.columns(2)         
                selected_x_column = col1.selectbox("Saisissez la colonne X :", numeric_columns)
                selected_y_column = col2.selectbox("Saisissez la colonne Y :", numeric_columns)
                colonnes_categoriques = ['']+[colonne for colonne in data.columns if pd.api.types.is_object_dtype(data[colonne])]
                catg_filtre = st.selectbox("Faire un filtre :",colonnes_categoriques)
        
        elif selected_chart_type == 'Pieplot':
            col1,col2 = st.columns(2)  
            selected_x_column = col1.selectbox("Saisissez la valeur :", data.columns)
            selected_y_column = col2.selectbox("Saisissez la valeur catégorique :", data.columns)

        elif selected_chart_type == 'Histogramme':
            selected_x_column = st.selectbox("Saisissez la colonne de l'axe X :", data.columns)
            colonnes_categoriques = ['']+[colonne for colonne in data.columns if pd.api.types.is_object_dtype(data[colonne])]
            catg_filtre = st.selectbox("Faire un filtre :",colonnes_categoriques)
            chx = st.radio("Choisir:",['Sans KDE', 'Avec KDE', 'Seulement KDE'])

        elif selected_chart_type == 'Nuage des points':
            
            # selectionner seulement les valeurs non object
            col1,col2 = st.columns(2)  
            col_numerique = [colonne for colonne in data.columns if pd.api.types.is_numeric_dtype(data[colonne])]
            selected_x_column = col1.selectbox("Saisissez la colonne X :", col_numerique)
            selected_y_column = col2.selectbox("Saisissez la colonne Y :", col_numerique)
            
            # selectionner les filtre pour les valeur categorique (object)
            colonnes_categoriques = ['']+[colonne for colonne in data.columns if pd.api.types.is_object_dtype(data[colonne])]
            catg_filtre = st.selectbox("Faire un filtre :",colonnes_categoriques)
            
            # Droite de regression
            regretion = st.radio("Choisire",['Sans droite de Regression', 'Avec droite de Regression'])
            if regretion == 'Avec droite de Regression':
                reg='ols'
            elif regretion == 'Sans droite de Regression':
                reg=None
                   
        elif selected_chart_type == 'Boxplot':
            variable = st.radio("Choisire:", ['Une Variable', 'Deux variable'])
            numeric_column = [colonne for colonne in data.columns if pd.api.types.is_numeric_dtype(data[colonne])]
            if variable == 'Une Variable':
                selected_y_column = st.selectbox("Saisissez la colonne :", numeric_column)
            elif variable == 'Deux variable':
                col1,col2 = st.columns(2)
                selected_x_column = col1.selectbox("Saisissez la colonne X :", data.columns)
                selected_y_column = col2.selectbox("Saisissez la colonne Y :", data.columns)
            colonnes_categoriques = ['']+[colonne for colonne in data.columns if pd.api.types.is_object_dtype(data[colonne])]
            catg_filtre = st.selectbox("Faire un filtre :",colonnes_categoriques)
            
        elif selected_chart_type == 'Barplot':
                categorical_columns = [col for col in data.columns if pd.api.types.is_object_dtype(data[col])]
                selected_x_column = st.selectbox("Saisissez la colonne de l'axe X :", data.columns)
                colonnes_categoriques = ['']+[categorical_columns]
                catg_filtre = st.selectbox("Faire un filtre :",colonnes_categoriques)
 
        # Bouton pour afficher le graphique
        if st.button("Afficher le graphique"):
                    
            if selected_chart_type == 'Courbe':
                
                if ch == 'Courbe à une variable':                  
                    st.line_chart(data.loc[selected_rows , selected_x_column].value_counts())
                    st.markdown(f"**Axe X :** {selected_x_column}")
                    st.markdown("**Axe Y :** Nombre de répétitions")
                
                elif ch == 'Courbe à deux variables':
                    color_column = catg_filtre if catg_filtre else None
                    plt.figure(figsize=(10, 6))  # Ajustez la taille du graphe selon vos besoins
                    sns.lineplot(data=data.loc[selected_rows], x=selected_x_column, y=selected_y_column, hue=color_column)
                    # Ajouter des étiquettes et un titre
                    plt.xlabel(selected_x_column)
                    plt.ylabel(selected_y_column)
                    plt.legend()
                    # Afficher le graphique dans Streamlit
                    st.pyplot() 
                               
            elif selected_chart_type == 'Barplot':
                color_column = catg_filtre if catg_filtre else None
                filtered_data = data if not color_column else data[data[color_column].notnull()]  # Filtrer les données si une colonne catégorique est sélectionnée
                numeric_columns = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col])] 
                if selected_x_column in numeric_columns:
                    st.warning("La colonne selectionnée est de type numérique. Le graphe est utilisé géneralement pour les valeurs catégoriques.")
                if color_column:
                    # Grouper les données par la colonne catégorique et l'axe X, puis créer le graphique de barres
                    grouped_data = filtered_data.groupby([color_column, selected_x_column]).size().reset_index(name='count')
                    fig = px.bar(grouped_data, x=selected_x_column, y='count', color=color_column, barmode='group')
                else:
                    count_data = filtered_data[selected_x_column].value_counts().reset_index(name='count')
                    fig = px.bar(count_data, x='index', y='count')  # 'index' is the default name for the original index column
                st.plotly_chart(fig, use_container_width=True)

            elif selected_chart_type == 'Histogramme':
                color_column = catg_filtre if catg_filtre else None
              
                if chx == 'Sans KDE':
                    fig = px.histogram(data.loc[selected_rows], x=selected_x_column, labels={'x':selected_x_column}, color=color_column)
                    fig.update_layout(bargap=0.2)
                    # Afficher l'histogramme dans l'interface Streamlit
                    st.plotly_chart(fig, use_container_width=True)
                        
                elif chx == 'Avec KDE':
                    if  color_column:
                        st.warning("Supprimer le filtre")
                    else:       
                        if  is_valid_column_for_statistic:
                            try:       
                                fig, ax = plt.subplots()
                                sns.histplot(data=data.loc[selected_rows], x=selected_x_column, kde=True)    
                                st.pyplot(fig)
                            except:
                                st.warning("La colonne sélectionnée ne contient pas des valeurs numériques.") 
                      
                elif chx == 'Seulement KDE':
                    if  not color_column:
                        if  is_valid_column_for_statistic:
                            try:    
                                fig, ax = plt.subplots()
                                sns.kdeplot(data.loc[selected_rows,selected_x_column], fill=True)
                                st.pyplot(fig)
                            except:
                                st.warning(f"La colonne sélectionnée ne contient pas des valeurs numériques.")
                    else:
                        st.warning("Supprimer le filtre")

            elif selected_chart_type == 'Heatmap':
                valid_columns, invalid_columns, message = are_valid_columns_for_heatmap(data, selected_x_columns)
                # Afficher un message si certaines colonnes ne sont pas valides
                if message:
                    st.warning(message)
                else:
                    # Créer le heatmap si toutes les colonnes sont valides
                    try:
                        fig, ax = plt.subplots()
                        correlation_matrix = data[valid_columns].corr()
                        sns.heatmap(correlation_matrix, annot=True, cmap='YlGnBu', ax=ax)
                        st.pyplot(fig)
                    except Exception:
                        st.write("Une erreur s'est produite lors de la création du heatmap.")
                    
            elif selected_chart_type == 'Nuage des points':
                if not is_valid_columns_for_chart(data, selected_x_column, selected_y_column):
                    st.warning(f"Les colonnes sélectionnées ne sont pas compatibles avec le type de graphique choisi.")
                else:
                    color_column = catg_filtre if catg_filtre else None
                    fig = px.scatter(data_frame=data.loc[selected_rows] , x=selected_x_column, y=selected_y_column, trendline=reg, labels={'x':selected_x_column, 'y':selected_y_column}, color=color_column)
                    st.plotly_chart(fig,use_container_width = True)
                    
            elif selected_chart_type == 'Boxplot': 
                color_column = catg_filtre if catg_filtre else None
                
                if variable == 'Une Variable':
                    fig = px.box(data.loc[selected_rows], y=selected_y_column,labels={'y':selected_y_column}, color=color_column)
                    fig.update_traces(quartilemethod="linear") # or "inclusive", or "linear" by default
                    
                elif variable == 'Deux variable':
                    fig = px.box(data.loc[selected_rows], x=selected_x_column, y=selected_y_column,labels={'x':selected_x_column, 'y':selected_y_column}, color=color_column)
                    fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default
                st.plotly_chart(fig, use_container_width=True)
                                
            elif selected_chart_type == 'Pieplot':
                y_is_numeric = pd.api.types.is_numeric_dtype(data[selected_y_column])
                x_is_categorical = pd.api.types.is_object_dtype(data[selected_x_column])

                if y_is_numeric and x_is_categorical:
                    st.warning("X contient des valeurs catégorique // Y contient des valeurs numériques, INVERSER les colonnes")
                elif y_is_numeric:
                    st.warning("Colonne Y contient des valeurs numériques, généralement est dédier à des valeurs catégoriques.")
                elif x_is_categorical:
                    st.warning("Colonne X contient des valeurs catégorique, généralement est dédier à des valeurs numériques.")
                
                color_palette = 'set1'
                fig = px.pie(data.loc[selected_rows], values=selected_x_column, names=selected_y_column, hole=.3, color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)


    elif Choix == 'Tests Statistiques':
        st.markdown("<h1 style='text-align: center;'>Teste statistique :</h1>", unsafe_allow_html=True)
        st.subheader("Choisir les filtres pour créer un échantillion:")
        
        data_filtre= filtrer_et_afficher(result_data)
        st.write(data_filtre)

        st.subheader("Choisir la colonne pour le test")
        numeric_columns_population = [col for col in result_data.columns if is_valid_column_for_statistic(result_data, col)]
        colonne_choisie_population = st.selectbox("Choisir la colonne:", numeric_columns_population)        
        echantillion = data_filtre[colonne_choisie_population]
        
        # TEST_Z

        if choisir_test(echantillion) == 'Z':
            st.subheader("_ _ _ _ TEST Z _ _ _ _")
            
            # tester la normalite des donnees
            st.subheader("Tester la normalité des données")
            test_norm = st.radio("Choisire la methode", ['Distibution', 'Teste de Kolmogorov-Smirnov'])
            
            if test_norm == 'Distibution':
                sns.kdeplot(echantillion, fill=True)
                #plt.hist(echantillion, bins='auto', density=True)
                st.pyplot(plt)
            
            elif test_norm == 'Teste de Kolmogorov-Smirnov':
                stat, p_value = kstest(echantillion, 'norm')
                st.subheader("Résultat:")
                st.write(f"Statistique de test D : {stat}")
                st.write(f"Valeur p : {p_value}")
                if p_value > 0.05:
                    st.warning("Les données suivent une distribution normale (p > 0.05)")
                else:
                    st.warning("Les données ne suivent pas une distribution normale (p <= 0.05)")
                
            # Continuer le test
            continuer_test_Z = st.radio("Continuer le test",['Non', 'Oui'])
           
            if continuer_test_Z == 'Oui':
                st.subheader("Test Z sur la moyenne de l'échantillon:")
                alternative = st.radio("Nature du test :",['Bilatéral', 'à Gauche', 'à Droite'])

                moyenne_population_Z = result_data[colonne_choisie_population].mean()
                ecart_type_population_Z = result_data[colonne_choisie_population].std()
                Z, Z_critic, result = test_Z(echantillion, moyenne_population_Z, ecart_type_population_Z, 0.05, alternative)               
                
                # Afficher les résultats
                st.subheader("_ _ _ _Résultat_ _ _ _")
                st.write(f"Valeur de Z =  {Z}")
                st.write(f"Valeur de Zc = {Z_critic}")
                
                st.subheader("_ _ _ _Conclusion_ _ _ _")
                
                # Interprétation du test
                if result == 'Rejeter' :
                    st.warning("Rejeter l'hypothèse nulle :")
                    #st.warning("La moyenne de l'échantillon est significativement différente de la moyenne de la population.")
                elif result == 'Accepter':
                    st.warning("Accepter l'hypothèse nulle :")
                
                # Intervale de confiance
                st.subheader("_ _ _ _Intervale de confiance_ _ _ _")
                choix_ic = st.radio("choisire:", ['Non', 'Oui'])

                if choix_ic == 'Oui':

                    if alternative == 'Bilatéral':
                        # Interval de confiance bilatéral
                        IC_inf_Z = round(np.mean(echantillion) - Z_critic * (ecart_type_population_Z / np.sqrt(len(echantillion))), 2)
                        IC_sup_Z = round(np.mean(echantillion) + Z_critic * (ecart_type_population_Z / np.sqrt(len(echantillion))), 2)

                    elif alternative == 'à Gauche':
                        IC_inf_Z = float('-inf')
                        IC_sup_Z = round(echantillion.mean() + Z_critic * (ecart_type_population_Z / np.sqrt(len(echantillion))), 2)

                    elif alternative == 'à Droite':
                        IC_inf_Z = round(echantillion.mean() - Z_critic * (ecart_type_population_Z / np.sqrt(len(echantillion))), 2)
                        IC_sup_Z = float('inf')
                    
                    st.write(f"IC = [  {IC_inf_Z}  ;  {IC_sup_Z}  ]")

            elif continuer_test_Z == 'Non':
                st.warning("Teste arreté.")
            
        # TEST_T

        elif choisir_test(echantillion) == 'T':
            st.subheader("_ _ _ _  TEST T _ _ _ _")
            
            # tester la normalite des donnees
            st.subheader("Tester la normalité des données")
            test_norm = st.radio("Choisire la methode", ['Distibution', 'Test de Shapiro-Wilk'])

            if test_norm == 'Distibution':
                sns.kdeplot(echantillion, fill=True)
                plt.hist(echantillion, bins='auto', density=True)
                st.pyplot(plt)
            
            elif test_norm == 'Test de Shapiro-Wilk':
                # Réaliser le test de Shapiro-Wilk
                w_stat, p_value = shapiro(echantillion)
                st.subheader("Résultat:")
                st.write(f"Statistique de test W : {w_stat}")
                st.write(f"Valeur p : {p_value}")
                
                if p_value > 0.05:
                    st.warning("Les données suivent une distribution normale (p > 0.05)")
                else:
                    st.warning("Les données ne suivent pas une distribution normale (p <= 0.05)")
            
            # Continuer le test
            cont_test_T = st.radio("Continuer le test",['Non', 'Oui'])
           
            if cont_test_T == 'Oui':
                st.subheader("Test T sur la moyenne de l'échantillon:")
                
                # Nature du test (à droite, à gauche, ou bilatéral)
                alternative_T = st.radio("Nature du test :", ['Bilatéral', 'à Gauche', 'à Droite'])

                # Réaliser le test T
                moyenne_population = result_data[colonne_choisie_population].mean()
                ecart_type_population_T = result_data[colonne_choisie_population].std()
                T, T_critic, result = test_T(echantillion, moyenne_population, ecart_type_population_T, 0.05, alternative_T)
                
                # Afficher les résultats
                st.subheader("_ _ _ _Résultat_ _ _ _")
                st.write(f"Valeur de  T = {T}")
                st.write(f"Valeur de  Tc = {T_critic}")

                st.subheader("_ _ _ _Conclusion_ _ _ _")
                # Interprétation du test
                if result == 'Rejeter':
                    st.warning("Rejeter l'hypothèse nulle :")
                else:
                    st.warning("Accepter l'hypothèse nulle :")

                # Intervalle de confiance
                st.subheader("_ _ _ _Intervalle de confiance_ _ _ _")
                choix_ic_T = st.radio("Choisir :", ['Non', 'Oui'])
                if choix_ic_T == 'Oui':
                    
                    if alternative_T == 'Bilatéral':
                        # Intervalle de confiance bilatéral
                        IC_inf_T = round(np.mean(echantillion) - T_critic * (ecart_type_population_T / np.sqrt(len(echantillion))), 2)
                        IC_sup_T = round(np.mean(echantillion) + T_critic * (ecart_type_population_T / np.sqrt(len(echantillion))), 2)

                    elif alternative_T == 'à Gauche':
                        IC_inf_T = float('-inf')
                        IC_sup_T = round(echantillion.mean() + T_critic * (ecart_type_population_T / np.sqrt(len(echantillion))), 2)

                    elif alternative_T == 'à Droite':
                        IC_inf_T = round(echantillion.mean() - T_critic * (ecart_type_population_T / np.sqrt(len(echantillion))), 2)
                        IC_sup_T = float('inf')

                    st.write(f"IC = [ {IC_inf_T} ; {IC_sup_T} ]")

            elif cont_test_T == 'Non':
                st.warning("Teste arreté.")


    elif Choix == "Prédiction avec droite de regression simple":
            st.markdown("<h1 style='text-align: center;'>Prédiction :</h1>", unsafe_allow_html=True)
            
            # Selection des variable
            Col1,Col2 = st.columns(2)
            col_numerique = [colonne for colonne in data.columns if pd.api.types.is_numeric_dtype(result_data[colonne])]
            colonne_x = Col1.selectbox("Choisire la variable independante:", col_numerique)
            colonne_y = Col2.selectbox("Choisire la variable à prédire:", col_numerique)
            
            # Calcule de la droite
            st.subheader("Droite de regression :")
            x = data.loc[selected_rows, colonne_x]
            y = data.loc[selected_rows, colonne_y]
            covariance = np.cov(x, y, bias=True)[0][1]
            variance = np.var (x, ddof=0)
            B1 = round(( covariance / variance ),2)
            B0 = round(( y.mean() - B1 * x.mean() ),2)
            y_predi = B0+B1*x
            
            # Calcule de residus
            residus = y - y_predi
            
            #Calcule de somme carre residus ssr et some carre total
            SSR = round( np.sum( ( y_predi - y.mean())  **2 ) ,2)
            SST = round( np.sum( ( y - y.mean() ) **2) ,2)
            
            #Coefficient de determination R2
            R2 = round(SSR/SST,2)

            # Affichage de la droite
            if B1 > 0:
                st.write(f"Y = {B0} + {B1} *X")
            elif B1 < 0:
                st.write(f"Y = {B0} - {-B1} *X")

            st.write(f"R carre = {R2}")
            st.write(f"Ce qui indique que se modèle explique environ {R2*100} %")
            
            # Estimer une valeur entrer par utilisateur
            st.subheader("Éstimer une valeur ?")
            estim = st.radio("", ['Non', 'Oui'])
            if estim == 'Oui':
                val = st.number_input("Entrer la valeur ")
                st.write(f"La prédiction pour X= {val}  est  Y= {round(B0+(B1)*val,2)}")


if __name__ == '__main__':
    main()
