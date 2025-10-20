/**
 * Service de gestion du mode hors ligne
 * - Détection de la connexion internet
 * - Cache des données essentielles
 * - Queue de synchronisation
 * - Synchronisation automatique et manuelle
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

// Clés de stockage
const STORAGE_KEYS = {
  CACHE_USERS: '@cache_users',
  CACHE_SECTIONS: '@cache_sections',
  CACHE_ACTIVITIES: '@cache_activities',
  CACHE_TIMESTAMP: '@cache_timestamp',
  SYNC_QUEUE: '@sync_queue',
  IS_SYNCING: '@is_syncing',
};

// Types
export interface OfflinePresence {
  cadet_id: string;
  date: string; // Format ISO: YYYY-MM-DD
  status: 'present' | 'absent' | 'retard';
  commentaire?: string;
  timestamp: string; // ISO datetime
  temp_id: string; // ID temporaire pour tracking
}

export interface OfflineInspection {
  cadet_id: string;
  date: string;
  note?: string;
  timestamp: string;
  temp_id: string;
}

export interface SyncQueueItem {
  type: 'presence' | 'inspection';
  data: OfflinePresence | OfflineInspection;
  attempts: number;
  created_at: string;
}

export interface CacheData {
  users: any[];
  sections: any[];
  activities: any[];
  timestamp: string;
}

// ============================================================================
// DÉTECTION DE CONNEXION
// ============================================================================

let isOnline = true;
let connectionListeners: Array<(online: boolean) => void> = [];

/**
 * Initialise la détection de connexion
 */
export const initNetworkListener = () => {
  NetInfo.addEventListener(state => {
    const wasOnline = isOnline;
    isOnline = state.isConnected === true;
    
    // Si passage de hors ligne à en ligne, notifier les listeners
    if (!wasOnline && isOnline) {
      console.log('🟢 Connexion internet restaurée');
      connectionListeners.forEach(listener => listener(true));
      // Déclencher synchronisation automatique
      syncQueueAutomatically();
    } else if (wasOnline && !isOnline) {
      console.log('🔴 Connexion internet perdue');
      connectionListeners.forEach(listener => listener(false));
    }
  });
  
  // Vérifier l'état initial
  NetInfo.fetch().then(state => {
    isOnline = state.isConnected === true;
    console.log(isOnline ? '🟢 En ligne' : '🔴 Hors ligne');
  });
};

/**
 * Ajoute un listener pour les changements de connexion
 */
export const addConnectionListener = (listener: (online: boolean) => void) => {
  connectionListeners.push(listener);
};

/**
 * Retire un listener
 */
export const removeConnectionListener = (listener: (online: boolean) => void) => {
  connectionListeners = connectionListeners.filter(l => l !== listener);
};

/**
 * Retourne l'état actuel de la connexion
 */
export const getConnectionStatus = (): boolean => {
  return isOnline;
};

// ============================================================================
// GESTION DU CACHE
// ============================================================================

/**
 * Sauvegarde les données en cache pour utilisation hors ligne
 */
export const saveCacheData = async (data: CacheData): Promise<void> => {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.CACHE_USERS, JSON.stringify(data.users));
    await AsyncStorage.setItem(STORAGE_KEYS.CACHE_SECTIONS, JSON.stringify(data.sections));
    await AsyncStorage.setItem(STORAGE_KEYS.CACHE_ACTIVITIES, JSON.stringify(data.activities));
    await AsyncStorage.setItem(STORAGE_KEYS.CACHE_TIMESTAMP, data.timestamp);
    console.log('✅ Données mises en cache');
  } catch (error) {
    console.error('❌ Erreur sauvegarde cache:', error);
  }
};

/**
 * Récupère les données du cache
 */
