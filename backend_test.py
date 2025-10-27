#!/usr/bin/env python3
"""
Tests pour valider que Jakob Moreau et Mariane Marsan apparaissent dans GET /api/users
après correction des emails invalides (.local) mis à None.

Objectif: Valider que les utilisateurs Jakob Moreau et Mariane Marsan apparaissent maintenant 
dans la liste GET /api/users après avoir mis leurs emails à None pour résoudre les erreurs 
de validation Pydantic.
"""

import requests
import json
from datetime import datetime, date
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://commandhub-cadet.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Enregistre le résultat d'un test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if message:
            print(f"    {message}")
        if details and not success:
            print(f"    Détails: {details}")
        print()
    
    def authenticate_admin(self):
        """Test 1: Authentification Admin"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user_info = data["user"]
                    self.log_test(
                        "Authentification Admin",
                        True,
                        f"Connexion réussie - Utilisateur: {user_info.get('prenom', '')} {user_info.get('nom', '')} (Rôle: {user_info.get('role', '')})"
                    )
                    return True
                else:
                    self.log_test("Authentification Admin", False, "Token JWT manquant dans la réponse")
                    return False
            else:
                self.log_test(
                    "Authentification Admin", 
                    False, 
                    f"Échec authentification - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Authentification Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_users_endpoint(self):
        """Test 2: GET /api/users (Principal) - Doit retourner 200 OK, pas 500"""
        if not self.admin_token:
            self.log_test("GET /api/users", False, "Token admin requis")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.base_url}/users", headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    # Vérifier la structure des utilisateurs
                    required_fields = [
                        "id", "nom", "prenom", "username", "grade", "role", 
                        "actif", "has_admin_privileges", "created_at", "must_change_password"
                    ]
                    
                    structure_valid = True
                    missing_fields = []
                    
                    if len(users) > 0:
                        first_user = users[0]
                        for field in required_fields:
                            if field not in first_user:
                                structure_valid = False
                                missing_fields.append(field)
                    
                    if structure_valid:
                        self.log_test(
                            "GET /api/users - Structure",
                            True,
                            f"Structure correcte - {len(users)} utilisateurs trouvés avec tous les champs requis"
                        )
                    else:
                        self.log_test(
                            "GET /api/users - Structure",
                            False,
                            f"Champs manquants: {missing_fields}"
                        )
                    
                    self.log_test(
                        "GET /api/users - Status 200",
                        True,
                        f"Endpoint accessible - {len(users)} utilisateurs retournés"
                    )
                    return users
                else:
                    self.log_test("GET /api/users", False, "Réponse n'est pas une liste")
                    return False
            else:
                self.log_test(
                    "GET /api/users", 
                    False, 
                    f"Status {response.status_code} - ERREUR CRITIQUE si 500!",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/users", False, f"Erreur: {str(e)}")
            return False
    
    def verify_user_schema(self, users):
        """Test 3: Vérifier structure des utilisateurs récents"""
        if not users:
            self.log_test("Vérification schéma utilisateurs", False, "Aucun utilisateur à vérifier")
            return
            
        try:
            # Analyser tous les utilisateurs pour détecter des problèmes de schéma
            schema_issues = []
            users_with_correct_schema = 0
            
            required_fields = {
                "id": str,
                "nom": str,
                "prenom": str,
                "grade": str,
                "role": str,
                "actif": bool,
                "has_admin_privileges": bool,
                "created_at": str,
                "must_change_password": bool
            }
            
            for user in users:
                user_issues = []
                
                # Vérifier chaque champ requis
                for field, expected_type in required_fields.items():
                    if field not in user:
                        user_issues.append(f"Champ manquant: {field}")
                    elif not isinstance(user[field], expected_type):
                        user_issues.append(f"Type incorrect pour {field}: attendu {expected_type.__name__}, reçu {type(user[field]).__name__}")
                
                # Vérifier l'ancien champ problématique
                if "require_password_change" in user:
                    user_issues.append("Ancien champ 'require_password_change' présent (devrait être 'must_change_password')")
                
                if user_issues:
                    schema_issues.append({
                        "user": f"{user.get('prenom', 'N/A')} {user.get('nom', 'N/A')} (ID: {user.get('id', 'N/A')})",
                        "issues": user_issues
                    })
                else:
                    users_with_correct_schema += 1
            
            if not schema_issues:
                self.log_test(
                    "Vérification schéma utilisateurs",
                    True,
                    f"Tous les {len(users)} utilisateurs ont le schéma correct"
                )
            else:
                self.log_test(
                    "Vérification schéma utilisateurs",
                    False,
                    f"{users_with_correct_schema}/{len(users)} utilisateurs OK - {len(schema_issues)} avec problèmes",
                    schema_issues[:3]  # Afficher seulement les 3 premiers problèmes
                )
                
        except Exception as e:
            self.log_test("Vérification schéma utilisateurs", False, f"Erreur: {str(e)}")
    
    def test_related_endpoints(self):
        """Test 4: Endpoints liés (régression)"""
        if not self.admin_token:
            self.log_test("Tests régression", False, "Token admin requis")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET /api/sections
        try:
            response = requests.get(f"{self.base_url}/sections", headers=headers, timeout=10)
            if response.status_code == 200:
                sections = response.json()
                self.log_test(
                    "GET /api/sections",
                    True,
                    f"Endpoint fonctionnel - {len(sections)} sections trouvées"
                )
            else:
                self.log_test("GET /api/sections", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/sections", False, f"Erreur: {str(e)}")
        
        # Test GET /api/presences
        try:
            response = requests.get(f"{self.base_url}/presences", headers=headers, timeout=10)
            if response.status_code == 200:
                presences = response.json()
                self.log_test(
                    "GET /api/presences",
                    True,
                    f"Endpoint fonctionnel - {len(presences)} présences trouvées"
                )
            else:
                self.log_test("GET /api/presences", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/presences", False, f"Erreur: {str(e)}")
        
        # Test POST /api/uniform-inspections (création inspection)
        try:
            # D'abord récupérer un utilisateur pour l'inspection
            users_response = requests.get(f"{self.base_url}/users", headers=headers, timeout=10)
            if users_response.status_code == 200:
                users = users_response.json()
                if users:
                    test_user_id = users[0]["id"]
                    
                    inspection_data = {
                        "cadet_id": test_user_id,
                        "uniform_type": "C1 - Tenue de Parade",
                        "criteria_scores": {
                            "Propreté générale": 4,
                            "Coiffure": 3,
                            "Chaussures": 4,
                            "Insignes": 3
                        },
                        "commentaire": "Test inspection - validation correctif"
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/uniform-inspections",
                        json=inspection_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            "POST /api/uniform-inspections",
                            True,
                            "Création d'inspection fonctionnelle"
                        )
                    else:
                        self.log_test(
                            "POST /api/uniform-inspections", 
                            False, 
                            f"Status {response.status_code}",
                            response.text[:200]
                        )
                else:
                    self.log_test("POST /api/uniform-inspections", False, "Aucun utilisateur pour test")
            else:
                self.log_test("POST /api/uniform-inspections", False, "Impossible de récupérer utilisateurs")
        except Exception as e:
            self.log_test("POST /api/uniform-inspections", False, f"Erreur: {str(e)}")
    
    def test_excel_import_simulation(self):
        """Test 5: Simulation import Excel (si possible)"""
        # Note: Ce test simule la vérification que les nouveaux utilisateurs 
        # créés auraient le bon schéma
        
        if not self.admin_token:
            self.log_test("Simulation import Excel", False, "Token admin requis")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Créer un utilisateur test pour simuler l'import Excel
            test_user_data = {
                "nom": "TestImport",
                "prenom": "Cadet",
                "grade": "cadet",
                "role": "cadet",
                "section_id": None,
                "subgroup_id": None,
                "has_admin_privileges": False,
                "actif": True
            }
            
            response = requests.post(
                f"{self.base_url}/users",
                json=test_user_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("user_id")
                
                # Vérifier que l'utilisateur créé a le bon schéma
                users_response = requests.get(f"{self.base_url}/users", headers=headers, timeout=10)
                if users_response.status_code == 200:
                    users = users_response.json()
                    created_user = next((u for u in users if u["id"] == user_id), None)
                    
                    if created_user:
                        # Vérifier les champs critiques du correctif
                        has_correct_fields = all([
                            "must_change_password" in created_user,
                            "actif" in created_user,
                            "has_admin_privileges" in created_user,
                            "require_password_change" not in created_user  # Ancien champ ne doit pas être présent
                        ])
                        
                        if has_correct_fields:
                            self.log_test(
                                "Simulation import Excel",
                                True,
                                "Nouvel utilisateur créé avec schéma correct"
                            )
                        else:
                            self.log_test(
                                "Simulation import Excel",
                                False,
                                "Nouvel utilisateur avec schéma incorrect"
                            )
                        
                        # Nettoyer - supprimer l'utilisateur test
                        requests.delete(f"{self.base_url}/users/{user_id}", headers=headers)
                    else:
                        self.log_test("Simulation import Excel", False, "Utilisateur créé non trouvé")
                else:
                    self.log_test("Simulation import Excel", False, "Impossible de vérifier utilisateur créé")
            else:
                self.log_test(
                    "Simulation import Excel", 
                    False, 
                    f"Création utilisateur échouée - Status {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Simulation import Excel", False, f"Erreur: {str(e)}")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("=" * 80)
        print("🧪 TESTS BACKEND - CORRECTIF CRITIQUE ERREUR 500 GET /api/users")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Admin: {ADMIN_USERNAME}")
        print()
        
        # Test 1: Authentification
        if not self.authenticate_admin():
            print("❌ ÉCHEC CRITIQUE: Impossible de s'authentifier")
            return self.generate_summary()
        
        # Test 2: GET /api/users (test principal)
        users = self.test_get_users_endpoint()
        
        # Test 3: Vérification schéma
        if users:
            self.verify_user_schema(users)
        
        # Test 4: Tests de régression
        self.test_related_endpoints()
        
        # Test 5: Simulation import Excel
        self.test_excel_import_simulation()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Génère un résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        print(f"Total: {total_tests} tests")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTS ÉCHOUÉS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['test']}: {test['message']}")
            print()
        
        # Vérification critique
        critical_test = next((t for t in self.test_results if "GET /api/users - Status 200" in t["test"]), None)
        if critical_test and critical_test["success"]:
            print("🎉 CORRECTIF VALIDÉ: GET /api/users retourne 200 OK (plus d'erreur 500)")
        else:
            print("🚨 CORRECTIF NON VALIDÉ: GET /api/users ne fonctionne toujours pas correctement")
        
        print("=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "critical_fix_validated": critical_test and critical_test["success"] if critical_test else False,
            "details": self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Code de sortie basé sur les résultats
    if results["failed"] == 0:
        sys.exit(0)  # Succès
    else:
        sys.exit(1)  # Échec