#!/usr/bin/env python3
"""
Lanceur de l'application GUI de compensation altimétrique.
Point d'entrée principal pour l'interface graphique.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire courant au path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Fonction principale de lancement."""
    
    print("🚀 Lancement de l'application de compensation altimétrique...")
    
    try:
        # Vérifier que CustomTkinter est installé
        import customtkinter as ctk
        print("✅ CustomTkinter détecté")
        
    except ImportError:
        print("❌ CustomTkinter non installé!")
        print("💡 Installez avec: pip install customtkinter")
        print("\nOu installez toutes les dépendances GUI:")
        print("pip install -r requirements_gui.txt")
        sys.exit(1)
    
    try:
        # Importer et lancer l'application
        from gui.main_window import MainApplication
        
        print("✅ Interface graphique initialisée")
        print("📊 Lancement de l'application...")
        
        # Créer et lancer l'application
        app = MainApplication()
        app.mainloop()
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que tous les modules sont présents")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()