"""
Mode comparaison de résultats pour le Système de Compensation Altimétrique.
Interface avancée pour comparer plusieurs projets, méthodes et configurations.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from .base_components import ThemedButton, ThemedLabel, ThemedFrame, StatusCard, ProjectCard
from .advanced_visualizations import AdvancedVisualizationPanel
from ..utils.theme import AppTheme


class ComparisonProject:
    """Classe pour représenter un projet dans la comparaison."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.id = data.get('id', '')
        self.name = data.get('name', 'Projet sans nom')
        self.precision = data.get('precision_achieved', 0.0)
        self.points_count = data.get('points_count', 0)
        self.closure_error = data.get('closure_error', 0.0)
        self.processing_time = data.get('processing_time_minutes', 0.0)
        self.status = data.get('status', 'unknown')
        
        # Générer des données simulées pour la démonstration
        self.generate_demo_data()
    
    def generate_demo_data(self):
        """Génère des données de démonstration pour les graphiques."""
        np.random.seed(hash(self.id) % 2**32)
        
        # Profil altimétrique
        n_points = self.points_count or 20
        self.distances = np.cumsum(np.random.uniform(80, 300, n_points))
        self.distances = np.insert(self.distances, 0, 0)  # Commencer à 0
        
        # Altitudes avec tendance
        base_altitude = 125.0 + np.random.uniform(-10, 10)
        trend = np.random.uniform(-0.001, 0.001)
        self.altitudes = (base_altitude + trend * self.distances + 
                         np.random.normal(0, 0.01, len(self.distances)))
        
        # Résidus et corrections
        self.residuals = np.random.normal(0, self.precision/1000 if self.precision else 0.002, n_points)
        self.corrections = np.random.normal(0, 0.001, n_points)
        
        # Statistiques LSQ
        self.sigma0 = self.precision/1000 if self.precision else np.random.uniform(0.0008, 0.003)
        self.chi_square = np.random.uniform(0.5, 2.5)
        self.dof = max(1, n_points - 3)


