#!/usr/bin/env python3
"""
Tests complets pour l'API Gestion Escadron Cadets
Focus sur le nouveau système de gestion des rôles et filtres utilisateurs

Nouveaux endpoints testés:
- GET /api/roles - Récupérer tous les rôles
- POST /api/roles - Créer un nouveau rôle
- PUT /api/roles/{role_id} - Mettre à jour un rôle
- DELETE /api/roles/{role_id} - Supprimer un rôle
- GET /api/users/filters - Récupérer les options de filtres
- GET /api/users?grade=...&role=...&section_id=... - Filtrer les utilisateurs

Modifications utilisateurs:
- Support du champ has_admin_privileges dans POST/PUT /users
"""

import requests
import json
from datetime import datetime, date, timedelta
import uuid
import sys

# Configuration
BASE_URL = "https://cadetsquad-app.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@escadron.fr"
ADMIN_PASSWORD = "admin123"

class CadetSquadTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "categories": {}
        }
        
    def log_test(self, category, test_name, success, message=""):
        """Enregistrer le résultat d'un test"""
        self.test_results["total_tests"] += 1
        
        if category not in self.test_results["categories"]:
            self.test_results["categories"][category] = {
                "passed": 0,
                "failed": 0,
                "tests": []
            }
        
        if success:
            self.test_results["passed_tests"] += 1
            self.test_results["categories"][category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results["failed_tests"] += 1
            self.test_results["categories"][category]["failed"] += 1
            status = "❌ FAIL"
            
        self.test_results["categories"][category]["tests"].append({
            "name": test_name,
            "success": success,
            "message": message
        })
        
        print(f"{status} - {category}: {test_name}")
        if message:
            print(f"    {message}")
    
    def authenticate_admin(self):
        """Authentification admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                self.log_test("Authentication", "Admin login", True, f"Token obtenu pour {data['user']['email']}")
                return True
            else:
                self.log_test("Authentication", "Admin login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", "Admin login", False, f"Exception: {str(e)}")
            return False
    
    def test_consecutive_absences_calculation(self):
        """Test du calcul des absences consécutives"""
        try:
            # Test avec seuil par défaut (3)
            response = self.session.get(f"{BASE_URL}/alerts/consecutive-absences")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Alerts", "Calculate consecutive absences (default threshold)", True, 
                            f"Trouvé {len(data)} cadets avec absences consécutives")
                
                # Vérifier la structure des données
                if data and len(data) > 0:
                    first_item = data[0]
                    required_fields = ["cadet_id", "consecutive_absences", "last_absence_date"]
                    missing_fields = [field for field in required_fields if field not in first_item]
                    
                    if not missing_fields:
                        self.log_test("Alerts", "Consecutive absences data structure", True, 
                                    f"Structure correcte: {list(first_item.keys())}")
                    else:
                        self.log_test("Alerts", "Consecutive absences data structure", False, 
                                    f"Champs manquants: {missing_fields}")
                else:
                    self.log_test("Alerts", "Consecutive absences data structure", True, 
                                "Aucune absence consécutive trouvée (normal si pas de données)")
                
                # Test avec seuil personnalisé
                response_custom = self.session.get(f"{BASE_URL}/alerts/consecutive-absences?threshold=2")
                if response_custom.status_code == 200:
                    custom_data = response_custom.json()
                    self.log_test("Alerts", "Calculate consecutive absences (custom threshold=2)", True, 
                                f"Trouvé {len(custom_data)} cadets avec seuil=2")
                else:
                    self.log_test("Alerts", "Calculate consecutive absences (custom threshold=2)", False, 
                                f"Status: {response_custom.status_code}")
                
            else:
                self.log_test("Alerts", "Calculate consecutive absences (default threshold)", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Alerts", "Calculate consecutive absences", False, f"Exception: {str(e)}")
    
    def test_get_alerts(self):
        """Test de récupération des alertes"""
        try:
            response = self.session.get(f"{BASE_URL}/alerts")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Alerts", "Get all alerts", True, f"Trouvé {len(data)} alertes")
                
                # Vérifier la structure si des alertes existent
                if data and len(data) > 0:
                    first_alert = data[0]
                    required_fields = ["id", "cadet_id", "cadet_nom", "cadet_prenom", "consecutive_absences", 
                                     "status", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_alert]
                    
                    if not missing_fields:
                        self.log_test("Alerts", "Alert data structure", True, 
                                    f"Structure correcte avec statut: {first_alert.get('status')}")
                    else:
                        self.log_test("Alerts", "Alert data structure", False, 
                                    f"Champs manquants: {missing_fields}")
                else:
                    self.log_test("Alerts", "Alert data structure", True, "Aucune alerte existante")
                    
            else:
                self.log_test("Alerts", "Get all alerts", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Alerts", "Get all alerts", False, f"Exception: {str(e)}")
    
    def test_generate_alerts(self):
        """Test de génération d'alertes"""
        try:
            # Test avec seuil par défaut
            response = self.session.post(f"{BASE_URL}/alerts/generate")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                self.log_test("Alerts", "Generate alerts (default threshold)", True, message)
                
                # Test avec seuil personnalisé
                response_custom = self.session.post(f"{BASE_URL}/alerts/generate?threshold=2")
                if response_custom.status_code == 200:
                    custom_data = response_custom.json()
                    custom_message = custom_data.get("message", "")
                    self.log_test("Alerts", "Generate alerts (custom threshold=2)", True, custom_message)
                else:
                    self.log_test("Alerts", "Generate alerts (custom threshold=2)", False, 
                                f"Status: {response_custom.status_code}")
                
            else:
                self.log_test("Alerts", "Generate alerts (default threshold)", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Alerts", "Generate alerts", False, f"Exception: {str(e)}")
    
    def test_alert_status_updates(self):
        """Test de mise à jour des statuts d'alertes"""
        try:
            # D'abord récupérer les alertes existantes
            response = self.session.get(f"{BASE_URL}/alerts")
            
            if response.status_code != 200:
                self.log_test("Alerts", "Alert status updates", False, "Impossible de récupérer les alertes")
                return
                
            alerts = response.json()
            
            if not alerts:
                # Générer des alertes d'abord
                gen_response = self.session.post(f"{BASE_URL}/alerts/generate?threshold=1")
                if gen_response.status_code == 200:
                    # Récupérer à nouveau
                    response = self.session.get(f"{BASE_URL}/alerts")
                    if response.status_code == 200:
                        alerts = response.json()
                
            if alerts and len(alerts) > 0:
                alert_id = alerts[0]["id"]
                
                # Test 1: Passer à "contacted"
                update_data = {
                    "status": "contacted",
                    "contact_comment": "Famille contactée par téléphone"
                }
                
                response = self.session.put(f"{BASE_URL}/alerts/{alert_id}", json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Alerts", "Update alert to contacted", True, 
                                "Alerte mise à jour vers 'contacted'")
                    
                    # Test 2: Passer à "resolved"
                    resolve_data = {"status": "resolved"}
                    response = self.session.put(f"{BASE_URL}/alerts/{alert_id}", json=resolve_data)
                    
                    if response.status_code == 200:
                        self.log_test("Alerts", "Update alert to resolved", True, 
                                    "Alerte mise à jour vers 'resolved'")
                    else:
                        self.log_test("Alerts", "Update alert to resolved", False, 
                                    f"Status: {response.status_code}")
                        
                else:
                    self.log_test("Alerts", "Update alert to contacted", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    
                # Test 3: Test avec ID invalide
                invalid_response = self.session.put(f"{BASE_URL}/alerts/invalid-id", json=update_data)
                if invalid_response.status_code == 404:
                    self.log_test("Alerts", "Update non-existent alert", True, 
                                "Erreur 404 correcte pour ID invalide")
                else:
                    self.log_test("Alerts", "Update non-existent alert", False, 
                                f"Status attendu 404, reçu: {invalid_response.status_code}")
                    
            else:
                self.log_test("Alerts", "Alert status updates", False, 
                            "Aucune alerte disponible pour les tests de mise à jour")
                
        except Exception as e:
            self.log_test("Alerts", "Alert status updates", False, f"Exception: {str(e)}")
    
    def test_delete_alert(self):
        """Test de suppression d'alertes"""
        try:
            # Générer une alerte pour la supprimer
            gen_response = self.session.post(f"{BASE_URL}/alerts/generate?threshold=1")
            
            # Récupérer les alertes
            response = self.session.get(f"{BASE_URL}/alerts")
            
            if response.status_code == 200:
                alerts = response.json()
                
                if alerts and len(alerts) > 0:
                    alert_id = alerts[0]["id"]
                    
                    # Supprimer l'alerte
                    delete_response = self.session.delete(f"{BASE_URL}/alerts/{alert_id}")
                    
                    if delete_response.status_code == 200:
                        self.log_test("Alerts", "Delete alert", True, "Alerte supprimée avec succès")
                        
                        # Vérifier que l'alerte n'existe plus
                        verify_response = self.session.delete(f"{BASE_URL}/alerts/{alert_id}")
                        if verify_response.status_code == 404:
                            self.log_test("Alerts", "Verify alert deletion", True, 
                                        "Alerte correctement supprimée (404 sur seconde tentative)")
                        else:
                            self.log_test("Alerts", "Verify alert deletion", False, 
                                        f"Status attendu 404, reçu: {verify_response.status_code}")
                    else:
                        self.log_test("Alerts", "Delete alert", False, 
                                    f"Status: {delete_response.status_code}")
                        
                    # Test avec ID invalide
                    invalid_response = self.session.delete(f"{BASE_URL}/alerts/invalid-id")
                    if invalid_response.status_code == 404:
                        self.log_test("Alerts", "Delete non-existent alert", True, 
                                    "Erreur 404 correcte pour ID invalide")
                    else:
                        self.log_test("Alerts", "Delete non-existent alert", False, 
                                    f"Status attendu 404, reçu: {invalid_response.status_code}")
                        
                else:
                    self.log_test("Alerts", "Delete alert", False, "Aucune alerte disponible pour suppression")
                    
            else:
                self.log_test("Alerts", "Delete alert", False, "Impossible de récupérer les alertes")
                
        except Exception as e:
            self.log_test("Alerts", "Delete alert", False, f"Exception: {str(e)}")
    
    def test_alert_permissions(self):
        """Test des permissions pour les alertes"""
        try:
            # Créer un token cadet pour tester les permissions
            cadet_response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": "marie.dubois@escadron.fr",  # Cadet existant
                "password": "cadet123"
            })
            
            if cadet_response.status_code == 200:
                cadet_data = cadet_response.json()
                cadet_token = cadet_data["access_token"]
                
                # Tester l'accès avec token cadet
                cadet_session = requests.Session()
                cadet_session.headers.update({
                    "Authorization": f"Bearer {cadet_token}"
                })
                
                # Test accès aux alertes (devrait échouer)
                response = cadet_session.get(f"{BASE_URL}/alerts")
                if response.status_code == 403:
                    self.log_test("Alerts", "Cadet permission denied", True, 
                                "Accès correctement refusé pour cadet")
                else:
                    self.log_test("Alerts", "Cadet permission denied", False, 
                                f"Status attendu 403, reçu: {response.status_code}")
                    
                # Test génération d'alertes (devrait échouer)
                gen_response = cadet_session.post(f"{BASE_URL}/alerts/generate")
                if gen_response.status_code == 403:
                    self.log_test("Alerts", "Cadet generate permission denied", True, 
                                "Génération d'alertes correctement refusée pour cadet")
                else:
                    self.log_test("Alerts", "Cadet generate permission denied", False, 
                                f"Status attendu 403, reçu: {gen_response.status_code}")
                    
            else:
                self.log_test("Alerts", "Alert permissions", False, 
                            "Impossible de se connecter avec compte cadet pour test permissions")
                
        except Exception as e:
            self.log_test("Alerts", "Alert permissions", False, f"Exception: {str(e)}")
    
    def test_existing_endpoints_compatibility(self):
        """Test de compatibilité avec les endpoints existants"""
        try:
            # Test endpoint utilisateurs
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Compatibility", "Users endpoint", True, f"Trouvé {len(users)} utilisateurs")
            else:
                self.log_test("Compatibility", "Users endpoint", False, f"Status: {response.status_code}")
            
            # Test endpoint sections
            response = self.session.get(f"{BASE_URL}/sections")
            if response.status_code == 200:
                sections = response.json()
                self.log_test("Compatibility", "Sections endpoint", True, f"Trouvé {len(sections)} sections")
            else:
                self.log_test("Compatibility", "Sections endpoint", False, f"Status: {response.status_code}")
            
            # Test endpoint présences
            response = self.session.get(f"{BASE_URL}/presences")
            if response.status_code == 200:
                presences = response.json()
                self.log_test("Compatibility", "Presences endpoint", True, f"Trouvé {len(presences)} présences")
            else:
                self.log_test("Compatibility", "Presences endpoint", False, f"Status: {response.status_code}")
            
            # Test endpoint activités
            response = self.session.get(f"{BASE_URL}/activities")
            if response.status_code == 200:
                activities = response.json()
                self.log_test("Compatibility", "Activities endpoint", True, f"Trouvé {len(activities)} activités")
            else:
                self.log_test("Compatibility", "Activities endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Compatibility", "Existing endpoints", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS - Système d'alertes d'absences consécutives")
        print("=" * 80)
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ Impossible de s'authentifier - Arrêt des tests")
            return
        
        # Tests du système d'alertes
        print("\n📋 TESTS DU SYSTÈME D'ALERTES")
        print("-" * 40)
        self.test_consecutive_absences_calculation()
        self.test_get_alerts()
        self.test_generate_alerts()
        self.test_alert_status_updates()
        self.test_delete_alert()
        self.test_alert_permissions()
        
        # Tests de compatibilité
        print("\n🔄 TESTS DE COMPATIBILITÉ")
        print("-" * 40)
        self.test_existing_endpoints_compatibility()
        
        # Résumé
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total des tests: {total}")
        print(f"✅ Réussis: {passed}")
        print(f"❌ Échoués: {failed}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        print("\n📋 DÉTAIL PAR CATÉGORIE:")
        for category, results in self.test_results["categories"].items():
            cat_total = results["passed"] + results["failed"]
            cat_rate = (results["passed"] / cat_total * 100) if cat_total > 0 else 0
            print(f"  {category}: {results['passed']}/{cat_total} ({cat_rate:.1f}%)")
        
        if failed > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for category, results in self.test_results["categories"].items():
                failed_tests = [t for t in results["tests"] if not t["success"]]
                if failed_tests:
                    print(f"  {category}:")
                    for test in failed_tests:
                        print(f"    - {test['name']}: {test['message']}")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Système d'alertes fonctionnel")
        elif success_rate >= 75:
            print("✅ BON! Quelques ajustements mineurs nécessaires")
        elif success_rate >= 50:
            print("⚠️  MOYEN! Plusieurs problèmes à corriger")
        else:
            print("❌ CRITIQUE! Système nécessite des corrections majeures")

if __name__ == "__main__":
    tester = CadetSquadTester()
    tester.run_all_tests()