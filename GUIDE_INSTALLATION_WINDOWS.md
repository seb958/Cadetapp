# 🪟 Guide d'Installation et Build APK - Windows

## Version 1.0.0 - CommandHub

---

## 📥 ÉTAPE 1 : Télécharger le Projet

### Téléchargement du ZIP

Le projet est packagé dans un fichier ZIP de **74 MB** (sans node_modules pour réduire la taille).

**Lien de téléchargement :**
```
https://command-central-9.emergent.host/commandhub-project.zip
```

**Alternative :** Si le lien ne fonctionne pas, demandez-moi de placer le fichier dans un emplacement accessible.

---

## 📂 ÉTAPE 2 : Extraire le Projet

1. **Téléchargez** le fichier `commandhub-project.zip`
2. **Extrayez-le** dans un dossier de votre choix, par exemple :
   ```
   C:\Users\Admin\Documents\CommandHub\
   ```
3. **Vérifiez** que vous avez cette structure :
   ```
   CommandHub/
   ├── frontend/
   │   ├── app/
   │   ├── components/
   │   ├── hooks/
   │   ├── services/
   │   ├── app.json
   │   ├── eas.json
   │   ├── package.json
   │   └── ...
   └── backend/
       ├── server.py
       ├── requirements.txt
       └── ...
   ```

---

## 🔧 ÉTAPE 3 : Installer les Dépendances

### Prérequis
- ✅ **Node.js** installé (version 18 ou supérieure)
- ✅ **npm** installé (vient avec Node.js)

Vérifiez avec :
```cmd
node --version
npm --version
```

### Installer les Dépendances du Projet

1. **Ouvrez CMD** (Windows + R, tapez `cmd`)

2. **Naviguez vers le dossier frontend :**
   ```cmd
   cd C:\Users\Admin\Documents\CommandHub\frontend
   ```

3. **Installez les dépendances :**
   ```cmd
   npm install
   ```
   
   ⏳ **Attention :** Cela peut prendre 5-10 minutes et télécharger ~500 MB de packages.

4. **Attendez** que vous voyiez :
   ```
   added XXX packages in XXXs
   ```

---

## 🚀 ÉTAPE 4 : Configuration EAS Build

### 4.1 Installer EAS CLI Globalement

```cmd
npm install -g eas-cli
```

### 4.2 Se Connecter à Expo

```cmd
eas login
```

**Entrez vos identifiants :**
- Username : `seb958`
- Password : [votre mot de passe Expo]

### 4.3 Configurer l'URL Backend de Production

**⚠️ IMPORTANT :** Utilisez l'URL de production, pas celle de développement !

```cmd
eas secret:create --scope project --name EXPO_PUBLIC_BACKEND_URL --value "https://command-central-9.emergent.host"
```

**Confirmation :**
```
✔ Created a new secret EXPO_PUBLIC_BACKEND_URL on project @seb958/commandhub.
```

### 4.4 Vérifier les Secrets (Optionnel)

```cmd
eas secret:list
```

Vous devriez voir :
```
┌──────────────────────────┬─────────────────────────────────────────┐
│ Name                     │ Value                                   │
├──────────────────────────┼─────────────────────────────────────────┤
│ EXPO_PUBLIC_BACKEND_URL  │ https://command-central-9.emergent.host │
└──────────────────────────┴─────────────────────────────────────────┘
```

---

## 📱 ÉTAPE 5 : Générer l'APK

### 5.1 Naviguer vers le Dossier Frontend

```cmd
cd C:\Users\Admin\Documents\CommandHub\frontend
```

### 5.2 Lancer le Build Production

```cmd
eas build --platform android --profile production
```

**Ce qui va se passer :**

1. **Configuration du build**
   ```
   ✔ Using remote Android credentials (Expo server)
   ✔ Checking if this build already exists...
   ```

2. **Questions possibles** (répondez Y ou appuyez sur Entrée) :
   - "Generate a new Android Keystore?" → **Y** (première fois)
   - "Would you like to automatically create a bundle identifier?" → **Y**

3. **Upload du code**
   ```
   ✔ Uploading to EAS Build
   ✔ Queued build
   ```

4. **Lien vers le build :**
   ```
   🔗 https://expo.dev/accounts/seb958/projects/commandhub/builds/[BUILD_ID]
   ```

### 5.3 Suivre la Progression du Build

**Option A - Dans CMD :**
La progression s'affichera automatiquement.

**Option B - Dans le Navigateur :**
1. Ouvrez le lien fourni dans votre navigateur
2. Connectez-vous avec votre compte Expo
3. Suivez le build en temps réel

**Durée estimée :** 15-20 minutes ⏱️

---

## 📥 ÉTAPE 6 : Télécharger l'APK

### Une fois le build terminé (✅ Success)

**Méthode 1 - Via CMD :**
```cmd
eas build:download --platform android --latest
```

L'APK sera téléchargé dans votre dossier actuel.

