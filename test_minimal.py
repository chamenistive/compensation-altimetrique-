#!/usr/bin/env python3
"""
Test minimal pour diagnostiquer le problème X11.
"""

import customtkinter as ctk

def test_minimal():
    """Test minimal de CustomTkinter."""
    try:
        print("🔧 Test minimal CustomTkinter...")
        
        # Configuration basique
        ctk.set_appearance_mode("light")
        
        # Fenêtre minimale
        root = ctk.CTk()
        root.title("Test Minimal")
        root.geometry("300x200")
        
        # Label simple
        label = ctk.CTkLabel(root, text="Test réussi !")
        label.pack(pady=50)
        
        print("✅ Fenêtre créée, tentative d'affichage...")
        
        # Afficher brièvement puis fermer
        root.after(2000, root.quit)  # Fermer après 2 secondes
        root.mainloop()
        
        print("✅ Test minimal réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Test minimal échoué: {e}")
        return False

if __name__ == "__main__":
    success = test_minimal()
    if success:
        print("\n🎯 L'interface graphique fonctionne !")
        print("Le problème vient probablement de la complexité de l'interface.")
    else:
        print("\n❌ Problème fondamental avec l'affichage graphique.")
        print("💡 Solutions possibles:")
        print("  - Vérifier la configuration X11")
        print("  - Utiliser un environnement graphique différent")
        print("  - Tester sur un autre système")