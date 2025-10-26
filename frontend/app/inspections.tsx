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
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { ConnectionIndicator } from '../components/ConnectionIndicator';
import { useOfflineMode } from '../hooks/useOfflineMode';
import * as offlineService from '../services/offlineService';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  nom: string;
  prenom: string;
  grade: string;
  role: string;
  section_id?: string;
}

interface Section {
  id: string;
  nom: string;
  responsable_id?: string;
}

interface Settings {
  inspectionCriteria: {
    [uniformType: string]: string[];
  };
}

interface UniformSchedule {
  id?: string;
  date: string;
  uniform_type: string | null;
  set_by?: string;
  set_at?: string;
  message?: string;
}

interface UniformInspection {
  id: string;
  cadet_id: string;
  cadet_nom: string;
  cadet_prenom: string;
  cadet_grade: string;
  date: string;
  uniform_type: string;
  criteria_scores: { [criterion: string]: number };  // Changé de boolean à number
  max_score: number;
  total_score: number;
  commentaire?: string;
  inspected_by: string;
  inspector_name: string;
  inspection_time: string;
  section_id?: string;
  section_nom?: string;
  auto_marked_present: boolean;
}

interface InspectionStats {
  cadet_id: string;
  cadet_nom: string;
  cadet_prenom: string;
  total_inspections: number;
  personal_average: number;
  section_average: number;
  squadron_average: number;
  recent_inspections: UniformInspection[];
  best_score: number;
  worst_score: number;
}

