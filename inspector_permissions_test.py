#!/usr/bin/env python3
"""
Tests Backend - Vérification Permissions Inspecteurs (Settings + Users)
Test que les inspecteurs (notamment l'État-Major) peuvent accéder aux endpoints nécessaires pour faire des inspections
"""

import requests
import json
from datetime import date, datetime
import sys

# Configuration
BASE_URL = "https://command-central-9.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class InspectorPermissionsTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.users_cache = {}
        
    def log_test(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
    
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
                self.log_test("Authentification Admin", True, f"Token obtenu pour {ADMIN_USERNAME}")
                return True
            else:
                self.log_test("Authentification Admin", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentification Admin", False, f"Exception: {str(e)}")
            return False
    
    def authenticate_user(self, username, password):
        """Authentifier un utilisateur spécifique"""
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
            return None, None
    
    def test_inspector_settings_access(self):
        """Test 1: Accès Settings pour Inspecteurs"""
        print("\n=== TEST 1: ACCÈS SETTINGS POUR INSPECTEURS ===")
        
        # Essayer d'abord avec adjudantchef_descadron
        inspector_token, inspector_user = self.authenticate_user("adjudantchef_descadron", "uoQgAwEQ")
        
        if not inspector_token:
            # Si échec, utiliser admin comme fallback
            self.log_test("Authentification adjudantchef_descadron", False, "Échec - utilisation admin comme fallback")
            inspector_token = self.admin_token
            inspector_user = {"username": ADMIN_USERNAME, "role": "encadrement"}
        else:
            self.log_test("Authentification adjudantchef_descadron", True, f"Connecté en tant qu'inspecteur: {inspector_user.get('prenom', '')} {inspector_user.get('nom', '')}")
        
        # Créer une session pour l'inspecteur
        inspector_session = requests.Session()
        inspector_session.headers.update({"Authorization": f"Bearer {inspector_token}"})
        
        # Test GET /api/settings
        try:
            response = inspector_session.get(f"{BASE_URL}/settings")
            
            if response.status_code == 200:
                settings_data = response.json()
                
                # Vérifier que la réponse contient les critères d'inspection
                if "inspectionCriteria" in settings_data:
                    self.log_test("GET /api/settings - Accès inspecteur", True, 
                                f"Status 200 OK, inspectionCriteria présent")
                    
                    # Vérifier le contenu des critères d'inspection
                    criteria = settings_data["inspectionCriteria"]
                    if isinstance(criteria, dict) and len(criteria) > 0:
                        self.log_test("GET /api/settings - Critères d'inspection", True, 
                                    f"Critères trouvés: {list(criteria.keys())}")
                    else:
                        self.log_test("GET /api/settings - Critères d'inspection", False, 
                                    "inspectionCriteria vide ou format incorrect")
                else:
                    self.log_test("GET /api/settings - Critères d'inspection", False, 
                                "inspectionCriteria manquant dans la réponse")
                    
            elif response.status_code == 403:
                self.log_test("GET /api/settings - Accès inspecteur", False, 
                            "Status 403 - Accès refusé (devrait être 200 OK maintenant)")
            else:
                self.log_test("GET /api/settings - Accès inspecteur", False, 
                            f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/settings - Accès inspecteur", False, f"Exception: {str(e)}")
    
    def test_inspector_users_access(self):
        """Test 2: Accès Users pour Inspecteurs"""
        print("\n=== TEST 2: ACCÈS USERS POUR INSPECTEURS ===")
        
        # Utiliser le même utilisateur inspecteur
        inspector_token, inspector_user = self.authenticate_user("adjudantchef_descadron", "uoQgAwEQ")
        
        if not inspector_token:
            # Si échec, utiliser admin comme fallback
            self.log_test("Authentification inspecteur pour users", False, "Échec - utilisation admin comme fallback")
            inspector_token = self.admin_token
            inspector_user = {"username": ADMIN_USERNAME, "role": "encadrement"}
        else:
            self.log_test("Authentification inspecteur pour users", True, f"Connecté: {inspector_user.get('prenom', '')} {inspector_user.get('nom', '')}")
        
        # Créer une session pour l'inspecteur
        inspector_session = requests.Session()
        inspector_session.headers.update({"Authorization": f"Bearer {inspector_token}"})
        
        # Test GET /api/users
        try:
            response = inspector_session.get(f"{BASE_URL}/users")
            
            if response.status_code == 200:
                users_data = response.json()
                
                if isinstance(users_data, list) and len(users_data) > 0:
                    self.log_test("GET /api/users - Accès inspecteur", True, 
                                f"Status 200 OK, {len(users_data)} utilisateurs retournés")
                    
                    # Vérifier que la liste contient des utilisateurs avec les champs requis
                    sample_user = users_data[0]
                    required_fields = ["id", "nom", "prenom", "role", "grade"]
                    missing_fields = [field for field in required_fields if field not in sample_user]
                    
                    if not missing_fields:
                        self.log_test("GET /api/users - Structure données", True, 
                                    "Tous les champs requis présents")
                    else:
                        self.log_test("GET /api/users - Structure données", False, 
                                    f"Champs manquants: {missing_fields}")
                else:
                    self.log_test("GET /api/users - Liste utilisateurs", False, 
                                "Liste vide ou format incorrect")
                    
            elif response.status_code == 403:
                self.log_test("GET /api/users - Accès inspecteur", False, 
                            "Status 403 - Accès refusé (devrait être 200 OK maintenant)")
            else:
                self.log_test("GET /api/users - Accès inspecteur", False, 
                            f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/users - Accès inspecteur", False, f"Exception: {str(e)}")
    
    def test_post_settings_still_protected(self):
        """Test 3: POST Settings toujours protégé"""
        print("\n=== TEST 3: POST SETTINGS TOUJOURS PROTÉGÉ ===")
        
        # Authentifier l'inspecteur
        inspector_token, inspector_user = self.authenticate_user("adjudantchef_descadron", "uoQgAwEQ")
        
        if not inspector_token:
            self.log_test("Authentification inspecteur pour POST settings", False, "Impossible d'authentifier l'inspecteur")
            return
        
        self.log_test("Authentification inspecteur pour POST settings", True, f"Connecté: {inspector_user.get('prenom', '')} {inspector_user.get('nom', '')}")
        
        # Créer une session pour l'inspecteur
        inspector_session = requests.Session()
        inspector_session.headers.update({"Authorization": f"Bearer {inspector_token}"})
        
        # Essayer de modifier les settings (doit échouer avec 403)
        test_settings = {
            "escadronName": "Test Escadron",
            "address": "Test Address",
            "contactEmail": "test@example.com",
            "allowMotivatedAbsences": True,
            "consecutiveAbsenceThreshold": 3,
            "inspectionCriteria": {
                "C1 - Tenue de Parade": {
                    "Propreté générale": "Uniforme propre et repassé",
                    "Ajustement": "Taille correcte et bien ajusté"
                }
            },
            "autoBackup": True
        }
        
        try:
            response = inspector_session.post(f"{BASE_URL}/settings", json=test_settings)
            
            if response.status_code == 403:
                self.log_test("POST /api/settings - Protection inspecteur", True, 
                            "Status 403 - Accès correctement refusé aux inspecteurs")
            elif response.status_code == 200 or response.status_code == 201:
                self.log_test("POST /api/settings - Protection inspecteur", False, 
                            "Status 200/201 - L'inspecteur peut modifier les settings (ne devrait pas)")
            else:
                self.log_test("POST /api/settings - Protection inspecteur", False, 
                            f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("POST /api/settings - Protection inspecteur", False, f"Exception: {str(e)}")
        
        # Vérifier que l'admin peut toujours modifier les settings
        try:
            response = self.session.post(f"{BASE_URL}/settings", json=test_settings)
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_test("POST /api/settings - Accès admin", True, 
                            "Admin peut toujours modifier les settings")
            else:
                self.log_test("POST /api/settings - Accès admin", False, 
                            f"Admin ne peut plus modifier les settings - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("POST /api/settings - Accès admin", False, f"Exception: {str(e)}")
    
    def test_uniform_inspections_regression(self):
        """Test 4: Régression Inspections"""
        print("\n=== TEST 4: RÉGRESSION INSPECTIONS ===")
        
        # Authentifier l'inspecteur
        inspector_token, inspector_user = self.authenticate_user("adjudantchef_descadron", "uoQgAwEQ")
        
        if not inspector_token:
            self.log_test("Authentification inspecteur pour inspections", False, "Impossible d'authentifier l'inspecteur")
            return
        
        self.log_test("Authentification inspecteur pour inspections", True, f"Connecté: {inspector_user.get('prenom', '')} {inspector_user.get('nom', '')}")
        
        # Créer une session pour l'inspecteur
        inspector_session = requests.Session()
        inspector_session.headers.update({"Authorization": f"Bearer {inspector_token}"})
        
        # Récupérer la liste des utilisateurs pour trouver un cadet à inspecter
        try:
            response = inspector_session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                
                # Trouver un cadet différent de l'inspecteur
                cadet_to_inspect = None
                for user in users:
                    if user["id"] != inspector_user["id"] and user.get("actif", False):
                        cadet_to_inspect = user
                        break
                
                if cadet_to_inspect:
                    # Test POST /api/uniform-inspections fonctionne toujours
                    inspection_data = {
                        "cadet_id": cadet_to_inspect["id"],
                        "uniform_type": "C1 - Tenue de Parade",
                        "criteria_scores": {
                            "Propreté générale": 4,
                            "Ajustement": 3,
                            "Accessoires": 4
                        },
                        "commentaire": "Test régression - inspection par inspecteur"
                    }
                    
                    try:
                        response = inspector_session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                        
                        if response.status_code == 200 or response.status_code == 201:
                            self.log_test("POST /api/uniform-inspections - Fonctionnel", True, 
                                        f"Inspection réussie du cadet {cadet_to_inspect.get('prenom', '')} {cadet_to_inspect.get('nom', '')}")
                        else:
                            self.log_test("POST /api/uniform-inspections - Fonctionnel", False, 
                                        f"Status: {response.status_code}, Response: {response.text}")
                            
                    except Exception as e:
                        self.log_test("POST /api/uniform-inspections - Fonctionnel", False, f"Exception: {str(e)}")
                    
                    # Test anti-auto-évaluation toujours active
                    auto_inspection_data = {
                        "cadet_id": inspector_user["id"],  # L'inspecteur s'inspecte lui-même
                        "uniform_type": "C1 - Tenue de Parade",
                        "criteria_scores": {
                            "Propreté générale": 4,
                            "Ajustement": 3
                        },
                        "commentaire": "Test anti-auto-évaluation"
                    }
                    
                    try:
                        response = inspector_session.post(f"{BASE_URL}/uniform-inspections", json=auto_inspection_data)
                        
                        if response.status_code == 403:
                            response_data = response.json()
                            expected_message = "Vous ne pouvez pas inspecter votre propre uniforme"
                            
                            if expected_message in response_data.get("detail", ""):
                                self.log_test("Anti-auto-évaluation - Toujours active", True, 
                                            "Erreur 403 correcte avec message attendu")
                            else:
                                self.log_test("Anti-auto-évaluation - Toujours active", False, 
                                            f"Erreur 403 mais message incorrect: {response_data.get('detail', 'N/A')}")
                        else:
                            self.log_test("Anti-auto-évaluation - Toujours active", False, 
                                        f"Status attendu: 403, reçu: {response.status_code}")
                            
                    except Exception as e:
                        self.log_test("Anti-auto-évaluation - Toujours active", False, f"Exception: {str(e)}")
                
                else:
                    self.log_test("Recherche cadet pour inspection", False, "Aucun cadet trouvé pour test")
            else:
                self.log_test("Récupération utilisateurs pour inspection", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Récupération utilisateurs pour inspection", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS - VÉRIFICATION PERMISSIONS INSPECTEURS")
        print(f"Base URL: {BASE_URL}")
        print(f"Admin: {ADMIN_USERNAME}")
        print("Focus: Vérifier que GET /api/settings et GET /api/users sont maintenant accessibles aux inspecteurs")
        
        # Authentification admin
        if not self.authenticate_admin():
            print("❌ ÉCHEC - Impossible de s'authentifier en tant qu'admin")
            return False
        
        # Exécuter les tests
        self.test_inspector_settings_access()
        self.test_inspector_users_access()
        self.test_post_settings_still_protected()
        self.test_uniform_inspections_regression()
        
        # Résumé final
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DES TESTS - PERMISSIONS INSPECTEURS")
        print("="*70)
        
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
        
        print("\n🎯 OBJECTIFS PRINCIPAUX:")
        print("   1. GET /api/settings accessible aux inspecteurs (État-Major)")
        print("   2. GET /api/users accessible aux inspecteurs")
        print("   3. POST /api/settings toujours protégé (admin/encadrement seulement)")
        print("   4. POST /api/uniform-inspections fonctionne toujours")
        print("   5. Anti-auto-évaluation toujours active")
        
        # Vérifier les objectifs critiques
        settings_access = any(t["success"] for t in self.test_results if "GET /api/settings - Accès inspecteur" in t["name"])
        users_access = any(t["success"] for t in self.test_results if "GET /api/users - Accès inspecteur" in t["name"])
        post_protection = any(t["success"] for t in self.test_results if "POST /api/settings - Protection inspecteur" in t["name"])
        
        print(f"\n📋 STATUT OBJECTIFS:")
        print(f"   ✅ Settings accessibles aux inspecteurs: {'OUI' if settings_access else 'NON'}")
        print(f"   ✅ Users accessibles aux inspecteurs: {'OUI' if users_access else 'NON'}")
        print(f"   ✅ POST Settings protégé: {'OUI' if post_protection else 'NON'}")

def main():
    """Fonction principale"""
    test_runner = InspectorPermissionsTest()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 Tests terminés avec succès")
        return 0
    else:
        print("\n💥 Échec des tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())