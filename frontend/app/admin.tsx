import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  TextInput,
  Modal,
  ActivityIndicator,
  RefreshControl,
  Switch
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
  actif: boolean;
  created_at: string;
}

interface Section {
  id: string;
  nom: string;
  description?: string;
  responsable_id?: string;
  created_at: string;
}

interface UserFormData {
  nom: string;
  prenom: string;
  email: string;
  grade: string;
  role: string;
  section_id: string;
}

const GRADES = [
  { value: 'cadet', label: 'Cadet' },
  { value: 'caporal', label: 'Caporal' },
  { value: 'sergent', label: 'Sergent' },
  { value: 'adjudant', label: 'Adjudant' },
  { value: 'lieutenant', label: 'Lieutenant' },
  { value: 'capitaine', label: 'Capitaine' },
  { value: 'commandant', label: 'Commandant' }
];

const ROLES = [
  { value: 'cadet', label: 'Cadet' },
  { value: 'cadet_responsible', label: 'Cadet Responsable' },
  { value: 'cadet_admin', label: 'Cadet Administrateur' },
  { value: 'encadrement', label: 'Encadrement' }
];

interface Activity {
  id: string;
  nom: string;
  description?: string;
  type: 'unique' | 'recurring';
  cadet_ids: string[];
  cadet_names: string[];
  recurrence_interval?: number;
  recurrence_unit?: string;
  next_date?: string;
  planned_date?: string;
  created_by: string;
  created_at: string;
  active: boolean;
}

interface ActivityFormData {
  nom: string;
  description: string;
  type: 'unique' | 'recurring';
  cadet_ids: string[];
  recurrence_interval: string;
  recurrence_unit: string;
  next_date: string;
  planned_date: string;
}

