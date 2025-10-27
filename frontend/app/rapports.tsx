import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Picker } from '@react-native-picker/picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  nom: string;
  prenom: string;
  role: string;
}

interface Section {
  id: string;
  nom: string;
}

export default function Rapports() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'cadets' | 'sheets' | 'stats' | 'individual'>('cadets');
  
  // États pour les sections
  const [sections, setSections] = useState<Section[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  
  // États pour Liste des Cadets
  const [cadetsFilterType, setCadetsFilterType] = useState<'all' | 'section' | 'role'>('all');
  const [selectedSection, setSelectedSection] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [generatingCadetsList, setGeneratingCadetsList] = useState(false);
  
  // États pour Feuilles d'Inspection
  const [uniformTypes, setUniformTypes] = useState<string[]>([]);
  const [selectedUniformType, setSelectedUniformType] = useState('');
  const [sheetSection, setSheetSection] = useState('all');
  const [generatingSheet, setGeneratingSheet] = useState(false);
  
  // États pour Rapports d'Inspections
  const [statsPeriod, setStatsPeriod] = useState<'week' | 'month' | 'quarter' | 'custom'>('month');
  const [statsSection, setStatsSection] = useState('all');
  const [statsFormat, setStatsFormat] = useState<'pdf' | 'excel'>('pdf');
  const [generatingStats, setGeneratingStats] = useState(false);
  
  // États pour Rapport Individuel
  const [selectedCadetId, setSelectedCadetId] = useState('');
  const [generatingIndividual, setGeneratingIndividual] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (token && userData) {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        
        // Vérifier les permissions
        const role = parsedUser.role.toLowerCase();
        const canAccessReports = ['chef', 'sergent', 'adjudant', 'officier', 'commandant', 'responsible', 'admin', 'encadrement'].some(
          keyword => role.includes(keyword)
        ) || parsedUser.has_admin_privileges;
        
        if (!canAccessReports) {
          Alert.alert('Accès refusé', 'Vous n\'avez pas les permissions nécessaires');
          router.back();
          return;
        }
        
        await loadData();
      } else {
        router.push('/');
      }
    } catch (error) {
      console.error('Erreur lors de la vérification:', error);
      router.push('/');
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Charger les sections
      const sectionsResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (sectionsResponse.ok) {
        const sectionsData = await sectionsResponse.json();
        setSections(sectionsData);
      }
      
      // Charger tous les utilisateurs pour le rapport individuel
      const usersResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (usersResponse.ok) {
        const usersData = await usersResponse.json();
        setAllUsers(usersData);
      }
      
      // Charger les types d'uniforme depuis les settings
      const settingsResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/settings`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json();
        const types = Object.keys(settingsData.inspectionCriteria || {});
        setUniformTypes(types);
        if (types.length > 0) {
          setSelectedUniformType(types[0]);
        }
      }
    } catch (error) {
      console.error('Erreur chargement données:', error);
    }
  };

  const downloadFile = async (url: string, filename: string, mimeType: string) => {
    try {
      if (Platform.OS === 'web') {
        // Sur web, ouvrir dans un nouvel onglet
        window.open(url, '_blank');
      } else {
        // Sur mobile, télécharger et partager
        const fileUri = FileSystem.documentDirectory + filename;
        const downloadResult = await FileSystem.downloadAsync(url, fileUri);
        
        if (downloadResult.status === 200) {
          const canShare = await Sharing.isAvailableAsync();
          if (canShare) {
            await Sharing.shareAsync(downloadResult.uri, {
              mimeType: mimeType,
              dialogTitle: 'Partager le rapport'
            });
          } else {
            Alert.alert('Succès', `Fichier téléchargé: ${filename}`);
          }
        } else {
          throw new Error('Échec du téléchargement');
        }
      }
    } catch (error) {
      console.error('Erreur téléchargement:', error);
      throw error;
    }
  };

  const generateCadetsList = async () => {
    if (cadetsFilterType === 'section' && !selectedSection) {
      Alert.alert('Erreur', 'Veuillez sélectionner une section');
      return;
    }
    if (cadetsFilterType === 'role' && !selectedRole) {
      Alert.alert('Erreur', 'Veuillez entrer un rôle');
      return;
    }

    setGeneratingCadetsList(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const requestBody = {
        filter_type: cadetsFilterType,
        section_id: cadetsFilterType === 'section' ? selectedSection : null,
        role: cadetsFilterType === 'role' ? selectedRole : null
      };
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/reports/cadets-list?format=pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = `liste_cadets_${new Date().toISOString().split('T')[0]}.pdf`;
        
        await downloadFile(url, filename, 'application/pdf');
        Alert.alert('Succès', 'Liste des cadets générée');
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la génération');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible de générer le rapport');
    } finally {
      setGeneratingCadetsList(false);
    }
  };

  const generateInspectionSheet = async () => {
    if (!selectedUniformType) {
      Alert.alert('Erreur', 'Veuillez sélectionner un type de tenue');
      return;
    }

    setGeneratingSheet(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const requestBody = {
        uniform_type: selectedUniformType,
        section_id: sheetSection !== 'all' ? sheetSection : null
      };
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/reports/inspection-sheet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = `feuille_inspection_${selectedUniformType.replace(/ /g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
        
        await downloadFile(url, filename, 'application/pdf');
        Alert.alert('Succès', 'Feuille d\'inspection générée');
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la génération');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible de générer la feuille');
    } finally {
      setGeneratingSheet(false);
    }
  };

  const generateInspectionStats = async () => {
    setGeneratingStats(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Calculer les dates selon la période
      const endDate = new Date();
      let startDate = new Date();
      
      switch (statsPeriod) {
        case 'week':
          startDate.setDate(endDate.getDate() - 7);
          break;
        case 'month':
          startDate.setMonth(endDate.getMonth() - 1);
          break;
        case 'quarter':
          startDate.setMonth(endDate.getMonth() - 3);
          break;
      }
      
      const requestBody = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        section_id: statsSection !== 'all' ? statsSection : null,
        include_comparisons: true,
        export_format: statsFormat
      };
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/reports/inspection-stats`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const extension = statsFormat === 'excel' ? 'xlsx' : 'pdf';
        const mimeType = statsFormat === 'excel' ? 
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 
          'application/pdf';
        const filename = `rapport_inspections_${new Date().toISOString().split('T')[0]}.${extension}`;
        
        await downloadFile(url, filename, mimeType);
        Alert.alert('Succès', 'Rapport d\'inspections généré');
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la génération');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible de générer le rapport');
    } finally {
      setGeneratingStats(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#3182ce" />
          <Text style={styles.loadingText}>Chargement...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Retour</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Rapports</Text>
      </View>

      {/* Onglets */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'cadets' && styles.activeTab]}
          onPress={() => setActiveTab('cadets')}
        >
          <Text style={[styles.tabText, activeTab === 'cadets' && styles.activeTabText]}>
            📋 Liste Cadets
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'sheets' && styles.activeTab]}
          onPress={() => setActiveTab('sheets')}
        >
          <Text style={[styles.tabText, activeTab === 'sheets' && styles.activeTabText]}>
            📝 Feuilles Vierges
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'stats' && styles.activeTab]}
          onPress={() => setActiveTab('stats')}
        >
          <Text style={[styles.tabText, activeTab === 'stats' && styles.activeTabText]}>
            📊 Statistiques
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {/* Tab 1: Liste des Cadets */}
        {activeTab === 'cadets' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>Générer une Liste des Cadets</Text>
            <Text style={styles.sectionDescription}>
              Créez une liste formatée des cadets avec leurs informations pour impression ou archivage
            </Text>

            <View style={styles.filterSection}>
              <Text style={styles.label}>Type de filtre</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={cadetsFilterType}
                  onValueChange={(value) => setCadetsFilterType(value as 'all' | 'section' | 'role')}
                  style={styles.picker}
                >
                  <Picker.Item label="Tous les cadets" value="all" />
                  <Picker.Item label="Par section" value="section" />
                  <Picker.Item label="Par rôle" value="role" />
                </Picker>
              </View>

              {cadetsFilterType === 'section' && (
                <View style={styles.subFilter}>
                  <Text style={styles.label}>Section</Text>
                  <View style={styles.pickerContainer}>
                    <Picker
                      selectedValue={selectedSection}
                      onValueChange={setSelectedSection}
                      style={styles.picker}
                    >
                      <Picker.Item label="Sélectionner une section..." value="" />
                      {sections.map(section => (
                        <Picker.Item key={section.id} label={section.nom} value={section.id} />
                      ))}
                    </Picker>
                  </View>
                </View>
              )}

              {cadetsFilterType === 'role' && (
                <View style={styles.subFilter}>
                  <Text style={styles.label}>Rôle (ex: Cadet, Sergent)</Text>
                  <View style={styles.pickerContainer}>
                    <Picker
                      selectedValue={selectedRole}
                      onValueChange={setSelectedRole}
                      style={styles.picker}
                    >
                      <Picker.Item label="Sélectionner un rôle..." value="" />
                      <Picker.Item label="Cadet" value="cadet" />
                      <Picker.Item label="Sergent" value="sergent" />
                      <Picker.Item label="Adjudant" value="adjudant" />
                      <Picker.Item label="Commandant" value="commandant" />
                    </Picker>
                  </View>
                </View>
              )}
            </View>

            <TouchableOpacity
              style={styles.generateButton}
              onPress={generateCadetsList}
              disabled={generatingCadetsList}
            >
              {generatingCadetsList ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.generateButtonText}>📄 Générer PDF</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Tab 2: Feuilles d'Inspection Vierges */}
        {activeTab === 'sheets' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>Feuilles d'Inspection Vierges</Text>
            <Text style={styles.sectionDescription}>
              Générez des feuilles d'inspection vierges pour remplir à la main avec les critères actuels
            </Text>

            <View style={styles.filterSection}>
              <Text style={styles.label}>Type de tenue</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={selectedUniformType}
                  onValueChange={setSelectedUniformType}
                  style={styles.picker}
                >
                  {uniformTypes.map(type => (
                    <Picker.Item key={type} label={type} value={type} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Section (optionnel)</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={sheetSection}
                  onValueChange={setSheetSection}
                  style={styles.picker}
                >
                  <Picker.Item label="Toutes les sections" value="all" />
                  {sections.map(section => (
                    <Picker.Item key={section.id} label={section.nom} value={section.id} />
                  ))}
                </Picker>
              </View>
            </View>

            <TouchableOpacity
              style={styles.generateButton}
              onPress={generateInspectionSheet}
              disabled={generatingSheet}
            >
              {generatingSheet ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.generateButtonText}>📄 Générer Feuille PDF</Text>
              )}
            </TouchableOpacity>

            <View style={styles.infoBox}>
              <Text style={styles.infoText}>
                ℹ️ Les critères seront chargés automatiquement depuis les paramètres actuels
              </Text>
            </View>
          </View>
        )}

        {/* Tab 3: Rapports d'Inspections */}
        {activeTab === 'stats' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>Rapports d'Inspections</Text>
            <Text style={styles.sectionDescription}>
              Générez des rapports détaillés avec statistiques, comparaisons et identification des cadets nécessitant un suivi
            </Text>

            <View style={styles.filterSection}>
              <Text style={styles.label}>Période</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={statsPeriod}
                  onValueChange={(value) => setStatsPeriod(value as any)}
                  style={styles.picker}
                >
                  <Picker.Item label="Dernière semaine" value="week" />
                  <Picker.Item label="Dernier mois" value="month" />
                  <Picker.Item label="Dernier trimestre" value="quarter" />
                </Picker>
              </View>

              <Text style={styles.label}>Section (optionnel)</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={statsSection}
                  onValueChange={setStatsSection}
                  style={styles.picker}
                >
                  <Picker.Item label="Toutes les sections" value="all" />
                  {sections.map(section => (
                    <Picker.Item key={section.id} label={section.nom} value={section.id} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Format d'export</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={statsFormat}
                  onValueChange={(value) => setStatsFormat(value as 'pdf' | 'excel')}
                  style={styles.picker}
                >
                  <Picker.Item label="PDF (Rapport visuel)" value="pdf" />
                  <Picker.Item label="Excel (Données détaillées)" value="excel" />
                </Picker>
              </View>
            </View>

            <TouchableOpacity
              style={styles.generateButton}
              onPress={generateInspectionStats}
              disabled={generatingStats}
            >
              {generatingStats ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.generateButtonText}>
                  {statsFormat === 'pdf' ? '📄 Générer PDF' : '📊 Générer Excel'}
                </Text>
              )}
            </TouchableOpacity>

            <View style={styles.featuresList}>
              <Text style={styles.featuresTitle}>Ce rapport inclut:</Text>
              <Text style={styles.featureItem}>✓ Statistiques globales de l'escadron</Text>
              <Text style={styles.featureItem}>✓ Comparaison par section</Text>
              <Text style={styles.featureItem}>✓ Identification des cadets en difficulté (&lt; 60%)</Text>
              <Text style={styles.featureItem}>✓ Top 10 des meilleurs cadets</Text>
              <Text style={styles.featureItem}>✓ Évolution dans le temps</Text>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  backButton: {
    marginRight: 16,
  },
  backButtonText: {
    color: '#3b82f6',
    fontSize: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#3b82f6',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  activeTabText: {
    color: '#3b82f6',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  tabContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 24,
    lineHeight: 20,
  },
  filterSection: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 12,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#fff',
  },
  picker: {
    height: 50,
  },
  subFilter: {
    marginTop: 12,
  },
  generateButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoBox: {
    backgroundColor: '#eff6ff',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  infoText: {
    fontSize: 13,
    color: '#1e40af',
    lineHeight: 18,
  },
  featuresList: {
    backgroundColor: '#f9fafb',
    padding: 16,
    borderRadius: 8,
    marginTop: 16,
  },
  featuresTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  featureItem: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 6,
    lineHeight: 18,
  },
});
