"""
Visualisations interactives avancées pour le Système de Compensation Altimétrique.
Graphiques modernes avec Plotly, Matplotlib et intégration CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as patches
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ Plotly non disponible - utilisation de Matplotlib seul")

# Configuration matplotlib pour éviter les erreurs d'affichage
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour éviter les erreurs X11

from .base_components import ThemedButton, ThemedLabel, ThemedFrame, StatusCard
from ..utils.theme import AppTheme


class AdvancedVisualizationPanel(ThemedFrame):
    """Panel de visualisation avancée avec graphiques interactifs."""
    
    def __init__(self, parent, data=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.data = data or {}
        self.current_chart = None
        self.fig = None
        self.canvas = None
        
        # Configuration matplotlib avec thème géodésique
        self.setup_matplotlib_theme()
        
        # Créer l'interface
        self.create_visualization_interface()
    
    def setup_matplotlib_theme(self):
        """Configure le thème matplotlib selon la palette géodésique."""
        
        # Style moderne avec couleurs géodésiques
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        
        # Configuration des couleurs globales
        plt.rcParams.update({
            'figure.facecolor': AppTheme.COLORS['background'],
            'axes.facecolor': AppTheme.COLORS['surface'],
            'axes.edgecolor': AppTheme.COLORS['border'],
            'axes.linewidth': 1,
            'axes.grid': True,
            'grid.color': AppTheme.COLORS['border_light'],
            'grid.alpha': 0.3,
            'text.color': AppTheme.COLORS['text'],
            'axes.labelcolor': AppTheme.COLORS['text'],
            'axes.titlecolor': AppTheme.COLORS['text'],
            'xtick.color': AppTheme.COLORS['text_secondary'],
            'ytick.color': AppTheme.COLORS['text_secondary'],
            'font.family': 'sans-serif',
            'font.sans-serif': ['Segoe UI', 'Arial', 'DejaVu Sans'],
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 16
        })
    
    def create_visualization_interface(self):
        """Crée l'interface de visualisation."""
        
        # En-tête avec contrôles
        self.create_header_controls()
        
        # Zone principale de visualisation
        self.create_main_visualization_area()
        
        # Panneau d'analyse
        self.create_analysis_panel()
    
    def create_header_controls(self):
        """Crée les contrôles d'en-tête."""
        
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Titre avec icône
        title_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        title_frame.pack(side='left')
        
        icon_label = ThemedLabel(
            title_frame,
            text="📊",
            style='heading',
            text_color=AppTheme.COLORS['primary']
        )
        icon_label.pack(side='left', padx=(0, 10))
        
        title_label = ThemedLabel(
            title_frame,
            text="Visualisations Avancées",
            style='heading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Contrôles de navigation
        controls_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        controls_frame.pack(side='right')
        
        # Sélecteur de type de graphique
        self.chart_type_var = ctk.StringVar(value="Profil Altimétrique")
        self.chart_selector = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.chart_type_var,
            values=[
                "Profil Altimétrique",
                "Analyse de Fermeture", 
                "Diagnostics Compensation",
                "Évolution Précision",
                "Carte de Chaleur Résidus",
                "Analyse Spectrale",
                "Comparaison Méthodes",
                "Dashboard Qualité"
            ],
            command=self.on_chart_type_changed,
            font=AppTheme.FONTS['body'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary'],
            dropdown_fg_color=AppTheme.COLORS['surface']
        )
        self.chart_selector.pack(side='left', padx=(0, 10))
        
        # Bouton actualiser
        refresh_button = ThemedButton(
            controls_frame,
            text="🔄 Actualiser",
            command=self.refresh_visualization,
            variant='outline',
            size='small'
        )
        refresh_button.pack(side='left', padx=(0, 10))
        
        # Bouton exporter
        export_button = ThemedButton(
            controls_frame,
            text="💾 Exporter",
            command=self.export_visualization,
            variant='primary',
            size='small'
        )
        export_button.pack(side='left')
    
    def create_main_visualization_area(self):
        """Crée la zone principale de visualisation."""
        
        # Container principal pour graphiques
        viz_container = ctk.CTkFrame(self, fg_color=AppTheme.COLORS['surface'])
        viz_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Zone de graphique matplotlib
        self.matplotlib_frame = ctk.CTkFrame(viz_container, fg_color='transparent')
        self.matplotlib_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Créer le graphique initial
        self.create_altitude_profile()
    
    def create_analysis_panel(self):
        """Crée le panneau d'analyse avec métriques."""
        
        analysis_frame = ctk.CTkFrame(self, fg_color='transparent')
        analysis_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Titre du panneau
        panel_title = ThemedLabel(
            analysis_frame,
            text="📈 Analyse en Temps Réel",
            style='subheading',
            text_color=AppTheme.COLORS['secondary']
        )
        panel_title.pack(anchor='w', pady=(0, 10))
        
        # Métriques en ligne
        metrics_frame = ctk.CTkFrame(analysis_frame, fg_color='transparent')
        metrics_frame.pack(fill='x')
        metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Créer les cartes de métriques
        self.create_analysis_metrics(metrics_frame)
    
    def create_analysis_metrics(self, parent):
        """Crée les métriques d'analyse."""
        
        # Données d'exemple (en production, viendraient des calculs)
        metrics_data = self.calculate_visualization_metrics()
        
        # Métrique 1: Points analysés
        points_metric = StatusCard(
            parent,
            title="Points Analysés",
            value=str(metrics_data['points_count']),
            icon="📍",
            color=AppTheme.COLORS['primary']
        )
        points_metric.grid(row=0, column=0, padx=(0, 10), sticky='ew')
        
        # Métrique 2: Erreur RMS
        rms_metric = StatusCard(
            parent,
            title="Erreur RMS",
            value=f"{metrics_data['rms_error']:.2f}mm",
            icon="📏",
            color=AppTheme.COLORS['warning'] if metrics_data['rms_error'] > 2.0 else AppTheme.COLORS['success']
        )
        rms_metric.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Métrique 3: Facteur qualité
        quality_metric = StatusCard(
            parent,
            title="Facteur Qualité",
            value=f"{metrics_data['quality_factor']:.1f}",
            icon="🎯",
            color=self.get_quality_color(metrics_data['quality_factor'])
        )
        quality_metric.grid(row=0, column=2, padx=5, sticky='ew')
        
        # Métrique 4: Statut global
        status_metric = StatusCard(
            parent,
            title="Statut Global",
            value=metrics_data['global_status'],
            icon="✅" if metrics_data['global_status'] == "OK" else "⚠️",
            color=AppTheme.COLORS['success'] if metrics_data['global_status'] == "OK" else AppTheme.COLORS['warning']
        )
        status_metric.grid(row=0, column=3, padx=(10, 0), sticky='ew')
    
    def calculate_visualization_metrics(self) -> Dict[str, Any]:
        """Calcule les métriques de visualisation."""
        
        # En mode démo, générer des données
        np.random.seed(42)
        
        points_count = 45
        errors = np.random.normal(0, 1.2, points_count)  # Erreurs en mm
        rms_error = np.sqrt(np.mean(errors**2))
        
        # Facteur qualité basé sur RMS et distribution
        quality_factor = max(0.1, 10 - rms_error)
        global_status = "OK" if rms_error < 2.0 and quality_factor > 7.0 else "ATTENTION"
        
        return {
            'points_count': points_count,
            'rms_error': rms_error,
            'quality_factor': quality_factor,
            'global_status': global_status,
            'errors': errors
        }
    
    def get_quality_color(self, quality: float) -> str:
        """Détermine la couleur selon la qualité."""
        if quality >= 8.0:
            return AppTheme.COLORS['success']
        elif quality >= 6.0:
            return AppTheme.COLORS['warning']
        else:
            return AppTheme.COLORS['error']
    
    def create_altitude_profile(self):
        """Crée le profil altimétrique moderne."""
        
        # Nettoyer le canvas précédent
        self.clear_canvas()
        
        # Créer la figure avec style moderne
        self.fig = Figure(figsize=(12, 6), dpi=100, facecolor=AppTheme.COLORS['background'])
        ax = self.fig.add_subplot(111)
        
        # Données d'exemple (en production: données réelles du projet)
        distances = np.array([0, 250, 550, 825, 1250])
        altitudes_brutes = np.array([125.456, 125.701, 125.578, 125.665, 125.821])
        altitudes_compensees = altitudes_brutes + np.random.normal(0, 0.001, len(altitudes_brutes))
        points = ['RN001', 'P001', 'P002', 'P003', 'RN002']
        
        # Zone de tolérance ±2mm
        tolerance_upper = altitudes_compensees + 0.002
        tolerance_lower = altitudes_compensees - 0.002
        ax.fill_between(distances, tolerance_lower, tolerance_upper, 
                       alpha=0.2, color=AppTheme.COLORS['success'], 
                       label='Zone de précision ±2mm')
        
        # Profil avant compensation
        ax.plot(distances, altitudes_brutes, 'o--', 
               color=AppTheme.COLORS['text_secondary'], 
               linewidth=2, markersize=8, alpha=0.7,
               label='Avant compensation')
        
        # Profil après compensation
        ax.plot(distances, altitudes_compensees, 'o-', 
               color=AppTheme.COLORS['primary'], 
               linewidth=3, markersize=10,
               label='Après compensation LSQ')
        
        # Points de contrôle spéciaux
        rn_indices = [0, 4]  # Repères de nivellement
        ax.scatter(distances[rn_indices], altitudes_compensees[rn_indices], 
                  s=200, marker='s', color=AppTheme.COLORS['accent'],
                  edgecolor='white', linewidth=2, zorder=5,
                  label='Repères de nivellement')
        
        # Annotations des points
        for i, (point, x, y) in enumerate(zip(points, distances, altitudes_compensees)):
            offset = 15 if i % 2 == 0 else -25
            ax.annotate(f'{point}\n{y:.3f}m', 
                       (x, y), xytext=(0, offset), 
                       textcoords='offset points', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='white', alpha=0.8,
                               edgecolor=AppTheme.COLORS['border']),
                       fontsize=9, color=AppTheme.COLORS['text'])
        
        # Configuration des axes
        ax.set_xlabel('Distance cumulative (m)', fontsize=12, color=AppTheme.COLORS['text'])
        ax.set_ylabel('Altitude (m)', fontsize=12, color=AppTheme.COLORS['text'])
        ax.set_title('📈 Profil Altimétrique - Compensation par Moindres Carrés\nPrécision: ±2mm • Méthode: LSQ • Qualité: Excellente', 
                    fontsize=14, color=AppTheme.COLORS['text'], pad=20)
        
        # Grille moderne
        ax.grid(True, alpha=0.3, color=AppTheme.COLORS['border_light'])
        ax.set_axisbelow(True)
        
        # Légende avec style
        legend = ax.legend(loc='upper right', fancybox=True, shadow=True, 
                          frameon=True, facecolor='white', edgecolor=AppTheme.COLORS['border'])
        legend.get_frame().set_alpha(0.9)
        
        # Couleurs des axes
        ax.spines['bottom'].set_color(AppTheme.COLORS['border'])
        ax.spines['top'].set_color(AppTheme.COLORS['border'])
        ax.spines['left'].set_color(AppTheme.COLORS['border'])
        ax.spines['right'].set_color(AppTheme.COLORS['border'])
        ax.tick_params(colors=AppTheme.COLORS['text_secondary'])
        
        # Intégrer dans l'interface
        self.integrate_matplotlib_canvas()
    
    def create_closure_analysis(self):
        """Crée l'analyse de fermeture moderne."""
        
        self.clear_canvas()
        
        # Figure avec sous-graphiques
        self.fig = Figure(figsize=(12, 8), dpi=100, facecolor=AppTheme.COLORS['background'])
        
        # Disposition 2x2
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Erreur de fermeture
        ax1 = self.fig.add_subplot(gs[0, 0])
        closure_error = 2.5  # mm
        tolerance = 4.8
        
        bars = ax1.bar(['Erreur mesurée', 'Tolérance'], 
                      [closure_error, tolerance],
                      color=[AppTheme.COLORS['warning'], AppTheme.COLORS['success']], 
                      alpha=0.8)
        ax1.set_ylabel('Erreur (mm)')
        ax1.set_title('🎯 Erreur de Fermeture', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Annotations
        for bar, value in zip(bars, [closure_error, tolerance]):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{value:.1f} mm', ha='center', fontweight='bold')
        
        # 2. Distribution des résidus
        ax2 = self.fig.add_subplot(gs[0, 1])
        residuals = np.random.normal(0, 0.8, 100)
        ax2.hist(residuals, bins=20, color=AppTheme.COLORS['primary'], 
                alpha=0.7, edgecolor='black')
        ax2.axvline(x=0, color=AppTheme.COLORS['error'], 
                   linestyle='--', linewidth=2, label='Référence')
        ax2.set_xlabel('Résidus (mm)')
        ax2.set_ylabel('Fréquence')
        ax2.set_title('📊 Distribution des Résidus', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # 3. Statistiques LSQ
        ax3 = self.fig.add_subplot(gs[1, 0])
        stats_labels = ['σ₀ (mm)', 'DDL', 'Test χ²']
        stats_values = [1.12, 4, 'OK']
        colors_stats = [AppTheme.COLORS['success'], AppTheme.COLORS['primary'], AppTheme.COLORS['success']]
        
        bars = ax3.bar(stats_labels, [1.12, 4, 1], color=colors_stats, alpha=0.8)
        ax3.set_ylabel('Valeurs')
        ax3.set_title('⚙️ Statistiques LSQ', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # 4. Qualité par point
        ax4 = self.fig.add_subplot(gs[1, 1])
        quality_points = ['RN001', 'P001', 'P002', 'P003', 'RN002']
        quality_values = [0.8, 1.2, 0.9, 1.1, 0.6]
        
        bars = ax4.bar(quality_points, quality_values, 
                      color=AppTheme.COLORS['accent'], alpha=0.8)
        ax4.axhline(y=1.0, color=AppTheme.COLORS['error'], 
                   linestyle='--', linewidth=2, label='Seuil qualité')
        ax4.set_ylabel('Indicateur qualité (mm)')
        ax4.set_title('🏆 Qualité par Point', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        # Titre général
        self.fig.suptitle('🧮 Analyse de Fermeture Complète\nSystème de Compensation Altimétrique', 
                         fontsize=16, color=AppTheme.COLORS['text'], y=0.95)
        
        self.integrate_matplotlib_canvas()
    
    def create_compensation_diagnostics(self):
        """Crée les diagnostics de compensation."""
        
        self.clear_canvas()
        
        self.fig = Figure(figsize=(12, 10), dpi=100, facecolor=AppTheme.COLORS['background'])
        
        # Disposition 3x2
        gs = self.fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
        
        # 1. Évolution des corrections
        ax1 = self.fig.add_subplot(gs[0, :])  # Span sur 2 colonnes
        points = np.arange(1, 6)
        corrections = np.array([-0.0012, 0.0008, -0.0015, 0.0021, -0.0005]) * 1000  # en mm
        
        bars = ax1.bar(points, corrections, color=AppTheme.COLORS['primary'], alpha=0.7)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.set_xlabel('Points de mesure')
        ax1.set_ylabel('Corrections (mm)')
        ax1.set_title('🔧 Corrections Appliquées par Point', fontweight='bold', pad=20)
        ax1.grid(True, alpha=0.3)
        
        # Coloration selon le seuil
        for bar, correction in zip(bars, corrections):
            if abs(correction) > 1.5:  # Seuil d'alerte
                bar.set_color(AppTheme.COLORS['warning'])
        
        # 2. Matrice de poids
        ax2 = self.fig.add_subplot(gs[1, 0])
        weights_matrix = np.random.exponential(2, (5, 5))
        np.fill_diagonal(weights_matrix, 5)  # Poids diagonaux plus élevés
        
        im = ax2.imshow(weights_matrix, cmap='Blues', aspect='auto')
        ax2.set_title('⚖️ Matrice des Poids', fontweight='bold')
        ax2.set_xlabel('Points j')
        ax2.set_ylabel('Points i')
        
        # Ajouter la barre de couleur
        cbar = self.fig.colorbar(im, ax=ax2)
        cbar.set_label('Poids relatifs')
        
        # 3. Convergence LSQ
        ax3 = self.fig.add_subplot(gs[1, 1])
        iterations = np.arange(1, 11)
        precision = 3.5 * np.exp(-iterations/3) + 0.8
        
        ax3.plot(iterations, precision, 'o-', color=AppTheme.COLORS['secondary'], 
                linewidth=2, markersize=6)
        ax3.axhline(y=2.0, color=AppTheme.COLORS['success'], 
                   linestyle='--', linewidth=2, label='Objectif 2mm')
        ax3.set_xlabel('Itération')
        ax3.set_ylabel('Précision (mm)')
        ax3.set_title('📈 Convergence LSQ', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # 4. Analyse des résidus normalisés
        ax4 = self.fig.add_subplot(gs[2, 0])
        residuals_norm = np.random.normal(0, 1, 100)
        
        # Q-Q plot simplifié
        sorted_residuals = np.sort(residuals_norm)
        theoretical_quantiles = np.linspace(-2.5, 2.5, len(sorted_residuals))
        
        ax4.scatter(theoretical_quantiles, sorted_residuals, 
                   color=AppTheme.COLORS['primary'], alpha=0.6)
        ax4.plot([-2.5, 2.5], [-2.5, 2.5], 'r--', linewidth=2, label='Distribution normale')
        ax4.set_xlabel('Quantiles théoriques')
        ax4.set_ylabel('Résidus observés')
        ax4.set_title('📉 Q-Q Plot Résidus', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # 5. Facteurs de variance
        ax5 = self.fig.add_subplot(gs[2, 1])
        variance_factors = np.array([1.2, 0.8, 1.5, 0.9, 1.1])
        point_names = ['RN001', 'P001', 'P002', 'P003', 'RN002']
        
        bars = ax5.bar(point_names, variance_factors, 
                      color=AppTheme.COLORS['accent'], alpha=0.8)
        ax5.axhline(y=1.0, color=AppTheme.COLORS['text'], 
                   linestyle='--', linewidth=2, alpha=0.5)
        ax5.set_ylabel('Facteur de variance')
        ax5.set_title('🎲 Facteurs de Variance', fontweight='bold')
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Titre général
        self.fig.suptitle('🔍 Diagnostics Avancés de Compensation\nAnalyse Statistique Complète', 
                         fontsize=16, color=AppTheme.COLORS['text'], y=0.98)
        
        self.integrate_matplotlib_canvas()
    
    def create_heatmap_residuals(self):
        """Crée la carte de chaleur des résidus."""
        
        self.clear_canvas()
        
        self.fig = Figure(figsize=(10, 8), dpi=100, facecolor=AppTheme.COLORS['background'])
        ax = self.fig.add_subplot(111)
        
        # Générer des données de résidus 2D
        x = np.linspace(0, 1000, 20)
        y = np.linspace(100, 200, 15)
        X, Y = np.meshgrid(x, y)
        
        # Résidus simulés avec pattern géographique
        Z = (np.sin(X/200) * np.cos(Y/50) + 
             np.random.normal(0, 0.3, X.shape)) * 2  # En mm
        
        # Carte de chaleur
        im = ax.imshow(Z, cmap='RdYlBu_r', aspect='auto', 
                      extent=[x.min(), x.max(), y.min(), y.max()])
        
        # Contours pour plus de lisibilité
        contours = ax.contour(X, Y, Z, levels=10, colors='black', alpha=0.3, linewidths=0.5)
        ax.clabel(contours, inline=True, fontsize=8)
        
        # Configuration
        ax.set_xlabel('Distance Est (m)')
        ax.set_ylabel('Distance Nord (m)')
        ax.set_title('🗺️ Carte de Chaleur des Résidus\nDistribution Spatiale des Erreurs', 
                    fontsize=14, pad=20)
        
        # Barre de couleur
        cbar = self.fig.colorbar(im, ax=ax)
        cbar.set_label('Résidus (mm)')
        
        self.integrate_matplotlib_canvas()
    
    def clear_canvas(self):
        """Nettoie le canvas matplotlib."""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
    
    def integrate_matplotlib_canvas(self):
        """Intègre le canvas matplotlib dans l'interface."""
        
        # Créer le canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.matplotlib_frame)
        self.canvas.draw()
        
        # Widget tkinter du canvas
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)
        
        # Toolbar de navigation
        toolbar_frame = ctk.CTkFrame(self.matplotlib_frame, fg_color='transparent', height=40)
        toolbar_frame.pack(fill='x', pady=(0, 10))
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.config(bg=AppTheme.COLORS['surface'])
        self.toolbar.update()
    
    # Callbacks des contrôles
    def on_chart_type_changed(self, selection):
        """Gère le changement de type de graphique."""
        
        chart_methods = {
            "Profil Altimétrique": self.create_altitude_profile,
            "Analyse de Fermeture": self.create_closure_analysis,
            "Diagnostics Compensation": self.create_compensation_diagnostics,
            "Évolution Précision": self.create_precision_evolution,
            "Carte de Chaleur Résidus": self.create_heatmap_residuals,
            "Analyse Spectrale": self.create_spectral_analysis,
            "Comparaison Méthodes": self.create_methods_comparison,
            "Dashboard Qualité": self.create_quality_dashboard
        }
        
        method = chart_methods.get(selection)
        if method:
            method()
        else:
            messagebox.showinfo("Info", f"Graphique '{selection}' en cours de développement")
    
    def create_precision_evolution(self):
        """Graphique d'évolution de la précision."""
        messagebox.showinfo("Développement", "Évolution de la précision - En cours d'implémentation")
    
    def create_spectral_analysis(self):
        """Analyse spectrale des données."""
        messagebox.showinfo("Développement", "Analyse spectrale - En cours d'implémentation")
    
    def create_methods_comparison(self):
        """Comparaison des méthodes."""
        messagebox.showinfo("Développement", "Comparaison méthodes - En cours d'implémentation")
    
    def create_quality_dashboard(self):
        """Dashboard de qualité."""
        messagebox.showinfo("Développement", "Dashboard qualité - En cours d'implémentation")
    
    def refresh_visualization(self):
        """Actualise la visualisation."""
        current_chart = self.chart_type_var.get()
        self.on_chart_type_changed(current_chart)
    
    def export_visualization(self):
        """Exporte la visualisation."""
        if self.fig:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"), 
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ]
            )
            if filepath:
                self.fig.savefig(filepath, dpi=300, bbox_inches='tight',
                               facecolor=AppTheme.COLORS['background'])
                messagebox.showinfo("Export", f"Visualisation exportée vers :\n{filepath}")


class InteractiveVisualizationWindow(ctk.CTkToplevel):
    """Fenêtre dédiée aux visualisations interactives."""
    
    def __init__(self, parent, data=None):
        super().__init__(parent)
        
        self.data = data
        
        # Configuration de la fenêtre
        self.title("📊 Visualisations Interactives - Compensation Altimétrique")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Appliquer le thème
        self.configure(fg_color=AppTheme.COLORS['background'])
        
        # Centrer la fenêtre
        self.center_window()
        
        # Créer l'interface
        self.create_interface()
    
    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        
        self.geometry(f"1400x900+{x}+{y}")
    
    def create_interface(self):
        """Crée l'interface de la fenêtre."""
        
        # Panel de visualisation principal
        self.viz_panel = AdvancedVisualizationPanel(
            self,
            data=self.data
        )
        self.viz_panel.pack(fill='both', expand=True, padx=20, pady=20)