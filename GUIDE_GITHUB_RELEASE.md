# Guide Complet : GitHub Releases pour CommandHub 🚀

## Partie 1 : Créer Votre Repository GitHub

### Étape 1 : Créer un Nouveau Repository
1. **Allez sur github.com** et connectez-vous
2. Cliquez sur **"+"** en haut à droite → **"New repository"**
3. **Configuration** :
   - Nom du repository : `CommandHub-Releases`
   - Description : `Releases APK pour CommandHub - Application de gestion escadron`
   - Visibilité : ✅ **Public** (nécessaire pour que les utilisateurs puissent télécharger)
   - ❌ Ne PAS cocher "Add README file"
4. Cliquez sur **"Create repository"**

✅ **Votre repository est créé !** Vous êtes maintenant sur la page du repository vide.

---

## Partie 2 : Créer Votre Première Release

### Étape 1 : Accéder à la Section Releases
1. Sur la page de votre repository, regardez la **barre latérale droite**
2. Cliquez sur **"Releases"** (section "About")
   - Ou allez directement à : `https://github.com/VOTRE-USERNAME/CommandHub-Releases/releases`

### Étape 2 : Créer la Release
1. Cliquez sur **"Create a new release"** ou **"Draft a new release"**
2. Vous arrivez sur la page de création de release

### Étape 3 : Remplir les Informations

#### **Tag version** (obligatoire)
```
v1.0.0
```
- Cliquez sur "Choose a tag"
- Tapez `v1.0.0`
- Cliquez sur "Create new tag: v1.0.0 on publish"

#### **Release title**
```
CommandHub v1.0.0 - Version Initiale
```

#### **Description** (avec exemples)
```markdown
## 🎉 Première version de CommandHub

### ✨ Fonctionnalités Principales
- ✅ Gestion des présences
- ✅ Inspections d'uniformes avec notation détaillée
- ✅ Mode offline avec synchronisation automatique
- ✅ Organigramme de l'escadron
- ✅ Interface d'administration

### 📱 Installation
1. Téléchargez le fichier APK ci-dessous
2. Transférez-le sur votre appareil Android
3. Installez l'application
4. Utilisez vos identifiants pour vous connecter

### 🔧 Configuration Requise
- Android 6.0 ou supérieur
- Connexion internet (pour synchronisation)
- Fonctionne hors ligne

### 📝 Notes Importantes
- Première installation requiert une connexion internet
- Les données sont synchronisées automatiquement
- Approchez-vous d'une fenêtre pour capter le signal
```

#### **Attacher le Fichier APK**
1. **Glissez-déposez** votre fichier APK dans la zone "Attach binaries by dropping them here or selecting them"
2. **Ou cliquez** sur la zone pour sélectionner votre fichier
3. **Nom du fichier recommandé** : `CommandHub-v1.0.0.apk`
4. Attendez que l'upload se termine (barre de progression)

### Étape 4 : Publier la Release
1. Vérifiez que tout est correct
2. Cochez ☐ **"Set as the latest release"** (pour la première release)
3. Cliquez sur **"Publish release"** (bouton vert)

✅ **Votre première release est publiée !**

---

## Partie 3 : Copier le Lien de Téléchargement

### Méthode Directe (Recommandée)
1. Une fois la release publiée, vous voyez votre APK dans la section "Assets"
2. **Clic droit** sur le nom du fichier APK → **"Copier l'adresse du lien"**
3. Le lien ressemble à :
   ```
   https://github.com/VOTRE-USERNAME/CommandHub-Releases/releases/download/v1.0.0/CommandHub-v1.0.0.apk
   ```

### Copie du Lien Complet
Le lien suit ce format :
```
https://github.com/<USERNAME>/CommandHub-Releases/releases/download/<TAG>/<FILENAME>.apk
```

**Exemple concret :**
```
https://github.com/jean879/CommandHub-Releases/releases/download/v1.0.0/CommandHub-v1.0.0.apk
```

---

## Partie 4 : Configurer dans CommandHub

### Étape 1 : Connectez-vous à l'Admin
1. Ouvrez CommandHub (web ou app)
2. Connectez-vous avec un compte admin
3. Allez dans **"Administration"**

### Étape 2 : Accéder aux Paramètres de Version
1. Cliquez sur l'onglet **"Paramètres"**
2. Scrollez jusqu'à la section **"Gestion des Versions APK"**

### Étape 3 : Remplir les Champs
```
Version APK Actuelle: 1.0.0
Version Minimale Supportée: 1.0.0
URL de Téléchargement: [COLLEZ LE LIEN GITHUB ICI]
Forcer la Mise à Jour: ☐ Non (pour l'instant)
```

### Étape 4 : Ajouter les Notes de Version
Cliquez sur **"Ajouter une note"** et ajoutez :
```
Première version stable
Inspections et présences fonctionnelles
Mode offline disponible
```

