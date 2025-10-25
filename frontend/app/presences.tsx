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
  Switch,
  ActivityIndicator,
  RefreshControl
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { ConnectionIndicator } from '../components/ConnectionIndicator';
import { useOfflineMode } from '../hooks/useOfflineMode';
import { addToSyncQueue, getCacheData, recordPresence, getConnectionStatus } from '../services/offlineService';
import { SwipeableAttendance } from '../components/SwipeableAttendance';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

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
}

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

interface Presence {
  id: string;
  cadet_id: string;
  cadet_nom: string;
  cadet_prenom: string;
  date: string;
  status: 'present' | 'absent' | 'retard';
  commentaire?: string;
  enregistre_par: string;
  heure_enregistrement: string;
  section_id?: string;
  section_nom?: string;
  activite?: string;
}

interface Section {
  id: string;
  nom: string;
  description?: string;
  responsable_id?: string;
  created_at?: string;
}

interface PresenceStats {
  total_seances: number;
  presences: number;
  absences: number;
  absences_excusees: number;  
  retards: number;
  taux_presence: number;
}

export default function Presences() {
  const [user, setUser] = useState<User | null>(null);
  const [presences, setPresences] = useState<Presence[]>([]);
  const [cadets, setCadets] = useState<User[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Hook pour le mode hors ligne
  const { isOnline, isSyncing, syncQueueCount, handleManualSync, refreshCache } = useOfflineMode();
  
  // États pour la prise de présence
  const [showTakeAttendance, setShowTakeAttendance] = useState(false);
  const [showNewAttendance, setShowNewAttendance] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [activite, setActivite] = useState('');
  const [attendanceData, setAttendanceData] = useState<{[key: string]: {status: string, commentaire: string}}>({});
  const [savingAttendance, setSavingAttendance] = useState(false);
  const [selectedCadets, setSelectedCadets] = useState<Set<string>>(new Set());
  const [attendanceMode, setAttendanceMode] = useState<'all' | 'selected' | 'activity'>('all');
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);

  // États pour les statistiques
  const [showStats, setShowStats] = useState(false);
  const [selectedCadetStats, setSelectedCadetStats] = useState<string | null>(null);
  const [stats, setStats] = useState<PresenceStats | null>(null);

  // États pour les groupements collapsibles
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showActivityDetail, setShowActivityDetail] = useState(false);

  // États pour l'ajout d'invités
  const [showAddGuest, setShowAddGuest] = useState(false);
  const [guestNom, setGuestNom] = useState('');
  const [guestPrenom, setGuestPrenom] = useState('');
  const [guestCommentaire, setGuestCommentaire] = useState('');
  const [savingGuest, setSavingGuest] = useState(false);
  const [selectedActivityDetail, setSelectedActivityDetail] = useState<{activite: string, date: string, presences: Presence[]} | null>(null);

  // Constantes pour l'affichage
  const MAX_CADETS_PREVIEW = 5;

  useEffect(() => {
    loadUserAndData();
    // Rafraîchir le cache périodiquement si en ligne
    const interval = setInterval(() => {
      if (isOnline) {
        refreshCache();
      }
    }, 300000); // Toutes les 5 minutes
    
    return () => clearInterval(interval);
  }, [isOnline]);

  const loadUserAndData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        
        // Télécharger et mettre en cache les données si en ligne
        if (isOnline) {
          await refreshCache();
        }
        
        await loadPresences(parsedUser);
        
        // Charger les cadets si l'utilisateur peut prendre les présences
        if (['cadet_responsible', 'cadet_admin', 'encadrement'].includes(parsedUser.role)) {
          await loadSections();
          await loadCadets(parsedUser);
          await loadActivities(parsedUser);
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
      Alert.alert('Erreur', 'Impossible de charger les données');
    } finally {
      setLoading(false);
    }
  };

  const loadPresences = async (currentUser: User) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/presences`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPresences(data);
      } else {
        console.error('Erreur lors du chargement des présences');
      }
    } catch (error) {
      console.error('Erreur réseau:', error);
    }
  };

  const loadCadets = async (currentUser: User) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Filtrer pour ne montrer que les cadets selon les permissions
        let filteredCadets = data.filter((u: User) => 
          ['cadet', 'cadet_responsible'].includes(u.role)
        );

        if (currentUser.role === 'cadet_responsible') {
          // Un cadet responsable ne voit que sa section
          filteredCadets = filteredCadets.filter((c: User) => 
            c.section_id === currentUser.section_id
          );
        }

        setCadets(filteredCadets);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des cadets:', error);
    }
  };

  const loadActivities = async (currentUser: User) => {
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

  const onRefresh = async () => {
    setRefreshing(true);
    if (user) {
      await loadPresences(user);
      if (['cadet_responsible', 'cadet_admin', 'encadrement'].includes(user.role)) {
        await loadSections();
        await loadCadets(user);
        await loadActivities(user);
      }
    }
    setRefreshing(false);
  };

  const getStatusDisplayName = (status: string) => {
    switch (status) {
      case 'present': return 'Présent';
      case 'absent': return 'Absent';
      case 'retard': return 'Retard';
      default: return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present': return '#10b981';
      case 'absent': return '#ef4444';
      case 'retard': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  const openTakeAttendance = () => {
    // Réinitialiser les états
    setSelectedCadets(new Set());
    setAttendanceData({});
    setAttendanceMode('all');
    setShowTakeAttendance(true);
  };

  const initializeAttendanceData = (mode: 'all' | 'selected' | 'individual') => {
    const initialData: {[key: string]: {status: string, commentaire: string}} = {};
    
    if (mode === 'all') {
      cadets.forEach(cadet => {
        initialData[cadet.id] = { status: 'present', commentaire: '' };
      });
    } else if (mode === 'selected') {
      Array.from(selectedCadets).forEach(cadetId => {
        initialData[cadetId] = { status: 'present', commentaire: '' };
      });
    }
    
    setAttendanceData(initialData);
  };

  const toggleCadetSelection = (cadetId: string) => {
    const newSelected = new Set(selectedCadets);
    if (newSelected.has(cadetId)) {
      newSelected.delete(cadetId);
    } else {
      newSelected.add(cadetId);
    }
    setSelectedCadets(newSelected);
  };

  const selectAllCadets = () => {
    setSelectedCadets(new Set(cadets.map(c => c.id)));
  };

  const clearSelection = () => {
    setSelectedCadets(new Set());
  };

  const updateAttendanceStatus = (cadetId: string, status: string) => {
    setAttendanceData(prev => ({
      ...prev,
      [cadetId]: { ...prev[cadetId], status }
    }));
  };

  const updateAttendanceComment = (cadetId: string, commentaire: string) => {
    setAttendanceData(prev => ({
      ...prev,
      [cadetId]: { ...prev[cadetId], commentaire }
    }));
  };

  const saveAttendance = async () => {
    // Vérifier qu'il y a des cadets sélectionnés
    const cadetsToSave = Object.keys(attendanceData);
    if (cadetsToSave.length === 0) {
      Alert.alert('Erreur', 'Aucun cadet sélectionné pour la prise de présence');
      return;
    }

    setSavingAttendance(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Préparer les données pour l'API
      const presencesData = cadetsToSave.map(cadetId => ({
        cadet_id: cadetId,
        status: attendanceData[cadetId].status,
        commentaire: attendanceData[cadetId].commentaire || null
      }));

      // Vérifier si on est en ligne
      if (!isOnline) {
        // Mode hors ligne : enregistrer localement dans la queue
        let offlineSavedCount = 0;
        for (const presence of presencesData) {
          await addToSyncQueue({
            type: 'presence',
            data: {
              cadet_id: presence.cadet_id,
              date: selectedDate,
              status: presence.status as 'present' | 'absent' | 'retard',
              commentaire: presence.commentaire || undefined,
              timestamp: new Date().toISOString(),
              temp_id: `presence_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            },
            attempts: 0,
            created_at: new Date().toISOString()
          });
          offlineSavedCount++;
        }
        
        Alert.alert(
          '📴 Mode Hors Ligne', 
          `${offlineSavedCount} présence(s) enregistrée(s) localement.\n\nElles seront synchronisées automatiquement quand la connexion sera restaurée.`
        );
        setShowTakeAttendance(false);
        setAttendanceData({});
        return;
      }

      // Mode en ligne : enregistrer directement sur le serveur
      const payload = {
        date: selectedDate,
        activite: activite || null,
        presences: presencesData
      };

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/presences/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        Alert.alert(
          'Succès', 
          `${result.created_count} présences enregistrées${result.errors.length > 0 ? `\n${result.errors.length} erreur(s)` : ''}`
        );
        setShowTakeAttendance(false);
        await loadPresences(user!);
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      console.error('Erreur lors de l\'enregistrement:', error);
      
      // Si erreur réseau en mode en ligne, proposer d'enregistrer localement
      if (!isOnline) {
        Alert.alert(
          'Erreur de connexion',
          'Pas de connexion internet. Les présences ont été enregistrées localement et seront synchronisées plus tard.',
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert('Erreur', 'Impossible d\'enregistrer les présences');
      }
    } finally {
      setSavingAttendance(false);
    }
  };

  // ============================================================================
  // NOUVELLES FONCTIONS POUR SWIPE ATTENDANCE
  // ============================================================================

  const openNewAttendance = () => {
    setShowNewAttendance(true);
  };

  const handleSaveGuest = async () => {
    // Validation
    if (!guestNom.trim() || !guestPrenom.trim()) {
      Alert.alert('Erreur', 'Le nom et le prénom sont requis');
      return;
    }

    setSavingGuest(true);

    try {
      const token = await AsyncStorage.getItem('access_token');
      
      const response = await fetch(
        `${EXPO_PUBLIC_BACKEND_URL}/api/presences?presence_date=${selectedDate}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            cadet_id: 'guest_temp', // Sera remplacé par le backend
            status: 'present',
            commentaire: guestCommentaire || `Invité: ${guestPrenom} ${guestNom}`,
            is_guest: true,
            guest_nom: guestNom,
            guest_prenom: guestPrenom
          }),
        }
      );

      if (response.ok) {
        Alert.alert('Succès', `Présence de l'invité ${guestPrenom} ${guestNom} enregistrée`);
        setShowAddGuest(false);
        setGuestNom('');
        setGuestPrenom('');
        setGuestCommentaire('');
        await loadPresences(); // Recharger les présences
      } else {
        const error = await response.json();
        Alert.alert('Erreur', error.detail || 'Impossible d\'enregistrer l\'invité');
      }
    } catch (error) {
      console.error('Erreur lors de l\'enregistrement de l\'invité:', error);
      Alert.alert('Erreur', 'Impossible d\'enregistrer l\'invité');
    } finally {
      setSavingGuest(false);
    }
  };

  const handleSwipeAttendanceComplete = async (presentIds: string[]) => {
    console.log('🎯 handleSwipeAttendanceComplete appelé avec:', presentIds.length, 'présents');
    setSavingAttendance(true);
    setShowNewAttendance(false);

    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Créer les données de présence : présents + absents (tous les autres)
      const allCadetIds = cadets.map(c => c.id);
      const absentIds = allCadetIds.filter(id => !presentIds.includes(id));
      
      console.log('📊 Total cadets:', allCadetIds.length, '| Présents:', presentIds.length, '| Absents:', absentIds.length);
      
      const presencesData = [
        ...presentIds.map(id => ({ cadet_id: id, status: 'present', commentaire: null })),
        ...absentIds.map(id => ({ cadet_id: id, status: 'absent', commentaire: null }))
      ];

      // Vérifier si on est en ligne
      if (!isOnline) {
        // Mode hors ligne : enregistrer localement
        console.log('📴 Mode hors ligne - enregistrement local');
        for (const presence of presencesData) {
          await addToSyncQueue({
            type: 'presence',
            data: {
              cadet_id: presence.cadet_id,
              date: selectedDate,
              status: presence.status as 'present' | 'absent',
              commentaire: undefined,
              timestamp: new Date().toISOString(),
              temp_id: `presence_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            },
            attempts: 0,
            created_at: new Date().toISOString()
          });
        }
        
        Alert.alert(
          '📴 Mode Hors Ligne', 
          `${presencesData.length} présence(s) enregistrée(s) localement.\n\n${presentIds.length} présent(s), ${absentIds.length} absent(s)`
        );
        await loadPresences(user!);
        return;
      }

      // Mode en ligne : enregistrer sur le serveur
      console.log('🌐 Mode en ligne - envoi au serveur');
      const payload = {
        date: selectedDate,
        activite: activite || null,
        presences: presencesData
      };

      console.log('📤 Envoi payload:', JSON.stringify(payload).substring(0, 200));
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/presences/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      console.log('📥 Réponse serveur:', response.status, response.ok);

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Succès:', result);
        Alert.alert(
          '✅ Succès', 
          `${result.created_count} présences enregistrées\n\n${presentIds.length} présent(s), ${absentIds.length} absent(s)`
        );
        await loadPresences(user!);
      } else {
        const errorData = await response.json();
        console.log('❌ Erreur serveur:', errorData);
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      console.error('❌ Erreur lors de l\'enregistrement:', error);
      Alert.alert('Erreur', 'Impossible d\'enregistrer les présences');
    } finally {
      setSavingAttendance(false);
    }
  };

  const loadStats = async (cadetId: string) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/presences/stats/${cadetId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
        setSelectedCadetStats(cadetId);
        setShowStats(true);
      } else {
        Alert.alert('Erreur', 'Impossible de charger les statistiques');
      }
    } catch (error) {
      console.error('Erreur lors du chargement des stats:', error);
      Alert.alert('Erreur', 'Erreur réseau');
    }
  };

  const canTakeAttendance = user && ['cadet_responsible', 'cadet_admin', 'encadrement'].includes(user.role);

  const toggleGroupExpansion = (groupKey: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey);
    } else {
      newExpanded.add(groupKey);
    }
    setExpandedGroups(newExpanded);
  };

  const openActivityDetail = (activite: string, date: string, presences: Presence[]) => {
    setSelectedActivityDetail({ activite, date, presences });
    setShowActivityDetail(true);
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
        <Text style={styles.title}>Gestion des Présences</Text>
      </View>

      {/* Indicateur de connexion et synchronisation */}
      <View style={styles.connectionIndicatorContainer}>
        <ConnectionIndicator 
          onSyncPress={async () => {
            const result = await handleManualSync();
            Alert.alert(
              result.success ? 'Succès' : 'Erreur',
              result.message
            );
          }}
        />
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Actions */}
        {canTakeAttendance && (
          <View style={styles.actionsContainer}>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={openNewAttendance}
            >
              <Text style={styles.primaryButtonText}>📝 Prise Rapide (Swipe)</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.secondaryButton}
              onPress={openTakeAttendance}
            >
              <Text style={styles.secondaryButtonText}>Prise Détaillée</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Statistiques rapides */}
        {user?.role === 'cadet' && (
          <TouchableOpacity 
            style={styles.statsCard}
            onPress={() => loadStats(user.id)}
          >
            <Text style={styles.statsTitle}>Mes Statistiques</Text>
            <Text style={styles.statsDescription}>Cliquez pour voir vos statistiques de présence</Text>
          </TouchableOpacity>
        )}

        {/* Liste des présences récentes organisées par activité */}
        <View style={styles.presencesContainer}>
          <Text style={styles.sectionTitle}>Présences par Activité</Text>
          
          {presences.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>Aucune présence enregistrée</Text>
            </View>
          ) : (
            (() => {
              // Grouper les présences par activité et date
              const groupedPresences = presences.reduce((acc, presence) => {
                const key = `${presence.activite || 'Activité générale'}_${presence.date}`;
                if (!acc[key]) {
                  acc[key] = {
                    activite: presence.activite || 'Activité générale',
                    date: presence.date,
                    presences: []
                  };
                }
                acc[key].presences.push(presence);
                return acc;
              }, {} as Record<string, {activite: string, date: string, presences: Presence[]}>);

              return Object.values(groupedPresences)
                .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                .map((group, groupIndex) => {
                  const groupKey = `${group.activite}_${group.date}`;
                  const isExpanded = expandedGroups.has(groupKey);
                  const shouldShowPreview = group.presences.length > MAX_CADETS_PREVIEW;
                  const displayedPresences = shouldShowPreview && !isExpanded 
                    ? group.presences.slice(0, MAX_CADETS_PREVIEW)
                    : group.presences;
                  
                  return (
                    <View key={groupIndex} style={styles.activityGroup}>
                      {/* En-tête de l'activité avec boutons d'action */}
                      <TouchableOpacity 
                        style={styles.activityGroupHeader}
                        onPress={() => shouldShowPreview && toggleGroupExpansion(groupKey)}
                      >
                        <View style={styles.activityInfo}>
                          <View style={styles.activityTitleRow}>
                            <Text style={styles.activityGroupTitle}>{group.activite}</Text>
                            {shouldShowPreview && (
                              <Text style={styles.expandIcon}>
                                {isExpanded ? '▼' : '▶'}
                              </Text>
                            )}
                          </View>
                          <Text style={styles.activityGroupDate}>
                            {new Date(group.date).toLocaleDateString('fr-FR', {
                              weekday: 'long',
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            })}
                          </Text>
                        </View>
                        <View style={styles.activityActions}>
                          <View style={styles.activityStats}>
                            <Text style={styles.participantCount}>{group.presences.length} cadets</Text>
                            <Text style={styles.presenceStats}>
                              {group.presences.filter(p => p.status === 'present').length} présents • {' '}
                              {group.presences.filter(p => p.status === 'absent').length} absents
                            </Text>
                          </View>
                          <TouchableOpacity
                            style={styles.detailButton}
                            onPress={() => openActivityDetail(group.activite, group.date, group.presences)}
                          >
                            <Text style={styles.detailButtonText}>Détail</Text>
                          </TouchableOpacity>
                        </View>
                      </TouchableOpacity>

                      {/* Liste des cadets (compacte ou complète) */}
                      <View style={styles.cadetsGrid}>
                        {displayedPresences.map((presence) => (
                          <View key={presence.id} style={styles.cadetPresenceCard}>
                            <View style={styles.cadetHeader}>
                              <Text style={styles.cadetName}>
                                {presence.cadet_prenom} {presence.cadet_nom}
                              </Text>
                              <View style={[
                                styles.statusBadge,
                                { backgroundColor: getStatusColor(presence.status) }
                              ]}>
                                <Text style={styles.statusText}>
                                  {getStatusDisplayName(presence.status)}
                                </Text>
                              </View>
                            </View>
                            
                            {presence.commentaire && (
                              <Text style={styles.presenceComment}>
                                💬 {presence.commentaire}
                              </Text>
                            )}

                            {/* Bouton stats pour admin/encadrement */}
                            {user && ['cadet_admin', 'encadrement'].includes(user.role) && (
                              <TouchableOpacity 
                                style={styles.statsButton}
                                onPress={() => loadStats(presence.cadet_id)}
                              >
                                <Text style={styles.statsButtonText}>Stats</Text>
                              </TouchableOpacity>
                            )}
                          </View>
                        ))}

                        {/* Indicateur "Voir plus" si nécessaire */}
                        {shouldShowPreview && !isExpanded && (
                          <TouchableOpacity 
                            style={styles.showMoreButton}
                            onPress={() => toggleGroupExpansion(groupKey)}
                          >
                            <Text style={styles.showMoreText}>
                              ▼ Voir {group.presences.length - MAX_CADETS_PREVIEW} cadets de plus
                            </Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>
                  )
                })
            })()
          )}
        </View>
      </ScrollView>

      {/* Modal de prise de présence */}
      <Modal
        visible={showTakeAttendance}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Prendre les Présences</Text>
            <TouchableOpacity onPress={() => setShowTakeAttendance(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {/* Configuration de la séance */}
            <View style={styles.sessionConfig}>
              <Text style={styles.inputLabel}>Date</Text>
              <TextInput
                style={styles.input}
                value={selectedDate}
                onChangeText={setSelectedDate}
                placeholder="YYYY-MM-DD"
              />

              <Text style={styles.inputLabel}>Activité (optionnel)</Text>
              <TextInput
                style={styles.input}
                value={activite}
                onChangeText={setActivite}
                placeholder="Ex: Entraînement, Parade, etc."
              />

              {/* Sélecteur de mode */}
              <Text style={styles.inputLabel}>Mode de prise de présence</Text>
              <View style={styles.modeSelector}>
                <TouchableOpacity
                  style={[styles.modeButton, attendanceMode === 'all' && styles.modeButtonActive]}
                  onPress={() => {
                    setAttendanceMode('all');
                    initializeAttendanceData('all');
                  }}
                >
                  <Text style={[styles.modeButtonText, attendanceMode === 'all' && styles.modeButtonTextActive]}>
                    Tous les cadets
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.modeButton, attendanceMode === 'selected' && styles.modeButtonActive]}
                  onPress={() => {
                    setAttendanceMode('selected');
                    setAttendanceData({});
                  }}
                >
                  <Text style={[styles.modeButtonText, attendanceMode === 'selected' && styles.modeButtonTextActive]}>
                    Sélection de cadets
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.modeButton, attendanceMode === 'activity' && styles.modeButtonActive]}
                  onPress={() => {
                    setAttendanceMode('activity');
                    setAttendanceData({});
                    setSelectedActivity(null);
                  }}
                >
                  <Text style={[styles.modeButtonText, attendanceMode === 'activity' && styles.modeButtonTextActive]}>
                    Liste d'activité
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Bouton pour ajouter un invité */}
            <TouchableOpacity 
              style={styles.addGuestButtonInModal}
              onPress={() => {
                setShowTakeAttendance(false);
                setShowAddGuest(true);
              }}
            >
              <Text style={styles.addGuestButtonText}>👤 Ajouter un Invité</Text>
            </TouchableOpacity>

            {/* Interface de sélection des cadets pour le mode 'selected' */}
            {attendanceMode === 'selected' && (
              <View style={styles.selectionInterface}>
                <View style={styles.selectionHeader}>
                  <Text style={styles.sectionTitle}>Sélectionner les cadets ({selectedCadets.size}/{cadets.length})</Text>
                </View>
                
                <View style={styles.selectionButtons}>
                  <TouchableOpacity style={styles.smallButton} onPress={selectAllCadets}>
                    <Text style={styles.smallButtonText}>Tout</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.smallButton} onPress={clearSelection}>
                    <Text style={styles.smallButtonText}>Aucun</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.smallButton, styles.confirmButton]}
                    onPress={() => initializeAttendanceData('selected')}
                    disabled={selectedCadets.size === 0}
                  >
                    <Text style={[styles.smallButtonText, {color: 'white'}]}>Confirmer</Text>
                  </TouchableOpacity>
                </View>

                {/* Liste des cadets pour sélection */}
                {cadets.map((cadet) => (
                  <TouchableOpacity
                    key={cadet.id}
                    style={[
                      styles.cadetSelectionCard,
                      selectedCadets.has(cadet.id) && styles.cadetSelectionCardSelected
                    ]}
                    onPress={() => toggleCadetSelection(cadet.id)}
                  >
                    <View style={styles.cadetSelectionInfo}>
                      <Text style={styles.cadetSelectionName}>
                        {cadet.prenom} {cadet.nom}
                      </Text>
                      <Text style={styles.cadetSelectionGrade}>
                        {cadet.grade}
                      </Text>
                    </View>
                    <View style={[
                      styles.checkbox,
                      selectedCadets.has(cadet.id) && styles.checkboxSelected
                    ]}>
                      {selectedCadets.has(cadet.id) && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Interface de sélection d'activité pour le mode 'activity' */}
            {attendanceMode === 'activity' && (
              <View style={styles.selectionInterface}>
                <Text style={styles.sectionTitle}>Choisir une activité pré-définie</Text>
                
                {activities.length === 0 ? (
                  <Text style={styles.emptyStateText}>Aucune activité configurée</Text>
                ) : (
                  activities.map((activity) => (
                    <TouchableOpacity
                      key={activity.id}
                      style={[
                        styles.activityCard,
                        selectedActivity?.id === activity.id && styles.activityCardSelected
                      ]}
                      onPress={() => {
                        setSelectedActivity(activity);
                        setActivite(activity.nom);
                        
                        // Pré-remplir avec les cadets de l'activité
                        const initialData: {[key: string]: {status: string, commentaire: string}} = {};
                        activity.cadet_ids.forEach(cadetId => {
                          initialData[cadetId] = { status: 'present', commentaire: '' };
                        });
                        setAttendanceData(initialData);
                      }}
                    >
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
                        </Text>
                      )}
                      
                      {activity.type === 'unique' && activity.planned_date && (
                        <Text style={styles.activityDate}>
                          Prévue: {new Date(activity.planned_date).toLocaleDateString('fr-FR')}
                        </Text>
                      )}
                    </TouchableOpacity>
                  ))
                )}
              </View>
            )}

            {/* Liste des cadets pour prise de présence */}
            {Object.keys(attendanceData).length > 0 && (
              <View>
                <Text style={styles.sectionTitle}>
                  Présences ({Object.keys(attendanceData).length} cadet{Object.keys(attendanceData).length > 1 ? 's' : ''})
                </Text>
                
                {Object.keys(attendanceData).map((cadetId) => {
                  const cadet = cadets.find(c => c.id === cadetId);
                  if (!cadet) return null;
                  
                  return (
                    <View key={cadet.id} style={styles.cadetCard}>
                      <Text style={styles.cadetName}>
                        {cadet.prenom} {cadet.nom}
                      </Text>
                      
                      {/* Boutons de statut */}
                      <View style={styles.statusButtons}>
                        {['present', 'absent', 'retard'].map((status) => (
                          <TouchableOpacity
                            key={status}
                            style={[
                              styles.statusButton,
                              attendanceData[cadet.id]?.status === status && styles.statusButtonActive,
                              { borderColor: getStatusColor(status) }
                            ]}
                            onPress={() => updateAttendanceStatus(cadet.id, status)}
                          >
                            <Text style={[
                              styles.statusButtonText,
                              attendanceData[cadet.id]?.status === status && { color: getStatusColor(status) }
                            ]}>
                              {getStatusDisplayName(status)}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </View>

                      {/* Commentaire */}
                      <TextInput
                        style={styles.commentInput}
                        placeholder="Commentaire (optionnel)"
                        value={attendanceData[cadet.id]?.commentaire || ''}
                        onChangeText={(text) => updateAttendanceComment(cadet.id, text)}
                        multiline
                      />
                    </View>
                  );
                })}

                {/* Bouton de sauvegarde */}
                <TouchableOpacity
                  style={[styles.saveButton, savingAttendance && styles.saveButtonDisabled]}
                  onPress={saveAttendance}
                  disabled={savingAttendance}
                >
                  <Text style={styles.saveButtonText}>
                    {savingAttendance ? 'Enregistrement...' : `Enregistrer ${Object.keys(attendanceData).length} présence${Object.keys(attendanceData).length > 1 ? 's' : ''}`}
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Modal des statistiques */}
      <Modal
        visible={showStats}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Statistiques de Présence</Text>
            <TouchableOpacity onPress={() => setShowStats(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          {stats && (
            <ScrollView style={styles.modalContent}>
              <View style={styles.statsContainer}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{stats.total_seances}</Text>
                  <Text style={styles.statLabel}>Séances Total</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, {color: '#10b981'}]}>{stats.presences}</Text>
                  <Text style={styles.statLabel}>Présences</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, {color: '#ef4444'}]}>{stats.absences}</Text>
                  <Text style={styles.statLabel}>Absences</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, {color: '#f59e0b'}]}>{stats.absences_excusees}</Text>
                  <Text style={styles.statLabel}>Abs. Excusées</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, {color: '#8b5cf6'}]}>{stats.retards}</Text>
                  <Text style={styles.statLabel}>Retards</Text>
                </View>
              </View>

              <View style={styles.presenceRate}>
                <Text style={styles.presenceRateValue}>{stats.taux_presence}%</Text>
                <Text style={styles.presenceRateLabel}>Taux de Présence</Text>
              </View>
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>

      {/* Modal pour la vue détaillée d'une activité */}
      <Modal
        visible={showActivityDetail}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {selectedActivityDetail?.activite || 'Détail de l\'Activité'}
            </Text>
            <TouchableOpacity onPress={() => setShowActivityDetail(false)}>
              <Text style={styles.closeButton}>Fermer</Text>
            </TouchableOpacity>
          </View>

          {selectedActivityDetail && (
            <ScrollView style={styles.modalContent}>
              {/* En-tête avec statistiques */}
              <View style={styles.detailHeader}>
                <Text style={styles.detailDate}>
                  {new Date(selectedActivityDetail.date).toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </Text>
                
                <View style={styles.detailStats}>
                  <View style={styles.statCard}>
                    <Text style={styles.statNumber}>{selectedActivityDetail.presences.length}</Text>
                    <Text style={styles.statLabel}>Participants</Text>
                  </View>
                  
                  <View style={styles.statCard}>
                    <Text style={[styles.statNumber, {color: '#10b981'}]}>
                      {selectedActivityDetail.presences.filter(p => p.status === 'present').length}
                    </Text>
                    <Text style={styles.statLabel}>Présents</Text>
                  </View>
                  
                  <View style={styles.statCard}>
                    <Text style={[styles.statNumber, {color: '#ef4444'}]}>
                      {selectedActivityDetail.presences.filter(p => p.status === 'absent').length}
                    </Text>
                    <Text style={styles.statLabel}>Absents</Text>
                  </View>
                </View>
              </View>

              {/* Liste complète des cadets */}
              <Text style={styles.sectionTitle}>Liste des Participants</Text>
              
              {['present', 'retard', 'absent'].map(status => {
                const cadetsWithStatus = selectedActivityDetail.presences.filter(p => p.status === status);
                if (cadetsWithStatus.length === 0) return null;
                
                return (
                  <View key={status} style={styles.statusSection}>
                    <Text style={[styles.statusSectionTitle, {color: getStatusColor(status)}]}>
                      {getStatusDisplayName(status)} ({cadetsWithStatus.length})
                    </Text>
                    
                    {cadetsWithStatus.map((presence) => (
                      <View key={presence.id} style={styles.detailCadetCard}>
                        <View style={styles.detailCadetInfo}>
                          <Text style={styles.detailCadetName}>
                            {presence.cadet_prenom} {presence.cadet_nom}
                          </Text>
                          {presence.section_nom && (
                            <Text style={styles.detailCadetSection}>
                              Section: {presence.section_nom}
                            </Text>
                          )}
                        </View>
                        
                        {presence.commentaire && (
                          <View style={styles.detailCommentBox}>
                            <Text style={styles.detailComment}>{presence.commentaire}</Text>
                          </View>
                        )}

                        {/* Bouton stats */}
                        {user && ['cadet_admin', 'encadrement'].includes(user.role) && (
                          <TouchableOpacity 
                            style={styles.detailStatsButton}
                            onPress={() => {
                              setShowActivityDetail(false);
                              loadStats(presence.cadet_id);
                            }}
                          >
                            <Text style={styles.detailStatsButtonText}>Voir Statistiques</Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    ))}
                  </View>
                );
              })}
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>

      {/* Nouveau Modal pour Swipe Attendance */}
      <Modal
        visible={showNewAttendance}
        animationType="slide"
        presentationStyle="fullScreen"
      >
        <GestureHandlerRootView style={{ flex: 1 }}>
          <SwipeableAttendance
            sections={sections.map(section => ({
              id: section.id,
              nom: section.nom,
              cadets: cadets
                .filter(cadet => cadet.section_id === section.id)
                .map(cadet => ({
                  id: cadet.id,
                  nom: cadet.nom || '',
                  prenom: cadet.prenom || '',
                  grade: cadet.grade || '',
                  section_id: cadet.section_id || '',
                }))
            }))}
            onComplete={handleSwipeAttendanceComplete}
            onCancel={() => setShowNewAttendance(false)}
            onAddGuest={() => {
              setShowNewAttendance(false);
              setShowAddGuest(true);
            }}
          />
        </GestureHandlerRootView>
      </Modal>

      {/* Modal pour ajouter un invité */}
      <Modal
        visible={showAddGuest}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAddGuest(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Ajouter un Invité</Text>
              <TouchableOpacity onPress={() => setShowAddGuest(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <Text style={styles.inputLabel}>Prénom *</Text>
              <TextInput
                style={styles.input}
                placeholder="Entrez le prénom"
                value={guestPrenom}
                onChangeText={setGuestPrenom}
              />

              <Text style={styles.inputLabel}>Nom *</Text>
              <TextInput
                style={styles.input}
                placeholder="Entrez le nom"
                value={guestNom}
                onChangeText={setGuestNom}
              />

              <Text style={styles.inputLabel}>Commentaire (optionnel)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Notes additionnelles..."
                value={guestCommentaire}
                onChangeText={setGuestCommentaire}
                multiline
                numberOfLines={3}
              />

              <Text style={styles.guestInfo}>
                ℹ️ Les invités sont des personnes qui ne sont pas encore inscrites dans le système.
                Ils ne seront pas éligibles aux inspections d'uniforme.
              </Text>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => {
                  setShowAddGuest(false);
                  setGuestNom('');
                  setGuestPrenom('');
                  setGuestCommentaire('');
                }}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.saveButton, savingGuest && styles.saveButtonDisabled]}
                onPress={handleSaveGuest}
                disabled={savingGuest}
              >
                {savingGuest ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.saveButtonText}>Enregistrer</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
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
  connectionIndicatorContainer: {
    backgroundColor: 'white',
    paddingHorizontal: 20,
    paddingVertical: 12,
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
  content: {
    flex: 1,
    padding: 20,
  },
  actionsContainer: {
    marginBottom: 20,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#3182ce',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#E5E5E5',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  statsCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 5,
  },
  statsDescription: {
    fontSize: 14,
    color: '#4a5568',
  },
  presencesContainer: {
    gap: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 15,
  },
  emptyState: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  presenceCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  presenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  presenceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  presenceDate: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 5,
  },
  presenceActivity: {
    fontSize: 14,
    color: '#2d3748',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  presenceComment: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 10,
  },
  statsButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#e2e8f0',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  statsButtonText: {
    fontSize: 12,
    color: '#2d3748',
    fontWeight: '600',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  sessionConfig: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
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
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f7fafc',
    marginBottom: 15,
  },
  cadetCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
  },
  cadetName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
    marginBottom: 15,
  },
  statusButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 15,
  },
  statusButton: {
    borderWidth: 2,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'white',
  },
  statusButtonActive: {
    backgroundColor: '#f0f9ff',
  },
  statusButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4a5568',
  },
  commentInput: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    backgroundColor: '#f7fafc',
    minHeight: 40,
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
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
    minWidth: '30%',
    marginBottom: 15,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a365d',
  },
  statLabel: {
    fontSize: 12,
    color: '#4a5568',
    textAlign: 'center',
    marginTop: 5,
  },
  presenceRate: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 30,
    alignItems: 'center',
  },
  presenceRateValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#10b981',
  },
  presenceRateLabel: {
    fontSize: 16,
    color: '#4a5568',
    marginTop: 10,
  },
  // Nouveaux styles pour l'interface de sélection
  modeSelector: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  modeButton: {
    flex: 1,
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    backgroundColor: 'white',
  },
  modeButtonActive: {
    borderColor: '#3182ce',
    backgroundColor: '#ebf8ff',
  },
  modeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4a5568',
  },
  modeButtonTextActive: {
    color: '#3182ce',
  },
  selectionInterface: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
  },
  selectionHeader: {
    marginBottom: 15,
  },
  selectionButtons: {
    flexDirection: 'row',
    gap: 8,
    flexShrink: 0,
    marginBottom: 15,
    justifyContent: 'flex-start',
  },
  smallButton: {
    backgroundColor: '#e2e8f0',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6,
    minWidth: 60,
    alignItems: 'center',
  },
  confirmButton: {
    backgroundColor: '#10b981',
    minWidth: 80,
  },
  smallButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2d3748',
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
  cadetSelectionInfo: {
    flex: 1,
  },
  cadetSelectionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
  },
  cadetSelectionGrade: {
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
  // Styles pour l'interface d'activité
  activityCard: {
    backgroundColor: '#f7fafc',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  activityCardSelected: {
    backgroundColor: '#ebf8ff',
    borderColor: '#3182ce',
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
  },
  // Nouveaux styles pour l'affichage par activité
  activityGroup: {
    backgroundColor: 'white',
    borderRadius: 15,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  activityGroupHeader: {
    backgroundColor: '#f8fafc',
    borderTopLeftRadius: 15,
    borderTopRightRadius: 15,
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  activityInfo: {
    marginBottom: 8,
  },
  activityGroupTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 4,
  },
  activityGroupDate: {
    fontSize: 14,
    color: '#4a5568',
    textTransform: 'capitalize',
  },
  activityStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  participantCount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
  },
  presenceStats: {
    fontSize: 12,
    color: '#718096',
    fontWeight: '500',
  },
  cadetsGrid: {
    padding: 16,
    gap: 12,
  },
  cadetPresenceCard: {
    backgroundColor: '#f7fafc',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#e2e8f0',
  },
  cadetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cadetName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d3748',
    flex: 1,
  },
  // Nouveaux styles pour l'interface collapsible
  activityTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  expandIcon: {
    fontSize: 16,
    color: '#4a5568',
    marginLeft: 10,
    fontWeight: 'bold',
  },
  activityActions: {
    alignItems: 'flex-end',
  },
  detailButton: {
    backgroundColor: '#3182ce',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginTop: 5,
  },
  detailButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  showMoreButton: {
    backgroundColor: '#f7fafc',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  showMoreText: {
    color: '#4a5568',
    fontSize: 14,
    fontWeight: '500',
  },
  // Styles pour la vue détaillée
  detailHeader: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
  },
  detailDate: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    marginBottom: 15,
    textTransform: 'capitalize',
  },
  detailStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#f7fafc',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
  },
  statLabel: {
    fontSize: 11,
    color: '#4a5568',
    marginTop: 4,
    textAlign: 'center',
  },
  statusSection: {
    marginBottom: 20,
  },
  statusSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    paddingHorizontal: 5,
  },
  detailCadetCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#e2e8f0',
  },
  detailCadetInfo: {
    marginBottom: 8,
  },
  detailCadetName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a365d',
  },
  detailCadetSection: {
    fontSize: 13,
    color: '#4a5568',
    marginTop: 2,
  },
  detailCommentBox: {
    backgroundColor: '#f9fafb',
    borderRadius: 6,
    padding: 8,
    marginBottom: 8,
  },
  detailComment: {
    fontSize: 14,
    color: '#374151',
    fontStyle: 'italic',
  },
  detailStatsButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#e2e8f0',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  detailStatsButtonText: {
    fontSize: 12,
    color: '#2d3748',
    fontWeight: '600',
  },
  // Styles pour le bouton invité dans le modal prise détaillée
  addGuestButtonInModal: {
    backgroundColor: '#10b981',
    padding: 14,
    borderRadius: 8,
    margin: 16,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  addGuestButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  // Styles pour le modal d'invité
  guestInfo: {
    backgroundColor: '#e0f2fe',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
    fontSize: 14,
    color: '#0369a1',
    lineHeight: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1f2937',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#e5e7eb',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
  },
  cancelButtonText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginLeft: 8,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonDisabled: {
    backgroundColor: '#93c5fd',
  },
});