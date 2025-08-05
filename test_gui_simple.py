#!/usr/bin/env python3
"""
Test simple de l'interface graphique.
Version minimale pour tester CustomTkinter et la palette de couleurs.
"""

import customtkinter as ctk
import sys
import os

# Configuration du thème
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Palette de couleurs
COLORS = {
    'primary': '#7671FA',
    'secondary': '#07244C', 
    'background': '#E5EAF3',
    'surface': '#FFFFFF',
    'text': '#07244C',
    'text_secondary': '#7E7F9C'
}

class SimpleTestApp(ctk.CTk):
    """Application de test simple."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration basique
        self.title("Test Interface - Compensation Altimétrique")
        self.geometry("600x400")
        self.configure(fg_color=COLORS['background'])
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crée l'interface de test."""
        
        # Titre
        title = ctk.CTkLabel(
            self,
            text="🎯 Test Interface Graphique",
            font=('Segoe UI', 24, 'bold'),
            text_color=COLORS['primary']
        )
        title.pack(pady=30)
        
        # Frame principale
        main_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS['surface'],
            corner_radius=12
        )
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Test des couleurs de votre palette
        color_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        color_frame.pack(pady=20)
        
        ctk.CTkLabel(
            color_frame, 
            text="Palette de couleurs testée :",
            font=('Segoe UI', 14, 'bold'),
            text_color=COLORS['text']
        ).pack(pady=10)
        
        # Boutons avec différentes couleurs
        button_frame = ctk.CTkFrame(color_frame, fg_color='transparent')
        button_frame.pack(pady=10)
        
        # Bouton principal (bleu)
        btn_primary = ctk.CTkButton(
            button_frame,
            text="Couleur Principale",
            fg_color=COLORS['primary'],
            hover_color='#5A54E6',
            font=('Segoe UI', 12, 'bold')
        )
        btn_primary.pack(side='left', padx=10)
        
        # Bouton secondaire (bleu foncé) 
        btn_secondary = ctk.CTkButton(
            button_frame,
            text="Couleur Secondaire",
            fg_color=COLORS['secondary'],
            hover_color='#0A2F5C',
            font=('Segoe UI', 12, 'bold')
        )
        btn_secondary.pack(side='left', padx=10)
        
        # Test des textes
        text_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        text_frame.pack(pady=20)
        
        ctk.CTkLabel(
            text_frame,
            text="Texte principal",
            font=('Segoe UI', 14, 'normal'),
            text_color=COLORS['text']
        ).pack()
        
        ctk.CTkLabel(
            text_frame,
            text="Texte secondaire",
            font=('Segoe UI', 12, 'normal'),
            text_color=COLORS['text_secondary']
        ).pack()
        
        # Zone de saisie
        entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Test de saisie...",
            font=('Segoe UI', 12),
            fg_color=COLORS['surface'],
            width=200,
            height=36
        )
        entry.pack(pady=20)
        
        # Statut
        status_frame = ctk.CTkFrame(
            self,
            height=30,
            fg_color=COLORS['background'],
            corner_radius=0
        )
        status_frame.pack(side='bottom', fill='x')
        
        ctk.CTkLabel(
            status_frame,
            text="✅ Interface graphique fonctionnelle avec votre palette de couleurs !",
            font=('Segoe UI', 10),
            text_color=COLORS['text_secondary']
        ).pack(pady=5)

def main():
    """Lance l'application de test."""
    print("🎨 Lancement du test d'interface...")
    
    try:
        app = SimpleTestApp()
        print("✅ Interface créée avec succès !")
        print("🎯 Test de votre palette de couleurs en cours...")
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()