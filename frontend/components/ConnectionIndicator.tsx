/**
 * Composant indicateur de statut de connexion et synchronisation
 */

import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useOfflineMode } from '../hooks/useOfflineMode';

interface ConnectionIndicatorProps {
  onSyncPress?: () => void;
}

export const ConnectionIndicator: React.FC<ConnectionIndicatorProps> = ({ onSyncPress }) => {
  const { isOnline, isSyncing, syncQueueCount, handleManualSync } = useOfflineMode();

  const handleSync = async () => {
    if (onSyncPress) {
      onSyncPress();
    } else {
      const result = await handleManualSync();
      // La notification sera gérée dans le composant parent
    }
  };

  return (
    <View style={styles.container}>
      {/* Indicateur de connexion */}
      <View style={styles.statusContainer}>
        <View style={[styles.statusDot, isOnline ? styles.onlineDot : styles.offlineDot]} />
        <Text style={styles.statusText}>
          {isSyncing ? 'Synchronisation...' : isOnline ? 'En ligne' : 'Hors ligne'}
        </Text>
      </View>

      {/* Badge de queue si des éléments en attente */}
      {syncQueueCount > 0 && (
        <View style={styles.queueBadge}>
          <Text style={styles.queueText}>{syncQueueCount}</Text>
        </View>
      )}

      {/* Bouton de synchronisation */}
      {!isSyncing && syncQueueCount > 0 && isOnline && (
        <TouchableOpacity style={styles.syncButton} onPress={handleSync}>
          <Text style={styles.syncButtonText}>Synchroniser</Text>
        </TouchableOpacity>
      )}

      {/* Indicateur de synchronisation en cours */}
      {isSyncing && (
        <View style={styles.syncingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  onlineDot: {
    backgroundColor: '#34C759',
  },
  offlineDot: {
    backgroundColor: '#FF3B30',
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  queueBadge: {
    backgroundColor: '#FF9500',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginRight: 8,
  },
  queueText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  syncButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  syncButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  syncingContainer: {
    marginLeft: 8,
  },
});
