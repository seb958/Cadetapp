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
    
    def test_get_roles(self):
        """Test de récupération des rôles"""
        try:
            response = self.session.get(f"{BASE_URL}/roles")
            
            if response.status_code == 200:
                roles = response.json()
                self.log_test("Role Management", "GET /api/roles", True, f"Récupéré {len(roles)} rôles")
                
                # Vérifier la structure des rôles
                if roles and len(roles) > 0:
                    first_role = roles[0]
                    required_fields = ["id", "name", "permissions", "is_system_role", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_role]
                    
                    if not missing_fields:
                        self.log_test("Role Management", "Role data structure", True, "Structure des rôles correcte")
                    else:
                        self.log_test("Role Management", "Role data structure", False, f"Champs manquants: {missing_fields}")
                else:
                    self.log_test("Role Management", "Role data structure", True, "Aucun rôle trouvé (base vide)")
                    
            else:
                self.log_test("Role Management", "GET /api/roles", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Role Management", "GET /api/roles", False, f"Exception: {str(e)}")
    
    def test_create_role(self):
        """Test de création d'un rôle"""
        try:
            role_data = {
                "name": "Test Role Manager",
                "description": "Rôle de test pour la gestion des permissions",
                "permissions": ["view_users", "create_users", "view_sections"]
            }
            
            response = self.session.post(f"{BASE_URL}/roles", json=role_data)
            
            if response.status_code == 200:
                role = response.json()
                self.created_role_id = role["id"]  # Stocker pour les tests suivants
                self.log_test("Role Management", "POST /api/roles", True, f"Rôle créé avec ID: {role['id']}")
                
                # Vérifier que le rôle a été créé avec les bonnes données
                if (role["name"] == role_data["name"] and 
                    role["description"] == role_data["description"] and
                    set(role["permissions"]) == set(role_data["permissions"])):
                    self.log_test("Role Management", "Role creation data validation", True, "Données du rôle correctes")
                else:
                    self.log_test("Role Management", "Role creation data validation", False, "Données du rôle incorrectes")
                    
            else:
                self.log_test("Role Management", "POST /api/roles", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Role Management", "POST /api/roles", False, f"Exception: {str(e)}")
    
    def test_update_role(self):
        """Test de mise à jour d'un rôle"""
        if not hasattr(self, 'created_role_id'):
            self.log_test("Role Management", "PUT /api/roles/{role_id}", False, "Aucun rôle créé pour le test")
            return
            
        try:
            update_data = {
                "name": "Test Role Manager Updated",
                "description": "Rôle de test mis à jour",
                "permissions": ["view_users", "create_users", "edit_users", "view_sections"]
            }
            
            response = self.session.put(f"{BASE_URL}/roles/{self.created_role_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Role Management", "PUT /api/roles/{role_id}", True, "Rôle mis à jour avec succès")
                
                # Vérifier la mise à jour en récupérant le rôle
                get_response = self.session.get(f"{BASE_URL}/roles")
                if get_response.status_code == 200:
                    roles = get_response.json()
                    updated_role = next((r for r in roles if r["id"] == self.created_role_id), None)
                    
                    if updated_role and updated_role["name"] == update_data["name"]:
                        self.log_test("Role Management", "Role update validation", True, "Mise à jour confirmée")
                    else:
                        self.log_test("Role Management", "Role update validation", False, "Mise à jour non confirmée")
                        
            else:
                self.log_test("Role Management", "PUT /api/roles/{role_id}", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Role Management", "PUT /api/roles/{role_id}", False, f"Exception: {str(e)}")
    
    def test_delete_role(self):
        """Test de suppression d'un rôle"""
        if not hasattr(self, 'created_role_id'):
            self.log_test("Role Management", "DELETE /api/roles/{role_id}", False, "Aucun rôle créé pour le test")
            return
            
        try:
            response = self.session.delete(f"{BASE_URL}/roles/{self.created_role_id}")
            
            if response.status_code == 200:
                self.log_test("Role Management", "DELETE /api/roles/{role_id}", True, "Rôle supprimé avec succès")
                
                # Vérifier que le rôle a été supprimé
                get_response = self.session.get(f"{BASE_URL}/roles")
                if get_response.status_code == 200:
                    roles = get_response.json()
                    deleted_role = next((r for r in roles if r["id"] == self.created_role_id), None)
                    
                    if not deleted_role:
                        self.log_test("Role Management", "Role deletion validation", True, "Suppression confirmée")
                    else:
                        self.log_test("Role Management", "Role deletion validation", False, "Rôle toujours présent")
                        
            else:
                self.log_test("Role Management", "DELETE /api/roles/{role_id}", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Role Management", "DELETE /api/roles/{role_id}", False, f"Exception: {str(e)}")
    
    def test_get_user_filters(self):
        """Test de récupération des filtres utilisateurs"""
        try:
            response = self.session.get(f"{BASE_URL}/users/filters")
            
            if response.status_code == 200:
                filters = response.json()
                self.log_test("User Filters", "GET /api/users/filters", True, "Filtres récupérés avec succès")
                
                # Vérifier la structure des filtres
                required_keys = ["grades", "roles", "sections"]
                missing_keys = [key for key in required_keys if key not in filters]
                
                if not missing_keys:
                    grades_count = len(filters["grades"])
                    roles_count = len(filters["roles"])
                    sections_count = len(filters["sections"])
                    
                    self.log_test("User Filters", "Filter structure validation", True, 
                                f"Structure correcte: {grades_count} grades, {roles_count} rôles, {sections_count} sections")
                else:
                    self.log_test("User Filters", "Filter structure validation", False, f"Clés manquantes: {missing_keys}")
                    
            else:
                self.log_test("User Filters", "GET /api/users/filters", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Filters", "GET /api/users/filters", False, f"Exception: {str(e)}")
    
    def test_user_filtering(self):
        """Test de filtrage des utilisateurs"""
        try:
            # Test 1: Filtrer par rôle
            response = self.session.get(f"{BASE_URL}/users?role=cadet")
            if response.status_code == 200:
                cadets = response.json()
                self.log_test("User Filters", "Filter by role (cadet)", True, f"Trouvé {len(cadets)} cadets")
                
                # Vérifier que tous les utilisateurs retournés ont bien le rôle cadet
                if cadets:
                    all_cadets = all(user.get("role") == "cadet" for user in cadets)
                    if all_cadets:
                        self.log_test("User Filters", "Role filter accuracy", True, "Tous les utilisateurs ont le bon rôle")
                    else:
                        self.log_test("User Filters", "Role filter accuracy", False, "Certains utilisateurs n'ont pas le bon rôle")
            else:
                self.log_test("User Filters", "Filter by role (cadet)", False, f"Status: {response.status_code}")
            
            # Test 2: Filtrer par grade
            response = self.session.get(f"{BASE_URL}/users?grade=cadet")
            if response.status_code == 200:
                users_with_grade = response.json()
                self.log_test("User Filters", "Filter by grade (cadet)", True, f"Trouvé {len(users_with_grade)} utilisateurs avec grade cadet")
                
                # Vérifier l'exactitude du filtre
                if users_with_grade:
                    all_correct_grade = all(user.get("grade") == "cadet" for user in users_with_grade)
                    if all_correct_grade:
                        self.log_test("User Filters", "Grade filter accuracy", True, "Tous les utilisateurs ont le bon grade")
                    else:
                        self.log_test("User Filters", "Grade filter accuracy", False, "Certains utilisateurs n'ont pas le bon grade")
            else:
                self.log_test("User Filters", "Filter by grade (cadet)", False, f"Status: {response.status_code}")
            
            # Test 3: Filtrer par section
            sections_response = self.session.get(f"{BASE_URL}/sections")
            if sections_response.status_code == 200:
                sections = sections_response.json()
                if sections:
                    section_id = sections[0]["id"]
                    response = self.session.get(f"{BASE_URL}/users?section_id={section_id}")
                    if response.status_code == 200:
                        users_in_section = response.json()
                        self.log_test("User Filters", "Filter by section", True, f"Trouvé {len(users_in_section)} utilisateurs dans la section")
                        
                        # Vérifier l'exactitude du filtre
                        if users_in_section:
                            all_correct_section = all(user.get("section_id") == section_id for user in users_in_section)
                            if all_correct_section:
                                self.log_test("User Filters", "Section filter accuracy", True, "Tous les utilisateurs sont dans la bonne section")
                            else:
                                self.log_test("User Filters", "Section filter accuracy", False, "Certains utilisateurs ne sont pas dans la bonne section")
                    else:
                        self.log_test("User Filters", "Filter by section", False, f"Status: {response.status_code}")
                else:
                    self.log_test("User Filters", "Filter by section", True, "Aucune section disponible pour le test")
            
            # Test 4: Filtres combinés
            response = self.session.get(f"{BASE_URL}/users?role=cadet&grade=cadet")
            if response.status_code == 200:
                filtered_users = response.json()
                self.log_test("User Filters", "Combined filters (role + grade)", True, f"Trouvé {len(filtered_users)} utilisateurs avec filtres combinés")
                
                # Vérifier l'exactitude des filtres combinés
                if filtered_users:
                    all_correct = all(user.get("role") == "cadet" and user.get("grade") == "cadet" for user in filtered_users)
                    if all_correct:
                        self.log_test("User Filters", "Combined filters accuracy", True, "Tous les utilisateurs correspondent aux filtres combinés")
                    else:
                        self.log_test("User Filters", "Combined filters accuracy", False, "Certains utilisateurs ne correspondent pas aux filtres")
            else:
                self.log_test("User Filters", "Combined filters (role + grade)", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("User Filters", "User filtering tests", False, f"Exception: {str(e)}")
    
    def test_admin_privileges_field(self):
        """Test du support du champ has_admin_privileges"""
        try:
            # Test 1: Créer un utilisateur avec privilèges admin
            user_data = {
                "nom": "Test",
                "prenom": "Admin Privileges",
                "email": "test.admin.privileges@escadron.fr",
                "grade": "cadet",
                "role": "cadet",
                "has_admin_privileges": True
            }
            
            response = self.session.post(f"{BASE_URL}/users", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result["user_id"]
                self.test_user_id = user_id  # Stocker pour nettoyage
                self.log_test("Admin Privileges", "Create user with admin privileges", True, f"Utilisateur créé avec ID: {user_id}")
                
                # Test 2: Vérifier que l'utilisateur a bien les privilèges admin
                get_response = self.session.get(f"{BASE_URL}/users/{user_id}")
                if get_response.status_code == 200:
                    user = get_response.json()
                    if user.get("has_admin_privileges") == True:
                        self.log_test("Admin Privileges", "Verify admin privileges field", True, "Champ has_admin_privileges correctement défini")
                    else:
                        self.log_test("Admin Privileges", "Verify admin privileges field", False, f"has_admin_privileges = {user.get('has_admin_privileges')}")
                else:
                    self.log_test("Admin Privileges", "Verify admin privileges field", False, f"Impossible de récupérer l'utilisateur: {get_response.status_code}")
                
                # Test 3: Mettre à jour les privilèges admin
                update_data = {"has_admin_privileges": False}
                update_response = self.session.put(f"{BASE_URL}/users/{user_id}", json=update_data)
                
                if update_response.status_code == 200:
                    self.log_test("Admin Privileges", "Update admin privileges", True, "Privilèges admin mis à jour")
                    
                    # Vérifier la mise à jour
                    verify_response = self.session.get(f"{BASE_URL}/users/{user_id}")
                    if verify_response.status_code == 200:
                        updated_user = verify_response.json()
                        if updated_user.get("has_admin_privileges") == False:
                            self.log_test("Admin Privileges", "Verify admin privileges update", True, "Mise à jour des privilèges confirmée")
                        else:
                            self.log_test("Admin Privileges", "Verify admin privileges update", False, "Privilèges non mis à jour")
                else:
                    self.log_test("Admin Privileges", "Update admin privileges", False, f"Status: {update_response.status_code}")
                
            else:
                self.log_test("Admin Privileges", "Create user with admin privileges", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Privileges", "Admin privileges tests", False, f"Exception: {str(e)}")
    
    def test_permissions_protection(self):
        """Test de la protection des endpoints (permissions admin/encadrement)"""
        try:
            # Créer une session sans token admin pour tester les permissions
            test_session = requests.Session()
            
            # Test 1: Accès aux rôles sans authentification
            response = test_session.get(f"{BASE_URL}/roles")
            if response.status_code in [401, 403]:  # Les deux sont acceptables
                self.log_test("Permissions", "Roles access without auth", True, f"Accès refusé sans authentification (status: {response.status_code})")
            else:
                self.log_test("Permissions", "Roles access without auth", False, f"Status inattendu: {response.status_code}")
            
            # Test 2: Accès aux filtres utilisateurs sans authentification
            response = test_session.get(f"{BASE_URL}/users/filters")
            if response.status_code in [401, 403]:  # Les deux sont acceptables
                self.log_test("Permissions", "User filters access without auth", True, f"Accès refusé sans authentification (status: {response.status_code})")
            else:
                self.log_test("Permissions", "User filters access without auth", False, f"Status inattendu: {response.status_code}")
            
            # Test 3: Création de rôle sans authentification
            role_data = {"name": "Test Role", "permissions": []}
            response = test_session.post(f"{BASE_URL}/roles", json=role_data)
            if response.status_code in [401, 403]:  # Les deux sont acceptables
                self.log_test("Permissions", "Create role without auth", True, f"Création refusée sans authentification (status: {response.status_code})")
            else:
                self.log_test("Permissions", "Create role without auth", False, f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            self.log_test("Permissions", "Permissions protection tests", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        # Nettoyer l'utilisateur de test s'il existe
        if hasattr(self, 'test_user_id'):
            try:
                self.session.delete(f"{BASE_URL}/users/{self.test_user_id}")
                print(f"🧹 Nettoyage: Utilisateur de test {self.test_user_id} supprimé")
            except:
                pass
        
        # Nettoyer le rôle de test s'il existe
        if hasattr(self, 'created_role_id'):
            try:
                self.session.delete(f"{BASE_URL}/roles/{self.created_role_id}")
                print(f"🧹 Nettoyage: Rôle de test {self.created_role_id} supprimé")
            except:
                pass

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
        print("🚀 DÉBUT DES TESTS - Système de gestion des rôles et filtres utilisateurs")
        print("=" * 80)
        print(f"📍 Base URL: {BASE_URL}")
        print(f"👤 Admin: {ADMIN_EMAIL}")
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ Impossible de s'authentifier - Arrêt des tests")
            return
        
        # Tests de gestion des rôles
        print("\n📋 TESTS DE GESTION DES RÔLES")
        print("-" * 40)
        self.test_get_roles()
        self.test_create_role()
        self.test_update_role()
        self.test_delete_role()
        
        # Tests des filtres utilisateurs
        print("\n🔍 TESTS DES FILTRES UTILISATEURS")
        print("-" * 40)
        self.test_get_user_filters()
        self.test_user_filtering()
        
        # Tests des privilèges administrateur
        print("\n👑 TESTS DES PRIVILÈGES ADMINISTRATEUR")
        print("-" * 40)
        self.test_admin_privileges_field()
        
        # Tests de protection des permissions
        print("\n🔒 TESTS DE PROTECTION DES PERMISSIONS")
        print("-" * 40)
        self.test_permissions_protection()
        
        # Tests du système d'alertes (existants)
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
        
        # Nettoyage des données de test
        print("\n🧹 NETTOYAGE")
        print("-" * 40)
        self.cleanup_test_data()
        
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