export const getCacheData = async (): Promise<CacheData | null> => {
  try {
    const users = await AsyncStorage.getItem(STORAGE_KEYS.CACHE_USERS);
    const sections = await AsyncStorage.getItem(STORAGE_KEYS.CACHE_SECTIONS);
    const activities = await AsyncStorage.getItem(STORAGE_KEYS.CACHE_ACTIVITIES);
    const timestamp = await AsyncStorage.getItem(STORAGE_KEYS.CACHE_TIMESTAMP);
    
    if (!users || !sections || !timestamp) {
      return null;
    }
    
    return {
      users: JSON.parse(users),
      sections: JSON.parse(sections),
      activities: activities ? JSON.parse(activities) : [],
      timestamp,
    };
  } catch (error) {
    console.error('❌ Erreur récupération cache:', error);
    return null;
  }
};

/**
 * Télécharge et met en cache les données depuis le serveur
 */
export const downloadCacheData = async (apiUrl: string, token: string): Promise<boolean> => {
  try {
    const response = await fetch(`${apiUrl}/api/sync/cache-data`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Échec téléchargement données');
    }
    
    const data = await response.json();
    await saveCacheData(data);
    return true;
  } catch (error) {
    console.error('❌ Erreur téléchargement cache:', error);
    return false;
  }
};

// ============================================================================
// GESTION DE LA QUEUE DE SYNCHRONISATION
// ============================================================================

/**
 * Ajoute un élément à la queue de synchronisation
 */
export const addToSyncQueue = async (item: SyncQueueItem): Promise<void> => {
  try {
    const queueJson = await AsyncStorage.getItem(STORAGE_KEYS.SYNC_QUEUE);
    const queue: SyncQueueItem[] = queueJson ? JSON.parse(queueJson) : [];
    
    queue.push(item);
    
    await AsyncStorage.setItem(STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(queue));
    console.log(`📝 Ajouté à la queue: ${item.type} (${item.data.temp_id})`);
  } catch (error) {
    console.error('❌ Erreur ajout queue:', error);
  }
};

/**
 * Récupère la queue de synchronisation
 */
export const getSyncQueue = async (): Promise<SyncQueueItem[]> => {
  try {
    const queueJson = await AsyncStorage.getItem(STORAGE_KEYS.SYNC_QUEUE);
    return queueJson ? JSON.parse(queueJson) : [];
  } catch (error) {
    console.error('❌ Erreur récupération queue:', error);
    return [];
  }
};

/**
 * Vide la queue de synchronisation
 */
export const clearSyncQueue = async (): Promise<void> => {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.SYNC_QUEUE, JSON.stringify([]));
    console.log('🗑️ Queue vidée');
  } catch (error) {
    console.error('❌ Erreur vidage queue:', error);
  }
};

/**
 * Supprime des éléments spécifiques de la queue
 */
export const removeFromSyncQueue = async (tempIds: string[]): Promise<void> => {
  try {
    const queue = await getSyncQueue();
    const newQueue = queue.filter(item => !tempIds.includes(item.data.temp_id));
    await AsyncStorage.setItem(STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(newQueue));
    console.log(`🗑️ ${tempIds.length} éléments supprimés de la queue`);
  } catch (error) {
    console.error('❌ Erreur suppression queue:', error);
  }
};

// ============================================================================
// ENREGISTREMENT HORS LIGNE
// ============================================================================

/**
 * Enregistre une présence (en ligne ou hors ligne)
 */
export const recordPresence = async (
  cadetId: string,
  date: string,
  status: 'present' | 'absent' | 'retard',
  commentaire?: string
): Promise<{ success: boolean; offline: boolean }> => {
  const presence: OfflinePresence = {
    cadet_id: cadetId,
    date,
    status,
    commentaire,
    timestamp: new Date().toISOString(),
    temp_id: `presence_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  };
  
  // Si hors ligne, ajouter à la queue
  if (!isOnline) {
    await addToSyncQueue({
      type: 'presence',
      data: presence,
      attempts: 0,
      created_at: new Date().toISOString(),
    });
    return { success: true, offline: true };
  }
  
  // Si en ligne, essayer d'envoyer immédiatement
  // (Ce sera géré par le composant qui appelle cette fonction)
  return { success: true, offline: false };
};

/**
 * Enregistre une inspection d'uniforme (en ligne ou hors ligne)
 */
export const recordInspection = async (
  cadetId: string,
  date: string,
  note?: string
): Promise<{ success: boolean; offline: boolean }> => {
  const inspection: OfflineInspection = {
    cadet_id: cadetId,
    date,
    note,
    timestamp: new Date().toISOString(),
    temp_id: `inspection_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  };
  
  // Si hors ligne, ajouter à la queue
  if (!isOnline) {
    await addToSyncQueue({
      type: 'inspection',
      data: inspection,
      attempts: 0,
      created_at: new Date().toISOString(),
    });
    return { success: true, offline: true };
  }
  
  return { success: true, offline: false };
};

