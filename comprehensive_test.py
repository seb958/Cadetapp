#!/usr/bin/env python3
"""
Tests Complets - Vérification Correctif Permissions selon Review Request
Focus: Tests requis spécifiques de la demande
"""

import requests
import json
from datetime import datetime, date
import sys

# Configuration
BASE_URL = "https://commandhub-3.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class ComprehensivePermissionTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
    
    def authenticate_admin(self):
        """Authentification admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_test("Authentification Admin", True, f"Token obtenu pour {data['user']['nom']}")
                return True
            else:
                self.log_test("Authentification Admin", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentification Admin", False, f"Erreur: {str(e)}")
            return False
    
    def authenticate_user(self, username, password):
        """Authentifier un utilisateur spécifique"""
        try:
            user_session = requests.Session()
            response = user_session.post(f"{BASE_URL}/auth/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user_session.headers.update({"Authorization": f"Bearer {token}"})
                return user_session, data["user"]
            else:
                return None, None
        except Exception as e:
            return None, None
    
    def test_anti_auto_evaluation_comprehensive(self):
        """Test 1: Anti-Auto-Évaluation (Re-test selon demande)"""
        print("\n=== TEST 1: ANTI-AUTO-ÉVALUATION (RE-TEST) ===")
        
        # Test avec admin
        admin_inspection = {
            "cadet_id": "0c9b2a6e-2d0e-4590-9e83-3071b411e591",  # ID admin (supposé)
            "uniform_type": "C1 - Tenue de Parade",
            "criteria_scores": {"Propreté": 4, "Ajustement": 4},
            "commentaire": "Test auto-évaluation admin"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/uniform-inspections", json=admin_inspection)
            if response.status_code == 403:
                response_data = response.json()
                if "Vous ne pouvez pas inspecter votre propre uniforme" in response_data.get("detail", ""):
                    self.log_test("Anti-Auto-Évaluation Admin", True, "403 avec message correct")
                else:
                    self.log_test("Anti-Auto-Évaluation Admin", False, f"Message incorrect: {response_data.get('detail')}")
            else:
                self.log_test("Anti-Auto-Évaluation Admin", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Anti-Auto-Évaluation Admin", False, f"Erreur: {str(e)}")
        
        # Test avec autres rôles
        test_users = [
            ("adjudantchef_descadron", "c8iLdxgx", "Adjudant-Chef"),
            ("jmoreau", "JWsrp3Od", "Commandant de section"),
            ("sergent_de_section", "Tilr5pxu", "Sergent de section")
        ]
        
        for username, password, role_name in test_users:
            user_session, user_data = self.authenticate_user(username, password)
            if user_session and user_data:
                inspection_data = {
                    "cadet_id": user_data["id"],
                    "uniform_type": "C1 - Tenue de Parade",
                    "criteria_scores": {"Propreté": 4, "Ajustement": 3},
                    "commentaire": f"Test auto-évaluation {role_name}"
                }
                
                try:
                    response = user_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    if response.status_code == 403:
                        response_data = response.json()
                        if "Vous ne pouvez pas inspecter votre propre uniforme" in response_data.get("detail", ""):
                            self.log_test(f"Anti-Auto-Évaluation {role_name}", True, "403 avec message correct")
                        else:
                            self.log_test(f"Anti-Auto-Évaluation {role_name}", False, f"Message incorrect")
                    else:
                        self.log_test(f"Anti-Auto-Évaluation {role_name}", False, f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"Anti-Auto-Évaluation {role_name}", False, f"Erreur: {str(e)}")
    
    def test_section_permissions_correctif(self):
        """Test 2: Permissions Section (CORRECTIF) - Focus principal"""
        print("\n=== TEST 2: PERMISSIONS SECTION (CORRECTIF) ===")
        
        # Récupérer les utilisateurs et sections
        users_response = self.session.get(f"{BASE_URL}/users")
        if users_response.status_code != 200:
            self.log_test("Récupération données", False, "Impossible de récupérer les utilisateurs")
            return
        
        users = users_response.json()
        
        # Identifier les commandants de section avec rôles personnalisés
        section_commanders = []
        for user in users:
            role = user.get("role", "").lower()
            if ("commandant" in role and "section" in role) or ("sergent" in role and "section" in role):
                if user.get("section_id") and user.get("username"):
                    section_commanders.append(user)
        
        print(f"Commandants de section trouvés: {len(section_commanders)}")
        
        # Test avec Jean Moreau (Commandant de section)
        jmoreau_session, jmoreau_data = self.authenticate_user("jmoreau", "JWsrp3Od")
        if jmoreau_session and jmoreau_data:
            print(f"Testing avec {jmoreau_data['prenom']} {jmoreau_data['nom']} - {jmoreau_data['role']}")
            print(f"Section ID: {jmoreau_data.get('section_id')}")
            
            # Trouver des cadets d'autres sections
            other_section_cadets = []
            same_section_cadets = []
            
            for user in users:
                if user["id"] != jmoreau_data["id"] and user.get("section_id"):
                    if user.get("section_id") == jmoreau_data.get("section_id"):
                        same_section_cadets.append(user)
                    else:
                        other_section_cadets.append(user)
            
            # Test 1: NE PEUT PAS inspecter des cadets d'autres sections (doit être 403)
            if other_section_cadets:
                target_cadet = other_section_cadets[0]
                inspection_data = {
                    "cadet_id": target_cadet["id"],
                    "uniform_type": "C1 - Tenue de Parade",
                    "criteria_scores": {"Propreté": 3, "Ajustement": 2},
                    "commentaire": "Test inspection autre section"
                }
                
                try:
                    response = jmoreau_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    if response.status_code == 403:
                        self.log_test("Commandant section - Refus autre section", True, 
                                    f"Correctement refusé d'inspecter {target_cadet['prenom']} {target_cadet['nom']} (autre section)")
                    else:
                        self.log_test("Commandant section - Refus autre section", False, 
                                    f"Status: {response.status_code}, devrait être 403")
                except Exception as e:
                    self.log_test("Commandant section - Refus autre section", False, f"Erreur: {str(e)}")
            
            # Test 2: PEUT inspecter les cadets de sa propre section (doit être 200)
            if same_section_cadets:
                target_cadet = same_section_cadets[0]
                inspection_data = {
                    "cadet_id": target_cadet["id"],
                    "uniform_type": "C1 - Tenue de Parade",
                    "criteria_scores": {"Propreté": 4, "Ajustement": 3},
                    "commentaire": "Test inspection même section"
                }
                
                try:
                    response = jmoreau_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    if response.status_code == 200:
                        self.log_test("Commandant section - Inspection même section", True, 
                                    f"Peut inspecter {target_cadet['prenom']} {target_cadet['nom']} (même section)")
                    else:
                        self.log_test("Commandant section - Inspection même section", False, 
                                    f"Status: {response.status_code}, devrait être 200")
                except Exception as e:
                    self.log_test("Commandant section - Inspection même section", False, f"Erreur: {str(e)}")
        
        # Test avec Sergent de section
        sergent_session, sergent_data = self.authenticate_user("sergent_de_section", "Tilr5pxu")
        if sergent_session and sergent_data:
            print(f"Testing avec {sergent_data['prenom']} {sergent_data['nom']} - {sergent_data['role']}")
            
            # Trouver des cadets d'autres sections
            other_section_cadets = [u for u in users if u["id"] != sergent_data["id"] and 
                                  u.get("section_id") and u.get("section_id") != sergent_data.get("section_id")]
            
            if other_section_cadets:
                target_cadet = other_section_cadets[0]
                inspection_data = {
                    "cadet_id": target_cadet["id"],
                    "uniform_type": "C5 - Tenue d'Entraînement",
                    "criteria_scores": {"Propreté": 3, "Ajustement": 2, "Accessoires": 4},
                    "commentaire": "Test sergent inspection autre section"
                }
                
                try:
                    response = sergent_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    if response.status_code == 403:
                        self.log_test("Sergent section - Refus autre section", True, 
                                    f"Correctement refusé d'inspecter autre section")
                    else:
                        self.log_test("Sergent section - Refus autre section", False, 
                                    f"Status: {response.status_code}, devrait être 403")
                except Exception as e:
                    self.log_test("Sergent section - Refus autre section", False, f"Erreur: {str(e)}")
    
    def test_etat_major_permissions(self):
        """Test 3: Permissions État-Major"""
        print("\n=== TEST 3: PERMISSIONS ÉTAT-MAJOR ===")
        
        # Test avec Adjudant d'escadron
        adj_session, adj_data = self.authenticate_user("adjudant_descadron", "admin123")
        if not adj_session:
            # Générer un mot de passe si nécessaire
            try:
                response = self.session.post(f"{BASE_URL}/users/a01b2ec0-64d0-4e35-8305-5db28e3efa97/generate-password")
                if response.status_code == 200:
                    password_data = response.json()
                    password = password_data["temporary_password"]
                    adj_session, adj_data = self.authenticate_user("adjudant_descadron", password)
            except:
                pass
        
        if adj_session and adj_data:
            # Récupérer un cadet à inspecter
            users_response = self.session.get(f"{BASE_URL}/users")
            if users_response.status_code == 200:
                users = users_response.json()
                cadets = [u for u in users if u["id"] != adj_data["id"] and u.get("role") == "cadet"]
                
                if cadets:
                    target_cadet = cadets[0]
                    inspection_data = {
                        "cadet_id": target_cadet["id"],
                        "uniform_type": "C1 - Tenue de Parade",
                        "criteria_scores": {"Propreté": 4, "Ajustement": 3, "Accessoires": 4},
                        "commentaire": "Test inspection État-Major"
                    }
                    
                    try:
                        response = adj_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                        if response.status_code == 200:
                            self.log_test("État-Major - Inspection n'importe quel cadet", True, 
                                        f"Adjudant d'escadron peut inspecter n'importe quel cadet")
                        else:
                            self.log_test("État-Major - Inspection n'importe quel cadet", False, 
                                        f"Status: {response.status_code}")
                    except Exception as e:
                        self.log_test("État-Major - Inspection n'importe quel cadet", False, f"Erreur: {str(e)}")
    
    def test_regression(self):
        """Test 4: Régression"""
        print("\n=== TEST 4: RÉGRESSION ===")
        
        # GET /api/users fonctionne
        try:
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Régression - GET /api/users", True, f"{len(users)} utilisateurs")
            else:
                self.log_test("Régression - GET /api/users", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Régression - GET /api/users", False, f"Erreur: {str(e)}")
        
        # GET /api/uniform-inspections fonctionne
        try:
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            if response.status_code == 200:
                inspections = response.json()
                self.log_test("Régression - GET /api/uniform-inspections", True, f"{len(inspections)} inspections")
            else:
                self.log_test("Régression - GET /api/uniform-inspections", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Régression - GET /api/uniform-inspections", False, f"Erreur: {str(e)}")
        
        # Inspections valides par admin fonctionnent
        users_response = self.session.get(f"{BASE_URL}/users")
        if users_response.status_code == 200:
            users = users_response.json()
            cadets = [u for u in users if u.get("role") == "cadet"]
            
            if cadets:
                target_cadet = cadets[0]
                inspection_data = {
                    "cadet_id": target_cadet["id"],
                    "uniform_type": "C5 - Tenue d'Entraînement",
                    "criteria_scores": {"Propreté": 3, "Ajustement": 4, "Accessoires": 2},
                    "commentaire": "Test régression admin"
                }
                
                try:
                    response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    if response.status_code == 200:
                        self.log_test("Régression - Inspections admin", True, "Admin peut toujours inspecter")
                    else:
                        self.log_test("Régression - Inspections admin", False, f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test("Régression - Inspections admin", False, f"Erreur: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests selon la review request"""
        print("🚀 TESTS COMPLETS - VÉRIFICATION CORRECTIF PERMISSIONS")
        print(f"Base URL: {BASE_URL}")
        print(f"Admin: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print("Focus: Vérifier que les chefs de section avec rôles personnalisés ne peuvent inspecter que leur section")
        
        # Authentification admin
        if not self.authenticate_admin():
            return False
        
        # Exécuter les tests requis
        self.test_anti_auto_evaluation_comprehensive()
        self.test_section_permissions_correctif()
        self.test_etat_major_permissions()
        self.test_regression()
        
        # Résumé final
        print(f"\n{'='*60}")
        print("RÉSUMÉ FINAL - CORRECTIF PERMISSIONS")
        print(f"{'='*60}")
        
        passed = len([r for r in self.test_results if r["success"]])
        total = len(self.test_results)
        
        print(f"Tests passés: {passed}/{total} ({(passed/total*100):.1f}%)")
        
        # Analyser les résultats critiques
        anti_eval_tests = [r for r in self.test_results if "Anti-Auto-Évaluation" in r["test"]]
        section_tests = [r for r in self.test_results if "section" in r["test"].lower() and "refus" in r["test"].lower()]
        
        anti_eval_ok = all(t["success"] for t in anti_eval_tests)
        section_fix_ok = all(t["success"] for t in section_tests)
        
        print(f"\n🎯 RÉSULTATS CRITIQUES:")
        print(f"✅ Anti-Auto-Évaluation: {'OK' if anti_eval_ok else 'ÉCHEC'}")
        print(f"✅ Correctif Permissions Section: {'OK' if section_fix_ok else 'ÉCHEC'}")
        
        if anti_eval_ok and section_fix_ok:
            print(f"\n🎉 CORRECTIF VALIDÉ - Permissions section corrigées avec succès!")
        else:
            print(f"\n❌ PROBLÈMES DÉTECTÉS - Correctif incomplet")
        
        # Détail des échecs
        failures = [r for r in self.test_results if not r["success"]]
        if failures:
            print(f"\n❌ ÉCHECS ({len(failures)}):")
            for failure in failures:
                print(f"   - {failure['test']}: {failure['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = ComprehensivePermissionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)