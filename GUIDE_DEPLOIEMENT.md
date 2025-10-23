# Guide de Déploiement CommandHub 🚀

## Phase 1 : Modifications Offline-First ✅

Les modifications suivantes ont été effectuées pour permettre à l'application de fonctionner en mode offline-first :

### 1. **Gestion des erreurs réseau au démarrage**
   - ✅ Ajout de timeouts sur toutes les requêtes réseau (5-10 secondes)
   - ✅ Mode offline automatique si le backend n'est pas accessible
   - ✅ L'app ne crash plus au démarrage, même sans connexion backend
   - ✅ Conservation de la session locale en cas d'erreur réseau

### 2. **Indicateur de connexion visible**
   - ✅ Ajout du composant `ConnectionIndicator` sur l'écran principal
   - ✅ Affichage du statut : En ligne / Hors ligne / Synchronisation
   - ✅ Badge indiquant le nombre d'éléments en attente de synchronisation
   - ✅ Bouton de synchronisation manuelle

### 3. **Synchronisation automatique**
   - ✅ Détection automatique de connexion réseau
   - ✅ Synchronisation automatique quand la connexion est rétablie
   - ✅ File d'attente persistante pour les données hors ligne
   - ✅ Feedback utilisateur sur le statut de synchronisation

### 4. **Configuration de production**
   - ✅ Création du fichier `.env.production`
   - ✅ Configuration d'EAS Build pour utiliser les variables d'environnement de production
   - ✅ Préparation pour URL backend Emergent

---

## Phase 2 : Déploiement Backend sur Emergent 🌐

### **Étape 1 : Tester en mode Preview**
1. Dans l'interface Emergent, cliquez sur **"Preview"**
2. Testez votre backend FastAPI + MongoDB
3. Vérifiez que tous les endpoints fonctionnent correctement

### **Étape 2 : Déployer sur Emergent**
1. Cliquez sur le bouton **"Deploy"** dans l'interface Emergent
2. Cliquez sur **"Deploy Now"**
3. Attendez environ **10 minutes** pour la finalisation
4. **Notez l'URL publique fournie** (ex: `https://votre-app.emergent.com`)

### **Étape 3 : Mettre à jour la configuration de production**
1. Ouvrez le fichier `/app/frontend/.env.production`
2. Remplacez `https://votre-app-emergent.com` par l'URL réelle fournie par Emergent
3. Exemple :
   ```
   EXPO_PUBLIC_BACKEND_URL=https://commandhub-879.emergent.com
   ```

---

## Phase 3 : Rebuild de l'APK Android 📱

### **Étape 1 : Préparer le build**
```bash
cd /app/frontend
```

### **Étape 2 : Lancer le build de production**
```bash
eas build --platform android --profile production
```

### **Étape 3 : Attendre la compilation**
- Le build prend environ **10-15 minutes**
- Vous recevrez un lien pour télécharger l'APK une fois terminé

### **Étape 4 : Télécharger et installer l'APK**
1. Téléchargez l'APK depuis le lien fourni par EAS
2. Transférez-le sur votre appareil Android
3. Installez l'application
4. **Testez la synchronisation** :
   - Utilisez l'app sans connexion (hors ligne)
   - Approchez-vous d'une fenêtre pour capter le signal
   - L'app devrait automatiquement synchroniser les données

---

## Phase 4 : Over-The-Air (OTA) Updates 🔄

Pour les mises à jour futures **sans recompiler l'APK** :

### **Publier une mise à jour OTA**
```bash
cd /app/frontend
eas update --branch production --message "Description de la mise à jour"
```

### **Comment ça fonctionne ?**
- Les utilisateurs recevront la mise à jour au prochain lancement de l'app
- Pas besoin de réinstaller l'APK
- Fonctionne uniquement pour les changements de code JavaScript/TypeScript
- Les modifications natives (dépendances, configurations) nécessitent un rebuild

---

## Scénario d'Utilisation 🏢

### **Dans le bâtiment (sans signal)**
1. ✅ Ouvrir l'application (mode offline)
2. ✅ Effectuer les inspections d'uniformes
3. ✅ Enregistrer les présences
4. ✅ Les données sont stockées localement

### **Près d'une fenêtre (avec signal)**
1. 🟢 L'indicateur passe à "En ligne"
2. 🔄 Synchronisation automatique des données
3. ✅ Confirmation visuelle de la synchronisation réussie

### **Synchronisation manuelle**
1. Appuyer sur le bouton **"Synchroniser"** dans l'indicateur de connexion
2. Attendre la confirmation
3. Vérifier que le compteur de données en attente = 0

---

## Résolution de Problèmes 🔧

### **L'app crash toujours au démarrage**
- ✅ Vérifiez que vous avez bien rebuild l'APK après les modifications
- ✅ Assurez-vous que le fichier `.env.production` contient l'URL correcte
- ✅ Vérifiez que le backend Emergent est accessible depuis internet

### **Les données ne se synchronisent pas**
- 🔍 Vérifiez l'indicateur de connexion (doit être "En ligne")
- 🔍 Essayez une synchronisation manuelle
- 🔍 Vérifiez que l'URL backend dans `.env.production` est correcte
- 🔍 Consultez les logs de l'application

### **Timeout de connexion**
- ⏱️ Les requêtes ont un timeout de 5-10 secondes
- 🌐 Assurez-vous d'avoir un minimum de signal internet
- 📡 Approchez-vous d'une fenêtre si dans le bâtiment

---

## Coûts Emergent 💰

- **50 crédits par mois** par application déployée
- **Maximum 100 déploiements** par utilisateur
- Possibilité d'arrêter l'application pour économiser des crédits
- Redéploiement gratuit pour les mises à jour

---

## Prochaines Étapes 🎯

Une fois l'APK fonctionnel avec le backend Emergent :

1. **Tester en conditions réelles** dans le bâtiment
2. **Ajuster les timeouts** si nécessaire (selon la qualité du signal)
3. **Implémenter les fonctionnalités restantes** :
   - Rapports
   - Communication
   - Import/Export Excel
   - Amélioration de l'organigramme

---

## Contact et Support 📞

Pour toute question ou problème :
- Consultez la documentation Emergent
- Utilisez l'agent de support Emergent
- Testez toujours en mode Preview avant de déployer en production

---

**Bonne chance avec votre déploiement ! 🚀**
