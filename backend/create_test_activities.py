#!/usr/bin/env python3
"""
Script pour créer des activités de test
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def create_test_activities():
    # Connexion MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🎵 Création des activités de test...")
    
    # Récupérer les IDs des cadets pour les exemples
    jean_moreau = await db.users.find_one({"email": "jean.moreau@escadron.fr"})
    pierre_martin = await db.users.find_one({"email": "pierre.martin@escadron.fr"})
    marie_dubois = await db.users.find_one({"email": "marie.dubois@escadron.fr"})
    emma_leroy = await db.users.find_one({"email": "emma.leroy@escadron.fr"})
    admin = await db.users.find_one({"email": "admin@escadron.fr"})
    
    if not all([jean_moreau, pierre_martin, marie_dubois, emma_leroy, admin]):
        print("❌ Certains cadets n'ont pas été trouvés")
        client.close()
        return
    
    activities = [
        # Activité récurrente - Musique
        {
            "id": str(uuid.uuid4()),
            "nom": "Cours de Musique",
            "description": "Cours de musique pour la fanfare de l'escadron",
            "type": "recurring",
            "cadet_ids": [jean_moreau["id"], pierre_martin["id"], marie_dubois["id"]],
            "recurrence_interval": 14,  # Toutes les 2 semaines
            "recurrence_unit": "days",
            "next_date": "2025-01-26",  # Prochain dimanche
            "planned_date": None,
            "created_by": admin["id"],
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        },
        
        # Activité ponctuelle - Planeur
        {
            "id": str(uuid.uuid4()),
            "nom": "Journée Planeur",
            "description": "Sortie découverte du planeur",
            "type": "unique",
            "cadet_ids": [emma_leroy["id"], marie_dubois["id"]],
            "recurrence_interval": None,
            "recurrence_unit": None,
            "next_date": None,
            "planned_date": "2025-09-28",
            "created_by": admin["id"],
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        },
        
        # Activité récurrente - Formation
        {
            "id": str(uuid.uuid4()),
            "nom": "Formation Technique",
            "description": "Formation technique hebdomadaire",
            "type": "recurring",
            "cadet_ids": [jean_moreau["id"], emma_leroy["id"], pierre_martin["id"], marie_dubois["id"]],
            "recurrence_interval": 7,  # Toutes les semaines
            "recurrence_unit": "days",
            "next_date": "2025-01-25",  # Prochain samedi
            "planned_date": None,
            "created_by": admin["id"],
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
    ]
    
    for activity in activities:
        existing = await db.activities.find_one({"nom": activity["nom"]})
        if not existing:
            await db.activities.insert_one(activity)
            print(f"✅ Activité créée: {activity['nom']} ({activity['type']})")
        else:
            print(f"⚠️  Activité existe déjà: {activity['nom']}")
    
    print("\n📋 Activités créées:")
    print("- Cours de Musique (récurrent, 2 semaines) - Jean, Pierre, Marie")
    print("- Journée Planeur (ponctuel, 28 sept) - Emma, Marie") 
    print("- Formation Technique (récurrent, hebdo) - Tous")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_activities())