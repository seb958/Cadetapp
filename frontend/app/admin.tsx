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
  Switch,
  Platform
} from 'react-native';
import { Picker } from '@react-native-picker/picker';

import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// Fonction utilitaire pour les alertes multi-plateforme
const showConfirmation = (title: string, message: string, onConfirm: () => void) => {
  if (Platform.OS === 'web') {
    // Pour web, utiliser window.confirm
    const confirmed = window.confirm(`${title}\n\n${message}`);
    if (confirmed) {
      onConfirm();
    }
  } else {
    // Pour mobile, utiliser Alert.alert
    Alert.alert(
      title,
      message,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer définitivement',
          style: 'destructive',
          onPress: onConfirm
        }
      ]
    );
  }
};

const showAlert = (title: string, message: string) => {
  if (Platform.OS === 'web') {
    window.alert(`${title}\n\n${message}`);
  } else {
    Alert.alert(title, message);
  }
};

interface User {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  grade: string;
  role: string;
  section_id?: string;
  actif: boolean;
  has_admin_privileges: boolean;
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
  has_admin_privileges: boolean;
}

const GRADES = [
  { value: 'cadet', label: 'Cadet' },
  { value: 'cadet_air_1re_classe', label: 'Cadet de l\'air 1re classe' },
  { value: 'caporal', label: 'Caporal' },
  { value: 'caporal_section', label: 'Caporal de section' },
  { value: 'sergent', label: 'Sergent' },
  { value: 'sergent_section', label: 'Sergent de section' },
  { value: 'adjudant_2e_classe', label: 'Adjudant de 2e classe' },
  { value: 'adjudant_1re_classe', label: 'Adjudant de 1re classe' },
  { value: 'instructeur_civil', label: 'Instructeur civil' },
  { value: 'eleve_officier', label: 'Élève-officier' },
  { value: 'sous_lieutenant', label: 'Sous-Lieutenant' },
  { value: 'lieutenant', label: 'Lieutenant' },
  { value: 'capitaine', label: 'Capitaine' },
  { value: 'commandant', label: 'Commandant' } // Compatibilité données existantes
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
  const [activeTab, setActiveTab] = useState<'activities' | 'users' | 'sections' | 'settings' | 'alerts' | 'roles'>('activities');

  // États pour l'onglet Alertes
  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [contactComment, setContactComment] = useState('');

  // États pour les filtres utilisateurs
  const [userFilters, setUserFilters] = useState({
    grade: '',
    role: '',
    section_id: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    grades: [],
    roles: [],
    sections: []
  });

  // États pour la gestion des rôles
  const [roles, setRoles] = useState([]);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [roleForm, setRoleForm] = useState({
    name: '',
    description: '',
    permissions: []
  });
  const [savingRole, setSavingRole] = useState(false);
  
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
    section_id: '',
    has_admin_privileges: false
  });
  const [savingUser, setSavingUser] = useState(false);

  // Gestion des sections
  const [showSectionModal, setShowSectionModal] = useState(false);
  const [editingSection, setEditingSection] = useState<Section | null>(null);
  const [sectionForm, setSectionForm] = useState({
    nom: '',
    description: '',
    responsable_id: ''
  });
  const [savingSection, setSavingSection] = useState(false);

  // Gestion des paramètres
  const [settings, setSettings] = useState({
    escadronName: '',
    address: '',
    contactEmail: '',
    allowMotivatedAbsences: true,
    consecutiveAbsenceThreshold: 3,
    inspectionCriteria: {
      'C1 - Tenue de Parade': [
        'Kippi réglementaire',
        'Chemise blanche impeccable',
        'Cravate correctement nouée',
        'Veste ajustée et boutonnée',
        'Pantalon repassé',
        'Chaussures cirées'
      ],
      'C5 - Tenue d\'Entraînement': [
        'Béret correctement porté',
        'Polo de sport propre',
        'Short/pantalon de sport',
        'Chaussures de sport',
        'Équipements sportifs'
      ]
    },
    autoBackup: true
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [newTenueName, setNewTenueName] = useState('');

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (token && userData) {
        const parsedUser = JSON.parse(userData);
        
        // Vérifier les permissions d'administration
        if (!['cadet_admin', 'encadrement'].includes(parsedUser.role)) {
          Alert.alert('Accès refusé', 'Vous n\'avez pas les permissions pour accéder à cette section.');
          router.back();
          return;
        }
        
        // Vérifier si le token est encore valide
        try {
          const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            setUser(parsedUser);
            // Forcer le rechargement complet des données
            await forceReloadAllData();
          } else {
            // Token invalide, rediriger vers la connexion
            Alert.alert('Session expirée', 'Veuillez vous reconnecter.');
            await AsyncStorage.removeItem('access_token');
            await AsyncStorage.removeItem('user_data');
            router.push('/');
          }
        } catch (error) {
          console.error('Erreur lors de la vérification du token:', error);
          Alert.alert('Erreur de connexion', 'Impossible de vérifier votre authentification.');
          router.push('/');
        }
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

  // Fonction pour forcer le rechargement complet des données
  const forceReloadAllData = async () => {
    console.log('🔄 Rechargement forcé de toutes les données...');
    
    // Réinitialiser tous les états
    setActivities([]);
    setCadets([]);
    setUsers([]);
    setSections([]);
    
    // Recharger toutes les données depuis l'API
    await loadData();
    
    console.log('✅ Rechargement complet terminé');
  };

  const loadData = async () => {
    // Charger d'abord les données de base
    await Promise.all([
      loadActivities(),
      loadCadets(),
      loadUsers(),
      loadSections(),
      loadAlerts(),
      loadRoles()
    ]);
    
    // Puis charger les options de filtres (qui peuvent utiliser les données de fallback)
    await loadFilterOptions();
  };

  const loadUsers = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Construire les paramètres de requête pour les filtres
      const params = new URLSearchParams();
      if (userFilters.grade) params.append('grade', userFilters.grade);
      if (userFilters.role) params.append('role', userFilters.role);
      if (userFilters.section_id) params.append('section_id', userFilters.section_id);
      
      const queryString = params.toString();
      const url = `${EXPO_PUBLIC_BACKEND_URL}/api/users${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('📊 Utilisateurs chargés depuis API:', userData.length);
        
        // Log détaillé de chaque utilisateur pour débogage
        userData.forEach((user: User, index: number) => {
          console.log(`${index + 1}. ${user.prenom} ${user.nom} | ID: ${user.id} | Actif: ${user.actif} | Admin: ${user.has_admin_privileges || false}`);
        });
        
        setUsers(userData);
      } else {
        console.error('Erreur lors du chargement des utilisateurs:', response.status);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des utilisateurs:', error);
    }
  };

  const loadFilterOptions = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users/filters`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFilterOptions(data);
      } else {
        console.warn('Erreur lors du chargement des filtres:', response.status);
        // Utiliser des données de fallback basées sur les utilisateurs existants
        const grades = [...new Set(users.map(u => u.grade))].sort();
        const roles = [...new Set(users.map(u => u.role))].sort();
        const sectionOptions = sections.map(s => ({id: s.id, name: s.nom}));
        setFilterOptions({
          grades,
          roles,
          sections: sectionOptions
        });
      }
    } catch (error) {
      console.error('Erreur lors du chargement des options de filtres:', error);
      // Utiliser des données de fallback
      const grades = [...new Set(users.map(u => u.grade))].sort();
      const roles = [...new Set(users.map(u => u.role))].sort();
      const sectionOptions = sections.map(s => ({id: s.id, name: s.nom}));
      setFilterOptions({
        grades,
        roles,
        sections: sectionOptions
      });
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
      // Trouver l'activité par nom dans la liste actuelle pour éviter les références obsolètes
      const currentActivity = activities.find(a => a.nom === activity.nom && a.id === activity.id);
      if (currentActivity) {
        console.log('Ouverture modal pour activité:', currentActivity.nom, 'ID:', currentActivity.id);
        setEditingActivity(currentActivity);
        setActivityForm({
          nom: currentActivity.nom,
          description: currentActivity.description || '',
          type: currentActivity.type,
          cadet_ids: currentActivity.cadet_ids,
          recurrence_interval: currentActivity.recurrence_interval?.toString() || '7',
          recurrence_unit: currentActivity.recurrence_unit || 'days',
          next_date: currentActivity.next_date || '',
          planned_date: currentActivity.planned_date || ''
        });
      } else {
        console.error('Activité non trouvée dans la liste actuelle:', activity.nom);
        showAlert('Erreur', 'Activité non trouvée dans les données actuelles. Veuillez actualiser.');
        return;
      }
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
      showAlert('Erreur', 'Le nom de l\'activité est requis');
      return;
    }

    // Filtrer les IDs de cadets pour ne garder que ceux qui existent encore
    const validCadetIds = activityForm.cadet_ids.filter(cadetId => 
      cadets.some(cadet => cadet.id === cadetId)
    );

    if (validCadetIds.length === 0) {
      showAlert('Erreur', 'Veuillez sélectionner au moins un cadet');
      return;
    }

    // Informer l'utilisateur si certains cadets ont été supprimés
    if (validCadetIds.length < activityForm.cadet_ids.length) {
      const removedCount = activityForm.cadet_ids.length - validCadetIds.length;
      showAlert(
        'Information', 
        `${removedCount} cadet(s) ont été automatiquement retirés car ils ne sont plus actifs.`
      );
    }

    setSavingActivity(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const payload = {
        nom: activityForm.nom.trim(),
        description: activityForm.description.trim() || null,
        type: activityForm.type,
        cadet_ids: validCadetIds,
        recurrence_interval: activityForm.type === 'recurring' ? parseInt(activityForm.recurrence_interval) : null,
        recurrence_unit: activityForm.type === 'recurring' ? activityForm.recurrence_unit : null,
        next_date: activityForm.type === 'recurring' && activityForm.next_date ? activityForm.next_date : null,
        planned_date: activityForm.type === 'unique' && activityForm.planned_date ? activityForm.planned_date : null
      };

      if (editingActivity) {
        // MODIFICATION : Chercher l'activité actuelle par nom au lieu d'utiliser l'ID cached
        console.log('🔍 Recherche activité par nom:', activityForm.nom);
        
        // Étape 1: Chercher l'activité actuelle en base par nom
        const searchResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!searchResponse.ok) {
          throw new Error('Impossible de récupérer les activités');
        }
        
        const allActivities = await searchResponse.json();
        const currentActivity = allActivities.find((a: Activity) => 
          a.nom === editingActivity.nom && a.id === editingActivity.id
        );
        
        if (!currentActivity) {
          showAlert('Erreur', `Activité "${editingActivity.nom}" non trouvée en base`);
          setSavingActivity(false);
          return;
        }
        
        console.log('✅ Activité trouvée avec ID:', currentActivity.id);
        
        // Étape 2: Utiliser l'ID actuel pour la modification
        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities/${currentActivity.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          showAlert('Succès', 'Activité modifiée avec succès');
          setShowActivityModal(false);
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
          await loadActivities();
        } else {
          const errorData = await response.json();
          showAlert('Erreur', errorData.detail || 'Erreur lors de la modification');
        }
      } else {
        // CRÉATION (reste inchangée)
        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          showAlert('Succès', 'Activité créée avec succès');
          setShowActivityModal(false);
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
          await loadActivities();
        } else {
          const errorData = await response.json();
          showAlert('Erreur', errorData.detail || 'Erreur lors de la sauvegarde');
        }
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      showAlert('Erreur', 'Impossible de sauvegarder l\'activité');
    } finally {
      setSavingActivity(false);
    }
  };

  const deleteActivity = async (activity: Activity) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/activities/${activity.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showAlert('Succès', `L'activité "${activity.nom}" a été supprimée définitivement.`);
        setShowActivityModal(false);
        setEditingActivity(null);
        await loadActivities();
      } else {
        const errorData = await response.json();
        showAlert('Erreur', errorData.detail || 'Impossible de supprimer l\'activité');
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      showAlert('Erreur', 'Erreur réseau lors de la suppression');
    }
  };

  const openUserModal = (user: User | null = null) => {
    if (user) {
      // Trouver l'utilisateur par nom dans la liste actuelle pour éviter les références obsolètes
      const currentUser = users.find(u => u.prenom === user.prenom && u.nom === user.nom);
      if (currentUser) {
        console.log('Ouverture modal pour:', currentUser.nom, currentUser.prenom, 'ID:', currentUser.id);
        setEditingUser(currentUser);
        setUserForm({
          nom: currentUser.nom,
          prenom: currentUser.prenom,
          email: currentUser.email || '',
          role: currentUser.role,
          grade: currentUser.grade,
          section_id: currentUser.section_id || '',
          has_admin_privileges: currentUser.has_admin_privileges || false
        });
      } else {
        console.error('Utilisateur non trouvé dans la liste actuelle:', user.nom, user.prenom);
        showAlert('Erreur', 'Utilisateur non trouvé dans les données actuelles. Veuillez actualiser.');
        return;
      }
    } else {
      setEditingUser(null);
      setUserForm({
        nom: '',
        prenom: '',
        email: '',
        grade: 'cadet',
        role: 'cadet',
        section_id: ''
      });
    }
    setShowUserModal(true);
  };

  const saveUser = async () => {
    if (!userForm.nom.trim() || !userForm.prenom.trim()) {
      Alert.alert('Erreur', 'Le nom et prénom sont requis');
      return;
    }

    // Validation email seulement si fourni
    if (userForm.email && userForm.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(userForm.email.trim())) {
        Alert.alert('Erreur', 'Format d\'email invalide');
        return;
      }
    }

    setSavingUser(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      if (editingUser) {
        // Modification d'utilisateur existant
        const payload: any = {};
        
        // Seulement inclure les champs modifiés
        if (userForm.nom !== editingUser.nom) payload.nom = userForm.nom.trim();
        if (userForm.prenom !== editingUser.prenom) payload.prenom = userForm.prenom.trim();
        if (userForm.email !== editingUser.email) {
          payload.email = userForm.email && userForm.email.trim() ? userForm.email.trim() : null;
        }
        if (userForm.grade !== editingUser.grade) payload.grade = userForm.grade;
        if (userForm.role !== editingUser.role) payload.role = userForm.role;
        if (userForm.section_id !== (editingUser.section_id || '')) {
          payload.section_id = userForm.section_id || null;
        }

        // Vérifier s'il y a des modifications
        if (Object.keys(payload).length === 0) {
          Alert.alert('Information', 'Aucune modification détectée');
          setSavingUser(false);
          return;
        }

        // MODIFICATION : Chercher l'utilisateur actuel par nom au lieu d'utiliser l'ID cached
        console.log('🔍 Recherche utilisateur par nom:', userForm.prenom, userForm.nom);
        
        // Étape 1: Chercher l'utilisateur actuel en base par nom
        const searchResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!searchResponse.ok) {
          throw new Error('Impossible de récupérer les utilisateurs');
        }
        
        const allUsers = await searchResponse.json();
        const currentUser = allUsers.find((u: User) => 
          u.prenom === editingUser.prenom && u.nom === editingUser.nom
        );
        
        if (!currentUser) {
          Alert.alert('Erreur', `Utilisateur ${editingUser.prenom} ${editingUser.nom} non trouvé en base`);
          setSavingUser(false);
          return;
        }
        
        console.log('✅ Utilisateur trouvé avec ID:', currentUser.id);
        
        // Étape 2: Utiliser l'ID actuel pour la modification
        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users/${currentUser.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          Alert.alert('Succès', 'Modifications enregistrées avec succès!');
          setShowUserModal(false);
          await loadUsers();
        } else {
          const errorData = await response.json();
          Alert.alert('Erreur', errorData.detail || 'Erreur lors de la modification');
        }
      } else {
        // Création d'invitation
        const payload = {
          nom: userForm.nom.trim(),
          prenom: userForm.prenom.trim(),
          email: userForm.email && userForm.email.trim() ? userForm.email.trim() : null,
          grade: userForm.grade,
          role: userForm.role,
          section_id: userForm.section_id || null
        };

        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/invite`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          const data = await response.json();
          let message = `Utilisateur créé avec succès: ${userForm.prenom} ${userForm.nom}`;
          
          if (userForm.email && userForm.email.trim()) {
            message += `\n\nInvitation envoyée à ${userForm.email}.\nToken d'invitation (pour test): ${data.token.substring(0, 20)}...`;
          } else {
            message += `\n\nAucun email fourni - l'utilisateur devra être configuré plus tard.`;
          }
          
          Alert.alert('Succès', message);
          setShowUserModal(false);
          await loadUsers();
        } else {
          const errorData = await response.json();
          Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'invitation');
        }
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      Alert.alert('Erreur', 'Impossible d\'envoyer l\'invitation');
    } finally {
      setSavingUser(false);
    }
  };

  const deleteUser = async (user: User) => {
    console.log('FONCTION deleteUser appelée avec:', user.nom, user.prenom);

    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users/${user.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showAlert('Succès', `L'utilisateur "${user.prenom} ${user.nom}" a été supprimé définitivement.`);
        setShowUserModal(false);
        await loadUsers();
      } else {
        const errorData = await response.json();
        showAlert('Erreur', errorData.detail || 'Impossible de supprimer l\'utilisateur');
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      showAlert('Erreur', 'Erreur réseau lors de la suppression');
    }
  };

  // Fonction pour charger les rôles depuis l'API
  const loadRoles = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/roles`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const customRoles = await response.json();
        setRoles(customRoles);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des rôles:', error);
    }
  };

  // Fonction pour obtenir tous les rôles (système + personnalisés)
  const getAllRoles = () => {
    const systemRoles = ROLES.map(r => ({ value: r.value, label: r.label, isSystem: true }));
    const customRoles = roles.map(r => ({ value: r.name, label: r.name, isSystem: false }));
    return [...systemRoles, ...customRoles];
  };

  const getRoleDisplayName = (role: string) => {
    // D'abord chercher dans les rôles système
    const systemRole = ROLES.find(r => r.value === role);
    if (systemRole) return systemRole.label;
    
    // Ensuite chercher dans les rôles personnalisés
    const customRole = roles.find(r => r.name === role);
    if (customRole) return customRole.name;
    
    return role;
  };

  const getGradeDisplayName = (grade: string) => {
    const gradeObj = GRADES.find(g => g.value === grade);
    return gradeObj ? gradeObj.label : grade;
  };

  const getSectionName = (sectionId: string) => {
    const section = sections.find(s => s.id === sectionId);
    return section ? section.nom : 'Aucune section';
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'cadet': return '#6b7280';
      case 'cadet_responsible': return '#3b82f6';
      case 'cadet_admin': return '#10b981';
      case 'encadrement': return '#dc2626';
      default: return '#6b7280';
    }
  };

  // Fonctions pour les sections
  const openSectionModal = (section: Section | null = null) => {
    if (section) {
      // Trouver la section par nom dans la liste actuelle pour éviter les références obsolètes
      const currentSection = sections.find(s => s.nom === section.nom && s.id === section.id);
      if (currentSection) {
        console.log('Ouverture modal pour section:', currentSection.nom, 'ID:', currentSection.id);
        setEditingSection(currentSection);
        setSectionForm({
          nom: currentSection.nom,
          description: currentSection.description || '',
          responsable_id: currentSection.responsable_id || ''
        });
      } else {
        console.error('Section non trouvée dans la liste actuelle:', section.nom);
        showAlert('Erreur', 'Section non trouvée dans les données actuelles. Veuillez actualiser.');
        return;
      }
    } else {
      setEditingSection(null);
      setSectionForm({
        nom: '',
        description: '',
        responsable_id: ''
      });
    }
    setShowSectionModal(true);
  };

  const saveSection = async () => {
    if (!sectionForm.nom.trim()) {
      Alert.alert('Erreur', 'Le nom de la section est requis');
      return;
    }

    setSavingSection(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const payload = {
        nom: sectionForm.nom.trim(),
        description: sectionForm.description.trim() || null,
        responsable_id: sectionForm.responsable_id || null
      };

      const url = editingSection 
        ? `${EXPO_PUBLIC_BACKEND_URL}/api/sections/${editingSection.id}`
        : `${EXPO_PUBLIC_BACKEND_URL}/api/sections`;
      
      const method = editingSection ? 'PUT' : 'POST';

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
          editingSection ? 'Section modifiée avec succès' : 'Section créée avec succès'
        );
        setShowSectionModal(false);
        await loadSections();
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la sauvegarde');
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      Alert.alert('Erreur', 'Impossible de sauvegarder la section');
    } finally {
      setSavingSection(false);
    }
  };

  const deleteSection = async (section: Section) => {
    console.log('FONCTION deleteSection appelée avec:', section.nom);

    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections/${section.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showAlert('Succès', `La section "${section.nom}" a été supprimée définitivement.`);
        setShowSectionModal(false);
        setEditingSection(null);
        await loadSections();
        await loadUsers(); // Recharger les utilisateurs car leurs sections ont pu changer
      } else {
        const errorData = await response.json();
        showAlert('Erreur', errorData.detail || 'Impossible de supprimer la section');
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      showAlert('Erreur', 'Erreur réseau lors de la suppression');
    }
  };

  const loadAlerts = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/alerts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des alertes:', error);
    }
  };

  const generateAlerts = async () => {
    setLoadingAlerts(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/alerts/generate?threshold=${settings.consecutiveAbsenceThreshold}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        showAlert('Alertes générées', result.message);
        await loadAlerts();
      }
    } catch (error) {
      console.error('Erreur lors de la génération des alertes:', error);
      showAlert('Erreur', 'Impossible de générer les alertes');
    } finally {
      setLoadingAlerts(false);
    }
  };

  const openAlertModal = (alert) => {
    setSelectedAlert(alert);
    setContactComment(alert.contact_comment || '');
    setShowAlertModal(true);
  };

  const updateAlertStatus = async (status, comment = '') => {
    if (!selectedAlert) return;

    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/alerts/${selectedAlert.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: status,
          contact_comment: comment
        }),
      });

      if (response.ok) {
        const statusLabels = {
          'contacted': 'contacté',
          'resolved': 'résolu'
        };
        showAlert('Succès', `Alerte marquée comme ${statusLabels[status]}`);
        setShowAlertModal(false);
        setSelectedAlert(null);
        setContactComment('');
        await loadAlerts();
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour de l\'alerte:', error);
      showAlert('Erreur', 'Impossible de mettre à jour l\'alerte');
    }
  };

  const saveSettings = async () => {
    setSavingSettings(true);
    try {
      // Simuler la sauvegarde des paramètres
      await new Promise(resolve => setTimeout(resolve, 1000));
      showAlert('Succès', 'Paramètres sauvegardés avec succès');
    } catch (error) {
      console.error('Erreur lors de la sauvegarde des paramètres:', error);
      showAlert('Erreur', 'Impossible de sauvegarder les paramètres');
    } finally {
      setSavingSettings(false);
    }
  };

  const addNewTenue = () => {
    if (!newTenueName.trim()) {
      showAlert('Erreur', 'Veuillez saisir un nom pour la nouvelle tenue');
      return;
    }

    const newCriteria = {...settings.inspectionCriteria};
    if (newCriteria[newTenueName.trim()]) {
      showAlert('Erreur', 'Une tenue avec ce nom existe déjà');
      return;
    }

    newCriteria[newTenueName.trim()] = [''];
    setSettings(prev => ({...prev, inspectionCriteria: newCriteria}));
    setNewTenueName('');
    showAlert('Succès', `Tenue "${newTenueName.trim()}" ajoutée avec succès`);
  };

  const removeTenue = (tenueType) => {
    showConfirmation(
      'Supprimer la tenue',
      `Êtes-vous sûr de vouloir supprimer la tenue "${tenueType}" et tous ses critères ?`,
      () => {
        const newCriteria = {...settings.inspectionCriteria};
        delete newCriteria[tenueType];
        setSettings(prev => ({...prev, inspectionCriteria: newCriteria}));
        showAlert('Succès', `Tenue "${tenueType}" supprimée avec succès`);
      }
    );
  };

  const openRoleModal = (role = null) => {
    if (role) {
      setEditingRole(role);
      setRoleForm({
        name: role.name,
        description: role.description || '',
        permissions: role.permissions || []
      });
    } else {
      setEditingRole(null);
      setRoleForm({
        name: '',
        description: '',
        permissions: []
      });
    }
    setShowRoleModal(true);
  };

  const saveRole = async () => {
    if (!roleForm.name.trim()) {
      showAlert('Erreur', 'Le nom du rôle est requis');
      return;
    }

    setSavingRole(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const payload = {
        name: roleForm.name.trim(),
        description: roleForm.description.trim() || null,
        permissions: roleForm.permissions
      };

      const url = editingRole 
        ? `${EXPO_PUBLIC_BACKEND_URL}/api/roles/${editingRole.id}`
        : `${EXPO_PUBLIC_BACKEND_URL}/api/roles`;
      
      const method = editingRole ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        showAlert(
          'Succès', 
          editingRole ? 'Rôle modifié avec succès' : 'Rôle créé avec succès'
        );
        setShowRoleModal(false);
        // Recharger les rôles ici si on avait la fonction
      } else {
        const errorData = await response.json();
        showAlert('Erreur', errorData.detail || 'Erreur lors de la sauvegarde');
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      showAlert('Erreur', 'Impossible de sauvegarder le rôle');
    } finally {
      setSavingRole(false);
    }
  };

  const getResponsableName = (responsableId: string) => {
    const responsable = users.find(u => u.id === responsableId);
    return responsable ? `${responsable.prenom} ${responsable.nom}` : 'Aucun responsable';
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
        <TouchableOpacity
          style={[styles.tab, activeTab === 'alerts' && styles.activeTab]}
          onPress={() => setActiveTab('alerts')}
        >
          <Text style={[styles.tabText, activeTab === 'alerts' && styles.activeTabText]}>
            Alertes
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'roles' && styles.activeTab]}
          onPress={() => setActiveTab('roles')}
        >
          <Text style={[styles.tabText, activeTab === 'roles' && styles.activeTabText]}>
            Rôles
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
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* Gestion des Utilisateurs */}
        {activeTab === 'users' && (
          <View style={styles.tabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Gestion des Utilisateurs</Text>
              <View style={styles.sectionActions}>
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => openUserModal()}
                >
                  <Text style={styles.addButtonText}>+ Inviter Utilisateur</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.refreshButton}
                  onPress={forceReloadAllData}
                >
                  <Text style={styles.refreshButtonText}>🔄 Actualiser</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Filtres */}
            <View style={styles.filtersContainer}>
              <Text style={styles.filtersTitle}>🔍 Filtres</Text>
              <View style={styles.filtersRow}>
                <View style={styles.filterItem}>
                  <Text style={styles.filterLabel}>Grade</Text>
                  <View style={styles.pickerContainer}>
                    <Picker
                      selectedValue={userFilters.grade}
                      style={styles.picker}
                      onValueChange={(value) => {
                        setUserFilters(prev => ({...prev, grade: value}));
                        // Recharger automatiquement les utilisateurs
                        setTimeout(loadUsers, 100);
                      }}
                    >
                      <Picker.Item label="Tous les grades" value="" />
                      {filterOptions.grades.map((grade) => (
                        <Picker.Item key={grade} label={grade} value={grade} />
                      ))}
                    </Picker>
                  </View>
                </View>

                <View style={styles.filterItem}>
                  <Text style={styles.filterLabel}>Rôle</Text>
                  <View style={styles.pickerContainer}>
                    <Picker
                      selectedValue={userFilters.role}
                      style={styles.picker}
                      onValueChange={(value) => {
                        setUserFilters(prev => ({...prev, role: value}));
                        setTimeout(loadUsers, 100);
                      }}
                    >
                      <Picker.Item label="Tous les rôles" value="" />
                      {filterOptions.roles.map((role) => (
                        <Picker.Item key={role} label={role} value={role} />
                      ))}
                    </Picker>
                  </View>
                </View>

                <View style={styles.filterItem}>
                  <Text style={styles.filterLabel}>Section</Text>
                  <View style={styles.pickerContainer}>
                    <Picker
                      selectedValue={userFilters.section_id}
                      style={styles.picker}
                      onValueChange={(value) => {
                        setUserFilters(prev => ({...prev, section_id: value}));
                        setTimeout(loadUsers, 100);
                      }}
                    >
                      <Picker.Item label="Toutes les sections" value="" />
                      {filterOptions.sections.map((section) => (
                        <Picker.Item key={section.id} label={section.name} value={section.id} />
                      ))}
                    </Picker>
                  </View>
                </View>
              </View>

              <TouchableOpacity
                style={styles.resetFiltersButton}
                onPress={() => {
                  setUserFilters({grade: '', role: '', section_id: ''});
                  setTimeout(loadUsers, 100);
                }}
              >
                <Text style={styles.resetFiltersText}>🔄 Réinitialiser les filtres</Text>
              </TouchableOpacity>
            </View>

            {users.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>Aucun utilisateur trouvé</Text>
                <Text style={styles.emptyStateSubtext}>
                  Invitez votre premier utilisateur pour commencer
                </Text>
              </View>
            ) : (
              users.map((user) => (
                <View key={user.id} style={styles.userCard}>
                  <View style={styles.userHeader}>
                    <View style={styles.userInfo}>
                      <Text style={styles.userName}>
                        {user.prenom} {user.nom}
                        {user.has_admin_privileges && (
                          <Text style={styles.adminBadge}> • ADMIN</Text>
                        )}
                      </Text>
                      <Text style={styles.userEmail}>{user.email || 'Pas d\'email'}</Text>
                    <Text style={[
                      styles.userStatus,
                      user.actif && user.email && {color: '#10b981'} // Vert pour "Peut se connecter"
                    ]}>
                      {user.actif 
                        ? (user.email ? 'Peut se connecter' : 'Ne s\'est pas encore connecté')
                        : 'Compte désactivé'
                      }
                    </Text>
                    </View>
                    <View style={styles.userBadges}>
                      <View style={[
                        styles.roleBadge,
                        { backgroundColor: getRoleBadgeColor(user.role) }
                      ]}>
                        <Text style={styles.roleBadgeText}>
                          {getRoleDisplayName(user.role)}
                        </Text>
                      </View>
                      {!user.actif && (
                        <View style={styles.statusBadge}>
                          <Text style={styles.statusBadgeText}>En attente</Text>
                        </View>
                      )}
                    </View>
                  </View>
                  
                  <View style={styles.userDetails}>
                    <Text style={styles.userDetail}>
                      Grade: {getGradeDisplayName(user.grade)}
                    </Text>
                    <Text style={styles.userDetail}>
                      Section: {user.section_id ? getSectionName(user.section_id) : 'Aucune'}
                    </Text>
                    <Text style={styles.userDetail}>
                      Créé le: {new Date(user.created_at).toLocaleDateString('fr-FR')}
                    </Text>
                  </View>

                  <View style={styles.userActions}>
                    <TouchableOpacity
                      style={styles.editButton}
                      onPress={() => {
                        console.log('Bouton modifier cliqué pour:', user.nom, user.prenom);
                        openUserModal(user);
                      }}
                    >
                      <Text style={styles.editButtonText}>Modifier</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {activeTab === 'sections' && (
          <View style={styles.tabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Gestion des Sections</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => openSectionModal()}
              >
                <Text style={styles.addButtonText}>+ Nouvelle Section</Text>
              </TouchableOpacity>
            </View>

            {sections.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>Aucune section créée</Text>
                <Text style={styles.emptyStateSubtext}>
                  Créez votre première section pour organiser les cadets
                </Text>
              </View>
            ) : (
              sections.map((section) => (
                <View key={section.id} style={styles.sectionCard}>
                  <View style={styles.sectionCardHeader}>
                    <Text style={styles.sectionCardName}>{section.nom}</Text>
                    <View style={styles.sectionActions}>
                      <TouchableOpacity
                        style={styles.editButton}
                        onPress={() => openSectionModal(section)}
                      >
                        <Text style={styles.editButtonText}>Modifier</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                  
                  {section.description && (
                    <Text style={styles.sectionCardDescription}>{section.description}</Text>
                  )}
                  
                  <Text style={styles.sectionCardInfo}>
                    Responsable: {section.responsable_id ? getResponsableName(section.responsable_id) : 'Aucun'}
                  </Text>
                  
                  <Text style={styles.sectionCardInfo}>
                    Créée le: {new Date(section.created_at).toLocaleDateString('fr-FR')}
                  </Text>

                  {/* Nombre de membres */}
                  <Text style={styles.sectionCardInfo}>
                    Membres: {users.filter(u => u.section_id === section.id).length} cadet(s)
                  </Text>
                </View>
              ))
            )}
          </View>
        )}

        {activeTab === 'settings' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>Paramètres de l'Escadron</Text>
            
            {/* Configuration générale */}
            <View style={styles.settingsSection}>
              <Text style={styles.settingsGroupTitle}>🏛️ Configuration Générale</Text>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Nom de l'escadron</Text>
                <TextInput
                  style={styles.input}
                  value={settings.escadronName}
                  onChangeText={(text) => setSettings(prev => ({...prev, escadronName: text}))}
                  placeholder="Ex: Escadron 781 Toulouse"
                />
              </View>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Adresse</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={settings.address}
                  onChangeText={(text) => setSettings(prev => ({...prev, address: text}))}
                  placeholder="Adresse complète de l'escadron"
                  multiline
                  numberOfLines={3}
                />
              </View>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Email de contact</Text>
                <TextInput
                  style={styles.input}
                  value={settings.contactEmail}
                  onChangeText={(text) => setSettings(prev => ({...prev, contactEmail: text}))}
                  placeholder="contact@escadron781.fr"
                  keyboardType="email-address"
                />
              </View>
            </View>

            {/* Paramètres des présences */}
            <View style={styles.settingsSection}>
              <Text style={styles.settingsGroupTitle}>📋 Paramètres des Présences</Text>
              
              <View style={styles.settingItem}>
                <View style={styles.switchContainer}>
                  <Text style={styles.settingLabel}>Autoriser les absences motivées</Text>
                  <Switch
                    value={settings.allowMotivatedAbsences}
                    onValueChange={(value) => setSettings(prev => ({...prev, allowMotivatedAbsences: value}))}
                  />
                </View>
              </View>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Seuil d'alerte absences consécutives</Text>
                <TextInput
                  style={styles.input}
                  value={settings.consecutiveAbsenceThreshold.toString()}
                  onChangeText={(text) => setSettings(prev => ({...prev, consecutiveAbsenceThreshold: parseInt(text) || 3}))}
                  placeholder="3"
                  keyboardType="numeric"
                />
                <Text style={styles.helperText}>Alerte automatique si un cadet a ce nombre d'absences consécutives</Text>
              </View>
            </View>

            {/* Critères d'inspection */}
            <View style={styles.settingsSection}>
              <Text style={styles.settingsGroupTitle}>👔 Critères d'Inspection des Uniformes</Text>
              
              {Object.entries(settings.inspectionCriteria).map(([tenueType, criteria]) => (
                <View key={tenueType} style={styles.tenueGroup}>
                  <View style={styles.tenueHeader}>
                    <Text style={styles.tenueTitle}>{tenueType}</Text>
                    <TouchableOpacity
                      style={styles.removeTenueButton}
                      onPress={() => removeTenue(tenueType)}
                    >
                      <Text style={styles.removeTenueButtonText}>🗑️</Text>
                    </TouchableOpacity>
                  </View>
                  
                  {criteria.map((criterion, index) => (
                    <View key={index} style={styles.criterionItem}>
                      <TextInput
                        style={[styles.input, {flex: 1}]}
                        value={criterion}
                        onChangeText={(text) => {
                          const newCriteria = {...settings.inspectionCriteria};
                          newCriteria[tenueType][index] = text;
                          setSettings(prev => ({...prev, inspectionCriteria: newCriteria}));
                        }}
                        placeholder={`Critère ${index + 1}`}
                      />
                      <TouchableOpacity
                        style={styles.removeButton}
                        onPress={() => {
                          const newCriteria = {...settings.inspectionCriteria};
                          newCriteria[tenueType] = newCriteria[tenueType].filter((_, i) => i !== index);
                          setSettings(prev => ({...prev, inspectionCriteria: newCriteria}));
                        }}
                      >
                        <Text style={styles.removeButtonText}>✕</Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                  
                  <TouchableOpacity
                    style={styles.addCriterionButton}
                    onPress={() => {
                      const newCriteria = {...settings.inspectionCriteria};
                      newCriteria[tenueType] = [...newCriteria[tenueType], ''];
                      setSettings(prev => ({...prev, inspectionCriteria: newCriteria}));
                    }}
                  >
                    <Text style={styles.addCriterionText}>+ Ajouter un critère pour {tenueType}</Text>
                  </TouchableOpacity>
                </View>
              ))}

              {/* Section pour ajouter une nouvelle tenue */}
              <View style={styles.newTenueSection}>
                <Text style={styles.settingLabel}>Ajouter une nouvelle tenue</Text>
                <View style={styles.newTenueInputRow}>
                  <TextInput
                    style={[styles.input, {flex: 1}]}
                    value={newTenueName}
                    onChangeText={setNewTenueName}
                    placeholder="Ex: C3 - Tenue de Combat, Tenue de Sortie..."
                  />
                  <TouchableOpacity
                    style={styles.addNewTenueButton}
                    onPress={addNewTenue}
                  >
                    <Text style={styles.addNewTenueButtonText}>+ Ajouter</Text>
                  </TouchableOpacity>
                </View>
              </View>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Barème de notation</Text>
                <Text style={styles.helperText}>
                  Excellent (4/4) - Bien (3/4) - Satisfaisant (2/4) - À améliorer (1/4) - Insuffisant (0/4)
                </Text>
              </View>
            </View>

            {/* Sauvegarde et données */}
            <View style={styles.settingsSection}>
              <Text style={styles.settingsGroupTitle}>💾 Sauvegarde et Données</Text>
              
              <View style={styles.settingItem}>
                <View style={styles.switchContainer}>
                  <Text style={styles.settingLabel}>Sauvegarde automatique hebdomadaire</Text>
                  <Switch
                    value={settings.autoBackup}
                    onValueChange={(value) => setSettings(prev => ({...prev, autoBackup: value}))}
                  />
                </View>
              </View>
              
              <View style={styles.buttonRow}>
                <TouchableOpacity style={styles.backupButton}>
                  <Text style={styles.backupButtonText}>📥 Exporter les données</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.backupButton}>
                  <Text style={styles.backupButtonText}>📤 Importer des données</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Bouton sauvegarder */}
            <TouchableOpacity
              style={[styles.saveButton, savingSettings && styles.saveButtonDisabled]}
              onPress={saveSettings}
              disabled={savingSettings}
            >
              <Text style={styles.saveButtonText}>
                {savingSettings ? 'Sauvegarde...' : '💾 Sauvegarder les paramètres'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Gestion des Alertes */}
        {activeTab === 'alerts' && (
          <View style={styles.tabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Alertes d'Absences Consécutives</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={generateAlerts}
                disabled={loadingAlerts}
              >
                <Text style={styles.addButtonText}>
                  {loadingAlerts ? 'Génération...' : '🔄 Générer Alertes'}
                </Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.helperText}>
              Seuil configuré : {settings.consecutiveAbsenceThreshold} absences consécutives
            </Text>

            {alerts.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>Aucune alerte active</Text>
                <Text style={styles.emptyStateSubtext}>
                  Cliquez sur "Générer Alertes" pour vérifier les absences consécutives
                </Text>
              </View>
            ) : (
              alerts.map((alert) => (
                <View key={alert.id} style={styles.alertCard}>
                  <View style={styles.alertHeader}>
                    <Text style={styles.alertCadetName}>
                      {alert.cadet_prenom} {alert.cadet_nom}
                    </Text>
                    <View style={[
                      styles.alertStatusBadge,
                      { backgroundColor: 
                        alert.status === 'active' ? '#ef4444' : 
                        alert.status === 'contacted' ? '#f59e0b' : 
                        '#10b981' 
                      }
                    ]}>
                      <Text style={styles.alertStatusText}>
                        {alert.status === 'active' ? 'Active' : 
                         alert.status === 'contacted' ? 'Contacté' : 
                         'Résolu'}
                      </Text>
                    </View>
                  </View>

                  <Text style={styles.alertDetails}>
                    🚨 {alert.consecutive_absences} absences consécutives
                  </Text>
                  
                  {alert.last_absence_date && (
                    <Text style={styles.alertDetails}>
                      📅 Dernière absence : {new Date(alert.last_absence_date).toLocaleDateString('fr-FR')}
                    </Text>
                  )}

                  {alert.contact_comment && (
                    <View style={styles.alertComment}>
                      <Text style={styles.alertCommentTitle}>💬 Commentaire :</Text>
                      <Text style={styles.alertCommentText}>{alert.contact_comment}</Text>
                    </View>
                  )}

                  {alert.contacted_at && (
                    <Text style={styles.alertMeta}>
                      Contacté le {new Date(alert.contacted_at).toLocaleDateString('fr-FR')}
                    </Text>
                  )}

                  {alert.resolved_at && (
                    <Text style={styles.alertMeta}>
                      Résolu le {new Date(alert.resolved_at).toLocaleDateString('fr-FR')}
                    </Text>
                  )}

                  <View style={styles.alertActions}>
                    {alert.status === 'active' && (
                      <TouchableOpacity
                        style={[styles.alertActionButton, {backgroundColor: '#f59e0b'}]}
                        onPress={() => openAlertModal(alert)}
                      >
                        <Text style={styles.alertActionText}>📞 Marquer comme contacté</Text>
                      </TouchableOpacity>
                    )}

                    {alert.status === 'contacted' && (
                      <TouchableOpacity
                        style={[styles.alertActionButton, {backgroundColor: '#10b981'}]}
                        onPress={() => {
                          setSelectedAlert(alert);
                          updateAlertStatus('resolved');
                        }}
                      >
                        <Text style={styles.alertActionText}>✅ Marquer comme résolu</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* Gestion des Rôles */}
        {activeTab === 'roles' && (
          <View style={styles.tabContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Gestion des Rôles et Permissions</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => openRoleModal()}
              >
                <Text style={styles.addButtonText}>+ Nouveau Rôle</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.helperText}>
              Créez des rôles personnalisés avec des permissions spécifiques
            </Text>

            {roles.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>Aucun rôle personnalisé créé</Text>
                <Text style={styles.emptyStateSubtext}>
                  Les rôles système (Cadet, Cadet Responsable, etc.) sont gérés automatiquement
                </Text>
              </View>
            ) : (
              roles.map((role) => (
                <View key={role.id} style={styles.roleCard}>
                  <View style={styles.roleHeader}>
                    <Text style={styles.roleName}>{role.name}</Text>
                    {role.is_system_role && (
                      <View style={styles.systemRoleBadge}>
                        <Text style={styles.systemRoleText}>Système</Text>
                      </View>
                    )}
                  </View>

                  {role.description && (
                    <Text style={styles.roleDescription}>{role.description}</Text>
                  )}

                  <Text style={styles.permissionsTitle}>Permissions :</Text>
                  <View style={styles.permissionsList}>
                    {role.permissions.map((permission, index) => (
                      <View key={index} style={styles.permissionTag}>
                        <Text style={styles.permissionText}>{permission.replace(/_/g, ' ')}</Text>
                      </View>
                    ))}
                  </View>

                  {!role.is_system_role && (
                    <View style={styles.roleActions}>
                      <TouchableOpacity
                        style={styles.editButton}
                        onPress={() => openRoleModal(role)}
                      >
                        <Text style={styles.editButtonText}>Modifier</Text>
                      </TouchableOpacity>
                    </View>
                  )}
                </View>
              ))
            )}
          </View>
        )}
      </ScrollView>

      {/* Modal pour créer/modifier un rôle */}
      <Modal
        visible={showRoleModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingRole ? 'Modifier le Rôle' : 'Nouveau Rôle'}
            </Text>
            <TouchableOpacity onPress={() => setShowRoleModal(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.formSection}>
              <Text style={styles.inputLabel}>Nom du rôle *</Text>
              <TextInput
                style={styles.input}
                value={roleForm.name}
                onChangeText={(text) => setRoleForm(prev => ({...prev, name: text}))}
                placeholder="Ex: Responsable Matériel"
              />

              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={roleForm.description}
                onChangeText={(text) => setRoleForm(prev => ({...prev, description: text}))}
                placeholder="Description des responsabilités de ce rôle"
                multiline
                numberOfLines={3}
              />

              <Text style={styles.inputLabel}>Permissions</Text>
              <Text style={styles.helperText}>
                Sélectionnez les actions autorisées pour ce rôle
              </Text>
              
              {/* Ici on devrait avoir la liste des permissions disponibles */}
              <View style={styles.comingSoonBox}>
                <Text style={styles.comingSoonText}>
                  Interface de sélection des permissions - En développement
                </Text>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.saveButton, savingRole && styles.saveButtonDisabled]}
              onPress={saveRole}
              disabled={savingRole}
            >
              <Text style={styles.saveButtonText}>
                {savingRole ? 'Sauvegarde...' : '💾 Sauvegarder le rôle'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Modal pour marquer une alerte comme contactée */}
      <Modal
        visible={showAlertModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Marquer comme contacté</Text>
            <TouchableOpacity onPress={() => setShowAlertModal(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.modalContent}>
            {selectedAlert && (
              <>
                <Text style={styles.modalSubtitle}>
                  {selectedAlert.cadet_prenom} {selectedAlert.cadet_nom}
                </Text>
                <Text style={styles.modalSubtitle}>
                  {selectedAlert.consecutive_absences} absences consécutives
                </Text>

                <Text style={styles.inputLabel}>Commentaire (visible aux autres administrateurs)</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={contactComment}
                  onChangeText={setContactComment}
                  placeholder="Décrivez les actions entreprises (contact parents, entretien avec le cadet, etc.)"
                  multiline
                  numberOfLines={4}
                />

                <TouchableOpacity
                  style={styles.saveButton}
                  onPress={() => updateAlertStatus('contacted', contactComment)}
                >
                  <Text style={styles.saveButtonText}>📞 Marquer comme contacté</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </SafeAreaView>
      </Modal>

      {/* Modal pour créer/modifier une activité */}
      <Modal
        visible={showActivityModal}
        animationType="slide"
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
                  <Text style={styles.inputLabel}>Date prévue *</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.planned_date}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, planned_date: text}))}
                    placeholder="2025-01-15"
                    placeholderTextColor="#9CA3AF"
                  />
                  <Text style={styles.helperText}>Format: YYYY-MM-DD</Text>
                </View>
              )}

              {activityForm.type === 'recurring' && (
                <View>
                  <Text style={styles.inputLabel}>Récurrence (en jours) *</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.recurrence_interval}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, recurrence_interval: text}))}
                    placeholder="7"
                    keyboardType="numeric"
                    placeholderTextColor="#9CA3AF"
                  />
                  <Text style={styles.helperText}>Ex: 7 pour chaque semaine, 14 pour toutes les 2 semaines</Text>
                  
                  <Text style={styles.inputLabel}>Prochaine occurrence</Text>
                  <TextInput
                    style={styles.input}
                    value={activityForm.next_date}
                    onChangeText={(text) => setActivityForm(prev => ({...prev, next_date: text}))}
                    placeholder="2025-01-15"
                    placeholderTextColor="#9CA3AF"
                  />
                  <Text style={styles.helperText}>Format: YYYY-MM-DD (optionnel)</Text>
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

            {/* Zone de suppression dangereuse - seulement en mode édition */}
            {editingActivity && (
              <View style={styles.dangerZone}>
                <Text style={styles.dangerZoneTitle}>🚨 Zone dangereuse</Text>
                <Text style={styles.dangerZoneText}>
                  La suppression d'une activité est définitive et irréversible.
                </Text>
                <TouchableOpacity
                  style={styles.dangerButton}
                  onPress={() => {
                    showConfirmation(
                      'Supprimer définitivement',
                      `Êtes-vous sûr de vouloir supprimer définitivement l'activité "${editingActivity.nom}" ?\n\n⚠️ Cette action est IRRÉVERSIBLE.\n\nTous les cadets assignés perdront cette activité de leur liste.`,
                      () => deleteActivity(editingActivity)
                    );
                  }}
                >
                  <Text style={styles.dangerButtonText}>🗑️ Supprimer définitivement cette activité</Text>
                </TouchableOpacity>
              </View>
            )}

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

      {/* Modal pour créer/modifier un utilisateur */}
      <Modal
        visible={showUserModal}
        animationType="slide"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingUser ? 'Modifier l\'Utilisateur' : 'Inviter un Utilisateur'}
            </Text>
            <TouchableOpacity onPress={() => setShowUserModal(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {/* Informations personnelles */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Informations personnelles</Text>
              
              <Text style={styles.inputLabel}>Prénom *</Text>
              <TextInput
                style={styles.input}
                value={userForm.prenom}
                onChangeText={(text) => setUserForm(prev => ({...prev, prenom: text}))}
                placeholder="Ex: Jean"
              />

              <Text style={styles.inputLabel}>Nom *</Text>
              <TextInput
                style={styles.input}
                value={userForm.nom}
                onChangeText={(text) => setUserForm(prev => ({...prev, nom: text}))}
                placeholder="Ex: Dupont"
              />

              <Text style={styles.inputLabel}>Email (optionnel)</Text>
              <TextInput
                style={styles.input}
                value={userForm.email}
                onChangeText={(text) => setUserForm(prev => ({...prev, email: text}))}
                placeholder="jean.dupont@exemple.com"
                keyboardType="email-address"
                autoCapitalize="none"
                editable={!editingUser} // Email non modifiable pour utilisateurs existants
              />
            </View>

            {/* Grade et rôle */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Grade et rôle</Text>
              
              <Text style={styles.inputLabel}>Grade *</Text>
              <Text style={styles.helperText}>Faites défiler horizontalement pour voir tous les grades</Text>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={true}
                contentContainerStyle={styles.scrollContent}
              >
                <View style={styles.optionsRow}>
                  {GRADES.map((grade) => (
                    <TouchableOpacity
                      key={grade.value}
                      style={[
                        styles.optionButton,
                        userForm.grade === grade.value && styles.optionButtonActive
                      ]}
                      onPress={() => setUserForm(prev => ({...prev, grade: grade.value}))}
                    >
                      <Text style={[
                        styles.optionButtonText,
                        userForm.grade === grade.value && styles.optionButtonTextActive
                      ]}>
                        {grade.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>

              <Text style={styles.inputLabel}>Rôle *</Text>
              <Text style={styles.helperText}>Faites défiler horizontalement pour voir tous les rôles</Text>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={true}
                contentContainerStyle={styles.scrollContent}
              >
                <View style={styles.optionsRow}>
                  {getAllRoles().map((role) => (
                    <TouchableOpacity
                      key={role.value}
                      style={[
                        styles.optionButton,
                        userForm.role === role.value && styles.optionButtonActive
                      ]}
                      onPress={() => setUserForm(prev => ({...prev, role: role.value}))}
                    >
                      <Text style={[
                        styles.optionButtonText,
                        userForm.role === role.value && styles.optionButtonTextActive
                      ]}>
                        {role.label}
                        {!role.isSystem && (
                          <Text style={{ fontSize: 10, color: '#6b7280' }}> (Personnalisé)</Text>
                        )}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>
            </View>

            {/* Section */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Affectation</Text>
              
              <Text style={styles.inputLabel}>Section</Text>
              <View style={styles.sectionSelector}>
                <TouchableOpacity
                  style={[
                    styles.sectionOption,
                    userForm.section_id === '' && styles.sectionOptionActive
                  ]}
                  onPress={() => setUserForm(prev => ({...prev, section_id: ''}))}
                >
                  <Text style={[
                    styles.sectionOptionText,
                    userForm.section_id === '' && styles.sectionOptionTextActive
                  ]}>
                    Aucune section
                  </Text>
                </TouchableOpacity>

                {sections.map((section) => (
                  <TouchableOpacity
                    key={section.id}
                    style={[
                      styles.sectionOption,
                      userForm.section_id === section.id && styles.sectionOptionActive
                    ]}
                    onPress={() => setUserForm(prev => ({...prev, section_id: section.id}))}
                  >
                    <Text style={[
                      styles.sectionOptionText,
                      userForm.section_id === section.id && styles.sectionOptionTextActive
                    ]}>
                      {section.nom}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Privilèges spéciaux */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Privilèges spéciaux</Text>
              
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Privilèges d'administration</Text>
                <Switch
                  value={userForm.has_admin_privileges}
                  onValueChange={(value) => setUserForm(prev => ({...prev, has_admin_privileges: value}))}
                  trackColor={{ false: '#d1d5db', true: '#34d399' }}
                  thumbColor={userForm.has_admin_privileges ? '#10b981' : '#9ca3af'}
                />
              </View>
              
              <Text style={styles.helperText}>
                Les privilèges d'administration permettent à ce cadet d'accéder aux fonctions administratives en plus de son rôle principal.
              </Text>
            </View>

            {/* Information sur l'invitation */}
            {!editingUser && (
              <View style={styles.infoSection}>
                <Text style={styles.infoTitle}>📧 Processus d'invitation</Text>
                <Text style={styles.infoText}>
                  Un email d'invitation sera envoyé à l'utilisateur avec un lien pour définir son mot de passe.
                  {'\n\n'}En mode test, le token d'invitation sera affiché pour permettre la simulation du processus.
                </Text>
              </View>
            )}

            {/* Zone de suppression dangereuse - uniquement pour utilisateurs existants */}
            {editingUser && (
              <View style={styles.dangerZone}>
                <Text style={styles.dangerZoneTitle}>🚨 Zone dangereuse</Text>
                <Text style={styles.dangerZoneText}>
                  La suppression d'un utilisateur est irréversible. Toutes ses données seront perdues définitivement.
                </Text>
                <TouchableOpacity
                  style={styles.dangerButton}
                  onPress={() => {
                    showConfirmation(
                      'Supprimer définitivement',
                      `Êtes-vous sûr de vouloir supprimer définitivement "${editingUser.prenom} ${editingUser.nom}" ?\n\n⚠️ Cette action est IRRÉVERSIBLE.\n\nToutes les données associées (présences, inspections, etc.) seront perdues.`,
                      () => deleteUser(editingUser)
                    );
                  }}
                >
                  <Text style={styles.dangerButtonText}>🗑️ Supprimer définitivement cet utilisateur</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Bouton de sauvegarde */}
            <TouchableOpacity
              style={[styles.saveButton, savingUser && styles.saveButtonDisabled]}
              onPress={saveUser}
              disabled={savingUser}
            >
              <Text style={styles.saveButtonText}>
                {savingUser ? 'Envoi en cours...' : editingUser ? 'Modifier l\'Utilisateur' : 'Envoyer l\'Invitation'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Modal pour créer/modifier une section */}
      <Modal
        visible={showSectionModal}
        animationType="slide"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingSection ? 'Modifier la Section' : 'Nouvelle Section'}
            </Text>
            <TouchableOpacity onPress={() => setShowSectionModal(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {/* Informations de base */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Informations de base</Text>
              
              <Text style={styles.inputLabel}>Nom de la section *</Text>
              <TextInput
                style={styles.input}
                value={sectionForm.nom}
                onChangeText={(text) => setSectionForm(prev => ({...prev, nom: text}))}
                placeholder="Ex: Section Alpha"
              />

              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={sectionForm.description}
                onChangeText={(text) => setSectionForm(prev => ({...prev, description: text}))}
                placeholder="Description de la section..."
                multiline
                numberOfLines={3}
              />
            </View>

            {/* Responsable de section */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Responsable de section</Text>
              
              <TouchableOpacity
                style={[
                  styles.sectionOption,
                  sectionForm.responsable_id === '' && styles.sectionOptionActive
                ]}
                onPress={() => setSectionForm(prev => ({...prev, responsable_id: ''}))}
              >
                <Text style={[
                  styles.sectionOptionText,
                  sectionForm.responsable_id === '' && styles.sectionOptionTextActive
                ]}>
                  Aucun responsable
                </Text>
              </TouchableOpacity>

              {users.filter(u => ['cadet_responsible', 'cadet_admin', 'encadrement'].includes(u.role)).map((user) => (
                <TouchableOpacity
                  key={user.id}
                  style={[
                    styles.sectionOption,
                    sectionForm.responsable_id === user.id && styles.sectionOptionActive
                  ]}
                  onPress={() => setSectionForm(prev => ({...prev, responsable_id: user.id}))}
                >
                  <View style={styles.responsableInfo}>
                    <Text style={[
                      styles.sectionOptionText,
                      sectionForm.responsable_id === user.id && styles.sectionOptionTextActive
                    ]}>
                      {user.prenom} {user.nom}
                    </Text>
                    <Text style={styles.responsableRole}>
                      {getRoleDisplayName(user.role)} - {getGradeDisplayName(user.grade)}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>

            {/* Information */}
            <View style={styles.infoSection}>
              <Text style={styles.infoTitle}>📋 À propos des sections</Text>
              <Text style={styles.infoText}>
                Les sections permettent d'organiser les cadets en groupes. Un responsable de section peut prendre les présences et gérer les cadets de sa section.
              </Text>
            </View>

            {/* Zone de suppression dangereuse - uniquement pour sections existantes */}
            {editingSection && (
              <View style={styles.dangerZone}>
                <Text style={styles.dangerZoneTitle}>🚨 Zone dangereuse</Text>
                <Text style={styles.dangerZoneText}>
                  La suppression d'une section est irréversible. Tous les cadets de cette section perdront leur affectation.
                </Text>
                <TouchableOpacity
                  style={styles.dangerButton}
                  onPress={() => {
                    showConfirmation(
                      'Supprimer définitivement',
                      `Êtes-vous sûr de vouloir supprimer définitivement la section "${editingSection.nom}" ?\n\n⚠️ Cette action est IRRÉVERSIBLE.\n\nTous les cadets de cette section perdront leur affectation.`,
                      () => deleteSection(editingSection)
                    );
                  }}
                >
                  <Text style={styles.dangerButtonText}>🗑️ Supprimer définitivement cette section</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Bouton de sauvegarde */}
            <TouchableOpacity
              style={[styles.saveButton, savingSection && styles.saveButtonDisabled]}
              onPress={saveSection}
              disabled={savingSection}
            >
              <Text style={styles.saveButtonText}>
                {savingSection ? 'Enregistrement...' : editingSection ? 'Modifier la Section' : 'Créer la Section'}
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
  // Styles pour les filtres utilisateurs
  filtersContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  filtersTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 12,
  },
  filtersRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  filterItem: {
    flex: 1,
    minWidth: 150,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
    marginBottom: 6,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    backgroundColor: '#f7fafc',
  },
  picker: {
    height: 40,
    color: '#2d3748',
  },
  resetFiltersButton: {
    backgroundColor: '#e2e8f0',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  resetFiltersText: {
    color: '#4a5568',
    fontSize: 14,
    fontWeight: '600',
  },
  // Styles pour la gestion des utilisateurs
  userCard: {
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
  userHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  userInfo: {
    flex: 1,
    marginRight: 10,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
    marginBottom: 2,
  },
  adminBadge: {
    fontSize: 12,
    fontWeight: '700',
    color: '#dc2626',
    textTransform: 'uppercase',
  },
  userEmail: {
    fontSize: 14,
    color: '#4a5568',
  },
  userBadges: {
    alignItems: 'flex-end',
  },
  roleBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  roleBadgeText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '600',
  },
  userDetails: {
    marginBottom: 12,
    gap: 4,
  },
  userDetail: {
    fontSize: 14,
    color: '#4a5568',
  },
  userActions: {
    flexDirection: 'row',
    gap: 10,
  },
  // Styles pour le modal utilisateur
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
    paddingBottom: 10,
  },
  scrollContent: {
    paddingRight: 20, // Espace à droite pour le scroll
  },
  optionButton: {
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: 'white',
  },
  optionButtonActive: {
    borderColor: '#3182ce',
    backgroundColor: '#ebf8ff',
  },
  optionButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4a5568',
  },
  optionButtonTextActive: {
    color: '#3182ce',
  },
  sectionSelector: {
    gap: 8,
  },
  sectionOption: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#f7fafc',
  },
  sectionOptionActive: {
    borderColor: '#3182ce',
    backgroundColor: '#ebf8ff',
  },
  sectionOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4a5568',
  },
  sectionOptionTextActive: {
    color: '#3182ce',
  },
  infoSection: {
    backgroundColor: '#f0f9ff',
    borderRadius: 10,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#3182ce',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1e40af',
    lineHeight: 20,
  },
  // Styles pour les sections
  sectionCard: {
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
  sectionCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionCardName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    flex: 1,
    marginRight: 10,
  },
  sectionCardDescription: {
    fontSize: 14,
    color: '#4a5568',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  sectionCardInfo: {
    fontSize: 14,
    color: '#2d3748',
    marginBottom: 4,
  },
  sectionActions: {
    flexDirection: 'row',
    gap: 8,
  },
  responsableInfo: {
    flex: 1,
  },
  responsableRole: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  // Styles pour la zone de suppression dangereuse
  dangerZone: {
    backgroundColor: '#fef2f2',
    borderRadius: 10,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#dc2626',
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  dangerZoneTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#dc2626',
    marginBottom: 8,
  },
  dangerZoneText: {
    fontSize: 14,
    color: '#991b1b',
    lineHeight: 20,
    marginBottom: 16,
  },
  dangerButton: {
    backgroundColor: '#dc2626',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  dangerButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  userStatus: {
    fontSize: 12,
    color: '#f59e0b',
    fontStyle: 'italic',
    marginTop: 2,
  },
  statusBadge: {
    backgroundColor: '#f59e0b',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 4,
  },
  statusBadgeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
  },
  // Styles pour les DatePickers
  datePickerButton: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  datePickerText: {
    fontSize: 16,
    color: '#374151',
    flex: 1,
  },
  helperText: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 15,
    fontStyle: 'italic',
  },
  // Styles pour les paramètres
  settingsSection: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  settingsGroupTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 15,
  },
  settingItem: {
    marginBottom: 15,
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 5,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  criterionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 10,
  },
  removeButton: {
    backgroundColor: '#ef4444',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  addCriterionButton: {
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  addCriterionText: {
    color: '#6b7280',
    fontSize: 14,
    fontWeight: '500',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  backupButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  backupButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  tenueGroup: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  tenueHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  tenueTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  removeTenueButton: {
    backgroundColor: '#ef4444',
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeTenueButtonText: {
    fontSize: 16,
  },
  newTenueSection: {
    backgroundColor: '#f0f9ff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#0ea5e9',
  },
  newTenueInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  addNewTenueButton: {
    backgroundColor: '#0ea5e9',
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  addNewTenueButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  // Styles pour les filtres utilisateurs
  filtersContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  filtersTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 12,
  },
  filtersRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  filterItem: {
    flex: 1,
    minWidth: 150,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
    marginBottom: 6,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    backgroundColor: '#f7fafc',
  },
  picker: {
    height: 40,
    color: '#2d3748',
  },
  resetFiltersButton: {
    backgroundColor: '#e2e8f0',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  resetFiltersText: {
    color: '#4a5568',
    fontSize: 14,
    fontWeight: '600',
  },
  // Styles pour les alertes
  alertCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  alertCadetName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  alertStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  alertStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  alertDetails: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 5,
  },
  alertComment: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
    marginBottom: 10,
  },
  alertCommentTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 5,
  },
  alertCommentText: {
    fontSize: 14,
    color: '#4b5563',
    fontStyle: 'italic',
  },
  alertMeta: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  alertActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  alertActionButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  alertActionText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  // Styles pour les rôles
  roleCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  roleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  roleName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  systemRoleBadge: {
    backgroundColor: '#6b7280',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  systemRoleText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  roleDescription: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 10,
    fontStyle: 'italic',
  },
  permissionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  permissionsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 15,
  },
  permissionTag: {
    backgroundColor: '#dbeafe',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  permissionText: {
    fontSize: 12,
    color: '#1d4ed8',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  roleActions: {
    flexDirection: 'row',
    gap: 10,
  },
  editButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 6,
  },
  editButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  comingSoonBox: {
    backgroundColor: '#fef3c7',
    borderWidth: 1,
    borderColor: '#f59e0b',
    borderRadius: 8,
    padding: 15,
    marginVertical: 10,
  },
  comingSoonText: {
    color: '#92400e',
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});