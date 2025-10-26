#!/usr/bin/env python3
"""
Tests pour vérifier les permissions présences avec has_admin_privileges
Demande spécifique: Tester que les cadets avec has_admin_privileges=True peuvent prendre les présences
"""

import requests
import json
from datetime import datetime, date
import sys

# Configuration
BASE_URL = "https://squadcommand.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_test(self, name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.test_details.append(f"{status} - {name}: {details}")
        print(f"{status} - {name}: {details}")
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"RÉSUMÉ DES TESTS - PERMISSIONS PRÉSENCES has_admin_privileges")
        print(f"{'='*80}")
        print(f"Total: {self.total_tests} | Réussis: {self.passed_tests} | Échoués: {self.failed_tests}")
        print(f"Taux de réussite: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*80}")

def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def login_user(username, password):
    """Connexion utilisateur et récupération du token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["user"]
        else:
            return None, None
    except Exception as e:
        print(f"Erreur lors de la connexion: {e}")
        return None, None

def generate_password_for_user(admin_token, user_id):
    """Génère un mot de passe temporaire pour un utilisateur"""
    try:
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/generate-password",
            headers=get_auth_headers(admin_token)
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Erreur génération mot de passe: {e}")
        return None
def test_permissions_presences_admin_privileges():
    """Test principal des permissions présences avec has_admin_privileges"""
    results = TestResults()
    
    print("🔐 TESTS PERMISSIONS PRÉSENCES - has_admin_privileges")
    print("="*80)
    
    # 1. Connexion admin
    print("\n1️⃣ CONNEXION ADMINISTRATEUR")
    admin_token, admin_user = login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
    
    if not admin_token:
        results.add_test("Connexion admin", False, "Impossible de se connecter en tant qu'admin")
        results.print_summary()
        return results
    
    results.add_test("Connexion admin", True, f"Connecté: {admin_user['prenom']} {admin_user['nom']}")
    
    # 2. Récupérer la liste des utilisateurs
    print("\n2️⃣ RÉCUPÉRATION LISTE UTILISATEURS")
    try:
        response = requests.get(f"{BASE_URL}/users", headers=get_auth_headers(admin_token))
        if response.status_code == 200:
            users = response.json()
            results.add_test("GET /api/users", True, f"{len(users)} utilisateurs trouvés")
        else:
            results.add_test("GET /api/users", False, f"Status: {response.status_code}")
            results.print_summary()
            return results
    except Exception as e:
        results.add_test("GET /api/users", False, f"Erreur: {e}")
        results.print_summary()
        return results
    
    def find_user_by_role_keywords(self, keywords):
        """Trouver un utilisateur par mots-clés dans le rôle"""
        for role, users in self.users_cache.items():
            if any(keyword.lower() in role for keyword in keywords):
                if users:
                    return users[0]  # Retourner le premier utilisateur trouvé
        return None
    
    def authenticate_user(self, username, password=None):
        """Authentifier un utilisateur spécifique"""
        # Mots de passe générés pour les utilisateurs de test
        user_passwords = {
            "adjudantchef_descadron": "c8iLdxgx",
            "jmoreau": "JWsrp3Od", 
            "sergent_de_section": "Tilr5pxu",
            "aadministrateur": "admin123"
        }
        
        if password is None:
            password = user_passwords.get(username, "admin123")
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                return data["access_token"]
            else:
                return None
        except Exception as e:
            return None
    
    def test_anti_auto_evaluation(self):
        """Test 1: Anti-Auto-Évaluation (Critique)"""
        print("\n=== TEST 1: ANTI-AUTO-ÉVALUATION ===")
        
        # Trouver des utilisateurs avec différents rôles
        test_users = []
        
        # État-Major (Adjudant d'escadron, Adjudant-chef d'escadron)
        etat_major = self.find_user_by_role_keywords(["adjudant"])
        if etat_major:
            test_users.append(("État-Major", etat_major))
        
        # Commandant de section
        commandant = self.find_user_by_role_keywords(["commandant"])
        if commandant:
            test_users.append(("Commandant de section", commandant))
        
        # Sergent de section
        sergent = self.find_user_by_role_keywords(["sergent"])
        if sergent:
            test_users.append(("Sergent de section", sergent))
        
        if not test_users:
            self.log_test("Anti-Auto-Évaluation - Utilisateurs trouvés", False, "Aucun utilisateur avec rôles requis trouvé")
            return
        
        # Tester l'auto-évaluation pour chaque type d'utilisateur
        for role_name, user in test_users:
            # Essayer d'authentifier l'utilisateur
            user_token = self.authenticate_user(user.get("username", ""))
            
            if not user_token:
                self.log_test(f"Anti-Auto-Évaluation - Auth {role_name}", False, f"Impossible d'authentifier {user.get('username', 'N/A')}")
                continue
            
            # Créer une session pour cet utilisateur
            user_session = requests.Session()
            user_session.headers.update({"Authorization": f"Bearer {user_token}"})
            
            # Tenter de créer une inspection où l'utilisateur s'inspecte lui-même
            inspection_data = {
                "cadet_id": user["id"],  # L'utilisateur s'inspecte lui-même
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Propreté générale": 4,
                    "Ajustement": 3,
                    "Accessoires": 4
                },
                "commentaire": "Test auto-évaluation"
            }
            
            try:
                response = user_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                
                if response.status_code == 403:
                    response_data = response.json()
                    expected_message = "Vous ne pouvez pas inspecter votre propre uniforme"
                    
                    if expected_message in response_data.get("detail", ""):
                        self.log_test(f"Anti-Auto-Évaluation - {role_name}", True, 
                                    f"Erreur 403 correcte avec message attendu")
                    else:
                        self.log_test(f"Anti-Auto-Évaluation - {role_name}", False, 
                                    f"Erreur 403 mais message incorrect: {response_data.get('detail', 'N/A')}")
                else:
                    self.log_test(f"Anti-Auto-Évaluation - {role_name}", False, 
                                f"Status attendu: 403, reçu: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Anti-Auto-Évaluation - {role_name}", False, f"Exception: {str(e)}")
    
    def test_etat_major_permissions(self):
        """Test 2: Permissions État-Major"""
        print("\n=== TEST 2: PERMISSIONS ÉTAT-MAJOR ===")
        
        # Trouver un membre de l'État-Major
        etat_major_user = self.find_user_by_role_keywords(["adjudant"])
        
        if not etat_major_user:
            self.log_test("État-Major - Utilisateur trouvé", False, "Aucun utilisateur État-Major trouvé")
            return
        
        # Authentifier l'utilisateur État-Major
        user_token = self.authenticate_user(etat_major_user.get("username", ""))
        
        if not user_token:
            self.log_test("État-Major - Authentification", False, f"Impossible d'authentifier {etat_major_user.get('username', 'N/A')}")
            return
        
        self.log_test("État-Major - Authentification", True, f"Utilisateur {etat_major_user.get('prenom', '')} {etat_major_user.get('nom', '')} authentifié")
        
        # Créer une session pour cet utilisateur
        user_session = requests.Session()
        user_session.headers.update({"Authorization": f"Bearer {user_token}"})
        
        # Trouver des cadets d'autres sections à inspecter
        cadets_to_inspect = []
        for role, users in self.users_cache.items():
            if "cadet" in role and role != etat_major_user.get("role", "").lower():
                for user in users:
                    if user["id"] != etat_major_user["id"]:  # Pas lui-même
                        cadets_to_inspect.append(user)
                        if len(cadets_to_inspect) >= 2:  # Limiter à 2 tests
                            break
            if len(cadets_to_inspect) >= 2:
                break
        
        if not cadets_to_inspect:
            self.log_test("État-Major - Cadets à inspecter", False, "Aucun cadet trouvé pour test")
            return
        
        # Tester l'inspection de cadets d'autres sections
        for i, cadet in enumerate(cadets_to_inspect):
            inspection_data = {
                "cadet_id": cadet["id"],
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Propreté générale": 4,
                    "Ajustement": 3,
                    "Accessoires": 4
                },
                "commentaire": f"Test inspection État-Major #{i+1}"
            }
            
            try:
                response = user_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                
                if response.status_code == 200 or response.status_code == 201:
                    self.log_test(f"État-Major - Inspection cadet {i+1}", True, 
                                f"Inspection réussie de {cadet.get('prenom', '')} {cadet.get('nom', '')}")
                else:
                    self.log_test(f"État-Major - Inspection cadet {i+1}", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test(f"État-Major - Inspection cadet {i+1}", False, f"Exception: {str(e)}")
    
    def test_section_permissions(self):
        """Test 3: Permissions Section"""
        print("\n=== TEST 3: PERMISSIONS SECTION ===")
        
        # Trouver un Commandant ou Sergent de section
        section_leader = self.find_user_by_role_keywords(["commandant", "sergent"])
        
        if not section_leader:
            self.log_test("Section - Chef trouvé", False, "Aucun chef de section trouvé")
            return
        
        # Authentifier le chef de section
        user_token = self.authenticate_user(section_leader.get("username", ""))
        
        if not user_token:
            self.log_test("Section - Authentification", False, f"Impossible d'authentifier {section_leader.get('username', 'N/A')}")
            return
        
        self.log_test("Section - Authentification", True, f"Chef {section_leader.get('prenom', '')} {section_leader.get('nom', '')} authentifié")
        
        # Créer une session pour cet utilisateur
        user_session = requests.Session()
        user_session.headers.update({"Authorization": f"Bearer {user_token}"})
        
        # Test 1: Essayer d'inspecter un cadet d'une autre section (doit échouer)
        other_section_cadet = None
        for role, users in self.users_cache.items():
            for user in users:
                if (user["id"] != section_leader["id"] and 
                    user.get("section_id") != section_leader.get("section_id") and
                    user.get("section_id") is not None):
                    other_section_cadet = user
                    break
            if other_section_cadet:
                break
        
        if other_section_cadet:
            inspection_data = {
                "cadet_id": other_section_cadet["id"],
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Propreté générale": 4,
                    "Ajustement": 3
                },
                "commentaire": "Test inspection autre section"
            }
            
            try:
                response = user_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                
                if response.status_code == 403:
                    self.log_test("Section - Refus autre section", True, 
                                "Inspection d'autre section correctement refusée (403)")
                else:
                    self.log_test("Section - Refus autre section", False, 
                                f"Status attendu: 403, reçu: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Section - Refus autre section", False, f"Exception: {str(e)}")
        else:
            self.log_test("Section - Cadet autre section", False, "Aucun cadet d'autre section trouvé pour test")
        
        # Test 2: Inspecter un cadet de sa propre section (doit réussir)
        same_section_cadet = None
        for role, users in self.users_cache.items():
            for user in users:
                if (user["id"] != section_leader["id"] and 
                    user.get("section_id") == section_leader.get("section_id") and
                    user.get("section_id") is not None):
                    same_section_cadet = user
                    break
            if same_section_cadet:
                break
        
        if same_section_cadet:
            inspection_data = {
                "cadet_id": same_section_cadet["id"],
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Propreté générale": 4,
                    "Ajustement": 3,
                    "Accessoires": 4
                },
                "commentaire": "Test inspection même section"
            }
            
            try:
                response = user_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                
                if response.status_code == 200 or response.status_code == 201:
                    self.log_test("Section - Inspection même section", True, 
                                f"Inspection de sa section réussie")
                else:
                    self.log_test("Section - Inspection même section", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test("Section - Inspection même section", False, f"Exception: {str(e)}")
        else:
            self.log_test("Section - Cadet même section", False, "Aucun cadet de même section trouvé pour test")
    
    def test_regression(self):
        """Test 4: Régression - Vérifier que les fonctionnalités existantes marchent"""
        print("\n=== TEST 4: RÉGRESSION ===")
        
        # Test 1: GET /api/users fonctionne toujours
        try:
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Régression - GET /api/users", True, f"{len(users)} utilisateurs récupérés")
            else:
                self.log_test("Régression - GET /api/users", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Régression - GET /api/users", False, f"Exception: {str(e)}")
        
        # Test 2: Inspection valide par admin fonctionne toujours
        if len(self.users_cache) > 0:
            # Trouver un cadet à inspecter (pas l'admin lui-même)
            cadet_to_inspect = None
            for role, users in self.users_cache.items():
                for user in users:
                    if user["id"] != "0c9b2a6e-2d0e-4590-9e83-3071b411e591":  # Pas l'admin
                        cadet_to_inspect = user
                        break
                if cadet_to_inspect:
                    break
            
            if cadet_to_inspect:
                inspection_data = {
                    "cadet_id": cadet_to_inspect["id"],
                    "uniform_type": "C5 - Tenue d'Entraînement",
                    "criteria_scores": {
                        "Propreté générale": 3,
                        "Ajustement": 4,
                        "Accessoires": 2,
                        "État général": 3
                    },
                    "commentaire": "Test régression - inspection valide par admin"
                }
                
                try:
                    response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                    
                    if response.status_code == 200 or response.status_code == 201:
                        self.log_test("Régression - Inspection valide admin", True, 
                                    f"Inspection admin réussie")
                    else:
                        self.log_test("Régression - Inspection valide admin", False, 
                                    f"Status: {response.status_code}, Response: {response.text}")
                        
                except Exception as e:
                    self.log_test("Régression - Inspection valide admin", False, f"Exception: {str(e)}")
            else:
                self.log_test("Régression - Cadet pour inspection", False, "Aucun cadet trouvé pour test")
        
        # Test 3: GET /api/uniform-inspections fonctionne
        try:
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            if response.status_code == 200:
                inspections = response.json()
                self.log_test("Régression - GET /api/uniform-inspections", True, 
                            f"{len(inspections)} inspections récupérées")
            else:
                self.log_test("Régression - GET /api/uniform-inspections", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Régression - GET /api/uniform-inspections", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS - PERMISSIONS INSPECTION + ANTI-AUTO-ÉVALUATION")
        print(f"Base URL: {BASE_URL}")
        print(f"Admin: {ADMIN_USERNAME}")
        
        # Authentification admin
        if not self.authenticate_admin():
            print("❌ ÉCHEC - Impossible de s'authentifier en tant qu'admin")
            return False
        
        # Récupérer les utilisateurs
        users = self.get_users()
        if not users:
            print("❌ ÉCHEC - Impossible de récupérer les utilisateurs")
            return False
        
        # Afficher les rôles disponibles pour debug
        print(f"\n📋 Rôles disponibles: {list(self.users_cache.keys())}")
        
        # Exécuter les tests
        self.test_anti_auto_evaluation()
        self.test_etat_major_permissions()
        self.test_section_permissions()
        self.test_regression()
        
        # Résumé final
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests} tests")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   - {test['name']}: {test['details']}")
        
        print("\n🎯 FOCUS: Validation anti-auto-évaluation (priorité maximale)")
        
        # Vérifier si les tests critiques ont réussi
        anti_eval_tests = [t for t in self.test_results if "Anti-Auto-Évaluation" in t["name"]]
        if anti_eval_tests:
            anti_eval_success = all(t["success"] for t in anti_eval_tests)
            if anti_eval_success:
                print("✅ CRITIQUE: Anti-auto-évaluation fonctionne correctement")
            else:
                print("❌ CRITIQUE: Problèmes détectés dans l'anti-auto-évaluation")

def main():
    """Fonction principale"""
    test_runner = TestRunner()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 Tests terminés avec succès")
        return 0
    else:
        print("\n💥 Échec des tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())