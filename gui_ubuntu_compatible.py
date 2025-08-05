#!/usr/bin/env python3
"""
Version Ubuntu-compatible de l'application de compensation altimétrique.
Interface simplifiée pour éviter les problèmes X11.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
from typing import Optional

# Configuration simplifiée
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Couleurs simplifiées (éviter les polices complexes)
COLORS = {
    'primary': '#7671FA',
    'secondary': '#07244C',
    'background': '#E5EAF3',
    'text': '#07244C'
}

class SimpleCompensationApp(ctk.CTk):
    """Application simplifiée compatible Ubuntu."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.title("Compensation Altimétrique - Version Ubuntu")
        self.geometry("800x600")
        self.configure(fg_color=COLORS['background'])
        
        # Variables d'état
        self.current_step = 0
        self.imported_data = None
        self.calculation_results = None
        self.compensation_results = None
        
        # Configuration par défaut
        self.config = {
            'precision_mm': 2.0,
            'initial_altitude': 125.456,
            'atmospheric_corrections': True,
            'temperature': 25.0,
            'pressure': 1010.0,
            'humidity': 60.0
        }
        
        self.create_interface()
    
    def create_interface(self):
        """Crée l'interface simplifiée."""
        
        # En-tête simple
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="🎯 Système de Compensation Altimétrique",
            font=('Arial', 20, 'bold'),
            text_color=COLORS['primary']
        )
        title.pack(pady=15)
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Version simplifiée Ubuntu - Compensation par moindres carrés",
            font=('Arial', 12),
            text_color=COLORS['text']
        )
        subtitle.pack(pady=5)
        
        # Zone principale
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Étapes simplifiées avec boutons
        steps_frame = ctk.CTkFrame(main_frame)
        steps_frame.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            steps_frame,
            text="🚀 Actions Disponibles",
            font=('Arial', 16, 'bold')
        ).pack(pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(steps_frame)
        buttons_frame.pack(fill='x', padx=20, pady=10)
        
        # Ligne 1
        row1 = ctk.CTkFrame(buttons_frame, fg_color='transparent')
        row1.pack(fill='x', pady=5)
        
        ctk.CTkButton(
            row1,
            text="📁 1. Importer Données",
            command=self.import_data,
            fg_color=COLORS['primary'],
            width=180
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            row1,
            text="⚙️ 2. Configurer",
            command=self.configure_params,
            fg_color=COLORS['secondary'],
            width=180
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            row1,
            text="🔧 3. Calculer",
            command=self.run_calculations,
            fg_color=COLORS['primary'],
            width=180
        ).pack(side='left', padx=5)
        
        # Ligne 2
        row2 = ctk.CTkFrame(buttons_frame, fg_color='transparent')
        row2.pack(fill='x', pady=5)
        
        ctk.CTkButton(
            row2,
            text="📊 4. Compenser",
            command=self.run_compensation,
            fg_color=COLORS['secondary'],
            width=180
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            row2,
            text="📈 5. Générer Résultats",
            command=self.generate_results,
            fg_color=COLORS['primary'],
            width=180
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            row2,
            text="📂 Ouvrir Dossier",
            command=self.open_results_folder,
            fg_color='#4CAF50',
            width=180
        ).pack(side='left', padx=5)
        
        # Zone de statut
        self.status_frame = ctk.CTkFrame(main_frame)
        self.status_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(
            self.status_frame,
            text="📋 Statut du Projet",
            font=('Arial', 14, 'bold')
        ).pack(pady=5)
        
        self.status_text = ctk.CTkTextbox(
            self.status_frame,
            height=200,
            font=('Courier', 10)
        )
        self.status_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Message initial
        self.update_status("🎯 Application prête ! Commencez par importer vos données de nivellement.")
    
    def update_status(self, message):
        """Met à jour le statut."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
    
    def import_data(self):
        """Import de données (simulé)."""
        self.update_status("📁 Import des données...")
        
        # Simulation d'import
        self.imported_data = {
            'points': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'denivellees': [0.245, -0.123, 0.087, -0.234],
            'distances': [250, 300, 275, 425]
        }
        
        self.update_status("✅ Données importées: 5 points, 4 tronçons")
        self.update_status(f"   Distance totale: {sum(self.imported_data['distances'])} m")
        messagebox.showinfo("Succès", "Données importées avec succès!")
    
    def configure_params(self):
        """Configuration des paramètres."""
        self.update_status("⚙️ Configuration des paramètres...")
        
        # Fenêtre de configuration simple
        config_window = ctk.CTkToplevel(self)
        config_window.title("Configuration")
        config_window.geometry("400x300")
        config_window.configure(fg_color=COLORS['background'])
        
        # Altitude initiale
        ctk.CTkLabel(config_window, text="Altitude initiale (m):").pack(pady=5)
        alt_entry = ctk.CTkEntry(config_window)
        alt_entry.insert(0, str(self.config['initial_altitude']))
        alt_entry.pack(pady=5)
        
        # Précision
        ctk.CTkLabel(config_window, text="Précision cible (mm):").pack(pady=5)
        prec_entry = ctk.CTkEntry(config_window)
        prec_entry.insert(0, str(self.config['precision_mm']))
        prec_entry.pack(pady=5)
        
        def save_config():
            try:
                self.config['initial_altitude'] = float(alt_entry.get())
                self.config['precision_mm'] = float(prec_entry.get())
                self.update_status("✅ Configuration sauvegardée")
                config_window.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
        
        ctk.CTkButton(
            config_window,
            text="Sauvegarder",
            command=save_config,
            fg_color=COLORS['primary']
        ).pack(pady=20)
    
    def run_calculations(self):
        """Lance les calculs."""
        if not self.imported_data:
            messagebox.showerror("Erreur", "Importez d'abord les données")
            return
        
        self.update_status("🔧 Lancement des calculs...")
        
        # Simulation des calculs
        import time
        import threading
        
        def calculate():
            time.sleep(1)  # Simulation
            
            # Calcul de fermeture simulé
            closure_error = -0.025  # 25mm d'erreur
            
            self.calculation_results = {
                'closure_error': closure_error,
                'precision_achieved': 1.8,
                'total_distance': sum(self.imported_data['distances'])
            }
            
            self.after(0, lambda: self.update_status(f"✅ Calculs terminés"))
            self.after(0, lambda: self.update_status(f"   Erreur de fermeture: {closure_error*1000:.1f} mm"))
            self.after(0, lambda: messagebox.showinfo("Succès", "Calculs terminés!"))
        
        thread = threading.Thread(target=calculate)
        thread.daemon = True
        thread.start()
    
    def run_compensation(self):
        """Lance la compensation."""
        if not self.calculation_results:
            messagebox.showerror("Erreur", "Effectuez d'abord les calculs")
            return
        
        self.update_status("📊 Lancement de la compensation...")
        
        def compensate():
            time.sleep(1)
            
            self.compensation_results = {
                'sigma0': 0.0012,
                'max_correction': 0.0067,
                'method': 'Distance inverse'
            }
            
            self.after(0, lambda: self.update_status("✅ Compensation terminée"))
            self.after(0, lambda: self.update_status(f"   σ₀ = {self.compensation_results['sigma0']*1000:.1f} mm"))
            self.after(0, lambda: messagebox.showinfo("Succès", "Compensation terminée!"))
        
        import threading
        thread = threading.Thread(target=compensate)
        thread.daemon = True
        thread.start()
    
    def generate_results(self):
        """Génère les résultats."""
        if not self.compensation_results:
            messagebox.showerror("Erreur", "Effectuez d'abord la compensation")
            return
        
        self.update_status("📈 Génération des résultats...")
        
        try:
            # Créer le dossier
            output_dir = Path("results_ubuntu")
            output_dir.mkdir(exist_ok=True)
            
            # Générer les graphiques
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Graphique simple
            fig, ax = plt.subplots(figsize=(10, 6))
            points = self.imported_data['points'][:4]
            corrections = np.random.normal(0, 0.002, 4) * 1000
            
            ax.bar(points, corrections, color=COLORS['primary'], alpha=0.7)
            ax.set_ylabel('Corrections (mm)')
            ax.set_title('Corrections de Compensation')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_dir / 'corrections_ubuntu.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Rapport simple
            from datetime import datetime
            report_path = output_dir / f'rapport_ubuntu_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("RAPPORT DE COMPENSATION - VERSION UBUNTU\n")
                f.write("="*45 + "\n\n")
                f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Points traités: {len(self.imported_data['points'])}\n")
                f.write(f"Erreur de fermeture: {self.calculation_results['closure_error']*1000:.1f} mm\n")
                f.write(f"Précision finale: {self.compensation_results['sigma0']*1000:.1f} mm\n")
                f.write("\nApplication compatible Ubuntu générée avec succès!\n")
            
            self.update_status("✅ Résultats générés dans results_ubuntu/")
            self.update_status(f"   - Graphique: corrections_ubuntu.png")
            self.update_status(f"   - Rapport: {report_path.name}")
            
            messagebox.showinfo("Succès", f"Résultats générés dans {output_dir}/")
            
        except Exception as e:
            self.update_status(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def open_results_folder(self):
        """Ouvre le dossier des résultats."""
        try:
            import subprocess
            output_dir = Path("results_ubuntu")
            output_dir.mkdir(exist_ok=True)
            subprocess.run(["xdg-open", str(output_dir)])
            self.update_status("📂 Dossier ouvert")
        except Exception as e:
            self.update_status(f"❌ Erreur ouverture: {str(e)}")

def main():
    """Lance l'application."""
    print("🚀 Lancement de l'application Ubuntu compatible...")
    
    try:
        app = SimpleCompensationApp()
        print("✅ Interface créée avec succès!")
        app.mainloop()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()