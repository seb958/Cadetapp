/**
 * Modal pour générer un mot de passe initial pour un utilisateur
 * Affiche le mot de passe généré une seule fois
 */

import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';

interface GeneratePasswordModalProps {
  visible: boolean;
  userId: string | null;
  username: string;
  onClose: () => void;
  backendUrl: string;
  token: string;
}

export const GeneratePasswordModal: React.FC<GeneratePasswordModalProps> = ({
  visible,
  userId,
  username,
  onClose,
  backendUrl,
  token,
}) => {
  const [generating, setGenerating] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);
  const [generatedUsername, setGeneratedUsername] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!userId) return;

    setGenerating(true);
    try {
      const response = await fetch(`${backendUrl}/api/users/${userId}/generate-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedPassword(data.temporary_password);
        setGeneratedUsername(data.username);
      } else {
        const errorData = await response.json();
        Alert.alert('Erreur', errorData.detail || 'Impossible de générer le mot de passe');
        onClose();
      }
    } catch (error) {
      console.error('Erreur génération mot de passe:', error);
      Alert.alert('Erreur', 'Impossible de générer le mot de passe');
      onClose();
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (generatedPassword) {
      await Clipboard.setStringAsync(generatedPassword);
      Alert.alert('Succès', 'Mot de passe copié dans le presse-papiers');
    }
  };

  const handleClose = () => {
    setGeneratedPassword(null);
    onClose();
  };

  // Générer automatiquement quand le modal s'ouvre
  React.useEffect(() => {
    if (visible && userId && !generatedPassword && !generating) {
      handleGenerate();
    }
  }, [visible, userId]);

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={true}
      onRequestClose={handleClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {generating ? (
            <View style={styles.centerContent}>
              <ActivityIndicator size="large" color="#3182CE" />
              <Text style={styles.loadingText}>Génération du mot de passe...</Text>
            </View>
          ) : generatedPassword ? (
            <>
              {/* Header */}
              <View style={styles.header}>
                <Text style={styles.icon}>🔑</Text>
                <Text style={styles.title}>Mot de Passe Temporaire Généré</Text>
                <Text style={styles.subtitle}>
                  Pour l'utilisateur : <Text style={styles.username}>{username}</Text>
                </Text>
              </View>

              {/* Credentials Display */}
              <View style={styles.credentialsContainer}>
                <View style={styles.credentialRow}>
                  <Text style={styles.credentialLabel}>Nom d'utilisateur :</Text>
                  <View style={styles.credentialBox}>
                    <Text style={styles.credentialText}>{username}</Text>
                  </View>
                </View>
                
                <View style={styles.credentialRow}>
                  <Text style={styles.credentialLabel}>Mot de passe temporaire :</Text>
                  <View style={styles.passwordBox}>
                    <Text style={styles.password}>{generatedPassword}</Text>
                  </View>
                </View>
              </View>

              {/* Warning */}
              <View style={styles.warningContainer}>
                <Text style={styles.warningIcon}>⚠️</Text>
                <Text style={styles.warningText}>
                  Ce mot de passe ne sera affiché qu'une seule fois.{'\n'}
                  L'utilisateur devra le changer à sa première connexion.
                </Text>
              </View>

              {/* Actions */}
              <View style={styles.actions}>
                <TouchableOpacity style={styles.copyButton} onPress={handleCopy}>
                  <Text style={styles.copyButtonText}>📋 Copier</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
                  <Text style={styles.closeButtonText}>Fermer</Text>
                </TouchableOpacity>
              </View>
            </>
          ) : null}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
  },
  centerContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  icon: {
    fontSize: 48,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#718096',
    textAlign: 'center',
  },
  username: {
    fontWeight: 'bold',
    color: '#2d3748',
  },
  credentialsContainer: {
    marginBottom: 20,
    gap: 16,
  },
  credentialRow: {
    gap: 8,
  },
  credentialLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 4,
  },
  credentialBox: {
    backgroundColor: '#f7fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
  },
  credentialText: {
    fontSize: 16,
    color: '#1a365d',
    fontWeight: '600',
  },
  passwordBox: {
    backgroundColor: '#f7fafc',
    borderWidth: 2,
    borderColor: '#3182ce',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  password: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a365d',
    fontFamily: 'monospace',
    letterSpacing: 2,
  },
  warningContainer: {
    backgroundColor: '#fef5e7',
    borderLeftWidth: 4,
    borderLeftColor: '#f39c12',
    padding: 16,
    borderRadius: 8,
    marginBottom: 20,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  warningIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    color: '#856404',
    lineHeight: 18,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  copyButton: {
    flex: 1,
    backgroundColor: '#3182ce',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  copyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  closeButton: {
    flex: 1,
    backgroundColor: '#e2e8f0',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#4a5568',
    fontSize: 16,
    fontWeight: '600',
  },
});