### Étape 5 : Sauvegarder
Cliquez sur **"Sauvegarder les Paramètres"**

✅ **Configuration terminée !** Les utilisateurs verront maintenant la bannière de téléchargement.

---

## Partie 5 : Créer une Nouvelle Release (Mises à Jour)

### Quand Créer une Nouvelle Release ?
- Changements nécessitant un rebuild APK (voir PHASE1_COMPLETE.md)
- Nouvelles permissions Android
- Changements de version dans app.json
- Modifications natives importantes

### Processus Complet

#### 1. Builder le Nouvel APK
```bash
cd /app/frontend

# Mettre à jour la version dans app.json
# "version": "1.1.0"

# Builder
eas build --platform android --profile production
```

#### 2. Télécharger le Nouvel APK
Une fois le build terminé, téléchargez le fichier APK

#### 3. Créer la Nouvelle Release sur GitHub
1. Allez sur votre repository : `CommandHub-Releases`
2. Cliquez sur **"Releases"** → **"Draft a new release"**
3. **Remplissez** :
   ```
   Tag: v1.1.0
   Title: CommandHub v1.1.0 - Ajout Import Excel
   ```
4. **Description exemple** :
   ```markdown
   ## 📊 Nouvelle Fonctionnalité : Import Excel

   ### ✨ Nouveautés
   - ✅ Import de cadets depuis fichier Excel
   - ✅ Export des présences en Excel
   - ✅ Amélioration de l'interface organigramme

   ### 🐛 Corrections
   - Correction bug synchronisation
   - Amélioration performance offline

   ### 🔄 Mise à Jour
   Téléchargez et installez cette nouvelle version pour bénéficier des nouvelles fonctionnalités.
   ```
5. **Glissez** le nouvel APK
6. **Publiez** la release

#### 4. Mettre à Jour dans l'Admin CommandHub
1. Copiez le nouveau lien de téléchargement
2. Admin → Paramètres → Gestion des Versions
3. **Mettez à jour** :
   ```
   Version APK Actuelle: 1.1.0
   URL de Téléchargement: [NOUVEAU LIEN]
   Notes: Ajoutez les nouvelles features
   ```
4. **Sauvegardez**

✅ **Les utilisateurs verront automatiquement la notification de nouvelle version !**

---

## Partie 6 : Bonnes Pratiques

### Versioning Sémantique
```
v MAJEUR . MINEUR . PATCH
  1     .   2    .  3

MAJEUR : Changements incompatibles (breaking changes)
MINEUR : Nouvelles fonctionnalités compatibles
PATCH : Corrections de bugs
```

**Exemples :**
```
v1.0.0 → v1.0.1 : Correction bug (PATCH)
v1.0.1 → v1.1.0 : Nouvelle fonctionnalité (MINEUR)
v1.1.0 → v2.0.0 : Changement majeur (MAJEUR)
```

### Nommage des Fichiers APK
```
CommandHub-v1.0.0.apk
CommandHub-v1.1.0.apk
CommandHub-v2.0.0.apk
```

### Description des Releases
Toujours inclure :
- ✅ Titre clair avec numéro de version
- ✅ Liste des nouveautés
- ✅ Liste des corrections
- ✅ Instructions d'installation (première release)
- ✅ Notes importantes pour les utilisateurs

### Gestion des Versions dans l'Admin
- **Version Actuelle** : Toujours la dernière version disponible
- **Version Minimale** : Plus ancienne version encore supportée
  - Exemple : Si v1.0.0 → v1.5.0, mais v1.0.0 fonctionne encore
  - Minimale = 1.0.0
  - Si v1.0.0 n'est plus compatible avec le backend
  - Minimale = 1.2.0 (forcer mise à jour)

---

## Partie 7 : FAQ et Troubleshooting

### Q : Puis-je supprimer une ancienne release ?
**R :** Oui, mais attention ! Si des utilisateurs utilisent encore cette version et que le lien est dans l'app, ils ne pourront plus télécharger. Recommandation : Garder au moins les 2-3 dernières versions.

### Q : Comment rendre une release "draft" (brouillon) ?
**R :** Lors de la création, au lieu de "Publish release", cliquez sur "Save draft". Utile pour préparer une release avant de la publier.

### Q : Puis-je modifier une release après publication ?
**R :** Oui ! Allez sur la release → Cliquez sur "Edit" → Modifiez la description ou ajoutez des fichiers → "Update release"

### Q : Que se passe-t-il si je mets le mauvais lien dans l'admin ?
**R :** Les utilisateurs verront une erreur "Impossible d'ouvrir le lien". Corrigez simplement le lien dans l'admin et sauvegardez.

### Q : Combien de temps les fichiers restent-ils sur GitHub ?
**R :** Indéfiniment, tant que le repository existe. GitHub ne supprime pas les releases.

