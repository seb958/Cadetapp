# Améliorations à implémenter

## 1. Filtres utilisateurs (dans la section Utilisateurs)
- Ajouter 3 dropdowns : Grade, Rôle, Section
- Ajouter un bouton "Réinitialiser les filtres"
- Connecter au backend avec les paramètres de requête

## 2. Checkbox "Privilèges Admin" (dans le modal utilisateur)
- Ajouter un Switch pour "Privilèges d'administration"
- Connecter à userForm.has_admin_privileges
- Modifier saveUser() pour inclure ce champ

## 3. Affichage des privilèges admin (dans la liste utilisateurs)
- Ajouter un badge "Admin" si has_admin_privileges = true
- Modifier l'affichage pour montrer rôle + privilège admin

## 4. Onglet Rôles (nouveau)
- Interface de création/modification des rôles
- Liste des permissions disponibles
- Gestion des rôles système (non supprimables)

## Structure des changements nécessaires :
1. Modifier la section utilisateurs pour ajouter les filtres
2. Modifier le modal utilisateur pour ajouter la checkbox
3. Modifier saveUser() pour inclure has_admin_privileges 
4. Ajouter l'affichage des privilèges dans la liste
5. Créer l'onglet Rôles avec interface complète