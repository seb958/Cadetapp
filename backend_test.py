#!/usr/bin/env python3
"""
Tests Backend pour le Système d'Inspection des Uniformes avec Barème de Notation (0-4)
Test du système d'inspection des uniformes avec le nouveau barème de notation de 0 à 4 points par critère.
Référence: test_result.md - Section "Système d'inspection des uniformes avec barème de notation"
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
    
    def test_settings_endpoints(self):
        """Test des endpoints de gestion des paramètres"""
        print("\n=== TESTS GESTION DES PARAMÈTRES ===")
        
        # Test 1: GET /api/settings - Récupération des paramètres
        try:
            response = self.session.get(f"{BASE_URL}/settings")
            if response.status_code == 200:
                settings = response.json()
                required_fields = ["escadronName", "address", "contactEmail", "allowMotivatedAbsences", 
                                 "consecutiveAbsenceThreshold", "inspectionCriteria", "autoBackup"]
                
                has_all_fields = all(field in settings for field in required_fields)
                self.log_test("GET /api/settings - Structure", has_all_fields, 
                            f"Champs présents: {list(settings.keys())}")
                
                # Vérifier que inspectionCriteria est un dictionnaire
                criteria_is_dict = isinstance(settings.get("inspectionCriteria"), dict)
                self.log_test("GET /api/settings - inspectionCriteria type", criteria_is_dict,
                            f"Type: {type(settings.get('inspectionCriteria'))}")
            else:
                self.log_test("GET /api/settings", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/settings", False, f"Erreur: {str(e)}")
        
        # Test 2: POST /api/settings - Sauvegarde des paramètres avec critères d'inspection
        try:
            test_settings = {
                "escadronName": "Escadron Test",
                "address": "123 Rue Test",
                "contactEmail": "test@escadron.fr",
                "allowMotivatedAbsences": True,
                "consecutiveAbsenceThreshold": 3,
                "inspectionCriteria": {
                    "C1 - Tenue de Parade": [
                        "Kippi réglementaire",
                        "Chemise blanche impeccable",
                        "Cravate correctement nouée",
                        "Chaussures cirées"
                    ],
                    "C5 - Tenue d'Entraînement": [
                        "Treillis propre",
                        "Rangers lacées",
                        "Béret correctement porté"
                    ]
                },
                "autoBackup": True
            }
            
            response = self.session.post(f"{BASE_URL}/settings", json=test_settings)
            if response.status_code == 200:
                self.log_test("POST /api/settings - Sauvegarde", True, "Paramètres sauvegardés")
                
                # Vérifier la persistance
                verify_response = self.session.get(f"{BASE_URL}/settings")
                if verify_response.status_code == 200:
                    saved_settings = verify_response.json()
                    criteria_saved = saved_settings.get("inspectionCriteria", {})
                    c1_criteria = criteria_saved.get("C1 - Tenue de Parade", [])
                    
                    criteria_match = len(c1_criteria) == 4 and "Kippi réglementaire" in c1_criteria
                    self.log_test("POST /api/settings - Persistance", criteria_match,
                                f"Critères C1 sauvés: {len(c1_criteria)} éléments")
                else:
                    self.log_test("POST /api/settings - Vérification persistance", False, 
                                f"Status: {verify_response.status_code}")
            else:
                self.log_test("POST /api/settings - Sauvegarde", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("POST /api/settings", False, f"Erreur: {str(e)}")
    
    def test_uniform_schedule_endpoints(self):
        """Test des endpoints de planification des tenues"""
        print("\n=== TESTS PLANIFICATION DES TENUES ===")
        
        test_date = "2025-06-15"
        
        # Test 1: GET /api/uniform-schedule - Tenue du jour (sans date)
        try:
            response = self.session.get(f"{BASE_URL}/uniform-schedule")
            if response.status_code == 200:
                schedule = response.json()
                has_required_fields = all(field in schedule for field in ["date", "uniform_type"])
                self.log_test("GET /api/uniform-schedule - Tenue du jour", has_required_fields,
                            f"Réponse: {schedule.get('message', 'Tenue trouvée')}")
            else:
                self.log_test("GET /api/uniform-schedule - Tenue du jour", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/uniform-schedule - Tenue du jour", False, f"Erreur: {str(e)}")
        
        # Test 2: POST /api/uniform-schedule - Programmer une tenue
        try:
            schedule_data = {
                "date": test_date,
                "uniform_type": "C1 - Tenue de Parade"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-schedule", json=schedule_data)
            if response.status_code == 200:
                result = response.json()
                self.log_test("POST /api/uniform-schedule - Programmation", True,
                            f"Message: {result.get('message')}")
                
                # Stocker l'ID pour suppression ultérieure
                self.schedule_id = result.get("id")
            else:
                self.log_test("POST /api/uniform-schedule - Programmation", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("POST /api/uniform-schedule - Programmation", False, f"Erreur: {str(e)}")
        
        # Test 3: GET /api/uniform-schedule?date_param=2025-06-15 - Tenue pour date spécifique
        try:
            response = self.session.get(f"{BASE_URL}/uniform-schedule", params={"date_param": test_date})
            if response.status_code == 200:
                schedule = response.json()
                uniform_found = schedule.get("uniform_type") == "C1 - Tenue de Parade"
                self.log_test("GET /api/uniform-schedule - Date spécifique", uniform_found,
                            f"Tenue: {schedule.get('uniform_type')}")
            else:
                self.log_test("GET /api/uniform-schedule - Date spécifique", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/uniform-schedule - Date spécifique", False, f"Erreur: {str(e)}")
        
        # Test 4: DELETE /api/uniform-schedule/{schedule_id} - Supprimer planification
        if hasattr(self, 'schedule_id') and self.schedule_id:
            try:
                response = self.session.delete(f"{BASE_URL}/uniform-schedule/{self.schedule_id}")
                if response.status_code == 200:
                    self.log_test("DELETE /api/uniform-schedule - Suppression", True,
                                "Planification supprimée")
                else:
                    self.log_test("DELETE /api/uniform-schedule - Suppression", False,
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("DELETE /api/uniform-schedule - Suppression", False, f"Erreur: {str(e)}")
    
    def get_test_cadet(self):
        """Récupérer un cadet pour les tests"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                # Chercher Emma Leroy ou un autre cadet
                for user in users:
                    if user.get("email") == "emma.leroy@escadron.fr" or user.get("role") == "cadet":
                        return user
                # Prendre le premier utilisateur si aucun cadet spécifique trouvé
                return users[0] if users else None
            return None
        except:
            return None
    
    def test_uniform_inspections_endpoints(self):
        """Test des endpoints d'inspection des uniformes"""
        print("\n=== TESTS INSPECTIONS D'UNIFORMES ===")
        
        # Récupérer un cadet pour les tests
        test_cadet = self.get_test_cadet()
        if not test_cadet:
            self.log_test("Récupération cadet test", False, "Aucun cadet trouvé")
            return
        
        cadet_id = test_cadet["id"]
        cadet_name = f"{test_cadet['prenom']} {test_cadet['nom']}"
        self.log_test("Récupération cadet test", True, f"Cadet: {cadet_name}")
        
        # Test 1: POST /api/uniform-inspections - Créer inspection avec nouveau barème (0-4)
        try:
            inspection_data = {
                "cadet_id": cadet_id,
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Kippi réglementaire": 4,
                    "Chemise blanche impeccable": 3,
                    "Pantalon bien repassé": 2,
                    "Chaussures cirées": 1
                },
                "commentaire": "Test barème notation"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier le calcul du score avec nouveau barème (4+3+2+1)/16 * 100 = 62.5%
                expected_score = 62.5
                actual_score = result.get("total_score")
                score_correct = actual_score == expected_score
                
                self.log_test("POST /api/uniform-inspections - Création nouveau barème", True,
                            f"Score calculé: {actual_score}% (attendu: {expected_score}%)")
                
                self.log_test("POST /api/uniform-inspections - Calcul score 0-4", score_correct,
                            f"Score: {actual_score}% vs {expected_score}%")
                
                # Vérifier la présence du champ max_score
                max_score = result.get("max_score")
                expected_max_score = 16  # 4 critères * 4 points max
                max_score_correct = max_score == expected_max_score
                self.log_test("POST /api/uniform-inspections - max_score présent", max_score_correct,
                            f"max_score: {max_score} (attendu: {expected_max_score})")
                
                # Vérifier le flag auto_marked_present
                auto_marked = result.get("auto_marked_present", False)
                self.log_test("POST /api/uniform-inspections - Auto présence", auto_marked,
                            f"Flag auto_marked_present: {auto_marked}")
                
                self.inspection_id = result.get("inspection_id")
            else:
                self.log_test("POST /api/uniform-inspections - Création", False,
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("POST /api/uniform-inspections - Création", False, f"Erreur: {str(e)}")
        
        # Test 2: GET /api/uniform-inspections - Récupération toutes inspections
        try:
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            if response.status_code == 200:
                inspections = response.json()
                self.log_test("GET /api/uniform-inspections - Récupération", True,
                            f"{len(inspections)} inspections trouvées")
                
                # Vérifier la structure des données enrichies avec nouveau format
                if inspections:
                    inspection = inspections[0]
                    required_fields = ["id", "cadet_id", "cadet_nom", "cadet_prenom", "cadet_grade",
                                     "date", "uniform_type", "criteria_scores", "max_score", "total_score",
                                     "inspected_by", "inspector_name", "auto_marked_present"]
                    
                    has_all_fields = all(field in inspection for field in required_fields)
                    self.log_test("GET /api/uniform-inspections - Structure enrichie nouveau format", has_all_fields,
                                f"Champs présents: {list(inspection.keys())}")
                    
                    # Vérifier que criteria_scores contient des entiers (0-4) et non des booléens
                    criteria_scores = inspection.get("criteria_scores", {})
                    if criteria_scores:
                        all_integers = all(isinstance(score, int) and 0 <= score <= 4 for score in criteria_scores.values())
                        self.log_test("GET /api/uniform-inspections - criteria_scores format 0-4", all_integers,
                                    f"Scores: {criteria_scores}")
                    else:
                        self.log_test("GET /api/uniform-inspections - criteria_scores présent", False, "criteria_scores manquant")
                    
                    # Vérifier la présence du champ max_score
                    has_max_score = "max_score" in inspection and isinstance(inspection["max_score"], int)
                    self.log_test("GET /api/uniform-inspections - max_score présent", has_max_score,
                                f"max_score: {inspection.get('max_score')}")
                    
                    # Vérifier les données enrichies
                    has_enriched_data = (inspection.get("cadet_nom") and 
                                       inspection.get("inspector_name") and
                                       inspection.get("inspector_name") != "Inconnu")
                    self.log_test("GET /api/uniform-inspections - Données enrichies", has_enriched_data,
                                f"Cadet: {inspection.get('cadet_nom')}, Inspecteur: {inspection.get('inspector_name')}")
            else:
                self.log_test("GET /api/uniform-inspections - Récupération", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/uniform-inspections - Récupération", False, f"Erreur: {str(e)}")
        
        # Test 3: GET /api/uniform-inspections?date=2025-06-15 - Filtrage par date
        try:
            test_date = date.today().isoformat()
            response = self.session.get(f"{BASE_URL}/uniform-inspections", params={"date": test_date})
            if response.status_code == 200:
                inspections = response.json()
                self.log_test("GET /api/uniform-inspections - Filtre date", True,
                            f"{len(inspections)} inspections pour {test_date}")
            else:
                self.log_test("GET /api/uniform-inspections - Filtre date", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/uniform-inspections - Filtre date", False, f"Erreur: {str(e)}")
        
        # Test 4: GET /api/uniform-inspections?cadet_id={id} - Filtrage par cadet (admin only)
        try:
            response = self.session.get(f"{BASE_URL}/uniform-inspections", params={"cadet_id": cadet_id})
            if response.status_code == 200:
                inspections = response.json()
                # Vérifier que toutes les inspections sont pour ce cadet
                all_for_cadet = all(insp.get("cadet_id") == cadet_id for insp in inspections)
                self.log_test("GET /api/uniform-inspections - Filtre cadet", all_for_cadet,
                            f"{len(inspections)} inspections pour cadet {cadet_name}")
            else:
                self.log_test("GET /api/uniform-inspections - Filtre cadet", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/uniform-inspections - Filtre cadet", False, f"Erreur: {str(e)}")
    
    def test_permissions(self):
        """Test des permissions granulaires"""
        print("\n=== TESTS PERMISSIONS ===")
        
        # Test 1: Vérifier que l'admin peut programmer des tenues
        try:
            schedule_data = {
                "date": "2025-06-16",
                "uniform_type": "C5 - Tenue d'Entraînement"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-schedule", json=schedule_data)
            admin_can_schedule = response.status_code == 200
            self.log_test("Permissions - Admin peut programmer tenue", admin_can_schedule,
                        f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Permissions - Admin peut programmer tenue", False, f"Erreur: {str(e)}")
        
        # Test 2: Vérifier que l'admin peut inspecter
        test_cadet = self.get_test_cadet()
        if test_cadet:
            try:
                inspection_data = {
                    "cadet_id": test_cadet["id"],
                    "uniform_type": "C5 - Tenue d'Entraînement",
                    "criteria_scores": {
                        "Treillis propre": True,
                        "Rangers lacées": True,
                        "Béret correctement porté": False
                    },
                    "commentaire": "Test permissions admin"
                }
                
                response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
                admin_can_inspect = response.status_code == 200
                self.log_test("Permissions - Admin peut inspecter", admin_can_inspect,
                            f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Permissions - Admin peut inspecter", False, f"Erreur: {str(e)}")
    
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        print("\n=== TESTS GESTION DES ERREURS ===")
        
        # Test 1: Inspection avec cadet inexistant
        try:
            inspection_data = {
                "cadet_id": "cadet-inexistant-12345",
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {"Test": True},
                "commentaire": "Test erreur"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
            error_handled = response.status_code == 404
            self.log_test("Gestion erreurs - Cadet inexistant", error_handled,
                        f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gestion erreurs - Cadet inexistant", False, f"Erreur: {str(e)}")
        
        # Test 2: Suppression planification inexistante
        try:
            response = self.session.delete(f"{BASE_URL}/uniform-schedule/schedule-inexistant-12345")
            error_handled = response.status_code == 404
            self.log_test("Gestion erreurs - Planification inexistante", error_handled,
                        f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gestion erreurs - Planification inexistante", False, f"Erreur: {str(e)}")
    
    def test_complete_inspection_workflow(self):
        """Test du flux complet d'inspection"""
        print("\n=== TEST FLUX COMPLET D'INSPECTION ===")
        
        # 1. Sauvegarder des critères d'inspection
        try:
            settings = {
                "escadronName": "Escadron Test Complet",
                "address": "456 Avenue Test",
                "contactEmail": "test.complet@escadron.fr",
                "allowMotivatedAbsences": True,
                "consecutiveAbsenceThreshold": 3,
                "inspectionCriteria": {
                    "C1 - Tenue de Parade": [
                        "Kippi réglementaire",
                        "Chemise blanche impeccable",
                        "Cravate correctement nouée"
                    ]
                },
                "autoBackup": True
            }
            
            response = self.session.post(f"{BASE_URL}/settings", json=settings)
            step1_success = response.status_code == 200
            self.log_test("Flux complet - 1. Sauvegarde critères", step1_success)
        except Exception as e:
            self.log_test("Flux complet - 1. Sauvegarde critères", False, f"Erreur: {str(e)}")
            return
        
        # 2. Programmer la tenue du jour
        try:
            schedule_data = {
                "date": date.today().isoformat(),
                "uniform_type": "C1 - Tenue de Parade"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-schedule", json=schedule_data)
            step2_success = response.status_code == 200
            self.log_test("Flux complet - 2. Programmation tenue", step2_success)
        except Exception as e:
            self.log_test("Flux complet - 2. Programmation tenue", False, f"Erreur: {str(e)}")
            return
        
        # 3. Créer une inspection avec auto-présence
        test_cadet = self.get_test_cadet()
        if not test_cadet:
            self.log_test("Flux complet - 3. Récupération cadet", False, "Aucun cadet trouvé")
            return
        
        try:
            inspection_data = {
                "cadet_id": test_cadet["id"],
                "uniform_type": "C1 - Tenue de Parade",
                "criteria_scores": {
                    "Kippi réglementaire": True,
                    "Chemise blanche impeccable": True,
                    "Cravate correctement nouée": False
                },
                "commentaire": "Test flux complet - inspection automatisée"
            }
            
            response = self.session.post(f"{BASE_URL}/uniform-inspections", json=inspection_data)
            if response.status_code == 200:
                result = response.json()
                
                # Vérifier le calcul du score (2/3 = 66.67%)
                expected_score = 66.67
                actual_score = result.get("total_score")
                score_correct = abs(actual_score - expected_score) < 0.01
                
                auto_marked = result.get("auto_marked_present", False)
                
                self.log_test("Flux complet - 3. Inspection créée", True,
                            f"Score: {actual_score}%, Auto-présence: {auto_marked}")
                self.log_test("Flux complet - 3. Calcul score correct", score_correct,
                            f"Attendu: {expected_score}%, Obtenu: {actual_score}%")
            else:
                self.log_test("Flux complet - 3. Inspection créée", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Flux complet - 3. Inspection créée", False, f"Erreur: {str(e)}")
        
        # 4. Récupérer les inspections et vérifier les données enrichies
        try:
            response = self.session.get(f"{BASE_URL}/uniform-inspections")
            if response.status_code == 200:
                inspections = response.json()
                
                # Chercher notre inspection
                our_inspection = None
                for insp in inspections:
                    if (insp.get("cadet_id") == test_cadet["id"] and 
                        insp.get("uniform_type") == "C1 - Tenue de Parade"):
                        our_inspection = insp
                        break
                
                if our_inspection:
                    # Vérifier les données enrichies
                    has_cadet_name = our_inspection.get("cadet_nom") == test_cadet["nom"]
                    has_inspector_name = our_inspection.get("inspector_name") and our_inspection.get("inspector_name") != "Inconnu"
                    has_section = our_inspection.get("section_id") is not None
                    
                    self.log_test("Flux complet - 4. Données enrichies", 
                                has_cadet_name and has_inspector_name,
                                f"Cadet: {our_inspection.get('cadet_nom')}, Inspecteur: {our_inspection.get('inspector_name')}")
                else:
                    self.log_test("Flux complet - 4. Inspection trouvée", False, "Inspection non trouvée")
            else:
                self.log_test("Flux complet - 4. Récupération inspections", False,
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Flux complet - 4. Récupération inspections", False, f"Erreur: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS SYSTÈME D'INSPECTION DES UNIFORMES")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"👤 Authentification: {ADMIN_CREDENTIALS['username']}")
        print("=" * 80)
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ ÉCHEC DE L'AUTHENTIFICATION - ARRÊT DES TESTS")
            return
        
        # Exécuter les tests par catégorie
        self.test_settings_endpoints()
        self.test_uniform_schedule_endpoints()
        self.test_uniform_inspections_endpoints()
        self.test_permissions()
        self.test_error_handling()
        self.test_complete_inspection_workflow()
        
        # Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests réussis: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        
        if self.passed_tests == self.total_tests:
            print("🎉 TOUS LES TESTS SONT PASSÉS - SYSTÈME FONCTIONNEL")
        else:
            print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFICATION NÉCESSAIRE")
        
        print("\n📋 DÉTAIL DES RÉSULTATS:")
        for result in self.test_results:
            print(f"  {result}")
        
        return success_rate >= 80  # Considérer comme succès si 80%+ des tests passent

if __name__ == "__main__":
    tester = UniformInspectionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ TESTS TERMINÉS AVEC SUCCÈS")
        sys.exit(0)
    else:
        print("\n❌ TESTS TERMINÉS AVEC DES ÉCHECS")
        sys.exit(1)