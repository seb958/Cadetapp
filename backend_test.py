#!/usr/bin/env python3
"""
Test backend de l'application de gestion d'escadron de cadets
Focus sur la vérification des 3 utilisateurs avec nouveaux usernames
"""

import requests
import json
from datetime import datetime, date
import sys

# Configuration
BASE_URL = "https://cadet-command.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@escadron.fr"
ADMIN_PASSWORD = "admin123"

# Utilisateurs avec nouveaux usernames à vérifier
EXPECTED_USERS_WITH_USERNAMES = [
    {
        "username": "adjudantchef_descadron",
        "role": "Adjudant-Chef d'escadron",
        "expected_id": "434b7d13-f0d8-469a-aeec-f25b2e2fd3b7"
    },
    {
        "username": "sergent_de_section", 
        "role": "Sergent de section",
        "expected_id": "2449f021-af86-4349-bf19-a2c7f1edd228"
    },
    {
        "username": "adjudant_descadron",
        "role": "Adjudant d'escadron", 
        "expected_id": "a01b2ec0-64d0-4e35-8305-5db28e3efa97"
    }
]

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": []
        }
    
    def log_test(self, test_name, success, message=""):
        """Enregistrer le résultat d'un test"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results["failed_tests"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def authenticate(self):
        """Authentification avec les credentials admin"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log_test(
                    "Authentification admin",
                    True,
                    f"Connexion réussie pour {ADMIN_USERNAME}"
                )
                return True
            else:
                self.log_test(
                    "Authentification admin",
                    False,
                    f"Échec de connexion: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Authentification admin",
                False,
                f"Erreur de connexion: {str(e)}"
            )
            return False
    
    def get_sections(self):
        """Récupérer toutes les sections"""
        try:
            response = self.session.get(f"{BASE_URL}/sections")
            
            if response.status_code == 200:
                sections = response.json()
                self.log_test(
                    "Récupération des sections",
                    True,
                    f"{len(sections)} sections trouvées"
                )
                return sections
            else:
                self.log_test(
                    "Récupération des sections",
                    False,
                    f"Erreur {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test(
                "Récupération des sections",
                False,
                f"Erreur: {str(e)}"
            )
            return None
    
    def get_users(self):
        """Récupérer tous les utilisateurs"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            
            if response.status_code == 200:
                users = response.json()
                self.log_test(
                    "Récupération des utilisateurs",
                    True,
                    f"{len(users)} utilisateurs trouvés"
                )
                return users
            else:
                self.log_test(
                    "Récupération des utilisateurs",
                    False,
                    f"Erreur {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test(
                "Récupération des utilisateurs",
                False,
                f"Erreur: {str(e)}"
            )
            return None
    
    def find_section_by_name(self, sections, section_name):
        """Trouver une section par son nom"""
        for section in sections:
            if section_name.lower() in section["nom"].lower():
                return section
        return None
    
    def find_user_by_id(self, users, user_id):
        """Trouver un utilisateur par son ID"""
        for user in users:
            if user["id"] == user_id:
                return user
        return None
    
    def assign_section_leader(self, section_id, responsable_id, section_name, user_name):
        """Assigner un responsable à une section"""
        try:
            # D'abord récupérer les détails actuels de la section
            response = self.session.get(f"{BASE_URL}/sections")
            if response.status_code != 200:
                self.log_test(
                    f"Assignation {user_name} -> {section_name}",
                    False,
                    "Impossible de récupérer les sections"
                )
                return False
            
            sections = response.json()
            current_section = None
            for section in sections:
                if section["id"] == section_id:
                    current_section = section
                    break
            
            if not current_section:
                self.log_test(
                    f"Assignation {user_name} -> {section_name}",
                    False,
                    "Section non trouvée"
                )
                return False
            
            # Préparer les données de mise à jour
            update_data = {
                "nom": current_section["nom"],
                "description": current_section.get("description"),
                "responsable_id": responsable_id
            }
            
            # Effectuer la mise à jour
            response = self.session.put(
                f"{BASE_URL}/sections/{section_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                self.log_test(
                    f"Assignation {user_name} -> {section_name}",
                    True,
                    "Assignation réussie"
                )
                return True
            else:
                self.log_test(
                    f"Assignation {user_name} -> {section_name}",
                    False,
                    f"Erreur {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Assignation {user_name} -> {section_name}",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def verify_assignment(self, section_id, expected_responsable_id, section_name, user_name):
        """Vérifier qu'une assignation a bien été effectuée"""
        try:
            response = self.session.get(f"{BASE_URL}/sections")
            
            if response.status_code == 200:
                sections = response.json()
                for section in sections:
                    if section["id"] == section_id:
                        actual_responsable_id = section.get("responsable_id")
                        if actual_responsable_id == expected_responsable_id:
                            self.log_test(
                                f"Vérification {user_name} -> {section_name}",
                                True,
                                "Assignation confirmée"
                            )
                            return True
                        else:
                            self.log_test(
                                f"Vérification {user_name} -> {section_name}",
                                False,
                                f"Responsable incorrect: attendu {expected_responsable_id}, trouvé {actual_responsable_id}"
                            )
                            return False
                
                self.log_test(
                    f"Vérification {user_name} -> {section_name}",
                    False,
                    "Section non trouvée"
                )
                return False
            else:
                self.log_test(
                    f"Vérification {user_name} -> {section_name}",
                    False,
                    f"Erreur {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Vérification {user_name} -> {section_name}",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def run_specific_tests(self):
        """Exécuter les tests spécifiques demandés"""
        print("🚀 DÉBUT DES TESTS D'ASSIGNATION DE RESPONSABLES DE SECTION")
        print("=" * 70)
        
        # 1. Authentification
        if not self.authenticate():
            print("❌ Impossible de continuer sans authentification")
            return False
        
        # 2. Récupérer les données de base
        sections = self.get_sections()
        users = self.get_users()
        
        if not sections or not users:
            print("❌ Impossible de récupérer les données de base")
            return False
        
        print(f"\n📊 DONNÉES DE BASE:")
        print(f"   - {len(sections)} sections disponibles")
        print(f"   - {len(users)} utilisateurs disponibles")
        
        # Afficher les sections disponibles
        print(f"\n📋 SECTIONS DISPONIBLES:")
        for section in sections:
            responsable_info = "Aucun responsable"
            if section.get("responsable_id"):
                responsable = self.find_user_by_id(users, section["responsable_id"])
                if responsable:
                    responsable_info = f"{responsable['prenom']} {responsable['nom']}"
                else:
                    responsable_info = f"ID: {section['responsable_id']} (utilisateur non trouvé)"
            
            print(f"   - {section['nom']} (ID: {section['id']}) - Responsable: {responsable_info}")
        
        # Afficher les utilisateurs avec les IDs spécifiés
        print(f"\n👥 UTILISATEURS CIBLES:")
        target_users = [
            ("2449f021-af86-4349-bf19-a2c7f1edd228", "sgst 2"),
            ("a01b2ec0-64d0-4e35-8305-5db28e3efa97", "adj 2"),
            ("434b7d13-f0d8-469a-aeec-f25b2e2fd3b7", "Cadet Commandant")
        ]
        
        found_users = {}
        for user_id, expected_name in target_users:
            user = self.find_user_by_id(users, user_id)
            if user:
                found_users[user_id] = user
                print(f"   - ✅ {user['prenom']} {user['nom']} (ID: {user_id}) - Rôle: {user['role']} - Grade: {user['grade']}")
            else:
                print(f"   - ❌ Utilisateur {expected_name} (ID: {user_id}) NON TROUVÉ")
        
        # 3. Test 1: Assigner sgst 2 comme responsable de Musique
        print(f"\n🎵 TEST 1: ASSIGNATION SGST 2 -> MUSIQUE")
        sgst2_id = "2449f021-af86-4349-bf19-a2c7f1edd228"
        musique_section = self.find_section_by_name(sections, "musique")
        
        if musique_section and sgst2_id in found_users:
            success = self.assign_section_leader(
                musique_section["id"], 
                sgst2_id, 
                "Musique", 
                "sgst 2"
            )
            if success:
                self.verify_assignment(
                    musique_section["id"], 
                    sgst2_id, 
                    "Musique", 
                    "sgst 2"
                )
        else:
            if not musique_section:
                self.log_test("Test 1 - Recherche section Musique", False, "Section Musique non trouvée")
            if sgst2_id not in found_users:
                self.log_test("Test 1 - Recherche sgst 2", False, "Utilisateur sgst 2 non trouvé")
        
        # 4. Test 2: Assigner adj 2 comme responsable de Garde aux drapeaux
        print(f"\n🏴 TEST 2: ASSIGNATION ADJ 2 -> GARDE AUX DRAPEAUX")
        adj2_id = "a01b2ec0-64d0-4e35-8305-5db28e3efa97"
        garde_section = self.find_section_by_name(sections, "garde")
        
        if garde_section and adj2_id in found_users:
            success = self.assign_section_leader(
                garde_section["id"], 
                adj2_id, 
                "Garde aux drapeaux", 
                "adj 2"
            )
            if success:
                self.verify_assignment(
                    garde_section["id"], 
                    adj2_id, 
                    "Garde aux drapeaux", 
                    "adj 2"
                )
        else:
            if not garde_section:
                self.log_test("Test 2 - Recherche section Garde", False, "Section Garde aux drapeaux non trouvée")
            if adj2_id not in found_users:
                self.log_test("Test 2 - Recherche adj 2", False, "Utilisateur adj 2 non trouvé")
        
        # 5. Test 3: Réassignation Section 2 de Cadet Commandant vers sgst 2
        print(f"\n🔄 TEST 3: RÉASSIGNATION SECTION 2")
        section2 = None
        for section in sections:
            if "section 2" in section["nom"].lower() or section["nom"] == "Section 2":
                section2 = section
                break
        
        if section2 and sgst2_id in found_users:
            print(f"   Section trouvée: {section2['nom']} (ID: {section2['id']})")
            current_responsable = section2.get("responsable_id")
            if current_responsable:
                current_user = self.find_user_by_id(users, current_responsable)
                if current_user:
                    print(f"   Responsable actuel: {current_user['prenom']} {current_user['nom']}")
            
            success = self.assign_section_leader(
                section2["id"], 
                sgst2_id, 
                "Section 2", 
                "sgst 2"
            )
            if success:
                self.verify_assignment(
                    section2["id"], 
                    sgst2_id, 
                    "Section 2", 
                    "sgst 2"
                )
        else:
            if not section2:
                self.log_test("Test 3 - Recherche Section 2", False, "Section 2 non trouvée")
        
        # 6. Vérification finale de toutes les assignations
        print(f"\n🔍 VÉRIFICATION FINALE DES ASSIGNATIONS")
        final_sections = self.get_sections()
        if final_sections:
            print("   État final des sections:")
            for section in final_sections:
                responsable_info = "Aucun responsable"
                if section.get("responsable_id"):
                    responsable = self.find_user_by_id(users, section["responsable_id"])
                    if responsable:
                        responsable_info = f"{responsable['prenom']} {responsable['nom']} ({responsable['role']})"
                    else:
                        responsable_info = f"ID: {section['responsable_id']} (utilisateur non trouvé)"
                
                print(f"   - {section['nom']}: {responsable_info}")
        
        return True
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - successful_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {successful_tests}")
        print(f"❌ Échecs: {failed_tests}")
        print(f"📈 Taux de réussite: {(successful_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   - {test['test']}: {test['message']}")
        
        print(f"\n🎯 OBJECTIF: Vérifier que les utilisateurs avec nouveaux rôles peuvent être assignés comme responsables")
        
        # Analyser les résultats spécifiques
        assignment_tests = [t for t in self.test_results if "Assignation" in t["test"]]
        verification_tests = [t for t in self.test_results if "Vérification" in t["test"]]
        
        successful_assignments = len([t for t in assignment_tests if t["success"]])
        successful_verifications = len([t for t in verification_tests if t["success"]])
        
        print(f"\n📋 RÉSULTATS SPÉCIFIQUES:")
        print(f"   - Assignations réussies: {successful_assignments}/{len(assignment_tests)}")
        print(f"   - Vérifications réussies: {successful_verifications}/{len(verification_tests)}")
        
        if successful_assignments == len(assignment_tests) and successful_verifications == len(verification_tests):
            print(f"\n🎉 CONCLUSION: Le problème d'assignation des responsables semble RÉSOLU!")
        else:
            print(f"\n⚠️  CONCLUSION: Des problèmes persistent dans l'assignation des responsables")

def main():
    """Fonction principale"""
    tester = SectionAssignmentTester()
    
    try:
        success = tester.run_specific_tests()
        tester.print_summary()
        
        # Retourner le code de sortie approprié
        failed_tests = len([t for t in tester.test_results if not t["success"]])
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()