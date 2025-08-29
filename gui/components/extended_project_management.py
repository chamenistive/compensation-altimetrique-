"""
Gestion étendue de projets pour le Dashboard avancé.
Interface complète de CRUD, recherche, filtrage et archivage de projets.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import os

from .base_components import (
    ThemedButton, ThemedLabel, ThemedFrame, ThemedEntry,
    StatusCard, ProjectCard, NotificationBanner
)
from .advanced_visualizations import InteractiveVisualizationWindow
from .comparison_mode import ComparisonModeWindow
from ..utils.theme import AppTheme


class ProjectSearchFilter(ThemedFrame):
    """Composant de recherche et filtrage des projets."""
    
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.callback = callback
        self.filters = {
            'search_text': '',
            'status': 'all',
            'precision_range': 'all',
            'date_range': 'all',
            'points_range': 'all'
        }
        
        self.create_search_interface()
    
    def create_search_interface(self):
        """Crée l'interface de recherche et filtrage."""
        
        # En-tête
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 15))
        
        title_label = ThemedLabel(
            header_frame,
            text="🔍 Recherche & Filtres",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Bouton reset filtres
        reset_button = ThemedButton(
            header_frame,
            text="🔄 Reset",
            command=self.reset_filters,
            variant='ghost',
            size='small'
        )
        reset_button.pack(side='right')
        
        # Zone de recherche textuelle
        search_frame = ctk.CTkFrame(self, fg_color='transparent')
        search_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        search_label = ThemedLabel(
            search_frame,
            text="Rechercher:",
            style='body',
            text_color=AppTheme.COLORS['text']
        )
        search_label.pack(side='left', padx=(0, 10))
        
        self.search_entry = ThemedEntry(
            search_frame,
            placeholder="Nom de projet, description..."
        )
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        search_button = ThemedButton(
            search_frame,
            text="🔍",
            command=self.apply_filters,
            variant='primary',
            size='small',
            width=40
        )
        search_button.pack(side='right')
        
        # Filtres avancés
        filters_frame = ctk.CTkFrame(self, fg_color='transparent')
        filters_frame.pack(fill='x', padx=20, pady=(0, 20))
        filters_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Filtre par statut
        status_frame = ctk.CTkFrame(filters_frame, fg_color='transparent')
        status_frame.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ThemedLabel(status_frame, text="Statut:", style='small').pack()
        self.status_filter = ctk.CTkOptionMenu(
            status_frame,
            values=["Tous", "Terminé", "En cours", "Brouillon"],
            command=self.on_filter_changed,
            font=AppTheme.FONTS['small'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        self.status_filter.pack(fill='x')
        
        # Filtre par précision
        precision_frame = ctk.CTkFrame(filters_frame, fg_color='transparent')
        precision_frame.grid(row=0, column=1, sticky='ew', padx=5)
        
        ThemedLabel(precision_frame, text="Précision:", style='small').pack()
        self.precision_filter = ctk.CTkOptionMenu(
            precision_frame,
            values=["Toutes", "< 1.5mm", "1.5-2.5mm", "> 2.5mm"],
            command=self.on_filter_changed,
            font=AppTheme.FONTS['small'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        self.precision_filter.pack(fill='x')
        
        # Filtre par date
        date_frame = ctk.CTkFrame(filters_frame, fg_color='transparent')
        date_frame.grid(row=0, column=2, sticky='ew', padx=5)
        
        ThemedLabel(date_frame, text="Période:", style='small').pack()
        self.date_filter = ctk.CTkOptionMenu(
            date_frame,
            values=["Toutes", "Aujourd'hui", "Cette semaine", "Ce mois"],
            command=self.on_filter_changed,
            font=AppTheme.FONTS['small'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        self.date_filter.pack(fill='x')
        
        # Filtre par taille
        points_frame = ctk.CTkFrame(filters_frame, fg_color='transparent')
        points_frame.grid(row=0, column=3, sticky='ew', padx=(10, 0))
        
        ThemedLabel(points_frame, text="Taille:", style='small').pack()
        self.points_filter = ctk.CTkOptionMenu(
            points_frame,
            values=["Toutes", "< 20 pts", "20-50 pts", "> 50 pts"],
            command=self.on_filter_changed,
            font=AppTheme.FONTS['small'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        self.points_filter.pack(fill='x')
    
    def on_search_changed(self, event):
        """Gère le changement de texte de recherche."""
        self.filters['search_text'] = self.search_entry.get().lower()
        # Appliquer avec un délai pour éviter trop d'appels
        self.after(300, self.apply_filters)
    
    def on_filter_changed(self, value):
        """Gère le changement des filtres."""
        # Mettre à jour les filtres
        self.filters['status'] = self.status_filter.get().lower()
        self.filters['precision_range'] = self.precision_filter.get()
        self.filters['date_range'] = self.date_filter.get()
        self.filters['points_range'] = self.points_filter.get()
        
        self.apply_filters()
    
    def apply_filters(self):
        """Applique les filtres et notifie le callback."""
        if self.callback:
            self.callback(self.filters)
    
    def reset_filters(self):
        """Remet les filtres par défaut."""
        self.search_entry.delete(0, 'end')
        self.status_filter.set("Tous")
        self.precision_filter.set("Toutes")
        self.date_filter.set("Toutes")
        self.points_filter.set("Toutes")
        
        self.filters = {
            'search_text': '',
            'status': 'tous',
            'precision_range': 'toutes',
            'date_range': 'toutes',
            'points_range': 'toutes'
        }
        
        self.apply_filters()


class ProjectDetails(ThemedFrame):
    """Panneau détaillé d'un projet avec actions avancées."""
    
    def __init__(self, parent, project_data: Dict, callback=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.project_data = project_data
        self.callback = callback
        
        self.create_details_interface()
    
    def create_details_interface(self):
        """Crée l'interface détaillée du projet."""
        
        # En-tête avec nom et statut
        self.create_project_header()
        
        # Informations détaillées
        self.create_project_info()
        
        # Métriques et statistiques
        self.create_project_metrics()
        
        # Actions avancées
        self.create_advanced_actions()
    
    def create_project_header(self):
        """Crée l'en-tête du projet."""
        
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 15))
        
        # Nom et icône
        name_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        name_frame.pack(side='left', fill='x', expand=True)
        
        # Icône selon le type de projet
        project_icon = self.get_project_icon()
        icon_label = ThemedLabel(
            name_frame,
            text=project_icon,
            style='title',
            text_color=AppTheme.COLORS['primary']
        )
        icon_label.pack(side='left', padx=(0, 15))
        
        # Nom et description
        info_frame = ctk.CTkFrame(name_frame, fg_color='transparent')
        info_frame.pack(side='left', fill='x', expand=True)
        
        name_label = ThemedLabel(
            info_frame,
            text=self.project_data.get('name', 'Projet sans nom'),
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        name_label.pack(anchor='w')
        
        if self.project_data.get('description'):
            desc_label = ThemedLabel(
                info_frame,
                text=self.project_data['description'],
                style='body',
                text_color=AppTheme.COLORS['text_secondary']
            )
            desc_label.pack(anchor='w', pady=(5, 0))
        
        # Badge de statut
        self.create_status_badge(header_frame)
    
    def get_project_icon(self) -> str:
        """Détermine l'icône du projet selon son type/nom."""
        name = self.project_data.get('name', '').lower()
        
        if any(word in name for word in ['autoroute', 'route', 'voie']):
            return '🛣️'
        elif any(word in name for word in ['tgv', 'train', 'rail', 'ligne']):
            return '🚄'
        elif any(word in name for word in ['campus', 'université', 'école']):
            return '🏫'
        elif any(word in name for word in ['port', 'maritime', 'quai']):
            return '⚓'
        elif any(word in name for word in ['zone', 'industriel', 'usine']):
            return '🏭'
        else:
            return '📍'
    
    def create_status_badge(self, parent):
        """Crée le badge de statut."""
        
        status = self.project_data.get('status', 'unknown')
        status_colors = {
            'completed': AppTheme.COLORS['success'],
            'in_progress': AppTheme.COLORS['warning'],
            'draft': AppTheme.COLORS['text_muted']
        }
        status_texts = {
            'completed': '✅ Terminé',
            'in_progress': '🔄 En cours', 
            'draft': '📝 Brouillon'
        }
        
        if status in status_colors:
            badge_frame = ctk.CTkFrame(
                parent,
                fg_color=status_colors[status],
                corner_radius=15
            )
            badge_frame.pack(side='right')
            
            badge_label = ThemedLabel(
                badge_frame,
                text=status_texts[status],
                style='body',
                text_color='white'
            )
            badge_label.pack(padx=15, pady=8)
    
    def create_project_info(self):
        """Crée les informations détaillées."""
        
        info_frame = ctk.CTkFrame(self, fg_color='transparent')
        info_frame.pack(fill='x', padx=20, pady=(0, 15))
        info_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Colonne gauche
        left_info = ctk.CTkFrame(info_frame, fg_color='transparent')
        left_info.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        # Dates
        self.add_info_item(left_info, "📅 Créé le", self.format_date(self.project_data.get('created_date')))
        self.add_info_item(left_info, "🔄 Modifié le", self.format_date(self.project_data.get('modified_date')))
        
        # Fichier source
        file_path = self.project_data.get('file_path', 'Non spécifié')
        self.add_info_item(left_info, "📁 Fichier", Path(file_path).name if file_path else 'N/A')
        
        # Colonne droite
        right_info = ctk.CTkFrame(info_frame, fg_color='transparent')
        right_info.grid(row=0, column=1, sticky='ew', padx=(10, 0))
        
        # Données techniques
        points_count = self.project_data.get('points_count', 0)
        self.add_info_item(right_info, "📍 Points mesurés", f"{points_count} points")
        
        precision = self.project_data.get('precision_achieved')
        if precision:
            self.add_info_item(right_info, "🎯 Précision", f"{precision:.1f} mm")
        
        closure_error = self.project_data.get('closure_error')
        if closure_error:
            self.add_info_item(right_info, "🔒 Erreur fermeture", f"{closure_error*1000:.1f} mm")
    
    def add_info_item(self, parent, label: str, value: str):
        """Ajoute un élément d'information."""
        
        item_frame = ctk.CTkFrame(parent, fg_color='transparent')
        item_frame.pack(fill='x', pady=3)
        
        label_widget = ThemedLabel(
            item_frame,
            text=label,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        label_widget.pack(side='left')
        
        value_widget = ThemedLabel(
            item_frame,
            text=value,
            style='small',
            text_color=AppTheme.COLORS['text']
        )
        value_widget.pack(side='right')
    
    def format_date(self, date_string: str) -> str:
        """Formate une date ISO."""
        if not date_string:
            return "Non spécifiée"
        
        try:
            date_obj = datetime.fromisoformat(date_string)
            return date_obj.strftime('%d/%m/%Y à %H:%M')
        except:
            return date_string
    
    def create_project_metrics(self):
        """Crée les métriques du projet."""
        
        metrics_frame = ctk.CTkFrame(self, fg_color='transparent')
        metrics_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        metrics_title = ThemedLabel(
            metrics_frame,
            text="📊 Métriques du Projet",
            style='subheading',
            text_color=AppTheme.COLORS['secondary']
        )
        metrics_title.pack(anchor='w', pady=(0, 10))
        
        # Grille de métriques
        grid_frame = ctk.CTkFrame(metrics_frame, fg_color='transparent')
        grid_frame.pack(fill='x')
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Métrique 1: Qualité
        quality_score = self.calculate_quality_score()
        quality_metric = StatusCard(
            grid_frame,
            title="Score Qualité",
            value=f"{quality_score:.1f}/10",
            icon="⭐",
            color=self.get_quality_color(quality_score)
        )
        quality_metric.grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        # Métrique 2: Temps de traitement
        processing_time = self.project_data.get('processing_time_minutes', 0)
        time_metric = StatusCard(
            grid_frame,
            title="Temps Traitement",
            value=f"{processing_time:.1f}min" if processing_time else "N/A",
            icon="⏱️",
            color=AppTheme.COLORS['accent']
        )
        time_metric.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Métrique 3: Efficacité
        efficiency = self.calculate_efficiency()
        efficiency_metric = StatusCard(
            grid_frame,
            title="Efficacité",
            value=f"{efficiency:.0f}%",
            icon="⚡",
            color=AppTheme.COLORS['primary']
        )
        efficiency_metric.grid(row=0, column=2, padx=(10, 0), sticky='ew')
    
    def calculate_quality_score(self) -> float:
        """Calcule un score de qualité du projet."""
        score = 10.0
        
        # Pénalité selon la précision
        precision = self.project_data.get('precision_achieved')
        if precision:
            if precision > 3.0:
                score -= 3.0
            elif precision > 2.0:
                score -= 1.0
        
        # Pénalité selon l'erreur de fermeture
        closure = self.project_data.get('closure_error')
        if closure and closure > 0.005:
            score -= 2.0
        
        # Bonus pour les projets terminés
        if self.project_data.get('status') == 'completed':
            score += 0.5
        
        return max(0, min(10, score))
    
    def calculate_efficiency(self) -> float:
        """Calcule l'efficacité du projet."""
        points = self.project_data.get('points_count', 1)
        time = self.project_data.get('processing_time_minutes', 1)
        
        # Points par minute
        ppm = points / max(time, 0.1)
        
        # Normaliser sur 100%
        return min(100, ppm * 20)  # 5 points/min = 100%
    
    def get_quality_color(self, score: float) -> str:
        """Détermine la couleur selon le score."""
        if score >= 8.0:
            return AppTheme.COLORS['success']
        elif score >= 6.0:
            return AppTheme.COLORS['warning']
        else:
            return AppTheme.COLORS['error']
    
    def create_advanced_actions(self):
        """Crée les actions avancées."""
        
        actions_frame = ctk.CTkFrame(self, fg_color='transparent')
        actions_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        actions_title = ThemedLabel(
            actions_frame,
            text="🛠️ Actions Avancées",
            style='subheading',
            text_color=AppTheme.COLORS['secondary']
        )
        actions_title.pack(anchor='w', pady=(0, 15))
        
        # Grille d'actions
        buttons_grid = ctk.CTkFrame(actions_frame, fg_color='transparent')
        buttons_grid.pack(fill='x')
        buttons_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Ligne 1
        open_button = ThemedButton(
            buttons_grid,
            text="📂 Ouvrir",
            command=lambda: self.handle_action('open'),
            variant='primary',
            width=150
        )
        open_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 10))
        
        duplicate_button = ThemedButton(
            buttons_grid,
            text="📋 Dupliquer",
            command=lambda: self.handle_action('duplicate'),
            variant='outline',
            width=150
        )
        duplicate_button.grid(row=0, column=1, padx=2.5, pady=(0, 10))
        
        visualize_button = ThemedButton(
            buttons_grid,
            text="📊 Visualiser",
            command=lambda: self.handle_action('visualize'),
            variant='outline',
            width=150
        )
        visualize_button.grid(row=0, column=2, padx=(5, 0), pady=(0, 10))
        
        # Ligne 2
        export_button = ThemedButton(
            buttons_grid,
            text="💾 Exporter",
            command=lambda: self.handle_action('export'),
            variant='ghost',
            width=150
        )
        export_button.grid(row=1, column=0, padx=(0, 5))
        
        archive_button = ThemedButton(
            buttons_grid,
            text="📦 Archiver",
            command=lambda: self.handle_action('archive'),
            variant='ghost',
            width=150
        )
        archive_button.grid(row=1, column=1, padx=2.5)
        
        delete_button = ThemedButton(
            buttons_grid,
            text="🗑️ Supprimer",
            command=lambda: self.handle_action('delete'),
            variant='ghost',
            width=150
        )
        delete_button.grid(row=1, column=2, padx=(5, 0))
    
    def handle_action(self, action: str):
        """Gère les actions sur le projet."""
        if self.callback:
            self.callback(action, self.project_data)


class ExtendedProjectManager(ctk.CTkScrollableFrame):
    """Gestionnaire étendu de projets avec toutes les fonctionnalités."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration scrollbar
        self.configure(
            scrollbar_button_color=AppTheme.COLORS['primary'],
            scrollbar_button_hover_color=AppTheme.COLORS['primary_dark']
        )
        
        # Données
        self.projects_file = Path("data/projects.json")
        self.all_projects = []
        self.filtered_projects = []
        self.selected_project = None
        
        # Interface
        self.current_view = 'list'  # 'list' ou 'details'
        
        # Charger les données
        self.load_projects()
        
        # Créer l'interface
        self.create_manager_interface()
    
    def create_manager_interface(self):
        """Crée l'interface complète du gestionnaire."""
        
        # En-tête avec statistiques
        self.create_main_header()
        
        # Barre de recherche et filtres
        self.create_search_filter()
        
        # Zone principale (liste ou détails)
        self.create_main_area()
        
        # Actualiser l'affichage initial
        self.refresh_projects_display()
    
    def create_main_header(self):
        """Crée l'en-tête principal."""
        
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', pady=(20, 30))
        
        # Titre et compteurs
        title_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        title_frame.pack(side='left', fill='x', expand=True)
        
        main_title = ThemedLabel(
            title_frame,
            text="🗂️ Gestion Étendue des Projets",
            style='title',
            text_color=AppTheme.COLORS['primary']
        )
        main_title.pack(anchor='w')
        
        # Statistiques en ligne
        self.create_header_statistics(title_frame)
        
        # Boutons d'action globaux
        actions_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        actions_frame.pack(side='right')
        
        new_button = ThemedButton(
            actions_frame,
            text="➕ Nouveau",
            command=self.create_new_project,
            variant='primary'
        )
        new_button.pack(side='left', padx=(0, 10))
        
        import_button = ThemedButton(
            actions_frame,
            text="📁 Importer",
            command=self.import_projects,
            variant='outline'
        )
        import_button.pack(side='left', padx=(0, 10))
        
        compare_button = ThemedButton(
            actions_frame,
            text="⚖️ Comparer",
            command=self.open_comparison_mode,
            variant='outline'
        )
        compare_button.pack(side='left')
    
    def create_header_statistics(self, parent):
        """Crée les statistiques en en-tête."""
        
        stats_frame = ctk.CTkFrame(parent, fg_color='transparent')
        stats_frame.pack(anchor='w', pady=(10, 0))
        
        total_projects = len(self.all_projects)
        completed = len([p for p in self.all_projects if p.get('status') == 'completed'])
        avg_precision = self.calculate_average_precision()
        
        stats_text = f"📊 {total_projects} projets • ✅ {completed} terminés • 🎯 {avg_precision:.1f}mm moy."
        
        stats_label = ThemedLabel(
            stats_frame,
            text=stats_text,
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        stats_label.pack()
    
    def calculate_average_precision(self) -> float:
        """Calcule la précision moyenne."""
        precisions = [p['precision_achieved'] for p in self.all_projects if p.get('precision_achieved')]
        return sum(precisions) / len(precisions) if precisions else 2.0
    
    def create_search_filter(self):
        """Crée la zone de recherche et filtrage."""
        
        self.search_filter = ProjectSearchFilter(
            self,
            callback=self.on_filters_changed
        )
        self.search_filter.pack(fill='x', pady=(0, 20))
    
    def create_main_area(self):
        """Crée la zone principale."""
        
        self.main_area = ctk.CTkFrame(self, fg_color='transparent')
        self.main_area.pack(fill='both', expand=True)
    
    def on_filters_changed(self, filters: Dict):
        """Gère les changements de filtres."""
        
        self.filtered_projects = self.apply_filters(self.all_projects, filters)
        self.refresh_projects_display()
    
    def apply_filters(self, projects: List[Dict], filters: Dict) -> List[Dict]:
        """Applique les filtres aux projets."""
        
        filtered = projects.copy()
        
        # Filtre par texte de recherche
        if filters['search_text']:
            search_text = filters['search_text'].lower()
            filtered = [
                p for p in filtered
                if search_text in p.get('name', '').lower() or
                   search_text in p.get('description', '').lower()
            ]
        
        # Filtre par statut
        if filters['status'] not in ['all', 'tous']:
            status_map = {
                'terminé': 'completed',
                'en cours': 'in_progress', 
                'brouillon': 'draft'
            }
            target_status = status_map.get(filters['status'], filters['status'])
            filtered = [p for p in filtered if p.get('status') == target_status]
        
        # Filtre par précision
        if filters['precision_range'] not in ['all', 'toutes']:
            if filters['precision_range'] == '< 1.5mm':
                filtered = [p for p in filtered if p.get('precision_achieved', 999) < 1.5]
            elif filters['precision_range'] == '1.5-2.5mm':
                filtered = [p for p in filtered if 1.5 <= p.get('precision_achieved', 999) <= 2.5]
            elif filters['precision_range'] == '> 2.5mm':
                filtered = [p for p in filtered if p.get('precision_achieved', 0) > 2.5]
        
        # Filtre par taille
        if filters['points_range'] not in ['all', 'toutes']:
            if filters['points_range'] == '< 20 pts':
                filtered = [p for p in filtered if p.get('points_count', 0) < 20]
            elif filters['points_range'] == '20-50 pts':
                filtered = [p for p in filtered if 20 <= p.get('points_count', 0) <= 50]
            elif filters['points_range'] == '> 50 pts':
                filtered = [p for p in filtered if p.get('points_count', 0) > 50]
        
        return filtered
    
    def refresh_projects_display(self):
        """Actualise l'affichage des projets."""
        
        # Nettoyer la zone principale
        for widget in self.main_area.winfo_children():
            widget.destroy()
        
        if not self.filtered_projects:
            self.show_no_projects_message()
            return
        
        if self.current_view == 'list':
            self.show_projects_list()
        else:
            self.show_project_details()
    
    def show_no_projects_message(self):
        """Affiche le message quand aucun projet ne correspond."""
        
        empty_frame = ctk.CTkFrame(self.main_area, fg_color='transparent')
        empty_frame.pack(expand=True, fill='both')
        
        icon_label = ThemedLabel(
            empty_frame,
            text="🔍",
            style='display',
            text_color=AppTheme.COLORS['text_secondary']
        )
        icon_label.pack(pady=(100, 20))
        
        message_label = ThemedLabel(
            empty_frame,
            text="Aucun projet ne correspond aux critères de recherche",
            style='heading',
            text_color=AppTheme.COLORS['text_secondary']
        )
        message_label.pack()
        
        reset_button = ThemedButton(
            empty_frame,
            text="🔄 Réinitialiser les filtres",
            command=self.search_filter.reset_filters,
            variant='outline'
        )
        reset_button.pack(pady=20)
    
    def show_projects_list(self):
        """Affiche la liste des projets."""
        
        list_frame = ctk.CTkFrame(self.main_area, fg_color='transparent')
        list_frame.pack(fill='both', expand=True)
        
        # En-tête de liste
        header_frame = ctk.CTkFrame(list_frame, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 15))
        
        title_label = ThemedLabel(
            header_frame,
            text=f"📋 Projets ({len(self.filtered_projects)})",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Options d'affichage
        view_options = ctk.CTkFrame(header_frame, fg_color='transparent')
        view_options.pack(side='right')
        
        # Grille de projets
        projects_grid = ctk.CTkFrame(list_frame, fg_color='transparent')
        projects_grid.pack(fill='both', expand=True)
        
        # Afficher les projets en grille 3 colonnes
        for i, project in enumerate(self.filtered_projects):
            row = i // 3
            col = i % 3
            
            if col == 0:
                projects_grid.grid_rowconfigure(row, weight=0)
            projects_grid.grid_columnconfigure(col, weight=1)
            
            project_card = ProjectCard(
                projects_grid,
                project_data=project,
                callback=self.on_project_selected
            )
            project_card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
    
    def show_project_details(self):
        """Affiche les détails d'un projet."""
        
        if not self.selected_project:
            return
        
        # Bouton retour
        back_frame = ctk.CTkFrame(self.main_area, fg_color='transparent')
        back_frame.pack(fill='x', pady=(0, 20))
        
        back_button = ThemedButton(
            back_frame,
            text="← Retour à la liste",
            command=self.return_to_list,
            variant='ghost'
        )
        back_button.pack(side='left')
        
        # Détails du projet
        self.project_details = ProjectDetails(
            self.main_area,
            project_data=self.selected_project,
            callback=self.handle_project_action
        )
        self.project_details.pack(fill='both', expand=True)
    
    def on_project_selected(self, project_data: Dict):
        """Gère la sélection d'un projet."""
        
        self.selected_project = project_data
        self.current_view = 'details'
        self.refresh_projects_display()
    
    def return_to_list(self):
        """Retourne à la vue liste."""
        
        self.current_view = 'list'
        self.selected_project = None
        self.refresh_projects_display()
    
    def handle_project_action(self, action: str, project_data: Dict):
        """Gère les actions sur un projet."""
        
        if action == 'open':
            messagebox.showinfo("Ouvrir", f"Ouverture du projet : {project_data['name']}")
        elif action == 'duplicate':
            self.duplicate_project(project_data)
        elif action == 'visualize':
            self.open_project_visualization(project_data)
        elif action == 'export':
            self.export_project(project_data)
        elif action == 'archive':
            self.archive_project(project_data)
        elif action == 'delete':
            self.delete_project(project_data)
    
    def duplicate_project(self, project_data: Dict):
        """Duplique un projet."""
        
        new_project = project_data.copy()
        new_project['id'] = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_project['name'] = f"{project_data['name']} - Copie"
        new_project['status'] = 'draft'
        new_project['created_date'] = datetime.now().isoformat()
        new_project['modified_date'] = datetime.now().isoformat()
        
        self.all_projects.append(new_project)
        self.save_projects()
        self.refresh_projects_display()
        
        messagebox.showinfo("Duplication", f"Projet dupliqué : {new_project['name']}")
    
    def open_project_visualization(self, project_data: Dict):
        """Ouvre les visualisations d'un projet."""
        
        viz_window = InteractiveVisualizationWindow(self, data=project_data)
    
    def export_project(self, project_data: Dict):
        """Exporte un projet."""
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title=f"Exporter {project_data['name']}"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export", f"Projet exporté vers :\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter :\n{str(e)}")
    
    def archive_project(self, project_data: Dict):
        """Archive un projet."""
        
        # Changer le statut
        project_data['status'] = 'archived'
        project_data['modified_date'] = datetime.now().isoformat()
        
        self.save_projects()
        self.refresh_projects_display()
        
        messagebox.showinfo("Archivage", f"Projet archivé : {project_data['name']}")
    
    def delete_project(self, project_data: Dict):
        """Supprime un projet."""
        
        result = messagebox.askyesno(
            "Confirmer suppression",
            f"Voulez-vous vraiment supprimer le projet :\n'{project_data['name']}' ?\n\nCette action est irréversible."
        )
        
        if result:
            self.all_projects = [p for p in self.all_projects if p['id'] != project_data['id']]
            self.save_projects()
            
            if self.current_view == 'details':
                self.return_to_list()
            else:
                self.refresh_projects_display()
            
            messagebox.showinfo("Suppression", f"Projet supprimé : {project_data['name']}")
    
    def create_new_project(self):
        """Crée un nouveau projet."""
        
        # Dialog pour les informations de base
        dialog = ctk.CTkInputDialog(
            text="Nom du nouveau projet:",
            title="Créer un Projet"
        )
        name = dialog.get_input()
        
        if name:
            new_project = {
                'id': f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'name': name,
                'description': '',
                'created_date': datetime.now().isoformat(),
                'modified_date': datetime.now().isoformat(),
                'status': 'draft',
                'points_count': 0,
                'precision_achieved': None,
                'file_path': '',
                'closure_error': None,
                'processing_time_minutes': None
            }
            
            self.all_projects.append(new_project)
            self.save_projects()
            self.refresh_projects_display()
            
            messagebox.showinfo("Nouveau projet", f"Projet créé : {name}")
    
    def import_projects(self):
        """Importe des projets depuis un fichier."""
        
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importer des projets"
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                # Si c'est une liste de projets
                if isinstance(imported_data, list):
                    imported_projects = imported_data
                # Si c'est un seul projet
                elif isinstance(imported_data, dict):
                    imported_projects = [imported_data]
                else:
                    raise ValueError("Format de fichier non reconnu")
                
                # Ajouter les projets
                for project in imported_projects:
                    # Générer un nouvel ID si nécessaire
                    if not project.get('id'):
                        project['id'] = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.all_projects)}"
                    
                    self.all_projects.append(project)
                
                self.save_projects()
                self.refresh_projects_display()
                
                messagebox.showinfo("Import", f"{len(imported_projects)} projet(s) importé(s)")
                
            except Exception as e:
                messagebox.showerror("Erreur d'import", f"Impossible d'importer :\n{str(e)}")
    
    def open_comparison_mode(self):
        """Ouvre le mode comparaison."""
        
        if len(self.all_projects) < 2:
            messagebox.showwarning("Comparaison", "Au moins 2 projets sont nécessaires pour la comparaison.")
            return
        
        comparison_window = ComparisonModeWindow(self, self.all_projects)
    
    def load_projects(self):
        """Charge les projets depuis le fichier."""
        
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.all_projects = json.load(f)
            else:
                self.all_projects = []
        except Exception as e:
            print(f"Erreur chargement projets: {e}")
            self.all_projects = []
        
        self.filtered_projects = self.all_projects.copy()
    
    def save_projects(self):
        """Sauvegarde les projets."""
        
        try:
            self.projects_file.parent.mkdir(exist_ok=True)
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde projets: {e}")


class ExtendedProjectManagerWindow(ctk.CTkToplevel):
    """Fenêtre de gestion étendue des projets."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuration fenêtre
        self.title("🗂️ Gestion Étendue des Projets - Système de Compensation Altimétrique")
        self.geometry("1600x1000")
        self.minsize(1200, 800)
        
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
        """Crée l'interface de la fenêtre."""
        
        # Gestionnaire principal
        self.project_manager = ExtendedProjectManager(self)
        self.project_manager.pack(fill='both', expand=True, padx=20, pady=20)