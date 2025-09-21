#!/usr/bin/env python3
"""
Script pour créer un utilisateur administrateur de test
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    # Connexion MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Données de l'admin
    admin_data = {
        "id": str(uuid.uuid4()),
        "nom": "Administrateur",
        "prenom": "Admin",
        "email": "admin@escadron.fr",
        "grade": "commandant",
        "role": "encadrement",
        "section_id": None,
        "photo_base64": None,
        "actif": True,
        "hashed_password": pwd_context.hash("admin123"),
        "created_at": datetime.utcnow(),
        "created_by": None
    }
    
    # Vérifier si l'admin existe déjà
    existing_admin = await db.users.find_one({"email": "admin@escadron.fr"})
    if existing_admin:
        print("❌ L'utilisateur admin existe déjà!")
        await client.close()
        return
    
    # Créer l'admin
    await db.users.insert_one(admin_data)
    print("✅ Utilisateur administrateur créé avec succès!")
    print("📧 Email: admin@escadron.fr")
    print("🔐 Mot de passe: admin123")
    print("⚠️  Changez ce mot de passe en production!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())