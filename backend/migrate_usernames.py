#!/usr/bin/env python3
"""
Script pour migrer les utilisateurs existants et ajouter des usernames
"""
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire backend au chemin
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import unicodedata
import re
import secrets

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def normalize_text(text: str) -> str:
    """Normalise le texte en supprimant les accents et caractères spéciaux"""
    # Normaliser les caractères Unicode (décomposer les accents)
    normalized = unicodedata.normalize('NFD', text)
    # Supprimer les caractères de catégorie "Mark" (accents)
    ascii_text = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    # Convertir en minuscules et supprimer les caractères non alphanumériques
    return re.sub(r'[^a-z0-9]', '', ascii_text.lower())

def generate_base_username(prenom: str, nom: str) -> str:
    """Génère un username de base à partir du prénom et nom"""
    # Prendre la première lettre du prénom + nom complet
    prenom_normalized = normalize_text(prenom)
    nom_normalized = normalize_text(nom)
    
    if prenom_normalized and nom_normalized:
        return f"{prenom_normalized[0]}{nom_normalized}"
    elif nom_normalized:
        return nom_normalized
    else:
        return "user"

async def generate_unique_username(prenom: str, nom: str, existing_usernames: set) -> str:
    """Génère un username unique en ajoutant un chiffre si nécessaire"""
    base_username = generate_base_username(prenom, nom)
    
    # Vérifier si le username de base existe déjà
    if base_username not in existing_usernames:
        return base_username
    
    # Si le username existe, ajouter un chiffre
    counter = 2
    while True:
        new_username = f"{base_username}{counter}"
        
        if new_username not in existing_usernames:
            return new_username
        
        counter += 1
        
        # Éviter les boucles infinies
        if counter > 100:
            # Utiliser un UUID aléatoire en dernier recours
            return f"{base_username}{secrets.randbelow(10000)}"

async def migrate_usernames():
    """Migre tous les utilisateurs pour ajouter les usernames"""
    print("🚀 Début de la migration des usernames...")
    
    # Récupérer tous les utilisateurs
    users = await db.users.find({}).to_list(1000)
    print(f"📊 Trouvé {len(users)} utilisateurs à migrer")
    
    if not users:
        print("✅ Aucun utilisateur à migrer")
        return
    
    # Collecter les usernames existants
    existing_usernames = set()
    for user in users:
        if user.get("username"):
            existing_usernames.add(user["username"])
    
    updated_count = 0
    
    # Traiter chaque utilisateur
    for user in users:
        if not user.get("username"):  # Seulement si pas de username
            # Générer un username unique
            username = await generate_unique_username(
                user.get("prenom", ""), 
                user.get("nom", ""), 
                existing_usernames
            )
            
            # Ajouter à la set pour éviter les doublons
            existing_usernames.add(username)
            
            # Mettre à jour l'utilisateur
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"username": username}}
            )
            
            print(f"✅ {user.get('prenom', '')} {user.get('nom', '')} -> {username}")
            updated_count += 1
        else:
            print(f"⏭️  {user.get('prenom', '')} {user.get('nom', '')} -> {user.get('username')} (déjà existant)")
    
    print(f"🎉 Migration terminée ! {updated_count} utilisateurs mis à jour")

async def main():
    try:
        await migrate_usernames()
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())