class ProjectSelector(ThemedFrame):
    """Sélecteur de projets pour la comparaison."""
    
    def __init__(self, parent, available_projects: List[Dict], callback=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.available_projects = available_projects
        self.selected_projects = []
        self.callback = callback
        self.max_projects = 4  # Limite pour la lisibilité
        
        self.create_selector_interface()
    
    def create_selector_interface(self):
        """Crée l'interface de sélection."""
        
        # En-tête
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = ThemedLabel(
            header_frame,
            text="🔍 Sélection de Projets à Comparer",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        info_label = ThemedLabel(
            header_frame,
            text=f"Maximum {self.max_projects} projets",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        info_label.pack(side='right')
        
        # Zone de sélection avec scroll
        selection_frame = ctk.CTkScrollableFrame(
            self,
            height=300,
            scrollbar_button_color=AppTheme.COLORS['primary']
        )
        selection_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        # Créer les checkboxes pour chaque projet
        self.project_checkboxes = {}
        for project in self.available_projects:
            self.create_project_checkbox(selection_frame, project)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(self, fg_color='transparent')
        actions_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Sélectionner tout / Aucun
        select_all_btn = ThemedButton(
            actions_frame,
            text="Tout sélectionner",
            command=self.select_all,
            variant='ghost',
            size='small'
        )
        select_all_btn.pack(side='left')
        
        select_none_btn = ThemedButton(
            actions_frame,
            text="Aucune sélection",
            command=self.select_none,
            variant='ghost',
            size='small'
        )
        select_none_btn.pack(side='left', padx=(10, 0))
        
        # Bouton comparer
        self.compare_button = ThemedButton(
            actions_frame,
            text="📊 Comparer les Projets",
            command=self.start_comparison,
            variant='primary'
        )
        self.compare_button.pack(side='right')
        self.compare_button.configure(state='disabled')
    
    def create_project_checkbox(self, parent, project):
        """Crée un checkbox pour un projet."""
        
        project_frame = ThemedFrame(parent, elevated=False)
        project_frame.pack(fill='x', pady=5)
        
        # Container principal
        content_frame = ctk.CTkFrame(project_frame, fg_color='transparent')
        content_frame.pack(fill='x', padx=15, pady=10)
        
        # Checkbox
        checkbox_var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            content_frame,
            text="",
            variable=checkbox_var,
            command=lambda: self.on_selection_changed(project['id'], checkbox_var.get()),
            font=AppTheme.FONTS['body'],
            fg_color=AppTheme.COLORS['primary'],
            hover_color=AppTheme.COLORS['primary_dark']
        )
        checkbox.pack(side='left', padx=(0, 15))
        
        # Informations du projet
        info_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        info_frame.pack(side='left', fill='x', expand=True)
        
        # Nom et statut
        header_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
        header_frame.pack(fill='x')
        
        name_label = ThemedLabel(
            header_frame,
            text=project.get('name', 'Projet sans nom'),
            style='body_medium',
            text_color=AppTheme.COLORS['text']
        )
        name_label.pack(side='left')
        
        # Badge de statut
        status = project.get('status', 'unknown')
        status_colors = {
            'completed': AppTheme.COLORS['success'],
            'in_progress': AppTheme.COLORS['warning'],
            'draft': AppTheme.COLORS['text_muted']
        }
        
        if status in status_colors:
            status_badge = ctk.CTkFrame(
                header_frame,
                fg_color=status_colors[status],
                corner_radius=10,
                height=20
            )
            status_badge.pack(side='right')
            
            status_text = {'completed': 'Terminé', 'in_progress': 'En cours', 'draft': 'Brouillon'}
            status_label = ThemedLabel(
                status_badge,
                text=status_text.get(status, status),
                style='caption',
                text_color='white'
            )
            status_label.pack(padx=8, pady=2)
        
        # Métriques du projet
        metrics_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
        metrics_frame.pack(fill='x', pady=(5, 0))
        
        # Points et précision
        points_text = f"📍 {project.get('points_count', 0)} points"
        precision = project.get('precision_achieved')
        if precision:
            precision_text = f" • 🎯 {precision:.1f}mm"
        else:
            precision_text = " • 🎯 Non calculé"
        
        metrics_label = ThemedLabel(
            metrics_frame,
            text=points_text + precision_text,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        metrics_label.pack(side='left')
        
        # Stocker la référence
        self.project_checkboxes[project['id']] = {
            'checkbox': checkbox,
            'variable': checkbox_var,
            'project': project
        }
    
    def on_selection_changed(self, project_id: str, is_selected: bool):
        """Gère le changement de sélection."""
        
        if is_selected:
            if len(self.selected_projects) >= self.max_projects:
                # Désélectionner si limite atteinte
                checkbox_info = self.project_checkboxes[project_id]
                checkbox_info['variable'].set(False)
                messagebox.showwarning(
                    "Limite atteinte", 
                    f"Vous ne pouvez comparer que {self.max_projects} projets maximum."
                )
                return
            
            self.selected_projects.append(project_id)
        else:
            if project_id in self.selected_projects:
                self.selected_projects.remove(project_id)
        
        # Mettre à jour l'état du bouton comparer
        self.compare_button.configure(
            state='normal' if len(self.selected_projects) >= 2 else 'disabled'
        )
    
    def select_all(self):
        """Sélectionne tous les projets (dans la limite)."""
        count = 0
        for project_id, checkbox_info in self.project_checkboxes.items():
            if count < self.max_projects and not checkbox_info['variable'].get():
                checkbox_info['variable'].set(True)
                self.selected_projects.append(project_id)
                count += 1
        
        self.compare_button.configure(
            state='normal' if len(self.selected_projects) >= 2 else 'disabled'
        )
    
    def select_none(self):
        """Désélectionne tous les projets."""
        for checkbox_info in self.project_checkboxes.values():
            checkbox_info['variable'].set(False)
        
        self.selected_projects.clear()
        self.compare_button.configure(state='disabled')
    
    def start_comparison(self):
        """Lance la comparaison."""
        if self.callback and len(self.selected_projects) >= 2:
            selected_project_data = [
                self.project_checkboxes[pid]['project'] 
                for pid in self.selected_projects
            ]
            self.callback(selected_project_data)


class ComparisonVisualization(ThemedFrame):
    """Panel de visualisation des comparaisons."""
    
    def __init__(self, parent, projects: List[ComparisonProject], **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.projects = projects
        self.fig = None
        self.canvas = None
        
        # Couleurs distinctes pour chaque projet
        self.project_colors = [
            AppTheme.COLORS['primary'],
            AppTheme.COLORS['secondary'],
            AppTheme.COLORS['accent'],
            AppTheme.COLORS['success']
        ][:len(projects)]
        
        self.create_comparison_interface()
    
    def create_comparison_interface(self):
        """Crée l'interface de comparaison."""
        
        # En-tête avec contrôles
        self.create_comparison_header()
        
        # Zone de visualisation
        self.create_comparison_visualization()
        
        # Panneau de métriques comparatives
        self.create_comparison_metrics()
    
    def create_comparison_header(self):
        """Crée l'en-tête de comparaison."""
        
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Titre
        title_label = ThemedLabel(
            header_frame,
            text=f"⚖️ Comparaison de {len(self.projects)} Projets",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Contrôles
        controls_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        controls_frame.pack(side='right')
        
        # Sélecteur de type de comparaison
        self.comparison_type = ctk.StringVar(value="Profils Altimetriques")
        type_selector = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.comparison_type,
            values=[
                "Profils Altimetriques",
                "Précisions Atteintes", 
                "Erreurs de Fermeture",
                "Statistiques LSQ",
                "Temps de Traitement",
                "Analyse Résidus",
                "Tableau Comparatif"
            ],
            command=self.on_comparison_type_changed,
            font=AppTheme.FONTS['body'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        type_selector.pack(side='left', padx=(0, 10))
        
        # Bouton export
        export_btn = ThemedButton(
            controls_frame,
            text="💾 Exporter",
            command=self.export_comparison,
            variant='primary',
            size='small'
        )
        export_btn.pack(side='left')
    
    def create_comparison_visualization(self):
        """Crée la zone de visualisation comparative."""
        
        viz_frame = ctk.CTkFrame(self, fg_color=AppTheme.COLORS['surface'])
        viz_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.matplotlib_frame = ctk.CTkFrame(viz_frame, fg_color='transparent')
        self.matplotlib_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Créer le premier graphique
        self.create_altitude_profiles_comparison()
    
    def create_comparison_metrics(self):
        """Crée le panneau de métriques comparatives."""
        
        metrics_frame = ctk.CTkFrame(self, fg_color='transparent')
        metrics_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Titre
        metrics_title = ThemedLabel(
            metrics_frame,
            text="📊 Métriques Comparatives",
            style='subheading',
            text_color=AppTheme.COLORS['secondary']
        )
        metrics_title.pack(anchor='w', pady=(0, 10))
        
        # Grille de métriques
        grid_frame = ctk.CTkFrame(metrics_frame, fg_color='transparent')
        grid_frame.pack(fill='x')
        grid_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Calculer les métriques
        self.calculate_comparative_metrics(grid_frame)
    
    def calculate_comparative_metrics(self, parent):
        """Calcule et affiche les métriques comparatives."""
        
        # Meilleure précision
        best_precision = min(p.precision for p in self.projects if p.precision > 0)
        best_project = next(p for p in self.projects if p.precision == best_precision)
        
        precision_metric = StatusCard(
            parent,
            title="Meilleure Précision",
            value=f"{best_precision:.1f}mm",
            icon="🏆",
            color=AppTheme.COLORS['success']
        )
        precision_metric.grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        # Plus grand projet
        largest_project = max(self.projects, key=lambda p: p.points_count)
        points_metric = StatusCard(
            parent,
            title="Plus Grand Projet",
            value=f"{largest_project.points_count} pts",
            icon="📏",
            color=AppTheme.COLORS['primary']
        )
        points_metric.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Écart-type moyen
        avg_sigma = np.mean([p.sigma0 for p in self.projects]) * 1000
        sigma_metric = StatusCard(
            parent,
            title="σ₀ Moyen",
            value=f"{avg_sigma:.2f}mm",
            icon="📐",
            color=AppTheme.COLORS['secondary']
        )
        sigma_metric.grid(row=0, column=2, padx=5, sticky='ew')
        
        # Projets comparés
        count_metric = StatusCard(
            parent,
            title="Projets Comparés",
            value=str(len(self.projects)),
            icon="⚖️",
            color=AppTheme.COLORS['accent']
        )
        count_metric.grid(row=0, column=3, padx=(10, 0), sticky='ew')
        
        # Détails des projets sous les métriques
        details_frame = ctk.CTkFrame(parent, fg_color='transparent')
        details_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=(15, 0))
        
        details_text = "Projets comparés : "
        for i, project in enumerate(self.projects):
            color_indicator = "●"
            details_text += f"{color_indicator} {project.name}"
            if i < len(self.projects) - 1:
                details_text += " • "
        
        details_label = ThemedLabel(
            details_frame,
            text=details_text,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        details_label.pack()
    
    def create_altitude_profiles_comparison(self):
        """Crée la comparaison des profils altimetriques."""
        
        self.clear_canvas()
        
        self.fig = Figure(figsize=(12, 8), dpi=100, facecolor=AppTheme.COLORS['background'])
        ax = self.fig.add_subplot(111)
        
        # Tracer chaque projet avec une couleur différente
        for i, project in enumerate(self.projects):
            color = self.project_colors[i]
            
            # Normaliser les distances pour la comparaison
            distances_norm = project.distances / project.distances[-1] * 100  # En pourcentage
            
            ax.plot(distances_norm, project.altitudes, 
                   'o-', color=color, linewidth=2, markersize=6, 
                   label=f"{project.name} ({project.precision:.1f}mm)",
                   alpha=0.8)
        
        # Configuration
        ax.set_xlabel('Distance relative (%)')
        ax.set_ylabel('Altitude (m)')
        ax.set_title('⚖️ Comparaison des Profils Altimetriques\nNormalisation par distance totale', 
                    fontsize=14, pad=20)
        
        # Légende améliorée
        legend = ax.legend(loc='upper right', fancybox=True, shadow=True, 
                          frameon=True, facecolor='white', 
                          edgecolor=AppTheme.COLORS['border'])
        legend.get_frame().set_alpha(0.9)
        
        # Grille et style
        ax.grid(True, alpha=0.3, color=AppTheme.COLORS['border_light'])
        ax.set_axisbelow(True)
        
        self.integrate_canvas()
    
    def create_precision_comparison(self):
        """Crée la comparaison des précisions."""
        
        self.clear_canvas()
        
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor=AppTheme.COLORS['background'])
        ax = self.fig.add_subplot(111)
        
        # Données
        project_names = [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in self.projects]
        precisions = [p.precision for p in self.projects]
        
        # Barres colorées
        bars = ax.bar(project_names, precisions, color=self.project_colors, alpha=0.8)
        
        # Ligne de référence 2mm
        ax.axhline(y=2.0, color=AppTheme.COLORS['success'], 
                  linestyle='--', linewidth=2, label='Objectif 2mm')
        
        # Annotations sur les barres
        for bar, precision in zip(bars, precisions):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                   f'{precision:.1f}mm', ha='center', va='bottom', fontweight='bold')
        
        # Configuration
        ax.set_ylabel('Précision atteinte (mm)')
        ax.set_title('🎯 Comparaison des Précisions Atteintes', fontsize=14, pad=20)
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        self.integrate_canvas()
    
    def create_closure_errors_comparison(self):
        """Crée la comparaison des erreurs de fermeture."""
        
        self.clear_canvas()
        
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor=AppTheme.COLORS['background'])
        ax = self.fig.add_subplot(111)
        
        # Données
        project_names = [p.name[:15] for p in self.projects]
        closure_errors = [(p.closure_error or 0) * 1000 for p in self.projects]  # En mm
        
        # Graphique en barres horizontales
        bars = ax.barh(project_names, closure_errors, color=self.project_colors, alpha=0.8)
        
        # Ligne de tolérance
        max_error = max(closure_errors) if closure_errors else 5
        tolerance = max_error * 0.8
        ax.axvline(x=tolerance, color=AppTheme.COLORS['warning'], 
                  linestyle='--', linewidth=2, label=f'Tolérance {tolerance:.1f}mm')
        
        # Annotations
        for bar, error in zip(bars, closure_errors):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{error:.1f}mm', ha='left', va='center')
        
        ax.set_xlabel('Erreur de fermeture (mm)')
        ax.set_title('🔒 Comparaison des Erreurs de Fermeture', fontsize=14, pad=20)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='x')
        
        self.integrate_canvas()
    
    def clear_canvas(self):
        """Nettoie le canvas."""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
    
    def integrate_canvas(self):
        """Intègre le canvas matplotlib."""
        self.canvas = FigureCanvasTkAgg(self.fig, self.matplotlib_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def on_comparison_type_changed(self, selection):
        """Gère le changement de type de comparaison."""
        
        comparison_methods = {
            "Profils Altimetriques": self.create_altitude_profiles_comparison,
            "Précisions Atteintes": self.create_precision_comparison,
            "Erreurs de Fermeture": self.create_closure_errors_comparison,
            "Statistiques LSQ": self.create_lsq_stats_comparison,
            "Temps de Traitement": self.create_timing_comparison,
            "Analyse Résidus": self.create_residuals_analysis,
            "Tableau Comparatif": self.create_comparative_table
        }
        
        method = comparison_methods.get(selection)
        if method:
            method()
        else:
            messagebox.showinfo("Info", f"Comparaison '{selection}' en cours de développement")
    
    def create_lsq_stats_comparison(self):
        """Comparaison des statistiques LSQ."""
        messagebox.showinfo("Développement", "Statistiques LSQ - En cours d'implémentation")
    
    def create_timing_comparison(self):
        """Comparaison des temps de traitement."""
        messagebox.showinfo("Développement", "Temps de traitement - En cours d'implémentation")
    
    def create_residuals_analysis(self):
        """Analyse comparative des résidus."""
        messagebox.showinfo("Développement", "Analyse résidus - En cours d'implémentation")
    
    def create_comparative_table(self):
        """Tableau comparatif détaillé."""
        messagebox.showinfo("Développement", "Tableau comparatif - En cours d'implémentation")
    
    def export_comparison(self):
        """Exporte la comparaison."""
        if self.fig:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ]
            )
            if filepath:
                self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export", f"Comparaison exportée vers :\n{filepath}")


class ComparisonModeWindow(ctk.CTkToplevel):
    """Fenêtre principale du mode comparaison."""
    
    def __init__(self, parent, available_projects: List[Dict]):
        super().__init__(parent)
        
        self.available_projects = available_projects
        self.selected_projects = []
        self.comparison_projects = []
        
        # Configuration fenêtre
        self.title("⚖️ Mode Comparaison - Système de Compensation Altimétrique")
        self.geometry("1600x1000")
        self.minsize(1400, 900)
        
        self.configure(fg_color=AppTheme.COLORS['background'])
        self.center_window()
        
        # Créer l'interface
        self.create_interface()
    
    def center_window(self):
        """Centre la fenêtre."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - 1600) // 2
        y = (screen_height - 1000) // 2
        
        self.geometry(f"1600x1000+{x}+{y}")
    
    def create_interface(self):
        """Crée l'interface principale."""
        
        # Conteneur principal avec sections
        main_container = ctk.CTkFrame(self, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        main_container.grid_columnconfigure(1, weight=2)  # Zone de visualisation plus large
        main_container.grid_rowconfigure(0, weight=1)
        
        # Zone de sélection (gauche)
        self.selector = ProjectSelector(
            main_container,
            available_projects=self.available_projects,
            callback=self.start_comparison
        )
        self.selector.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Zone de visualisation (droite) - initialement vide
        self.visualization_frame = ctk.CTkFrame(
            main_container, 
            fg_color=AppTheme.COLORS['surface']
        )
        self.visualization_frame.grid(row=0, column=1, sticky='nsew')
        
        # Message initial
        self.show_initial_message()
    
    def show_initial_message(self):
        """Affiche le message initial."""
        
        initial_frame = ctk.CTkFrame(self.visualization_frame, fg_color='transparent')
        initial_frame.pack(expand=True, fill='both')
        
        # Illustration
        icon_label = ThemedLabel(
            initial_frame,
            text="⚖️",
            style='display',
            text_color=AppTheme.COLORS['text_secondary']
        )
        icon_label.pack(pady=(100, 20))
        
        # Titre
        title_label = ThemedLabel(
            initial_frame,
            text="Mode Comparaison Avancé",
            style='title',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = [
            "1. Sélectionnez 2 à 4 projets à comparer",
            "2. Cliquez sur 'Comparer les Projets'",
            "3. Analysez les visualisations comparatives",
            "4. Exportez vos résultats"
        ]
        
        for instruction in instructions:
            instr_label = ThemedLabel(
                initial_frame,
                text=instruction,
                style='body',
                text_color=AppTheme.COLORS['text_secondary']
            )
            instr_label.pack(pady=2)
    
    def start_comparison(self, selected_project_data: List[Dict]):
        """Lance la comparaison avec les projets sélectionnés."""
        
        # Convertir en objets ComparisonProject
        self.comparison_projects = [
            ComparisonProject(project_data) 
            for project_data in selected_project_data
        ]
        
        # Nettoyer la zone de visualisation
        for widget in self.visualization_frame.winfo_children():
            widget.destroy()
        
        # Créer la visualisation comparative
        self.comparison_viz = ComparisonVisualization(
            self.visualization_frame,
            projects=self.comparison_projects
        )
        self.comparison_viz.pack(fill='both', expand=True)