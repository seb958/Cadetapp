/**
 * Bannière de téléchargement APK
 * Affiche une notification si une nouvelle version est disponible
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

interface VersionInfo {
  currentApkVersion: string;
  minimumSupportedVersion: string;
  apkDownloadUrl: string;
  forceUpdate: boolean;
  releaseNotes: string[];
}

interface APKDownloadBannerProps {
  backendUrl: string;
}

export const APKDownloadBanner: React.FC<APKDownloadBannerProps> = ({ backendUrl }) => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
  const [showBanner, setShowBanner] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Version actuelle de l'app (depuis app.json)
  const currentVersion = Constants.expoConfig?.version || '1.0.0';

  useEffect(() => {
    checkForUpdates();
    loadDismissedState();
  }, []);

  const loadDismissedState = async () => {
    try {
      const dismissedVersion = await AsyncStorage.getItem('dismissed_update_version');
      if (dismissedVersion === currentVersion) {
        setDismissed(true);
      }
    } catch (error) {
      console.error('Erreur chargement état dismissed:', error);
    }
  };

  const checkForUpdates = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${backendUrl}/api/version-info`, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return;
      }

      const info: VersionInfo = await response.json();
      setVersionInfo(info);

      // Vérifier si une mise à jour est disponible
      if (info.apkDownloadUrl && isNewerVersion(info.currentApkVersion, currentVersion)) {
        setShowBanner(true);
      }
    } catch (error) {
      console.log('Impossible de vérifier les mises à jour:', error);
    }
  };

  const isNewerVersion = (serverVersion: string, appVersion: string): boolean => {
    const parseVersion = (v: string) => v.split('.').map(Number);
    const server = parseVersion(serverVersion);
    const app = parseVersion(appVersion);

    for (let i = 0; i < 3; i++) {
      if (server[i] > app[i]) return true;
      if (server[i] < app[i]) return false;
    }
    return false;
  };

  const handleDownload = async () => {
    if (!versionInfo?.apkDownloadUrl) {
      Alert.alert('Erreur', 'URL de téléchargement non disponible');
      return;
    }

    try {
      const supported = await Linking.canOpenURL(versionInfo.apkDownloadUrl);
      if (supported) {
        await Linking.openURL(versionInfo.apkDownloadUrl);
      } else {
        Alert.alert('Erreur', 'Impossible d\'ouvrir le lien de téléchargement');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Impossible d\'ouvrir le lien de téléchargement');
    }
  };

  const handleDismiss = async () => {
    setDismissed(true);
    try {
      await AsyncStorage.setItem('dismissed_update_version', versionInfo?.currentApkVersion || currentVersion);
    } catch (error) {
      console.error('Erreur sauvegarde dismissed:', error);
    }
  };

  // Ne pas afficher si :
  // - Pas d'info de version
  // - Pas de nouvelle version disponible
  // - Utilisateur a dismissé
  // - Pas d'URL de téléchargement
  if (!showBanner || !versionInfo || dismissed || !versionInfo.apkDownloadUrl) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.icon}>📱</Text>
          <Text style={styles.title}>Nouvelle Version Disponible</Text>
        </View>

        <Text style={styles.version}>
          Version {versionInfo.currentApkVersion}
        </Text>

        {versionInfo.releaseNotes.length > 0 && (
          <View style={styles.notesContainer}>
            {versionInfo.releaseNotes.slice(0, 3).map((note, index) => (
              <Text key={index} style={styles.note}>
                • {note}
              </Text>
            ))}
          </View>
        )}

        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.downloadButton}
            onPress={handleDownload}
          >
            <Text style={styles.downloadButtonText}>📥 Télécharger</Text>
          </TouchableOpacity>

          {!versionInfo.forceUpdate && (
            <TouchableOpacity
              style={styles.dismissButton}
              onPress={handleDismiss}
            >
              <Text style={styles.dismissButtonText}>Plus tard</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#EBF8FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#3182CE',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  content: {
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  icon: {
    fontSize: 24,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2C5282',
    flex: 1,
  },
  version: {
    fontSize: 14,
    color: '#2D3748',
    fontWeight: '600',
  },
  notesContainer: {
    gap: 4,
  },
  note: {
    fontSize: 13,
    color: '#4A5568',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 4,
  },
  downloadButton: {
    flex: 1,
    backgroundColor: '#3182CE',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  downloadButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  dismissButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#E2E8F0',
  },
  dismissButtonText: {
    color: '#4A5568',
    fontSize: 15,
    fontWeight: '600',
  },
});
