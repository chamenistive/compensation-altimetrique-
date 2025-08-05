#!/usr/bin/env python3
"""
Test ultra-simple pour identifier le problème X11.
Version progressive pour isoler le composant problématique.
"""

import customtkinter as ctk
import sys

def test_progressif():
    """Test progressif des composants GUI."""
    
    print("🔧 Test progressif des composants...")
    
    try:
        # Configuration de base
        ctk.set_appearance_mode("light")
        print("✅ Apparence configurée")
        
        # Fenêtre minimale
        root = ctk.CTk()
        root.title("Test Ultra-Simple")
        root.geometry("400x300")
        print("✅ Fenêtre créée")
        
        # Test 1: Label simple
        label1 = ctk.CTkLabel(root, text="Test 1: Label simple")
        label1.pack(pady=10)
        print("✅ Label simple OK")
        
        # Test 2: Bouton simple
        def test_click():
            print("Bouton cliqué!")
        
        button1 = ctk.CTkButton(root, text="Test 2: Bouton", command=test_click)
        button1.pack(pady=10)
        print("✅ Bouton simple OK")
        
        # Test 3: Entry simple
        entry1 = ctk.CTkEntry(root, placeholder_text="Test 3: Saisie")
        entry1.pack(pady=10)
        print("✅ Entry simple OK")
        
        # Test 4: Frame simple
        frame1 = ctk.CTkFrame(root)
        frame1.pack(pady=10, padx=20, fill="x")
        
        label_frame = ctk.CTkLabel(frame1, text="Test 4: Frame avec contenu")
        label_frame.pack(pady=10)
        print("✅ Frame avec contenu OK")
        
        # Test 5: Couleurs personnalisées (ici que ça pourrait planter)
        try:
            label_color = ctk.CTkLabel(
                root, 
                text="Test 5: Couleurs", 
                text_color="#7671FA"
            )
            label_color.pack(pady=10)
            print("✅ Couleurs personnalisées OK")
        except Exception as e:
            print(f"❌ Erreur couleurs: {e}")
        
        # Affichage bref
        print("🎯 Tentative d'affichage de la fenêtre...")
        root.after(3000, root.quit)  # Fermer après 3 secondes
        root.mainloop()
        
        print("✅ Test progressif réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans test progressif: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_progressif()
    
    if success:
        print("\n🎯 L'interface de base fonctionne!")
        print("Le problème vient probablement de:")
        print("- Polices spécifiques (Segoe UI)")
        print("- Composants complexes (ProgressBar, etc.)")
        print("- Nombre trop élevé de widgets")
    else:
        print("\n❌ Problème fondamental détecté")