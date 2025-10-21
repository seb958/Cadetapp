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

export default function Inspections() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
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
  
  // États pour la programmation de tenue
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedUniformType, setSelectedUniformType] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');
  const [savingSchedule, setSavingSchedule] = useState(false);
  
  // Permissions
  const [canScheduleUniform, setCanScheduleUniform] = useState(false);
  const [canInspect, setCanInspect] = useState(false);

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
        
        // Charger les données
        await loadAllData();
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

  const loadAllData = async () => {
    await Promise.all([
      loadCadets(),
      loadSections(),
      loadSettings(),
      loadTodaySchedule(),
      loadRecentInspections()
    ]);
  };

  const loadCadets = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setCadets(data.filter((u: User) => u.role.includes('cadet') || u.role.includes('Cadet')));
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
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-inspections?date=${today}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
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
    if (!todaySchedule || !todaySchedule.uniform_type) {
      Alert.alert('Attention', 'Veuillez d\'abord programmer la tenue du jour');
      return;
    }

    setSelectedCadet(cadet);
    
    // Initialiser les scores des critères à 0 (barème de 0 à 4)
    const uniformType = todaySchedule.uniform_type;
    const criteria = settings?.inspectionCriteria[uniformType] || [];
    const initialScores: { [key: string]: number } = {};
    criteria.forEach(criterion => {
      initialScores[criterion] = 0;
    });
    setCriteriaScores(initialScores);
    setInspectionComment('');
    
    setShowInspectionModal(true);
  };

  const updateCriterionScore = (criterion: string, score: number) => {
    setCriteriaScores(prev => ({
      ...prev,
      [criterion]: score
    }));
  };

  const calculateScore = () => {
    const total = Object.keys(criteriaScores).length;
    if (total === 0) return 0;
    const obtained = Object.values(criteriaScores).reduce((sum, score) => sum + score, 0);
    const maxScore = total * 4;
    return Math.round((obtained / maxScore) * 100);
  };

  const saveInspection = async () => {
    if (!selectedCadet || !todaySchedule?.uniform_type) return;

    setSavingInspection(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      const today = new Date().toISOString().split('T')[0];
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/uniform-inspections?inspection_date=${today}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          cadet_id: selectedCadet.id,
          uniform_type: todaySchedule.uniform_type,
          criteria_scores: criteriaScores,
          commentaire: inspectionComment || null
        }),
      });

      if (response.ok) {
        const result = await response.json();
        let message = `Inspection enregistrée avec succès\nScore: ${result.total_score}%`;
        
        if (result.auto_marked_present) {
          message += '\n\n⚠️ Le cadet a été automatiquement marqué présent suite à cette inspection';
        }
        
        Alert.alert('Succès', message);
        setShowInspectionModal(false);
        setSelectedCadet(null);
        await loadRecentInspections();
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible d\'enregistrer l\'inspection');
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

  if (!canInspect) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Retour</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Inspections</Text>
        </View>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>❌ Accès refusé</Text>
          <Text style={styles.errorSubtext}>
            Vous devez être chef de section ou supérieur pour accéder aux inspections
          </Text>
        </View>
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

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Tenue du jour */}
        <View style={styles.scheduleCard}>
          <View style={styles.scheduleHeader}>
            <Text style={styles.scheduleTitle}>👔 Tenue du jour</Text>
            {canScheduleUniform && (
              <TouchableOpacity style={styles.scheduleButton} onPress={openScheduleModal}>
                <Text style={styles.scheduleButtonText}>Programmer</Text>
              </TouchableOpacity>
            )}
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
              <View key={inspection.id} style={styles.inspectionCard}>
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
              </View>
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
});
