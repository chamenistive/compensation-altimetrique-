"""
Script de démonstration pour le nouveau Dashboard moderne.
Lance une fenêtre de test pour visualiser le Dashboard.
"""

import customtkinter as ctk
import sys
import os

# Ajouter le répertoire courant au path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from gui.utils.theme import AppTheme
from gui.components.dashboard import ModernDashboard


class DashboardDemo(ctk.CTk):
    """Fenêtre de démonstration du Dashboard."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("🧮 Dashboard Moderne - Système de Compensation Altimétrique")
        self.geometry(f"{AppTheme.SIZES['window_default_width']}x{AppTheme.SIZES['window_default_height']}")
        self.minsize(AppTheme.SIZES['window_min_width'], AppTheme.SIZES['window_min_height'])
        
        # Appliquer le thème
        AppTheme.apply_theme()
        self.configure(fg_color=AppTheme.COLORS['background'])
        
        # Centrer la fenêtre
        self.center_window()
        
        # Créer le Dashboard
        self.create_dashboard()
    
    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - AppTheme.SIZES['window_default_width']) // 2
        y = (screen_height - AppTheme.SIZES['window_default_height']) // 2
        
        # S'assurer que la fenêtre reste sur l'écran
        x = max(0, x)
        y = max(0, y)
        
        self.geometry(f"{AppTheme.SIZES['window_default_width']}x{AppTheme.SIZES['window_default_height']}+{x}+{y}")
    
    def create_dashboard(self):
        """Crée et affiche le Dashboard."""
        
        # Dashboard principal
        self.dashboard = ModernDashboard(
            self,
            callback=self.handle_dashboard_action
        )
        self.dashboard.pack(fill='both', expand=True)
    
    def handle_dashboard_action(self, action, data=None):
        """Gère les actions du Dashboard."""
        print(f"Action Dashboard: {action}")
        if data:
            print(f"Données: {data}")
        
        # Ici on pourrait naviguer vers les différentes étapes
        action_messages = {
            'new_project': "🚀 Nouveau projet - Navigation vers étape Import",
            'quick_import': "⚡ Import rapide - Ouverture dialogue fichier", 
            'open_project': "🔄 Ouvrir projet - Navigation vers liste projets",
            'open_specific_project': f"📂 Ouverture projet: {data.get('name') if data else 'Inconnu'}",
            'view_all_projects': "📋 Affichage tous les projets"
        }
        
        message = action_messages.get(action, f"Action: {action}")
        
        # Affichage dans le titre pour la démo
        self.title(f"🧮 Dashboard - {message}")
        
        # Remettre le titre original après 3 secondes
        self.after(3000, lambda: self.title("🧮 Dashboard Moderne - Système de Compensation Altimétrique"))


def main():
    """Point d'entrée principal."""
    
    print("🚀 Lancement de la démonstration Dashboard...")
    print("📊 Interface moderne avec palette géodésique")
    print("🎯 Précision 2mm • Design professionnel")
    print("-" * 50)
    
    # Créer et lancer l'application
    app = DashboardDemo()
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("✅ Application fermée")


if __name__ == "__main__":
    main()