export default function Admin() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Navigation
  const [activeTab, setActiveTab] = useState<'activities' | 'users' | 'sections' | 'settings'>('activities');
  
  // Gestion des activités
  const [activities, setActivities] = useState<Activity[]>([]);
  const [cadets, setCadets] = useState<User[]>([]);
  const [showActivityModal, setShowActivityModal] = useState(false);
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null);
  const [activityForm, setActivityForm] = useState<ActivityFormData>({
    nom: '',
    description: '',
    type: 'unique',
    cadet_ids: [],
    recurrence_interval: '7',
    recurrence_unit: 'days',
    next_date: '',
    planned_date: ''
  });
  const [savingActivity, setSavingActivity] = useState(false);

  // Gestion des utilisateurs
  const [users, setUsers] = useState<User[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState<UserFormData>({
    nom: '',
    prenom: '',
    email: '',
    grade: 'cadet',
    role: 'cadet',
    section_id: ''
  });
  const [savingUser, setSavingUser] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        const parsedUser = JSON.parse(userData);
        
        // Vérifier les permissions d'administration
        if (!['cadet_admin', 'encadrement'].includes(parsedUser.role)) {
          Alert.alert('Accès refusé', 'Vous n\'avez pas les permissions pour accéder à cette section.');
          router.back();
          return;
        }
        
        setUser(parsedUser);
        await loadData();
      } else {
        router.push('/');
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des permissions:', error);
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    await Promise.all([
      loadActivities(),
      loadCadets(),
      loadUsers(),
      loadSections()
    ]);
  };

  const loadUsers = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des utilisateurs:', error);
    }
  };

  const loadSections = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSections(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des sections:', error);
    }
  };

  const loadActivities = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setActivities(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des activités:', error);
    }
  };

  const loadCadets = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const filteredCadets = data.filter((u: User) => 
          ['cadet', 'cadet_responsible'].includes(u.role)
        );
        setCadets(filteredCadets);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des cadets:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const openActivityModal = (activity: Activity | null = null) => {
    if (activity) {
      setEditingActivity(activity);
      setActivityForm({
        nom: activity.nom,
        description: activity.description || '',
        type: activity.type,
        cadet_ids: activity.cadet_ids,
        recurrence_interval: activity.recurrence_interval?.toString() || '7',
        recurrence_unit: activity.recurrence_unit || 'days',
        next_date: activity.next_date || '',
        planned_date: activity.planned_date || ''
      });
    } else {
      setEditingActivity(null);
      setActivityForm({
        nom: '',
        description: '',
        type: 'unique',
        cadet_ids: [],
        recurrence_interval: '7',
        recurrence_unit: 'days',
        next_date: '',
        planned_date: ''
      });
    }
    setShowActivityModal(true);
  };

  const saveActivity = async () => {
    if (!activityForm.nom.trim()) {
      Alert.alert('Erreur', 'Le nom de l\'activité est requis');
      return;
    }

    if (activityForm.cadet_ids.length === 0) {
      Alert.alert('Erreur', 'Veuillez sélectionner au moins un cadet');
      return;
    }

    setSavingActivity(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const payload = {
        nom: activityForm.nom.trim(),
        description: activityForm.description.trim() || null,
        type: activityForm.type,
        cadet_ids: activityForm.cadet_ids,
        recurrence_interval: activityForm.type === 'recurring' ? parseInt(activityForm.recurrence_interval) : null,
        recurrence_unit: activityForm.type === 'recurring' ? activityForm.recurrence_unit : null,
        next_date: activityForm.type === 'recurring' && activityForm.next_date ? activityForm.next_date : null,
        planned_date: activityForm.type === 'unique' && activityForm.planned_date ? activityForm.planned_date : null
      };

      const url = editingActivity 
        ? `${EXPO_PUBLIC_BACKEND_URL}/api/activities/${editingActivity.id}`
        : `${EXPO_PUBLIC_BACKEND_URL}/api/activities`;
      
      const method = editingActivity ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        Alert.alert(
          'Succès', 
          editingActivity ? 'Activité modifiée avec succès' : 'Activité créée avec succès'
        );
        setShowActivityModal(false);
        await loadActivities();
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la sauvegarde');
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      Alert.alert('Erreur', 'Impossible de sauvegarder l\'activité');
    } finally {
      setSavingActivity(false);
    }
  };

  const deleteActivity = async (activity: Activity) => {
    Alert.alert(
      'Confirmer la suppression',
      `Êtes-vous sûr de vouloir supprimer l'activité "${activity.nom}" ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            try {
              const token = await AsyncStorage.getItem('access_token');
              const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities/${activity.id}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              if (response.ok) {
                Alert.alert('Succès', 'Activité supprimée avec succès');
                await loadActivities();
              } else {
                Alert.alert('Erreur', 'Impossible de supprimer l\'activité');
              }
            } catch (error) {
              console.error('Erreur lors de la suppression:', error);
              Alert.alert('Erreur', 'Erreur réseau');
            }
          }
        }
      ]
    );
  };

  const toggleCadetSelection = (cadetId: string) => {
    setActivityForm(prev => ({
      ...prev,
      cadet_ids: prev.cadet_ids.includes(cadetId)
        ? prev.cadet_ids.filter(id => id !== cadetId)
        : [...prev.cadet_ids, cadetId]
    }));
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
        <Text style={styles.title}>Administration</Text>
      </View>

      {/* Navigation tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'activities' && styles.activeTab]}
          onPress={() => setActiveTab('activities')}
        >
          <Text style={[styles.tabText, activeTab === 'activities' && styles.activeTabText]}>
            Activités
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'users' && styles.activeTab]}
          onPress={() => setActiveTab('users')}
        >
          <Text style={[styles.tabText, activeTab === 'users' && styles.activeTabText]}>
            Utilisateurs
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'sections' && styles.activeTab]}
          onPress={() => setActiveTab('sections')}
        >
          <Text style={[styles.tabText, activeTab === 'sections' && styles.activeTabText]}>
            Sections
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'settings' && styles.activeTab]}
          onPress={() => setActiveTab('settings')}
        >
          <Text style={[styles.tabText, activeTab === 'settings' && styles.activeTabText]}>
            Paramètres
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Gestion des Activités */}
        {activeTab === 'activities' && (
          <View style={styles.tabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Gestion des Activités</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => openActivityModal()}
              >
                <Text style={styles.addButtonText}>+ Nouvelle Activité</Text>
              </TouchableOpacity>
            </View>

            {activities.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>Aucune activité configurée</Text>
                <Text style={styles.emptyStateSubtext}>
                  Créez votre première activité pour organiser les présences par groupes prédéfinis
                </Text>
              </View>
            ) : (
              activities.map((activity) => (
                <View key={activity.id} style={styles.activityCard}>
                  <View style={styles.activityHeader}>
                    <Text style={styles.activityName}>{activity.nom}</Text>
                    <View style={[
                      styles.activityTypeBadge,
                      { backgroundColor: activity.type === 'recurring' ? '#10b981' : '#3b82f6' }
                    ]}>
                      <Text style={styles.activityTypeText}>
                        {activity.type === 'recurring' ? 'Récurrent' : 'Ponctuel'}
                      </Text>
                    </View>
                  </View>
                  
                  {activity.description && (
                    <Text style={styles.activityDescription}>{activity.description}</Text>
                  )}
                  
                  <Text style={styles.activityCadets}>
                    Cadets: {activity.cadet_names.join(', ')} ({activity.cadet_ids.length})
                  </Text>
                  
                  {activity.type === 'recurring' && activity.next_date && (
                    <Text style={styles.activityDate}>
                      Prochaine: {new Date(activity.next_date).toLocaleDateString('fr-FR')}
                      {activity.recurrence_interval && (
                        <Text> (tous les {activity.recurrence_interval} {activity.recurrence_unit === 'days' ? 'jour(s)' : 'semaine(s)'})</Text>
                      )}
                    </Text>
                  )}
                  
                  {activity.type === 'unique' && activity.planned_date && (
                    <Text style={styles.activityDate}>
                      Prévue: {new Date(activity.planned_date).toLocaleDateString('fr-FR')}
                    </Text>
                  )}

                  <View style={styles.activityActions}>
                    <TouchableOpacity
                      style={styles.editButton}
                      onPress={() => openActivityModal(activity)}
                    >
                      <Text style={styles.editButtonText}>Modifier</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.deleteButton}
                      onPress={() => deleteActivity(activity)}
                    >
                      <Text style={styles.deleteButtonText}>Supprimer</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* Autres tabs (à implémenter) */}
        {activeTab === 'users' && (
          <View style={styles.tabContent}>
            <Text style={styles.comingSoon}>Gestion des Utilisateurs - Prochainement</Text>
          </View>
        )}

        {activeTab === 'sections' && (
          <View style={styles.tabContent}>
            <Text style={styles.comingSoon}>Gestion des Sections - Prochainement</Text>
          </View>
        )}

        {activeTab === 'settings' && (
          <View style={styles.tabContent}>
            <Text style={styles.comingSoon}>Paramètres - Prochainement</Text>
          </View>
        )}
      </ScrollView>

      {/* Modal pour créer/modifier une activité */}
      <Modal
        visible={showActivityModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingActivity ? 'Modifier l\'Activité' : 'Nouvelle Activité'}
            </Text>
            <TouchableOpacity onPress={() => setShowActivityModal(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {/* Informations de base */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Informations de base</Text>
              
              <Text style={styles.inputLabel}>Nom de l'activité *</Text>
              <TextInput
                style={styles.input}
                value={activityForm.nom}
                onChangeText={(text) => setActivityForm(prev => ({...prev, nom: text}))}
                placeholder="Ex: Cours de Musique"
              />

              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={activityForm.description}
                onChangeText={(text) => setActivityForm(prev => ({...prev, description: text}))}
                placeholder="Description de l'activité..."
                multiline
                numberOfLines={3}
              />
            </View>

            {/* Type d'activité */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Type d'activité</Text>
              
              <View style={styles.typeSelector}>
                <TouchableOpacity
                  style={[
                    styles.typeButton,
                    activityForm.type === 'unique' && styles.typeButtonActive
                  ]}
                  onPress={() => setActivityForm(prev => ({...prev, type: 'unique'}))}
                >
                  <Text style={[
                    styles.typeButtonText,
                    activityForm.type === 'unique' && styles.typeButtonTextActive
                  ]}>
                    Ponctuel
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[
                    styles.typeButton,
                    activityForm.type === 'recurring' && styles.typeButtonActive
                  ]}
                  onPress={() => setActivityForm(prev => ({...prev, type: 'recurring'}))}
                >
                  <Text style={[
                    styles.typeButtonText,
                    activityForm.type === 'recurring' && styles.typeButtonTextActive
                  ]}>
                    Récurrent
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Configuration selon le type */}
              {activityForm.type === 'unique' && (
                <View>
                  <Text style={styles.inputLabel}>Date prévue</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.planned_date}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, planned_date: text}))}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
              )}

              {activityForm.type === 'recurring' && (
                <View>
                  <Text style={styles.inputLabel}>Récurrence (en jours)</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.recurrence_interval}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, recurrence_interval: text}))}
                    placeholder="7"
                    keyboardType="numeric"
                  />
                  
                  <Text style={styles.inputLabel}>Prochaine occurrence</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.next_date}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, next_date: text}))}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
              )}
            </View>

            {/* Sélection des cadets */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>
                Cadets participants ({activityForm.cadet_ids.length}/{cadets.length})
              </Text>
              
              {cadets.map((cadet) => (
                <TouchableOpacity
                  key={cadet.id}
                  style={[
                    styles.cadetSelectionCard,
                    activityForm.cadet_ids.includes(cadet.id) && styles.cadetSelectionCardSelected
                  ]}
                  onPress={() => toggleCadetSelection(cadet.id)}
                >
                  <View style={styles.cadetInfo}>
                    <Text style={styles.cadetName}>
                      {cadet.prenom} {cadet.nom}
                    </Text>
                    <Text style={styles.cadetGrade}>{cadet.grade}</Text>
                  </View>
                  <View style={[
                    styles.checkbox,
                    activityForm.cadet_ids.includes(cadet.id) && styles.checkboxSelected
                  ]}>
                    {activityForm.cadet_ids.includes(cadet.id) && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>

            {/* Bouton de sauvegarde */}
            <TouchableOpacity
              style={[styles.saveButton, savingActivity && styles.saveButtonDisabled]}
              onPress={saveActivity}
              disabled={savingActivity}
            >
              <Text style={styles.saveButtonText}>
                {savingActivity ? 'Enregistrement...' : editingActivity ? 'Modifier l\'Activité' : 'Créer l\'Activité'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  backButton: {
    marginRight: 15,
  },
  backButtonText: {
    fontSize: 16,
    color: '#3182ce',
    fontWeight: '600',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  tab: {
    flex: 1,
    paddingVertical: 15,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#3182ce',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  activeTabText: {
    color: '#3182ce',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    padding: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
  },
  addButton: {
    backgroundColor: '#10b981',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  addButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a365d',
    marginBottom: 10,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  activityCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 16,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  activityName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
    flex: 1,
    marginRight: 10,
  },
  activityTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  activityTypeText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '600',
  },
  activityDescription: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 8,
    fontStyle: 'italic',
  },
  activityCadets: {
    fontSize: 14,
    color: '#2d3748',
    marginBottom: 4,
  },
  activityDate: {
    fontSize: 13,
    color: '#718096',
    fontWeight: '500',
    marginBottom: 12,
  },
  activityActions: {
    flexDirection: 'row',
    gap: 10,
  },
  editButton: {
    backgroundColor: '#3182ce',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  editButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  deleteButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  deleteButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  comingSoon: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 50,
    fontStyle: 'italic',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
  },
  closeButton: {
    fontSize: 16,
    color: '#3182ce',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  formSection: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
  },
  formSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 15,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 5,
    marginTop: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f7fafc',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 15,
  },
  typeButton: {
    flex: 1,
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: 'white',
  },
  typeButtonActive: {
    borderColor: '#3182ce',
    backgroundColor: '#ebf8ff',
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
  },
  typeButtonTextActive: {
    color: '#3182ce',
  },
  cadetSelectionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#f7fafc',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cadetSelectionCardSelected: {
    backgroundColor: '#ebf8ff',
    borderColor: '#3182ce',
  },
  cadetInfo: {
    flex: 1,
  },
  cadetName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
  },
  cadetGrade: {
    fontSize: 14,
    color: '#4a5568',
    marginTop: 2,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e2e8f0',
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxSelected: {
    backgroundColor: '#3182ce',
    borderColor: '#3182ce',
  },
  checkmark: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  saveButton: {
    backgroundColor: '#10b981',
    borderRadius: 10,
    padding: 18,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  saveButtonDisabled: {
    backgroundColor: '#a0aec0',
  },
  saveButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});