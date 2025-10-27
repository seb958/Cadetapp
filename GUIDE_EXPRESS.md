# 🎯 Guide Express - Génération APK CommandHub

**Version 1.0.0** | **Windows** | **5 Étapes Simples**

---

## ⚡ Démarrage Ultra-Rapide

### ✅ ÉTAPE 1 : Télécharger le Projet (5 min)

**Lien de téléchargement :**
```
https://command-central-9.emergent.host/commandhub-project.zip
```

**Extraire** dans : `C:\Users\Admin\Documents\CommandHub\`

---

### ✅ ÉTAPE 2 : Installer les Outils (10 min)

**Ouvrez CMD** (Windows + R → tapez `cmd`)

```cmd
REM Se placer dans le dossier frontend
cd C:\Users\Admin\Documents\CommandHub\frontend

REM Installer les dépendances du projet
npm install

REM Installer EAS CLI
npm install -g eas-cli
```

---

### ✅ ÉTAPE 3 : Configuration Expo (2 min)

```cmd
REM Se connecter à Expo
eas login
```

**Identifiants :**
- Username : `seb958`
- Password : [votre mot de passe]

```cmd
REM Configurer l'URL backend de PRODUCTION
eas secret:create --scope project --name EXPO_PUBLIC_BACKEND_URL --value "https://command-central-9.emergent.host"
```

---

### ✅ ÉTAPE 4 : Lancer le Build (15-20 min)

```cmd
REM Générer l'APK
eas build --platform android --profile production
```

**Questions pendant le build :**
- "Generate new keystore?" → Tapez **Y** et Entrée
- Autres questions → Appuyez sur **Entrée**

**Suivez le build :**
- Dans CMD (automatique)
- Ou dans votre navigateur : https://expo.dev/accounts/seb958/projects/commandhub/builds

---

### ✅ ÉTAPE 5 : Télécharger l'APK (1 min)

**Une fois le build terminé** (vous verrez "✅ Build finished") :

```cmd
REM Télécharger l'APK
eas build:download --platform android --latest
```

**OU** via le navigateur :
1. Allez sur https://expo.dev/accounts/seb958/projects/commandhub/builds
2. Cliquez sur votre dernier build
3. Cliquez sur "Download"

---

## 📱 Installation sur Android

1. **Transférez l'APK** sur votre appareil Android
2. **Ouvrez le fichier** et appuyez sur "Installer"
3. **Lancez CommandHub** !

**Premier login :**
- Username : `aadministrateur`
- Password : `admin123`

---

## 📚 Documentation Complète

**Guides détaillés disponibles :**
- `GUIDE_INSTALLATION_WINDOWS.md` - Instructions complètes
- `GUIDE_BUILD_APK.md` - Détails techniques
- `TELECHARGEMENT_PROJET.md` - Infos sur le téléchargement

---

## 🆘 Aide Rapide

**Problème PowerShell ?**
→ Utilisez CMD au lieu de PowerShell

**npm install échoue ?**
```cmd
rmdir /s node_modules
npm install
```

**Build échoue ?**
```cmd
eas build --platform android --profile production --clear-cache
```

**Oublié le mot de passe Expo ?**
→ Réinitialisez sur https://expo.dev

---

## ⏱️ Temps Total Estimé

- ✅ Téléchargement : 5 minutes
- ✅ Installation dépendances : 10 minutes
- ✅ Configuration : 2 minutes
- ✅ Build APK : 15-20 minutes
- ✅ Téléchargement APK : 1 minute

**TOTAL : ~35 minutes** ⏱️

---

## 📊 Informations Clés

| Paramètre | Valeur |
|-----------|--------|
| **Version** | 1.0.0 |
| **Backend** | https://command-central-9.emergent.host |
| **Package ID** | com.escadron879.commandhub |
| **Compte Expo** | seb958 |

---

## ✅ Checklist

- [ ] Projet téléchargé et extrait
- [ ] Node.js installé
- [ ] `npm install` terminé
- [ ] EAS CLI installé
- [ ] Connecté à Expo (`eas login`)
- [ ] Secret backend créé
- [ ] Build lancé
- [ ] APK téléchargé
- [ ] APK testé sur Android

---

**🎉 Vous êtes prêt ! Commencez par l'Étape 1.**

**Support :** Si vous rencontrez un problème, consultez les guides détaillés listés ci-dessus.
