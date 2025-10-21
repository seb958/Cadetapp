#!/usr/bin/env python3
"""
Script pour redistribuer les cadets dans différentes sections
"""
from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URL)
db = client["escadron_cadets"]

print("=== REDISTRIBUTION DES CADETS DANS LES SECTIONS ===\n")

# Récupérer les sections
sections = list(db.sections.find({}, {"_id": 0, "id": 1, "nom": 1}))
print(f"📋 Sections disponibles: {len(sections)}")
for section in sections:
    print(f"  - {section['nom']} (ID: {section['id']})")

section_ids = [s['id'] for s in sections if s['nom'] not in ['Musique', 'Garde aux drapeaux']]
print(f"\n📌 Sections principales (hors Musique et Garde): {len(section_ids)}")

# Récupérer tous les cadets
cadets = list(db.users.find(
    {"role": {"$regex": "cadet", "$options": "i"}},
    {"_id": 0, "id": 1, "nom": 1, "prenom": 1}
))

print(f"\n👥 Cadets à redistribuer: {len(cadets)}")

# Redistribuer les cadets dans les sections principales
updates = []
for i, cadet in enumerate(cadets):
    # Répartir de manière équitable dans les 3 sections principales
    section_id = section_ids[i % len(section_ids)]
    section_name = next(s['nom'] for s in sections if s['id'] == section_id)
    
    result = db.users.update_one(
        {"id": cadet['id']},
        {"$set": {"section_id": section_id}}
    )
    
    if result.modified_count > 0:
        updates.append(f"✅ {cadet['nom']} {cadet['prenom']} → {section_name}")
    else:
        print(f"⚠️  {cadet['nom']} {cadet['prenom']} déjà dans {section_name}")

print("\n=== RÉSULTAT DE LA REDISTRIBUTION ===\n")
for update in updates:
    print(update)

# Vérifier la nouvelle répartition
print("\n=== NOUVELLE RÉPARTITION ===\n")
for section in sections:
    if section['nom'] in ['Musique', 'Garde aux drapeaux']:
        continue
    
    count = db.users.count_documents({
        "role": {"$regex": "cadet", "$options": "i"},
        "section_id": section['id']
    })
    print(f"{section['nom']}: {count} cadets")

print("\n✅ Redistribution terminée!")
