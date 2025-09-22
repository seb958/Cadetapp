import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  grade: string;
  role: string;
  section_id?: string;
  photo_base64?: string;
  actif: boolean;
  created_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export default function Index() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  // États pour la connexion
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Vérifier si l'utilisateur est déjà connecté
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (token && userData) {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Erreur lors de la vérification du statut d\'authentification:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async () => {
    if (!email || !password) {
      Alert.alert('Erreur', 'Veuillez saisir votre email et mot de passe');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
          password,
        }),
      });

      if (response.ok) {
        const data: AuthResponse = await response.json();
        
        // Sauvegarder les données d'authentification
        await AsyncStorage.setItem('access_token', data.access_token);
        await AsyncStorage.setItem('user_data', JSON.stringify(data.user));
        
        setUser(data.user);
        setIsAuthenticated(true);
        setEmail('');
        setPassword('');
        
        Alert.alert('Succès', `Bienvenue ${data.user.prenom} ${data.user.nom}!`);
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur de connexion', errorData.detail || 'Email ou mot de passe incorrect');
      }
    } catch (error) {
      console.error('Erreur de connexion:', error);
      Alert.alert('Erreur', 'Impossible de se connecter au serveur');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('user_data');
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    }
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'cadet': return 'Cadet';
      case 'cadet_responsible': return 'Cadet Responsable';
      case 'cadet_admin': return 'Cadet Administrateur';
      case 'encadrement': return 'Encadrement';
      default: return role;
    }
  };

  const getGradeDisplayName = (grade: string) => {
    const grades: { [key: string]: string } = {
      'cadet': 'Cadet',
      'caporal': 'Caporal',
      'sergent': 'Sergent',
      'adjudant': 'Adjudant',
      'lieutenant': 'Lieutenant',
      'capitaine': 'Capitaine',
      'commandant': 'Commandant'
    };
    return grades[grade] || grade;
  };

  // Navigation vers les fonctionnalités
  const navigateToPresences = () => {
    router.push('/presences');
  };

  const navigateToInspections = () => {
    // TODO: Implémenter plus tard
    Alert.alert('Bientôt disponible', 'Fonctionnalité en cours de développement');
  };

  const navigateToReports = () => {
    // TODO: Implémenter plus tard
    Alert.alert('Bientôt disponible', 'Fonctionnalité en cours de développement');
  };

  const navigateToCommunication = () => {
    // TODO: Implémenter plus tard
    Alert.alert('Bientôt disponible', 'Fonctionnalité en cours de développement');
  };

  const navigateToAdmin = () => {
    router.push('/admin');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.loadingText}>Chargement...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardContainer}
        >
          <ScrollView contentContainerStyle={styles.scrollContainer}>
            <View style={styles.loginContainer}>
              <Text style={styles.title}>Gestion Escadron Cadets</Text>
              <Text style={styles.subtitle}>Connexion</Text>

              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Email</Text>
                <TextInput
                  style={styles.input}
                  placeholder="votre.email@exemple.com"
                  placeholderTextColor="#999"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Mot de passe</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Votre mot de passe"
                  placeholderTextColor="#999"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                />
              </View>

              <TouchableOpacity
                style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
                onPress={login}
                disabled={isLoading}
              >
                <Text style={styles.loginButtonText}>
                  {isLoading ? 'Connexion...' : 'Se connecter'}
                </Text>
              </TouchableOpacity>

              <View style={styles.infoContainer}>
                <Text style={styles.infoText}>
                  Pour obtenir un compte, contactez votre administrateur.
                </Text>
              </View>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.dashboardContainer}>
        <View style={styles.header}>
          <Text style={styles.welcomeText}>
            Bienvenue, {user?.prenom} {user?.nom}
          </Text>
          <TouchableOpacity style={styles.logoutButton} onPress={logout}>
            <Text style={styles.logoutButtonText}>Déconnexion</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.profileCard}>
          <Text style={styles.cardTitle}>Mon Profil</Text>
          <View style={styles.profileInfo}>
            <Text style={styles.profileItem}>
              <Text style={styles.profileLabel}>Grade: </Text>
              {getGradeDisplayName(user?.grade || '')}
            </Text>
            <Text style={styles.profileItem}>
              <Text style={styles.profileLabel}>Rôle: </Text>
              {getRoleDisplayName(user?.role || '')}
            </Text>
            <Text style={styles.profileItem}>
              <Text style={styles.profileLabel}>Email: </Text>
              {user?.email}
            </Text>
          </View>
        </View>

        <View style={styles.featuresContainer}>
          <Text style={styles.sectionTitle}>Fonctionnalités</Text>
          
          {/* Présences */}
          <TouchableOpacity style={styles.featureCard} onPress={navigateToPresences}>
            <Text style={styles.featureTitle}>📊 Gestion des Présences</Text>
            <Text style={styles.featureDescription}>
              Enregistrer et consulter les présences
            </Text>
          </TouchableOpacity>

          {/* Inspections */}
          <TouchableOpacity style={styles.featureCard} onPress={navigateToInspections}>
            <Text style={styles.featureTitle}>👕 Inspection d'Uniformes</Text>
            <Text style={styles.featureDescription}>
              Effectuer et consulter les inspections
            </Text>
          </TouchableOpacity>

          {/* Rapports */}
          <TouchableOpacity style={styles.featureCard} onPress={navigateToReports}>
            <Text style={styles.featureTitle}>📈 Rapports</Text>
            <Text style={styles.featureDescription}>
              Générer et exporter des rapports
            </Text>
          </TouchableOpacity>

          {/* Communication */}
          <TouchableOpacity style={styles.featureCard} onPress={navigateToCommunication}>
            <Text style={styles.featureTitle}>💬 Communication</Text>
            <Text style={styles.featureDescription}>
              Fil d'actualité et messagerie
            </Text>
          </TouchableOpacity>

          {/* Administration - uniquement pour admin/encadrement */}
          {(user?.role === 'cadet_admin' || user?.role === 'encadrement') && (
            <TouchableOpacity style={[styles.featureCard, styles.adminCard]} onPress={navigateToAdmin}>
              <Text style={styles.featureTitle}>⚙️ Administration</Text>
              <Text style={styles.featureDescription}>
                Gestion des utilisateurs et paramètres
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#666',
  },
  loginContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 30,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
    color: '#1a365d',
  },
  subtitle: {
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 30,
    color: '#4a5568',
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    backgroundColor: '#f7fafc',
  },
  loginButton: {
    backgroundColor: '#3182ce',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  loginButtonDisabled: {
    backgroundColor: '#a0aec0',
  },
  loginButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  infoContainer: {
    marginTop: 20,
    padding: 15,
    backgroundColor: '#ebf8ff',
    borderRadius: 8,
  },
  infoText: {
    textAlign: 'center',
    color: '#2c5282',
    fontSize: 14,
  },
  dashboardContainer: {
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  welcomeText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
    flex: 1,
  },
  logoutButton: {
    backgroundColor: '#e53e3e',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 6,
  },
  logoutButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  profileCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 15,
  },
  profileInfo: {
    gap: 10,
  },
  profileItem: {
    fontSize: 16,
    color: '#4a5568',
  },
  profileLabel: {
    fontWeight: '600',
    color: '#2d3748',
  },
  featuresContainer: {
    gap: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 10,
  },
  featureCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  adminCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#38a169',
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 5,
  },
  featureDescription: {
    fontSize: 14,
    color: '#4a5568',
  },
});