#!/usr/bin/env python3
"""
Tests pour vérifier les permissions présences avec has_admin_privileges
Demande spécifique: Tester que les cadets avec has_admin_privileges=True peuvent prendre les présences
"""

import requests
import json
from datetime import datetime, date
import sys

# Configuration
BASE_URL = "https://commandhub-cadet.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_test(self, name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.test_details.append(f"{status} - {name}: {details}")
        print(f"{status} - {name}: {details}")
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"RÉSUMÉ DES TESTS - PERMISSIONS PRÉSENCES has_admin_privileges")
        print(f"{'='*80}")
        print(f"Total: {self.total_tests} | Réussis: {self.passed_tests} | Échoués: {self.failed_tests}")
        print(f"Taux de réussite: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*80}")

def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def login_user(username, password):
    """Connexion utilisateur et récupération du token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["user"]
        else:
            return None, None
    except Exception as e:
        print(f"Erreur lors de la connexion: {e}")
        return None, None

def generate_password_for_user(admin_token, user_id):
    """Génère un mot de passe temporaire pour un utilisateur"""
    try:
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/generate-password",
            headers=get_auth_headers(admin_token)
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Erreur génération mot de passe: {e}")
        return None

def test_permissions_presences_admin_privileges():
    """Test principal des permissions présences avec has_admin_privileges"""
    results = TestResults()
    
    print("🔐 TESTS PERMISSIONS PRÉSENCES - has_admin_privileges")
    print("="*80)
    
    # 1. Connexion admin
    print("\n1️⃣ CONNEXION ADMINISTRATEUR")
    admin_token, admin_user = login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
    
    if not admin_token:
        results.add_test("Connexion admin", False, "Impossible de se connecter en tant qu'admin")
        results.print_summary()
        return results
    
    results.add_test("Connexion admin", True, f"Connecté: {admin_user['prenom']} {admin_user['nom']}")
    
    # 2. Récupérer la liste des utilisateurs
    print("\n2️⃣ RÉCUPÉRATION LISTE UTILISATEURS")
    try:
        response = requests.get(f"{BASE_URL}/users", headers=get_auth_headers(admin_token))
        if response.status_code == 200:
            users = response.json()
            results.add_test("GET /api/users", True, f"{len(users)} utilisateurs trouvés")
        else:
            results.add_test("GET /api/users", False, f"Status: {response.status_code}")
            results.print_summary()
            return results
    except Exception as e:
        results.add_test("GET /api/users", False, f"Erreur: {e}")
        results.print_summary()
        return results
    
    # 3. Chercher utilisateur maryesoleil.bourassa
    print("\n3️⃣ RECHERCHE UTILISATEUR maryesoleil.bourassa")
    target_user = None
    for user in users:
        username = user.get('username', '').lower()
        nom = user.get('nom', '').lower()
        prenom = user.get('prenom', '').lower()
        
        if ('maryesoleil' in username or 'maryesoleil' in prenom or 
            'bourassa' in username or 'bourassa' in nom):
            target_user = user
            break
    
    if target_user:
        results.add_test("Recherche maryesoleil.bourassa", True, 
                        f"Trouvé: {target_user['prenom']} {target_user['nom']} (ID: {target_user['id']}, username: {target_user.get('username', 'N/A')})")
        
        # Vérifier has_admin_privileges
        has_admin_privileges = target_user.get('has_admin_privileges', False)
        results.add_test("Vérification has_admin_privileges", has_admin_privileges, 
                        f"has_admin_privileges = {has_admin_privileges}")
        
        if not has_admin_privileges:
            print("⚠️  L'utilisateur n'a pas has_admin_privileges=True. Test des permissions non applicable.")
            results.print_summary()
            return results
            
    else:
        results.add_test("Recherche maryesoleil.bourassa", False, "Utilisateur non trouvé")
        print("⚠️  Utilisateur maryesoleil.bourassa non trouvé. Création d'un utilisateur de test...")
        
        # Créer un utilisateur de test avec has_admin_privileges=True
        test_user_data = {
            "nom": "Bourassa",
            "prenom": "Maryesoleil",
            "grade": "cadet",
            "role": "cadet",
            "has_admin_privileges": True
        }
        
        try:
            response = requests.post(f"{BASE_URL}/users", 
                                   json=test_user_data,
                                   headers=get_auth_headers(admin_token))
            if response.status_code == 200:
                created_data = response.json()
                # Récupérer l'utilisateur créé
                response = requests.get(f"{BASE_URL}/users", headers=get_auth_headers(admin_token))
                users = response.json()
                for user in users:
                    if user['nom'] == 'Bourassa' and user['prenom'] == 'Maryesoleil':
                        target_user = user
                        break
                
                results.add_test("Création utilisateur test", True, 
                               f"Créé: {target_user['prenom']} {target_user['nom']} avec has_admin_privileges=True")
            else:
                results.add_test("Création utilisateur test", False, f"Status: {response.status_code}")
                results.print_summary()
                return results
        except Exception as e:
            results.add_test("Création utilisateur test", False, f"Erreur: {e}")
            results.print_summary()
            return results
    
    # 4. Vérifier/Générer mot de passe
    print("\n4️⃣ GESTION MOT DE PASSE UTILISATEUR")
    user_username = target_user.get('username')
    user_password = None
    
    if not user_username:
        results.add_test("Vérification username", False, "Pas de username défini")
        results.print_summary()
        return results
    
    # Essayer de se connecter pour voir si un mot de passe existe
    test_token, test_user_data = login_user(user_username, "test123")
    
    if not test_token:
        # Générer un mot de passe temporaire
        print(f"Génération mot de passe pour {user_username}...")
        password_data = generate_password_for_user(admin_token, target_user['id'])
        
        if password_data:
            user_password = password_data['temporary_password']
            results.add_test("Génération mot de passe", True, 
                           f"Mot de passe généré: {user_password}")
        else:
            results.add_test("Génération mot de passe", False, "Échec génération")
            results.print_summary()
            return results
    else:
        user_password = "test123"
        results.add_test("Vérification mot de passe existant", True, "Mot de passe existant fonctionnel")
    
    # 5. Connexion avec l'utilisateur has_admin_privileges
    print("\n5️⃣ CONNEXION UTILISATEUR has_admin_privileges")
    user_token, user_data = login_user(user_username, user_password)
    
    if user_token:
        results.add_test("Connexion utilisateur has_admin_privileges", True, 
                        f"Connecté: {user_data['prenom']} {user_data['nom']}")
    else:
        results.add_test("Connexion utilisateur has_admin_privileges", False, 
                        f"Échec connexion avec {user_username}/{user_password}")
        results.print_summary()
        return results
    
    # 6. Test GET /api/presences (doit être 200 OK maintenant)
    print("\n6️⃣ TEST GET /api/presences avec has_admin_privileges")
    try:
        response = requests.get(f"{BASE_URL}/presences", headers=get_auth_headers(user_token))
        
        if response.status_code == 200:
            presences = response.json()
            results.add_test("GET /api/presences avec has_admin_privileges", True, 
                           f"Status 200 OK - {len(presences)} présences récupérées")
        elif response.status_code == 403:
            results.add_test("GET /api/presences avec has_admin_privileges", False, 
                           "Status 403 - Accès toujours refusé malgré has_admin_privileges=True")
        else:
            results.add_test("GET /api/presences avec has_admin_privileges", False, 
                           f"Status inattendu: {response.status_code}")
    except Exception as e:
        results.add_test("GET /api/presences avec has_admin_privileges", False, f"Erreur: {e}")
    
    # 7. Test POST /api/presences (créer une présence de test)
    print("\n7️⃣ TEST POST /api/presences avec has_admin_privileges")
    
    # Trouver un cadet pour créer une présence
    test_cadet = None
    for user in users:
        if user['role'] == 'cadet' and user['id'] != target_user['id']:
            test_cadet = user
            break
    
    if test_cadet:
        presence_data = {
            "cadet_id": test_cadet['id'],
            "status": "present",
            "commentaire": "Test présence has_admin_privileges"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/presences", 
                                   json=presence_data,
                                   headers=get_auth_headers(user_token))
            
            if response.status_code == 200:
                results.add_test("POST /api/presences avec has_admin_privileges", True, 
                               f"Status 200 OK - Présence créée pour {test_cadet['prenom']} {test_cadet['nom']}")
            elif response.status_code == 403:
                results.add_test("POST /api/presences avec has_admin_privileges", False, 
                               "Status 403 - Création refusée malgré has_admin_privileges=True")
            elif response.status_code == 400:
                # Vérifier si c'est une présence qui existe déjà
                error_detail = response.json().get('detail', '')
                if 'existe déjà' in error_detail:
                    results.add_test("POST /api/presences avec has_admin_privileges", True, 
                                   f"Status 400 - Présence existe déjà (fonctionnalité normale): {error_detail}")
                else:
                    results.add_test("POST /api/presences avec has_admin_privileges", False, 
                                   f"Status 400 - Erreur: {error_detail}")
            else:
                results.add_test("POST /api/presences avec has_admin_privileges", False, 
                               f"Status inattendu: {response.status_code} - {response.text}")
        except Exception as e:
            results.add_test("POST /api/presences avec has_admin_privileges", False, f"Erreur: {e}")
    else:
        results.add_test("POST /api/presences avec has_admin_privileges", False, 
                        "Aucun cadet trouvé pour test")
    
    # 8. Test régression - Utilisateur SANS has_admin_privileges
    print("\n8️⃣ TEST RÉGRESSION - Utilisateur SANS has_admin_privileges")
    
    # Trouver un cadet normal (sans has_admin_privileges, pas chef de section)
    normal_cadet = None
    for user in users:
        if (user['role'] == 'cadet' and 
            not user.get('has_admin_privileges', False) and
            'chef' not in user['role'].lower() and
            'sergent' not in user['role'].lower() and
            'commandant' not in user['role'].lower() and
            'adjudant' not in user['role'].lower()):
            normal_cadet = user
            break
    
    if normal_cadet:
        # Générer mot de passe si nécessaire
        normal_username = normal_cadet.get('username')
        if normal_username:
            # Essayer connexion
            normal_token, _ = login_user(normal_username, "test123")
            
            if not normal_token:
                # Générer mot de passe
                password_data = generate_password_for_user(admin_token, normal_cadet['id'])
                if password_data:
                    normal_password = password_data['temporary_password']
                    normal_token, _ = login_user(normal_username, normal_password)
            
            if normal_token:
                # Test GET /api/presences (doit être 403)
                try:
                    response = requests.get(f"{BASE_URL}/presences", headers=get_auth_headers(normal_token))
                    
                    if response.status_code == 403:
                        results.add_test("Régression - Cadet normal GET /api/presences", True, 
                                       f"Status 403 - Accès correctement refusé pour {normal_cadet['prenom']} {normal_cadet['nom']}")
                    elif response.status_code == 200:
                        # Vérifier si le cadet ne voit que ses propres présences
                        presences = response.json()
                        own_presences = [p for p in presences if p['cadet_id'] == normal_cadet['id']]
                        if len(presences) == len(own_presences):
                            results.add_test("Régression - Cadet normal GET /api/presences", True, 
                                           f"Status 200 - Cadet voit seulement ses propres présences ({len(own_presences)})")
                        else:
                            results.add_test("Régression - Cadet normal GET /api/presences", False, 
                                           f"Status 200 - Cadet voit {len(presences)} présences au lieu de seulement les siennes")
                    else:
                        results.add_test("Régression - Cadet normal GET /api/presences", False, 
                                       f"Status inattendu: {response.status_code}")
                except Exception as e:
                    results.add_test("Régression - Cadet normal GET /api/presences", False, f"Erreur: {e}")
            else:
                results.add_test("Régression - Connexion cadet normal", False, 
                               f"Impossible de se connecter avec {normal_cadet['prenom']} {normal_cadet['nom']}")
        else:
            results.add_test("Régression - Username cadet normal", False, 
                           f"Pas de username pour {normal_cadet['prenom']} {normal_cadet['nom']}")
    else:
        results.add_test("Régression - Recherche cadet normal", False, 
                        "Aucun cadet normal trouvé pour test régression")
    
    # 9. Lister tous les utilisateurs avec has_admin_privileges=True
    print("\n9️⃣ VÉRIFICATION UTILISATEURS avec has_admin_privileges=True")
    
    admin_privilege_users = [user for user in users if user.get('has_admin_privileges', False)]
    
    if admin_privilege_users:
        results.add_test("Utilisateurs avec has_admin_privileges", True, 
                        f"{len(admin_privilege_users)} utilisateurs trouvés")
        
        # Vérifier qu'ils sont bien des cadets
        cadets_with_privileges = []
        non_cadets_with_privileges = []
        
        for user in admin_privilege_users:
            role = user['role'].lower()
            if 'cadet' in role or role in ['cadet', 'cadet_responsible']:
                cadets_with_privileges.append(user)
            else:
                non_cadets_with_privileges.append(user)
        
        results.add_test("Cadets avec has_admin_privileges", True, 
                        f"{len(cadets_with_privileges)} cadets avec privilèges admin")
        
        if non_cadets_with_privileges:
            results.add_test("Non-cadets avec has_admin_privileges", True, 
                           f"{len(non_cadets_with_privileges)} non-cadets avec privilèges (normal pour encadrement)")
        
        # Afficher détails
        print("\nDétail des utilisateurs avec has_admin_privileges=True:")
        for user in admin_privilege_users:
            print(f"  - {user['prenom']} {user['nom']} (Rôle: {user['role']}, Grade: {user['grade']})")
    else:
        results.add_test("Utilisateurs avec has_admin_privileges", False, 
                        "Aucun utilisateur avec has_admin_privileges=True trouvé")
    
    results.print_summary()
    return results

if __name__ == "__main__":
    print("🚀 DÉMARRAGE TESTS PERMISSIONS PRÉSENCES has_admin_privileges")
    print(f"Base URL: {BASE_URL}")
    print(f"Admin: {ADMIN_USERNAME}")
    
    results = test_permissions_presences_admin_privileges()
    
    # Code de sortie basé sur les résultats
    if results.failed_tests == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results.failed_tests} TEST(S) ÉCHOUÉ(S)")
        sys.exit(1)