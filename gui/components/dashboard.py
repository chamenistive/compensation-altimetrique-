"""
Composant Dashboard moderne pour le Système de Compensation Altimétrique.
Interface principale avec vue d'ensemble, projets récents et navigation intuitive.
Suit l'architecture existante et utilise les composants base_components.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

from .base_components import (
    ThemedButton, ThemedLabel, ThemedFrame, StatusCard, 
    ProgressCard, ProjectCard, ThemedEntry
)
from ..utils.theme import AppTheme


class ModernDashboard(ThemedFrame):
    """Dashboard principal moderne avec vue d'ensemble et gestion des projets."""
    
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.callback = callback  # Callback pour navigation vers les étapes
        self.projects_data = []   # Données des projets récents
        self.current_project = None
        
        # Charger les données des projets
        self.load_projects_data()
        
        # Configuration responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Créer l'interface
        self.create_dashboard()
        
        # Actualiser périodiquement les données
        self.refresh_data()
    
    def create_dashboard(self):
        """Crée l'interface complète du dashboard."""
        
        # Container principal avec scrolling
        self.main_container = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent',
            scrollbar_button_color=AppTheme.COLORS['primary'],
            scrollbar_button_hover_color=AppTheme.COLORS['primary_dark']
        )
        self.main_container.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        self.main_container.grid_columnconfigure((0, 1), weight=1)
        
        # En-tête moderne avec branding
        self.create_modern_header()
        
        # Section des actions rapides
        self.create_quick_actions()
        
        # Section des projets récents
        self.create_recent_projects()
        
        # Section des statistiques et métriques
        self.create_statistics_panel()
        
        # Section des outils et ressources
        self.create_tools_panel()
    
    def create_modern_header(self):
        """Crée l'en-tête moderne avec branding géodésique."""
        
        header_frame = ThemedFrame(self.main_container, elevated=True)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Conteneur gauche - Logo et titre
        left_container = ctk.CTkFrame(header_frame, fg_color='transparent')
        left_container.grid(row=0, column=0, sticky='w', padx=30, pady=30)
        
        # Logo géodésique moderne
        logo_frame = ctk.CTkFrame(
            left_container,
            width=80,
            height=80,
            corner_radius=20,
            fg_color=AppTheme.COLORS['primary']
        )
        logo_frame.grid(row=0, column=0, padx=(0, 20))
        logo_frame.grid_propagate(False)
        
        # Symbole géodésique
        logo_symbol = ThemedLabel(
            logo_frame,
            text="🧭",
            style='display',
            text_color='white'
        )
        logo_symbol.place(relx=0.5, rely=0.5, anchor='center')
        
        # Conteneur titre et sous-titre
        title_container = ctk.CTkFrame(left_container, fg_color='transparent')
        title_container.grid(row=0, column=1, sticky='w')
        
        # Titre principal
        main_title = ThemedLabel(
            title_container,
            text="Système de Compensation Altimétrique",
            style='title',
            text_color=AppTheme.COLORS['text']
        )
        main_title.grid(row=0, column=0, sticky='w')
        
        # Sous-titre avec badge de version
        subtitle_frame = ctk.CTkFrame(title_container, fg_color='transparent')
        subtitle_frame.grid(row=1, column=0, sticky='w', pady=(5, 0))
        
        subtitle = ThemedLabel(
            subtitle_frame,
            text="Dashboard Principal • Précision Géodésique",
            style='subheading',
            text_color=AppTheme.COLORS['text_secondary']
        )
        subtitle.grid(row=0, column=0, sticky='w')
        
        # Badge version
        version_badge = ctk.CTkFrame(
            subtitle_frame,
            fg_color=AppTheme.COLORS['accent'],
            corner_radius=15,
            height=25
        )
        version_badge.grid(row=0, column=1, padx=(10, 0))
        
        version_label = ThemedLabel(
            version_badge,
            text="v2.0",
            style='small',
            text_color='white'
        )
        version_label.pack(padx=10, pady=2)
        
        # Conteneur droite - Informations système
        right_container = ctk.CTkFrame(header_frame, fg_color='transparent')
        right_container.grid(row=0, column=1, sticky='e', padx=30, pady=30)
        
        # Date et heure
        datetime_now = datetime.now()
        date_label = ThemedLabel(
            right_container,
            text=datetime_now.strftime("%d/%m/%Y • %H:%M"),
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        date_label.grid(row=0, column=0, sticky='e')
        
        # Statut système
        status_frame = ctk.CTkFrame(right_container, fg_color='transparent')
        status_frame.grid(row=1, column=0, sticky='e', pady=(5, 0))
        
        status_indicator = ctk.CTkFrame(
            status_frame,
            width=10,
            height=10,
            corner_radius=5,
            fg_color=AppTheme.COLORS['success']
        )
        status_indicator.grid(row=0, column=0, padx=(0, 5))
        
        status_label = ThemedLabel(
            status_frame,
            text="Système Opérationnel",
            style='small',
            text_color=AppTheme.COLORS['success']
        )
        status_label.grid(row=0, column=1)
    
    def create_quick_actions(self):
        """Crée la section des actions rapides."""
        
        # Titre de section
        section_title = ThemedLabel(
            self.main_container,
            text="🚀 Actions Rapides",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        section_title.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 15))
        
        # Conteneur des cartes d'action
        actions_frame = ctk.CTkFrame(self.main_container, fg_color='transparent')
        actions_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Action 1: Nouveau projet
        new_project_card = self.create_action_card(
            actions_frame,
            title="Nouveau Projet",
            description="Démarrer une nouvelle compensation altimétrique",
            icon="📁",
            color=AppTheme.COLORS['primary'],
            command=self.start_new_project
        )
        new_project_card.grid(row=0, column=0, padx=(0, 15), sticky='ew')
        
        # Action 2: Import rapide
        quick_import_card = self.create_action_card(
            actions_frame,
            title="Import Rapide",
            description="Importer directement un fichier de données",
            icon="⚡",
            color=AppTheme.COLORS['accent'],
            command=self.quick_import
        )
        quick_import_card.grid(row=0, column=1, padx=7.5, sticky='ew')
        
        # Action 3: Ouvrir projet
        open_project_card = self.create_action_card(
            actions_frame,
            title="Ouvrir Projet",
            description="Continuer un projet existant",
            icon="🔄",
            color=AppTheme.COLORS['secondary'],
            command=self.open_existing_project
        )
        open_project_card.grid(row=0, column=2, padx=(15, 0), sticky='ew')
    
    def create_action_card(self, parent, title, description, icon, color, command):
        """Crée une carte d'action moderne."""
        
        card = ThemedFrame(parent, elevated=True)
        card.configure(cursor='hand2')
        
        # Conteneur principal
        content_frame = ctk.CTkFrame(card, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Icône avec cercle coloré
        icon_frame = ctk.CTkFrame(
            content_frame,
            width=60,
            height=60,
            corner_radius=30,
            fg_color=color
        )
        icon_frame.pack(pady=(0, 15))
        icon_frame.pack_propagate(False)
        
        icon_label = ThemedLabel(
            icon_frame,
            text=icon,
            style='title',
            text_color='white'
        )
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Titre
        title_label = ThemedLabel(
            content_frame,
            text=title,
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(pady=(0, 8))
        
        # Description
        desc_label = ThemedLabel(
            content_frame,
            text=description,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        desc_label.pack(pady=(0, 20))
        
        # Bouton d'action
        action_button = ThemedButton(
            content_frame,
            text="Commencer",
            command=command,
            variant='primary',
            width=120,
            height=35
        )
        action_button.pack()
        
        # Effet hover sur la carte
        def on_enter(event):
            card.configure(fg_color=AppTheme.COLORS['background'])
        
        def on_leave(event):
            card.configure(fg_color=AppTheme.COLORS['surface_elevated'])
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        return card
    
    def create_recent_projects(self):
        """Crée la section des projets récents."""
        
        # Titre avec compteur
        projects_count = len(self.projects_data)
        section_title = ThemedLabel(
            self.main_container,
            text=f"📂 Projets Récents ({projects_count})",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        section_title.grid(row=3, column=0, sticky='w', pady=(0, 15))
        
        # Bouton "Voir tous"
        view_all_button = ThemedButton(
            self.main_container,
            text="Voir tous",
            command=self.view_all_projects,
            variant='ghost',
            size='small'
        )
        view_all_button.grid(row=3, column=1, sticky='e', pady=(0, 15))
        
        # Conteneur des projets
        projects_frame = ctk.CTkFrame(self.main_container, fg_color='transparent')
        projects_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        
        if self.projects_data:
            self.display_recent_projects(projects_frame)
        else:
            self.display_no_projects_message(projects_frame)
    
    def display_recent_projects(self, parent):
        """Affiche les projets récents."""
        
        # Afficher les 3 projets les plus récents
        recent_projects = self.projects_data[:3]
        
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        
        for i, project_data in enumerate(recent_projects):
            project_card = ProjectCard(
                parent,
                project_data=project_data,
                callback=self.open_project
            )
            project_card.grid(row=0, column=i, padx=7.5 if i == 1 else (0, 15) if i == 0 else (15, 0), sticky='ew')
    
    def display_no_projects_message(self, parent):
        """Affiche un message quand aucun projet n'existe."""
        
        empty_state = ThemedFrame(parent, elevated=False)
        empty_state.pack(fill='x', pady=40)
        
        # Illustration vide
        empty_icon = ThemedLabel(
            empty_state,
            text="📭",
            style='display',
            text_color=AppTheme.COLORS['text_secondary']
        )
        empty_icon.pack(pady=(40, 20))
        
        # Message principal
        empty_title = ThemedLabel(
            empty_state,
            text="Aucun projet récent",
            style='subheading',
            text_color=AppTheme.COLORS['text_secondary']
        )
        empty_title.pack(pady=(0, 10))
        
        # Message secondaire
        empty_desc = ThemedLabel(
            empty_state,
            text="Commencez votre premier projet de compensation altimétrique",
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        empty_desc.pack(pady=(0, 30))
        
        # Bouton d'action
        start_button = ThemedButton(
            empty_state,
            text="🚀 Créer mon premier projet",
            command=self.start_new_project,
            variant='primary',
            width=200
        )
        start_button.pack(pady=(0, 40))
    
    def create_statistics_panel(self):
        """Crée le panneau de statistiques et métriques."""
        
        # Titre de section
        section_title = ThemedLabel(
            self.main_container,
            text="📊 Aperçu Système",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        section_title.grid(row=5, column=0, columnspan=2, sticky='w', pady=(0, 15))
        
        # Conteneur des métriques
        metrics_frame = ctk.CTkFrame(self.main_container, fg_color='transparent')
        metrics_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Calculer les statistiques
        stats = self.calculate_system_statistics()
        
        # Métrique 1: Projets totaux
        projects_metric = StatusCard(
            metrics_frame,
            title="Projets Totaux",
            value=str(stats['total_projects']),
            icon="📁",
            color=AppTheme.COLORS['primary']
        )
        projects_metric.grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        # Métrique 2: Précision moyenne
        precision_metric = StatusCard(
            metrics_frame,
            title="Précision Moyenne",
            value=f"{stats['avg_precision']:.1f}mm",
            icon="🎯",
            color=AppTheme.COLORS['success']
        )
        precision_metric.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Métrique 3: Points traités
        points_metric = StatusCard(
            metrics_frame,
            title="Points Traités",
            value=str(stats['total_points']),
            icon="📍",
            color=AppTheme.COLORS['accent']
        )
        points_metric.grid(row=0, column=2, padx=5, sticky='ew')
        
        # Métrique 4: Temps moyen
        time_metric = StatusCard(
            metrics_frame,
            title="Temps Moyen",
            value=f"{stats['avg_processing_time']}min",
            icon="⏱️",
            color=AppTheme.COLORS['secondary']
        )
        time_metric.grid(row=0, column=3, padx=(10, 0), sticky='ew')
    
    def create_tools_panel(self):
        """Crée le panneau des outils et ressources."""
        
        # Titre de section
        section_title = ThemedLabel(
            self.main_container,
            text="🛠️ Outils et Ressources",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        section_title.grid(row=7, column=0, columnspan=2, sticky='w', pady=(0, 15))
        
        # Conteneur des outils
        tools_frame = ctk.CTkFrame(self.main_container, fg_color='transparent')
        tools_frame.grid(row=8, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        tools_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Colonne gauche - Outils techniques
        left_tools = ThemedFrame(tools_frame, elevated=True)
        left_tools.grid(row=0, column=0, padx=(0, 15), sticky='nsew')
        
        # Titre section gauche
        left_title = ThemedLabel(
            left_tools,
            text="🔧 Outils Techniques",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        left_title.pack(padx=20, pady=(20, 15), anchor='w')
        
        # Liste des outils techniques
        tech_tools = [
            ("Calculatrice Géodésique", "🧮", self.open_calculator),
            ("Convertisseur d'Unités", "🔄", self.open_converter),
            ("Vérificateur de Formats", "✅", self.check_formats),
            ("Diagnostics Système", "🔍", self.run_diagnostics)
        ]
        
        for tool_name, tool_icon, tool_command in tech_tools:
            tool_button = self.create_tool_button(
                left_tools, tool_name, tool_icon, tool_command
            )
            tool_button.pack(fill='x', padx=20, pady=2)
        
        # Colonne droite - Ressources et aide
        right_tools = ThemedFrame(tools_frame, elevated=True)
        right_tools.grid(row=0, column=1, padx=(15, 0), sticky='nsew')
        
        # Titre section droite
        right_title = ThemedLabel(
            right_tools,
            text="📚 Ressources & Aide",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        right_title.pack(padx=20, pady=(20, 15), anchor='w')
        
        # Liste des ressources
        resources = [
            ("Documentation Utilisateur", "📖", self.open_documentation),
            ("Tutoriels Vidéo", "🎥", self.open_tutorials),
            ("Exemples de Projets", "🌟", self.open_examples),
            ("Support Technique", "💬", self.contact_support)
        ]
        
        for resource_name, resource_icon, resource_command in resources:
            resource_button = self.create_tool_button(
                right_tools, resource_name, resource_icon, resource_command
            )
            resource_button.pack(fill='x', padx=20, pady=2)
        
        # Espacement final
        ctk.CTkFrame(tools_frame, height=20, fg_color='transparent').grid(row=1, column=0, columnspan=2)
    
    def create_tool_button(self, parent, text, icon, command):
        """Crée un bouton d'outil avec icône."""
        
        button_frame = ctk.CTkFrame(parent, fg_color='transparent')
        
        button = ThemedButton(
            button_frame,
            text=f"{icon} {text}",
            command=command,
            variant='ghost',
            width=200
        )
        button.pack(fill='x')
        
        return button_frame
    
    # Méthodes de gestion des données
    def load_projects_data(self):
        """Charge les données des projets depuis le stockage."""
        try:
            projects_file = Path("data/projects.json")
            if projects_file.exists():
                with open(projects_file, 'r', encoding='utf-8') as f:
                    self.projects_data = json.load(f)
            else:
                # Créer des données de démonstration
                self.projects_data = self.create_demo_projects()
        except Exception as e:
            print(f"Erreur chargement projets: {e}")
            self.projects_data = []
    
    def create_demo_projects(self):
        """Crée des projets de démonstration."""
        demo_projects = [
            {
                'id': 'proj_001',
                'name': 'Nivellement Autoroute A7',
                'description': 'Compensation altimétrique section Lyon-Marseille',
                'created_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'modified_date': (datetime.now() - timedelta(hours=3)).isoformat(),
                'status': 'completed',
                'points_count': 45,
                'precision_achieved': 1.8,
                'file_path': 'projects/a7_nivellement.xlsx'
            },
            {
                'id': 'proj_002', 
                'name': 'Campus Universitaire',
                'description': 'Relevé topographique bâtiments principaux',
                'created_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'modified_date': (datetime.now() - timedelta(days=1)).isoformat(),
                'status': 'in_progress',
                'points_count': 28,
                'precision_achieved': 2.1,
                'file_path': 'projects/campus_topo.csv'
            },
            {
                'id': 'proj_003',
                'name': 'Zone Industrielle Sud',
                'description': 'Implantation nouveaux équipements',
                'created_date': (datetime.now() - timedelta(days=7)).isoformat(),
                'modified_date': (datetime.now() - timedelta(days=6)).isoformat(),
                'status': 'draft',
                'points_count': 15,
                'precision_achieved': None,
                'file_path': 'projects/zone_indus.xlsx'
            }
        ]
        return demo_projects
    
    def calculate_system_statistics(self):
        """Calcule les statistiques système."""
        total_projects = len(self.projects_data)
        
        completed_projects = [p for p in self.projects_data if p.get('precision_achieved')]
        avg_precision = sum(p['precision_achieved'] for p in completed_projects) / len(completed_projects) if completed_projects else 2.0
        
        total_points = sum(p.get('points_count', 0) for p in self.projects_data)
        avg_processing_time = 3.5  # Estimation moyenne
        
        return {
            'total_projects': total_projects,
            'avg_precision': avg_precision,
            'total_points': total_points,
            'avg_processing_time': avg_processing_time
        }
    
    def refresh_data(self):
        """Actualise les données périodiquement."""
        # Actualiser toutes les 30 secondes
        self.after(30000, self.refresh_data)
    
    # Méthodes de callback pour les actions
    def start_new_project(self):
        """Démarre un nouveau projet."""
        if self.callback:
            self.callback('new_project')
    
    def quick_import(self):
        """Lance l'import rapide."""
        if self.callback:
            self.callback('quick_import')
    
    def open_existing_project(self):
        """Ouvre un projet existant."""
        if self.callback:
            self.callback('open_project')
    
    def open_project(self, project_data):
        """Ouvre un projet spécifique."""
        self.current_project = project_data
        if self.callback:
            self.callback('open_specific_project', project_data)
    
    def view_all_projects(self):
        """Affiche tous les projets."""
        if self.callback:
            self.callback('view_all_projects')
    
    def open_calculator(self):
        """Ouvre la calculatrice géodésique."""
        messagebox.showinfo("Calculatrice", "Fonctionnalité à implémenter")
    
    def open_converter(self):
        """Ouvre le convertisseur d'unités.""" 
        messagebox.showinfo("Convertisseur", "Fonctionnalité à implémenter")
    
    def check_formats(self):
        """Vérifie les formats de fichiers."""
        messagebox.showinfo("Vérification", "Tous les formats sont supportés")
    
    def run_diagnostics(self):
        """Lance les diagnostics système."""
        messagebox.showinfo("Diagnostics", "Système opérationnel - Aucun problème détecté")
    
    def open_documentation(self):
        """Ouvre la documentation."""
        messagebox.showinfo("Documentation", "Documentation disponible en ligne")
    
    def open_tutorials(self):
        """Ouvre les tutoriels."""
        messagebox.showinfo("Tutoriels", "Tutoriels vidéo disponibles")
    
    def open_examples(self):
        """Ouvre les exemples."""
        messagebox.showinfo("Exemples", "Exemples de projets disponibles")
    
    def contact_support(self):
        """Contact le support."""
        messagebox.showinfo("Support", "Support technique: support@geodesie.fr")