export default function Inspections() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Hook mode hors ligne
  const { isOnline, isSyncing, syncQueueCount, handleManualSync } = useOfflineMode();
  
  // Données
  const [cadets, setCadets] = useState<User[]>([]); 
  const [sections, setSections] = useState<Section[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [todaySchedule, setTodaySchedule] = useState<UniformSchedule | null>(null);
  const [recentInspections, setRecentInspections] = useState<UniformInspection[]>([]);
  
  // États pour l'inspection
  const [showInspectionModal, setShowInspectionModal] = useState(false);
  const [selectedCadet, setSelectedCadet] = useState<User | null>(null);
  const [criteriaScores, setCriteriaScores] = useState<{ [key: string]: number }>({});  // 0-4 points
  const [inspectionComment, setInspectionComment] = useState('');
  const [savingInspection, setSavingInspection] = useState(false);
  const [inspectionUniformType, setInspectionUniformType] = useState(''); // Type d'uniforme choisi pour l'inspection
  
  // États pour la programmation de tenue
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedUniformType, setSelectedUniformType] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');
  const [savingSchedule, setSavingSchedule] = useState(false);
  
  // États pour le modal de détail d'inspection
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedInspection, setSelectedInspection] = useState<UniformInspection | null>(null);
  
  // Permissions
  const [canScheduleUniform, setCanScheduleUniform] = useState(false);
  const [canInspect, setCanInspect] = useState(false);
  
  // États pour la vue cadet (statistiques personnelles)
  const [myStats, setMyStats] = useState<InspectionStats | null>(null);
  const [isViewingMyStats, setIsViewingMyStats] = useState(false);

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
        checkPermissions(parsedUser);
        
        // Charger les données en passant l'utilisateur
        await loadAllData(parsedUser);
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

  const checkPermissions = (currentUser: User) => {
    const role = currentUser.role.toLowerCase();
    
    // Permission pour programmer la tenue: Adjudants, Officiers, Encadrement
    const canScheduleKeywords = ['adjudant', 'officier', 'lieutenant', 'capitaine', 'commandant', 'encadrement', 'cadet_admin'];
    setCanScheduleUniform(canScheduleKeywords.some(keyword => role.includes(keyword)));
    
    // Permission pour inspecter: Chefs de section et supérieurs
    const canInspectKeywords = ['chef', 'sergent', 'adjudant', 'officier', 'commandant', 'responsible', 'admin', 'encadrement'];
    setCanInspect(canInspectKeywords.some(keyword => role.includes(keyword)));
  };

  const loadAllData = async (currentUser: User) => {
    // Si l'utilisateur est un cadet régulier, charger uniquement ses stats
    if (currentUser && currentUser.role === 'cadet') {
      console.log('📊 Chargement des stats pour cadet:', currentUser.prenom, currentUser.nom);
      await loadMyStats();
      setIsViewingMyStats(true);
    } else {
      // Sinon, charger toutes les données pour les inspecteurs
      await Promise.all([
        loadCadets(),
        loadSections(),
        loadSettings(),
        loadTodaySchedule(),
        loadRecentInspections()
      ]);
    }
  };

  const loadMyStats = async () => {
    try {
      console.log('🔍 Appel API stats/me...');
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-inspections/stats/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      console.log('📥 Réponse stats/me:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Stats reçues:', data);
        setMyStats(data);
      } else {
        console.error('❌ Erreur lors du chargement des statistiques:', response.status);
      }
    } catch (error) {
      console.error('❌ Erreur lors du chargement des statistiques:', error);
    }
  };

  const loadCadets = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        
        // Filtrer pour exclure uniquement les vrais officiers et l'encadrement
        let filteredCadets = data.filter((u: User) => {
          const roleLower = u.role.toLowerCase();
          
          // Exclure l'encadrement et les admins
          if (roleLower.includes('encadrement') || roleLower.includes('admin')) {
            return false;
          }
          
          // Exclure les officiers SAUF "Commandant de..." (Garde, Musique)
          if (roleLower.includes('lieutenant') || 
              roleLower.includes('capitaine') || 
              roleLower.includes('major') || 
              roleLower.includes('colonel')) {
            return false;
          }
          
          // Pour "commandant", exclure seulement si ce n'est PAS "commandant de"
          if (roleLower.includes('commandant') && !roleLower.includes('commandant de')) {
            return false;
          }
          
          return true;
        });

        // Assigner une section virtuelle "État-Major" aux adjudants d'escadron sans section
        filteredCadets = filteredCadets.map((cadet: User) => {
          const roleLower = cadet.role.toLowerCase();
          // Si c'est un adjudant d'escadron sans section, lui assigner l'état-major virtuel
          if (!cadet.section_id && 
              (roleLower.includes('adjudant d\'escadron') || 
               roleLower.includes('adjudant-chef d\'escadron') ||
               roleLower.includes('adjudant chef d\'escadron'))) {
            return {
              ...cadet,
              section_id: 'etat-major-virtual',
            };
          }
          return cadet;
        });

        // Filtrer selon le rôle de l'utilisateur connecté
        if (user) {
          const userRoleLower = user.role.toLowerCase();
          const isEtatMajor = user.section_id === 'etat-major-virtual' || 
                              userRoleLower.includes('adjudant d\'escadron') ||
                              userRoleLower.includes('adjudant-chef d\'escadron') ||
                              userRoleLower.includes('adjudant chef d\'escadron');

          if (isEtatMajor) {
            // État-Major peut inspecter tout le monde SAUF soi-même
            filteredCadets = filteredCadets.filter((c: User) => c.id !== user.id);
          } else if (userRoleLower.includes('commandant') || userRoleLower.includes('sergent')) {
            // Commandants/Sergents de section peuvent inspecter seulement leur section SAUF soi-même
            filteredCadets = filteredCadets.filter((c: User) => 
              c.section_id === user.section_id && c.id !== user.id
            );
          } else {
            // Autres utilisateurs ne voient personne (sécurité)
            filteredCadets = filteredCadets.filter((c: User) => c.id !== user.id);
          }
        }

        console.log(`📋 ${filteredCadets.length} cadets inspectables chargés`);
        setCadets(filteredCadets);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des cadets:', error);
    }
  };

  const loadSections = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSections(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des sections:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const timestamp = new Date().getTime();
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/settings?t=${timestamp}`, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        console.log('✅ Settings chargés dans inspections:', Object.keys(data.inspectionCriteria || {}));
      }
    } catch (error) {
      console.error('Erreur lors du chargement des paramètres:', error);
    }
  };

  const loadTodaySchedule = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-schedule?date_param=${today}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTodaySchedule(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la tenue du jour:', error);
    }
  };

  const loadRecentInspections = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const today = new Date().toISOString().split('T')[0];
      console.log(`🔍 Chargement inspections pour la date: ${today}`);
      
      const url = `${EXPO_PUBLIC_BACKEND_URL}/api/uniform-inspections?date=${today}`;
      console.log(`🌐 URL: ${url}`);
      
      const response = await fetch(url, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        },
      });

      console.log(`📥 Statut réponse: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`📊 Inspections reçues: ${data.length} inspections`);
        console.log('📋 Cadets inspectés:', data.map((i: any) => `${i.cadet_nom} ${i.cadet_prenom}`));
        setRecentInspections(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des inspections:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAllData();
    setRefreshing(false);
  };

  const openScheduleModal = () => {
    const today = new Date().toISOString().split('T')[0];
    setScheduleDate(today);
    setSelectedUniformType('');
    setShowScheduleModal(true);
  };

  const saveSchedule = async () => {
    if (!selectedUniformType) {
      Alert.alert('Erreur', 'Veuillez sélectionner un type de tenue');
      return;
    }

    setSavingSchedule(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          date: scheduleDate,
          uniform_type: selectedUniformType
        }),
      });

      if (response.ok) {
        console.log('✅ Tenue programmée avec succès');
        Alert.alert('Succès', 'Tenue programmée avec succès');
        setShowScheduleModal(false);
        await loadTodaySchedule();
        await loadRecentInspections(); // Recharger les inspections pour réinitialiser la liste
        console.log('✅ Tenue du jour et inspections rechargées');
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de la programmation');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible de programmer la tenue');
    } finally {
      setSavingSchedule(false);
    }
  };

  const openInspectionModal = (cadet: User) => {
    setSelectedCadet(cadet);
    
    // Utiliser la tenue du jour si disponible, sinon laisser vide pour que l'utilisateur choisisse
    const uniformType = todaySchedule?.uniform_type || '';
    setInspectionUniformType(uniformType);
    
    // Initialiser les scores des critères à 0 (barème de 0 à 4)
    if (uniformType && settings?.inspectionCriteria[uniformType]) {
      const criteria = settings.inspectionCriteria[uniformType];
      const initialScores: { [key: string]: number } = {};
      criteria.forEach(criterion => {
        initialScores[criterion] = 0;
      });
      setCriteriaScores(initialScores);
      
      console.log(`🔍 Ouverture inspection pour ${cadet.nom} ${cadet.prenom}`);
      console.log(`👔 Tenue: ${uniformType}`);
      console.log(`📋 Critères chargés:`, criteria);
    } else {
      // Pas de tenue sélectionnée, les critères seront chargés après sélection
      setCriteriaScores({});
      console.log(`🔍 Ouverture inspection pour ${cadet.nom} ${cadet.prenom} - Aucune tenue sélectionnée`);
    }
    
    setInspectionComment('');
    setShowInspectionModal(true);
  };

  const updateCriterionScore = (criterion: string, score: number) => {
    setCriteriaScores(prev => ({
      ...prev,
      [criterion]: score
    }));
  };

  const handleUniformTypeChange = (uniformType: string) => {
    setInspectionUniformType(uniformType);
    
    // Charger les critères pour ce type d'uniforme
    if (uniformType && settings?.inspectionCriteria[uniformType]) {
      const criteria = settings.inspectionCriteria[uniformType];
      const initialScores: { [key: string]: number } = {};
      criteria.forEach(criterion => {
        initialScores[criterion] = 0;
      });
      setCriteriaScores(initialScores);
      console.log(`👔 Tenue changée: ${uniformType}`);
      console.log(`📋 Critères chargés:`, criteria);
    } else {
      setCriteriaScores({});
    }
  };

  const calculateScore = () => {
    const total = Object.keys(criteriaScores).length;
    if (total === 0) return 0;
    const obtained = Object.values(criteriaScores).reduce((sum, score) => sum + score, 0);
    const maxScore = total * 4;
    return Math.round((obtained / maxScore) * 100);
  };

  const saveInspection = async () => {
    if (!selectedCadet || !inspectionUniformType) {
      Alert.alert('Erreur', 'Veuillez sélectionner un type de tenue');
      return;
    }

    console.log('💾 Début sauvegarde inspection pour cadet:', selectedCadet.nom, selectedCadet.prenom);
    console.log(`📶 Statut connexion: ${isOnline ? 'EN LIGNE' : 'HORS LIGNE'}`);
    
    setSavingInspection(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      
      // Si hors ligne, utiliser le service offline
      if (!isOnline) {
        const result = await offlineService.recordUniformInspection(
          selectedCadet.id,
          today,
          inspectionUniformType,
          criteriaScores,
          inspectionComment || undefined
        );
        
        if (result.success && result.offline) {
          Alert.alert(
            '📦 Enregistré hors ligne',
            `Inspection de ${selectedCadet.prenom} ${selectedCadet.nom} enregistrée localement.\n\nElle sera synchronisée automatiquement au retour de la connexion.\n\nNote: La présence sera confirmée lors de la synchronisation.`
          );
          
          setShowInspectionModal(false);
          setSelectedCadet(null);
          
          // Ajouter l'inspection à la liste locale temporairement
          const tempInspection: UniformInspection = {
            id: `temp_${Date.now()}`,
            cadet_id: selectedCadet.id,
            cadet_nom: selectedCadet.nom,
            cadet_prenom: selectedCadet.prenom,
            cadet_grade: selectedCadet.grade,
            date: today,
            uniform_type: inspectionUniformType,
            criteria_scores: criteriaScores,
            max_score: Object.keys(criteriaScores).length * 4,
            total_score: calculateScore(),
            commentaire: inspectionComment || undefined,
            inspected_by: user?.id || '',
            inspector_name: `${user?.prenom} ${user?.nom}`,
            inspection_time: new Date().toISOString(),
            section_id: selectedCadet.section_id,
            auto_marked_present: false
          };
          
          setRecentInspections(prev => [...prev, tempInspection]);
          return;
        }
      }
      
      // Mode en ligne - envoyer directement au backend
      const token = await AsyncStorage.getItem('access_token');
      
      const requestBody = {
        cadet_id: selectedCadet.id,
        uniform_type: inspectionUniformType,
        criteria_scores: criteriaScores,
        commentaire: inspectionComment || null
      };
      
      console.log('📤 Envoi requête:', JSON.stringify(requestBody));
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-inspections?inspection_date=${today}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      console.log('📥 Réponse statut:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Inspection sauvegardée:', result);
        
        let message = `Inspection enregistrée avec succès\nScore: ${result.total_score}%`;
        
        if (result.auto_marked_present) {
          message += '\n\n⚠️ Le cadet a été automatiquement marqué présent suite à cette inspection';
        }
        
        Alert.alert('Succès', message);
        setShowInspectionModal(false);
        setSelectedCadet(null);
        
        console.log('🔄 Rechargement des inspections...');
        await loadRecentInspections();
        console.log('✅ Inspections rechargées');
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      console.error('❌ Erreur saveInspection:', error);
      console.error('❌ Erreur détails:', JSON.stringify(error));
      console.error('❌ Stack:', error instanceof Error ? error.stack : 'N/A');
      Alert.alert('Erreur', `Impossible d'enregistrer l'inspection: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    } finally {
      setSavingInspection(false);
    }
  };

  const getCadetsBySection = () => {
    const grouped: { [sectionId: string]: User[] } = {};
    
    cadets.forEach(cadet => {
      const sectionId = cadet.section_id || 'no_section';
      if (!grouped[sectionId]) {
        grouped[sectionId] = [];
      }
      grouped[sectionId].push(cadet);
    });
    
    return grouped;
  };

  const getSectionName = (sectionId: string) => {
    if (sectionId === 'no_section') return 'Sans section';
    const section = sections.find(s => s.id === sectionId);
    return section?.nom || 'Section inconnue';
  };

  const getGradeDisplayName = (grade: string) => {
    const gradeMap: { [key: string]: string } = {
      'cadet': 'Cadet',
      'cadet_air_1re_classe': 'Cadet de l\'air 1re classe',
      'caporal': 'Caporal',
      'caporal_section': 'Caporal de section',
      'sergent': 'Sergent',
      'sergent_section': 'Sergent de section',
      'adjudant_2e_classe': 'Adjudant de 2e classe',
      'adjudant_1re_classe': 'Adjudant de 1re classe',
    };
    return gradeMap[grade] || grade;
  };

  const isAlreadyInspected = (cadetId: string) => {
    return recentInspections.some(insp => insp.cadet_id === cadetId);
  };

  const openInspectionDetail = (inspection: UniformInspection) => {
    setSelectedInspection(inspection);
    setShowDetailModal(true);
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

  if (!canInspect && !isViewingMyStats) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Retour</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Inspections</Text>
        </View>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#3182ce" />
          <Text style={styles.loadingText}>Chargement de vos statistiques...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Vue spéciale pour les cadets réguliers
  if (isViewingMyStats && myStats) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Retour</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Mes Inspections</Text>
        </View>

        <ScrollView
          style={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
          {/* Vue d'ensemble des statistiques */}
          <View style={styles.statsOverviewCard}>
            <Text style={styles.statsTitle}>📊 Mes Statistiques d'Inspection</Text>
            <Text style={styles.statsSubtitle}>
              {myStats.total_inspections} inspection{myStats.total_inspections > 1 ? 's' : ''} effectuée{myStats.total_inspections > 1 ? 's' : ''}
            </Text>
          </View>

          {/* Cartes de comparaison */}
          <View style={styles.comparisonContainer}>
            {/* Ma moyenne */}
            <View style={[styles.statCard, styles.personalStatCard]}>
              <Text style={styles.statLabel}>Ma Moyenne</Text>
              <Text style={styles.statValue}>{myStats.personal_average.toFixed(1)}%</Text>
              <View style={styles.scoreRange}>
                <Text style={styles.scoreRangeText}>
                  Meilleur: {myStats.best_score.toFixed(1)}%
                </Text>
                <Text style={styles.scoreRangeText}>
                  Plus bas: {myStats.worst_score.toFixed(1)}%
                </Text>
              </View>
            </View>

            {/* Moyenne de la section */}
            <View style={[styles.statCard, styles.sectionStatCard]}>
              <Text style={styles.statLabel}>Moyenne Section</Text>
              <Text style={styles.statValue}>{myStats.section_average.toFixed(1)}%</Text>
              {myStats.personal_average >= myStats.section_average ? (
                <Text style={styles.comparisonText}>
                  ✅ Au-dessus de la moyenne
                </Text>
              ) : (
                <Text style={styles.comparisonTextBellow}>
                  📈 En dessous de {(myStats.section_average - myStats.personal_average).toFixed(1)}%
                </Text>
              )}
            </View>

            {/* Moyenne de l'escadron */}
            <View style={[styles.statCard, styles.squadronStatCard]}>
              <Text style={styles.statLabel}>Moyenne Escadron</Text>
              <Text style={styles.statValue}>{myStats.squadron_average.toFixed(1)}%</Text>
              {myStats.personal_average >= myStats.squadron_average ? (
                <Text style={styles.comparisonText}>
                  ✅ Au-dessus de la moyenne
                </Text>
              ) : (
                <Text style={styles.comparisonTextBellow}>
                  📈 En dessous de {(myStats.squadron_average - myStats.personal_average).toFixed(1)}%
                </Text>
              )}
            </View>
          </View>

          {/* Historique des inspections */}
          <View style={styles.historyCard}>
            <Text style={styles.historyTitle}>📋 Mes Dernières Inspections</Text>
            {myStats.recent_inspections.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>Aucune inspection enregistrée</Text>
              </View>
            ) : (
              myStats.recent_inspections.map((inspection) => (
                <TouchableOpacity
                  key={inspection.id}
                  style={styles.inspectionHistoryItem}
                  onPress={() => {
                    setSelectedInspection(inspection);
                    setShowDetailModal(true);
                  }}
                >
                  <View style={styles.inspectionHistoryHeader}>
                    <Text style={styles.inspectionDate}>
                      {new Date(inspection.date).toLocaleDateString('fr-CA')}
                    </Text>
                    <View style={[
                      styles.scoreBadge,
                      inspection.total_score >= 85 ? styles.scoreExcellent :
                      inspection.total_score >= 70 ? styles.scoreGood :
                      inspection.total_score >= 50 ? styles.scoreFair : styles.scorePoor
                    ]}>
                      <Text style={styles.scoreBadgeText}>
                        {inspection.total_score.toFixed(1)}%
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.inspectionUniform}>{inspection.uniform_type}</Text>
                  <Text style={styles.inspectionInspector}>
                    Inspecté par: {inspection.inspector_name}
                  </Text>
                  {inspection.commentaire && (
                    <Text style={styles.inspectionComment} numberOfLines={2}>
                      💬 {inspection.commentaire}
                    </Text>
                  )}
                </TouchableOpacity>
              ))
            )}
          </View>
        </ScrollView>

        {/* Modal de détail d'inspection */}
        {showDetailModal && selectedInspection && (
          <Modal visible={showDetailModal} transparent animationType="slide">
            <View style={styles.modalOverlay}>
              <View style={styles.detailModalContent}>
                <ScrollView>
                  <Text style={styles.detailModalTitle}>Détail de l'Inspection</Text>
                  
                  <View style={styles.detailSection}>
                    <Text style={styles.detailLabel}>Date:</Text>
                    <Text style={styles.detailValue}>
                      {new Date(selectedInspection.date).toLocaleDateString('fr-CA')}
                    </Text>
                  </View>

                  <View style={styles.detailSection}>
                    <Text style={styles.detailLabel}>Type de tenue:</Text>
                    <Text style={styles.detailValue}>{selectedInspection.uniform_type}</Text>
                  </View>

                  <View style={styles.detailSection}>
                    <Text style={styles.detailLabel}>Score total:</Text>
                    <Text style={[styles.detailValue, styles.detailScore]}>
                      {selectedInspection.total_score.toFixed(1)}%
                    </Text>
                  </View>

                  <View style={styles.detailSection}>
                    <Text style={styles.detailLabel}>Inspecté par:</Text>
                    <Text style={styles.detailValue}>{selectedInspection.inspector_name}</Text>
                  </View>

                  <View style={styles.detailSection}>
                    <Text style={styles.detailLabel}>Détail des critères:</Text>
                    {Object.entries(selectedInspection.criteria_scores).map(([criterion, score]) => (
                      <View key={criterion} style={styles.criterionRow}>
                        <Text style={styles.criterionName}>{criterion}</Text>
                        <Text style={styles.criterionScore}>{score}/4</Text>
                      </View>
                    ))}
                  </View>

                  {selectedInspection.commentaire && (
                    <View style={styles.detailSection}>
                      <Text style={styles.detailLabel}>Commentaire:</Text>
                      <Text style={styles.detailCommentText}>
                        {selectedInspection.commentaire}
                      </Text>
                    </View>
                  )}
                </ScrollView>

                <TouchableOpacity
                  style={styles.closeModalButton}
                  onPress={() => setShowDetailModal(false)}
                >
                  <Text style={styles.closeModalButtonText}>Fermer</Text>
                </TouchableOpacity>
              </View>
            </View>
          </Modal>
        )}
      </SafeAreaView>
    );
  }

  const cadetsBySection = getCadetsBySection();
  const uniformTypes = settings ? Object.keys(settings.inspectionCriteria) : [];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Retour</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Inspections d'Uniformes</Text>
      </View>

      {/* Indicateur de connexion */}
      <View style={styles.connectionIndicatorContainer}>
        <ConnectionIndicator 
          isOnline={isOnline}
          isSyncing={isSyncing}
          syncQueueCount={syncQueueCount}
          onSync={handleManualSync}
        />
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Tenue du jour */}
        <View style={styles.scheduleCard}>
          <View style={styles.scheduleHeader}>
            <Text style={styles.scheduleTitle}>👔 Tenue du jour</Text>
            <View style={{flexDirection: 'row', gap: 8}}>
              {canScheduleUniform && (
                <TouchableOpacity style={styles.scheduleButton} onPress={openScheduleModal}>
                  <Text style={styles.scheduleButtonText}>Programmer</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity 
                style={[styles.scheduleButton, {backgroundColor: '#ef4444'}]} 
                onPress={async () => {
                  console.log('🔄 Réinitialisation complète...');
                  
                  // Vider le state
                  setRecentInspections([]);
                  
                  // Vider le cache AsyncStorage des inspections
                  try {
                    const keys = await AsyncStorage.getAllKeys();
                    console.log('🔑 Clés AsyncStorage:', keys);
                    
                    // Supprimer toutes les clés liées aux inspections
                    const inspectionKeys = keys.filter(key => 
                      key.includes('inspection') || 
                      key.includes('sync_queue') ||
                      key.includes('cache')
                    );
                    
                    if (inspectionKeys.length > 0) {
                      console.log('🗑️ Suppression des clés:', inspectionKeys);
                      await AsyncStorage.multiRemove(inspectionKeys);
                      console.log('✅ Cache AsyncStorage vidé');
                    }
                  } catch (error) {
                    console.error('❌ Erreur vidage AsyncStorage:', error);
                  }
                  
                  // Forcer le rechargement des settings
                  await loadSettings();
                  
                  Alert.alert('Réinitialisé', 'Liste vidée et cache nettoyé');
                }}
              >
                <Text style={styles.scheduleButtonText}>Réinitialiser</Text>
              </TouchableOpacity>
            </View>
          </View>
          
          {todaySchedule?.uniform_type ? (
            <View style={styles.scheduleInfo}>
              <Text style={styles.scheduleType}>{todaySchedule.uniform_type}</Text>
              <Text style={styles.scheduleDate}>
                {new Date().toLocaleDateString('fr-FR', { 
                  weekday: 'long', 
                  day: 'numeric', 
                  month: 'long', 
                  year: 'numeric' 
                })}
              </Text>
            </View>
          ) : (
            <View style={styles.noSchedule}>
              <Text style={styles.noScheduleText}>⚠️ Aucune tenue programmée pour aujourd'hui</Text>
              {canScheduleUniform && (
                <Text style={styles.noScheduleSubtext}>
                  Programmez la tenue pour commencer les inspections
                </Text>
              )}
            </View>
          )}
        </View>

        {/* Liste des cadets par section */}
        {todaySchedule?.uniform_type && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Cadets à inspecter</Text>
            
            {Object.entries(cadetsBySection).map(([sectionId, sectionCadets]) => (
              <View key={sectionId} style={styles.sectionGroup}>
                <Text style={styles.sectionGroupTitle}>{getSectionName(sectionId)}</Text>
                
                {sectionCadets.map(cadet => {
                  const inspected = isAlreadyInspected(cadet.id);
                  
                  return (
                    <TouchableOpacity
                      key={cadet.id}
                      style={[styles.cadetCard, inspected && styles.cadetCardInspected]}
                      onPress={() => !inspected && openInspectionModal(cadet)}
                      disabled={inspected}
                    >
                      <View style={styles.cadetInfo}>
                        <Text style={styles.cadetName}>
                          {getGradeDisplayName(cadet.grade)} {cadet.nom} {cadet.prenom}
                        </Text>
                        {inspected && (
                          <View style={styles.inspectedBadge}>
                            <Text style={styles.inspectedBadgeText}>✓ Inspecté</Text>
                          </View>
                        )}
                      </View>
                      {!inspected && (
                        <Text style={styles.cadetAction}>Inspecter →</Text>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            ))}
          </View>
        )}

        {/* Inspections récentes */}
        {recentInspections.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Inspections du jour ({recentInspections.length})</Text>
            
            {recentInspections.map(inspection => (
              <TouchableOpacity 
                key={inspection.id} 
                style={styles.inspectionCard}
                onPress={() => openInspectionDetail(inspection)}
                activeOpacity={0.7}
              >
                <View style={styles.inspectionHeader}>
                  <Text style={styles.inspectionCadet}>
                    {getGradeDisplayName(inspection.cadet_grade)} {inspection.cadet_nom} {inspection.cadet_prenom}
                  </Text>
                  <View style={[
                    styles.scoreBadge,
                    { backgroundColor: inspection.total_score >= 80 ? '#10b981' : inspection.total_score >= 60 ? '#f59e0b' : '#ef4444' }
                  ]}>
                    <Text style={styles.scoreBadgeText}>{inspection.total_score}%</Text>
                  </View>
                </View>
                
                <Text style={styles.inspectionUniform}>{inspection.uniform_type}</Text>
                <Text style={styles.inspectionInspector}>Par: {inspection.inspector_name}</Text>
                
                {inspection.auto_marked_present && (
                  <View style={styles.autoPresenceBadge}>
                    <Text style={styles.autoPresenceText}>⚠️ Marqué présent automatiquement</Text>
                  </View>
                )}
                
                {inspection.commentaire && (
                  <Text style={styles.inspectionComment}>{inspection.commentaire}</Text>
                )}
                
                <Text style={styles.tapToSeeDetail}>👆 Appuyer pour voir le détail</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Modal de programmation de tenue */}
      <Modal
        visible={showScheduleModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowScheduleModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Programmer la tenue</Text>
            
            <Text style={styles.label}>Date</Text>
            <TextInput
              style={styles.input}
              value={scheduleDate}
              onChangeText={setScheduleDate}
              placeholder="YYYY-MM-DD"
            />
            
            <Text style={styles.label}>Type de tenue</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={selectedUniformType}
                onValueChange={setSelectedUniformType}
                style={styles.picker}
              >
                <Picker.Item label="Sélectionner une tenue..." value="" />
                {uniformTypes.map(type => (
                  <Picker.Item key={type} label={type} value={type} />
                ))}
              </Picker>
            </View>
            
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowScheduleModal(false)}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.saveButton}
                onPress={saveSchedule}
                disabled={savingSchedule}
              >
                {savingSchedule ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.saveButtonText}>Enregistrer</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Modal d'inspection */}
      <Modal
        visible={showInspectionModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowInspectionModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalTitle}>Inspection d'uniforme</Text>
            
            {selectedCadet && (
              <>
                <Text style={styles.modalSubtitle}>
                  {getGradeDisplayName(selectedCadet.grade)} {selectedCadet.nom} {selectedCadet.prenom}
                </Text>
                <Text style={styles.modalUniform}>{todaySchedule?.uniform_type}</Text>
                
                <View style={styles.criteriaSection}>
                  <Text style={styles.criteriaTitle}>Critères d'inspection (Barème: 0-4 points)</Text>
                  <Text style={styles.criteriaSubtitle}>
                    0 = Très mauvais | 1 = Mauvais | 2 = Passable | 3 = Bon | 4 = Excellent
                  </Text>
                  
                  {Object.keys(criteriaScores).map(criterion => (
                    <View key={criterion} style={styles.criterionContainer}>
                      <Text style={styles.criterionLabel}>{criterion}</Text>
                      
                      <View style={styles.scoreButtons}>
                        {[0, 1, 2, 3, 4].map(score => (
                          <TouchableOpacity
                            key={score}
                            style={[
                              styles.scoreButton,
                              criteriaScores[criterion] === score && styles.scoreButtonSelected,
                              score === 0 && styles.scoreButton0,
                              score === 1 && styles.scoreButton1,
                              score === 2 && styles.scoreButton2,
                              score === 3 && styles.scoreButton3,
                              score === 4 && styles.scoreButton4,
                            ]}
                            onPress={() => updateCriterionScore(criterion, score)}
                          >
                            <Text style={[
                              styles.scoreButtonText,
                              criteriaScores[criterion] === score && styles.scoreButtonTextSelected
                            ]}>
                              {score}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </View>
                    </View>
                  ))}
                </View>
                
                <View style={styles.scoreDisplay}>
                  <Text style={styles.scoreLabel}>Score calculé:</Text>
                  <Text style={styles.scoreValue}>{calculateScore()}%</Text>
                </View>
                
                <Text style={styles.label}>Commentaire (optionnel)</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={inspectionComment}
                  onChangeText={setInspectionComment}
                  placeholder="Remarques sur l'inspection..."
                  multiline
                  numberOfLines={3}
                />
                
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => {
                      setShowInspectionModal(false);
                      setSelectedCadet(null);
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Annuler</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={styles.saveButton}
                    onPress={saveInspection}
                    disabled={savingInspection}
                  >
                    {savingInspection ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.saveButtonText}>Enregistrer</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>

      {/* Modal de détail d'inspection */}
      <Modal
        visible={showDetailModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowDetailModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView style={styles.detailModalScroll}>
              {selectedInspection && (
                <>
                  {/* En-tête */}
                  <View style={styles.detailHeader}>
                    <Text style={styles.detailTitle}>Détail de l'inspection</Text>
                    <TouchableOpacity 
                      onPress={() => setShowDetailModal(false)}
                      style={styles.closeButton}
                    >
                      <Text style={styles.closeButtonText}>✕</Text>
                    </TouchableOpacity>
                  </View>

                  {/* Informations du cadet */}
                  <View style={styles.detailSection}>
                    <Text style={styles.detailSectionTitle}>Cadet</Text>
                    <Text style={styles.detailCadetName}>
                      {getGradeDisplayName(selectedInspection.cadet_grade)} {selectedInspection.cadet_nom} {selectedInspection.cadet_prenom}
                    </Text>
                    {selectedInspection.section_nom && (
                      <Text style={styles.detailSectionName}>{selectedInspection.section_nom}</Text>
                    )}
                  </View>

                  {/* Tenue et Score */}
                  <View style={styles.detailSection}>
                    <Text style={styles.detailSectionTitle}>Tenue inspectée</Text>
                    <Text style={styles.detailUniformType}>{selectedInspection.uniform_type}</Text>
                    
                    <View style={styles.detailScoreContainer}>
                      <Text style={styles.detailScoreLabel}>Score total:</Text>
                      <View style={[
                        styles.detailScoreBadge,
                        { backgroundColor: selectedInspection.total_score >= 80 ? '#10b981' : selectedInspection.total_score >= 60 ? '#f59e0b' : '#ef4444' }
                      ]}>
                        <Text style={styles.detailScoreText}>{selectedInspection.total_score}%</Text>
                      </View>
                    </View>
                  </View>

                  {/* Détail des critères */}
                  <View style={styles.detailSection}>
                    <Text style={styles.detailSectionTitle}>Détail des critères (sur 4 points)</Text>
                    {Object.entries(selectedInspection.criteria_scores).map(([criterion, score]) => (
                      <View key={criterion} style={styles.criteriaDetailRow}>
                        <Text style={styles.criteriaDetailName}>{criterion}</Text>
                        <View style={styles.criteriaDetailScoreContainer}>
                          <View style={[
                            styles.criteriaDetailScoreBadge,
                            { 
                              backgroundColor: 
                                score === 4 ? '#059669' :
                                score === 3 ? '#10b981' : 
                                score === 2 ? '#fbbf24' : 
                                score === 1 ? '#f97316' : '#dc2626'
                            }
                          ]}>
                            <Text style={styles.criteriaDetailScoreText}>{score}/4</Text>
                          </View>
                          <Text style={styles.criteriaDetailScoreLabel}>
                            {score === 4 ? 'Excellent' :
                             score === 3 ? 'Bien' : 
                             score === 2 ? 'Moyen' : 
                             score === 1 ? 'Faible' : 'Insuffisant'}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>

                  {/* Commentaire */}
                  {selectedInspection.commentaire && (
                    <View style={styles.detailSection}>
                      <Text style={styles.detailSectionTitle}>Commentaire</Text>
                      <Text style={styles.detailComment}>{selectedInspection.commentaire}</Text>
                    </View>
                  )}

                  {/* Informations supplémentaires */}
                  <View style={styles.detailSection}>
                    <Text style={styles.detailSectionTitle}>Informations</Text>
                    <Text style={styles.detailInfo}>Inspecté par: {selectedInspection.inspector_name}</Text>
                    <Text style={styles.detailInfo}>
                      Date: {new Date(selectedInspection.inspection_time).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Text>
                    {selectedInspection.auto_marked_present && (
                      <View style={styles.autoPresenceBadge}>
                        <Text style={styles.autoPresenceText}>⚠️ Marqué présent automatiquement</Text>
                      </View>
                    )}
                  </View>
                </>
              )}
            </ScrollView>

            <TouchableOpacity 
              style={styles.closeModalButton}
              onPress={() => setShowDetailModal(false)}
            >
              <Text style={styles.closeModalButtonText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  content: {
    flex: 1,
    padding: 16,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  errorText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ef4444',
    marginBottom: 8,
  },
  errorSubtext: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
  scheduleCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  scheduleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  scheduleTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  scheduleButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  scheduleButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  scheduleInfo: {
    paddingTop: 8,
  },
  scheduleType: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 4,
  },
  scheduleDate: {
    fontSize: 14,
    color: '#6b7280',
  },
  noSchedule: {
    padding: 16,
    backgroundColor: '#fef3c7',
    borderRadius: 8,
  },
  noScheduleText: {
    fontSize: 16,
    color: '#92400e',
    fontWeight: '600',
    marginBottom: 4,
  },
  noScheduleSubtext: {
    fontSize: 14,
    color: '#92400e',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 12,
  },
  sectionGroup: {
    marginBottom: 16,
  },
  sectionGroupTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4b5563',
    marginBottom: 8,
    paddingLeft: 4,
  },
  cadetCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cadetCardInspected: {
    backgroundColor: '#f3f4f6',
    opacity: 0.7,
  },
  cadetInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cadetName: {
    fontSize: 16,
    color: '#1f2937',
  },
  inspectedBadge: {
    backgroundColor: '#10b981',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  inspectedBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  cadetAction: {
    color: '#3b82f6',
    fontSize: 14,
    fontWeight: '600',
  },
  inspectionCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  inspectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  inspectionCadet: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
  },
  scoreBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  scoreBadgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  inspectionUniform: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  inspectionInspector: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 8,
  },
  autoPresenceBadge: {
    backgroundColor: '#fef3c7',
    padding: 8,
    borderRadius: 6,
    marginBottom: 8,
  },
  autoPresenceText: {
    fontSize: 12,
    color: '#92400e',
    fontWeight: '600',
  },
  inspectionComment: {
    fontSize: 14,
    color: '#4b5563',
    fontStyle: 'italic',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    padding: 16,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    maxHeight: '90%',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3b82f6',
    marginBottom: 4,
  },
  modalUniform: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1f2937',
    backgroundColor: '#fff',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  criteriaSection: {
    marginVertical: 16,
  },
  criteriaTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  criteriaSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 12,
    fontStyle: 'italic',
  },
  criterionContainer: {
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  criterionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  scoreButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  scoreButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#d1d5db',
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  scoreButtonSelected: {
    borderWidth: 3,
  },
  scoreButton0: {
    borderColor: '#ef4444',
  },
  scoreButton1: {
    borderColor: '#f97316',
  },
  scoreButton2: {
    borderColor: '#eab308',
  },
  scoreButton3: {
    borderColor: '#84cc16',
  },
  scoreButton4: {
    borderColor: '#10b981',
  },
  scoreButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4b5563',
  },
  scoreButtonTextSelected: {
    color: '#1f2937',
  },
  criterionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#fff',
  },
  criterionCardConforming: {
    borderColor: '#10b981',
    backgroundColor: '#d1fae5',
  },
  criterionText: {
    fontSize: 14,
    color: '#4b5563',
    flex: 1,
  },
  criterionTextConforming: {
    color: '#065f46',
    fontWeight: '600',
  },
  criterionStatus: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  scoreDisplay: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#eff6ff',
    padding: 16,
    borderRadius: 8,
    marginVertical: 12,
  },
  scoreLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e40af',
  },
  scoreValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e40af',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#4b5563',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  connectionIndicatorContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#f9fafb',
  },
  tapToSeeDetail: {
    marginTop: 8,
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  detailModalScroll: {
    flex: 1,
  },
  detailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  detailTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 18,
    color: '#6b7280',
    fontWeight: 'bold',
  },
  detailSection: {
    marginBottom: 24,
    padding: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
  },
  detailSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  detailCadetName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  detailSectionName: {
    fontSize: 14,
    color: '#6b7280',
  },
  detailUniformType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  detailScoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  detailScoreLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4b5563',
  },
  detailScoreBadge: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
  },
  detailScoreText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  criteriaDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  criteriaDetailName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#1f2937',
    flex: 1,
  },
  criteriaDetailScoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  criteriaDetailScoreBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    minWidth: 50,
    alignItems: 'center',
  },
  criteriaDetailScoreText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
  },
  criteriaDetailScoreLabel: {
    fontSize: 13,
    color: '#6b7280',
    fontWeight: '500',
  },
  detailComment: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
    fontStyle: 'italic',
  },
  detailInfo: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  closeModalButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  closeModalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Styles pour la vue cadet
  statsOverviewCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  statsSubtitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  comparisonContainer: {
    marginBottom: 16,
  },
  statCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  personalStatCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  sectionStatCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#10b981',
  },
  squadronStatCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  scoreRange: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  scoreRangeText: {
    fontSize: 12,
    color: '#6b7280',
  },
  comparisonText: {
    fontSize: 14,
    color: '#10b981',
    fontWeight: '600',
  },
  comparisonTextBellow: {
    fontSize: 14,
    color: '#f59e0b',
    fontWeight: '600',
  },
  historyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  historyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  emptyState: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#9ca3af',
  },
  inspectionHistoryItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  inspectionHistoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  inspectionDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  scoreBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreExcellent: {
    backgroundColor: '#d1fae5',
  },
  scoreGood: {
    backgroundColor: '#dbeafe',
  },
  scoreFair: {
    backgroundColor: '#fef3c7',
  },
  scorePoor: {
    backgroundColor: '#fee2e2',
  },
  scoreBadgeText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  inspectionUniform: {
    fontSize: 14,
    color: '#3b82f6',
    marginBottom: 4,
  },
  inspectionInspector: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  inspectionComment: {
    fontSize: 12,
    color: '#4b5563',
    fontStyle: 'italic',
    marginTop: 4,
  },
  detailModalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    maxHeight: '80%',
    width: '90%',
  },
  detailModalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  detailSection: {
    marginBottom: 16,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 16,
    color: '#1f2937',
  },
  detailScore: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  criterionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  criterionName: {
    fontSize: 14,
    color: '#4b5563',
  },
  criterionScore: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3b82f6',
  },
  detailCommentText: {
    fontSize: 14,
    color: '#4b5563',
    fontStyle: 'italic',
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
});
