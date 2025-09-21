#!/usr/bin/env python3
"""
Tests complets pour le système d'authentification de l'application escadron de cadets
Teste tous les endpoints d'authentification, permissions et gestion des utilisateurs
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://cadetron.preview.emergentagent.com/api"

# Comptes de test existants
ADMIN_EMAIL = "admin@escadron.fr"
ADMIN_PASSWORD = "admin123"
CADET_EMAIL = "cadet.test@escadron.fr"
CADET_PASSWORD = "cadet123"

class AuthenticationTester:
    def __init__(self):
        self.admin_token = None
        self.cadet_token = None
        self.admin_user = None
        self.cadet_user = None
        self.test_results = []
        self.invitation_token = None
        self.new_user_email = f"test.invite.{int(time.time())}@escadron.fr"
        
    def log_test(self, test_name, success, details=""):
        """Enregistre le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_api_health(self):
        """Test de base - vérifier que l'API répond"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"Message: {data.get('message', 'N/A')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Erreur: {str(e)}")
            return False
    
    def test_admin_login(self):
        """Test de connexion administrateur"""
        try:
            payload = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    self.admin_user = data["user"]
                    user_role = self.admin_user.get("role", "unknown")
                    self.log_test("Login Admin", True, f"Token reçu, Rôle: {user_role}")
                    return True
                else:
                    self.log_test("Login Admin", False, "Token ou utilisateur manquant dans la réponse")
                    return False
            else:
                self.log_test("Login Admin", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Login Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_cadet_login(self):
        """Test de connexion cadet"""
        try:
            payload = {
                "email": CADET_EMAIL,
                "password": CADET_PASSWORD
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.cadet_token = data["access_token"]
                    self.cadet_user = data["user"]
                    user_role = self.cadet_user.get("role", "unknown")
                    self.log_test("Login Cadet", True, f"Token reçu, Rôle: {user_role}")
                    return True
                else:
                    self.log_test("Login Cadet", False, "Token ou utilisateur manquant dans la réponse")
                    return False
            else:
                self.log_test("Login Cadet", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Login Cadet", False, f"Erreur: {str(e)}")
            return False
    
    def test_invalid_login(self):
        """Test avec des identifiants invalides"""
        try:
            payload = {
                "email": "invalid@test.com",
                "password": "wrongpassword"
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Login Invalide", True, "Erreur 401 correctement retournée")
                return True
            else:
                self.log_test("Login Invalide", False, f"Status attendu: 401, reçu: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login Invalide", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_current_user_admin(self):
        """Test récupération profil utilisateur admin"""
        if not self.admin_token:
            self.log_test("Get Current User Admin", False, "Token admin non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == ADMIN_EMAIL:
                    self.log_test("Get Current User Admin", True, f"Profil récupéré: {data.get('prenom')} {data.get('nom')}")
                    return True
                else:
                    self.log_test("Get Current User Admin", False, "Email ne correspond pas")
                    return False
            else:
                self.log_test("Get Current User Admin", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Current User Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_current_user_cadet(self):
        """Test récupération profil utilisateur cadet"""
        if not self.cadet_token:
            self.log_test("Get Current User Cadet", False, "Token cadet non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.cadet_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == CADET_EMAIL:
                    self.log_test("Get Current User Cadet", True, f"Profil récupéré: {data.get('prenom')} {data.get('nom')}")
                    return True
                else:
                    self.log_test("Get Current User Cadet", False, "Email ne correspond pas")
                    return False
            else:
                self.log_test("Get Current User Cadet", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Current User Cadet", False, f"Erreur: {str(e)}")
            return False
    
    def test_protected_route_without_token(self):
        """Test accès route protégée sans token"""
        try:
            response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
            
            if response.status_code == 403:
                self.log_test("Route Protégée Sans Token", True, "Accès refusé correctement (403)")
                return True
            else:
                self.log_test("Route Protégée Sans Token", False, f"Status attendu: 403, reçu: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Route Protégée Sans Token", False, f"Erreur: {str(e)}")
            return False
    
    def test_create_invitation_admin(self):
        """Test création d'invitation par admin"""
        if not self.admin_token:
            self.log_test("Création Invitation Admin", False, "Token admin non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "email": self.new_user_email,
                "nom": "TestInvite",
                "prenom": "Utilisateur",
                "grade": "cadet",
                "role": "cadet"
            }
            response = requests.post(f"{BASE_URL}/auth/invite", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.invitation_token = data["token"]
                    self.log_test("Création Invitation Admin", True, f"Invitation créée pour {self.new_user_email}")
                    return True
                else:
                    self.log_test("Création Invitation Admin", False, "Token d'invitation manquant")
                    return False
            else:
                self.log_test("Création Invitation Admin", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Création Invitation Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_create_invitation_cadet_forbidden(self):
        """Test création d'invitation par cadet (doit être refusée)"""
        if not self.cadet_token:
            self.log_test("Invitation Cadet Interdite", False, "Token cadet non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.cadet_token}"}
            payload = {
                "email": f"forbidden.{int(time.time())}@escadron.fr",
                "nom": "Forbidden",
                "prenom": "Test",
                "grade": "cadet",
                "role": "cadet"
            }
            response = requests.post(f"{BASE_URL}/auth/invite", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 403:
                self.log_test("Invitation Cadet Interdite", True, "Accès refusé correctement pour cadet")
                return True
            else:
                self.log_test("Invitation Cadet Interdite", False, f"Status attendu: 403, reçu: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invitation Cadet Interdite", False, f"Erreur: {str(e)}")
            return False
    
    def test_set_password_with_invitation_token(self):
        """Test définition mot de passe avec token d'invitation"""
        if not self.invitation_token:
            self.log_test("Définition Mot de Passe", False, "Token d'invitation non disponible")
            return False
            
        try:
            payload = {
                "token": self.invitation_token,
                "password": "nouveaumotdepasse123"
            }
            response = requests.post(f"{BASE_URL}/auth/set-password", json=payload, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Définition Mot de Passe", True, "Mot de passe défini avec succès")
                return True
            else:
                self.log_test("Définition Mot de Passe", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Définition Mot de Passe", False, f"Erreur: {str(e)}")
            return False
    
    def test_login_with_new_account(self):
        """Test connexion avec le nouveau compte créé"""
        try:
            payload = {
                "email": self.new_user_email,
                "password": "nouveaumotdepasse123"
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.log_test("Login Nouveau Compte", True, f"Connexion réussie pour {self.new_user_email}")
                    return True
                else:
                    self.log_test("Login Nouveau Compte", False, "Token manquant")
                    return False
            else:
                self.log_test("Login Nouveau Compte", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Login Nouveau Compte", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_users_admin(self):
        """Test récupération liste utilisateurs par admin"""
        if not self.admin_token:
            self.log_test("Liste Utilisateurs Admin", False, "Token admin non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Liste Utilisateurs Admin", True, f"{len(data)} utilisateurs trouvés")
                    return True
                else:
                    self.log_test("Liste Utilisateurs Admin", False, "Réponse n'est pas une liste")
                    return False
            else:
                self.log_test("Liste Utilisateurs Admin", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Liste Utilisateurs Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_users_cadet_forbidden(self):
        """Test récupération liste utilisateurs par cadet (doit être refusée)"""
        if not self.cadet_token:
            self.log_test("Liste Utilisateurs Cadet Interdite", False, "Token cadet non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.cadet_token}"}
            response = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
            
            if response.status_code == 403:
                self.log_test("Liste Utilisateurs Cadet Interdite", True, "Accès refusé correctement pour cadet")
                return True
            else:
                self.log_test("Liste Utilisateurs Cadet Interdite", False, f"Status attendu: 403, reçu: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Liste Utilisateurs Cadet Interdite", False, f"Erreur: {str(e)}")
            return False
    
    def test_create_section_admin(self):
        """Test création de section par admin"""
        if not self.admin_token:
            self.log_test("Création Section Admin", False, "Token admin non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "nom": f"Section Test {int(time.time())}",
                "description": "Section créée pour les tests automatisés"
            }
            response = requests.post(f"{BASE_URL}/sections", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "nom" in data:
                    self.log_test("Création Section Admin", True, f"Section créée: {data['nom']}")
                    return True
                else:
                    self.log_test("Création Section Admin", False, "Données de section manquantes")
                    return False
            else:
                self.log_test("Création Section Admin", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Création Section Admin", False, f"Erreur: {str(e)}")
            return False
    
    def test_get_sections(self):
        """Test récupération liste des sections"""
        if not self.admin_token:
            self.log_test("Liste Sections", False, "Token admin non disponible")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BASE_URL}/sections", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Liste Sections", True, f"{len(data)} sections trouvées")
                    return True
                else:
                    self.log_test("Liste Sections", False, "Réponse n'est pas une liste")
                    return False
            else:
                self.log_test("Liste Sections", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Liste Sections", False, f"Erreur: {str(e)}")
            return False
    
    def test_invalid_token(self):
        """Test avec token invalide"""
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Token Invalide", True, "Token invalide correctement rejeté")
                return True
            else:
                self.log_test("Token Invalide", False, f"Status attendu: 401, reçu: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Token Invalide", False, f"Erreur: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests dans l'ordre approprié"""
        print("=" * 80)
        print("TESTS SYSTÈME D'AUTHENTIFICATION - ESCADRON DE CADETS")
        print("=" * 80)
        print(f"URL de base: {BASE_URL}")
        print(f"Heure de début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Tests de base
        print("🔍 TESTS DE BASE")
        print("-" * 40)
        self.test_api_health()
        self.test_invalid_token()
        self.test_protected_route_without_token()
        print()
        
        # Tests d'authentification
        print("🔐 TESTS D'AUTHENTIFICATION")
        print("-" * 40)
        self.test_admin_login()
        self.test_cadet_login()
        self.test_invalid_login()
        self.test_get_current_user_admin()
        self.test_get_current_user_cadet()
        print()
        
        # Tests système d'invitation
        print("📧 TESTS SYSTÈME D'INVITATION")
        print("-" * 40)
        self.test_create_invitation_admin()
        self.test_create_invitation_cadet_forbidden()
        if self.invitation_token:
            self.test_set_password_with_invitation_token()
            self.test_login_with_new_account()
        print()
        
        # Tests permissions et gestion utilisateurs
        print("👥 TESTS GESTION UTILISATEURS")
        print("-" * 40)
        self.test_get_users_admin()
        self.test_get_users_cadet_forbidden()
        print()
        
        # Tests gestion sections
        print("📋 TESTS GESTION SECTIONS")
        print("-" * 40)
        self.test_create_section_admin()
        self.test_get_sections()
        print()
        
        # Résumé des résultats
        return self.print_summary()
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        print("=" * 80)
        print("RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Tests échoués: {failed_tests}")
        print(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTS ÉCHOUÉS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"• {result['test']}: {result['details']}")
            print()
        
        print("✅ TESTS RÉUSSIS:")
        print("-" * 40)
        for result in self.test_results:
            if result["success"]:
                print(f"• {result['test']}")
        
        print()
        print(f"Heure de fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return passed_tests, failed_tests

def main():
    """Fonction principale"""
    tester = AuthenticationTester()
    passed, failed = tester.run_all_tests()
    
    # Code de sortie basé sur les résultats
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) ont échoué. Vérifiez les détails ci-dessus.")
        sys.exit(1)
    else:
        print(f"\n🎉 Tous les {passed} tests ont réussi!")
        sys.exit(0)

if __name__ == "__main__":
    main()