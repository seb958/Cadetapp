#!/usr/bin/env python3
"""
Tests Backend - Permissions Inspection + Anti-Auto-Évaluation
Test des nouvelles permissions d'inspection et validation anti-auto-évaluation
"""

import requests
import json
from datetime import date, datetime
import sys

# Configuration
BASE_URL = "https://squadcommand.preview.emergentagent.com/api"
ADMIN_USERNAME = "aadministrateur"
ADMIN_PASSWORD = "admin123"

class TestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.users_cache = {}
        
    def log_test(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate_admin(self):
        """Authentification admin"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_test("Authentification Admin", True, f"Token obtenu pour {ADMIN_USERNAME}")
                return True
            else:
                self.log_test("Authentification Admin", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentification Admin", False, f"Exception: {str(e)}")
            return False
    
    def test_users_api(self):
        """Test GET /api/users endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            
            if response.status_code == 200:
                users = response.json()
                user_count = len(users)
                
                # Check if we have users
                if user_count > 0:
                    # Sample some user data for validation
                    sample_user = users[0]
                    required_fields = ['id', 'nom', 'prenom', 'role', 'grade', 'actif']
                    missing_fields = [field for field in required_fields if field not in sample_user]
                    
                    if not missing_fields:
                        self.log_test(
                            "Users API - GET /api/users", 
                            True, 
                            f"Retrieved {user_count} users successfully. Sample user has all required fields."
                        )
                    else:
                        self.log_test(
                            "Users API - GET /api/users", 
                            False, 
                            f"Retrieved {user_count} users but missing fields: {missing_fields}"
                        )
                else:
                    self.log_test("Users API - GET /api/users", False, "No users found in response")
                    
            else:
                self.log_test("Users API - GET /api/users", False, f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Users API - GET /api/users", False, f"Request error: {str(e)}")
    
    def test_sections_api(self):
        """Test GET /api/sections endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/sections")
            
            if response.status_code == 200:
                sections = response.json()
                section_count = len(sections)
                
                # Check if we have sections
                if section_count > 0:
                    # Sample some section data for validation
                    sample_section = sections[0]
                    required_fields = ['id', 'nom', 'created_at']
                    missing_fields = [field for field in required_fields if field not in sample_section]
                    
                    if not missing_fields:
                        self.log_test(
                            "Sections API - GET /api/sections", 
                            True, 
                            f"Retrieved {section_count} sections successfully. Sample section has all required fields."
                        )
                    else:
                        self.log_test(
                            "Sections API - GET /api/sections", 
                            False, 
                            f"Retrieved {section_count} sections but missing fields: {missing_fields}"
                        )
                else:
                    self.log_test("Sections API - GET /api/sections", False, "No sections found in response")
                    
            else:
                self.log_test("Sections API - GET /api/sections", False, f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Sections API - GET /api/sections", False, f"Request error: {str(e)}")
    
    def test_presences_get_api(self):
        """Test GET /api/presences endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/presences")
            
            if response.status_code == 200:
                presences = response.json()
                presence_count = len(presences)
                
                # Check if we have presences
                if presence_count >= 0:  # 0 is acceptable for presences
                    if presence_count > 0:
                        # Sample some presence data for validation
                        sample_presence = presences[0]
                        required_fields = ['id', 'cadet_id', 'cadet_nom', 'cadet_prenom', 'date', 'status']
                        missing_fields = [field for field in required_fields if field not in sample_presence]
                        
                        if not missing_fields:
                            self.log_test(
                                "Presences API - GET /api/presences", 
                                True, 
                                f"Retrieved {presence_count} presences successfully. Sample presence has all required fields."
                            )
                        else:
                            self.log_test(
                                "Presences API - GET /api/presences", 
                                False, 
                                f"Retrieved {presence_count} presences but missing fields: {missing_fields}"
                            )
                    else:
                        self.log_test(
                            "Presences API - GET /api/presences", 
                            True, 
                            f"Retrieved {presence_count} presences successfully (empty list is acceptable)."
                        )
                        
            else:
                self.log_test("Presences API - GET /api/presences", False, f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Presences API - GET /api/presences", False, f"Request error: {str(e)}")
    
    def test_presences_post_api(self):
        """Test POST /api/presences endpoint"""
        try:
            # First get a user to create presence for
            users_response = self.session.get(f"{BASE_URL}/users")
            if users_response.status_code != 200:
                self.log_test("Presences API - POST /api/presences", False, "Cannot get users for presence test")
                return
                
            users = users_response.json()
            if not users:
                self.log_test("Presences API - POST /api/presences", False, "No users available for presence test")
                return
                
            # Use first active user
            test_user = None
            for user in users:
                if user.get('actif', False):
                    test_user = user
                    break
                    
            if not test_user:
                self.log_test("Presences API - POST /api/presences", False, "No active users available for presence test")
                return
            
            # Create test presence data
            today = date.today().isoformat()
            presence_data = {
                "cadet_id": test_user['id'],
                "status": "present",
                "commentaire": "Test presence for regression testing"
            }
            
            response = self.session.post(
                f"{BASE_URL}/presences?presence_date={today}&activite=Test Regression", 
                json=presence_data
            )
            
            if response.status_code == 200:
                presence = response.json()
                required_fields = ['id', 'cadet_id', 'date', 'status']
                missing_fields = [field for field in required_fields if field not in presence]
                
                if not missing_fields:
                    self.log_test(
                        "Presences API - POST /api/presences", 
                        True, 
                        f"Created presence successfully for user {test_user['prenom']} {test_user['nom']}"
                    )
                else:
                    self.log_test(
                        "Presences API - POST /api/presences", 
                        False, 
                        f"Created presence but missing fields: {missing_fields}"
                    )
            elif response.status_code == 400 and "existe déjà" in response.text:
                # Presence already exists for today - this is acceptable
                self.log_test(
                    "Presences API - POST /api/presences", 
                    True, 
                    f"Presence already exists for user {test_user['prenom']} {test_user['nom']} today (acceptable)"
                )
            else:
                self.log_test("Presences API - POST /api/presences", False, f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Presences API - POST /api/presences", False, f"Request error: {str(e)}")
    
    def run_all_tests(self):
        """Run all regression tests"""
        print("🧪 Starting Backend Regression Tests")
        print("=" * 60)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with other tests")
            return False
            
        # Run core API tests
        self.test_users_api()
        self.test_sections_api()
        self.test_presences_get_api()
        self.test_presences_post_api()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests < self.total_tests:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result:
                    print(f"  - {result}")
        
        return self.passed_tests == self.total_tests

if __name__ == "__main__":
    tester = BackendRegressionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All regression tests passed! Backend functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)