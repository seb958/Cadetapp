#!/usr/bin/env python3
"""
Tests complets pour le système d'inspection des uniformes
Référence: test_result.md - Section "Système d'inspection des uniformes"
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os

# Configuration
BASE_URL = "https://squadnet-1.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "username": "aadministrateur",
    "password": "admin123"
}

class UniformInspectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.cadet_token = None
        self.responsible_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details and not success:
            print(f"   Détails: {details}")
    
    def authenticate_admin(self):
        """Authentification admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": "aadministrateur",  # Username admin
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.log_result("Authentification admin", True)
                return True
            else:
                self.log_result("Authentification admin", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Authentification admin", False, str(e))
            return False
    
    def get_auth_headers(self, token):
        """Obtenir les headers d'authentification"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_cache_data_endpoint(self):
        """Test de l'endpoint GET /api/sync/cache-data"""
        print("\n=== TEST ENDPOINT GET /api/sync/cache-data ===")
        
        # Test 1: Accès avec authentification admin
        try:
            response = self.session.get(
                f"{BASE_URL}/sync/cache-data",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de la réponse
                required_keys = ["users", "sections", "activities", "timestamp"]
                has_all_keys = all(key in data for key in required_keys)
                
                if has_all_keys:
                    self.log_result("Structure réponse cache-data", True, 
                                  f"Clés trouvées: {list(data.keys())}")
                    
                    # Vérifier le contenu des données
                    users_count = len(data["users"])
                    sections_count = len(data["sections"])
                    activities_count = len(data["activities"])
                    
                    self.log_result("Données utilisateurs récupérées", users_count > 0,
                                  f"{users_count} utilisateurs trouvés")
                    self.log_result("Données sections récupérées", sections_count > 0,
                                  f"{sections_count} sections trouvées")
                    self.log_result("Données activités récupérées", True,
                                  f"{activities_count} activités trouvées (30 derniers jours)")
                    
                    # Vérifier que les mots de passe hashés sont supprimés
                    passwords_removed = True
                    for user in data["users"]:
                        if "hashed_password" in user or "invitation_token" in user:
                            passwords_removed = False
                            break
                    
                    self.log_result("Mots de passe hashés supprimés", passwords_removed)
                    
                    # Vérifier le timestamp
                    try:
                        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                        self.log_result("Timestamp valide", True, f"Timestamp: {data['timestamp']}")
                    except:
                        self.log_result("Timestamp valide", False, f"Timestamp invalide: {data.get('timestamp')}")
                    
                else:
                    self.log_result("Structure réponse cache-data", False, 
                                  f"Clés manquantes. Trouvées: {list(data.keys())}")
            else:
                self.log_result("Endpoint cache-data accessible", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Test endpoint cache-data", False, str(e))
        
        # Test 2: Accès sans authentification (doit échouer)
        try:
            response = self.session.get(f"{BASE_URL}/sync/cache-data")
            
            if response.status_code == 401:
                self.log_result("Authentification requise pour cache-data", True)
            else:
                self.log_result("Authentification requise pour cache-data", False,
                              f"Status attendu: 401, reçu: {response.status_code}")
        except Exception as e:
            self.log_result("Test authentification cache-data", False, str(e))
    
    def test_sync_batch_endpoint(self):
        """Test de l'endpoint POST /api/sync/batch"""
        print("\n=== TEST ENDPOINT POST /api/sync/batch ===")
        
        # Récupérer des cadets pour les tests
        try:
            response = self.session.get(
                f"{BASE_URL}/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code != 200:
                self.log_result("Récupération utilisateurs pour tests", False, 
                              f"Status: {response.status_code}")
                return
            
            users = response.json()
            cadets = [u for u in users if u.get("role") in ["cadet", "cadet_responsible"]]
            
            if len(cadets) < 2:
                self.log_result("Cadets disponibles pour tests", False, 
                              f"Seulement {len(cadets)} cadets trouvés")
                return
            
            self.log_result("Cadets disponibles pour tests", True, 
                          f"{len(cadets)} cadets trouvés")
            
        except Exception as e:
            self.log_result("Récupération cadets pour tests", False, str(e))
            return
        
        # Test 1: Synchronisation de présences simples
        self.test_simple_presence_sync(cadets)
        
        # Test 2: Fusion intelligente (timestamp plus récent)
        self.test_intelligent_merge(cadets)
        
        # Test 3: Création automatique de présence lors d'inspection
        self.test_automatic_presence_creation(cadets)
        
        # Test 4: Gestion des conflits de timestamp
        self.test_timestamp_conflicts(cadets)
        
        # Test 5: Authentification requise
        self.test_batch_authentication()
        
        # Test 6: Permissions par rôle
        self.test_batch_permissions(cadets)
    
    def test_simple_presence_sync(self, cadets):
        """Test de synchronisation simple de présences"""
        print("\n--- Test synchronisation présences simples ---")
        
        cadet = cadets[0]
        today = date.today().isoformat()
        
        # Créer une présence hors ligne
        offline_presence = {
            "cadet_id": cadet["id"],
            "date": today,
            "status": "present",
            "commentaire": "Test synchronisation hors ligne",
            "timestamp": datetime.utcnow().isoformat(),
            "temp_id": str(uuid.uuid4())
        }
        
        sync_request = {
            "presences": [offline_presence],
            "inspections": []
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/sync/batch",
                json=sync_request,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de la réponse
                required_keys = ["presence_results", "inspection_results", "total_synced", "total_errors"]
                has_structure = all(key in data for key in required_keys)
                
                self.log_result("Structure réponse sync/batch", has_structure)
                
                if has_structure and len(data["presence_results"]) > 0:
                    result = data["presence_results"][0]
                    
                    self.log_result("Synchronisation présence simple", result["success"],
                                  f"Action: {result.get('action')}, Server ID: {result.get('server_id')}")
                    
                    self.log_result("Statistiques sync correctes", 
                                  data["total_synced"] == 1 and data["total_errors"] == 0,
                                  f"Synced: {data['total_synced']}, Errors: {data['total_errors']}")
                else:
                    self.log_result("Synchronisation présence simple", False, "Pas de résultats")
            else:
                self.log_result("Synchronisation présence simple", False,
                              f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Test synchronisation présence simple", False, str(e))
    
    def test_intelligent_merge(self, cadets):
        """Test de fusion intelligente basée sur timestamp"""
        print("\n--- Test fusion intelligente ---")
        
        cadet = cadets[0]
        today = date.today().isoformat()
        
        # Créer d'abord une présence via l'API normale
        try:
            initial_presence = {
                "cadet_id": cadet["id"],
                "status": "absent",
                "commentaire": "Présence initiale"
            }
            
            response = self.session.post(
                f"{BASE_URL}/presences?presence_date={today}",
                json=initial_presence,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code not in [200, 201, 400]:  # 400 si déjà existe
                self.log_result("Création présence initiale pour test fusion", False,
                              f"Status: {response.status_code}")
                return
            
            # Attendre un peu pour avoir un timestamp différent
            time.sleep(1)
            
            # Créer une présence hors ligne plus récente
            offline_presence = {
                "cadet_id": cadet["id"],
                "date": today,
                "status": "present",
                "commentaire": "Présence mise à jour hors ligne",
                "timestamp": datetime.utcnow().isoformat(),
                "temp_id": str(uuid.uuid4())
            }
            
            sync_request = {
                "presences": [offline_presence],
                "inspections": []
            }
            
            response = self.session.post(
                f"{BASE_URL}/sync/batch",
                json=sync_request,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data["presence_results"]) > 0:
                    result = data["presence_results"][0]
                    
                    # La présence plus récente devrait gagner (action = "updated")
                    self.log_result("Fusion intelligente (plus récent gagne)", 
                                  result["success"] and result.get("action") in ["updated", "merged"],
                                  f"Action: {result.get('action')}")
                else:
                    self.log_result("Fusion intelligente", False, "Pas de résultats")
            else:
                self.log_result("Fusion intelligente", False,
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Test fusion intelligente", False, str(e))
    
    def test_automatic_presence_creation(self, cadets):
        """Test de création automatique de présence lors d'inspection"""
        print("\n--- Test création automatique présence ---")
        
        cadet = cadets[1]  # Utiliser un autre cadet
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        # Créer une inspection sans présence préalable
        offline_inspection = {
            "cadet_id": cadet["id"],
            "date": tomorrow,
            "note": "Uniforme correct",
            "timestamp": datetime.utcnow().isoformat(),
            "temp_id": str(uuid.uuid4())
        }
        
        sync_request = {
            "presences": [],
            "inspections": [offline_inspection]
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/sync/batch",
                json=sync_request,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data["inspection_results"]) > 0:
                    result = data["inspection_results"][0]
                    
                    self.log_result("Inspection synchronisée", result["success"],
                                  f"Action: {result.get('action')}")
                    
                    # Vérifier qu'une présence automatique a été créée
                    presence_response = self.session.get(
                        f"{BASE_URL}/presences?date={tomorrow}&cadet_id={cadet['id']}",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if presence_response.status_code == 200:
                        presences = presence_response.json()
                        auto_presence = any(p.get("commentaire", "").startswith("Présence automatique") 
                                          for p in presences)
                        
                        self.log_result("Présence automatique créée", auto_presence,
                                      f"{len(presences)} présences trouvées pour cette date")
                    else:
                        self.log_result("Vérification présence automatique", False,
                                      f"Status: {presence_response.status_code}")
                else:
                    self.log_result("Inspection synchronisée", False, "Pas de résultats")
            else:
                self.log_result("Test création automatique présence", False,
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Test création automatique présence", False, str(e))
    
    def test_timestamp_conflicts(self, cadets):
        """Test de gestion des conflits de timestamp"""
        print("\n--- Test conflits timestamp ---")
        
        cadet = cadets[0]
        test_date = (date.today() + timedelta(days=2)).isoformat()
        
        # Créer deux présences avec des timestamps différents
        old_timestamp = datetime.utcnow() - timedelta(hours=2)
        new_timestamp = datetime.utcnow()
        
        offline_presences = [
            {
                "cadet_id": cadet["id"],
                "date": test_date,
                "status": "absent",
                "commentaire": "Ancienne présence",
                "timestamp": old_timestamp.isoformat(),
                "temp_id": str(uuid.uuid4())
            },
            {
                "cadet_id": cadet["id"],
                "date": test_date,
                "status": "present",
                "commentaire": "Nouvelle présence",
                "timestamp": new_timestamp.isoformat(),
                "temp_id": str(uuid.uuid4())
            }
        ]
        
        sync_request = {
            "presences": offline_presences,
            "inspections": []
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/sync/batch",
                json=sync_request,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data["presence_results"]) == 2:
                    # La première devrait créer, la seconde devrait mettre à jour
                    results = data["presence_results"]
                    
                    created_count = sum(1 for r in results if r.get("action") == "created")
                    updated_count = sum(1 for r in results if r.get("action") == "updated")
                    
                    self.log_result("Gestion conflits timestamp", 
                                  created_count == 1 and updated_count == 1,
                                  f"Créées: {created_count}, Mises à jour: {updated_count}")
                else:
                    self.log_result("Gestion conflits timestamp", False,
                                  f"Attendu 2 résultats, reçu {len(data.get('presence_results', []))}")
            else:
                self.log_result("Test conflits timestamp", False,
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Test conflits timestamp", False, str(e))
    
    def test_batch_authentication(self):
        """Test que l'authentification est requise pour sync/batch"""
        print("\n--- Test authentification sync/batch ---")
        
        sync_request = {
            "presences": [],
            "inspections": []
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/sync/batch", json=sync_request)
            
            if response.status_code == 401:
                self.log_result("Authentification requise pour sync/batch", True)
            else:
                self.log_result("Authentification requise pour sync/batch", False,
                              f"Status attendu: 401, reçu: {response.status_code}")
        except Exception as e:
            self.log_result("Test authentification sync/batch", False, str(e))
    
    def test_batch_permissions(self, cadets):
        """Test des permissions par rôle pour sync/batch"""
        print("\n--- Test permissions sync/batch ---")
        
        # Pour ce test, on utilise le token admin qui a toutes les permissions
        # Dans un vrai test, on devrait créer des tokens pour différents rôles
        
        cadet = cadets[0]
        today = date.today().isoformat()
        
        # Test avec cadet inexistant
        offline_presence = {
            "cadet_id": "inexistant-id",
            "date": today,
            "status": "present",
            "commentaire": "Test cadet inexistant",
            "timestamp": datetime.utcnow().isoformat(),
            "temp_id": str(uuid.uuid4())
        }
        
        sync_request = {
            "presences": [offline_presence],
            "inspections": []
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/sync/batch",
                json=sync_request,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data["presence_results"]) > 0:
                    result = data["presence_results"][0]
                    
                    # Devrait échouer avec "Cadet non trouvé"
                    self.log_result("Gestion cadet inexistant", 
                                  not result["success"] and "non trouvé" in result.get("error", ""),
                                  f"Erreur: {result.get('error')}")
                else:
                    self.log_result("Gestion cadet inexistant", False, "Pas de résultats")
            else:
                self.log_result("Test permissions sync/batch", False,
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Test permissions sync/batch", False, str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS SYSTÈME DE SYNCHRONISATION HORS LIGNE")
        print("=" * 60)
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ Impossible de s'authentifier. Arrêt des tests.")
            return
        
        # Tests des endpoints
        self.test_cache_data_endpoint()
        self.test_sync_batch_endpoint()
        
        # Résumé des résultats
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n🎯 FOCUS: Tests du système de synchronisation hors ligne")
        print("   - GET /api/sync/cache-data: Données pour cache local")
        print("   - POST /api/sync/batch: Synchronisation groupée avec fusion intelligente")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = OfflineSyncTester()
    tester.run_all_tests()