# 🚀 Démarrage Rapide - Génération APK CommandHub

## Version 1.0.0 - Build Android

---

## ⚡ Génération Rapide (5 étapes)

### 1️⃣ Installation EAS CLI

```bash
npm install -g eas-cli
```

### 2️⃣ Connexion Expo

```bash
eas login
```

Identifiants : Compte **seb958**

### 3️⃣ Configuration URL Backend

**Option A - Via Command Line :**
```bash
eas secret:create --scope project \
  --name EXPO_PUBLIC_BACKEND_URL \
  --value "https://react-native-fix-3.preview.emergentagent.com"
```

**Option B - Via Dashboard :**
1. Allez sur [expo.dev](https://expo.dev/accounts/seb958/projects/commandhub/secrets)
2. Ajoutez le secret `EXPO_PUBLIC_BACKEND_URL`
3. Valeur : URL de votre backend production

### 4️⃣ Lancer le Build

**Build Production :**
```bash
cd /app/frontend
eas build --platform android --profile production
```

**Build Preview (Tests) :**
```bash
eas build --platform android --profile preview
```

### 5️⃣ Télécharger l'APK

Une fois le build terminé (~15 minutes) :

**Via Terminal :**
```bash
eas build:download --platform android --latest
```

**Via Dashboard :**
- [https://expo.dev/accounts/seb958/projects/commandhub/builds](https://expo.dev/accounts/seb958/projects/commandhub/builds)
- Cliquez sur le dernier build
- Téléchargez l'APK

---

## 📊 Informations Projet

| Propriété | Valeur |
|-----------|--------|
| **Nom** | CommandHub |
| **Version** | 1.0.0 |
| **Package Android** | com.escadron879.commandhub |
| **Propriétaire Expo** | seb958 |
| **Project ID** | a7003ce2-d0f5-44c1-b1c8-47aac49695ba |

---

## 🔄 Mises à Jour OTA (Sans Rebuild)

Pour publier une mise à jour sans rebuild complet :

```bash
cd /app/frontend
eas update --branch production --message "Description de la mise à jour"
```

Les utilisateurs recevront automatiquement la mise à jour au prochain lancement.

---

## 📱 Distribution

### Pour Android
1. Téléchargez l'APK
2. Partagez le fichier ou un lien de téléchargement
3. Les utilisateurs installent directement l'APK

### Pour iOS (Expo Go)
1. Lancez le serveur de dev :
   ```bash
   cd /app/frontend
   npx expo start --tunnel
   ```
2. Partagez le QR code
3. Les utilisateurs scannent avec Expo Go

---

## ✅ Vérifications Pré-Build

- [x] Backend accessible : `https://react-native-fix-3.preview.emergentagent.com/api`
- [x] Services démarrés : `sudo supervisorctl status`
- [x] Version 1.0.0 configurée
- [x] EAS configuration complète
- [ ] URL backend production configurée dans secrets Expo
- [ ] Compte Expo (seb958) accessible

---

## 🆘 Aide Rapide

### Build échoue ?
```bash
cd /app/frontend
rm -rf node_modules package-lock.json
npm install
eas build --platform android --profile production --clear-cache
```

### Voir les secrets configurés
```bash
eas secret:list
```

### Voir l'historique des builds
```bash
eas build:list
```

### Annuler un build en cours
```bash
eas build:cancel
```

---

## 📞 Ressources

- **Documentation complète :** `/app/GUIDE_BUILD_APK.md`
- **État de l'app :** `/app/ÉTAT_APPLICATION_AVANT_BUILD.md`
- **Dashboard Expo :** [expo.dev/accounts/seb958/projects/commandhub](https://expo.dev/accounts/seb958/projects/commandhub)
- **Documentation EAS :** [docs.expo.dev/build/introduction](https://docs.expo.dev/build/introduction/)

---

**🎉 Prêt à builder !**

Commande recommandée :
```bash
cd /app/frontend && eas build --platform android --profile production
```

⏱️ Temps estimé : 15-20 minutes
