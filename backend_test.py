#!/usr/bin/env python3
"""
Tests complets pour le système de sous-groupes nouvellement implémenté
Test du système de gestion d'escadron de cadets - Focus sur les sous-groupes
"""

import requests
import json
from datetime import datetime, date
import uuid

# Configuration
BASE_URL = "https://squadron-app.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class SubgroupSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_data = {
            'sections': [],
            'subgroups': [],
            'users': []
        }
        
    def authenticate_admin(self):
        """Authentification avec le compte administrateur"""
        print("🔐 Authentification administrateur...")
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            print(f"✅ Authentification réussie - Token obtenu")
            return True
        else:
            print(f"❌ Échec authentification: {response.status_code} - {response.text}")
            return False
    
    def test_subgroup_crud_endpoints(self):
        """Test des endpoints CRUD pour les sous-groupes"""
        print("\n📋 === TEST ENDPOINTS CRUD SOUS-GROUPES ===")
        
        results = {
            'get_subgroups': False,
            'create_subgroup': False,
            'update_subgroup': False,
            'delete_subgroup': False
        }
        
        try:
            # 1. Créer une section de test
            print("\n1️⃣ Création section de test...")
            section_data = {
                "nom": f"Section Test Sous-groupes {datetime.now().strftime('%H%M%S')}",
                "description": "Section créée pour tester les sous-groupes"
            }
            
            response = self.session.post(f"{BASE_URL}/sections", json=section_data)
            if response.status_code == 200:
                section = response.json()
                self.test_data['sections'].append(section['id'])
                print(f"✅ Section créée: {section['id']}")
            else:
                print(f"❌ Erreur création section: {response.status_code} - {response.text}")
                return results
            
            section_id = section['id']
            
            # 2. Test GET /api/sections/{section_id}/subgroups (vide initialement)
            print("\n2️⃣ Test GET sous-groupes (section vide)...")
            response = self.session.get(f"{BASE_URL}/sections/{section_id}/subgroups")
            if response.status_code == 200:
                subgroups = response.json()
                if isinstance(subgroups, list) and len(subgroups) == 0:
                    print("✅ GET sous-groupes fonctionne (liste vide)")
                    results['get_subgroups'] = True
                else:
                    print(f"⚠️ Réponse inattendue: {subgroups}")
            else:
                print(f"❌ Erreur GET sous-groupes: {response.status_code} - {response.text}")
            
            # 3. Test POST /api/subgroups - Création sous-groupe
            print("\n3️⃣ Test POST création sous-groupe...")
            subgroup_data = {
                "nom": f"Sous-groupe Alpha {datetime.now().strftime('%H%M%S')}",
                "description": "Premier sous-groupe de test",
                "section_id": section_id
            }
            
            response = self.session.post(f"{BASE_URL}/subgroups", json=subgroup_data)
            if response.status_code == 200:
                subgroup = response.json()
                self.test_data['subgroups'].append(subgroup['id'])
                print(f"✅ Sous-groupe créé: {subgroup['id']}")
                print(f"   Nom: {subgroup['nom']}")
                print(f"   Section: {subgroup['section_id']}")
                results['create_subgroup'] = True
                subgroup_id = subgroup['id']
            else:
                print(f"❌ Erreur création sous-groupe: {response.status_code} - {response.text}")
                return results
            
            # 4. Vérifier GET après création
            print("\n4️⃣ Vérification GET après création...")
            response = self.session.get(f"{BASE_URL}/sections/{section_id}/subgroups")
            if response.status_code == 200:
                subgroups = response.json()
                if len(subgroups) == 1 and subgroups[0]['id'] == subgroup_id:
                    print("✅ GET sous-groupes retourne le sous-groupe créé")
                else:
                    print(f"⚠️ Sous-groupe non trouvé dans la liste: {subgroups}")
            
            # 5. Test PUT /api/subgroups/{subgroup_id} - Mise à jour
            print("\n5️⃣ Test PUT mise à jour sous-groupe...")
            update_data = {
                "nom": f"Sous-groupe Alpha Modifié {datetime.now().strftime('%H%M%S')}",
                "description": "Description mise à jour"
            }
            
            response = self.session.put(f"{BASE_URL}/subgroups/{subgroup_id}", json=update_data)
            if response.status_code == 200:
                print("✅ Mise à jour sous-groupe réussie")
                results['update_subgroup'] = True
                
                # Vérifier la mise à jour
                response = self.session.get(f"{BASE_URL}/sections/{section_id}/subgroups")
                if response.status_code == 200:
                    subgroups = response.json()
                    updated_subgroup = next((sg for sg in subgroups if sg['id'] == subgroup_id), None)
                    if updated_subgroup and updated_subgroup['nom'] == update_data['nom']:
                        print("✅ Vérification mise à jour: nom correctement modifié")
                    else:
                        print("⚠️ Mise à jour non reflétée dans GET")
            else:
                print(f"❌ Erreur mise à jour sous-groupe: {response.status_code} - {response.text}")
            
            # 6. Test DELETE /api/subgroups/{subgroup_id} - Suppression
            print("\n6️⃣ Test DELETE suppression sous-groupe...")
            response = self.session.delete(f"{BASE_URL}/subgroups/{subgroup_id}")
            if response.status_code == 200:
                print("✅ Suppression sous-groupe réussie")
                results['delete_subgroup'] = True
                
                # Vérifier la suppression
                response = self.session.get(f"{BASE_URL}/sections/{section_id}/subgroups")
                if response.status_code == 200:
                    subgroups = response.json()
                    if len(subgroups) == 0:
                        print("✅ Vérification suppression: liste vide")
                    else:
                        print(f"⚠️ Sous-groupe encore présent après suppression: {subgroups}")
                
                # Retirer de nos données de test
                if subgroup_id in self.test_data['subgroups']:
                    self.test_data['subgroups'].remove(subgroup_id)
            else:
                print(f"❌ Erreur suppression sous-groupe: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception dans test CRUD: {str(e)}")
        
        return results
    
    def test_user_subgroup_integration(self):
        """Test de l'intégration utilisateur-sous-groupe"""
        print("\n👥 === TEST INTÉGRATION UTILISATEUR-SOUS-GROUPE ===")
        
        results = {
            'user_creation_with_subgroup': False,
            'user_update_subgroup': False,
            'subgroup_section_validation': False
        }
        
        try:
            # 1. Créer section et sous-groupe pour les tests
            print("\n1️⃣ Préparation: création section et sous-groupe...")
            
            # Créer section
            section_data = {
                "nom": f"Section Intégration {datetime.now().strftime('%H%M%S')}",
                "description": "Section pour test intégration utilisateur-sous-groupe"
            }
            response = self.session.post(f"{BASE_URL}/sections", json=section_data)
            if response.status_code != 200:
                print(f"❌ Erreur création section: {response.text}")
                return results
            
            section = response.json()
            section_id = section['id']
            self.test_data['sections'].append(section_id)
            
            # Créer sous-groupe
            subgroup_data = {
                "nom": f"Sous-groupe Beta {datetime.now().strftime('%H%M%S')}",
                "description": "Sous-groupe pour test intégration",
                "section_id": section_id
            }
            response = self.session.post(f"{BASE_URL}/subgroups", json=subgroup_data)
            if response.status_code != 200:
                print(f"❌ Erreur création sous-groupe: {response.text}")
                return results
            
            subgroup = response.json()
            subgroup_id = subgroup['id']
            self.test_data['subgroups'].append(subgroup_id)
            print(f"✅ Section {section_id} et sous-groupe {subgroup_id} créés")
            
            # 2. Test création utilisateur avec sous-groupe
            print("\n2️⃣ Test création utilisateur avec sous-groupe...")
            user_data = {
                "nom": "TestSubgroup",
                "prenom": f"Cadet{datetime.now().strftime('%H%M%S')}",
                "email": f"cadet.subgroup.{datetime.now().strftime('%H%M%S')}@test.fr",
                "grade": "cadet",
                "role": "cadet",
                "section_id": section_id,
                "subgroup_id": subgroup_id,
                "has_admin_privileges": False
            }
            
            response = self.session.post(f"{BASE_URL}/users", json=user_data)
            if response.status_code == 200:
                user_result = response.json()
                user_id = user_result['user_id']
                self.test_data['users'].append(user_id)
                print(f"✅ Utilisateur créé avec sous-groupe: {user_id}")
                results['user_creation_with_subgroup'] = True
                
                # Vérifier que l'utilisateur a bien le sous-groupe
                response = self.session.get(f"{BASE_URL}/users/{user_id}")
                if response.status_code == 200:
                    user = response.json()
                    if user.get('subgroup_id') == subgroup_id:
                        print("✅ Vérification: utilisateur a le bon sous-groupe")
                    else:
                        print(f"⚠️ Sous-groupe incorrect: attendu {subgroup_id}, reçu {user.get('subgroup_id')}")
            else:
                print(f"❌ Erreur création utilisateur: {response.status_code} - {response.text}")
            
            # 3. Test mise à jour sous-groupe utilisateur
            print("\n3️⃣ Test mise à jour sous-groupe utilisateur...")
            
            # Créer un deuxième sous-groupe
            subgroup2_data = {
                "nom": f"Sous-groupe Gamma {datetime.now().strftime('%H%M%S')}",
                "description": "Deuxième sous-groupe pour test",
                "section_id": section_id
            }
            response = self.session.post(f"{BASE_URL}/subgroups", json=subgroup2_data)
            if response.status_code == 200:
                subgroup2 = response.json()
                subgroup2_id = subgroup2['id']
                self.test_data['subgroups'].append(subgroup2_id)
                
                # Mettre à jour l'utilisateur
                update_data = {"subgroup_id": subgroup2_id}
                response = self.session.put(f"{BASE_URL}/users/{user_id}", json=update_data)
                if response.status_code == 200:
                    print("✅ Mise à jour sous-groupe utilisateur réussie")
                    results['user_update_subgroup'] = True
                    
                    # Vérifier la mise à jour
                    response = self.session.get(f"{BASE_URL}/users/{user_id}")
                    if response.status_code == 200:
                        user = response.json()
                        if user.get('subgroup_id') == subgroup2_id:
                            print("✅ Vérification: sous-groupe utilisateur mis à jour")
                        else:
                            print(f"⚠️ Mise à jour non reflétée: {user.get('subgroup_id')}")
                else:
                    print(f"❌ Erreur mise à jour utilisateur: {response.text}")
            
            # 4. Test validation section-sous-groupe
            print("\n4️⃣ Test validation cohérence section-sous-groupe...")
            
            # Créer une autre section
            other_section_data = {
                "nom": f"Autre Section {datetime.now().strftime('%H%M%S')}",
                "description": "Section pour test validation"
            }
            response = self.session.post(f"{BASE_URL}/sections", json=other_section_data)
            if response.status_code == 200:
                other_section = response.json()
                other_section_id = other_section['id']
                self.test_data['sections'].append(other_section_id)
                
                # Essayer d'assigner un utilisateur à un sous-groupe d'une autre section
                invalid_update = {
                    "section_id": other_section_id,
                    "subgroup_id": subgroup_id  # Sous-groupe de la première section
                }
                
                response = self.session.put(f"{BASE_URL}/users/{user_id}", json=invalid_update)
                if response.status_code == 400:
                    print("✅ Validation section-sous-groupe: erreur 400 attendue")
                    results['subgroup_section_validation'] = True
                elif response.status_code != 200:
                    print(f"✅ Validation section-sous-groupe: erreur {response.status_code} (validation active)")
                    results['subgroup_section_validation'] = True
                else:
                    print("⚠️ Validation section-sous-groupe: aucune erreur (validation manquante?)")
                    
        except Exception as e:
            print(f"❌ Exception dans test intégration: {str(e)}")
        
        return results
    
    def test_error_scenarios(self):
        """Test des scénarios d'erreur"""
        print("\n🚨 === TEST SCÉNARIOS D'ERREUR ===")
        
        results = {
            'nonexistent_section_subgroup_creation': False,
            'nonexistent_subgroup_user_assignment': False,
            'duplicate_subgroup_name': False
        }
        
        try:
            # 1. Test création sous-groupe avec section inexistante
            print("\n1️⃣ Test création sous-groupe avec section inexistante...")
            fake_section_id = str(uuid.uuid4())
            
            subgroup_data = {
                "nom": "Sous-groupe Erreur",
                "description": "Test avec section inexistante",
                "section_id": fake_section_id
            }
            
            response = self.session.post(f"{BASE_URL}/subgroups", json=subgroup_data)
            if response.status_code == 404:
                print("✅ Erreur 404 pour section inexistante")
                results['nonexistent_section_subgroup_creation'] = True
            elif response.status_code != 200:
                print(f"✅ Erreur {response.status_code} pour section inexistante (validation active)")
                results['nonexistent_section_subgroup_creation'] = True
            else:
                print("⚠️ Aucune erreur pour section inexistante (validation manquante)")
            
            # 2. Test assignation utilisateur à sous-groupe inexistant
            print("\n2️⃣ Test assignation utilisateur à sous-groupe inexistant...")
            
            # D'abord créer un utilisateur valide
            section_data = {
                "nom": f"Section Erreur {datetime.now().strftime('%H%M%S')}",
                "description": "Section pour test erreur"
            }
            response = self.session.post(f"{BASE_URL}/sections", json=section_data)
            if response.status_code == 200:
                section = response.json()
                section_id = section['id']
                self.test_data['sections'].append(section_id)
                
                user_data = {
                    "nom": "TestErreur",
                    "prenom": f"Cadet{datetime.now().strftime('%H%M%S')}",
                    "grade": "cadet",
                    "role": "cadet",
                    "section_id": section_id
                }
                
                response = self.session.post(f"{BASE_URL}/users", json=user_data)
                if response.status_code == 200:
                    user_result = response.json()
                    user_id = user_result['user_id']
                    self.test_data['users'].append(user_id)
                    
                    # Essayer d'assigner un sous-groupe inexistant
                    fake_subgroup_id = str(uuid.uuid4())
                    update_data = {"subgroup_id": fake_subgroup_id}
                    
                    response = self.session.put(f"{BASE_URL}/users/{user_id}", json=update_data)
                    if response.status_code == 404:
                        print("✅ Erreur 404 pour sous-groupe inexistant")
                        results['nonexistent_subgroup_user_assignment'] = True
                    elif response.status_code != 200:
                        print(f"✅ Erreur {response.status_code} pour sous-groupe inexistant (validation active)")
                        results['nonexistent_subgroup_user_assignment'] = True
                    else:
                        print("⚠️ Aucune erreur pour sous-groupe inexistant (validation manquante)")
            
            # 3. Test nom de sous-groupe dupliqué dans même section
            print("\n3️⃣ Test nom de sous-groupe dupliqué...")
            
            if section_id:
                # Créer premier sous-groupe
                subgroup_data = {
                    "nom": f"Sous-groupe Unique {datetime.now().strftime('%H%M%S')}",
                    "description": "Premier sous-groupe",
                    "section_id": section_id
                }
                
                response = self.session.post(f"{BASE_URL}/subgroups", json=subgroup_data)
                if response.status_code == 200:
                    subgroup = response.json()
                    self.test_data['subgroups'].append(subgroup['id'])
                    
                    # Essayer de créer un deuxième avec le même nom
                    duplicate_data = {
                        "nom": subgroup_data["nom"],  # Même nom
                        "description": "Tentative de duplication",
                        "section_id": section_id
                    }
                    
                    response = self.session.post(f"{BASE_URL}/subgroups", json=duplicate_data)
                    if response.status_code == 400:
                        print("✅ Erreur 400 pour nom dupliqué")
                        results['duplicate_subgroup_name'] = True
                    elif response.status_code != 200:
                        print(f"✅ Erreur {response.status_code} pour nom dupliqué (validation active)")
                        results['duplicate_subgroup_name'] = True
                    else:
                        print("⚠️ Aucune erreur pour nom dupliqué (validation manquante)")
                        # Si créé par erreur, l'ajouter pour nettoyage
                        if response.json().get('id'):
                            self.test_data['subgroups'].append(response.json()['id'])
                            
        except Exception as e:
            print(f"❌ Exception dans test erreurs: {str(e)}")
        
        return results
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        print("\n🧹 === NETTOYAGE DONNÉES DE TEST ===")
        
        # Supprimer les utilisateurs
        for user_id in self.test_data['users']:
            try:
                response = self.session.delete(f"{BASE_URL}/users/{user_id}")
                if response.status_code == 200:
                    print(f"✅ Utilisateur {user_id} supprimé")
                else:
                    print(f"⚠️ Erreur suppression utilisateur {user_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception suppression utilisateur {user_id}: {str(e)}")
        
        # Supprimer les sous-groupes
        for subgroup_id in self.test_data['subgroups']:
            try:
                response = self.session.delete(f"{BASE_URL}/subgroups/{subgroup_id}")
                if response.status_code == 200:
                    print(f"✅ Sous-groupe {subgroup_id} supprimé")
                else:
                    print(f"⚠️ Erreur suppression sous-groupe {subgroup_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception suppression sous-groupe {subgroup_id}: {str(e)}")
        
        # Supprimer les sections
        for section_id in self.test_data['sections']:
            try:
                response = self.session.delete(f"{BASE_URL}/sections/{section_id}")
                if response.status_code == 200:
                    print(f"✅ Section {section_id} supprimée")
                else:
                    print(f"⚠️ Erreur suppression section {section_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception suppression section {section_id}: {str(e)}")
        
        print("🧹 Nettoyage terminé")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 === DÉBUT TESTS SYSTÈME SOUS-GROUPES ===")
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"👤 Authentification: {ADMIN_USERNAME}")
        
        # Authentification
        if not self.authenticate_admin():
            print("❌ Échec authentification - Arrêt des tests")
            return
        
        all_results = {}
        
        try:
            # Test 1: CRUD endpoints
            print("\n" + "="*60)
            crud_results = self.test_subgroup_crud_endpoints()
            all_results.update(crud_results)
            
            # Test 2: Intégration utilisateur-sous-groupe
            print("\n" + "="*60)
            integration_results = self.test_user_subgroup_integration()
            all_results.update(integration_results)
            
            # Test 3: Scénarios d'erreur
            print("\n" + "="*60)
            error_results = self.test_error_scenarios()
            all_results.update(error_results)
            
        finally:
            # Nettoyage (toujours exécuté)
            print("\n" + "="*60)
            self.cleanup_test_data()
        
        # Résumé final
        print("\n" + "="*60)
        print("📊 === RÉSUMÉ FINAL ===")
        
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results.values() if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        print("\n📋 Détail des résultats:")
        for test_name, result in all_results.items():
            status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
            print(f"  {status} - {test_name}")
        
        if success_rate >= 80:
            print(f"\n🎉 SYSTÈME SOUS-GROUPES FONCTIONNEL ({success_rate:.1f}% réussite)")
        else:
            print(f"\n⚠️ PROBLÈMES DÉTECTÉS DANS LE SYSTÈME SOUS-GROUPES ({success_rate:.1f}% réussite)")
        
        return all_results

if __name__ == "__main__":
    tester = SubgroupSystemTester()
    results = tester.run_all_tests()