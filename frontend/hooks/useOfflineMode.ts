/**
 * Hook personnalisé pour gérer le mode hors ligne
 */

import { useState, useEffect } from 'react';
import {
  initNetworkListener,
  addConnectionListener,
  removeConnectionListener,
  getConnectionStatus,
  getSyncQueue,
  syncQueue,
  downloadCacheData,
  getCacheData,
  SyncQueueItem,
} from '../services/offlineService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

export const useOfflineMode = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncQueueCount, setSyncQueueCount] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);

  useEffect(() => {
    // Initialiser le listener de connexion
    initNetworkListener();
    
    // Vérifier l'état initial
    setIsOnline(getConnectionStatus());
    
    // Ajouter un listener pour les changements
    const listener = (online: boolean) => {
      setIsOnline(online);
      if (online) {
        // Synchroniser automatiquement quand connexion restaurée
        handleAutoSync();
      }
    };
    
    addConnectionListener(listener);
    
    // Charger le nombre d'éléments en attente
    loadSyncQueueCount();
    
    // Vérifier périodiquement la queue
    const interval = setInterval(loadSyncQueueCount, 5000);
    
    return () => {
      removeConnectionListener(listener);
      clearInterval(interval);
    };
  }, []);

  const loadSyncQueueCount = async () => {
    try {
      const queue = await getSyncQueue();
      setSyncQueueCount(queue.length);
    } catch (error) {
      console.error('Erreur chargement queue:', error);
    }
  };

  const handleAutoSync = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
      
      if (token && backendUrl) {
        await handleManualSync();
      }
    } catch (error) {
      console.error('Erreur auto-sync:', error);
    }
  };

  const handleManualSync = async (): Promise<{ success: boolean; message: string }> => {
    if (isSyncing) {
      return { success: false, message: 'Synchronisation déjà en cours' };
    }

    if (!isOnline) {
      return { success: false, message: 'Pas de connexion internet' };
    }

    try {
      setIsSyncing(true);
      
      const token = await AsyncStorage.getItem('access_token');
      const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
      
      if (!token) {
        return { success: false, message: 'Non authentifié' };
      }

      const result = await syncQueue(backendUrl, token);
      
      if (result.success) {
        await loadSyncQueueCount();
        setLastSyncTime(new Date().toISOString());
        
        if (result.synced === 0 && result.errors === 0) {
          return { success: true, message: 'Aucune donnée à synchroniser' };
        }
        
        // Si des erreurs, construire un message détaillé
        if (result.errors > 0 && result.errorDetails) {
          const errorMessages = result.errorDetails.map((err: any) => 
            `• ${err.error || 'Erreur inconnue'}`
          ).join('\n');
          
          return {
            success: result.synced > 0, // Succès partiel si au moins 1 synchronisé
            message: `${result.synced} élément(s) synchronisé(s)\n${result.errors} erreur(s):\n\n${errorMessages}`,
          };
        }
        
        return {
          success: true,
          message: `${result.synced} élément(s) synchronisé(s)`,
        };
      }
      
      return { success: false, message: 'Échec de la synchronisation' };
    } catch (error: any) {
      console.error('Erreur sync manuelle:', error);
      return { success: false, message: error.message || 'Erreur de synchronisation' };
    } finally {
      setIsSyncing(false);
    }
  };

  const refreshCache = async (): Promise<boolean> => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
      
      if (!token || !backendUrl) {
        return false;
      }

      return await downloadCacheData(backendUrl, token);
    } catch (error) {
      console.error('Erreur refresh cache:', error);
      return false;
    }
  };

  return {
    isOnline,
    isSyncing,
    syncQueueCount,
    lastSyncTime,
    handleManualSync,
    refreshCache,
    loadSyncQueueCount,
  };
};
