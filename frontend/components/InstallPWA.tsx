import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Platform, ScrollView, Image } from 'react-native';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export const InstallPWA = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Vérifier si déjà installé
    const checkInstalled = () => {
      if (Platform.OS === 'web') {
        const isStandalone = (window as any).matchMedia('(display-mode: standalone)').matches;
        const isIOSStandalone = (window.navigator as any).standalone === true;
        setIsInstalled(isStandalone || isIOSStandalone);
        
        // Si pas installé, montrer le bouton
        if (!isStandalone && !isIOSStandalone) {
          setShowInstallButton(true);
        }
      }
    };

    checkInstalled();

    // Écouter l'événement beforeinstallprompt (Chrome/Edge/Android)
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setShowInstallButton(true);
    };

    if (Platform.OS === 'web') {
      window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    }

    return () => {
      if (Platform.OS === 'web') {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      }
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Android/Chrome - Utiliser le prompt natif
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        console.log('✅ PWA installée');
        setShowInstallButton(false);
      }
      setDeferredPrompt(null);
    } else {
      // iOS Safari ou autres - Montrer les instructions
      setShowInstructions(true);
    }
  };

  const isIOS = () => {
    if (Platform.OS !== 'web') return false;
    const userAgent = window.navigator.userAgent.toLowerCase();
    return /iphone|ipad|ipod/.test(userAgent);
  };

  if (isInstalled || !showInstallButton) {
    return null;
  }

  return (
    <>
      {/* Bouton d'installation flottant */}
      <TouchableOpacity
        style={styles.installButton}
        onPress={handleInstallClick}
        activeOpacity={0.8}
      >
        <View style={styles.installButtonContent}>
          <Text style={styles.installIcon}>📱</Text>
          <Text style={styles.installButtonText}>Installer l'app</Text>
        </View>
      </TouchableOpacity>

      {/* Modal avec instructions */}
      <Modal
        visible={showInstructions}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowInstructions(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView style={styles.modalScroll}>
              <Text style={styles.modalTitle}>
                📱 Installer CommandHub
              </Text>
              
              <Text style={styles.modalSubtitle}>
                Pour utiliser l'application hors ligne
              </Text>

              {isIOS() ? (
                // Instructions iOS
                <>
                  <View style={styles.instructionSection}>
                    <Text style={styles.instructionTitle}>Sur iPhone/iPad (Safari):</Text>
                    
                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>1</Text>
                      <Text style={styles.stepText}>
                        Appuyez sur le bouton <Text style={styles.bold}>Partager</Text> (icône ↑) en bas de l'écran
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>2</Text>
                      <Text style={styles.stepText}>
                        Faites défiler et appuyez sur <Text style={styles.bold}>"Sur l'écran d'accueil"</Text>
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>3</Text>
                      <Text style={styles.stepText}>
                        Appuyez sur <Text style={styles.bold}>"Ajouter"</Text>
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>✓</Text>
                      <Text style={styles.stepText}>
                        L'icône CommandHub apparaîtra sur votre écran d'accueil!
                      </Text>
                    </View>
                  </View>
                </>
              ) : (
                // Instructions Android
                <>
                  <View style={styles.instructionSection}>
                    <Text style={styles.instructionTitle}>Sur Android (Chrome):</Text>
                    
                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>1</Text>
                      <Text style={styles.stepText}>
                        Appuyez sur le menu <Text style={styles.bold}>(⋮)</Text> en haut à droite
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>2</Text>
                      <Text style={styles.stepText}>
                        Sélectionnez <Text style={styles.bold}>"Installer l'application"</Text> ou <Text style={styles.bold}>"Ajouter à l'écran d'accueil"</Text>
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>3</Text>
                      <Text style={styles.stepText}>
                        Appuyez sur <Text style={styles.bold}>"Installer"</Text>
                      </Text>
                    </View>

                    <View style={styles.step}>
                      <Text style={styles.stepNumber}>✓</Text>
                      <Text style={styles.stepText}>
                        L'icône CommandHub apparaîtra sur votre écran d'accueil!
                      </Text>
                    </View>
                  </View>
                </>
              )}

              <View style={styles.benefitsSection}>
                <Text style={styles.benefitsTitle}>✨ Avantages:</Text>
                <Text style={styles.benefit}>✅ Fonctionne hors ligne (murs en béton)</Text>
                <Text style={styles.benefit}>✅ Chargement ultra-rapide</Text>
                <Text style={styles.benefit}>✅ Comme une vraie application</Text>
                <Text style={styles.benefit}>✅ Icône sur l'écran d'accueil</Text>
              </View>
            </ScrollView>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowInstructions(false)}
            >
              <Text style={styles.closeButtonText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  installButton: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: '#3b82f6',
    borderRadius: 30,
    paddingVertical: 12,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    zIndex: 1000,
  },
  installButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  installIcon: {
    fontSize: 24,
    marginRight: 8,
  },
  installButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingTop: 24,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  modalScroll: {
    flex: 1,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
    textAlign: 'center',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  instructionSection: {
    marginBottom: 24,
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 16,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingLeft: 8,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#3b82f6',
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
    lineHeight: 32,
    marginRight: 12,
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    color: '#4b5563',
    lineHeight: 22,
    paddingTop: 5,
  },
  bold: {
    fontWeight: '700',
    color: '#1f2937',
  },
  benefitsSection: {
    backgroundColor: '#f0f9ff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  benefitsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  benefit: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 6,
  },
  closeButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