### Q : Y a-t-il une limite de taille pour les fichiers APK ?
**R :** Oui, 2 GB par fichier. Largement suffisant pour un APK (généralement 50-150 MB).

---

## Partie 8 : Workflow Complet Résumé

### Flux de Travail Standard

```
1. Développement de Fonctionnalité
   ↓
2. Mise à Jour de la Version dans app.json
   ↓
3. Build APK via EAS
   eas build --platform android --profile production
   ↓
4. Téléchargement de l'APK
   ↓
5. Création Release sur GitHub
   - Tag: v1.x.x
   - Description avec changelog
   - Upload APK
   ↓
6. Copie du Lien de Téléchargement
   ↓
7. Mise à Jour Admin CommandHub
   - Nouvelle version
   - Nouveau lien
   - Notes de release
   ↓
8. Les Utilisateurs Reçoivent la Notification
   ↓
9. Les Utilisateurs Téléchargent et Installent
```

### Temps Estimés
- Créer repository GitHub : **2 minutes**
- Créer première release : **3 minutes**
- Configurer dans admin : **2 minutes**
- **Total première fois : ~7 minutes**
- **Releases suivantes : ~5 minutes**

---

## Partie 9 : Exemple Complet de Release Notes

### Version 1.0.0 (Initiale)
```markdown
## 🎉 CommandHub v1.0.0 - Lancement Officiel

### Description
Première version stable de CommandHub, l'application de gestion pour l'Escadron 879 Sir-Wilfrid-Laurier.

### ✨ Fonctionnalités
- **Gestion des Présences** : Enregistrement rapide avec statut et commentaires
- **Inspections d'Uniformes** : Notation détaillée selon critères configurables
- **Mode Offline** : Fonctionne sans connexion, synchronisation automatique
- **Organigramme** : Visualisation de la structure de l'escadron
- **Administration** : Gestion des utilisateurs, sections, et paramètres

### 📱 Installation
1. Téléchargez `CommandHub-v1.0.0.apk`
2. Autorisez l'installation depuis sources inconnues
3. Installez l'application
4. Connectez-vous avec vos identifiants

### 🔧 Prérequis
- Android 6.0 ou supérieur
- Connexion internet pour première connexion
- Mode offline disponible après synchronisation initiale

### 📝 Notes
- Idéal pour utilisation dans bâtiments avec signal faible
- Synchronisation automatique près des fenêtres
- Données sécurisées avec authentification JWT
```

### Version 1.1.0 (Mise à Jour)
```markdown
## 📊 CommandHub v1.1.0 - Import/Export Excel

### Nouveautés
- ✅ **Import Excel** : Importer une liste de cadets depuis fichier Excel
- ✅ **Export Excel** : Exporter les présences et inspections
- ✅ **Amélioration Interface** : Organigramme avec zoom/pan
- ✅ **Notifications** : Alertes pour absences consécutives

### Améliorations
- 🚀 Performance de synchronisation améliorée
- 🎨 Interface organigramme plus fluide
- 📱 Meilleure gestion du mode offline

### Corrections
- 🐛 Correction bug synchronisation multiple
- 🐛 Correction affichage dates en mode offline
- 🐛 Correction scroll dans liste des cadets

### 🔄 Mise à Jour Recommandée
Cette version apporte des fonctionnalités importantes. Téléchargez et installez pour en bénéficier.

### Installation
Si vous avez déjà v1.0.0, téléchargez simplement v1.1.0 et installez par-dessus. Vos données seront préservées.
```

---

## Partie 10 : Checklist Avant Publication

### ✅ Checklist Repository GitHub
- [ ] Repository créé avec nom clair
- [ ] Visibilité = Public
- [ ] Description du repository ajoutée

### ✅ Checklist Première Release
- [ ] Tag suit format vX.Y.Z
- [ ] Titre clair avec numéro de version
- [ ] Description complète avec fonctionnalités
- [ ] Fichier APK uploadé (nom clair)
- [ ] "Set as latest release" coché
- [ ] Release publiée (pas draft)

### ✅ Checklist Configuration Admin
- [ ] Lien de téléchargement copié
- [ ] Version actuelle = version de la release
- [ ] Version minimale configurée
- [ ] Notes de version ajoutées
- [ ] Paramètres sauvegardés
- [ ] Testé la bannière sur l'app

### ✅ Checklist Test Utilisateur
- [ ] Bannière visible sur dashboard
- [ ] Lien de téléchargement fonctionne
- [ ] APK télécharge correctement
- [ ] Installation réussie
- [ ] App fonctionne après installation

---

🎉 **Vous êtes maintenant prêt à gérer les releases de CommandHub sur GitHub !**

**Prochaine étape :** Une fois votre APK prêt, créez votre première release et configurez l'URL dans l'admin.
