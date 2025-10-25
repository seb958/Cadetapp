import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Dimensions
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  nom: string;
  prenom: string;
  username: string;
  email?: string;
  grade: string;
  role: string;
  section_id?: string;
  subgroup_id?: string;
  actif: boolean;
  has_admin_privileges: boolean;
}

interface Section {
  id: string;
  nom: string;
  description?: string;
  responsable_id?: string;
  created_at: string;
}

interface SubGroup {
  id: string;
  nom: string;
  description?: string;
  section_id: string;
  responsable_id?: string;
  created_at: string;
}

interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system_role: boolean;
}

// Structure pour l'organigrame horizontal
interface LevelData {
  level: number;
  nodes: HierarchyNode[];
}

interface HierarchyNode {
  user?: User;
  level: number;
  children: HierarchyNode[];
  type: 'user' | 'section' | 'subgroup';
  section?: Section;
  subgroup?: SubGroup;
  memberCount?: number;
  isExpanded?: boolean;
  x?: number; // Position X pour le layout horizontal
  y?: number; // Position Y pour le layout horizontal
  width?: number;
  height?: number;
}

export default function Organigrame() {
  const [user, setUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [subGroups, setSubGroups] = useState<SubGroup[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [hierarchyData, setHierarchyData] = useState<HierarchyNode[]>([]);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);

  // Obtenir les dimensions de l'écran
  const screenWidth = Dimensions.get('window').width;
  const screenHeight = Dimensions.get('window').height;

  // Gestionnaires de gestes pour zoom et pan
  // (Supprimés - utilisation de ScrollView standard pour la navigation)

  // Vérifier l'authentification
  useEffect(() => {
    checkAuth();
  }, []);

  // Charger les données quand l'utilisateur est authentifié
  useEffect(() => {
    if (user) {
      loadAllData();
    }
  }, [user]);

  // Reconstruire la hiérarchie quand les données changent
  useEffect(() => {
    if (users.length > 0) {
      buildHorizontalHierarchy();
    }
  }, [users, sections, subGroups, searchText, expandedNodes]);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (!token || !userData) {
        setLoading(false);
        router.replace('/');
        return;
      }

      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
    } catch (error) {
      console.error('Erreur lors de la vérification d\'authentification:', error);
      setLoading(false);
      router.replace('/');
    }
  };

  const loadAllData = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('access_token');
      
      // Utiliser le nouvel endpoint public pour l'organigrame
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/organigram/public`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        
        setUsers(data.users);
        setSections(data.sections);
        setRoles(data.roles);
        setSubGroups(data.subgroups);
      } else {
        Alert.alert('Erreur', 'Impossible de charger les données de l\'organigrame');
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
      Alert.alert('Erreur', 'Impossible de charger les données');
    } finally {
      setLoading(false);
    }
  };

  const loadSubGroups = async (sectionsData: Section[], token: string) => {
    try {
      let allSubGroups: SubGroup[] = [];
      
      for (const section of sectionsData) {
        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections/${section.id}/subgroups`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          allSubGroups = [...allSubGroups, ...data];
        }
      }
      
      setSubGroups(allSubGroups);
    } catch (error) {
      console.error('Erreur lors du chargement des sous-groupes:', error);
    }
  };

  // Nouvelle fonction pour construire une hiérarchie horizontale par niveaux
  const buildHorizontalHierarchy = () => {
    let filteredUsers = users;
    
    // Filtrer par recherche si nécessaire
    if (searchText.trim()) {
      const search = searchText.toLowerCase();
      filteredUsers = users.filter(u => 
        u.nom.toLowerCase().includes(search) ||
        u.prenom.toLowerCase().includes(search) ||
        u.grade.toLowerCase().includes(search) ||
        u.role.toLowerCase().includes(search)
      );
    }

    const allNodes: HierarchyNode[] = [];
    const cardWidth = 200;
    const cardHeight = 80;
    const horizontalSpacing = 250;
    const verticalSpacing = 120;

    // Niveau 0: Commandant
    const commandants = filteredUsers.filter(u => 
      u.grade === 'commandant' || 
      u.role === 'encadrement' || 
      u.role === 'Commandant'
    );
    
    commandants.forEach((commandant, index) => {
      allNodes.push({
        user: commandant,
        level: 0,
        type: 'user',
        children: [],
        x: index * horizontalSpacing,
        y: 0,
        width: cardWidth,
        height: cardHeight
      });
    });

    // Niveau 1: Officiers
    const officiers = filteredUsers.filter(u => 
      u.grade === 'lieutenant' || 
      u.role === 'Officier'
    );
    
    officiers.forEach((officier, index) => {
      allNodes.push({
        user: officier,
        level: 1,
        type: 'user',
        children: [],
        x: index * horizontalSpacing,
        y: verticalSpacing,
        width: cardWidth,
        height: cardHeight
      });
    });

    // Niveau 2: Adjudant-Chef d'escadron
    const adjudantChefs = filteredUsers.filter(u => 
      u.role.toLowerCase().includes('adjudant-chef') || 
      u.role === 'Adjudant-Chef d\'escadron' ||
      u.role.toLowerCase() === 'adjudant-chef d\'escadron'
    );
    
    adjudantChefs.forEach((adjudantChef, index) => {
      allNodes.push({
        user: adjudantChef,
        level: 2,
        type: 'user',
        children: [],
        x: index * horizontalSpacing,
        y: verticalSpacing * 2,
        width: cardWidth,
        height: cardHeight
      });
    });

    // Niveau 3: Adjudant d'escadron + Sergents de section + anciens cadet_admin
    const level3Users = filteredUsers.filter(u => 
      // Adjudants d'escadron
      u.role === 'Adjudant d\'escadron' ||
      u.role.toLowerCase() === 'adjudant d\'escadron' ||
      // Sergents de section (Emma Leroy maintenant)
      u.role === 'Sergent de section' ||
      u.role.toLowerCase() === 'sergent de section' ||
      // Administration senior
      (u.role.toLowerCase().includes('senior') && u.role.toLowerCase().includes('administration')) ||
      // Anciens rôles
      u.role === 'cadet_admin'
    );

    level3Users.forEach((level3User, index) => {
      allNodes.push({
        user: level3User,
        level: 3,
        type: 'user',
        children: [],
        x: index * horizontalSpacing,
        y: verticalSpacing * 3,
        width: cardWidth,
        height: cardHeight
      });
    });

    // Niveau 4: Sections (TOUJOURS afficher toutes les sections)
    let level4X = 0;
    sections.forEach((section, sectionIndex) => {
      const sectionUsers = filteredUsers.filter(u => u.section_id === section.id);
      const sectionSubGroups = subGroups.filter(sg => sg.section_id === section.id);
      const totalMembers = sectionUsers.length;

      const sectionNode = {
        section: section,
        level: 4,
        type: 'section' as const,
        memberCount: totalMembers,
        isExpanded: expandedNodes.has(`section-${section.id}`),
        children: [],
        x: level4X,
        y: verticalSpacing * 4,
        width: cardWidth + 50, // Un peu plus large pour les sections
        height: cardHeight
      };
      
      // Debug log pour voir si les sections sont ajoutées
      console.log(`DEBUG: Ajout section "${section.nom}" à la position x=${level4X}, y=${verticalSpacing * 4}, membres=${totalMembers}`);
      
      allNodes.push(sectionNode);
      level4X += horizontalSpacing;
    });

    console.log(`DEBUG: Total nœuds dans hierarchyData: ${allNodes.length}`);
    console.log(`DEBUG: Sections trouvées: ${sections.length}`);
    
    setHierarchyData(allNodes);
  };

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const getGradeDisplayName = (grade: string) => {
    const grades: Record<string, string> = {
      'cadet': 'Cadet',
      'cadet_first_class': 'Cadet 1ère Classe',
      'caporal': 'Caporal',
      'sergent': 'Sergent',
      'adjudant': 'Adjudant',
      'lieutenant': 'Lieutenant',
      'capitaine': 'Capitaine',
      'commandant': 'Commandant'
    };
    return grades[grade] || grade;
  };

  const getRoleDisplayName = (role: string) => {
    // D'abord chercher dans les rôles personnalisés
    const customRole = roles.find(r => r.name === role);
    if (customRole) return customRole.name;
    
    // Puis dans les rôles système
    const systemRoles: Record<string, string> = {
      'cadet': 'Cadet',
      'cadet_responsible': 'Cadet Responsable',
      'cadet_admin': 'Cadet Admin',
      'encadrement': 'Encadrement'
    };
    return systemRoles[role] || role;
  };

  const getUserName = (user: User) => {
    return user ? `${getGradeDisplayName(user.grade)} ${user.prenom} ${user.nom}` : '';
  };

  const getResponsableName = (responsableId?: string) => {
    if (!responsableId) return 'Aucun';
    const responsable = users.find(u => u.id === responsableId);
    return responsable ? getUserName(responsable) : 'Inconnu';
  };

  const getCardStyleByLevel = (level: number) => {
    switch (level) {
      case 0: return styles.commandantCard;
      case 1: return styles.officierCard;
      case 2: return styles.adjudantChefCard;
      case 3: return styles.adjudantCard;
      case 4: return styles.level4Card;
      case 5: return styles.level5Card;
      default: return styles.cadetCard;
    }
  };

  const getTextStyleByLevel = (level: number) => {
    switch (level) {
      case 0: return styles.commandantText;
      case 1: return styles.officierText;
      case 2: return styles.adjudantChefText;
      case 3: return styles.adjudantText;
      default: return styles.normalText;
    }
  };

  const showUserDetails = (selectedUser: User) => {
    const section = selectedUser.section_id ? 
      sections.find(s => s.id === selectedUser.section_id) : null;
    const subgroup = selectedUser.subgroup_id ? 
      subGroups.find(sg => sg.id === selectedUser.subgroup_id) : null;

    let details = `${getUserName(selectedUser)}\n\n`;
    details += `Rôle: ${getRoleDisplayName(selectedUser.role)}\n`;
    details += `Username: ${selectedUser.username}\n`;
    if (selectedUser.email) details += `Email: ${selectedUser.email}\n`;
    if (section) details += `Section: ${section.nom}\n`;
    if (subgroup) details += `Sous-groupe: ${subgroup.nom}\n`;
    details += `Statut: ${selectedUser.actif ? 'Actif' : 'Inactif'}\n`;
    if (selectedUser.has_admin_privileges) details += `Privilèges Admin: Oui`;

    Alert.alert('Détails du profil', details);
  };

  const exportOrganigrame = () => {
    Alert.alert('Bientôt disponible', 'Fonction d\'export en cours de développement');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3182ce" />
          <Text style={styles.loadingText}>Chargement de l'organigrame...</Text>
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
        <Text style={styles.title}>Organigrame de l'Escadron</Text>
        <TouchableOpacity style={styles.exportButton} onPress={exportOrganigrame}>
          <Text style={styles.exportButtonText}>📤</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Rechercher une personne, grade, rôle..."
          value={searchText}
          onChangeText={setSearchText}
          clearButtonMode="while-editing"
        />
      </View>

      <ScrollView style={styles.content} horizontal={true} showsHorizontalScrollIndicator={true}>
        <ScrollView showsVerticalScrollIndicator={true}>
          <Text style={styles.instructions}>
            Glisser horizontalement et verticalement pour naviguer • Toucher une boîte pour plus d'infos
          </Text>
          
          <View style={styles.organigrammeContainer}>
            {hierarchyData.length > 0 ? (
              renderHorizontalOrganigrame()
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>
                  {searchText ? 'Aucun résultat trouvé' : 'Aucune donnée à afficher'}
                </Text>
              </View>
            )}
          </View>
        </ScrollView>
      </ScrollView>
    </SafeAreaView>
  );

  // Nouvelle fonction de rendu horizontal
  function renderHorizontalOrganigrame() {
    const orgWidth = Math.max(800, hierarchyData.length * 250);
    const orgHeight = 600;

    return (
      <View style={[{ width: orgWidth, height: orgHeight, position: 'relative', backgroundColor: 'white' }]}>
        {/* Lignes de connexion */}
        {renderConnectionLines()}
        
        {/* Nœuds de l'organigrame */}
        {hierarchyData.map((node, index) => renderNode(node, index))}
      </View>
    );
  }

  // Rendu des lignes de connexion
  function renderConnectionLines() {
    const lines: React.ReactElement[] = [];
    
    hierarchyData.forEach((node, index) => {
      if (node.level > 0 && node.x !== undefined && node.y !== undefined) {
        // Ligne verticale depuis le niveau supérieur
        const upperLevelNodes = hierarchyData.filter(n => n.level === node.level - 1);
        if (upperLevelNodes.length > 0) {
          const parentNode = upperLevelNodes[0]; // Simplifié pour le prototype
          if (parentNode.x !== undefined && parentNode.y !== undefined) {
            // Ligne verticale
            lines.push(
              <View
                key={`vline-${index}`}
                style={[
                  styles.verticalLine,
                  {
                    left: parentNode.x + (parentNode.width || 200) / 2 - 1,
                    top: parentNode.y + (parentNode.height || 80),
                    height: (node.y || 0) - (parentNode.y + (parentNode.height || 80))
                  }
                ]}
              />
            );
            
            // Ligne horizontale
            lines.push(
              <View
                key={`hline-${index}`}
                style={[
                  styles.horizontalLine,
                  {
                    left: Math.min(parentNode.x + (parentNode.width || 200) / 2, node.x + (node.width || 200) / 2),
                    top: node.y - 1,
                    width: Math.abs(node.x + (node.width || 200) / 2 - (parentNode.x + (parentNode.width || 200) / 2))
                  }
                ]}
              />
            );
          }
        }
      }
    });

    return lines;
  }

  // Rendu d'un nœud individuel
  function renderNode(node: HierarchyNode, index: number) {
    // Vérification debug pour voir les coordonnées
    if (node.type === 'section') {
      console.log(`DEBUG renderNode: Section "${node.section?.nom}" x=${node.x}, y=${node.y}`);
    }
    
    if (node.x === undefined || node.y === undefined) {
      console.log(`DEBUG: Nœud ignoré car coordonnées manquantes - type: ${node.type}, x: ${node.x}, y: ${node.y}`);
      return null;
    }

    const nodeStyle = [
      styles.orgNode,
      getCardStyleByLevel(node.level),
      {
        left: node.x,
        top: node.y,
        width: node.width || 200,
        height: node.height || 80,
      }
    ];

    if (node.type === 'user' && node.user) {
      return (
        <TouchableOpacity
          key={`user-${node.user.id}`}
          style={nodeStyle}
          onPress={() => showUserDetails(node.user!)}
        >
          <Text style={[styles.nodeName, getTextStyleByLevel(node.level)]}>
            {getUserName(node.user)}
          </Text>
          <Text style={styles.nodeRole}>
            {getRoleDisplayName(node.user.role)}
          </Text>
          {node.user.has_admin_privileges && (
            <Text style={styles.adminBadge}>• ADMIN</Text>
          )}
          {!node.user.actif && (
            <Text style={styles.inactiveBadge}>• INACTIF</Text>
          )}
        </TouchableOpacity>
      );
    }

    if (node.type === 'section' && node.section) {
      const sectionId = `section-${node.section.id}`;
      return (
        <TouchableOpacity
          key={sectionId}
          style={nodeStyle}
          onPress={() => toggleNode(sectionId)}
        >
          <Text style={styles.sectionNodeName}>
            {node.isExpanded ? '📂' : '📁'} {node.section.nom}
          </Text>
          <Text style={styles.sectionNodeInfo}>
            {node.memberCount} membre(s)
          </Text>
          <Text style={styles.sectionNodeResponsable}>
            {getResponsableName(node.section.responsable_id)}
          </Text>
        </TouchableOpacity>
      );
    }

    return null;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  backButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  backButtonText: {
    color: '#3182ce',
    fontSize: 16,
    fontWeight: '600',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a365d',
    textAlign: 'center',
    flex: 1,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resetButton: {
    paddingVertical: 8,
    paddingHorizontal: 8,
    marginRight: 8,
  },
  resetButtonText: {
    fontSize: 18,
  },
  exportButton: {
    paddingVertical: 8,
    paddingHorizontal: 8,
  },
  exportButtonText: {
    fontSize: 18,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6b7280',
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  searchInput: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    backgroundColor: '#f9fafb',
  },
  content: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  instructions: {
    textAlign: 'center',
    fontSize: 12,
    color: '#6b7280',
    paddingVertical: 8,
    backgroundColor: '#f0f9ff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  organigrammeContainer: {
    minHeight: 600,
    minWidth: 800, // Largeur fixe pour permettre le scroll horizontal
    padding: 20,
  },
  
  // Lignes de connexion
  verticalLine: {
    position: 'absolute',
    width: 2,
    backgroundColor: '#cbd5e0',
  },
  horizontalLine: {
    position: 'absolute',
    height: 2,
    backgroundColor: '#cbd5e0',
  },
  
  // Nœuds de l'organigrame
  orgNode: {
    position: 'absolute',
    borderRadius: 8,
    padding: 12,
    borderWidth: 2,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  nodeName: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 2,
  },
  nodeRole: {
    fontSize: 11,
    color: '#6b7280',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  adminBadge: {
    fontSize: 9,
    color: '#059669',
    fontWeight: 'bold',
    marginTop: 2,
  },
  inactiveBadge: {
    fontSize: 9,
    color: '#dc2626',
    fontWeight: 'bold',
    marginTop: 2,
  },
  sectionNodeName: {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#2d3748',
  },
  sectionNodeInfo: {
    fontSize: 11,
    color: '#4a5568',
    textAlign: 'center',
    marginTop: 2,
  },
  sectionNodeResponsable: {
    fontSize: 10,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 2,
  },
  
  // Styles par niveau hiérarchique
  commandantCard: {
    backgroundColor: '#fef5e7',
    borderColor: '#f6ad55',
  },
  officierCard: {
    backgroundColor: '#e6fffa',
    borderColor: '#4fd1c7',
  },
  adjudantChefCard: {
    backgroundColor: '#f0fff4',
    borderColor: '#68d391',
  },
  adjudantCard: {
    backgroundColor: '#f7fafc',
    borderColor: '#a0aec0',
  },
  level4Card: {
    backgroundColor: '#fffbf0',
    borderColor: '#f6e05e',
  },
  level5Card: {
    backgroundColor: '#f7fafc',
    borderColor: '#cbd5e0',
  },
  cadetCard: {
    backgroundColor: 'white',
    borderColor: '#e2e8f0',
  },
  
  // Styles de texte par niveau
  commandantText: {
    color: '#744210',
    fontWeight: 'bold',
  },
  officierText: {
    color: '#234e52',
    fontWeight: 'bold',
  },
  adjudantChefText: {
    color: '#22543d',
    fontWeight: '600',
  },
  adjudantText: {
    color: '#2d3748',
    fontWeight: '600',
  },
  normalText: {
    color: '#4a5568',
  },
  
  emptyState: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
});