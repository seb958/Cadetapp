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

class TestResults:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        
    def add_success(self, test_name: str):
        self.tests_passed += 1
        print(f"✅ {test_name}")
        
    def add_failure(self, test_name: str, error: str):
        self.tests_failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        
    def print_summary(self):
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        print(f"\n{'='*60}")
        print(f"RÉSUMÉ DES TESTS: {self.tests_passed}/{total} réussis ({success_rate:.1f}%)")
        print(f"{'='*60}")
        
        if self.errors:
            print("\nERREURS DÉTECTÉES:")
            for error in self.errors:
                print(f"  - {error}")

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
    
    def authenticate_admin(self, results: TestResults) -> str:
        """Test 1: Authentification Admin"""
        try:
            # Try both endpoints - the review mentions POST /api/login but backend has /auth/login
            endpoints_to_try = [
                f"{self.base_url}/login",  # As mentioned in review request
                f"{self.base_url}/auth/login"  # As seen in backend code
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = requests.post(
                        endpoint,
                        json={
                            "username": ADMIN_USERNAME,
                            "password": ADMIN_PASSWORD
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "access_token" in data:
                            self.admin_token = data["access_token"]
                            results.add_success(f"Test 1: Authentification admin réussie via {endpoint}")
                            return self.admin_token
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        results.add_failure("Test 1: Authentification admin", 
                                          f"Status {response.status_code} sur {endpoint}")
                        return None
                        
                except Exception as e:
                    continue  # Try next endpoint
            
            results.add_failure("Test 1: Authentification admin", "Aucun endpoint d'authentification fonctionnel")
            return None
            
        except Exception as e:
            results.add_failure("Test 1: Authentification admin", str(e))
            return None
    
    def get_users(self, results: TestResults) -> List[Dict[str, Any]]:
        """Test 2: GET /api/users - Vérifier Jakob et Mariane"""
        if not self.admin_token:
            results.add_failure("Test 2: GET /api/users", "Token admin requis")
            return []
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.base_url}/users", headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    results.add_success(f"Test 2: GET /api/users accessible - Status 200 OK")
                    results.add_success(f"Test 2a: {len(users)} utilisateurs récupérés")
                    return users
                else:
                    results.add_failure("Test 2: GET /api/users", "Réponse n'est pas une liste")
                    return []
            else:
                results.add_failure("Test 2: GET /api/users", 
                                  f"Status {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            results.add_failure("Test 2: GET /api/users", str(e))
            return []
    
    def test_jakob_moreau_presence(self, results: TestResults, users: List[Dict[str, Any]]):
        """Test 3: Vérifier présence de Jakob Moreau"""
        jakob = None
        for user in users:
            if user.get("username") == "jakob.moreau":
                jakob = user
                break
        
        if jakob:
            results.add_success("Test 3: Jakob Moreau trouvé dans la liste")
            
            # Vérifier les détails
            if jakob.get("nom") == "Moreau" and jakob.get("prenom") == "Jakob":
                results.add_success("Test 3a: Jakob Moreau - nom et prénom corrects")
            else:
                results.add_failure("Test 3a: Jakob Moreau - nom/prénom", 
                                  f"Attendu: Jakob Moreau, Trouvé: {jakob.get('prenom')} {jakob.get('nom')}")
            
            # Vérifier email à None
            if jakob.get("email") is None:
                results.add_success("Test 3b: Jakob Moreau - email à None")
            else:
                results.add_failure("Test 3b: Jakob Moreau - email", 
                                  f"Attendu: None, Trouvé: {jakob.get('email')}")
        else:
            results.add_failure("Test 3: Jakob Moreau", "Utilisateur jakob.moreau non trouvé dans la liste")

    def test_mariane_marsan_presence(self, results: TestResults, users: List[Dict[str, Any]]):
        """Test 4: Vérifier présence de Mariane Marsan"""
        mariane = None
        for user in users:
            if user.get("username") == "mariane.marsan":
                mariane = user
                break
        
        if mariane:
            results.add_success("Test 4: Mariane Marsan trouvée dans la liste")
            
            # Vérifier les détails
            if mariane.get("nom") == "Marsan" and mariane.get("prenom") == "Mariane":
                results.add_success("Test 4a: Mariane Marsan - nom et prénom corrects")
            else:
                results.add_failure("Test 4a: Mariane Marsan - nom/prénom", 
                                  f"Attendu: Mariane Marsan, Trouvé: {mariane.get('prenom')} {mariane.get('nom')}")
            
            # Vérifier email à None
            if mariane.get("email") is None:
                results.add_success("Test 4b: Mariane Marsan - email à None")
            else:
                results.add_failure("Test 4b: Mariane Marsan - email", 
                                  f"Attendu: None, Trouvé: {mariane.get('email')}")
        else:
            results.add_failure("Test 4: Mariane Marsan", "Utilisateur mariane.marsan non trouvé dans la liste")

    def test_total_users_count(self, results: TestResults, users: List[Dict[str, Any]]):
        """Test 5: Vérifier le nombre total d'utilisateurs"""
        total_users = len(users)
        if total_users == 22:
            results.add_success(f"Test 5: Nombre total d'utilisateurs correct (22)")
        else:
            results.add_failure("Test 5: Nombre total d'utilisateurs", 
                              f"Attendu: 22, Trouvé: {total_users}")

    def test_no_pydantic_errors(self, results: TestResults, users: List[Dict[str, Any]]):
        """Test 6: Vérifier qu'il n'y a pas d'erreurs de validation Pydantic"""
        # Si on arrive ici et qu'on a récupéré tous les utilisateurs sans erreur 500,
        # cela signifie que les erreurs Pydantic sont résolues
        if users:
            results.add_success("Test 6: Pas d'erreurs de validation Pydantic détectées")
            
            # Vérifier que tous les utilisateurs ont une structure valide
            valid_users = 0
            for user in users:
                if all(key in user for key in ["id", "nom", "prenom", "role", "grade"]):
                    valid_users += 1
            
            if valid_users == len(users):
                results.add_success(f"Test 6a: Tous les {len(users)} utilisateurs ont une structure valide")
            else:
                results.add_failure("Test 6a: Structure utilisateurs", 
                                  f"{valid_users}/{len(users)} utilisateurs ont une structure valide")
        else:
            results.add_failure("Test 6: Validation Pydantic", "Aucun utilisateur récupéré")
    
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