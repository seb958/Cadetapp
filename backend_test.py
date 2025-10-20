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
    
    def authenticate_admin(self):
        """Authentification avec le compte admin"""
        try:
            login_data = {
                "username": "aadministrateur",  # Username de l'admin selon les tests précédents
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("Authentification admin", True, f"Token obtenu pour {data['user']['prenom']} {data['user']['nom']}")
                return True
            else:
                self.log_test("Authentification admin", False, f"Erreur {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentification admin", False, f"Exception: {str(e)}")
            return False
    
    def test_get_all_users(self):
        """Test GET /api/users - récupération de tous les utilisateurs"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            
            if response.status_code == 200:
                users = response.json()
                self.log_test("GET /api/users", True, f"{len(users)} utilisateurs trouvés")
                return users
            else:
                self.log_test("GET /api/users", False, f"Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("GET /api/users", False, f"Exception: {str(e)}")
            return []
    
    def test_users_with_new_usernames(self, users):
        """Vérifier les 3 utilisateurs avec nouveaux usernames"""
        found_users = {}
        
        # Créer un dictionnaire des utilisateurs par ID et username
        users_by_id = {user["id"]: user for user in users}
        users_by_username = {user.get("username"): user for user in users if user.get("username")}
        
        for expected_user in EXPECTED_USERS_WITH_USERNAMES:
            username = expected_user["username"]
            role = expected_user["role"]
            expected_id = expected_user["expected_id"]
            
            # Vérifier par username
            if username in users_by_username:
                user = users_by_username[username]
                found_users[username] = user
                
                # Vérifier l'ID
                if user["id"] == expected_id:
                    self.log_test(f"Username {username} - ID correct", True, f"ID {expected_id} confirmé")
                else:
                    self.log_test(f"Username {username} - ID correct", False, f"ID attendu: {expected_id}, trouvé: {user['id']}")
                
                # Vérifier le rôle
                if user["role"] == role:
                    self.log_test(f"Username {username} - Rôle correct", True, f"Rôle '{role}' confirmé")
                else:
                    self.log_test(f"Username {username} - Rôle correct", False, f"Rôle attendu: '{role}', trouvé: '{user['role']}'")
                
                # Vérifier que l'utilisateur est actif
                if user.get("actif", False):
                    self.log_test(f"Username {username} - Statut actif", True, "Utilisateur actif")
                else:
                    self.log_test(f"Username {username} - Statut actif", False, "Utilisateur inactif")
                    
            else:
                # Vérifier par ID si username pas trouvé
                if expected_id in users_by_id:
                    user = users_by_id[expected_id]
                    current_username = user.get("username", "AUCUN")
                    self.log_test(f"Username {username} - Trouvé par ID", False, 
                                f"ID {expected_id} trouvé mais username est '{current_username}' au lieu de '{username}'")
                else:
                    self.log_test(f"Username {username} - Existence", False, f"Utilisateur avec username '{username}' ou ID '{expected_id}' non trouvé")
        
        return found_users
    
    def test_get_sections(self):
        """Test GET /api/sections"""
        try:
            response = self.session.get(f"{BASE_URL}/sections")
            
            if response.status_code == 200:
                sections = response.json()
                self.log_test("GET /api/sections", True, f"{len(sections)} sections trouvées")
                return sections
            else:
                self.log_test("GET /api/sections", False, f"Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("GET /api/sections", False, f"Exception: {str(e)}")
            return []
    
    def test_get_activities(self):
        """Test GET /api/activities"""
        try:
            response = self.session.get(f"{BASE_URL}/activities")
            
            if response.status_code == 200:
                activities = response.json()
                self.log_test("GET /api/activities", True, f"{len(activities)} activités trouvées")
                return activities
            else:
                self.log_test("GET /api/activities", False, f"Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("GET /api/activities", False, f"Exception: {str(e)}")
            return []
    
    def test_get_presences(self):
        """Test GET /api/presences"""
        try:
            response = self.session.get(f"{BASE_URL}/presences")
            
            if response.status_code == 200:
                presences = response.json()
                self.log_test("GET /api/presences", True, f"{len(presences)} présences trouvées")
                return presences
            else:
                self.log_test("GET /api/presences", False, f"Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("GET /api/presences", False, f"Exception: {str(e)}")
            return []
    
    def test_get_roles(self):
        """Test GET /api/roles"""
        try:
            response = self.session.get(f"{BASE_URL}/roles")
            
            if response.status_code == 200:
                roles = response.json()
                self.log_test("GET /api/roles", True, f"{len(roles)} rôles trouvés")
                
                # Vérifier les rôles personnalisés attendus
                role_names = [role["name"] for role in roles]
                expected_custom_roles = ["Adjudant-Chef d'escadron", "Sergent de section", "Adjudant d'escadron"]
                
                for expected_role in expected_custom_roles:
                    if expected_role in role_names:
                        self.log_test(f"Rôle personnalisé '{expected_role}'", True, "Rôle trouvé")
                    else:
                        self.log_test(f"Rôle personnalisé '{expected_role}'", False, "Rôle non trouvé")
                
                return roles
            else:
                self.log_test("GET /api/roles", False, f"Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("GET /api/roles", False, f"Exception: {str(e)}")
            return []
    
    def test_get_subgroups(self, sections):
        """Test GET /api/sections/{section_id}/subgroups pour chaque section"""
        total_subgroups = 0
        
        for section in sections:
            section_id = section["id"]
            section_name = section["nom"]
            
            try:
                response = self.session.get(f"{BASE_URL}/sections/{section_id}/subgroups")
                
                if response.status_code == 200:
                    subgroups = response.json()
                    total_subgroups += len(subgroups)
                    self.log_test(f"GET /api/sections/{section_name}/subgroups", True, 
                                f"{len(subgroups)} sous-groupes trouvés")
                else:
                    self.log_test(f"GET /api/sections/{section_name}/subgroups", False, 
                                f"Erreur {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"GET /api/sections/{section_name}/subgroups", False, f"Exception: {str(e)}")
        
        self.log_test("Total sous-groupes", True, f"{total_subgroups} sous-groupes au total")
        return total_subgroups
    
    def test_section_managers(self, sections, users):
        """Vérifier l'assignation des responsables de sections"""
        users_by_id = {user["id"]: user for user in users}
        
        sections_with_managers = 0
        for section in sections:
            section_name = section["nom"]
            manager_id = section.get("responsable_id")
            
            if manager_id:
                if manager_id in users_by_id:
                    manager = users_by_id[manager_id]
                    sections_with_managers += 1
                    self.log_test(f"Section '{section_name}' - Responsable assigné", True, 
                                f"Responsable: {manager['prenom']} {manager['nom']} ({manager['role']})")
                else:
                    self.log_test(f"Section '{section_name}' - Responsable valide", False, 
                                f"Responsable ID {manager_id} non trouvé dans les utilisateurs")
            else:
                self.log_test(f"Section '{section_name}' - Responsable assigné", False, "Aucun responsable assigné")
        
        self.log_test("Sections avec responsables", True, f"{sections_with_managers}/{len(sections)} sections ont un responsable")
    
    def test_custom_role_users(self, users):
        """Vérifier les utilisateurs avec rôles personnalisés"""
        custom_role_users = []
        expected_roles = ["Adjudant-Chef d'escadron", "Sergent de section", "Adjudant d'escadron"]
        
        for user in users:
            if user["role"] in expected_roles:
                custom_role_users.append(user)
                self.log_test(f"Utilisateur rôle personnalisé - {user['prenom']} {user['nom']}", True, 
                            f"Rôle: {user['role']}, Username: {user.get('username', 'AUCUN')}")
        
        if len(custom_role_users) >= 3:
            self.log_test("Utilisateurs rôles personnalisés", True, f"{len(custom_role_users)} utilisateurs avec rôles personnalisés trouvés")
        else:
            self.log_test("Utilisateurs rôles personnalisés", False, f"Seulement {len(custom_role_users)} utilisateurs avec rôles personnalisés trouvés (attendu: au moins 3)")
        
        return custom_role_users
    
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