// ============================================================================
// SYNCHRONISATION
// ============================================================================

/**
 * Synchronise la queue avec le serveur
 */
export const syncQueue = async (
  apiUrl: string,
  token: string,
  onProgress?: (current: number, total: number) => void
): Promise<{ success: boolean; synced: number; errors: number }> => {
  try {
    // Vérifier si une synchronisation est déjà en cours
    const isSyncing = await AsyncStorage.getItem(STORAGE_KEYS.IS_SYNCING);
    if (isSyncing === 'true') {
      console.log('⚠️ Synchronisation déjà en cours');
      return { success: false, synced: 0, errors: 0 };
    }
    
    // Marquer la synchronisation comme en cours
    await AsyncStorage.setItem(STORAGE_KEYS.IS_SYNCING, 'true');
    
    const queue = await getSyncQueue();
    
    if (queue.length === 0) {
      await AsyncStorage.setItem(STORAGE_KEYS.IS_SYNCING, 'false');
      return { success: true, synced: 0, errors: 0 };
    }
    
    console.log(`🔄 Synchronisation de ${queue.length} éléments...`);
    
    // Préparer les données pour l'API batch
    const presences: OfflinePresence[] = [];
    const inspections: OfflineInspection[] = [];
    
    queue.forEach(item => {
      if (item.type === 'presence') {
        presences.push(item.data as OfflinePresence);
      } else if (item.type === 'inspection') {
        inspections.push(item.data as OfflineInspection);
      }
    });
    
    // Appeler l'API de synchronisation batch
    const response = await fetch(`${apiUrl}/api/sync/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ presences, inspections }),
    });
    
    if (!response.ok) {
      throw new Error('Échec synchronisation');
    }
    
    const result = await response.json();
    
    // Supprimer les éléments synchronisés avec succès de la queue
    const successTempIds = [
      ...result.presence_results.filter((r: any) => r.success).map((r: any) => r.temp_id),
      ...result.inspection_results.filter((r: any) => r.success).map((r: any) => r.temp_id),
    ];
    
    await removeFromSyncQueue(successTempIds);
    
    // Mettre à jour le cache avec les nouvelles données
    await downloadCacheData(apiUrl, token);
    
    await AsyncStorage.setItem(STORAGE_KEYS.IS_SYNCING, 'false');
    
    console.log(`✅ Synchronisation terminée: ${result.total_synced} synchronisés, ${result.total_errors} erreurs`);
    
    return {
      success: true,
      synced: result.total_synced,
      errors: result.total_errors,
    };
  } catch (error) {
    console.error('❌ Erreur synchronisation:', error);
    await AsyncStorage.setItem(STORAGE_KEYS.IS_SYNCING, 'false');
    return { success: false, synced: 0, errors: 0 };
  }
};

/**
 * Synchronisation automatique (appelée quand connexion restaurée)
 */
const syncQueueAutomatically = async () => {
  // Cette fonction sera appelée avec les bonnes credentials depuis le composant
  console.log('🔄 Synchronisation automatique déclenchée');
};

/**
 * Export de la fonction pour déclencher la sync auto depuis l'app
 */
export const triggerAutoSync = async (apiUrl: string, token: string) => {
  if (isOnline) {
    await syncQueue(apiUrl, token);
  }
};
