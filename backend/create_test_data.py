#!/usr/bin/env python3
"""
Script pour créer des données de test pour l'application escadron de cadets
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

async def create_test_data():
    # Connexion MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Création des données de test...")
    
    # 1. Créer des sections
    sections = [
        {"id": str(uuid.uuid4()), "nom": "Section Alpha", "description": "Section d'entraînement", "created_at": datetime.utcnow()},
        {"id": str(uuid.uuid4()), "nom": "Section Bravo", "description": "Section de parade", "created_at": datetime.utcnow()},
        {"id": str(uuid.uuid4()), "nom": "Section Charlie", "description": "Section logistique", "created_at": datetime.utcnow()}
    ]
    
    for section in sections:
        existing = await db.sections.find_one({"nom": section["nom"]})
        if not existing:
            await db.sections.insert_one(section)
            print(f"✅ Section créée: {section['nom']}")
        else:
            sections[sections.index(section)] = existing
            print(f"⚠️  Section existe déjà: {section['nom']}")
    
    # 2. Créer des cadets de test
    cadets = [
        {
            "id": str(uuid.uuid4()),
            "nom": "Martin",
            "prenom": "Pierre",
            "email": "pierre.martin@escadron.fr",
            "grade": "cadet",
            "role": "cadet",
            "section_id": sections[0]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("cadet123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        },
        {
            "id": str(uuid.uuid4()),
            "nom": "Dubois",
            "prenom": "Marie",
            "email": "marie.dubois@escadron.fr", 
            "grade": "caporal",
            "role": "cadet",
            "section_id": sections[0]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("cadet123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        },
        {
            "id": str(uuid.uuid4()),
            "nom": "Moreau",
            "prenom": "Jean",
            "email": "jean.moreau@escadron.fr",
            "grade": "sergent",
            "role": "cadet_responsible",
            "section_id": sections[0]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("resp123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        },
        {
            "id": str(uuid.uuid4()),
            "nom": "Bernard",
            "prenom": "Sophie",
            "email": "sophie.bernard@escadron.fr",
            "grade": "cadet",
            "role": "cadet",
            "section_id": sections[1]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("cadet123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        },
        {
            "id": str(uuid.uuid4()),
            "nom": "Petit",
            "prenom": "Thomas",
            "email": "thomas.petit@escadron.fr",
            "grade": "caporal",
            "role": "cadet",
            "section_id": sections[1]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("cadet123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        },
        {
            "id": str(uuid.uuid4()),
            "nom": "Leroy",
            "prenom": "Emma",
            "email": "emma.leroy@escadron.fr",
            "grade": "adjudant",
            "role": "cadet_admin",  
            "section_id": sections[1]["id"],
            "actif": True,
            "hashed_password": pwd_context.hash("admin123"),
            "created_at": datetime.utcnow(),
            "created_by": None
        }
    ]
    
    for cadet in cadets:
        existing = await db.users.find_one({"email": cadet["email"]})
        if not existing:
            await db.users.insert_one(cadet)
            print(f"✅ Cadet créé: {cadet['prenom']} {cadet['nom']} ({cadet['role']})")
        else:
            print(f"⚠️  Cadet existe déjà: {cadet['prenom']} {cadet['nom']}")
    
    # 3. Mettre à jour les responsables de section
    await db.sections.update_one(
        {"nom": "Section Alpha"},
        {"$set": {"responsable_id": next(c["id"] for c in cadets if c["nom"] == "Moreau")}}
    )
    
    await db.sections.update_one(
        {"nom": "Section Bravo"}, 
        {"$set": {"responsable_id": next(c["id"] for c in cadets if c["nom"] == "Leroy")}}
    )
    
    print("\n📊 Résumé des données créées:")
    print(f"- {len(sections)} sections")
    print(f"- {len(cadets)} cadets")
    print("\n🔑 Comptes de connexion:")
    print("Admin: admin@escadron.fr / admin123")
    print("Cadet Admin: emma.leroy@escadron.fr / admin123")
    print("Cadet Responsable: jean.moreau@escadron.fr / resp123")
    print("Cadets: pierre.martin@escadron.fr, marie.dubois@escadron.fr, etc. / cadet123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_data())