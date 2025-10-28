#!/usr/bin/env python3
"""
Debug script to understand the permission logic issue
"""

import requests
import json

# Configuration
BASE_URL = "https://squadron-app-1.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

def authenticate_admin():
    """Authentification admin"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    return None

def get_users_with_sections():
    """Récupérer les utilisateurs avec leurs sections"""
    token = authenticate_admin()
    if not token:
        return []
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Récupérer les utilisateurs
    users_response = requests.get(f"{BASE_URL}/users", headers=headers)
    sections_response = requests.get(f"{BASE_URL}/sections", headers=headers)
    
    if users_response.status_code != 200 or sections_response.status_code != 200:
        return []
    
    users = users_response.json()
    sections = sections_response.json()
    
    # Créer un mapping des sections
    section_map = {s["id"]: s["nom"] for s in sections}
    
    print("=== ANALYSE DES UTILISATEURS ET SECTIONS ===")
    print(f"Total utilisateurs: {len(users)}")
    print(f"Total sections: {len(sections)}")
    
    print("\n=== SECTIONS DISPONIBLES ===")
    for section in sections:
        print(f"- {section['nom']} (ID: {section['id']})")
    
    print("\n=== UTILISATEURS PAR RÔLE ET SECTION ===")
    
    # Grouper par rôle
    role_groups = {}
    for user in users:
        role = user.get("role", "N/A")
        if role not in role_groups:
            role_groups[role] = []
        role_groups[role].append(user)
    
    for role, users_in_role in role_groups.items():
        print(f"\n🏷️  RÔLE: {role}")
        for user in users_in_role:
            section_id = user.get("section_id")
            section_name = section_map.get(section_id, "Aucune section") if section_id else "Aucune section"
            username = user.get("username", "N/A")
            print(f"   - {user['prenom']} {user['nom']} (username: {username})")
            print(f"     Section: {section_name} (ID: {section_id})")
            print(f"     Actif: {user.get('actif', False)}")
    
    # Analyser la logique de permissions
    print("\n=== ANALYSE LOGIQUE PERMISSIONS ===")
    
    for role, users_in_role in role_groups.items():
        role_lower = role.lower()
        
        # Reproduire la logique du backend
        has_commandant = 'commandant' in role_lower
        has_sergent = 'sergent' in role_lower
        has_commandant_de = 'commandant de' in role_lower
        
        if has_commandant or has_sergent:
            print(f"\n🔍 RÔLE: {role}")
            print(f"   - Contient 'commandant': {has_commandant}")
            print(f"   - Contient 'sergent': {has_sergent}")
            print(f"   - Contient 'commandant de': {has_commandant_de}")
            
            for user in users_in_role:
                section_id = user.get("section_id")
                
                # Logique actuelle du backend
                is_section_leader = (has_commandant or has_sergent) and \
                                  not has_commandant_de and \
                                  section_id is not None
                
                print(f"   - {user['prenom']} {user['nom']}:")
                print(f"     Section ID: {section_id}")
                print(f"     Est chef de section (logique actuelle): {is_section_leader}")
                
                # Logique corrigée proposée
                is_section_leader_fixed = (has_commandant or has_sergent) and \
                                        section_id is not None and \
                                        ('section' in role_lower or 'sergent' in role_lower)
                
                print(f"     Est chef de section (logique corrigée): {is_section_leader_fixed}")

if __name__ == "__main__":
    get_users_with_sections()