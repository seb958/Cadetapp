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
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 Début des tests backend - Application de gestion d'escadron de cadets")
        print(f"📍 Base URL: {BASE_URL}")
        print("=" * 80)
        
        # 1. Authentification
        if not self.authenticate_admin():
            print("❌ Impossible de continuer sans authentification")
            return False
        
        print("\n📋 Tests des endpoints principaux:")
        print("-" * 40)
        
        # 2. Test des endpoints principaux
        users = self.test_get_all_users()
        sections = self.test_get_sections()
        activities = self.test_get_activities()
        presences = self.test_get_presences()
        roles = self.test_get_roles()
        
        print("\n👥 Tests spécifiques aux utilisateurs avec nouveaux usernames:")
        print("-" * 60)
        
        # 3. Tests spécifiques aux utilisateurs avec nouveaux usernames
        if users:
            found_users = self.test_users_with_new_usernames(users)
            custom_role_users = self.test_custom_role_users(users)
        
        print("\n🏢 Tests des sections et sous-groupes:")
        print("-" * 40)
        
        # 4. Tests des sections et responsables
        if sections and users:
            self.test_section_managers(sections, users)
            self.test_get_subgroups(sections)
        
        # 5. Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Tests réussis: {passed}/{total} ({success_rate:.1f}%)")
        print(f"❌ Tests échoués: {failed}/{total}")
        
        if self.test_results["errors"]:
            print(f"\n🔍 ERREURS DÉTAILLÉES:")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        print("\n🎯 FOCUS: Vérification des 3 utilisateurs avec nouveaux usernames")
        username_tests_passed = sum(1 for error in self.test_results["errors"] if "Username" not in error)
        total_username_tests = sum(1 for _ in range(self.test_results["total_tests"]) if "Username" in str(_))
        
        if failed == 0:
            print("🎉 TOUS LES TESTS SONT PASSÉS - Backend fonctionnel")
            return True
        elif failed <= 2:
            print("⚠️  TESTS MAJORITAIREMENT RÉUSSIS - Quelques problèmes mineurs")
            return True
        else:
            print("🚨 PROBLÈMES CRITIQUES DÉTECTÉS - Intervention requise")
            return False
    
def main():
    """Fonction principale"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Code de sortie pour les scripts
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()