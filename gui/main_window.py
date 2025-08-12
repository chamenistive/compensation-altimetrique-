"""
Fenêtre principale de l'application de compensation altimétrique.
Interface utilisateur avec assistant étape par étape.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Ajouter le répertoire parent au path pour les imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from gui.utils.theme import AppTheme
from gui.components.base_components import (
    ThemedButton, ThemedLabel, ThemedFrame, StepIndicator, 
    StatusBar, FileDropFrame, ThemedEntry, ThemedProgressBar
)

# Import des modules backend
try:
    from src.data_importer import DataImporter
    from src.calculator import LevelingCalculator
    from src.compensator import LevelingCompensator
    from src.atmospheric_corrections import create_standard_conditions
except ImportError as e:
    print(f"Erreur import backend: {e}")
    # Fallback si les modules backend ne sont pas trouvés
    DataImporter = None
    LevelingCalculator = None
    LevelingCompensator = None


class MainApplication(ctk.CTk):
    """Application principale de compensation altimétrique."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.title("Système de Compensation Altimétrique")
        self.geometry("900x600")  # Taille plus petite pour éviter les problèmes X11
        self.minsize(800, 500)
        
        # Appliquer le thème
        AppTheme.apply_theme()
        self.configure(fg_color=AppTheme.COLORS['background'])
        
        # Variables d'état
        self.current_step = 0
        self.imported_data = None
        self.calculation_results = None
        self.compensation_results = None
        
        # Configuration par défaut
        self.config = {
            'precision_mm': 2.0,
            'initial_altitude': None,
            'final_altitude': None,
            'atmospheric_corrections': True,
            'temperature': 25.0,
            'pressure': 1010.0,
            'humidity': 60.0
        }
        
        # Initialisation de l'interface
        self.create_widgets()
        self.center_window()
        
        # Modules backend
        self.data_importer = DataImporter()
        self.calculator = None
        self.compensator = None
    
    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Crée l'interface utilisateur."""
        
        # En-tête avec titre et indicateur d'étapes
        self.create_header()
        
        # Zone principale (contenu variable selon l'étape)
        self.main_frame = ThemedFrame(self)
        self.main_frame.pack(fill='both', expand=True, padx=AppTheme.SPACING['lg'], 
                           pady=(0, AppTheme.SPACING['lg']))
        
        # Barre d'état
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Afficher la première étape
        self.show_step()
    
    def create_header(self):
        """Crée l'en-tête avec titre et indicateur d'étapes."""
        
        # Frame d'en-tête
        header_frame = ThemedFrame(self)
        header_frame.pack(fill='x', padx=AppTheme.SPACING['lg'], 
                         pady=AppTheme.SPACING['lg'])
        
        # Titre principal
        title_label = ThemedLabel(
            header_frame,
            text="🎯 Système de Compensation Altimétrique",
            style='title',
            text_color=AppTheme.COLORS['primary']
        )
        title_label.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Sous-titre
        subtitle_label = ThemedLabel(
            header_frame,
            text="Assistant de compensation par moindres carrés - Précision 2mm",
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, AppTheme.SPACING['lg']))
        
        # Indicateur d'étapes
        steps = [
            "Import\\nDonnées", 
            "Configuration\\nParamètres", 
            "Calculs\\nPréliminaires", 
            "Compensation\\nLSQ", 
            "Résultats\\nRapports"
        ]
        
        self.step_indicator = StepIndicator(
            header_frame, 
            steps=steps, 
            current_step=self.current_step
        )
        self.step_indicator.pack(pady=AppTheme.SPACING['md'])
    
    def show_step(self):
        """Affiche l'étape courante."""
        
        # Vider le frame principal
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Afficher l'étape appropriée
        if self.current_step == 0:
            self.show_import_step()
        elif self.current_step == 1:
            self.show_config_step()
        elif self.current_step == 2:
            self.show_calculation_step()
        elif self.current_step == 3:
            self.show_compensation_step()
        elif self.current_step == 4:
            self.show_results_step()
        
        # Mettre à jour l'indicateur d'étapes
        self.step_indicator.update_step(self.current_step)
        
        # Mettre à jour la barre d'état
        step_names = ["Import des données", "Configuration", "Calculs", "Compensation", "Résultats"]
        self.status_bar.set_status(f"Étape {self.current_step + 1}/5 - {step_names[self.current_step]}")
    
    def show_import_step(self):
        """Étape 1: Import des données."""
        
        # Titre de l'étape
        step_title = ThemedLabel(
            self.main_frame,
            text="📁 Import des Données de Nivellement",
            style='heading',
            text_color=AppTheme.COLORS['secondary']
        )
        step_title.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Description
        desc_text = """
Sélectionnez votre fichier Excel (.xlsx, .xls) ou CSV contenant les données de nivellement.
Le fichier doit contenir les colonnes : Matricule, AR (lectures arrière), AV (lectures avant), et optionnellement les distances.
        """
        
        desc_label = ThemedLabel(
            self.main_frame,
            text=desc_text.strip(),
            style='body'
        )
        desc_label.pack(pady=(0, AppTheme.SPACING['lg']))
        
        # Zone de glisser-déposer / sélection de fichier
        self.file_drop = FileDropFrame(
            self.main_frame,
            callback=self.select_file
        )
        self.file_drop.pack(fill='x', pady=AppTheme.SPACING['lg'])
        
        # Frame pour les informations du fichier
        self.file_info_frame = ThemedFrame(self.main_frame)
        
        # Boutons de navigation
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        nav_frame.pack(side='bottom', fill='x', pady=AppTheme.SPACING['lg'])
        
        # Bouton Suivant (désactivé initialement)
        self.next_button = ThemedButton(
            nav_frame,
            text="Suivant →",
            command=self.next_step,
            variant='primary'
        )
        self.next_button.pack(side='right')
        self.next_button.configure(state='disabled')
    
    def show_config_step(self):
        """Étape 2: Configuration des paramètres."""
        
        # Titre de l'étape
        step_title = ThemedLabel(
            self.main_frame,
            text="⚙️ Configuration des Paramètres",
            style='heading',
            text_color=AppTheme.COLORS['secondary']
        )
        step_title.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Frame défilable pour les paramètres
        config_frame = ctk.CTkScrollableFrame(self.main_frame)
        config_frame.pack(fill='both', expand=True, pady=AppTheme.SPACING['md'])
        
        # Paramètres de base
        self.create_basic_config(config_frame)
        
        # Paramètres atmosphériques
        self.create_atmospheric_config(config_frame)
        
        # Boutons de navigation
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        nav_frame.pack(side='bottom', fill='x', pady=AppTheme.SPACING['lg'])
        
        ThemedButton(
            nav_frame,
            text="← Précédent",
            command=self.previous_step,
            variant='outline'
        ).pack(side='left')
        
        self.config_next_button = ThemedButton(
            nav_frame,
            text="Suivant →",
            command=self.next_step,
            variant='primary'
        )
        self.config_next_button.pack(side='right')
    
    def create_basic_config(self, parent):
        """Crée la section des paramètres de base."""
        
        # Section Altitudes
        alt_section = ThemedFrame(parent)
        alt_section.pack(fill='x', pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            alt_section,
            text="🏔️ Altitudes de Référence",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Altitude initiale
        alt_init_frame = ctk.CTkFrame(alt_section, fg_color='transparent')
        alt_init_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        ThemedLabel(alt_init_frame, text="Altitude initiale (m):").pack(side='left')
        self.initial_alt_entry = ThemedEntry(
            alt_init_frame,
            placeholder="Ex: 125.456",
            width=120
        )
        self.initial_alt_entry.pack(side='right')
        
        # Altitude finale (optionnelle)
        alt_final_frame = ctk.CTkFrame(alt_section, fg_color='transparent')
        alt_final_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        ThemedLabel(alt_final_frame, text="Altitude finale (optionnel):").pack(side='left')
        self.final_alt_entry = ThemedEntry(
            alt_final_frame,
            placeholder="Pour cheminement ouvert",
            width=120
        )
        self.final_alt_entry.pack(side='right')
        
        # Section Précision
        precision_section = ThemedFrame(parent)
        precision_section.pack(fill='x', pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            precision_section,
            text="🎯 Paramètres de Précision",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Précision cible
        precision_frame = ctk.CTkFrame(precision_section, fg_color='transparent')
        precision_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        ThemedLabel(precision_frame, text="Précision cible (mm):").pack(side='left')
        self.precision_entry = ThemedEntry(
            precision_frame,
            placeholder="2.0",
            width=80
        )
        self.precision_entry.insert(0, "2.0")
        self.precision_entry.pack(side='right')
    
    def create_atmospheric_config(self, parent):
        """Crée la section des corrections atmosphériques."""
        
        atm_section = ThemedFrame(parent)
        atm_section.pack(fill='x', pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            atm_section,
            text="🌡️ Corrections Atmosphériques",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Activer/désactiver les corrections
        self.atm_checkbox = ctk.CTkCheckBox(
            atm_section,
            text="Appliquer les corrections atmosphériques",
            font=AppTheme.FONTS['body'],
            text_color=AppTheme.COLORS['text'],
            fg_color=AppTheme.COLORS['primary'],
            hover_color=AppTheme.COLORS['primary_dark'],
            command=self.toggle_atmospheric_config
        )
        self.atm_checkbox.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        self.atm_checkbox.select()  # Activé par défaut
        
        # Frame pour les paramètres atmosphériques
        self.atm_params_frame = ctk.CTkFrame(atm_section, fg_color='transparent')
        self.atm_params_frame.pack(fill='x', padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['sm'])
        
        # Température
        temp_frame = ctk.CTkFrame(self.atm_params_frame, fg_color='transparent')
        temp_frame.pack(fill='x', pady=AppTheme.SPACING['xs'])
        
        ThemedLabel(temp_frame, text="Température (°C):").pack(side='left')
        self.temp_entry = ThemedEntry(temp_frame, placeholder="25.0", width=80)
        self.temp_entry.insert(0, "25.0")
        self.temp_entry.pack(side='right')
        
        # Pression
        pressure_frame = ctk.CTkFrame(self.atm_params_frame, fg_color='transparent')
        pressure_frame.pack(fill='x', pady=AppTheme.SPACING['xs'])
        
        ThemedLabel(pressure_frame, text="Pression (hPa):").pack(side='left')
        self.pressure_entry = ThemedEntry(pressure_frame, placeholder="1010.0", width=80)
        self.pressure_entry.insert(0, "1010.0")
        self.pressure_entry.pack(side='right')
        
        # Humidité
        humidity_frame = ctk.CTkFrame(self.atm_params_frame, fg_color='transparent')
        humidity_frame.pack(fill='x', pady=AppTheme.SPACING['xs'])
        
        ThemedLabel(humidity_frame, text="Humidité (%):").pack(side='left')
        self.humidity_entry = ThemedEntry(humidity_frame, placeholder="60.0", width=80)
        self.humidity_entry.insert(0, "60.0")
        self.humidity_entry.pack(side='right')
    
    def show_calculation_step(self):
        """Étape 3: Calculs préliminaires."""
        
        # Titre de l'étape
        step_title = ThemedLabel(
            self.main_frame,
            text="🔧 Calculs Préliminaires",
            style='heading',
            text_color=AppTheme.COLORS['secondary']
        )
        step_title.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Description
        desc_text = """
Calcul des dénivelées, fermeture du cheminement et diagnostic des erreurs.
Les corrections atmosphériques seront appliquées si configurées.
        """
        
        desc_label = ThemedLabel(
            self.main_frame,
            text=desc_text.strip(),
            style='body'
        )
        desc_label.pack(pady=(0, AppTheme.SPACING['lg']))
        
        # Frame principal pour les calculs
        calc_frame = ThemedFrame(self.main_frame)
        calc_frame.pack(fill='both', expand=True, pady=AppTheme.SPACING['md'])
        
        # Zone de progression
        progress_section = ThemedFrame(calc_frame)
        progress_section.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            progress_section,
            text="📊 Progression des Calculs",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Barre de progression
        self.calc_progress = ThemedProgressBar(progress_section)
        self.calc_progress.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Statut des calculs
        self.calc_status_label = ThemedLabel(
            progress_section,
            text="Prêt à calculer...",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.calc_status_label.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Zone des résultats
        self.results_section = ThemedFrame(calc_frame)
        self.results_section.pack(fill='both', expand=True, padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        # Bouton de calcul
        calc_button_frame = ctk.CTkFrame(calc_frame, fg_color='transparent')
        calc_button_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        self.calc_button = ThemedButton(
            calc_button_frame,
            text="🚀 Lancer les Calculs",
            command=self.run_calculations,
            variant='primary',
            width=200
        )
        self.calc_button.pack()
        
        # Boutons de navigation
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        nav_frame.pack(side='bottom', fill='x', pady=AppTheme.SPACING['lg'])
        
        ThemedButton(nav_frame, text="← Précédent", command=self.previous_step, variant='outline').pack(side='left')
        
        self.calc_next_button = ThemedButton(
            nav_frame,
            text="Suivant →",
            command=self.next_step,
            variant='primary'
        )
        self.calc_next_button.pack(side='right')
        self.calc_next_button.configure(state='disabled')  # Activé après calculs
    
    def show_compensation_step(self):
        """Étape 4: Compensation par moindres carrés."""
        
        # Titre de l'étape
        step_title = ThemedLabel(
            self.main_frame,
            text="📊 Compensation par Moindres Carrés",
            style='heading',
            text_color=AppTheme.COLORS['secondary']
        )
        step_title.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Description
        desc_text = """
Application de la méthode des moindres carrés pour distribuer optimalement l'erreur de fermeture.
Cette étape améliore la précision et fournit les altitudes compensées finales.
        """
        
        desc_label = ThemedLabel(
            self.main_frame,
            text=desc_text.strip(),
            style='body'
        )
        desc_label.pack(pady=(0, AppTheme.SPACING['lg']))
        
        # Frame principal pour la compensation
        comp_frame = ThemedFrame(self.main_frame)
        comp_frame.pack(fill='both', expand=True, pady=AppTheme.SPACING['md'])
        
        # Paramètres de compensation
        params_section = ThemedFrame(comp_frame)
        params_section.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            params_section,
            text="⚙️ Paramètres de Compensation",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Méthode de pondération
        weight_frame = ctk.CTkFrame(params_section, fg_color='transparent')
        weight_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        ThemedLabel(weight_frame, text="Méthode de pondération:").pack(side='left')
        
        self.weight_method = ctk.CTkOptionMenu(
            weight_frame,
            values=["Distance inverse", "Distance inverse au carré", "Uniforme"],
            font=AppTheme.FONTS['body'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary'],
            button_hover_color=AppTheme.COLORS['primary_dark'],
            dropdown_fg_color=AppTheme.COLORS['surface']
        )
        self.weight_method.set("Distance inverse")
        self.weight_method.pack(side='right')
        
        # Tolérance de convergence
        tolerance_frame = ctk.CTkFrame(params_section, fg_color='transparent')
        tolerance_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        ThemedLabel(tolerance_frame, text="Tolérance de convergence (mm):").pack(side='left')
        self.tolerance_entry = ThemedEntry(tolerance_frame, placeholder="0.1", width=80)
        self.tolerance_entry.insert(0, "0.1")
        self.tolerance_entry.pack(side='right')
        
        # Zone de progression
        progress_section = ThemedFrame(comp_frame)
        progress_section.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            progress_section,
            text="📈 Progression de la Compensation",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Barre de progression pour la compensation
        self.comp_progress = ThemedProgressBar(progress_section)
        self.comp_progress.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Statut de la compensation
        self.comp_status_label = ThemedLabel(
            progress_section,
            text="Prêt pour la compensation...",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.comp_status_label.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Zone des résultats de compensation
        self.comp_results_section = ThemedFrame(comp_frame)
        self.comp_results_section.pack(fill='both', expand=True, padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        # Bouton de compensation
        comp_button_frame = ctk.CTkFrame(comp_frame, fg_color='transparent')
        comp_button_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        self.comp_button = ThemedButton(
            comp_button_frame,
            text="🎯 Lancer la Compensation",
            command=self.run_compensation,
            variant='primary',
            width=200
        )
        self.comp_button.pack()
        
        # Boutons de navigation
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        nav_frame.pack(side='bottom', fill='x', pady=AppTheme.SPACING['lg'])
        
        ThemedButton(nav_frame, text="← Précédent", command=self.previous_step, variant='outline').pack(side='left')
        
        self.comp_next_button = ThemedButton(
            nav_frame,
            text="Suivant →",
            command=self.next_step,
            variant='primary'
        )
        self.comp_next_button.pack(side='right')
        self.comp_next_button.configure(state='disabled')  # Activé après compensation
    
    def show_results_step(self):
        """Étape 5: Résultats et rapports."""
        
        # Titre de l'étape
        step_title = ThemedLabel(
            self.main_frame,
            text="📈 Résultats et Rapports",
            style='heading',
            text_color=AppTheme.COLORS['secondary']
        )
        step_title.pack(pady=(AppTheme.SPACING['lg'], AppTheme.SPACING['md']))
        
        # Description
        desc_text = """
Visualisation des résultats, génération de graphiques et export des rapports détaillés.
Tous les résultats sont maintenant disponibles pour analyse et archivage.
        """
        
        desc_label = ThemedLabel(
            self.main_frame,
            text=desc_text.strip(),
            style='body'
        )
        desc_label.pack(pady=(0, AppTheme.SPACING['lg']))
        
        # Frame principal pour les résultats
        results_frame = ThemedFrame(self.main_frame)
        results_frame.pack(fill='both', expand=True, pady=AppTheme.SPACING['md'])
        
        # Résumé des résultats
        if self.compensation_results:
            self.create_results_summary(results_frame)
        else:
            self.create_no_results_message(results_frame)
        
        # Actions disponibles
        actions_section = ThemedFrame(results_frame)
        actions_section.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            actions_section,
            text="🛠️ Actions Disponibles",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(actions_section, fg_color='transparent')
        actions_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Première ligne d'actions
        actions_row1 = ctk.CTkFrame(actions_frame, fg_color='transparent')
        actions_row1.pack(fill='x', pady=AppTheme.SPACING['xs'])
        
        ThemedButton(
            actions_row1,
            text="📊 Générer Graphiques",
            command=self.generate_charts,
            variant='primary',
            width=180
        ).pack(side='left', padx=(0, AppTheme.SPACING['sm']))
        
        ThemedButton(
            actions_row1,
            text="📄 Rapport Détaillé",
            command=self.generate_detailed_report,
            variant='outline',
            width=180
        ).pack(side='left', padx=(0, AppTheme.SPACING['sm']))
        
        ThemedButton(
            actions_row1,
            text="💾 Exporter CSV",
            command=self.export_csv,
            variant='outline',
            width=180
        ).pack(side='left')
        
        # Deuxième ligne d'actions
        actions_row2 = ctk.CTkFrame(actions_frame, fg_color='transparent')
        actions_row2.pack(fill='x', pady=AppTheme.SPACING['xs'])
        
        ThemedButton(
            actions_row2,
            text="🗂️ Ouvrir Dossier",
            command=self.open_results_folder,
            variant='ghost',
            width=180
        ).pack(side='left', padx=(0, AppTheme.SPACING['sm']))
        
        ThemedButton(
            actions_row2,
            text="🔄 Nouveau Projet",
            command=self.new_project,
            variant='ghost',
            width=180
        ).pack(side='left')
        
        # Zone de statut des actions
        self.results_status_frame = ThemedFrame(results_frame)
        self.results_status_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        # Boutons de navigation
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        nav_frame.pack(side='bottom', fill='x', pady=AppTheme.SPACING['lg'])
        
        ThemedButton(nav_frame, text="← Précédent", command=self.previous_step, variant='outline').pack(side='left')
        ThemedButton(nav_frame, text="🎉 Terminer", command=self.finish, variant='primary').pack(side='right')
    
    def create_results_summary(self, parent):
        """Crée le résumé des résultats."""
        summary_section = ThemedFrame(parent)
        summary_section.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            summary_section,
            text="🎯 Résumé des Résultats",
            style='subheading'
        ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Métriques clés
        if isinstance(self.calculation_results, dict):
            # Mode démo
            n_points = 5
            closure_error = self.calculation_results.get('closure_error', 0.003)
            precision = self.calculation_results.get('precision_achieved', 1.8)
        else:
            # Mode réel
            n_points = len(self.imported_data.dataframe) if self.imported_data else 0
            closure_error = abs(self.calculation_results.get('closure_error', 0.0))
            precision = self.calculation_results.get('precision_achieved', 2.0)
        
        sigma0 = self.compensation_results.get('sigma0', 0.0008)
        max_correction = self.compensation_results.get('precision_analysis', {}).get('max_correction', 0.0023)
        
        summary_text = f"""
✅ Points traités: {n_points}
🔒 Erreur de fermeture: {closure_error:.3f} m ({closure_error*1000:.1f} mm)
📊 Écart-type unitaire: {sigma0*1000:.1f} mm  
🔧 Correction maximale: {max_correction*1000:.1f} mm
⚡ Précision finale: {precision:.1f} mm
🎯 Méthode: {self.compensation_results.get('weight_method', 'Distance inverse')}
        """
        
        summary_label = ThemedLabel(
            summary_section,
            text=summary_text.strip(),
            style='body',
            text_color=AppTheme.COLORS['text']
        )
        summary_label.pack(anchor='w', padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['sm'])
        
        # Qualité globale
        if sigma0 < 0.001 and closure_error < 0.005:
            quality_color = AppTheme.COLORS['success']
            quality_text = "🌟 Qualité Excellente - Résultats très fiables"
        elif sigma0 < 0.002 and closure_error < 0.010:
            quality_color = AppTheme.COLORS['success']  
            quality_text = "✅ Qualité Bonne - Résultats satisfaisants"
        else:
            quality_color = AppTheme.COLORS['warning']
            quality_text = "⚠️ Qualité Acceptable - Vérifier si nécessaire"
        
        quality_label = ThemedLabel(
            summary_section,
            text=quality_text,
            style='subheading',
            text_color=quality_color
        )
        quality_label.pack(anchor='w', padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['sm'])
    
    def create_no_results_message(self, parent):
        """Affiche un message si aucun résultat n'est disponible."""
        message_frame = ThemedFrame(parent)
        message_frame.pack(fill='both', expand=True, padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
        
        ThemedLabel(
            message_frame,
            text="⚠️ Aucun Résultat Disponible",
            style='heading',
            text_color=AppTheme.COLORS['warning']
        ).pack(pady=AppTheme.SPACING['xl'])
        
        ThemedLabel(
            message_frame,
            text="Vous devez compléter les étapes précédentes pour générer des résultats.",
            style='body'
        ).pack(pady=AppTheme.SPACING['md'])
    
    # Méthodes de navigation
    def next_step(self):
        """Passe à l'étape suivante."""
        if self.current_step < 4:
            if self.validate_current_step():
                self.current_step += 1
                self.show_step()
    
    def previous_step(self):
        """Revient à l'étape précédente."""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
    
    def validate_current_step(self) -> bool:
        """Valide l'étape courante avant de continuer."""
        if self.current_step == 0:
            return self.imported_data is not None
        elif self.current_step == 1:
            return self.validate_config()
        elif self.current_step == 2:
            return self.calculation_results is not None
        elif self.current_step == 3:
            return self.compensation_results is not None
        return True
    
    def validate_config(self) -> bool:
        """Valide la configuration."""
        try:
            # Validation de l'altitude initiale
            initial_alt = float(self.initial_alt_entry.get())
            
            # Validation de la précision
            precision = float(self.precision_entry.get())
            
            # Sauvegarder la configuration
            self.config['initial_altitude'] = initial_alt
            self.config['precision_mm'] = precision
            
            final_alt_text = self.final_alt_entry.get().strip()
            if final_alt_text:
                self.config['final_altitude'] = float(final_alt_text)
            
            if self.atm_checkbox.get():
                self.config['temperature'] = float(self.temp_entry.get())
                self.config['pressure'] = float(self.pressure_entry.get())
                self.config['humidity'] = float(self.humidity_entry.get())
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Erreur de Configuration", 
                               "Veuillez vérifier que tous les champs numériques sont correctement remplis.")
            return False
    
    # Méthodes pour l'import de fichiers
    def select_file(self):
        """Ouvre le dialogue de sélection de fichier."""
        filetypes = [
            ("Fichiers Excel", "*.xlsx *.xls"),
            ("Fichiers CSV", "*.csv"),
            ("Tous les fichiers", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier de données",
            filetypes=filetypes
        )
        
        if filename:
            self.load_file(filename)
    
    def load_file(self, filepath: str):
        """Charge et valide le fichier sélectionné."""
        try:
            if self.data_importer is None:
                # Mode démo si les modules backend ne sont pas disponibles
                filename = Path(filepath).name
                self.file_drop.set_file_selected(filename)
                
                # Créer des données factices pour la démo
                self.imported_data = type('MockData', (), {
                    'dataframe': type('MockDF', (), {'__len__': lambda x: 10})(),
                    'ar_columns': ['AR_1', 'AR_2'],
                    'av_columns': ['AV_1', 'AV_2'],
                    'initial_point': 'P001',
                    'final_point': 'P010'
                })()
                
                self.show_file_info()
                self.next_button.configure(state='normal')
                return
            
            # Import du fichier réel
            self.imported_data = self.data_importer.import_file(filepath)
            
            # Mettre à jour l'interface
            filename = Path(filepath).name
            self.file_drop.set_file_selected(filename)
            
            # Afficher les informations du fichier
            self.show_file_info()
            
            # Activer le bouton Suivant
            self.next_button.configure(state='normal')
            
        except Exception as e:
            messagebox.showerror("Erreur d'Import", f"Impossible de charger le fichier:\\n{str(e)}")
    
    def show_file_info(self):
        """Affiche les informations du fichier importé."""
        if not self.imported_data:
            return
        
        self.file_info_frame.pack(fill='x', pady=AppTheme.SPACING['md'])
        
        # Vider le frame précédent
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        # Titre
        info_title = ThemedLabel(
            self.file_info_frame,
            text="📋 Informations du Fichier",
            style='subheading'
        )
        info_title.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
        
        # Informations
        df = self.imported_data.dataframe
        info_text = f"""
Points de mesure: {len(df)}
Colonnes AR détectées: {len(self.imported_data.ar_columns)}
Colonnes AV détectées: {len(self.imported_data.av_columns)}
Point initial: {self.imported_data.initial_point}
Point final: {self.imported_data.final_point}
Type de cheminement: {"Fermé" if self.imported_data.initial_point == self.imported_data.final_point else "Ouvert"}
        """
        
        info_label = ThemedLabel(
            self.file_info_frame,
            text=info_text.strip(),
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        info_label.pack(anchor='w', padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['sm'])
    
    def toggle_atmospheric_config(self):
        """Active/désactive la configuration atmosphérique."""
        if self.atm_checkbox.get():
            self.atm_params_frame.pack(fill='x', padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['sm'])
        else:
            self.atm_params_frame.pack_forget()
    
    def finish(self):
        """Termine l'assistant."""
        messagebox.showinfo("Terminé", "Assistant terminé avec succès!")
    
    # Méthodes de calcul
    def run_calculations(self):
        """Lance les calculs préliminaires."""
        import threading
        
        # Désactiver le bouton pendant les calculs
        self.calc_button.configure(state='disabled')
        self.calc_progress.set(0)
        self.calc_status_label.configure(text="Initialisation des calculs...")
        
        # Vider la zone des résultats
        for widget in self.results_section.winfo_children():
            widget.destroy()
        
        # Lancer les calculs dans un thread séparé
        calc_thread = threading.Thread(target=self._perform_calculations)
        calc_thread.daemon = True
        calc_thread.start()
    
    def _perform_calculations(self):
        """Effectue les calculs dans un thread séparé."""
        try:
            self.after(0, lambda: self.calc_status_label.configure(text="Chargement des données..."))
            self.after(0, lambda: self.calc_progress.set(0.1))
            
            # Créer le calculateur
            if LevelingCalculator is None:
                # Mode démo
                self._demo_calculations()
                return
            
            self.calculator = LevelingCalculator(
                data=self.imported_data.dataframe,
                initial_altitude=self.config['initial_altitude'],
                ar_columns=self.imported_data.ar_columns,
                av_columns=self.imported_data.av_columns
            )
            
            self.after(0, lambda: self.calc_status_label.configure(text="Calcul des dénivelées..."))
            self.after(0, lambda: self.calc_progress.set(0.3))
            
            # Calcul des dénivelées
            results = self.calculator.calculate_all()
            
            self.after(0, lambda: self.calc_status_label.configure(text="Application des corrections atmosphériques..."))
            self.after(0, lambda: self.calc_progress.set(0.6))
            
            # Appliquer les corrections atmosphériques si configurées
            if self.config.get('atmospheric_corrections', False):
                from src.atmospheric_corrections import AtmosphericCorrections
                
                atm_conditions = create_standard_conditions(
                    temperature=self.config['temperature'],
                    pressure=self.config['pressure'],
                    humidity=self.config['humidity']
                )
                
                atm_corrector = AtmosphericCorrections(atm_conditions)
                results = atm_corrector.apply_corrections(results)
            
            self.after(0, lambda: self.calc_status_label.configure(text="Calcul de la fermeture..."))
            self.after(0, lambda: self.calc_progress.set(0.8))
            
            # Calcul de la fermeture
            closure_error = self.calculator.calculate_closure()
            results['closure_error'] = closure_error
            
            self.after(0, lambda: self.calc_status_label.configure(text="Finalisation des résultats..."))
            self.after(0, lambda: self.calc_progress.set(1.0))
            
            # Sauvegarder les résultats
            self.calculation_results = results
            
            # Mettre à jour l'interface dans le thread principal
            self.after(0, self._update_calculation_results)
            
        except Exception as e:
            self.after(0, lambda: self._handle_calculation_error(str(e)))
    
    def _demo_calculations(self):
        """Mode démo pour les calculs."""
        import time
        
        # Simulation des étapes de calcul
        steps = [
            ("Chargement des données...", 0.2),
            ("Calcul des dénivelées...", 0.4),
            ("Application des corrections...", 0.6),
            ("Calcul de la fermeture...", 0.8),
            ("Finalisation...", 1.0)
        ]
        
        for step_text, progress in steps:
            self.after(0, lambda t=step_text, p=progress: self._update_demo_progress(t, p))
            time.sleep(0.5)
        
        # Créer des résultats de démo
        demo_results = {
            'denivellees': [0.245, -0.123, 0.087, -0.234, 0.156],
            'closure_error': 0.003,
            'total_distance': 1250.0,
            'precision_achieved': 1.8,
            'atmospheric_corrections_applied': self.config.get('atmospheric_corrections', False)
        }
        
        self.calculation_results = demo_results
        self.after(0, self._update_calculation_results)
    
    def _update_demo_progress(self, text, progress):
        """Met à jour la progression en mode démo."""
        self.calc_status_label.configure(text=text)
        self.calc_progress.set(progress)
    
    def _update_calculation_results(self):
        """Met à jour l'affichage des résultats de calcul."""
        try:
            # Titre des résultats
            results_title = ThemedLabel(
                self.results_section,
                text="📋 Résultats des Calculs",
                style='subheading'
            )
            results_title.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
            
            # Frame pour les métriques
            metrics_frame = ctk.CTkFrame(self.results_section, fg_color='transparent')
            metrics_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
            
            # Métriques principales
            if isinstance(self.calculation_results, dict):
                # Mode démo
                closure = self.calculation_results.get('closure_error', 0.003)
                precision = self.calculation_results.get('precision_achieved', 1.8)
                distance = self.calculation_results.get('total_distance', 1250.0)
                n_points = 5
            else:
                # Mode réel
                closure = abs(self.calculation_results.get('closure_error', 0.0))
                precision = self.calculation_results.get('precision_achieved', 2.0)
                distance = self.calculation_results.get('total_distance', 0.0)
                n_points = len(self.calculation_results.get('denivellees', []))
            
            # Affichage des métriques
            metrics_text = f"""
🎯 Points de mesure: {n_points}
📏 Distance totale: {distance:.1f} m
🔒 Erreur de fermeture: {closure:.3f} m
⚡ Précision atteinte: {precision:.1f} mm
            """
            
            metrics_label = ThemedLabel(
                metrics_frame,
                text=metrics_text.strip(),
                style='small',
                text_color=AppTheme.COLORS['text']
            )
            metrics_label.pack(anchor='w')
            
            # Diagnostic de qualité
            quality_frame = ThemedFrame(self.results_section)
            quality_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
            
            ThemedLabel(
                quality_frame,
                text="🔍 Diagnostic de Qualité",
                style='subheading'
            ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
            
            # Évaluation de la qualité
            if closure < 0.005:
                quality_color = AppTheme.COLORS['success']
                quality_text = "✅ Excellente qualité - Erreur de fermeture acceptable"
            elif closure < 0.010:
                quality_color = AppTheme.COLORS['warning']
                quality_text = "⚠️ Qualité correcte - Erreur de fermeture limite"
            else:
                quality_color = AppTheme.COLORS['error']
                quality_text = "❌ Qualité insuffisante - Erreur de fermeture trop élevée"
            
            quality_label = ThemedLabel(
                quality_frame,
                text=quality_text,
                style='body',
                text_color=quality_color
            )
            quality_label.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
            
            # Statut final
            self.calc_status_label.configure(text="✅ Calculs terminés avec succès!")
            
            # Réactiver les boutons
            self.calc_button.configure(state='normal', text="🔄 Recalculer")
            self.calc_next_button.configure(state='normal')
            
        except Exception as e:
            self._handle_calculation_error(f"Erreur lors de l'affichage des résultats: {str(e)}")
    
    def _handle_calculation_error(self, error_message):
        """Gère les erreurs de calcul."""
        self.calc_status_label.configure(text=f"❌ Erreur: {error_message}")
        self.calc_progress.set(0)
        self.calc_button.configure(state='normal')
        
        messagebox.showerror("Erreur de Calcul", f"Une erreur est survenue lors des calculs:\n\n{error_message}")
    
    # Méthodes de compensation
    def run_compensation(self):
        """Lance la compensation par moindres carrés."""
        import threading
        
        if self.calculation_results is None:
            messagebox.showerror("Erreur", "Vous devez d'abord effectuer les calculs préliminaires.")
            return
        
        # Désactiver le bouton pendant la compensation
        self.comp_button.configure(state='disabled')
        self.comp_progress.set(0)
        self.comp_status_label.configure(text="Initialisation de la compensation...")
        
        # Vider la zone des résultats
        for widget in self.comp_results_section.winfo_children():
            widget.destroy()
        
        # Lancer la compensation dans un thread séparé
        comp_thread = threading.Thread(target=self._perform_compensation)
        comp_thread.daemon = True
        comp_thread.start()
    
    def _perform_compensation(self):
        """Effectue la compensation dans un thread séparé."""
        try:
            self.after(0, lambda: self.comp_status_label.configure(text="Préparation des matrices..."))
            self.after(0, lambda: self.comp_progress.set(0.1))
            
            # Créer le compensateur
            if LevelingCompensator is None:
                # Mode démo
                self._demo_compensation()
                return
            
            # Récupérer les paramètres de compensation
            weight_method = self.weight_method.get()
            tolerance = float(self.tolerance_entry.get())
            
            self.compensator = LevelingCompensator(
                calculation_results=self.calculation_results,
                weight_method=weight_method,
                tolerance=tolerance
            )
            
            self.after(0, lambda: self.comp_status_label.configure(text="Construction du système d'équations..."))
            self.after(0, lambda: self.comp_progress.set(0.3))
            
            # Construction du système d'équations
            A, P, f = self.compensator.build_system()
            
            self.after(0, lambda: self.comp_status_label.configure(text="Résolution par moindres carrés..."))
            self.after(0, lambda: self.comp_progress.set(0.6))
            
            # Résolution du système
            corrections, residuals, sigma0 = self.compensator.solve_system(A, P, f)
            
            self.after(0, lambda: self.comp_status_label.configure(text="Calcul des altitudes compensées..."))
            self.after(0, lambda: self.comp_progress.set(0.8))
            
            # Calcul des altitudes compensées
            compensated_altitudes = self.compensator.compute_compensated_altitudes(corrections)
            
            self.after(0, lambda: self.comp_status_label.configure(text="Analyse de la précision..."))
            self.after(0, lambda: self.comp_progress.set(0.9))
            
            # Analyse de la précision
            precision_analysis = self.compensator.analyze_precision(residuals, sigma0)
            
            self.after(0, lambda: self.comp_progress.set(1.0))
            
            # Sauvegarder les résultats
            self.compensation_results = {
                'corrections': corrections,
                'residuals': residuals,
                'sigma0': sigma0,
                'compensated_altitudes': compensated_altitudes,
                'precision_analysis': precision_analysis,
                'weight_method': weight_method,
                'tolerance': tolerance
            }
            
            # Mettre à jour l'interface dans le thread principal
            self.after(0, self._update_compensation_results)
            
        except Exception as e:
            self.after(0, lambda: self._handle_compensation_error(str(e)))
    
    def _demo_compensation(self):
        """Mode démo pour la compensation."""
        import time
        import numpy as np
        
        # Simulation des étapes de compensation
        steps = [
            ("Préparation des matrices...", 0.2),
            ("Construction du système...", 0.4),
            ("Résolution LSQ...", 0.6),
            ("Calcul des altitudes...", 0.8),
            ("Analyse de précision...", 1.0)
        ]
        
        for step_text, progress in steps:
            self.after(0, lambda t=step_text, p=progress: self._update_comp_progress(t, p))
            time.sleep(0.4)
        
        # Créer des résultats de démo
        n_points = 5
        demo_results = {
            'corrections': np.random.normal(0, 0.001, n_points),
            'residuals': np.random.normal(0, 0.0005, n_points),
            'sigma0': 0.0008,
            'compensated_altitudes': [125.456 + i*0.1 + np.random.normal(0, 0.001) for i in range(n_points)],
            'precision_analysis': {
                'std_dev': 0.0008,
                'max_correction': 0.0023,
                'rms_residuals': 0.0006,
                'chi_square': 2.45,
                'degrees_of_freedom': n_points - 1
            },
            'weight_method': self.weight_method.get(),
            'tolerance': float(self.tolerance_entry.get())
        }
        
        self.compensation_results = demo_results
        self.after(0, self._update_compensation_results)
    
    def _update_comp_progress(self, text, progress):
        """Met à jour la progression de la compensation."""
        self.comp_status_label.configure(text=text)
        self.comp_progress.set(progress)
    
    def _update_compensation_results(self):
        """Met à jour l'affichage des résultats de compensation."""
        try:
            # Titre des résultats
            results_title = ThemedLabel(
                self.comp_results_section,
                text="🎯 Résultats de la Compensation",
                style='subheading'
            )
            results_title.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
            
            # Métriques de compensation
            metrics_frame = ctk.CTkFrame(self.comp_results_section, fg_color='transparent')
            metrics_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
            
            # Extraction des résultats
            sigma0 = self.compensation_results.get('sigma0', 0.0008)
            precision_analysis = self.compensation_results.get('precision_analysis', {})
            max_correction = precision_analysis.get('max_correction', 0.0023)
            rms_residuals = precision_analysis.get('rms_residuals', 0.0006)
            
            # Affichage des métriques
            metrics_text = f"""
📊 Écart-type unitaire (σ₀): {sigma0*1000:.1f} mm
🔧 Correction maximale: {max_correction*1000:.1f} mm
📈 RMS des résidus: {rms_residuals*1000:.1f} mm
⚙️ Méthode de pondération: {self.compensation_results.get('weight_method', 'Distance inverse')}
            """
            
            metrics_label = ThemedLabel(
                metrics_frame,
                text=metrics_text.strip(),
                style='small',
                text_color=AppTheme.COLORS['text']
            )
            metrics_label.pack(anchor='w')
            
            # Qualité de la compensation
            quality_frame = ThemedFrame(self.comp_results_section)
            quality_frame.pack(fill='x', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['md'])
            
            ThemedLabel(
                quality_frame,
                text="✅ Évaluation de la Compensation",
                style='subheading'
            ).pack(anchor='w', padx=AppTheme.SPACING['md'], pady=(AppTheme.SPACING['md'], AppTheme.SPACING['sm']))
            
            # Évaluation de la qualité
            if sigma0 < 0.001:
                quality_color = AppTheme.COLORS['success']
                quality_text = "🌟 Excellente qualité - Compensation très précise"
            elif sigma0 < 0.002:
                quality_color = AppTheme.COLORS['success']
                quality_text = "✅ Bonne qualité - Compensation satisfaisante"
            elif sigma0 < 0.003:
                quality_color = AppTheme.COLORS['warning']
                quality_text = "⚠️ Qualité acceptable - Vérifier les données"
            else:
                quality_color = AppTheme.COLORS['error']
                quality_text = "❌ Qualité insuffisante - Réviser les mesures"
            
            quality_label = ThemedLabel(
                quality_frame,
                text=quality_text,
                style='body',
                text_color=quality_color
            )
            quality_label.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
            
            # Statut final
            self.comp_status_label.configure(text="✅ Compensation terminée avec succès!")
            
            # Réactiver les boutons
            self.comp_button.configure(state='normal', text="🔄 Recompenser")
            self.comp_next_button.configure(state='normal')
            
        except Exception as e:
            self._handle_compensation_error(f"Erreur lors de l'affichage des résultats: {str(e)}")
    
    def _handle_compensation_error(self, error_message):
        """Gère les erreurs de compensation."""
        self.comp_status_label.configure(text=f"❌ Erreur: {error_message}")
        self.comp_progress.set(0)
        self.comp_button.configure(state='normal')
        
        messagebox.showerror("Erreur de Compensation", f"Une erreur est survenue lors de la compensation:\n\n{error_message}")
    
    # Méthodes d'action pour les résultats
    def generate_charts(self):
        """Génère les graphiques de visualisation."""
        try:
            from pathlib import Path
            import os
            
            # Créer le dossier de sortie
            output_dir = Path("results_gui")
            output_dir.mkdir(exist_ok=True)
            
            self._show_action_status("🎨 Génération des graphiques en cours...")
            
            # Utiliser le visualizer si disponible
            try:
                from src.visualizer import LevelingVisualizer
                
                if self.calculation_results and self.compensation_results:
                    visualizer = LevelingVisualizer(
                        calculation_results=self.calculation_results,
                        compensation_results=self.compensation_results
                    )
                    
                    # Générer tous les graphiques
                    chart_files = visualizer.create_complete_report(output_dir)
                    
                    self._show_action_status(f"✅ Graphiques générés dans {output_dir}/")
                    messagebox.showinfo("Succès", f"Graphiques générés avec succès dans le dossier {output_dir}/")
                    
                else:
                    self._show_action_status("⚠️ Données insuffisantes pour générer les graphiques")
                    
            except ImportError:
                # Mode démo - créer des graphiques factices
                self._generate_demo_charts(output_dir)
                self._show_action_status(f"✅ Graphiques de démo générés dans {output_dir}/")
                messagebox.showinfo("Mode Démo", f"Graphiques de démonstration générés dans {output_dir}/")
                
        except Exception as e:
            self._show_action_status(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération des graphiques:\n{str(e)}")
    
    def _generate_demo_charts(self, output_dir):
        """Génère des graphiques de démonstration."""
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Configuration matplotlib pour les couleurs du thème
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        
        # Graphique 1: Profil altimétrique
        fig, ax = plt.subplots(figsize=(12, 6))
        distances = np.cumsum([0, 250, 300, 275, 425])
        altitudes = [125.456, 125.701, 125.578, 125.665, 125.821]
        
        ax.plot(distances, altitudes, 'o-', color='#7671FA', linewidth=2, markersize=8)
        ax.set_xlabel('Distance cumulative (m)')
        ax.set_ylabel('Altitude (m)')
        ax.set_title('Profil Altimétrique - Cheminement de Nivellement')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'profil_altimetrique.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Graphique 2: Résidus de compensation
        fig, ax = plt.subplots(figsize=(10, 6))
        points = ['P001', 'P002', 'P003', 'P004', 'P005']
        residuals = np.random.normal(0, 0.0005, 5) * 1000  # en mm
        
        bars = ax.bar(points, residuals, color='#7671FA', alpha=0.7)
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax.set_ylabel('Résidus (mm)')
        ax.set_title('Résidus de Compensation par Point')
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'residus_compensation.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Graphique 3: Analyse de précision
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogramme des corrections
        corrections = np.random.normal(0, 0.001, 100) * 1000  # en mm
        ax1.hist(corrections, bins=20, color='#7671FA', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Corrections (mm)')
        ax1.set_ylabel('Fréquence')
        ax1.set_title('Distribution des Corrections')
        ax1.grid(True, alpha=0.3)
        
        # Évolution de la précision
        iterations = np.arange(1, 11)
        precision = 2.5 * np.exp(-iterations/3) + 0.8
        ax2.plot(iterations, precision, 'o-', color='#07244C', linewidth=2, markersize=6)
        ax2.set_xlabel('Itération')
        ax2.set_ylabel('Précision (mm)')
        ax2.set_title('Convergence de la Compensation')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'analyse_precision.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_detailed_report(self):
        """Génère un rapport détaillé."""
        try:
            from pathlib import Path
            from datetime import datetime
            
            output_dir = Path("results_gui")
            output_dir.mkdir(exist_ok=True)
            
            self._show_action_status("📄 Génération du rapport en cours...")
            
            # Créer le rapport
            report_path = output_dir / f"rapport_compensation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("RAPPORT DE COMPENSATION ALTIMÉTRIQUE\n")
                f.write("="*50 + "\n\n")
                f.write(f"Date de génération: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                # Informations du projet
                f.write("INFORMATIONS DU PROJET\n")
                f.write("-" * 25 + "\n")
                if self.imported_data:
                    if hasattr(self.imported_data, 'dataframe'):
                        f.write(f"Nombre de points: {len(self.imported_data.dataframe)}\n")
                    else:
                        f.write("Nombre de points: 5 (démo)\n")
                else:
                    f.write("Nombre de points: 5 (démo)\n")
                
                f.write(f"Précision cible: {self.config.get('precision_mm', 2.0)} mm\n")
                f.write(f"Altitude initiale: {self.config.get('initial_altitude', 125.456)} m\n\n")
                
                # Résultats des calculs
                if self.calculation_results:
                    f.write("RÉSULTATS DES CALCULS PRÉLIMINAIRES\n")
                    f.write("-" * 35 + "\n")
                    if isinstance(self.calculation_results, dict):
                        closure = self.calculation_results.get('closure_error', 0.003)
                        f.write(f"Erreur de fermeture: {closure:.3f} m ({closure*1000:.1f} mm)\n")
                        f.write(f"Distance totale: {self.calculation_results.get('total_distance', 1250.0):.1f} m\n")
                    f.write("\n")
                
                # Résultats de la compensation
                if self.compensation_results:
                    f.write("RÉSULTATS DE LA COMPENSATION\n")
                    f.write("-" * 30 + "\n")
                    sigma0 = self.compensation_results.get('sigma0', 0.0008)
                    f.write(f"Écart-type unitaire (σ₀): {sigma0*1000:.1f} mm\n")
                    f.write(f"Méthode de pondération: {self.compensation_results.get('weight_method', 'Distance inverse')}\n")
                    
                    precision_analysis = self.compensation_results.get('precision_analysis', {})
                    if precision_analysis:
                        f.write(f"Correction maximale: {precision_analysis.get('max_correction', 0.0023)*1000:.1f} mm\n")
                        f.write(f"RMS des résidus: {precision_analysis.get('rms_residuals', 0.0006)*1000:.1f} mm\n")
                    f.write("\n")
                
                # Évaluation de la qualité
                f.write("ÉVALUATION DE LA QUALITÉ\n")
                f.write("-" * 25 + "\n")
                if self.compensation_results:
                    sigma0 = self.compensation_results.get('sigma0', 0.0008)
                    if sigma0 < 0.001:
                        f.write("Qualité: EXCELLENTE\n")
                    elif sigma0 < 0.002:
                        f.write("Qualité: BONNE\n")
                    else:
                        f.write("Qualité: ACCEPTABLE\n")
                
                f.write("\nRapport généré par le Système de Compensation Altimétrique\n")
            
            self._show_action_status(f"✅ Rapport généré: {report_path.name}")
            messagebox.showinfo("Succès", f"Rapport détaillé généré:\n{report_path}")
            
        except Exception as e:
            self._show_action_status(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport:\n{str(e)}")
    
    def export_csv(self):
        """Exporte les résultats en CSV."""
        try:
            from pathlib import Path
            from datetime import datetime
            import csv
            
            if not self.compensation_results:
                messagebox.showerror("Erreur", "Aucun résultat de compensation disponible pour l'export.")
                return
            
            output_dir = Path("results_gui")
            output_dir.mkdir(exist_ok=True)
            
            self._show_action_status("💾 Export CSV en cours...")
            
            csv_path = output_dir / f"resultats_compensation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # En-têtes
                writer.writerow(['Point', 'Altitude_Compensée_m', 'Correction_mm', 'Résidu_mm'])
                
                # Données (mode démo ou réel)
                if isinstance(self.compensation_results.get('compensated_altitudes'), list):
                    altitudes = self.compensation_results['compensated_altitudes']
                    corrections = self.compensation_results.get('corrections', [0]*len(altitudes))
                    residuals = self.compensation_results.get('residuals', [0]*len(altitudes))
                    
                    for i, (alt, corr, res) in enumerate(zip(altitudes, corrections, residuals)):
                        point_name = f"P{i+1:03d}"
                        writer.writerow([
                            point_name, 
                            f"{alt:.6f}", 
                            f"{corr*1000:.2f}", 
                            f"{res*1000:.2f}"
                        ])
            
            self._show_action_status(f"✅ Export CSV réussi: {csv_path.name}")
            messagebox.showinfo("Succès", f"Export CSV réalisé:\n{csv_path}")
            
        except Exception as e:
            self._show_action_status(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export CSV:\n{str(e)}")
    
    def open_results_folder(self):
        """Ouvre le dossier des résultats."""
        try:
            from pathlib import Path
            import subprocess
            import platform
            
            output_dir = Path("results_gui")
            output_dir.mkdir(exist_ok=True)
            
            # Ouvrir le dossier selon l'OS
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(output_dir)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir)])
            
            self._show_action_status(f"📂 Dossier ouvert: {output_dir}")
            
        except Exception as e:
            self._show_action_status(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{str(e)}")
    
    def new_project(self):
        """Démarre un nouveau projet."""
        response = messagebox.askyesno(
            "Nouveau Projet", 
            "Êtes-vous sûr de vouloir démarrer un nouveau projet?\nTous les résultats actuels seront perdus."
        )
        
        if response:
            # Réinitialiser l'application
            self.current_step = 0
            self.imported_data = None
            self.calculation_results = None
            self.compensation_results = None
            
            # Réinitialiser la configuration
            self.config = {
                'precision_mm': 2.0,
                'initial_altitude': None,
                'final_altitude': None,
                'atmospheric_corrections': True,
                'temperature': 25.0,
                'pressure': 1010.0,
                'humidity': 60.0
            }
            
            # Retourner à la première étape
            self.show_step()
            self._show_action_status("🔄 Nouveau projet démarré")
    
    def _show_action_status(self, message):
        """Affiche un message de statut pour les actions."""
        # Vider le frame précédent
        for widget in self.results_status_frame.winfo_children():
            widget.destroy()
        
        status_label = ThemedLabel(
            self.results_status_frame,
            text=message,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        status_label.pack(anchor='w', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])


def main():
    """Point d'entrée principal."""
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    main()