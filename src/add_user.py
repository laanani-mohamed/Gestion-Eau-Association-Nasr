from utils.auth import add_user,create_user_table

create_user_table()

# Ajouter un utilisateur
username = "Mohamed"
password = "laanani.med"

username1 = "Abdelkrim"
password1 = "laanani.abdel"

add_user(username, password)
print(f"Utilisateur {username} ajouté avec succès.")

