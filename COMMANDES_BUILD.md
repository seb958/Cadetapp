# Commandes pour Builder l'APK 📱

## Prérequis
- ✅ Phase 1 terminée (modifications offline-first)
- ⚠️ Backend déployé sur Emergent
- ⚠️ URL backend mise à jour dans `.env.production`

---

## Étape 1 : Mettre à Jour l'URL Backend

### Ouvrir le fichier de configuration
```bash
nano /app/frontend/.env.production
```

### Remplacer l'URL
Changez cette ligne :
```
EXPO_PUBLIC_BACKEND_URL=https://votre-app-emergent.com
```

Par votre URL réelle Emergent :
```
EXPO_PUBLIC_BACKEND_URL=https://commandhub-879.emergent.com
```
*(Remplacez par votre vraie URL)*

### Sauvegarder
- Appuyez sur `Ctrl + X`
- Tapez `Y` pour confirmer
- Appuyez sur `Entrée`

---

## Étape 2 : Vérifier la Configuration

### Afficher le contenu du fichier
```bash
cat /app/frontend/.env.production
```

### Vérifier que l'URL est correcte
Vous devriez voir :
```
EXPO_PUBLIC_BACKEND_URL=https://votre-vraie-url.emergent.com
```

---

## Étape 3 : Lancer le Build Android

### Naviguer vers le dossier frontend
```bash
cd /app/frontend
```

### Lancer le build de production
```bash
eas build --platform android --profile production
```

### Ce qui va se passer
1. EAS va préparer l'environnement de build
2. Installation des dépendances (avec `legacy-peer-deps`)
3. Configuration de l'environnement de production
4. Compilation du code JavaScript/TypeScript
5. Build natif Android (Gradle)
6. Signature de l'APK
7. **Temps estimé : 10-15 minutes**

### Suivre la progression
Vous verrez :
```
✔ Build completed!
📦 Download URL: https://expo.dev/artifacts/eas/...
```

---

## Étape 4 : Télécharger l'APK

### Option A : Depuis le Terminal
```bash
# EAS fournira un lien direct, exemple :
wget https://expo.dev/artifacts/eas/votre-build-id.apk -O CommandHub.apk
```

### Option B : Depuis le Navigateur
1. Copiez le lien fourni par EAS
2. Ouvrez-le dans votre navigateur
3. Téléchargez le fichier APK

---

## Étape 5 : Installer l'APK sur Android

### Via USB (Android Debug Bridge)
```bash
adb install CommandHub.apk
```

### Via Transfert de Fichier
1. Transférez l'APK sur votre téléphone (USB, email, cloud)
2. Ouvrez le fichier APK sur votre téléphone
3. Autorisez l'installation depuis sources inconnues si demandé
4. Installez l'application

---

## Étape 6 : Tester l'Application

### Test 1 : Démarrage
```
1. Ouvrir l'app
2. ✅ L'app démarre sans crash
3. ✅ Écran de connexion visible
```

### Test 2 : Connexion
```
1. Entrer vos identifiants
2. ✅ Connexion réussie
3. ✅ Dashboard visible avec indicateur de connexion
```

### Test 3 : Mode Offline
```
1. Désactiver WiFi et données mobiles
2. ✅ Indicateur passe à "Hors ligne"
3. ✅ App reste fonctionnelle
4. Effectuer une inspection
5. ✅ Badge de compteur apparaît (ex: "1")
```

### Test 4 : Synchronisation
```
1. Réactiver WiFi ou données mobiles
2. ✅ Indicateur passe à "En ligne"
3. ✅ Synchronisation automatique démarre
4. ✅ Badge disparaît
5. Ou appuyer sur "Synchroniser" manuellement
```

---

## Dépannage

### Erreur : "Build failed"
**Vérifier :**
1. Que l'URL dans `.env.production` est valide
2. Que le backend Emergent est accessible
3. Les logs du build pour identifier l'erreur spécifique

### Erreur : "Cannot connect to backend"
**Solutions :**
1. Vérifier que l'URL backend est correcte
2. Tester l'URL dans un navigateur
3. Vérifier que le backend Emergent est déployé et actif
4. **Note :** L'app devrait quand même démarrer en mode offline

### APK crash au démarrage
**Vérifier :**
1. Que vous avez bien rebuild l'APK après les modifications Phase 1
2. Que le fichier `.env.production` existe
3. Les logs de l'application (via `adb logcat`)

---

## Commandes Utiles

### Voir l'historique des builds
```bash
eas build:list
```

### Annuler un build en cours
```bash
eas build:cancel
```

### Voir les logs d'un build
```bash
eas build:view <build-id>
```

### Publier une mise à jour OTA (après le premier build)
```bash
eas update --branch production --message "Correction bug X"
```

---

## Vérification Finale Avant Build

### Checklist
- [ ] Backend déployé sur Emergent
- [ ] URL backend copiée
- [ ] `.env.production` mis à jour avec la vraie URL
- [ ] Vérification de l'URL (cat .env.production)
- [ ] Vous êtes dans le dossier `/app/frontend`
- [ ] Vous avez lancé `eas build --platform android --profile production`

---

## Après le Build Réussi

### 1. Télécharger l'APK
```bash
# Utiliser le lien fourni par EAS
```

### 2. Distribuer aux Utilisateurs
Options :
- Email
- Google Drive / Dropbox
- Serveur de fichiers interne
- QR code avec lien de téléchargement

### 3. Tester en Conditions Réelles
- Dans le bâtiment sans signal
- Près des fenêtres avec signal
- Vérifier la synchronisation automatique

### 4. Former les Utilisateurs
Points clés :
- L'app fonctionne hors ligne
- Les données se synchronisent automatiquement
- Possibilité de synchroniser manuellement
- Indicateur de connexion visible

---

## Mises à Jour Futures

### Pour des changements de code uniquement (OTA)
```bash
cd /app/frontend
eas update --branch production --message "Description"
```
**Avantage :** Pas besoin de réinstaller l'APK

### Pour des changements natifs (nouveau build)
```bash
cd /app/frontend
eas build --platform android --profile production
```
**Nécessaire si :**
- Nouvelles dépendances natives
- Changements dans `app.json`
- Changements dans les configurations Android

---

🚀 **Vous êtes maintenant prêt à builder votre APK !**

**Prochaine étape :** Déployer votre backend sur Emergent et copier l'URL.
