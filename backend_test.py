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
BASE_URL = "https://squadron-app-1.preview.emergentagent.com/api"
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
    
    def print_user_details(self, users: List[Dict[str, Any]]):
        """Affiche les détails des utilisateurs Jakob et Mariane pour debug"""
        print(f"\n{'='*60}")
        print("DÉTAILS DES UTILISATEURS RECHERCHÉS:")
        print(f"{'='*60}")
        
        jakob = next((u for u in users if u.get("username") == "jakob.moreau"), None)
        mariane = next((u for u in users if u.get("username") == "mariane.marsan"), None)
        
        if jakob:
            print(f"Jakob Moreau trouvé:")
            print(f"  - ID: {jakob.get('id')}")
            print(f"  - Username: {jakob.get('username')}")
            print(f"  - Nom: {jakob.get('nom')}")
            print(f"  - Prénom: {jakob.get('prenom')}")
            print(f"  - Email: {jakob.get('email')}")
            print(f"  - Rôle: {jakob.get('role')}")
            print(f"  - Grade: {jakob.get('grade')}")
            print(f"  - Actif: {jakob.get('actif')}")
        else:
            print("Jakob Moreau: NON TROUVÉ")
        
        print()
        
        if mariane:
            print(f"Mariane Marsan trouvée:")
            print(f"  - ID: {mariane.get('id')}")
            print(f"  - Username: {mariane.get('username')}")
            print(f"  - Nom: {mariane.get('nom')}")
            print(f"  - Prénom: {mariane.get('prenom')}")
            print(f"  - Email: {mariane.get('email')}")
            print(f"  - Rôle: {mariane.get('role')}")
            print(f"  - Grade: {mariane.get('grade')}")
            print(f"  - Actif: {mariane.get('actif')}")
        else:
            print("Mariane Marsan: NON TROUVÉE")

    def run_all_tests(self):
        """Fonction principale des tests"""
        print("🧪 TESTS DE VALIDATION - Jakob Moreau et Mariane Marsan")
        print(f"Base URL: {self.base_url}")
        print(f"Authentification: {ADMIN_USERNAME}")
        print("="*60)
        
        results = TestResults()
        
        # Test 1: Authentification
        token = self.authenticate_admin(results)
        if not token:
            print("\n❌ ARRÊT DES TESTS - Authentification échouée")
            results.print_summary()
            return results
        
        # Test 2: Récupération des utilisateurs
        users = self.get_users(results)
        if not users:
            print("\n❌ ARRÊT DES TESTS - Impossible de récupérer les utilisateurs")
            results.print_summary()
            return results
        
        # Tests 3-6: Validation des exigences
        self.test_jakob_moreau_presence(results, users)
        self.test_mariane_marsan_presence(results, users)
        self.test_total_users_count(results, users)
        self.test_no_pydantic_errors(results, users)
        
        # Affichage des détails pour debug
        self.print_user_details(users)
        
        # Résumé final
        results.print_summary()
        
        # Critères de réussite
        print(f"\n{'='*60}")
        print("CRITÈRES DE RÉUSSITE:")
        print(f"{'='*60}")
        success_criteria = [
            ("✅ GET /api/users retourne 200 avec 22 utilisateurs", len(users) == 22),
            ("✅ Jakob Moreau visible dans la liste", any(u.get("username") == "jakob.moreau" for u in users)),
            ("✅ Mariane Marsan visible dans la liste", any(u.get("username") == "mariane.marsan" for u in users)),
            ("✅ Pas d'erreurs de validation Pydantic", results.tests_failed == 0)
        ]
        
        all_success = True
        for criterion, met in success_criteria:
            status = "✅" if met else "❌"
            print(f"{status} {criterion[2:]}")
            if not met:
                all_success = False
        
        if all_success:
            print(f"\n🎉 TOUS LES CRITÈRES DE RÉUSSITE SONT REMPLIS!")
        else:
            print(f"\n⚠️  CERTAINS CRITÈRES NE SONT PAS REMPLIS")
        
        return results

def main():
    """Fonction principale"""
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Code de sortie basé sur les résultats
    if results.tests_failed == 0:
        sys.exit(0)  # Succès
    else:
        sys.exit(1)  # Échec

if __name__ == "__main__":
    main()