/**
 * Composant de prise de présence optimisé avec swipe
 * - Organisation par sections (collapsible)
 * - Recherche en temps réel
 * - Swipe droite = Présent (disparaît)
 * - Non swipé = Absent automatiquement
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Animated,
  Alert,
  ScrollView,
} from 'react-native';
import { Swipeable } from 'react-native-gesture-handler';

interface Cadet {
  id: string;
  nom: string;
  prenom: string;
  grade: string;
  section_id: string;
}

interface Section {
  id: string;
  nom: string;
  cadets: Cadet[];
}

interface SwipeableAttendanceProps {
  sections: Section[];
  onComplete: (presentIds: string[]) => void;
  onCancel: () => void;
  onAddGuest?: () => void;
}

export const SwipeableAttendance: React.FC<SwipeableAttendanceProps> = ({
  sections,
  onComplete,
  onCancel,
  onAddGuest,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [presentCadets, setPresentCadets] = useState<Set<string>>(new Set());
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  // Filtrer les cadets selon la recherche
  const filteredSections = sections.map(section => {
    const filteredCadets = section.cadets.filter(cadet => {
      // Exclure les cadets déjà marqués présents
      if (presentCadets.has(cadet.id)) return false;
      
      // Filtrer selon la recherche
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const fullName = `${cadet.prenom} ${cadet.nom}`.toLowerCase();
        const grade = cadet.grade.toLowerCase();
        return fullName.includes(query) || grade.includes(query);
      }
      return true;
    });
    
    return { ...section, cadets: filteredCadets };
  }).filter(section => section.cadets.length > 0);

  const toggleSection = (sectionId: string) => {
    const newCollapsed = new Set(collapsedSections);
    if (newCollapsed.has(sectionId)) {
      newCollapsed.delete(sectionId);
    } else {
      newCollapsed.add(sectionId);
    }
    setCollapsedSections(newCollapsed);
  };

  const markPresent = (cadetId: string) => {
    setPresentCadets(prev => new Set(prev).add(cadetId));
  };

  const handleComplete = () => {
    const presentIds = Array.from(presentCadets);
    const totalCadets = sections.reduce((sum, s) => sum + s.cadets.length, 0);
    const absentCount = totalCadets - presentIds.length;
    
    // Utiliser window.confirm pour web (fonctionne aussi sur mobile)
    const message = `${presentIds.length} présent(s)\n${absentCount} absent(s)\n\nLes cadets non-swipés seront marqués absents.\n\nConfirmer ?`;
    
    if (window.confirm(message)) {
      console.log('✅ Confirmation utilisateur - appel onComplete avec', presentIds.length, 'présents');
      onComplete(presentIds);
    } else {
      console.log('❌ Annulé par l\'utilisateur');
    }
  };

  const renderRightActions = () => (
    <View style={styles.swipeAction}>
      <Text style={styles.swipeActionText}>✓ Présent</Text>
    </View>
  );

  const renderCadet = (cadet: Cadet) => (
    <Swipeable
      key={cadet.id}
      renderRightActions={renderRightActions}
      onSwipeableOpen={() => markPresent(cadet.id)}
      overshootRight={false}
      rightThreshold={40}
    >
      <View style={styles.cadetCard}>
        <View style={styles.cadetInfo}>
          <Text style={styles.cadetGrade}>{cadet.grade}</Text>
          <Text style={styles.cadetName}>
            {cadet.prenom} {cadet.nom}
          </Text>
        </View>
        <Text style={styles.swipeHint}>← Swipe</Text>
      </View>
    </Swipeable>
  );

  const totalRemaining = filteredSections.reduce((sum, s) => sum + s.cadets.length, 0);
  const totalPresent = presentCadets.size;

  return (
    <View style={styles.container}>
      {/* Header avec stats */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Prise de Présence</Text>
        <View style={styles.stats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{totalPresent}</Text>
            <Text style={styles.statLabel}>Présents</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{totalRemaining}</Text>
            <Text style={styles.statLabel}>Restants</Text>
          </View>
        </View>
      </View>

      {/* Barre de recherche */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="🔍 Rechercher par nom ou grade..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => setSearchQuery('')}
          >
            <Text style={styles.clearButtonText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Liste des sections */}
      <ScrollView 
        style={styles.sectionsContainer}
        showsVerticalScrollIndicator={true}
        nestedScrollEnabled={true}
      >
        {filteredSections.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>
              {searchQuery 
                ? '🔍 Aucun cadet trouvé'
                : '✅ Tous les cadets ont été marqués présents !'}
            </Text>
          </View>
        ) : (
          filteredSections.map(section => {
            const isCollapsed = collapsedSections.has(section.id);
            return (
              <View key={section.id} style={styles.sectionContainer}>
                <TouchableOpacity
                  style={styles.sectionHeader}
                  onPress={() => toggleSection(section.id)}
                >
                  <Text style={styles.sectionName}>
                    {isCollapsed ? '▶' : '▼'} {section.nom}
                  </Text>
                  <Text style={styles.sectionCount}>
                    {section.cadets.length} cadet(s)
                  </Text>
                </TouchableOpacity>
                
                {!isCollapsed && (
                  <View style={styles.cadetsContainer}>
                    {section.cadets.map(cadet => renderCadet(cadet))}
                  </View>
                )}
              </View>
            );
          })
        )}
      </ScrollView>

      {/* Boutons d'action */}
      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.button, styles.cancelButton]}
          onPress={onCancel}
        >
          <Text style={styles.cancelButtonText}>Annuler</Text>
        </TouchableOpacity>
        
        {onAddGuest && (
          <TouchableOpacity
            style={[styles.button, styles.guestButton]}
            onPress={onAddGuest}
          >
            <Text style={styles.guestButtonText}>👤 Invité</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[styles.button, styles.confirmButton]}
          onPress={handleComplete}
        >
          <Text style={styles.confirmButtonText}>
            Valider ({totalPresent} présent{totalPresent > 1 ? 's' : ''})
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#FFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  searchContainer: {
    backgroundColor: '#FFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 44,
    backgroundColor: '#F0F0F0',
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  clearButton: {
    marginLeft: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#CCC',
    justifyContent: 'center',
    alignItems: 'center',
  },
  clearButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  sectionsContainer: {
    flex: 1,
    padding: 16,
  },
  sectionContainer: {
    marginBottom: 16,
    backgroundColor: '#FFF',
    borderRadius: 8,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#007AFF',
  },
  sectionName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFF',
  },
  sectionCount: {
    fontSize: 14,
    color: '#FFF',
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  cadetsContainer: {
    backgroundColor: '#FFF',
  },
  cadetCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  cadetInfo: {
    flex: 1,
  },
  cadetGrade: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  cadetName: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  swipeHint: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  swipeAction: {
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    width: 120,
  },
  swipeActionText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
  },
  actionButtons: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
    gap: 12,
  },
  button: {
    flex: 1,
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#F0F0F0',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  confirmButton: {
    backgroundColor: '#007AFF',
  },
  confirmButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  guestButton: {
    backgroundColor: '#10b981',
  },
  guestButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
