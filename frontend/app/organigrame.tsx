import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator
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

// Structure hiérarchique pour l'organigrame
interface HierarchyNode {
  user?: User;
  level: number;
  children: HierarchyNode[];
  type: 'user' | 'section' | 'subgroup';
  section?: Section;
  subgroup?: SubGroup;
  memberCount?: number;
  isExpanded?: boolean;
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
      buildHierarchy();
    }
  }, [users, sections, subGroups, searchText]);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (!token || !userData) {
        router.replace('/');
        return;
      }

      setUser(JSON.parse(userData));
    } catch (error) {
      console.error('Erreur lors de la vérification d\'authentification:', error);
      router.replace('/');
    }
  };

  const loadAllData = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('access_token');
      
      const [usersRes, sectionsRes, rolesRes] = await Promise.all([
        fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/users`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/sections`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/roles`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (usersRes.ok && sectionsRes.ok && rolesRes.ok) {
        const usersData = await usersRes.json();
        const sectionsData = await sectionsRes.json();
        const rolesData = await rolesRes.json();

        setUsers(usersData);
        setSections(sectionsData);
        setRoles(rolesData);

        // Charger les sous-groupes pour chaque section
        await loadSubGroups(sectionsData, token);
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

  const buildHierarchy = () => {
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

    const hierarchy: HierarchyNode[] = [];

    // Niveau 0: Commandant (role = 'encadrement' ou grade = 'commandant')
    const commandants = filteredUsers.filter(u => 
      u.grade === 'commandant' || (u.role === 'encadrement' && u.grade !== 'lieutenant')
    );
    
    commandants.forEach(commandant => {
      const commandantNode: HierarchyNode = {
        user: commandant,
        level: 0,
        type: 'user',
        children: []
      };

      // Niveau 1: Officiers (lieutenants)
      const officiers = filteredUsers.filter(u => 
        u.grade === 'lieutenant' || (u.role === 'encadrement' && u.grade === 'lieutenant')
      );
      
      officiers.forEach(officier => {
        commandantNode.children.push({
          user: officier,
          level: 1,
          type: 'user',
          children: buildLevel2AndBelow(filteredUsers)
        });
      });

      // Si pas d'officiers, directement les niveaux inférieurs
      if (officiers.length === 0) {
        commandantNode.children = buildLevel2AndBelow(filteredUsers);
      }

      hierarchy.push(commandantNode);
    });

    // S'il n'y a pas de commandant, commencer par les officiers
    if (commandants.length === 0) {
      const officiers = filteredUsers.filter(u => u.grade === 'lieutenant');
      officiers.forEach(officier => {
        hierarchy.push({
          user: officier,
          level: 0, // Devient le niveau 0 s'il n'y a pas de commandant
          type: 'user',
          children: buildLevel2AndBelow(filteredUsers)
        });
      });

      // S'il n'y a ni commandant ni officier, commencer par les adjudants
      if (officiers.length === 0) {
        hierarchy.push(...buildLevel2AndBelow(filteredUsers));
      }
    }

    setHierarchyData(hierarchy);
  };

  const buildLevel2AndBelow = (filteredUsers: User[]): HierarchyNode[] => {
    const nodes: HierarchyNode[] = [];

    // Niveau 2: Adjudant-Chef d'escadron
    const adjudantChefs = filteredUsers.filter(u => 
      u.role.toLowerCase().includes('adjudant-chef') || u.role.toLowerCase().includes('adjudant_chef')
    );
    
    adjudantChefs.forEach(adjudantChef => {
      nodes.push({
        user: adjudantChef,
        level: 2,
        type: 'user',
        children: buildLevel3AndBelow(filteredUsers)
      });
    });

    // Niveau 3: Adjudant d'escadron + Cadet Senior à l'administration
    const level3Users = filteredUsers.filter(u => 
      u.role.toLowerCase().includes('adjudant') && !u.role.toLowerCase().includes('chef') ||
      u.role.toLowerCase().includes('senior') && u.role.toLowerCase().includes('administration')
    );

    level3Users.forEach(level3User => {
      nodes.push({
        user: level3User,
        level: 3,
        type: 'user',
        children: buildSectionsAndLevel4(filteredUsers)
      });
    });

    // Si pas de niveau 2 et 3, directement les sections
    if (adjudantChefs.length === 0 && level3Users.length === 0) {
      nodes.push(...buildSectionsAndLevel4(filteredUsers));
    }

    return nodes;
  };

  const buildSectionsAndLevel4 = (filteredUsers: User[]): HierarchyNode[] => {
    const nodes: HierarchyNode[] = [];

    // Niveau 4: Sections + Cadet à l'administration
    const adminLevel4 = filteredUsers.filter(u => 
      u.role.toLowerCase().includes('administration') && 
      !u.role.toLowerCase().includes('senior') &&
      !u.role.toLowerCase().includes('adjoint')
    );

    adminLevel4.forEach(adminUser => {
      nodes.push({
        user: adminUser,
        level: 4,
        type: 'user',
        children: []
      });
    });

    // Sections avec leurs sous-groupes
    sections.forEach(section => {
      const sectionUsers = filteredUsers.filter(u => u.section_id === section.id);
      const sectionSubGroups = subGroups.filter(sg => sg.section_id === section.id);
      const totalMembers = sectionUsers.length;

      const sectionNode: HierarchyNode = {
        section: section,
        level: 4,
        type: 'section',
        memberCount: totalMembers,
        isExpanded: expandedNodes.has(`section-${section.id}`),
        children: []
      };

      if (sectionNode.isExpanded) {
        // Niveau 5: Sous-groupes + Cadet adjoint à l'administration
        const adminLevel5 = filteredUsers.filter(u => 
          u.role.toLowerCase().includes('adjoint') && u.role.toLowerCase().includes('administration')
        );

        adminLevel5.forEach(adminUser => {
          sectionNode.children.push({
            user: adminUser,
            level: 5,
            type: 'user',
            children: []
          });
        });

        // Sous-groupes
        sectionSubGroups.forEach(subgroup => {
          const subgroupUsers = sectionUsers.filter(u => u.subgroup_id === subgroup.id);
          const subgroupNode: HierarchyNode = {
            subgroup: subgroup,
            level: 5,
            type: 'subgroup',
            memberCount: subgroupUsers.length,
            isExpanded: expandedNodes.has(`subgroup-${subgroup.id}`),
            children: []
          };

          if (subgroupNode.isExpanded) {
            // Niveau 6: Cadets individuels
            subgroupUsers.forEach(cadet => {
              subgroupNode.children.push({
                user: cadet,
                level: 6,
                type: 'user',
                children: []
              });
            });
          }

          sectionNode.children.push(subgroupNode);
        });

        // Cadets directement dans la section (sans sous-groupe)
        const directSectionUsers = sectionUsers.filter(u => !u.subgroup_id);
        directSectionUsers.forEach(cadet => {
          sectionNode.children.push({
            user: cadet,
            level: 5,
            type: 'user',
            children: []
          });
        });
      }

      nodes.push(sectionNode);
    });

    return nodes;
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

  const renderHierarchyNode = (node: HierarchyNode, index: number) => {
    const indentLevel = node.level * 20;

    if (node.type === 'section') {
      const sectionId = `section-${node.section!.id}`;
      return (
        <View key={sectionId} style={[styles.nodeContainer, { marginLeft: indentLevel }]}>
          <TouchableOpacity
            style={styles.sectionCard}
            onPress={() => toggleNode(sectionId)}
          >
            <View style={styles.sectionHeader}>
              <View style={styles.sectionInfo}>
                <Text style={styles.sectionName}>
                  {node.isExpanded ? '📂' : '📁'} {node.section!.nom}
                </Text>
                <Text style={styles.sectionDetails}>
                  Responsable: {getResponsableName(node.section!.responsable_id)}
                </Text>
                <Text style={styles.sectionDetails}>
                  {node.memberCount} membre(s)
                </Text>
              </View>
              <Text style={styles.expandIcon}>
                {node.isExpanded ? '▼' : '▶'}
              </Text>
            </View>
          </TouchableOpacity>
          
          {node.isExpanded && node.children.map((child, childIndex) => 
            renderHierarchyNode(child, childIndex)
          )}
        </View>
      );
    }

    if (node.type === 'subgroup') {
      const subgroupId = `subgroup-${node.subgroup!.id}`;
      return (
        <View key={subgroupId} style={[styles.nodeContainer, { marginLeft: indentLevel }]}>
          <TouchableOpacity
            style={styles.subgroupCard}
            onPress={() => toggleNode(subgroupId)}
          >
            <View style={styles.subgroupHeader}>
              <View style={styles.subgroupInfo}>
                <Text style={styles.subgroupName}>
                  {node.isExpanded ? '📦' : '📦'} {node.subgroup!.nom}
                </Text>
                <Text style={styles.subgroupDetails}>
                  Commandant: {getResponsableName(node.subgroup!.responsable_id)}
                </Text>
                <Text style={styles.subgroupDetails}>
                  {node.memberCount} membre(s)
                </Text>
              </View>
              <Text style={styles.expandIcon}>
                {node.isExpanded ? '▼' : '▶'}
              </Text>
            </View>
          </TouchableOpacity>
          
          {node.isExpanded && node.children.map((child, childIndex) => 
            renderHierarchyNode(child, childIndex)
          )}
        </View>
      );
    }

    // Type 'user'
    if (node.user) {
      return (
        <View key={node.user.id} style={[styles.nodeContainer, { marginLeft: indentLevel }]}>
          <TouchableOpacity 
            style={[styles.userCard, getCardStyleByLevel(node.level)]}
            onPress={() => showUserDetails(node.user!)}
          >
            <View style={styles.userInfo}>
              <Text style={[styles.userName, getTextStyleByLevel(node.level)]}>
                {getUserName(node.user)}
              </Text>
              <Text style={styles.userRole}>
                {getRoleDisplayName(node.user.role)}
              </Text>
              {node.user.has_admin_privileges && (
                <Text style={styles.adminBadge}>• ADMIN</Text>
              )}
              {!node.user.actif && (
                <Text style={styles.inactiveBadge}>• INACTIF</Text>
              )}
            </View>
          </TouchableOpacity>
          
          {node.children.map((child, childIndex) => 
            renderHierarchyNode(child, childIndex)
          )}
        </View>
      );
    }

    return null;
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

      <ScrollView style={styles.content} showsVerticalScrollIndicator={true}>
        <View style={styles.hierarchyContainer}>
          <Text style={styles.sectionSubtitle}>
            Structure hiérarchique • {users.filter(u => u.actif).length} membre(s) actif(s)
          </Text>
          
          {hierarchyData.length > 0 ? (
            hierarchyData.map((node, index) => renderHierarchyNode(node, index))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>
                {searchText ? 'Aucun résultat trouvé' : 'Aucune donnée à afficher'}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
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
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a365d',
    textAlign: 'center',
    flex: 1,
  },
  exportButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  exportButtonText: {
    fontSize: 20,
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
    paddingVertical: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  searchInput: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#f9fafb',
  },
  content: {
    flex: 1,
  },
  hierarchyContainer: {
    padding: 20,
  },
  sectionSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4a5568',
    marginBottom: 20,
    textAlign: 'center',
  },
  nodeContainer: {
    marginVertical: 4,
  },
  
  // Styles pour les sections
  sectionCard: {
    backgroundColor: '#edf2f7',
    borderRadius: 8,
    padding: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#3182ce',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionInfo: {
    flex: 1,
  },
  sectionName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 4,
  },
  sectionDetails: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 2,
  },
  expandIcon: {
    fontSize: 16,
    color: '#6b7280',
  },
  
  // Styles pour les sous-groupes
  subgroupCard: {
    backgroundColor: '#f0fff4',
    borderRadius: 6,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#48bb78',
  },
  subgroupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subgroupInfo: {
    flex: 1,
  },
  subgroupName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 3,
  },
  subgroupDetails: {
    fontSize: 13,
    color: '#4a5568',
    marginBottom: 1,
  },
  
  // Styles pour les utilisateurs
  userCard: {
    borderRadius: 6,
    padding: 10,
    marginVertical: 2,
    borderWidth: 1,
  },
  userInfo: {
    flexDirection: 'column',
  },
  userName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  userRole: {
    fontSize: 12,
    color: '#6b7280',
  },
  adminBadge: {
    fontSize: 10,
    color: '#059669',
    fontWeight: 'bold',
    marginTop: 2,
  },
  inactiveBadge: {
    fontSize: 10,
    color: '#dc2626',
    fontWeight: 'bold',
    marginTop: 2,
  },
  
  // Styles par niveau hiérarchique
  commandantCard: {
    backgroundColor: '#fef5e7',
    borderColor: '#f6ad55',
    borderWidth: 2,
  },
  officierCard: {
    backgroundColor: '#e6fffa',
    borderColor: '#4fd1c7',
    borderWidth: 2,
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
    fontSize: 16,
    fontWeight: 'bold',
  },
  officierText: {
    color: '#234e52',
    fontSize: 15,
    fontWeight: 'bold',
  },
  adjudantChefText: {
    color: '#22543d',
    fontSize: 15,
    fontWeight: '600',
  },
  adjudantText: {
    color: '#2d3748',
    fontSize: 14,
    fontWeight: '600',
  },
  normalText: {
    color: '#4a5568',
    fontSize: 14,
  },
  
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
});