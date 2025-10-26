# 🔄 Guide des Mises à Jour CommandHub

## 📋 Comment publier une mise à jour OTA

### Prérequis
- Être dans le dossier du projet
- Être connecté à Expo (`eas login`)

### Commande pour publier une mise à jour

```bash
cd C:\Users\Admin\Desktop\Projet\frontend
eas update --branch production --message "Description de la mise à jour"
```

### Exemples

**Correction de bug:**
```bash
eas update --branch production --message "Fix: Correction bug synchronisation"
```

**Nouvelle fonctionnalité:**
```bash
eas update --branch production --message "Feature: Ajout filtre par date"
```

**Changement UI:**
```bash
eas update --branch production --message "UI: Changement couleur boutons"
```

---

## ⏱️ Temps de déploiement

- **Publication:** 30 secondes à 1 minute
- **Réception par les utilisateurs:** Immédiat au prochain lancement de l'app

---

## 📱 Côté utilisateur

### Que voient les inspecteurs?

1. **Première ouverture après la mise à jour:**
   - Message: "Mise à jour disponible..."
   - Téléchargement automatique (quelques secondes)
   
2. **Deuxième ouverture:**
   - Application mise à jour automatiquement
   - Nouvelles fonctionnalités disponibles

**Les utilisateurs ne font RIEN! Tout est automatique!**

---

## 🔄 Workflow complet

### Développement d'une nouvelle fonctionnalité

```
1. Agent développe dans Emergent
   ↓
2. Vous testez sur: https://commandhub-cadet.preview.emergentagent.com
   ↓
3. Quand validé, vous publiez:
   cd C:\Users\Admin\Desktop\Projet\frontend
   eas update --branch production --message "Votre message"
   ↓
4. Inspecteurs reçoivent la mise à jour automatiquement
```

---

## ⚠️ Quand faire un nouveau build APK?

**Nécessaire seulement pour:**
- Changement d'icône/logo de l'app
- Nouvelles permissions Android (caméra, localisation, etc.)
- Changement de nom de l'app
- Upgrade SDK Expo majeur

**Commande:**
```bash
eas build --platform android --profile production
```

---

## 📊 Suivi des mises à jour

### Voir l'historique des updates

```bash
eas update:list --branch production
```

### Voir les détails d'une update

Allez sur: https://expo.dev/accounts/seb958/projects/commandhub/updates

---

## 🐛 Rollback en cas de problème

Si une mise à jour cause un problème, vous pouvez revenir en arrière:

```bash
eas update:rollback --branch production
```

---

## 💡 Conseils

1. **Testez toujours sur le web avant de publier**
2. **Écrivez des messages de commit clairs**
3. **Publiez en dehors des heures d'inspection** (éviter les mises à jour pendant les soirées de mardi)
4. **Groupez les petites modifications** (publiez 1x par semaine plutôt que 5x par jour)

---

## 📞 Questions?

Revenez dans la session Emergent et demandez de l'aide!
