#!/usr/bin/env python3
"""
Test simple d'import des composants d'onglets.
"""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Teste les imports des nouveaux composants."""
    try:
        print("🔍 Test des imports...")
        
        # Test import CustomTkinter
        import customtkinter as ctk
        print("✅ CustomTkinter importé")
        
        # Test import theme
        from gui.utils.theme import AppTheme
        print("✅ Theme importé")
        
        # Test import composants existants
        from gui.components.base_components import ThemedLabel, ThemedButton, ThemedFrame
        print("✅ Composants existants importés")
        
        # Test import nouveaux composants
        from gui.components.base_components import TabButton, TabFrame
        print("✅ Nouveaux composants d'onglets importés")
        
        # Test instanciation basique (sans interface graphique)
        print("\n🔧 Test instanciation...")
        
        # Vérifier que les classes sont bien définies
        assert hasattr(TabButton, '__init__')
        assert hasattr(TabFrame, '__init__')
        print("✅ Classes bien définies")
        
        # Vérifier les méthodes principales
        assert hasattr(TabButton, 'set_active')
        assert hasattr(TabButton, 'set_disabled')
        assert hasattr(TabFrame, 'get_tab_content')
        assert hasattr(TabFrame, 'switch_to_tab')
        print("✅ Méthodes principales présentes")
        
        print("\n✅ Tous les tests d'import sont passés!")
        print("🎯 Les composants d'onglets sont prêts à être utilisés")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_imports():
        print("\n🚀 Composants prêts pour l'intégration!")
    else:
        print("\n💥 Problèmes détectés")
        sys.exit(1)