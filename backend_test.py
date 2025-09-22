#!/usr/bin/env python3
"""
Tests pour l'endpoint DELETE /api/sections/{id}
Test de suppression des sections avec désaffectation des utilisateurs
"""

import requests
import json
import uuid
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://squadronapp.preview.emergentagent.com/api"

# Comptes de test
ADMIN_CREDENTIALS = {
    "email": "admin@escadron.fr",
    "password": "admin123"
}

# Créer un compte cadet pour les tests de permissions
CADET_CREDENTIALS = {
    "email": "cadet.test@escadron.fr", 
    "password": "cadet123"
}

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []
    
    def add_result(self, test_name, passed, message=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        
        self.results.append(result)
        print(result)
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"RÉSUMÉ DES TESTS - ENDPOINT DELETE /api/sections/{{id}}")
        print(f"{'='*60}")
        print(f"Total: {self.total_tests}")
        print(f"Réussis: {self.passed_tests}")
        print(f"Échoués: {self.failed_tests}")
        print(f"Taux de réussite: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*60}")

def get_auth_token(credentials):
    """Obtenir un token d'authentification"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=credentials)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Erreur login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erreur lors de l'authentification: {e}")
        return None

def create_test_section(token, section_name=None):
    """Créer une section de test"""
    if not section_name:
        section_name = f"Section Test {uuid.uuid4().hex[:8]}"
    
    headers = {"Authorization": f"Bearer {token}"}
    section_data = {
        "nom": section_name,
        "description": "Section créée pour les tests de suppression"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/sections", json=section_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur création section: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erreur lors de la création de section: {e}")
        return None

def create_test_user(token, section_id=None):
    """Créer un utilisateur de test"""
    headers = {"Authorization": f"Bearer {token}"}
    user_data = {
        "nom": f"TestUser{uuid.uuid4().hex[:6]}",
        "prenom": "Test",
        "grade": "cadet",
        "role": "cadet",
        "section_id": section_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/invite", json=user_data, headers=headers)
        if response.status_code == 200:
            return user_data
        else:
            print(f"Erreur création utilisateur: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erreur lors de la création d'utilisateur: {e}")
        return None

def get_users_by_section(token, section_id):
    """Récupérer les utilisateurs d'une section"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            return [user for user in users if user.get("section_id") == section_id]
        else:
            print(f"Erreur récupération utilisateurs: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
        return []

def test_delete_section_endpoint():
    """Tests complets pour l'endpoint DELETE /api/sections/{id}"""
    results = TestResults()
    
    print("🚀 DÉBUT DES TESTS - ENDPOINT DELETE /api/sections/{id}")
    print("="*60)
    
    # 1. Test d'authentification - utilisateur non authentifié
    print("\n📋 CATÉGORIE 1: TESTS D'AUTHENTIFICATION")
    print("-" * 40)
    
    fake_section_id = str(uuid.uuid4())
    response = requests.delete(f"{BASE_URL}/sections/{fake_section_id}")
    results.add_result(
        "Utilisateur non authentifié (401)",
        response.status_code == 401,
        f"Status: {response.status_code}"
    )
    
    # 2. Obtenir les tokens d'authentification
    admin_token = get_auth_token(ADMIN_CREDENTIALS)
    cadet_token = get_auth_token(CADET_CREDENTIALS)
    
    if not admin_token:
        results.add_result("Obtention token admin", False, "Impossible d'obtenir le token admin")
        results.print_summary()
        return results
    
    results.add_result("Obtention token admin", True, "Token admin obtenu avec succès")
    
    if not cadet_token:
        results.add_result("Obtention token cadet", False, "Impossible d'obtenir le token cadet")
    else:
        results.add_result("Obtention token cadet", True, "Token cadet obtenu avec succès")
    
    # 3. Test permissions - cadet normal ne peut pas supprimer
    if cadet_token:
        headers = {"Authorization": f"Bearer {cadet_token}"}
        response = requests.delete(f"{BASE_URL}/sections/{fake_section_id}", headers=headers)
        results.add_result(
            "Cadet normal ne peut pas supprimer (403)",
            response.status_code == 403,
            f"Status: {response.status_code}"
        )
    
    # 4. Tests des cas normaux
    print("\n📋 CATÉGORIE 2: TESTS CAS NORMAUX")
    print("-" * 40)
    
    # Créer une section de test
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    test_section = create_test_section(admin_token, "Section à supprimer")
    
    if test_section:
        results.add_result("Création section de test", True, f"Section créée: {test_section['nom']}")
        section_id = test_section["id"]
        
        # Supprimer la section
        response = requests.delete(f"{BASE_URL}/sections/{section_id}", headers=admin_headers)
        results.add_result(
            "Suppression section existante",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            response_data = response.json()
            results.add_result(
                "Message de succès présent",
                "message" in response_data and "supprimée définitivement" in response_data["message"],
                f"Message: {response_data.get('message', 'Aucun message')}"
            )
            
            # Vérifier que la section n'existe plus
            get_response = requests.get(f"{BASE_URL}/sections", headers=admin_headers)
            if get_response.status_code == 200:
                sections = get_response.json()
                section_exists = any(s["id"] == section_id for s in sections)
                results.add_result(
                    "Section supprimée de la base",
                    not section_exists,
                    f"Section trouvée: {section_exists}"
                )
            else:
                results.add_result("Vérification suppression", False, "Impossible de vérifier la suppression")
        
    else:
        results.add_result("Création section de test", False, "Impossible de créer la section de test")
    
    # 5. Tests de désaffectation des utilisateurs
    print("\n📋 CATÉGORIE 3: TESTS DÉSAFFECTATION UTILISATEURS")
    print("-" * 40)
    
    # Créer une nouvelle section avec des utilisateurs
    test_section_2 = create_test_section(admin_token, "Section avec utilisateurs")
    
    if test_section_2:
        section_id_2 = test_section_2["id"]
        results.add_result("Création section avec utilisateurs", True, f"Section: {test_section_2['nom']}")
        
        # Créer des utilisateurs dans cette section
        test_users = []
        for i in range(2):
            user = create_test_user(admin_token, section_id_2)
            if user:
                test_users.append(user)
        
        results.add_result(
            "Création utilisateurs de test",
            len(test_users) > 0,
            f"{len(test_users)} utilisateurs créés"
        )
        
        if test_users:
            # Vérifier que les utilisateurs sont bien affectés à la section
            users_in_section = get_users_by_section(admin_token, section_id_2)
            results.add_result(
                "Utilisateurs affectés à la section",
                len(users_in_section) >= len(test_users),
                f"{len(users_in_section)} utilisateurs trouvés dans la section"
            )
            
            # Supprimer la section
            response = requests.delete(f"{BASE_URL}/sections/{section_id_2}", headers=admin_headers)
            results.add_result(
                "Suppression section avec utilisateurs",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                # Vérifier que les utilisateurs ne sont plus affectés à la section
                users_after_deletion = get_users_by_section(admin_token, section_id_2)
                results.add_result(
                    "Utilisateurs désaffectés",
                    len(users_after_deletion) == 0,
                    f"{len(users_after_deletion)} utilisateurs encore affectés"
                )
                
                # Vérifier que les utilisateurs existent toujours mais sans section
                all_users_response = requests.get(f"{BASE_URL}/users", headers=admin_headers)
                if all_users_response.status_code == 200:
                    all_users = all_users_response.json()
                    users_without_section = [
                        user for user in all_users 
                        if any(user["nom"] == test_user["nom"] for test_user in test_users)
                        and user.get("section_id") is None
                    ]
                    results.add_result(
                        "Utilisateurs conservés sans section",
                        len(users_without_section) >= len(test_users),
                        f"{len(users_without_section)} utilisateurs trouvés sans section"
                    )
    else:
        results.add_result("Création section avec utilisateurs", False, "Impossible de créer la section")
    
    # 6. Tests des cas d'erreur
    print("\n📋 CATÉGORIE 4: TESTS CAS D'ERREUR")
    print("-" * 40)
    
    # Tenter de supprimer une section inexistante
    fake_id = str(uuid.uuid4())
    response = requests.delete(f"{BASE_URL}/sections/{fake_id}", headers=admin_headers)
    results.add_result(
        "Suppression section inexistante (404)",
        response.status_code == 404,
        f"Status: {response.status_code}"
    )
    
    # Test avec ID invalide
    response = requests.delete(f"{BASE_URL}/sections/invalid-id", headers=admin_headers)
    results.add_result(
        "Suppression avec ID invalide",
        response.status_code in [404, 422],  # 404 ou 422 selon l'implémentation
        f"Status: {response.status_code}"
    )
    
    results.print_summary()
    return results

if __name__ == "__main__":
    print("🧪 TESTS ENDPOINT DELETE /api/sections/{id}")
    print("Testeur: Agent de test backend")
    print(f"URL de base: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = test_delete_section_endpoint()
    
    # Code de sortie basé sur les résultats
    if results.failed_tests == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results.failed_tests} TEST(S) ONT ÉCHOUÉ")
        sys.exit(1)