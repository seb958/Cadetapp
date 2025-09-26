#!/usr/bin/env python3
"""
Test de création d'utilisateur avec rôle personnalisé
Test spécifique pour vérifier la création d'utilisateurs avec des rôles personnalisés
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://squadron-app.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class CustomRoleUserTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.created_user_ids = []  # Pour nettoyer après les tests
        
    def authenticate(self):
        """Authentification avec les credentials admin"""
        print("🔐 Authentification en cours...")
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"✅ Authentification réussie pour {data['user']['prenom']} {data['user']['nom']}")
            return True
        else:
            print(f"❌ Échec authentification: {response.status_code} - {response.text}")
            return False
    
    def create_user_with_custom_role(self, nom, prenom, grade, role, email=None):
        """Créer un utilisateur avec un rôle personnalisé"""
        print(f"\n👤 Création utilisateur: {prenom} {nom} - Rôle: {role} - Grade: {grade}")
        
        # Générer un email unique si non fourni
        if not email:
            unique_id = str(uuid.uuid4())[:8]
            email = f"{prenom.lower()}.{nom.lower()}.{unique_id}@test-escadron.fr"
        
        user_data = {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "grade": grade,
            "role": role,
            "section_id": None,
            "subgroup_id": None,
            "has_admin_privileges": False
        }
        
        response = self.session.post(f"{BASE_URL}/users", json=user_data)
        
        if response.status_code == 200:
            result = response.json()
            user_id = result["user_id"]
            username = result["username"]
            self.created_user_ids.append(user_id)
            print(f"✅ Utilisateur créé avec succès:")
            print(f"   - ID: {user_id}")
            print(f"   - Username: {username}")
            print(f"   - Email: {email}")
            return user_id, username
        else:
            print(f"❌ Échec création utilisateur: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None, None
    
    def get_users_list(self):
        """Récupérer la liste des utilisateurs"""
        print(f"\n📋 Récupération de la liste des utilisateurs...")
        
        response = self.session.get(f"{BASE_URL}/users")
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Liste récupérée: {len(users)} utilisateurs trouvés")
            return users
        else:
            print(f"❌ Échec récupération liste: {response.status_code} - {response.text}")
            return []
    
    def verify_user_in_list(self, user_id, expected_role, expected_grade):
        """Vérifier qu'un utilisateur apparaît dans la liste avec le bon rôle et grade"""
        print(f"\n🔍 Vérification utilisateur {user_id} dans la liste...")
        
        users = self.get_users_list()
        
        for user in users:
            if user["id"] == user_id:
                print(f"✅ Utilisateur trouvé:")
                print(f"   - Nom: {user['prenom']} {user['nom']}")
                print(f"   - Rôle: {user['role']}")
                print(f"   - Grade: {user['grade']}")
                
                # Vérifications
                role_ok = user["role"] == expected_role
                grade_ok = user["grade"] == expected_grade
                
                if role_ok and grade_ok:
                    print(f"✅ Rôle et grade corrects")
                    return True
                else:
                    print(f"❌ Rôle ou grade incorrect:")
                    print(f"   - Rôle attendu: {expected_role}, trouvé: {user['role']}")
                    print(f"   - Grade attendu: {expected_grade}, trouvé: {user['grade']}")
                    return False
        
        print(f"❌ Utilisateur {user_id} non trouvé dans la liste")
        return False
    
    def delete_user(self, user_id):
        """Supprimer un utilisateur de test"""
        print(f"\n🗑️ Suppression utilisateur {user_id}...")
        
        response = self.session.delete(f"{BASE_URL}/users/{user_id}")
        
        if response.status_code == 200:
            print(f"✅ Utilisateur supprimé avec succès")
            return True
        else:
            print(f"❌ Échec suppression: {response.status_code} - {response.text}")
            return False
    
    def cleanup_test_users(self):
        """Nettoyer tous les utilisateurs de test créés"""
        print(f"\n🧹 Nettoyage des utilisateurs de test...")
        
        deleted_count = 0
        for user_id in self.created_user_ids:
            if self.delete_user(user_id):
                deleted_count += 1
        
        print(f"✅ Nettoyage terminé: {deleted_count}/{len(self.created_user_ids)} utilisateurs supprimés")
        self.created_user_ids.clear()
    
    def run_tests(self):
        """Exécuter tous les tests"""
        print("=" * 80)
        print("🧪 TESTS DE CRÉATION D'UTILISATEUR AVEC RÔLE PERSONNALISÉ")
        print("=" * 80)
        
        # Authentification
        if not self.authenticate():
            print("❌ Impossible de continuer sans authentification")
            return False
        
        test_results = []
        
        # Test 1: Création utilisateur avec rôle "Adjudant-Chef d'escadron"
        print("\n" + "=" * 60)
        print("TEST 1: Création utilisateur avec rôle 'Adjudant-Chef d'escadron'")
        print("=" * 60)
        
        user_id_1, username_1 = self.create_user_with_custom_role(
            nom="Dupont",
            prenom="Jean-Pierre",
            grade="adjudant_1re_classe",
            role="Adjudant-Chef d'escadron"
        )
        
        if user_id_1:
            # Vérifier que l'utilisateur apparaît dans la liste
            verification_ok = self.verify_user_in_list(
                user_id_1, 
                "Adjudant-Chef d'escadron", 
                "adjudant_1re_classe"
            )
            test_results.append(("Test 1 - Création + Vérification", verification_ok))
        else:
            test_results.append(("Test 1 - Création", False))
        
        # Test 2: Création utilisateur avec rôle "Adjudant d'escadron"
        print("\n" + "=" * 60)
        print("TEST 2: Création utilisateur avec rôle 'Adjudant d'escadron'")
        print("=" * 60)
        
        user_id_2, username_2 = self.create_user_with_custom_role(
            nom="Martin",
            prenom="Sophie",
            grade="adjudant_1re_classe",
            role="Adjudant d'escadron"
        )
        
        if user_id_2:
            # Vérifier que l'utilisateur apparaît dans la liste
            verification_ok = self.verify_user_in_list(
                user_id_2, 
                "Adjudant d'escadron", 
                "adjudant_1re_classe"
            )
            test_results.append(("Test 2 - Création + Vérification", verification_ok))
        else:
            test_results.append(("Test 2 - Création", False))
        
        # Test 3: Vérification que les deux utilisateurs sont bien dans la liste
        print("\n" + "=" * 60)
        print("TEST 3: Vérification présence des deux utilisateurs")
        print("=" * 60)
        
        users = self.get_users_list()
        custom_role_users = [
            user for user in users 
            if user["role"] in ["Adjudant-Chef d'escadron", "Adjudant d'escadron"]
        ]
        
        print(f"📊 Utilisateurs avec rôles personnalisés trouvés: {len(custom_role_users)}")
        for user in custom_role_users:
            print(f"   - {user['prenom']} {user['nom']} ({user['role']})")
        
        both_found = len(custom_role_users) >= 2
        test_results.append(("Test 3 - Présence des deux utilisateurs", both_found))
        
        # Résumé des tests
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"{status} - {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n🎯 Taux de réussite: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Nettoyage
        self.cleanup_test_users()
        
        return success_rate == 100.0

def main():
    """Fonction principale"""
    tester = CustomRoleUserTest()
    
    try:
        success = tester.run_tests()
        
        if success:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
            print("✅ Le système de création d'utilisateurs avec rôles personnalisés fonctionne correctement")
        else:
            print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
            print("❌ Des problèmes ont été détectés dans le système")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {str(e)}")
        # Essayer de nettoyer même en cas d'erreur
        try:
            tester.cleanup_test_users()
        except:
            pass
        return False
    
    return success

if __name__ == "__main__":
    main()