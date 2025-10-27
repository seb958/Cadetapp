# Guide de Génération APK CommandHub

## 📋 Prérequis

### Configuration Expo
- ✅ Compte Expo configuré (propriétaire: `seb958`)
- ✅ Projet Expo ID: `a7003ce2-d0f5-44c1-b1c8-47aac49695ba`
- ✅ Version app: `1.0.0`
- ✅ Package Android: `com.escadron879.commandhub`

### Fonctionnalités Validées
- ✅ Mode hors ligne avec synchronisation automatique
- ✅ Mises à jour OTA (Over-The-Air) activées
- ✅ Persistance de session (reste connecté jusqu'à déconnexion)
- ✅ Système de synchronisation avec queue offline
- ✅ Tous les endpoints backend fonctionnels

---

## 🚀 Génération de l'APK

### Étape 1: Installation d'EAS CLI

```bash
cd /app/frontend
npm install -g eas-cli
```

### Étape 2: Connexion à votre compte Expo

```bash
eas login
```

Entrez vos identifiants Expo (compte `seb958`).

### Étape 3: Configuration du Build

Le fichier `eas.json` est déjà configuré avec 3 profils :

#### **Profil Production (Recommandé)**
```bash
eas build --platform android --profile production
```

- Génère un **APK** pour distribution manuelle
- Configuration optimale pour production
- Variables d'environnement configurées

#### **Profil Preview (Pour tests)**
```bash
eas build --platform android --profile preview
```

- Génère un **APK** pour tests internes
- Plus rapide à compiler
- Idéal pour validation avant production

### Étape 4: Attendre la Compilation

Le build sera effectué sur les serveurs Expo (durée: 10-20 minutes).

Vous pouvez suivre la progression :
- Dans le terminal
- Sur [https://expo.dev](https://expo.dev) > Votre projet > Builds

### Étape 5: Télécharger l'APK

Une fois le build terminé, vous recevrez :
- Un lien de téléchargement direct
- L'APK sera disponible sur votre compte Expo
- Vous pourrez aussi générer un QR code pour téléchargement

---

## 📱 Distribution de l'APK

### Option 1: Distribution Manuelle

1. Téléchargez l'APK depuis Expo
2. Transférez le fichier vers les appareils Android
3. Activez "Sources inconnues" sur Android
4. Installez l'APK

### Option 2: Lien de Téléchargement

Expo génère automatiquement un lien de téléchargement que vous pouvez partager :
```
https://expo.dev/accounts/seb958/projects/commandhub/builds/[BUILD_ID]
```

### Option 3: Distribution via APKDownloadBanner

L'application inclut déjà un composant `APKDownloadBanner` qui affiche un lien de téléchargement dans l'interface pour les utilisateurs Android.

---

## 🔄 Mises à Jour de l'Application

### Mises à Jour OTA (Sans rebuild)

Pour des modifications JavaScript/React Native (90% des changements) :

```bash
cd /app/frontend
eas update --branch production --message "Description des modifications"
```

**Avantages :**
- Les utilisateurs reçoivent automatiquement les mises à jour
- Pas besoin de redistribuer l'APK
- Mise à jour au prochain lancement de l'app

**Configuration actuelle :**
```json
"updates": {
  "enabled": true,
  "checkAutomatically": "ON_LOAD",
  "url": "https://u.expo.dev/a7003ce2-d0f5-44c1-b1c8-47aac49695ba"
}
```

### Rebuild Complet (Nécessaire si...)

Un nouveau build est requis uniquement pour :
- Changement de version native (dépendances natives)
- Modification des permissions Android
- Changement d'icône ou splash screen
- Mise à jour majeure d'Expo SDK

---

## 🔐 Configuration des Variables d'Environnement

### Pour Production

Le backend URL est déjà configuré dans `eas.json` :

```json
"production": {
  "android": {
    "buildType": "apk",
    "env": {
      "EXPO_PUBLIC_BACKEND_URL": "$EXPO_PUBLIC_BACKEND_URL"
    }
  }
}
```

**Important :** Définissez la variable sur Expo avant le build :

```bash
eas secret:create --scope project --name EXPO_PUBLIC_BACKEND_URL --value "https://votre-backend-production.com"
```

Ou configurez-la directement sur [expo.dev](https://expo.dev) dans les paramètres du projet.

---

## 📊 Gestion des Versions

### Incrémenter la Version

Avant chaque nouveau build production, mettez à jour :

**Dans `app.json` :**
```json
{
  "expo": {
    "version": "1.0.1",  // ← Incrémenter ici
    "android": {
      "versionCode": 2    // ← ET ici (nombre entier)
    }
  }
}
```

**Dans `package.json` :**
```json
{
  "version": "1.0.1"  // ← Garder synchronisé
}
```

### Stratégie de Versioning

- **1.0.0 → 1.0.1** : Corrections de bugs
- **1.0.0 → 1.1.0** : Nouvelles fonctionnalités mineures
- **1.0.0 → 2.0.0** : Changements majeurs

---

## 🧪 Test de l'APK

### Avant Distribution

1. **Téléchargez l'APK** sur un appareil Android de test
2. **Installez et testez** les fonctionnalités critiques :
   - ✅ Connexion / Déconnexion
   - ✅ Mode hors ligne
   - ✅ Synchronisation automatique
   - ✅ Prise de présences
   - ✅ Inspections d'uniformes
   - ✅ Navigation entre les écrans
   - ✅ Persistance de session

3. **Vérifiez les mises à jour OTA** :
   - Publiez une petite mise à jour de test
   - Redémarrez l'app
   - Vérifiez que la mise à jour est appliquée

---

## 🛠️ Dépannage

### Erreur de Build

**Problème :** Build échoue avec erreur de dépendances

**Solution :**
```bash
cd /app/frontend
rm -rf node_modules package-lock.json
npm install
eas build --platform android --profile production --clear-cache
```

### Variables d'Environnement Non Trouvées

**Problème :** `EXPO_PUBLIC_BACKEND_URL` undefined dans l'app

**Solution :**
1. Vérifiez que la variable est définie dans Expo secrets
2. Utilisez `eas secret:list` pour voir les secrets existants
3. Recréez le secret si nécessaire

### APK Trop Volumineux

**Problème :** APK > 100 MB

**Solution :** Utiliser AAB au lieu d'APK (si publication sur Play Store)
```bash
eas build --platform android --profile production
# Modifiez eas.json : "buildType": "app-bundle"
```

---

## 📞 Support

### Documentation Expo
- [Guide EAS Build](https://docs.expo.dev/build/introduction/)
- [Guide EAS Update](https://docs.expo.dev/eas-update/introduction/)
- [Troubleshooting](https://docs.expo.dev/build-reference/troubleshooting/)

### Liens Utiles
- Dashboard Expo : [https://expo.dev/accounts/seb958/projects/commandhub](https://expo.dev/accounts/seb958/projects/commandhub)
- Builds : [https://expo.dev/accounts/seb958/projects/commandhub/builds](https://expo.dev/accounts/seb958/projects/commandhub/builds)

---

## ✅ Checklist Avant Production

- [ ] Tests backend complets
- [ ] Tests frontend sur plusieurs appareils
- [ ] Version incrémentée dans app.json et package.json
- [ ] EXPO_PUBLIC_BACKEND_URL configuré pour production
- [ ] Build APK généré et téléchargé
- [ ] APK testé sur appareil Android physique
- [ ] Mode hors ligne validé
- [ ] Synchronisation testée
- [ ] Mises à jour OTA testées
- [ ] Documentation utilisateur préparée

---

**Date de création :** $(date)
**Version application :** 1.0.0
**Plateforme :** Android (iOS via Expo Go)
