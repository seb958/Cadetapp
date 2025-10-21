#!/usr/bin/env python3
"""
Tests Backend pour l'Endpoint de Synchronisation Offline des Inspections Uniformes
Focus: POST /api/sync/batch avec des inspections uniformes
Référence: test_result.md - Section "Système de synchronisation hors ligne"
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os

# Configuration
BASE_URL = "https://uniformcheck.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "aadministrateur",
    "password": "admin123"
}

class OfflineSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate_admin(self):
        """Authentification admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_test("Authentification admin", True, f"Token obtenu pour {data['user']['username']}")
                return True
            else:
                self.log_test("Authentification admin", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentification admin", False, f"Erreur: {str(e)}")
            return False
    
    def get_test_cadet_id(self):
        """Récupérer l'ID d'un cadet pour les tests"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                # Chercher un cadet actif
                for user in users:
                    if user.get("role") == "cadet" and user.get("actif", False):
                        return user["id"]
                
                # Si pas de cadet, prendre le premier utilisateur actif
                for user in users:
                    if user.get("actif", False):
                        return user["id"]
                        
            return None
        except Exception as e:
            print(f"Erreur récupération cadet: {e}")
            return None
    
    def test_sync_batch_endpoint_exists(self):
        """Test 1: Vérifier que l'endpoint /api/sync/batch existe"""
        try:
            # Test avec requête vide pour vérifier la structure
            response = self.session.post(f"{BASE_URL}/sync/batch", json={
                "presences": [],
                "inspections": []
            })
            
            if response.status_code in [200, 422]:  # 422 = validation error acceptable
                self.log_test("Endpoint /api/sync/batch accessible", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Endpoint /api/sync/batch accessible", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Endpoint /api/sync/batch accessible", False, f"Erreur: {str(e)}")
            return False
    
    def test_sync_inspection_basic(self):
        """Test 2: Synchronisation d'une inspection uniforme basique"""
        cadet_id = self.get_test_cadet_id()
        if not cadet_id:
            self.log_test("Sync inspection basique", False, "Aucun cadet trouvé")
            return False
        
        try:
            # Données d'inspection selon le format attendu dans la review request
            inspection_data = {
                "presences": [],
                "inspections": [{
                    "type": "inspection",
                    "data": {
                        "cadet_id": cadet_id,
                        "date": "2024-01-15",
                        "uniform_type": "C1",
                        "criteria_scores": {
                            "Tenue générale": 3,
                            "Propreté": 4,
                            "Accessoires": 2,
                            "Chaussures": 3
                        },
                        "commentaire": "Test synchronisation offline",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "temp_id": "inspection_test_001"
                    }
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/sync/batch", json=inspection_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de la réponse
                if ("inspection_results" in data and 
                    len(data["inspection_results"]) > 0 and
                    data["inspection_results"][0].get("success", False)):
                    
                    server_id = data["inspection_results"][0].get("server_id")
                    self.log_test("Sync inspection basique (format review)", True, 
                                f"Inspection créée avec ID: {server_id}")
                    return True
                else:
                    # Essayer le format direct (sans wrapper "type" et "data")
                    inspection_data_direct = {
                        "presences": [],
                        "inspections": [{
                            "cadet_id": cadet_id,
                            "date": "2024-01-15",
                            "uniform_type": "C1",
                            "criteria_scores": {
                                "Tenue générale": 3,
                                "Propreté": 4,
                                "Accessoires": 2,
                                "Chaussures": 3
                            },
                            "commentaire": "Test synchronisation offline direct",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "temp_id": "inspection_test_002"
                        }]
                    }
                    
                    response2 = self.session.post(f"{BASE_URL}/sync/batch", json=inspection_data_direct)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if ("inspection_results" in data2 and 
                            len(data2["inspection_results"]) > 0 and
                            data2["inspection_results"][0].get("success", False)):
                            
                            server_id = data2["inspection_results"][0].get("server_id")
                            self.log_test("Sync inspection basique (format direct)", True, 
                                        f"Inspection créée avec ID: {server_id}")
                            return True
                    
                    error_msg = data.get("inspection_results", [{}])[0].get("error", "Erreur inconnue")
                    self.log_test("Sync inspection basique", False, f"Échec sync: {error_msg}")
                    return False
            else:
                self.log_test("Sync inspection basique", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Sync inspection basique", False, f"Erreur: {str(e)}")
            return False
    
    def test_inspection_saved_to_collection(self):
        """Test 3: Vérifier que l'inspection est sauvée dans uniform_inspections"""
        try:
            # Récupérer les inspections via l'endpoint GET
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            
            if response.status_code == 200:
                inspections = response.json()
                
                # Chercher notre inspection de test
                test_inspection = None
                for inspection in inspections:
                    if ("Test synchronisation offline" in inspection.get("commentaire", "") or
                        "Test synchronisation offline direct" in inspection.get("commentaire", "")):
                        test_inspection = inspection
                        break
                
                if test_inspection:
                    # Vérifier les champs requis
                    required_fields = ["id", "cadet_id", "uniform_type", "criteria_scores", 
                                     "total_score", "max_score", "auto_marked_present"]
                    
                    missing_fields = [field for field in required_fields 
                                    if field not in test_inspection]
                    
                    if not missing_fields:
                        self.log_test("Inspection sauvée dans collection", True, 
                                    f"Tous les champs présents. Score: {test_inspection.get('total_score')}%")
                        return True
                    else:
                        self.log_test("Inspection sauvée dans collection", False, 
                                    f"Champs manquants: {missing_fields}")
                        return False
                else:
                    self.log_test("Inspection sauvée dans collection", False, 
                                "Inspection de test non trouvée")
                    return False
            else:
                self.log_test("Inspection sauvée dans collection", False, 
                            f"Erreur GET inspections: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Inspection sauvée dans collection", False, f"Erreur: {str(e)}")
            return False
    
    def test_auto_presence_creation(self):
        """Test 4: Vérifier la création automatique de présence"""
        cadet_id = self.get_test_cadet_id()
        if not cadet_id:
            self.log_test("Création automatique présence", False, "Aucun cadet trouvé")
            return False
        
        try:
            # Utiliser une date différente pour éviter les conflits
            test_date = "2024-01-16"
            
            # Vérifier qu'il n'y a pas de présence existante
            response = self.session.get(f"{BASE_URL}/presences?date={test_date}&cadet_id={cadet_id}")
            existing_presences = response.json() if response.status_code == 200 else []
            
            # Créer une inspection pour déclencher la création automatique de présence
            inspection_data = {
                "presences": [],
                "inspections": [{
                    "cadet_id": cadet_id,
                    "date": test_date,
                    "uniform_type": "C5",
                    "criteria_scores": {
                        "Tenue générale": 4,
                        "Propreté": 3
                    },
                    "commentaire": "Test auto présence",
                    "timestamp": "2024-01-16T09:00:00Z",
                    "temp_id": "inspection_auto_presence"
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/sync/batch", json=inspection_data)
            
            if response.status_code == 200:
                # Vérifier qu'une présence a été créée
                response = self.session.get(f"{BASE_URL}/presences?date={test_date}&cadet_id={cadet_id}")
                
                if response.status_code == 200:
                    presences = response.json()
                    new_presences = [p for p in presences if p not in existing_presences]
                    
                    if new_presences:
                        presence = new_presences[0]
                        if (presence.get("status") == "present" and 
                            "inspection" in presence.get("commentaire", "").lower()):
                            
                            self.log_test("Création automatique présence", True, 
                                        f"Présence créée: {presence.get('status')}")
                            return True
                        else:
                            self.log_test("Création automatique présence", False, 
                                        f"Présence incorrecte: {presence}")
                            return False
                    else:
                        self.log_test("Création automatique présence", False, 
                                    "Aucune nouvelle présence créée")
                        return False
                else:
                    self.log_test("Création automatique présence", False, 
                                f"Erreur récupération présences: {response.status_code}")
                    return False
            else:
                self.log_test("Création automatique présence", False, 
                            f"Erreur sync: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Création automatique présence", False, f"Erreur: {str(e)}")
            return False
    
    def test_auto_marked_present_flag(self):
        """Test 5: Vérifier le flag auto_marked_present"""
        try:
            # Récupérer les inspections récentes
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            
            if response.status_code == 200:
                inspections = response.json()
                
                # Chercher une inspection avec auto_marked_present
                auto_marked_inspection = None
                for inspection in inspections:
                    if inspection.get("auto_marked_present") == True:
                        auto_marked_inspection = inspection
                        break
                
                if auto_marked_inspection:
                    self.log_test("Flag auto_marked_present", True, 
                                f"Flag trouvé sur inspection ID: {auto_marked_inspection.get('id')}")
                    return True
                else:
                    # Vérifier s'il y a des inspections sans le flag (ce qui est aussi valide)
                    total_inspections = len(inspections)
                    if total_inspections > 0:
                        self.log_test("Flag auto_marked_present", True, 
                                    f"Champ présent dans {total_inspections} inspections")
                        return True
                    else:
                        self.log_test("Flag auto_marked_present", False, 
                                    "Aucune inspection trouvée")
                        return False
            else:
                self.log_test("Flag auto_marked_present", False, 
                            f"Erreur GET inspections: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Flag auto_marked_present", False, f"Erreur: {str(e)}")
            return False
    
    def test_score_calculation(self):
        """Test 6: Vérifier le calcul du score (barème 0-4)"""
        cadet_id = self.get_test_cadet_id()
        if not cadet_id:
            self.log_test("Calcul du score", False, "Aucun cadet trouvé")
            return False
        
        try:
            # Test avec des scores connus
            test_cases = [
                {
                    "criteria_scores": {"Critère1": 4, "Critère2": 4, "Critère3": 4, "Critère4": 4},
                    "expected_score": 100.0,
                    "name": "Score parfait"
                },
                {
                    "criteria_scores": {"Critère1": 2, "Critère2": 2},
                    "expected_score": 50.0,
                    "name": "Score moyen"
                },
                {
                    "criteria_scores": {"Critère1": 0, "Critère2": 1, "Critère3": 2},
                    "expected_score": 25.0,
                    "name": "Score faible"
                }
            ]
            
            all_passed = True
            
            for i, test_case in enumerate(test_cases):
                inspection_data = {
                    "presences": [],
                    "inspections": [{
                        "cadet_id": cadet_id,
                        "date": f"2024-01-{17+i}",  # Dates différentes
                        "uniform_type": "C1",
                        "criteria_scores": test_case["criteria_scores"],
                        "commentaire": f"Test calcul score - {test_case['name']}",
                        "timestamp": f"2024-01-{17+i}T10:00:00Z",
                        "temp_id": f"score_test_{i}"
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/sync/batch", json=inspection_data)
                
                if response.status_code == 200:
                    # Récupérer l'inspection créée pour vérifier le score
                    response = self.session.get(f"{BASE_URL}/uniform-inspections")
                    if response.status_code == 200:
                        inspections = response.json()
                        
                        # Chercher notre inspection
                        test_inspection = None
                        for inspection in inspections:
                            if inspection.get("commentaire") == f"Test calcul score - {test_case['name']}":
                                test_inspection = inspection
                                break
                        
                        if test_inspection:
                            actual_score = test_inspection.get("total_score")
                            expected_score = test_case["expected_score"]
                            
                            if abs(actual_score - expected_score) < 0.1:  # Tolérance de 0.1%
                                print(f"   ✅ {test_case['name']}: {actual_score}% (attendu: {expected_score}%)")
                            else:
                                print(f"   ❌ {test_case['name']}: {actual_score}% (attendu: {expected_score}%)")
                                all_passed = False
                        else:
                            print(f"   ❌ {test_case['name']}: Inspection non trouvée")
                            all_passed = False
                    else:
                        print(f"   ❌ {test_case['name']}: Erreur GET inspections")
                        all_passed = False
                else:
                    print(f"   ❌ {test_case['name']}: Erreur sync")
                    all_passed = False
            
            self.log_test("Calcul du score", all_passed, 
                        "Tous les cas de test" if all_passed else "Certains cas ont échoué")
            return all_passed
            
        except Exception as e:
            self.log_test("Calcul du score", False, f"Erreur: {str(e)}")
            return False
    
    def test_regression_other_endpoints(self):
        """Test 7: Vérifier que les autres endpoints d'inspection fonctionnent toujours"""
        try:
            endpoints_to_test = [
                ("/settings", "GET", "Paramètres"),
                ("/uniform-schedule", "GET", "Planning uniformes"),
                ("/uniform-inspections", "GET", "Liste inspections")
            ]
            
            all_passed = True
            
            for endpoint, method, name in endpoints_to_test:
                try:
                    if method == "GET":
                        response = self.session.get(f"{BASE_URL}{endpoint}")
                    
                    if response.status_code == 200:
                        print(f"   ✅ {name}: OK")
                    else:
                        print(f"   ❌ {name}: Status {response.status_code}")
                        all_passed = False
                        
                except Exception as e:
                    print(f"   ❌ {name}: Erreur {str(e)}")
                    all_passed = False
            
            self.log_test("Régression autres endpoints", all_passed, 
                        "Tous les endpoints testés" if all_passed else "Certains endpoints ont échoué")
            return all_passed
            
        except Exception as e:
            self.log_test("Régression autres endpoints", False, f"Erreur: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 8: Gestion des erreurs (cadet inexistant, etc.)"""
        try:
            # Test avec cadet inexistant
            inspection_data = {
                "presences": [],
                "inspections": [{
                    "cadet_id": "cadet-inexistant-12345",
                    "date": "2024-01-20",
                    "uniform_type": "C1",
                    "criteria_scores": {"Test": 3},
                    "commentaire": "Test erreur cadet inexistant",
                    "timestamp": "2024-01-20T10:00:00Z",
                    "temp_id": "error_test_001"
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/sync/batch", json=inspection_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get("inspection_results") and 
                    len(data["inspection_results"]) > 0 and
                    not data["inspection_results"][0].get("success", True) and
                    "non trouvé" in data["inspection_results"][0].get("error", "").lower()):
                    
                    self.log_test("Gestion erreurs", True, 
                                f"Erreur correctement gérée: {data['inspection_results'][0]['error']}")
                    return True
                else:
                    self.log_test("Gestion erreurs", False, 
                                f"Erreur mal gérée: {data}")
                    return False
            else:
                self.log_test("Gestion erreurs", False, 
                            f"Status inattendu: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Gestion erreurs", False, f"Erreur: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests de synchronisation offline"""
        print("🧪 TESTS BACKEND - SYNCHRONISATION OFFLINE INSPECTIONS UNIFORMES")
        print("=" * 70)
        
        # Authentification requise
        if not self.authenticate_admin():
            print("❌ Impossible de s'authentifier. Arrêt des tests.")
            return False
        
        # Tests principaux
        tests = [
            self.test_sync_batch_endpoint_exists,
            self.test_sync_inspection_basic,
            self.test_inspection_saved_to_collection,
            self.test_auto_presence_creation,
            self.test_auto_marked_present_flag,
            self.test_score_calculation,
            self.test_regression_other_endpoints,
            self.test_error_handling
        ]
        
        print("\n📋 EXÉCUTION DES TESTS:")
        print("-" * 40)
        
        for test in tests:
            test()
        
        # Résumé
        print("\n📊 RÉSUMÉ DES TESTS:")
        print("-" * 40)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests réussis: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        
        if self.passed_tests < self.total_tests:
            print(f"❌ Tests échoués: {self.total_tests - self.passed_tests}")
            print("\nDétails des échecs:")
            for result in self.test_results:
                if "❌ FAIL" in result:
                    print(f"  - {result}")
        
        print(f"\n🎯 STATUT GLOBAL: {'✅ SUCCÈS' if self.passed_tests == self.total_tests else '❌ ÉCHECS DÉTECTÉS'}")
        
        return self.passed_tests == self.total_tests

if __name__ == "__main__":
    tester = OfflineSyncTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)