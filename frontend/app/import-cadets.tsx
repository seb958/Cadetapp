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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  role: string;
  has_admin_privileges?: boolean;
}

interface PreviewData {
  total_rows: number;
  new_cadets: any[];
  updated_cadets: any[];
  errors: any[];
  new_sections: string[];
}

export default function ImportCadets() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [importResult, setImportResult] = useState<any>(null);

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
        
        // Vérifier les permissions admin
        const role = parsedUser.role.toLowerCase();
        const isAdmin = ['cadet_admin', 'encadrement'].some(keyword => role.includes(keyword));
        
        if (!isAdmin) {
          Alert.alert('Accès refusé', 'Seuls les administrateurs peuvent importer des cadets');
          router.back();
          return;
        }
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

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
        copyToCacheDirectory: true,
      });

      if (result.canceled) {
        return;
      }

      if (result.assets && result.assets.length > 0) {
        const file = result.assets[0];
        setSelectedFile(file);
        setPreviewData(null);
        setImportResult(null);
        Alert.alert('Fichier sélectionné', `${file.name}\nTaille: ${(file.size / 1024).toFixed(2)} KB`);
      }
    } catch (error) {
      console.error('Erreur sélection fichier:', error);
      Alert.alert('Erreur', 'Impossible de sélectionner le fichier');
    }
  };

  const previewImport = async () => {
    if (!selectedFile) {
      Alert.alert('Erreur', 'Veuillez sélectionner un fichier Excel');
      return;
    }

    setUploading(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      
      // Créer FormData pour l'upload
      const formData = new FormData();
      
      if (Platform.OS === 'web') {
        // Sur web, utiliser le fichier directement
        const response = await fetch(selectedFile.uri);
        const blob = await response.blob();
        formData.append('file', blob, selectedFile.name);
      } else {
        // Sur mobile
        formData.append('file', {
          uri: selectedFile.uri,
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          name: selectedFile.name,
        } as any);
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/import/cadets/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
        Alert.alert('Prévisualisation prête', `${data.total_rows} lignes analysées`);
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'analyse du fichier');
      }
    } catch (error) {
      console.error('Erreur:', error);
      Alert.alert('Erreur', 'Impossible d\'analyser le fichier');
    } finally {
      setUploading(false);
    }
  };

  const confirmImport = async () => {
    if (!previewData) {
      Alert.alert('Erreur', 'Veuillez d\'abord prévisualiser l\'import');
      return;
    }

    Alert.alert(
      'Confirmer l\'import',
      `Voulez-vous importer ${previewData.new_cadets.length} nouveaux cadets et mettre à jour ${previewData.updated_cadets.length} cadets existants ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Confirmer',
          onPress: async () => {
            setConfirming(true);
            try {
              const token = await AsyncStorage.getItem('access_token');
              
              // Préparer les changements
              const changes = [
                ...previewData.new_cadets.map(c => ({
                  type: 'new',
                  nom: c.nom,
                  prenom: c.prenom,
                  grade: c.grade,
                  section: c.section,
                  username: c.username
                })),
                ...previewData.updated_cadets.map(c => ({
                  type: 'update',
                  username: c.username,
                  new_grade: c.new_grade,
                  new_section: c.new_section
                }))
              ];

              const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/import/cadets/confirm`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                  changes: changes,
                  create_sections: true
                }),
              });

              if (response.ok) {
                const result = await response.json();
                setImportResult(result);
                Alert.alert('Succès', `Import terminé !\n${result.cadets_created} créés, ${result.cadets_updated} mis à jour`);
              } else {
                const errorData = await response.json();
                Alert.alert('Erreur', errorData.detail || 'Erreur lors de l\'import');
              }
            } catch (error) {
              console.error('Erreur:', error);
              Alert.alert('Erreur', 'Impossible de confirmer l\'import');
            } finally {
              setConfirming(false);
            }
          }
        }
      ]
    );
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
        <Text style={styles.title}>Import Excel - Cadets</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Instructions */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 Instructions</Text>
          <Text style={styles.instructionText}>
            1. Préparez un fichier Excel (.xlsx) avec les colonnes :{'\n'}
            <Text style={styles.bold}>   • Nom | Prénom | Grade | Groupe</Text>
          </Text>
          <Text style={styles.instructionText}>
            2. Grades acceptés : cdt, cdt 1, cpl, cpls, sgt, sgts, adj 2, adj 1
          </Text>
          <Text style={styles.instructionText}>
            3. Les sections manquantes seront créées automatiquement
          </Text>
          <Text style={styles.instructionText}>
            4. Les doublons seront mis à jour (grade et section)
          </Text>
        </View>

        {/* Sélection du fichier */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📁 Fichier Excel</Text>
          
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={pickDocument}
            disabled={uploading || confirming}
          >
            <Text style={styles.uploadButtonText}>
              {selectedFile ? '✓ Changer de fichier' : '📤 Sélectionner un fichier'}
            </Text>
          </TouchableOpacity>

          {selectedFile && (
            <View style={styles.fileInfo}>
              <Text style={styles.fileName}>📄 {selectedFile.name}</Text>
              <Text style={styles.fileSize}>{(selectedFile.size / 1024).toFixed(2)} KB</Text>
            </View>
          )}

          {selectedFile && !previewData && (
            <TouchableOpacity
              style={styles.previewButton}
              onPress={previewImport}
              disabled={uploading}
            >
              {uploading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.previewButtonText}>🔍 Prévisualiser l'import</Text>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* Prévisualisation */}
        {previewData && !importResult && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>👀 Prévisualisation</Text>
            
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Total de lignes :</Text>
              <Text style={styles.statValue}>{previewData.total_rows}</Text>
            </View>

            <View style={styles.statRow}>
              <Text style={[styles.statLabel, styles.successText]}>Nouveaux cadets :</Text>
              <Text style={[styles.statValue, styles.successText]}>{previewData.new_cadets.length}</Text>
            </View>

            <View style={styles.statRow}>
              <Text style={[styles.statLabel, styles.warningText]}>Mises à jour :</Text>
              <Text style={[styles.statValue, styles.warningText]}>{previewData.updated_cadets.length}</Text>
            </View>

            <View style={styles.statRow}>
              <Text style={[styles.statLabel, styles.errorText]}>Erreurs :</Text>
              <Text style={[styles.statValue, styles.errorText]}>{previewData.errors.length}</Text>
            </View>

            {previewData.new_sections.length > 0 && (
              <View style={styles.newSectionsBox}>
                <Text style={styles.newSectionsTitle}>📍 Nouvelles sections à créer :</Text>
                {previewData.new_sections.map((section, idx) => (
                  <Text key={idx} style={styles.newSectionItem}>• {section}</Text>
                ))}
              </View>
            )}

            {/* Détails des nouveaux cadets */}
            {previewData.new_cadets.length > 0 && (
              <View style={styles.detailsBox}>
                <Text style={styles.detailsTitle}>✨ Nouveaux cadets (5 premiers) :</Text>
                {previewData.new_cadets.slice(0, 5).map((cadet, idx) => (
                  <Text key={idx} style={styles.detailItem}>
                    • {cadet.prenom} {cadet.nom} - {cadet.grade} - {cadet.section}
                  </Text>
                ))}
                {previewData.new_cadets.length > 5 && (
                  <Text style={styles.moreText}>... et {previewData.new_cadets.length - 5} autres</Text>
                )}
              </View>
            )}

            {/* Détails des mises à jour */}
            {previewData.updated_cadets.length > 0 && (
              <View style={styles.detailsBox}>
                <Text style={styles.detailsTitle}>🔄 Mises à jour (5 premières) :</Text>
                {previewData.updated_cadets.slice(0, 5).map((cadet, idx) => (
                  <View key={idx} style={styles.updateItem}>
                    <Text style={styles.updateName}>{cadet.prenom} {cadet.nom}</Text>
                    {cadet.changes.map((change: string, cidx: number) => (
                      <Text key={cidx} style={styles.updateChange}>  → {change}</Text>
                    ))}
                  </View>
                ))}
                {previewData.updated_cadets.length > 5 && (
                  <Text style={styles.moreText}>... et {previewData.updated_cadets.length - 5} autres</Text>
                )}
              </View>
            )}

            {/* Erreurs */}
            {previewData.errors.length > 0 && (
              <View style={styles.errorsBox}>
                <Text style={styles.errorsTitle}>⚠️ Erreurs détectées :</Text>
                {previewData.errors.map((error, idx) => (
                  <Text key={idx} style={styles.errorItem}>
                    Ligne {error.row}: {error.error}
                  </Text>
                ))}
              </View>
            )}

            <TouchableOpacity
              style={styles.confirmButton}
              onPress={confirmImport}
              disabled={confirming || previewData.errors.length > 0}
            >
              {confirming ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.confirmButtonText}>
                  {previewData.errors.length > 0 ? '❌ Impossible (erreurs détectées)' : '✅ Confirmer l\'import'}
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => {
                setPreviewData(null);
                setSelectedFile(null);
              }}
              disabled={confirming}
            >
              <Text style={styles.cancelButtonText}>Annuler</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Résultats */}
        {importResult && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>✅ Import Terminé !</Text>
            
            <View style={styles.resultBox}>
              <Text style={styles.resultText}>
                ✨ <Text style={styles.bold}>{importResult.cadets_created}</Text> cadets créés
              </Text>
              <Text style={styles.resultText}>
                🔄 <Text style={styles.bold}>{importResult.cadets_updated}</Text> cadets mis à jour
              </Text>
              
              {importResult.new_sections_created.length > 0 && (
                <Text style={styles.resultText}>
                  📍 <Text style={styles.bold}>{importResult.new_sections_created.length}</Text> sections créées
                </Text>
              )}
            </View>

            <TouchableOpacity
              style={styles.doneButton}
              onPress={() => router.back()}
            >
              <Text style={styles.doneButtonText}>Terminé</Text>
            </TouchableOpacity>
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
  content: {
    flex: 1,
    padding: 16,
  },
  card: {
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
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  instructionText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
    lineHeight: 20,
  },
  bold: {
    fontWeight: 'bold',
    color: '#374151',
  },
  uploadButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  fileInfo: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#eff6ff',
    borderRadius: 8,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 4,
  },
  fileSize: {
    fontSize: 12,
    color: '#6b7280',
  },
  previewButton: {
    backgroundColor: '#10b981',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  previewButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  statValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  successText: {
    color: '#10b981',
  },
  warningText: {
    color: '#f59e0b',
  },
  errorText: {
    color: '#ef4444',
  },
  newSectionsBox: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#dbeafe',
    borderRadius: 8,
  },
  newSectionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1e40af',
    marginBottom: 8,
  },
  newSectionItem: {
    fontSize: 13,
    color: '#1e40af',
    marginLeft: 8,
    marginBottom: 4,
  },
  detailsBox: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  detailsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  detailItem: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 4,
  },
  updateItem: {
    marginBottom: 8,
  },
  updateName: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#374151',
  },
  updateChange: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 8,
  },
  moreText: {
    fontSize: 12,
    fontStyle: 'italic',
    color: '#9ca3af',
    marginTop: 4,
  },
  errorsBox: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
  },
  errorsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#dc2626',
    marginBottom: 8,
  },
  errorItem: {
    fontSize: 13,
    color: '#dc2626',
    marginBottom: 4,
  },
  confirmButton: {
    backgroundColor: '#10b981',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#6b7280',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultBox: {
    padding: 16,
    backgroundColor: '#d1fae5',
    borderRadius: 8,
    marginBottom: 16,
  },
  resultText: {
    fontSize: 16,
    color: '#065f46',
    marginBottom: 8,
  },
  doneButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
