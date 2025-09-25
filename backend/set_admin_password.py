#!/usr/bin/env python3
"""
Script pour définir le mot de passe de l'admin
"""
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire backend au chemin
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def set_admin_password():
    username = 'aadministrateur'
    password = 'admin123'
    hashed = pwd_context.hash(password)
    
    result = await db.users.update_one(
        {'username': username},
        {'$set': {'hashed_password': hashed}}
    )
    
    if result.modified_count > 0:
        print(f'✅ Mot de passe défini pour {username}')
    else:
        print(f'❌ Utilisateur {username} non trouvé')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(set_admin_password())