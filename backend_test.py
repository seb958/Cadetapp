#!/usr/bin/env python3
"""
Tests pour l'assignation des responsables de section et vérification de l'organigrame
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://squadron-app.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

# IDs spécifiques mentionnés dans la demande
CADET_COMMANDANT_ID = "434b7d13-f0d8-469a-aeec-f25b2e2fd3b7"
SECTION_2_ID = "1f06b8a5-462a-457b-88c7-6cebf7a00bee"

class TestResults:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        
    def log_success(self, test_name):
        print(f"✅ {test_name}")
        self.tests_passed += 1
        
    def log_error(self, test_name, error):
        print(f"❌ {test_name}: {error}")
        self.errors.append(f"{test_name}: {error}")
        self.tests_failed += 1
        
    def summary(self):
        total = self.tests_passed + self.tests_failed
        print(f"\n📊 RÉSULTATS: {self.tests_passed}/{total} tests réussis")
        if self.errors:
            print("\n🔍 ERREURS DÉTAILLÉES:")
            for error in self.errors:
                print(f"  - {error}")

def authenticate():
    """Authentification avec les credentials admin"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Échec authentification: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur authentification: {e}")
        return None

def get_headers(token):
    """Retourne les headers avec le token d'authentification"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_section_assignment(token, results):
    """Test 1: Assignation responsable de section"""
    print("\n🔧 TEST 1: ASSIGNATION RESPONSABLE DE SECTION")
    
    headers = get_headers(token)
    
    # Vérifier que le cadet commandant existe
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            cadet_commandant = next((u for u in users if u["id"] == CADET_COMMANDANT_ID), None)
            
            if cadet_commandant:
                results.log_success(f"Cadet Commandant trouvé: {cadet_commandant['prenom']} {cadet_commandant['nom']}")
            else:
                results.log_error("Vérification Cadet Commandant", f"Utilisateur avec ID {CADET_COMMANDANT_ID} non trouvé")
                return
        else:
            results.log_error("Récupération utilisateurs", f"Status {response.status_code}")
            return
    except Exception as e:
        results.log_error("Vérification Cadet Commandant", str(e))
        return
    
    # Vérifier que la section 2 existe
    try:
        response = requests.get(f"{BASE_URL}/sections", headers=headers)
        if response.status_code == 200:
            sections = response.json()
            section_2 = next((s for s in sections if s["id"] == SECTION_2_ID), None)
            
            if section_2:
                results.log_success(f"Section 2 trouvée: {section_2['nom']}")
            else:
                results.log_error("Vérification Section 2", f"Section avec ID {SECTION_2_ID} non trouvée")
                return
        else:
            results.log_error("Récupération sections", f"Status {response.status_code}")
            return
    except Exception as e:
        results.log_error("Vérification Section 2", str(e))
        return
    
    # Assigner le responsable à la section
    try:
        update_data = {
            "nom": section_2["nom"],
            "description": section_2.get("description"),
            "responsable_id": CADET_COMMANDANT_ID
        }
        
        response = requests.put(f"{BASE_URL}/sections/{SECTION_2_ID}", 
                              json=update_data, headers=headers)
        
        if response.status_code == 200:
            results.log_success("Assignation responsable de section réussie")
        else:
            results.log_error("Assignation responsable", f"Status {response.status_code} - {response.text}")
            return
    except Exception as e:
        results.log_error("Assignation responsable", str(e))
        return
    
    # Vérifier l'assignation
    try:
        response = requests.get(f"{BASE_URL}/sections", headers=headers)
        if response.status_code == 200:
            sections = response.json()
            section_2_updated = next((s for s in sections if s["id"] == SECTION_2_ID), None)
            
            if section_2_updated and section_2_updated.get("responsable_id") == CADET_COMMANDANT_ID:
                results.log_success("Vérification assignation: Cadet Commandant bien assigné à Section 2")
            else:
                results.log_error("Vérification assignation", "L'assignation n'a pas été sauvegardée correctement")
        else:
            results.log_error("Vérification assignation", f"Status {response.status_code}")
    except Exception as e:
        results.log_error("Vérification assignation", str(e))

def test_organizational_chart(token, results):
    """Test 2: Récupération données organigrame"""
    print("\n📊 TEST 2: RÉCUPÉRATION DONNÉES ORGANIGRAME")
    
    headers = get_headers(token)
    
    # Récupérer tous les utilisateurs
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            results.log_success(f"Récupération utilisateurs: {len(users)} utilisateurs trouvés")
            
            # Analyser la hiérarchie
            hierarchy_analysis = {
                "niveau_0_admin": [],
                "niveau_2_commandant": [],
                "niveau_3_sergents": [],
                "autres": []
            }
            
            for user in users:
                role = user.get("role", "")
                grade = user.get("grade", "")
                
                # Niveau 0: Admin/Encadrement
                if role in ["cadet_admin", "encadrement"] or "admin" in role.lower():
                    hierarchy_analysis["niveau_0_admin"].append({
                        "nom": f"{user['prenom']} {user['nom']}",
                        "role": role,
                        "grade": grade
                    })
                # Niveau 2: Adjudant-Chef d'escadron
                elif "adjudant_chef" in role.lower() or "commandant" in role.lower():
                    hierarchy_analysis["niveau_2_commandant"].append({
                        "nom": f"{user['prenom']} {user['nom']}",
                        "role": role,
                        "grade": grade
                    })
                # Niveau 3: Sergents/Adjudant d'escadron
                elif "sergent" in role.lower() or "adjudant_escadron" in role.lower():
                    hierarchy_analysis["niveau_3_sergents"].append({
                        "nom": f"{user['prenom']} {user['nom']}",
                        "role": role,
                        "grade": grade
                    })
                else:
                    hierarchy_analysis["autres"].append({
                        "nom": f"{user['prenom']} {user['nom']}",
                        "role": role,
                        "grade": grade
                    })
            
            # Afficher l'analyse
            print(f"  📋 Niveau 0 (Admin/Encadrement): {len(hierarchy_analysis['niveau_0_admin'])} utilisateurs")
            for user in hierarchy_analysis["niveau_0_admin"]:
                print(f"    - {user['nom']} ({user['role']}, {user['grade']})")
            
            print(f"  📋 Niveau 2 (Commandant): {len(hierarchy_analysis['niveau_2_commandant'])} utilisateurs")
            for user in hierarchy_analysis["niveau_2_commandant"]:
                print(f"    - {user['nom']} ({user['role']}, {user['grade']})")
            
            print(f"  📋 Niveau 3 (Sergents): {len(hierarchy_analysis['niveau_3_sergents'])} utilisateurs")
            for user in hierarchy_analysis["niveau_3_sergents"]:
                print(f"    - {user['nom']} ({user['role']}, {user['grade']})")
            
            print(f"  📋 Autres: {len(hierarchy_analysis['autres'])} utilisateurs")
            for user in hierarchy_analysis["autres"]:
                print(f"    - {user['nom']} ({user['role']}, {user['grade']})")
            
            results.log_success("Analyse hiérarchique complétée")
            
        else:
            results.log_error("Récupération utilisateurs", f"Status {response.status_code}")
            return
    except Exception as e:
        results.log_error("Récupération utilisateurs", str(e))
        return
    
    # Récupérer toutes les sections
    try:
        response = requests.get(f"{BASE_URL}/sections", headers=headers)
        if response.status_code == 200:
            sections = response.json()
            results.log_success(f"Récupération sections: {len(sections)} sections trouvées")
            
            # Analyser les sections et leurs responsables
            print(f"  📋 Analyse des sections:")
            for section in sections:
                responsable_info = "Aucun responsable"
                if section.get("responsable_id"):
                    # Trouver le responsable dans la liste des utilisateurs
                    responsable = next((u for u in users if u["id"] == section["responsable_id"]), None)
                    if responsable:
                        responsable_info = f"{responsable['prenom']} {responsable['nom']} ({responsable['role']})"
                
                print(f"    - {section['nom']} (ID: {section['id']}) - Responsable: {responsable_info}")
            
            results.log_success("Analyse des sections complétée")
            
        else:
            results.log_error("Récupération sections", f"Status {response.status_code}")
    except Exception as e:
        results.log_error("Récupération sections", str(e))

def test_structure_validation(token, results):
    """Test 3: Validation structure"""
    print("\n✅ TEST 3: VALIDATION STRUCTURE")
    
    headers = get_headers(token)
    
    # Vérifier que Section 1 a Emma Leroy comme responsable
    try:
        response = requests.get(f"{BASE_URL}/sections", headers=headers)
        if response.status_code == 200:
            sections = response.json()
            section_1 = next((s for s in sections if "1" in s["nom"]), None)
            
            if section_1:
                if section_1.get("responsable_id"):
                    # Récupérer les infos du responsable
                    users_response = requests.get(f"{BASE_URL}/users", headers=headers)
                    if users_response.status_code == 200:
                        users = users_response.json()
                        responsable = next((u for u in users if u["id"] == section_1["responsable_id"]), None)
                        
                        if responsable:
                            if "emma" in responsable["prenom"].lower() and "leroy" in responsable["nom"].lower():
                                results.log_success(f"Section 1 a bien Emma Leroy comme responsable")
                            else:
                                results.log_error("Validation Section 1", f"Responsable trouvé: {responsable['prenom']} {responsable['nom']} (attendu: Emma Leroy)")
                        else:
                            results.log_error("Validation Section 1", "Responsable non trouvé dans la liste des utilisateurs")
                    else:
                        results.log_error("Validation Section 1", "Impossible de récupérer la liste des utilisateurs")
                else:
                    results.log_error("Validation Section 1", "Section 1 n'a pas de responsable assigné")
            else:
                results.log_error("Validation Section 1", "Section 1 non trouvée")
        else:
            results.log_error("Validation Section 1", f"Status {response.status_code}")
    except Exception as e:
        results.log_error("Validation Section 1", str(e))
    
    # Vérifier que les utilisateurs créés sont actifs
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            active_users = [u for u in users if u.get("actif", False)]
            inactive_users = [u for u in users if not u.get("actif", False)]
            
            results.log_success(f"Utilisateurs actifs: {len(active_users)}/{len(users)}")
            
            if inactive_users:
                print(f"  ⚠️ Utilisateurs inactifs trouvés:")
                for user in inactive_users:
                    print(f"    - {user['prenom']} {user['nom']} ({user.get('role', 'N/A')})")
            
        else:
            results.log_error("Validation utilisateurs actifs", f"Status {response.status_code}")
    except Exception as e:
        results.log_error("Validation utilisateurs actifs", str(e))

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS - ASSIGNATION RESPONSABLES ET ORGANIGRAME")
    print(f"📡 Base URL: {BASE_URL}")
    print(f"👤 Utilisateur: {ADMIN_USERNAME}")
    
    results = TestResults()
    
    # Authentification
    print("\n🔐 AUTHENTIFICATION")
    token = authenticate()
    if not token:
        print("❌ Impossible de continuer sans authentification")
        return
    
    results.log_success("Authentification réussie")
    
    # Exécuter les tests
    test_section_assignment(token, results)
    test_organizational_chart(token, results)
    test_structure_validation(token, results)
    
    # Résumé final
    results.summary()
    
    return results.tests_failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)