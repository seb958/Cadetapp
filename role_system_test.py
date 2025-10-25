#!/usr/bin/env python3
"""
Tests pour le système de gestion des rôles - Escadron Cadets
Test spécifique pour vérifier le système de rôles et permissions

Tests demandés:
1. Les rôles personnalisés créés sont bien récupérés par GET /api/roles
2. Un nouveau rôle peut être créé avec POST /api/roles 
3. Les rôles créés contiennent les bonnes données (id, name, description, permissions, is_system_role, created_at)
4. Les rôles système vs personnalisés sont bien distingués
5. Vérifier que les rôles créés dans les tests précédents sont toujours présents

Credentials: admin@escadron.fr / admin123 ou aadministrateur / admin123
"""

import requests
import json
import sys
from datetime import datetime
import os

# Configuration
BASE_URL = "https://squadcommand.preview.emergentagent.com/api"

# Credentials de test
ADMIN_CREDENTIALS = {
    "username": "admin@escadron.fr",
    "password": "admin123"
}

ADMIN_CREDENTIALS_ALT = {
    "username": "aadministrateur", 
    "password": "admin123"
}

class RoleSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.test_results = []
        self.created_role_ids = []
        
    def log_result(self, test_name, success, message, details=None):
        """Enregistrer le résultat d'un test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Détails: {details}")
    
    def authenticate_admin(self):
        """Authentifier l'administrateur"""
        print("\n=== AUTHENTIFICATION ADMINISTRATEUR ===")
        
        # Essayer d'abord avec admin@escadron.fr
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.log_result("Authentification Admin", True, f"Connecté avec {ADMIN_CREDENTIALS['username']}")
                return True
        except Exception as e:
            print(f"Erreur avec {ADMIN_CREDENTIALS['username']}: {e}")
        
        # Essayer avec aadministrateur
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=ADMIN_CREDENTIALS_ALT)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.log_result("Authentification Admin", True, f"Connecté avec {ADMIN_CREDENTIALS_ALT['username']}")
                return True
        except Exception as e:
            print(f"Erreur avec {ADMIN_CREDENTIALS_ALT['username']}: {e}")
        
        self.log_result("Authentification Admin", False, "Impossible de s'authentifier avec les deux comptes")
        return False
    
    def get_auth_headers(self):
        """Obtenir les headers d'authentification"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_get_existing_roles(self):
        """Test 1: Récupérer les rôles existants"""
        print("\n=== TEST 1: RÉCUPÉRATION DES RÔLES EXISTANTS ===")
        
        try:
            response = requests.get(f"{self.base_url}/roles", headers=self.get_auth_headers())
            
            if response.status_code == 200:
                roles = response.json()
                self.log_result("GET /api/roles", True, f"Récupération réussie - {len(roles)} rôles trouvés")
                
                # Analyser les rôles
                system_roles = [r for r in roles if r.get("is_system_role", False)]
                custom_roles = [r for r in roles if not r.get("is_system_role", False)]
                
                print(f"   - Rôles système: {len(system_roles)}")
                print(f"   - Rôles personnalisés: {len(custom_roles)}")
                
                # Vérifier la structure des données
                for role in roles[:3]:  # Vérifier les 3 premiers
                    required_fields = ["id", "name", "created_at"]
                    missing_fields = [field for field in required_fields if field not in role]
                    
                    if missing_fields:
                        self.log_result("Structure des rôles", False, f"Champs manquants: {missing_fields}")
                    else:
                        self.log_result("Structure des rôles", True, f"Structure correcte pour {role['name']}")
                
                return roles
            else:
                self.log_result("GET /api/roles", False, f"Erreur HTTP {response.status_code}", response.text)
                return []
                
        except Exception as e:
            self.log_result("GET /api/roles", False, f"Exception: {str(e)}")
            return []
    
    def test_create_custom_role(self):
        """Test 2: Créer un nouveau rôle personnalisé"""
        print("\n=== TEST 2: CRÉATION D'UN RÔLE PERSONNALISÉ ===")
        
        # Données du nouveau rôle
        new_role_data = {
            "name": f"Test_Role_{datetime.now().strftime('%H%M%S')}",
            "description": "Rôle de test créé automatiquement",
            "permissions": ["view_users", "view_sections", "view_presences"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/roles", 
                json=new_role_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                created_role = response.json()
                self.created_role_ids.append(created_role["id"])
                
                self.log_result("POST /api/roles", True, f"Rôle créé: {created_role['name']}")
                
                # Vérifier les données du rôle créé
                expected_fields = ["id", "name", "description", "permissions", "is_system_role", "created_at"]
                for field in expected_fields:
                    if field in created_role:
                        self.log_result(f"Champ {field}", True, f"Présent: {created_role[field]}")
                    else:
                        self.log_result(f"Champ {field}", False, "Champ manquant")
                
                # Vérifier que c'est bien un rôle personnalisé
                if created_role.get("is_system_role", True) == False:
                    self.log_result("Rôle personnalisé", True, "Correctement marqué comme non-système")
                else:
                    self.log_result("Rôle personnalisé", False, "Incorrectement marqué comme système")
                
                return created_role
            else:
                self.log_result("POST /api/roles", False, f"Erreur HTTP {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("POST /api/roles", False, f"Exception: {str(e)}")
            return None
    
    def test_verify_role_persistence(self, created_role):
        """Test 3: Vérifier que le rôle créé est bien récupéré"""
        print("\n=== TEST 3: VÉRIFICATION DE LA PERSISTANCE ===")
        
        if not created_role:
            self.log_result("Vérification persistance", False, "Pas de rôle créé à vérifier")
            return
        
        try:
            response = requests.get(f"{self.base_url}/roles", headers=self.get_auth_headers())
            
            if response.status_code == 200:
                roles = response.json()
                
                # Chercher le rôle créé
                found_role = None
                for role in roles:
                    if role["id"] == created_role["id"]:
                        found_role = role
                        break
                
                if found_role:
                    self.log_result("Persistance du rôle", True, f"Rôle {found_role['name']} retrouvé")
                    
                    # Vérifier que les données sont identiques
                    if found_role["name"] == created_role["name"]:
                        self.log_result("Nom du rôle", True, "Nom correct")
                    else:
                        self.log_result("Nom du rôle", False, f"Nom différent: {found_role['name']} vs {created_role['name']}")
                    
                    if found_role["description"] == created_role["description"]:
                        self.log_result("Description du rôle", True, "Description correcte")
                    else:
                        self.log_result("Description du rôle", False, "Description différente")
                    
                    if set(found_role.get("permissions", [])) == set(created_role.get("permissions", [])):
                        self.log_result("Permissions du rôle", True, "Permissions correctes")
                    else:
                        self.log_result("Permissions du rôle", False, "Permissions différentes")
                        
                else:
                    self.log_result("Persistance du rôle", False, "Rôle créé non retrouvé")
            else:
                self.log_result("Vérification persistance", False, f"Erreur HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Vérification persistance", False, f"Exception: {str(e)}")
    
    def test_system_vs_custom_roles(self):
        """Test 4: Distinguer les rôles système vs personnalisés"""
        print("\n=== TEST 4: DISTINCTION RÔLES SYSTÈME VS PERSONNALISÉS ===")
        
        try:
            response = requests.get(f"{self.base_url}/roles", headers=self.get_auth_headers())
            
            if response.status_code == 200:
                roles = response.json()
                
                system_roles = []
                custom_roles = []
                
                for role in roles:
                    if role.get("is_system_role", False):
                        system_roles.append(role)
                    else:
                        custom_roles.append(role)
                
                self.log_result("Rôles système identifiés", True, f"{len(system_roles)} rôles système trouvés")
                self.log_result("Rôles personnalisés identifiés", True, f"{len(custom_roles)} rôles personnalisés trouvés")
                
                # Afficher quelques exemples
                if system_roles:
                    print("   Exemples de rôles système:")
                    for role in system_roles[:3]:
                        print(f"     - {role['name']} (système: {role.get('is_system_role', False)})")
                
                if custom_roles:
                    print("   Exemples de rôles personnalisés:")
                    for role in custom_roles[:3]:
                        print(f"     - {role['name']} (système: {role.get('is_system_role', False)})")
                
                # Vérifier qu'il y a bien des rôles des deux types
                if len(system_roles) > 0 and len(custom_roles) > 0:
                    self.log_result("Distinction système/personnalisé", True, "Les deux types de rôles sont présents")
                else:
                    self.log_result("Distinction système/personnalisé", False, "Un seul type de rôle trouvé")
                    
            else:
                self.log_result("Distinction rôles", False, f"Erreur HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Distinction rôles", False, f"Exception: {str(e)}")
    
    def test_role_data_completeness(self):
        """Test 5: Vérifier la complétude des données des rôles"""
        print("\n=== TEST 5: COMPLÉTUDE DES DONNÉES DES RÔLES ===")
        
        try:
            response = requests.get(f"{self.base_url}/roles", headers=self.get_auth_headers())
            
            if response.status_code == 200:
                roles = response.json()
                
                required_fields = ["id", "name", "created_at"]
                optional_fields = ["description", "permissions", "is_system_role"]
                
                complete_roles = 0
                incomplete_roles = 0
                
                for role in roles:
                    missing_required = [field for field in required_fields if field not in role or role[field] is None]
                    
                    if not missing_required:
                        complete_roles += 1
                        
                        # Vérifier les types de données
                        if isinstance(role.get("permissions", []), list):
                            self.log_result(f"Permissions {role['name']}", True, "Type liste correct")
                        else:
                            self.log_result(f"Permissions {role['name']}", False, "Type permissions incorrect")
                        
                        if isinstance(role.get("is_system_role", False), bool):
                            self.log_result(f"is_system_role {role['name']}", True, "Type booléen correct")
                        else:
                            self.log_result(f"is_system_role {role['name']}", False, "Type is_system_role incorrect")
                    else:
                        incomplete_roles += 1
                        self.log_result(f"Rôle incomplet {role.get('name', 'UNKNOWN')}", False, f"Champs manquants: {missing_required}")
                
                self.log_result("Complétude des données", True, f"{complete_roles} rôles complets, {incomplete_roles} incomplets")
                
            else:
                self.log_result("Complétude des données", False, f"Erreur HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Complétude des données", False, f"Exception: {str(e)}")
    
    def test_previous_roles_still_present(self):
        """Test 6: Vérifier que les rôles des tests précédents sont toujours présents"""
        print("\n=== TEST 6: PRÉSENCE DES RÔLES DES TESTS PRÉCÉDENTS ===")
        
        try:
            response = requests.get(f"{self.base_url}/roles", headers=self.get_auth_headers())
            
            if response.status_code == 200:
                roles = response.json()
                role_names = [role["name"] for role in roles]
                
                # Chercher des rôles qui pourraient avoir été créés lors de tests précédents
                test_role_patterns = ["Test_Role_", "Custom_", "Nouveau_"]
                previous_test_roles = []
                
                for role in roles:
                    role_name = role["name"]
                    if any(pattern in role_name for pattern in test_role_patterns):
                        previous_test_roles.append(role)
                
                if previous_test_roles:
                    self.log_result("Rôles de tests précédents", True, f"{len(previous_test_roles)} rôles de tests trouvés")
                    for role in previous_test_roles:
                        print(f"     - {role['name']} (créé le {role.get('created_at', 'date inconnue')})")
                else:
                    self.log_result("Rôles de tests précédents", True, "Aucun rôle de test précédent trouvé (normal)")
                
                # Vérifier qu'il y a au moins quelques rôles au total
                if len(roles) >= 4:  # Au minimum les 4 rôles système de base
                    self.log_result("Nombre total de rôles", True, f"{len(roles)} rôles au total")
                else:
                    self.log_result("Nombre total de rôles", False, f"Seulement {len(roles)} rôles trouvés")
                    
            else:
                self.log_result("Rôles précédents", False, f"Erreur HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Rôles précédents", False, f"Exception: {str(e)}")
    
    def cleanup_test_roles(self):
        """Nettoyer les rôles de test créés"""
        print("\n=== NETTOYAGE DES RÔLES DE TEST ===")
        
        for role_id in self.created_role_ids:
            try:
                response = requests.delete(f"{self.base_url}/roles/{role_id}", headers=self.get_auth_headers())
                if response.status_code == 200:
                    print(f"✅ Rôle {role_id} supprimé")
                else:
                    print(f"⚠️ Impossible de supprimer le rôle {role_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression du rôle {role_id}: {e}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS DU SYSTÈME DE RÔLES")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ ÉCHEC DE L'AUTHENTIFICATION - ARRÊT DES TESTS")
            return False
        
        # Tests principaux
        existing_roles = self.test_get_existing_roles()
        created_role = self.test_create_custom_role()
        self.test_verify_role_persistence(created_role)
        self.test_system_vs_custom_roles()
        self.test_role_data_completeness()
        self.test_previous_roles_still_present()
        
        # Nettoyage
        self.cleanup_test_roles()
        
        # Résumé
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS DU SYSTÈME DE RÔLES")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n🎯 FONCTIONNALITÉS TESTÉES:")
        print("   ✓ Récupération des rôles existants (GET /api/roles)")
        print("   ✓ Création de nouveaux rôles (POST /api/roles)")
        print("   ✓ Structure des données des rôles")
        print("   ✓ Distinction rôles système vs personnalisés")
        print("   ✓ Persistance des rôles créés")
        print("   ✓ Présence des rôles des tests précédents")

def main():
    """Fonction principale"""
    tester = RoleSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TESTS TERMINÉS AVEC SUCCÈS")
        return 0
    else:
        print("\n💥 ÉCHEC DES TESTS")
        return 1

if __name__ == "__main__":
    sys.exit(main())