**Méthode 2 - Via le Navigateur :**
1. Allez sur votre [dashboard Expo](https://expo.dev/accounts/seb958/projects/commandhub/builds)
2. Cliquez sur votre dernier build
3. Cliquez sur **"Download"** pour télécharger l'APK

**Nom du fichier :** `commandhub-[BUILD_ID].apk` (environ 40-60 MB)

---

## 📲 ÉTAPE 7 : Installer l'APK sur Android

### Sur votre Appareil Android

1. **Transférez l'APK** sur votre téléphone/tablette Android :
   - Via câble USB
   - Via email
   - Via Google Drive, etc.

2. **Activez "Sources inconnues" :**
   - Paramètres → Sécurité → Sources inconnues
   - OU lors de l'installation, autorisez l'installation

3. **Ouvrez le fichier APK** et appuyez sur **"Installer"**

4. **Lancez l'application** CommandHub

### Premier Lancement

1. **Connexion requise** (connexion internet nécessaire au premier démarrage)
2. **Identifiants administrateur :**
   - Username : `aadministrateur`
   - Password : `admin123`

3. **Après connexion :** L'app fonctionne en mode hors ligne !

---

## 🔄 Publier une Mise à Jour (Sans Rebuild)

### Pour des Modifications JavaScript/React Native

```cmd
cd C:\Users\Admin\Documents\CommandHub\frontend
eas update --branch production --message "Description de la mise à jour"
```

**Avantages :**
- Les utilisateurs reçoivent automatiquement la mise à jour
- Pas besoin de redistribuer l'APK
- Mise à jour au prochain lancement de l'app

**Limitations :**
- Fonctionne uniquement pour les modifications JS/TS/JSX/TSX
- Ne fonctionne PAS pour :
  - Changements natifs (nouvelle bibliothèque native)
  - Modifications de permissions Android
  - Changement d'icône ou splash screen

---

## 🔧 Dépannage

### Erreur "No development build installed"

**Solution :**
```cmd
cd C:\Users\Admin\Documents\CommandHub\frontend
eas build --platform android --profile production --clear-cache
```

### Erreur "EXPO_PUBLIC_BACKEND_URL not found"

**Solution :**
```cmd
eas secret:delete --name EXPO_PUBLIC_BACKEND_URL
eas secret:create --scope project --name EXPO_PUBLIC_BACKEND_URL --value "https://command-central-9.emergent.host"
```

### Erreur lors de npm install

**Solution :**
```cmd
cd C:\Users\Admin\Documents\CommandHub\frontend
rmdir /s node_modules
del package-lock.json
npm install
```

### Build échoue avec erreur de certificat Android

**Solution :** Laissez Expo générer automatiquement les certificats :
```cmd
eas build --platform android --profile production
```
Répondez **Y** quand il demande de générer un nouveau keystore.

---

## 📊 Informations de Configuration

| Paramètre | Valeur |
|-----------|--------|
| **Nom App** | CommandHub |
| **Version** | 1.0.0 |
| **Package ID** | com.escadron879.commandhub |
| **Backend URL** | https://command-central-9.emergent.host |
| **Compte Expo** | seb958 |
| **Project ID** | a7003ce2-d0f5-44c1-b1c8-47aac49695ba |

---

## ✅ Checklist Complète

- [ ] Node.js et npm installés
- [ ] Projet téléchargé et extrait
- [ ] Dépendances installées (`npm install`)
- [ ] EAS CLI installé (`npm install -g eas-cli`)
- [ ] Connecté à Expo (`eas login`)
- [ ] URL backend configurée (secret créé)
- [ ] Build lancé (`eas build`)
- [ ] APK téléchargé
- [ ] APK testé sur appareil Android
- [ ] Application fonctionne correctement

---

## 🎯 Prochaines Étapes Après Installation

1. **Testez toutes les fonctionnalités :**
   - ✅ Connexion/Déconnexion
   - ✅ Mode hors ligne
   - ✅ Synchronisation
   - ✅ Prise de présences
   - ✅ Inspections d'uniformes
   - ✅ Rapports

2. **Distribuez l'APK** aux utilisateurs

3. **Formez les utilisateurs** à l'application

4. **Collectez les retours** pour améliorations futures

---

## 📞 Support

**Documentation :**
- Guide Build APK : `/app/GUIDE_BUILD_APK.md`
- Guide Démarrage Rapide : `/app/DEMARRAGE_RAPIDE_APK.md`
- État Application : `/app/ÉTAT_APPLICATION_AVANT_BUILD.md`

**Liens Utiles :**
- Dashboard Expo : [expo.dev/accounts/seb958/projects/commandhub](https://expo.dev/accounts/seb958/projects/commandhub)
- Documentation EAS : [docs.expo.dev/build/introduction](https://docs.expo.dev/build/introduction/)
- Backend Production : [https://command-central-9.emergent.host](https://command-central-9.emergent.host)

---

**🎉 Vous êtes prêt à générer l'APK CommandHub !**

**Commencez par l'Étape 1 : Télécharger le projet**
