#!/usr/bin/env python3
"""
Script pour générer automatiquement des usernames pour les utilisateurs qui n'en ont pas
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()


def generate_username(first_name, last_name, role):
    """Génère un username basé sur le nom, prénom et rôle"""
    if first_name and last_name:
        # Format: prenom.nom (lowercase, sans accents)
        username = f"{first_name}.{last_name}".lower()
        username = re.sub(r'[àáâãäå]', 'a', username)
        username = re.sub(r'[èéêë]', 'e', username)
        username = re.sub(r'[ìíîï]', 'i', username)
        username = re.sub(r'[òóôõö]', 'o', username)
        username = re.sub(r'[ùúûü]', 'u', username)
        username = re.sub(r'[ç]', 'c', username)
        username = re.sub(r'[^a-z0-9.]', '', username)
    else:
        # Si pas de nom/prénom, utiliser le rôle
        if role:
            username = role.lower().replace(' ', '_')
            username = re.sub(r'[àáâãäå]', 'a', username)
            username = re.sub(r'[èéêë]', 'e', username)
            username = re.sub(r'[^a-z0-9_]', '', username)
        else:
            username = "user"
    
    return username


async def generate_missing_usernames():
    """Génère les usernames manquants pour les utilisateurs"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['escadron_cadets']
    
    print("🔍 Recherche des utilisateurs sans username...\n")
    
    # Trouver tous les utilisateurs sans username
    users_without_username = await db.users.find({"username": None}).to_list(length=100)
    
    if not users_without_username:
        print("✅ Tous les utilisateurs ont déjà un username!")
        client.close()
        return
    
    print(f"📋 {len(users_without_username)} utilisateurs trouvés sans username\n")
    
    # Récupérer tous les usernames existants pour éviter les doublons
    all_users = await db.users.find({}, {"username": 1}).to_list(length=1000)
    existing_usernames = {u.get("username") for u in all_users if u.get("username")}
    
    updated_count = 0
    
    for user in users_without_username:
        user_id = user.get("id")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        role = user.get("role")
        email = user.get("email")
        
        # Générer le username de base
        base_username = generate_username(first_name, last_name, role)
        
        # S'assurer que le username est unique
        username = base_username
        counter = 1
        while username in existing_usernames:
            username = f"{base_username}{counter}"
            counter += 1
        
        # Mettre à jour l'utilisateur
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"username": username}}
        )
        
        if result.modified_count > 0:
            existing_usernames.add(username)
            updated_count += 1
            print(f"✅ Username généré: {username}")
            print(f"   - Utilisateur: {first_name or 'N/A'} {last_name or 'N/A'}")
            print(f"   - Rôle: {role or 'N/A'}")
            print(f"   - Email: {email or 'N/A'}")
            print(f"   - ID: {user_id}\n")
    
    client.close()
    
    print(f"\n🎉 {updated_count}/{len(users_without_username)} usernames générés avec succès!")
    print("\n⚠️ IMPORTANT: Ces utilisateurs devront définir leur mot de passe via le système d'invitation.")


if __name__ == "__main__":
    asyncio.run(generate_missing_usernames())
