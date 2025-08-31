#!/usr/bin/env python3
"""
Script de test pour les nouveaux composants d'onglets.
Teste TabButton et TabFrame avant intégration dans l'application principale.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    import customtkinter as ctk
    from gui.utils.theme import AppTheme
    from gui.components.base_components import TabFrame, ThemedLabel, ThemedButton
    
    class TabsTestApp(ctk.CTk):
        """Application de test pour les composants d'onglets."""
        
        def __init__(self):
            super().__init__()
            
            self.title("🧮 Test - Système d'Onglets")
            self.geometry("800x600")
            
            # Appliquer le thème
            AppTheme.apply_theme()
            self.configure(fg_color=AppTheme.COLORS['background'])
            
            self.create_test_interface()
        
        def create_test_interface(self):
            """Crée l'interface de test."""
            
            # Titre principal
            title = ThemedLabel(self, "Test du Système d'Onglets", style='title')
            title.pack(pady=20)
            
            # Créer le système d'onglets
            tab_names = [
                "1. Import Données",
                "2. Paramètres", 
                "3. Calculs",
                "4. Résultats",
                "5. Export"
            ]
            
            self.tab_frame = TabFrame(self, tabs=tab_names)
            self.tab_frame.pack(expand=True, fill='both', padx=20, pady=10)
            
            # Ajouter du contenu aux onglets
            self.populate_tabs()
            
            # Désactiver les onglets 3, 4, 5 au début
            self.tab_frame.set_tab_disabled(2, True)  # Calculs
            self.tab_frame.set_tab_disabled(3, True)  # Résultats
            self.tab_frame.set_tab_disabled(4, True)  # Export
        
        def populate_tabs(self):
            """Remplit les onglets avec du contenu de test."""
            
            # Onglet 1: Import
            tab1 = self.tab_frame.get_tab_content(0)
            ThemedLabel(tab1, "📁 Section Import des Données", style='heading').pack(pady=10)
            ThemedLabel(tab1, "Contenu de test pour l'import des données Excel.", style='body').pack(pady=5)
            
            btn_activate = ThemedButton(
                tab1, 
                "Activer onglet Paramètres",
                command=lambda: self.tab_frame.set_tab_disabled(1, False)
            )
            btn_activate.pack(pady=10)
            
            # Onglet 2: Paramètres
            tab2 = self.tab_frame.get_tab_content(1)
            ThemedLabel(tab2, "⚙️ Configuration des Paramètres", style='heading').pack(pady=10)
            ThemedLabel(tab2, "Contenu de test pour la configuration.", style='body').pack(pady=5)
            
            btn_activate2 = ThemedButton(
                tab2,
                "Activer onglet Calculs", 
                command=lambda: self.tab_frame.set_tab_disabled(2, False)
            )
            btn_activate2.pack(pady=10)
            
            # Onglet 3: Calculs
            tab3 = self.tab_frame.get_tab_content(2)
            ThemedLabel(tab3, "🧮 Calculs de Compensation", style='heading').pack(pady=10)
            ThemedLabel(tab3, "Contenu de test pour les calculs.", style='body').pack(pady=5)
            
            # Onglet 4: Résultats
            tab4 = self.tab_frame.get_tab_content(3)
            ThemedLabel(tab4, "📊 Résultats Détaillés", style='heading').pack(pady=10)
            ThemedLabel(tab4, "Contenu de test pour les résultats.", style='body').pack(pady=5)
            
            # Onglet 5: Export
            tab5 = self.tab_frame.get_tab_content(4)
            ThemedLabel(tab5, "📤 Export des Résultats", style='heading').pack(pady=10)
            ThemedLabel(tab5, "Contenu de test pour l'export.", style='body').pack(pady=5)
    
    def main():
        """Lance l'application de test."""
        print("🚀 Lancement du test des composants d'onglets...")
        
        app = TabsTestApp()
        print("✅ Interface de test créée")
        print("📝 Testez les fonctionnalités suivantes:")
        print("   - Navigation entre onglets")
        print("   - Activation/désactivation d'onglets")
        print("   - Styles visuels (actif/inactif/désactivé)")
        
        app.mainloop()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Vérifiez que CustomTkinter est installé et que les composants sont présents")
    sys.exit(1)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)