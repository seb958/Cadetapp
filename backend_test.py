#!/usr/bin/env python3
"""
Tests complets pour le système de gestion des présences - Escadron de Cadets
Teste les APIs de présences, permissions, et statistiques
"""

import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import sys

# Configuration
BASE_URL = "https://cadetron.preview.emergentagent.com/api"

# Comptes de test fournis
TEST_ACCOUNTS = {
    "admin": {"email": "admin@escadron.fr", "password": "admin123"},
    "cadet_admin": {"email": "emma.leroy@escadron.fr", "password": "admin123"},
    "cadet_responsable": {"email": "jean.moreau@escadron.fr", "password": "resp123"},
    "cadet1": {"email": "pierre.martin@escadron.fr", "password": "cadet123"},
    "cadet2": {"email": "marie.dubois@escadron.fr", "password": "cadet123"}
}

class PresenceTestSuite:
    def __init__(self):
        self.tokens = {}
        self.users = {}
        self.test_results = []
        self.failed_tests = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Enregistre le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        
        self.test_results.append(result)
        if not success:
            self.failed_tests.append(f"{test_name}: {message}")
        print(result)
        
    def authenticate_users(self) -> bool:
        """Authentifie tous les utilisateurs de test"""
        print("\n=== AUTHENTIFICATION DES UTILISATEURS ===")
        
        for role, credentials in TEST_ACCOUNTS.items():
            try:
                response = requests.post(
                    f"{BASE_URL}/auth/login",
                    json=credentials,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.users[role] = data["user"]
                    self.log_result(f"Auth {role}", True, f"Token obtenu pour {credentials['email']}")
                else:
                    self.log_result(f"Auth {role}", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
            except Exception as e:
                self.log_result(f"Auth {role}", False, f"Erreur: {str(e)}")
                return False
                
        return True
    
    def get_headers(self, role: str) -> Dict[str, str]:
        """Retourne les headers avec token d'authentification"""
        return {
            "Authorization": f"Bearer {self.tokens[role]}",
            "Content-Type": "application/json"
        }
    
    def test_create_individual_presence(self) -> bool:
        """Test création de présence individuelle"""
        print("\n=== TEST CRÉATION PRÉSENCE INDIVIDUELLE ===")
        
        # Test avec cadet_admin (doit réussir) - utiliser une date future unique
        cadet_id = self.users["cadet1"]["id"]
        future_date = date(2025, 12, 15)  # Date fixe dans le futur
        presence_data = {
            "cadet_id": cadet_id,
            "presence_date": future_date.isoformat(),
            "status": "present",
            "commentaire": "Test présence individuelle",
            "activite": "Test automatisé"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/presences",
                json=presence_data,
                headers=self.get_headers("cadet_admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Création présence individuelle", True, f"Présence créée ID: {data['id']}")
                return True
            else:
                self.log_result("Création présence individuelle", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Création présence individuelle", False, f"Erreur: {str(e)}")
            return False
    
    def test_create_bulk_presences(self) -> bool:
        """Test création de présences en bulk"""
        print("\n=== TEST CRÉATION PRÉSENCES EN BULK ===")
        
        today = date.today()
        bulk_data = {
            "date": today.isoformat(),
            "activite": "Formation test automatisé",
            "presences": [
                {
                    "cadet_id": self.users["cadet1"]["id"],
                    "status": "present",
                    "commentaire": "Présent formation"
                },
                {
                    "cadet_id": self.users["cadet2"]["id"],
                    "status": "absent_excuse",
                    "commentaire": "Absent excusé - maladie"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/presences/bulk",
                json=bulk_data,
                headers=self.get_headers("cadet_admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Création bulk présences", True, f"Créées: {data['created_count']}, Erreurs: {len(data['errors'])}")
                return True
            else:
                self.log_result("Création bulk présences", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Création bulk présences", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_presences_with_filters(self) -> bool:
        """Test récupération des présences avec filtres"""
        print("\n=== TEST RÉCUPÉRATION PRÉSENCES AVEC FILTRES ===")
        
        success_count = 0
        
        # Test 1: Récupération toutes présences (admin)
        try:
            response = requests.get(
                f"{BASE_URL}/presences",
                headers=self.get_headers("admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get présences (admin)", True, f"{len(data)} présences trouvées")
                success_count += 1
            else:
                self.log_result("Get présences (admin)", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Get présences (admin)", False, f"Erreur: {str(e)}")
        
        # Test 2: Récupération avec filtre date
        today = date.today()
        try:
            response = requests.get(
                f"{BASE_URL}/presences?date={today.isoformat()}",
                headers=self.get_headers("cadet_admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get présences avec filtre date", True, f"{len(data)} présences pour {today}")
                success_count += 1
            else:
                self.log_result("Get présences avec filtre date", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Get présences avec filtre date", False, f"Erreur: {str(e)}")
        
        # Test 3: Récupération par cadet_id (admin seulement)
        try:
            cadet_id = self.users["cadet1"]["id"]
            response = requests.get(
                f"{BASE_URL}/presences?cadet_id={cadet_id}",
                headers=self.get_headers("admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get présences par cadet_id", True, f"{len(data)} présences pour cadet")
                success_count += 1
            else:
                self.log_result("Get présences par cadet_id", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Get présences par cadet_id", False, f"Erreur: {str(e)}")
        
        return success_count >= 2
    
    def test_permissions_system(self) -> bool:
        """Test système de permissions"""
        print("\n=== TEST SYSTÈME DE PERMISSIONS ===")
        
        success_count = 0
        
        # Test 1: Cadet ne peut voir que ses propres présences
        try:
            response = requests.get(
                f"{BASE_URL}/presences",
                headers=self.get_headers("cadet1")
            )
            
            if response.status_code == 200:
                data = response.json()
                # Vérifier que toutes les présences appartiennent au cadet
                cadet_id = self.users["cadet1"]["id"]
                all_own_presences = all(p["cadet_id"] == cadet_id for p in data)
                
                if all_own_presences:
                    self.log_result("Permission cadet - propres présences", True, f"{len(data)} présences personnelles")
                    success_count += 1
                else:
                    self.log_result("Permission cadet - propres présences", False, "Accès à présences d'autres cadets")
            else:
                self.log_result("Permission cadet - propres présences", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Permission cadet - propres présences", False, f"Erreur: {str(e)}")
        
        # Test 2: Cadet ne peut pas créer de présences
        try:
            future_date = date.today() + timedelta(days=5)
            presence_data = {
                "cadet_id": self.users["cadet1"]["id"],
                "presence_date": future_date.isoformat(),
                "status": "present",
                "commentaire": "Test permission refusée"
            }
            
            response = requests.post(
                f"{BASE_URL}/presences",
                json=presence_data,
                headers=self.get_headers("cadet1")
            )
            
            if response.status_code == 403:
                self.log_result("Permission cadet - création refusée", True, "403 Forbidden comme attendu")
                success_count += 1
            else:
                self.log_result("Permission cadet - création refusée", False, f"Status {response.status_code} (attendu 403)")
                
        except Exception as e:
            self.log_result("Permission cadet - création refusée", False, f"Erreur: {str(e)}")
        
        # Test 3: Admin peut tout voir
        try:
            response = requests.get(
                f"{BASE_URL}/presences",
                headers=self.get_headers("admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Permission admin - accès global", True, f"{len(data)} présences visibles")
                success_count += 1
            else:
                self.log_result("Permission admin - accès global", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Permission admin - accès global", False, f"Erreur: {str(e)}")
        
        # Test 4: Cadet admin peut créer des présences
        try:
            future_date = date.today() + timedelta(days=15)
            presence_data = {
                "cadet_id": self.users["cadet2"]["id"],
                "presence_date": future_date.isoformat(),
                "status": "retard",
                "commentaire": "Test permission cadet admin",
                "activite": "Test automatisé"
            }
            
            response = requests.post(
                f"{BASE_URL}/presences",
                json=presence_data,
                headers=self.get_headers("cadet_admin")
            )
            
            if response.status_code == 200:
                self.log_result("Permission cadet admin - création", True, "Création autorisée")
                success_count += 1
            else:
                self.log_result("Permission cadet admin - création", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Permission cadet admin - création", False, f"Erreur: {str(e)}")
        
        return success_count >= 3
    
    def test_presence_statistics(self) -> bool:
        """Test récupération des statistiques de présence"""
        print("\n=== TEST STATISTIQUES DE PRÉSENCE ===")
        
        success_count = 0
        
        # Test 1: Statistiques pour un cadet (admin)
        try:
            cadet_id = self.users["cadet1"]["id"]
            response = requests.get(
                f"{BASE_URL}/presences/stats/{cadet_id}",
                headers=self.get_headers("admin")
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_seances", "presences", "absences", "absences_excusees", "retards", "taux_presence"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Statistiques cadet (admin)", True, f"Taux présence: {data['taux_presence']}%")
                    success_count += 1
                else:
                    self.log_result("Statistiques cadet (admin)", False, "Champs manquants dans la réponse")
            else:
                self.log_result("Statistiques cadet (admin)", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Statistiques cadet (admin)", False, f"Erreur: {str(e)}")
        
        # Test 2: Cadet peut voir ses propres statistiques
        try:
            cadet_id = self.users["cadet1"]["id"]
            response = requests.get(
                f"{BASE_URL}/presences/stats/{cadet_id}",
                headers=self.get_headers("cadet1")
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Statistiques propres (cadet)", True, f"Taux présence: {data['taux_presence']}%")
                success_count += 1
            else:
                self.log_result("Statistiques propres (cadet)", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Statistiques propres (cadet)", False, f"Erreur: {str(e)}")
        
        # Test 3: Cadet ne peut pas voir statistiques d'autres cadets
        try:
            other_cadet_id = self.users["cadet2"]["id"]
            response = requests.get(
                f"{BASE_URL}/presences/stats/{other_cadet_id}",
                headers=self.get_headers("cadet1")
            )
            
            if response.status_code == 403:
                self.log_result("Statistiques autres cadets refusées", True, "403 Forbidden comme attendu")
                success_count += 1
            else:
                self.log_result("Statistiques autres cadets refusées", False, f"Status {response.status_code} (attendu 403)")
                
        except Exception as e:
            self.log_result("Statistiques autres cadets refusées", False, f"Erreur: {str(e)}")
        
        return success_count >= 2
    
    def test_update_presence(self) -> bool:
        """Test mise à jour des présences"""
        print("\n=== TEST MISE À JOUR PRÉSENCES ===")
        
        # D'abord, récupérer une présence existante
        try:
            response = requests.get(
                f"{BASE_URL}/presences?limit=1",
                headers=self.get_headers("admin")
            )
            
            if response.status_code != 200 or not response.json():
                self.log_result("Mise à jour présence", False, "Aucune présence trouvée pour test")
                return False
            
            presence_id = response.json()[0]["id"]
            
            # Tester la mise à jour
            update_data = {
                "status": "absent_excuse",
                "commentaire": "Mise à jour test automatisé"
            }
            
            response = requests.put(
                f"{BASE_URL}/presences/{presence_id}",
                json=update_data,
                headers=self.get_headers("cadet_admin")
            )
            
            if response.status_code == 200:
                self.log_result("Mise à jour présence", True, "Présence mise à jour avec succès")
                return True
            else:
                self.log_result("Mise à jour présence", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Mise à jour présence", False, f"Erreur: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test gestion des erreurs"""
        print("\n=== TEST GESTION DES ERREURS ===")
        
        success_count = 0
        
        # Test 1: Création présence avec cadet inexistant
        try:
            future_date = date.today() + timedelta(days=20)
            presence_data = {
                "cadet_id": "cadet-inexistant-12345",
                "presence_date": future_date.isoformat(),
                "status": "present",
                "commentaire": "Test cadet inexistant"
            }
            
            response = requests.post(
                f"{BASE_URL}/presences",
                json=presence_data,
                headers=self.get_headers("admin")
            )
            
            if response.status_code == 404:
                self.log_result("Erreur cadet inexistant", True, "404 Not Found comme attendu")
                success_count += 1
            else:
                self.log_result("Erreur cadet inexistant", False, f"Status {response.status_code} (attendu 404)")
                
        except Exception as e:
            self.log_result("Erreur cadet inexistant", False, f"Erreur: {str(e)}")
        
        # Test 2: Statistiques pour cadet inexistant
        try:
            response = requests.get(
                f"{BASE_URL}/presences/stats/cadet-inexistant-12345",
                headers=self.get_headers("admin")
            )
            
            if response.status_code in [404, 200]:  # 200 avec stats vides est acceptable
                if response.status_code == 200:
                    data = response.json()
                    if data["total_seances"] == 0:
                        self.log_result("Stats cadet inexistant", True, "Statistiques vides retournées")
                        success_count += 1
                    else:
                        self.log_result("Stats cadet inexistant", False, "Statistiques non vides pour cadet inexistant")
                else:
                    self.log_result("Stats cadet inexistant", True, "404 Not Found comme attendu")
                    success_count += 1
            else:
                self.log_result("Stats cadet inexistant", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Stats cadet inexistant", False, f"Erreur: {str(e)}")
        
        # Test 3: Données invalides
        try:
            future_date = date.today() + timedelta(days=25)
            invalid_data = {
                "cadet_id": self.users["cadet1"]["id"],
                "presence_date": future_date.isoformat(),
                "status": "status_invalide",
                "commentaire": "Test status invalide"
            }
            
            response = requests.post(
                f"{BASE_URL}/presences",
                json=invalid_data,
                headers=self.get_headers("admin")
            )
            
            if response.status_code in [400, 422]:  # Bad Request ou Unprocessable Entity
                self.log_result("Données invalides", True, f"Status {response.status_code} comme attendu")
                success_count += 1
            else:
                self.log_result("Données invalides", False, f"Status {response.status_code} (attendu 400/422)")
                
        except Exception as e:
            self.log_result("Données invalides", False, f"Erreur: {str(e)}")
        
        return success_count >= 2
    
    def run_all_tests(self) -> bool:
        """Exécute tous les tests"""
        print("🚀 DÉBUT DES TESTS SYSTÈME DE GESTION DES PRÉSENCES")
        print(f"Base URL: {BASE_URL}")
        print("=" * 60)
        
        # Authentification préalable
        if not self.authenticate_users():
            print("❌ ÉCHEC AUTHENTIFICATION - ARRÊT DES TESTS")
            return False
        
        # Exécution des tests
        test_methods = [
            self.test_create_individual_presence,
            self.test_create_bulk_presences,
            self.test_get_presences_with_filters,
            self.test_permissions_system,
            self.test_presence_statistics,
            self.test_update_presence,
            self.test_error_handling
        ]
        
        passed_tests = 0
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(test_methods)
        print(f"Tests réussis: {passed_tests}/{total_tests}")
        print(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ TESTS ÉCHOUÉS:")
            for failed_test in self.failed_tests:
                print(f"  - {failed_test}")
        
        print("\n📋 DÉTAIL DES RÉSULTATS:")
        for result in self.test_results:
            print(f"  {result}")
        
        return passed_tests == total_tests

def main():
    """Point d'entrée principal"""
    test_suite = PresenceTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        sys.exit(0)
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)

if __name__ == "__main__":
    main()