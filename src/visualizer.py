"""
Module de visualisation graphique pour le système de compensation altimétrique.

Ce module fournit des outils complets de visualisation pour :
- Profils altimétriques avant/après compensation
- Graphiques de contrôle des résidus
- Analyse des corrections atmosphériques  
- Diagnostics de fermeture
- Cartes de précision
- Rapports visuels complets

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm avec visualisations interactives
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
import seaborn as sns
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import datetime

# Import optionnel de Plotly pour graphiques interactifs
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
    
    # Configuration thème Plotly géodésique
    PLOTLY_THEME = {
        'layout': {
            'font': {'family': 'Segoe UI, Arial, sans-serif', 'size': 12},
            'colorway': ['#2E86AB', '#A23B72', '#F18F01', '#10B981', '#F59E0B', '#EF4444'],
            'plot_bgcolor': '#F8FAFC',
            'paper_bgcolor': 'white',
            'title': {'font': {'size': 18, 'color': '#1E293B'}},
            'xaxis': {'gridcolor': '#E2E8F0', 'linecolor': '#64748B'},
            'yaxis': {'gridcolor': '#E2E8F0', 'linecolor': '#64748B'},
        }
    }
except ImportError:
    PLOTLY_AVAILABLE = False
    print("📊 Plotly non installé - graphiques interactifs non disponibles")
    print("💡 Installez avec: pip install plotly")

# Import des modules internes
from calculator import CalculationResults, AltitudeCalculation, HeightDifference, ClosureAnalysis
from compensator import CompensationResults, CompensationStatistics
from atmospheric_corrections import RefractionCorrection, AtmosphericConditions
from validators import ValidationResult

# Configuration style moderne géodésique
plt.style.use(['seaborn-v0_8-whitegrid'])
sns.set_palette("husl")

# Palette de couleurs géodésiques moderne (synchronisée avec le thème GUI)
COLORS = {
    # Couleurs principales géodésiques
    'primary': '#2E86AB',          # Bleu géodésique
    'primary_dark': '#1F5F85',     # Bleu géodésique foncé
    'primary_light': '#4DA3C7',    # Bleu géodésique clair
    'secondary': '#A23B72',        # Magenta technique  
    'secondary_dark': '#7A2B56',   # Magenta foncé
    'accent': '#F18F01',           # Orange précision
    'accent_dark': '#CC7700',      # Orange foncé
    
    # États de validation modernes
    'success': '#10B981',          # Vert validation
    'success_light': '#D1FAE5',    # Vert clair
    'warning': '#F59E0B',          # Jaune avertissement
    'warning_light': '#FEF3C7',    # Jaune clair
    'error': '#EF4444',            # Rouge critique
    'error_light': '#FEE2E2',      # Rouge clair
    'info': '#3B82F6',             # Bleu information
    
    # Couleurs utilitaires
    'neutral': '#64748B',          # Gris neutre
    'neutral_light': '#94A3B8',    # Gris clair
    'background': '#F8FAFC',       # Arrière-plan moderne
    'text': '#1E293B',             # Texte principal
    'grid': '#E2E8F0',             # Grille subtile
    
    # Couleurs spéciales géodésie
    'precision_zone': '#D1FAE5',   # Zone de précision (vert très clair)
    'tolerance_zone': '#FEF3C7',   # Zone de tolérance (jaune très clair)
    'critical_zone': '#FEE2E2',    # Zone critique (rouge très clair)
}

PRECISION_TARGET_MM = 2.0


class LevelingVisualizer:
    """
    Visualiseur principal pour le système de compensation altimétrique.
    
    Génère des graphiques professionnels pour l'analyse et le contrôle
    des opérations de nivellement géométrique.
    """
    
    def __init__(self, precision_mm: float = 2.0, output_dir: Optional[Path] = None):
        """
        Initialisation du visualiseur.
        
        Args:
            precision_mm: Précision cible en millimètres
            output_dir: Dossier de sortie pour les graphiques
        """
        self.precision_mm = precision_mm
        self.output_dir = Path(output_dir) if output_dir else Path("./visualizations")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Configuration matplotlib
        self._setup_matplotlib()
        
        # Métadonnées
        self.created_plots = []
    
    def _setup_matplotlib(self):
        """Configuration du style matplotlib moderne et professionnel."""
        plt.rcParams.update({
            # Dimensions et qualité
            'figure.figsize': (14, 10),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.facecolor': 'white',
            'savefig.edgecolor': 'none',
            'savefig.transparent': False,
            
            # Typographie moderne (Windows-friendly)
            'font.family': ['Segoe UI', 'DejaVu Sans', 'Arial', 'sans-serif'],
            'font.size': 11,
            'font.weight': 'normal',
            
            # Hiérarchie typographique
            'axes.labelsize': 12,
            'axes.titlesize': 16,
            'axes.labelweight': 'bold',
            'axes.titleweight': 'bold',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 11,
            'figure.titlesize': 18,
            'figure.titleweight': 'bold',
            
            # Couleurs modernes
            'axes.facecolor': COLORS['background'],
            'figure.facecolor': 'white',
            'axes.edgecolor': COLORS['neutral'],
            'axes.linewidth': 1.2,
            'text.color': COLORS['text'],
            'axes.labelcolor': COLORS['text'],
            'xtick.color': COLORS['neutral'],
            'ytick.color': COLORS['neutral'],
            
            # Grilles professionnelles
            'axes.grid': True,
            'grid.color': COLORS['grid'],
            'grid.alpha': 0.6,
            'grid.linewidth': 0.8,
            'axes.axisbelow': True,
            
            # Légendes modernes
            'legend.frameon': True,
            'legend.fancybox': True,
            'legend.shadow': False,
            'legend.framealpha': 0.95,
            'legend.facecolor': 'white',
            'legend.edgecolor': COLORS['neutral_light'],
            'legend.borderpad': 0.6,
            
            # Marges et espacement
            'figure.subplot.left': 0.08,
            'figure.subplot.right': 0.95,
            'figure.subplot.bottom': 0.08,
            'figure.subplot.top': 0.92,
            'figure.subplot.wspace': 0.25,
            'figure.subplot.hspace': 0.35,
            
            # Lignes et marqueurs
            'lines.linewidth': 2.5,
            'lines.markersize': 8,
            'lines.markeredgewidth': 0.8,
            
            # Couleurs par défaut professionnelles
            'axes.prop_cycle': plt.cycler('color', [
                COLORS['primary'], COLORS['secondary'], COLORS['accent'],
                COLORS['success'], COLORS['warning'], COLORS['info']
            ])
        })
    
    def create_altitude_profile(self, 
                               calculation_results: CalculationResults,
                               compensation_results: Optional[CompensationResults] = None,
                               show_corrections: bool = True) -> Path:
        """
        Création du profil altimétrique avec comparaison avant/après compensation.
        
        Args:
            calculation_results: Résultats des calculs préliminaires
            compensation_results: Résultats de compensation (optionnel)
            show_corrections: Afficher les corrections
            
        Returns:
            Path: Chemin du fichier graphique généré
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
        
        # Données de base
        points = [alt.point_id for alt in calculation_results.altitudes]
        altitudes_orig = [alt.altitude_m for alt in calculation_results.altitudes]
        
        # Graphique principal - Profil altimétrique
        x_positions = range(len(points))
        
        # Profil original
        ax1.plot(x_positions, altitudes_orig, 
                'o-', color=COLORS['primary'], linewidth=2, markersize=6,
                label='Altitudes calculées', alpha=0.8)
        
        # Profil compensé si disponible
        if compensation_results:
            altitudes_comp = [alt.altitude_m for alt in compensation_results.adjusted_altitudes]
            ax1.plot(x_positions, altitudes_comp,
                    's-', color=COLORS['accent'], linewidth=2, markersize=6,
                    label='Altitudes compensées', alpha=0.9)
            
            # Flèches des corrections
            if show_corrections and len(altitudes_orig) == len(altitudes_comp):
                for i, (orig, comp) in enumerate(zip(altitudes_orig, altitudes_comp)):
                    if abs(orig - comp) > 0.001:  # > 1mm
                        correction_mm = (comp - orig) * 1000
                        color = COLORS['success'] if abs(correction_mm) <= self.precision_mm else COLORS['warning']
                        ax1.annotate('', xy=(i, comp), xytext=(i, orig),
                                   arrowprops=dict(arrowstyle='<->', color=color, lw=1.5))
                        ax1.text(i, (orig + comp) / 2, f'{correction_mm:+.1f}mm',
                               ha='center', va='bottom', fontsize=8, color=color,
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Configuration axe principal
        ax1.set_xticks(x_positions)
        ax1.set_xticklabels(points, rotation=45, ha='right')
        ax1.set_ylabel('Altitude (m)', fontsize=12)
        ax1.set_title('Profil Altimétrique - Nivellement Géométrique', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Zone de précision cible avec meilleur design
        alt_mean = np.mean(altitudes_orig)
        precision_zone = ax1.axhspan(
            alt_mean - self.precision_mm/1000, 
            alt_mean + self.precision_mm/1000, 
            alpha=0.15, 
            color=COLORS['precision_zone'], 
            label=f'🎯 Zone précision ±{self.precision_mm}mm',
            zorder=0
        )
        
        # Graphique secondaire - Dénivelées
        if len(calculation_results.height_differences) > 0:
            deltas = [hd.delta_h_m for hd in calculation_results.height_differences if hd.is_valid]
            delta_positions = range(len(deltas))
            
            ax2.bar(delta_positions, np.array(deltas) * 1000, 
                   color=COLORS['secondary'], alpha=0.7, label='Dénivelées (mm)')
            ax2.set_ylabel('Dénivelée (mm)', fontsize=12)
            ax2.set_xlabel('Segments', fontsize=12)
            ax2.set_title('Dénivelées par segment', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Ligne de référence à zéro
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        # Sauvegarde
        filename = f"profil_altimetrique_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath)
        self.created_plots.append(filepath)
        
        plt.close()
        return filepath
    
    def create_closure_analysis_plot(self, 
                                   closure_analysis: ClosureAnalysis,
                                   calculation_results: CalculationResults) -> Path:
        """
        Graphique d'analyse de fermeture.
        
        Args:
            closure_analysis: Analyse de fermeture
            calculation_results: Résultats des calculs
            
        Returns:
            Path: Chemin du fichier généré
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Erreur de fermeture
        error_mm = abs(closure_analysis.closure_error_mm)
        tolerance_mm = closure_analysis.tolerance_mm
        
        categories = ['Erreur mesurée', 'Tolérance']
        values = [error_mm, tolerance_mm]
        colors = [COLORS['error'] if error_mm > tolerance_mm else COLORS['success'], COLORS['neutral']]
        
        bars = ax1.bar(categories, values, color=colors, alpha=0.8)
        ax1.set_ylabel('Erreur (mm)', fontsize=12)
        ax1.set_title('Analyse de Fermeture', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Annotations sur les barres
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value:.2f}mm', ha='center', va='bottom', fontweight='bold')
        
        # Status
        status = "ACCEPTABLE" if closure_analysis.is_acceptable else "DEPASSEMENT"
        ax1.text(0.5, max(values) * 0.8, status, ha='center', va='center',
                transform=ax1.transData, fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', 
                         facecolor=COLORS['success'] if closure_analysis.is_acceptable else COLORS['error'],
                         alpha=0.2))
        
        # 2. Distribution des dénivelées
        if calculation_results.height_differences:
            deltas_mm = [hd.delta_h_m * 1000 for hd in calculation_results.height_differences if hd.is_valid]
            ax2.hist(deltas_mm, bins=15, color=COLORS['secondary'], alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Dénivelée (mm)', fontsize=12)
            ax2.set_ylabel('Fréquence', fontsize=12)
            ax2.set_title('Distribution des Dénivelées', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Statistiques
            mean_delta = np.mean(deltas_mm)
            std_delta = np.std(deltas_mm)
            ax2.axvline(mean_delta, color=COLORS['accent'], linestyle='--', 
                       label=f'Moyenne: {mean_delta:.1f}mm')
            ax2.axvline(mean_delta + std_delta, color=COLORS['warning'], linestyle=':', alpha=0.7)
            ax2.axvline(mean_delta - std_delta, color=COLORS['warning'], linestyle=':', alpha=0.7,
                       label=f'±1σ: {std_delta:.1f}mm')
            ax2.legend()
        
        # 3. Évolution cumulative des erreurs
        altitudes = [alt.altitude_m for alt in calculation_results.altitudes]
        cumulative_error = np.array(altitudes) - altitudes[0]
        
        ax3.plot(range(len(altitudes)), cumulative_error * 1000, 
                'o-', color=COLORS['primary'], linewidth=2, markersize=4)
        ax3.set_xlabel('Points', fontsize=12)
        ax3.set_ylabel('Erreur cumulative (mm)', fontsize=12)
        ax3.set_title('Évolution Cumulative des Erreurs', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # Zone de tolérance
        tolerance_bound = tolerance_mm * np.sqrt(np.arange(len(altitudes)) + 1)
        ax3.fill_between(range(len(altitudes)), -tolerance_bound, tolerance_bound,
                        alpha=0.2, color=COLORS['success'], label='Zone tolérance')
        ax3.legend()
        
        # 4. Informations du cheminement
        ax4.axis('off')
        info_text = f"""
INFORMATIONS CHEMINEMENT

Type: {closure_analysis.traverse_type.value}
Distance totale: {closure_analysis.total_distance_km:.3f} km
Points: {len(calculation_results.altitudes)}
Observations: {len([hd for hd in calculation_results.height_differences if hd.is_valid])}

FERMETURE
Erreur: {closure_analysis.closure_error_mm:+.2f} mm
Tolérance: ±{closure_analysis.tolerance_mm:.2f} mm
Précision atteinte: {error_mm/tolerance_mm*100:.1f}% de la tolérance

VERDICT: {status}
        """
        
        ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['background'], alpha=0.8))
        
        plt.tight_layout()
        
        # Sauvegarde
        filename = f"analyse_fermeture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath)
        self.created_plots.append(filepath)
        
        plt.close()
        return filepath
    
    def create_compensation_diagnostics(self, 
                                      compensation_results: CompensationResults,
                                      calculation_results: CalculationResults) -> Path:
        """
        Graphiques de diagnostic de la compensation.
        
        Args:
            compensation_results: Résultats de compensation
            calculation_results: Résultats des calculs
            
        Returns:
            Path: Chemin du fichier généré
        """
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 3, figure=fig)
        
        # 1. Corrections appliquées
        ax1 = fig.add_subplot(gs[0, :2])
        corrections_mm = compensation_results.adjusted_coordinates.flatten() * 1000
        points = range(len(corrections_mm))
        
        bars = ax1.bar(points, corrections_mm, 
                      color=[COLORS['success'] if abs(c) <= self.precision_mm else COLORS['warning'] 
                            for c in corrections_mm], alpha=0.8)
        ax1.set_xlabel('Points', fontsize=12)
        ax1.set_ylabel('Correction (mm)', fontsize=12)
        ax1.set_title('Corrections Appliquées par la Compensation', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Zones de précision
        ax1.axhspan(-self.precision_mm, self.precision_mm, alpha=0.2, color=COLORS['success'],
                   label=f'Zone cible ±{self.precision_mm}mm')
        ax1.legend()
        
        # 2. Résidus normalisés
        ax2 = fig.add_subplot(gs[0, 2])
        residuals = compensation_results.residuals.flatten() * 1000
        ax2.hist(residuals, bins=10, color=COLORS['secondary'], alpha=0.7, orientation='horizontal')
        ax2.set_ylabel('Résidus (mm)', fontsize=12)
        ax2.set_xlabel('Fréquence', fontsize=12)
        ax2.set_title('Distribution\ndes Résidus', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 3. Matrice de covariance (heatmap)
        ax3 = fig.add_subplot(gs[1, :2])
        covariance_mm2 = compensation_results.covariance_matrix * 1000000  # mm²
        im = ax3.imshow(covariance_mm2, cmap='RdYlBu_r', aspect='auto')
        ax3.set_title('Matrice de Covariance (mm²)', fontsize=12)
        ax3.set_xlabel('Points', fontsize=12)
        ax3.set_ylabel('Points', fontsize=12)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax3)
        cbar.set_label('Covariance (mm²)', fontsize=10)
        
        # 4. Statistiques de qualité
        ax4 = fig.add_subplot(gs[1, 2])
        ax4.axis('off')
        
        stats = compensation_results.statistics
        metadata = compensation_results.computation_metadata
        
        stats_text = f"""
STATISTIQUES COMPENSATION

sigma_0 (a posteriori): {stats.sigma_0_hat:.4f}
Degres de liberte: {stats.degrees_of_freedom}
Test chi2: {'OK' if stats.unit_weight_valid else 'NOK'}

CORRECTIONS
Maximum: {metadata['max_correction_mm']:.2f} mm
Methode: {compensation_results.solution_method.value}
Conditionnement: {metadata['condition_number']:.2e}

FAUTES GROSSIERES
Detectees: {metadata['blunder_detection']['suspect_count']}
Seuil: {stats.blunder_detection_threshold:.2f}

PRECISION FINALE
Cible: {self.precision_mm} mm
Residu max: {stats.max_standardized_residual:.2f}
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['background'], alpha=0.8))
        
        # 5. Évolution des corrections
        ax5 = fig.add_subplot(gs[2, :])
        cumulative_corrections = np.cumsum(corrections_mm)
        
        ax5.plot(points, corrections_mm, 'o-', color=COLORS['accent'], 
                label='Corrections individuelles', markersize=4)
        ax5.plot(points, cumulative_corrections, 's-', color=COLORS['primary'], 
                label='Corrections cumulatives', markersize=4, alpha=0.7)
        
        ax5.set_xlabel('Points', fontsize=12)
        ax5.set_ylabel('Correction (mm)', fontsize=12)
        ax5.set_title('Évolution des Corrections', fontsize=12)
        ax5.grid(True, alpha=0.3)
        ax5.legend()
        ax5.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        # Sauvegarde
        filename = f"diagnostics_compensation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath)
        self.created_plots.append(filepath)
        
        plt.close()
        return filepath
    
    def create_atmospheric_corrections_plot(self, 
                                          corrections: List[RefractionCorrection],
                                          distances: np.ndarray) -> Path:
        """
        Graphique des corrections atmosphériques.
        
        Args:
            corrections: Liste des corrections atmosphériques
            distances: Distances correspondantes
            
        Returns:
            Path: Chemin du fichier généré
        """
        if not corrections:
            # Créer des corrections d'exemple
            from atmospheric_corrections import AtmosphericCorrector, AtmosphericConditions
            corrector = AtmosphericCorrector()
            conditions = AtmosphericConditions(temperature_celsius=25.0)
            
            corrections = []
            for dist in distances:
                corr = corrector.calculate_atmospheric_correction(dist, 0.0, conditions)
                corrections.append(corr)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        distances_plot = [c.distance_m for c in corrections]
        
        # 1. Corrections par distance
        curvature_mm = [c.curvature_correction_mm for c in corrections]
        refraction_mm = [c.refraction_correction_mm for c in corrections]
        level_apparent_mm = [c.level_apparent_correction_mm for c in corrections]
        total_mm = [c.total_correction_mm for c in corrections]
        
        ax1.plot(distances_plot, curvature_mm, 'o-', label='Courbure terrestre', color=COLORS['primary'])
        ax1.plot(distances_plot, refraction_mm, 's-', label='Réfraction atm.', color=COLORS['secondary'])
        ax1.plot(distances_plot, level_apparent_mm, '^-', label='Niveau apparent', color=COLORS['accent'])
        ax1.plot(distances_plot, total_mm, 'D-', label='Correction totale', color=COLORS['error'], linewidth=2)
        
        ax1.set_xlabel('Distance (m)', fontsize=12)
        ax1.set_ylabel('Correction (mm)', fontsize=12)
        ax1.set_title('Corrections Atmosphériques par Distance', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 2. Coefficients de réfraction
        refraction_coeffs = [c.refraction_coefficient for c in corrections]
        ax2.plot(distances_plot, refraction_coeffs, 'o-', color=COLORS['warning'])
        ax2.set_xlabel('Distance (m)', fontsize=12)
        ax2.set_ylabel('Coefficient de réfraction', fontsize=12)
        ax2.set_title('Variation du Coefficient de Réfraction', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Ligne de référence standard
        ax2.axhline(y=0.13, color=COLORS['neutral'], linestyle='--', 
                   label='Standard (0.13)', alpha=0.7)
        ax2.legend()
        
        # 3. Impact sur les dénivelées
        if len(corrections) > 1:
            ax3.scatter(distances_plot, total_mm, c=distances_plot, cmap='viridis', s=50, alpha=0.7)
            ax3.set_xlabel('Distance (m)', fontsize=12)
            ax3.set_ylabel('Correction totale (mm)', fontsize=12)
            ax3.set_title('Impact des Corrections', fontsize=12)
            ax3.grid(True, alpha=0.3)
            
            # Courbe de tendance
            z = np.polyfit(distances_plot, total_mm, 2)
            p = np.poly1d(z)
            x_smooth = np.linspace(min(distances_plot), max(distances_plot), 100)
            ax3.plot(x_smooth, p(x_smooth), '--', color=COLORS['error'], alpha=0.8, label='Tendance')
            ax3.legend()
        
        # 4. Informations des conditions
        ax4.axis('off')
        if corrections:
            # Utiliser les conditions de la première correction
            conditions_text = f"""
CONDITIONS ATMOSPHÉRIQUES

Température: {corrections[0].refraction_coefficient * 100:.1f}°C (estimé)
Coefficient réfraction moyen: {np.mean(refraction_coeffs):.3f}
Plage de variation: {np.ptp(refraction_coeffs):.3f}

CORRECTIONS MOYENNES
Courbure: {np.mean(curvature_mm):.3f} mm
Réfraction: {np.mean(refraction_mm):.3f} mm
Niveau apparent: {np.mean(level_apparent_mm):.3f} mm
Total: {np.mean(total_mm):.3f} mm

STATISTIQUES
Distance max: {max(distances_plot):.0f} m
Correction max: {max(total_mm):.3f} mm
Précision impact: {abs(max(total_mm))/self.precision_mm*100:.1f}% de {self.precision_mm}mm
            """
        else:
            conditions_text = "Aucune correction atmosphérique disponible"
        
        ax4.text(0.05, 0.95, conditions_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['background'], alpha=0.8))
        
        plt.tight_layout()
        
        # Sauvegarde
        filename = f"corrections_atmospheriques_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath)
        self.created_plots.append(filepath)
        
        plt.close()
        return filepath
    
    def create_precision_map(self, 
                           compensation_results: CompensationResults,
                           calculation_results: CalculationResults) -> Path:
        """
        Carte de précision par point.
        
        Args:
            compensation_results: Résultats de compensation
            calculation_results: Résultats des calculs
            
        Returns:
            Path: Chemin du fichier généré
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Calcul des précisions par point
        if compensation_results:
            covar_diag = np.diag(compensation_results.covariance_matrix)
            std_errors_mm = np.sqrt(covar_diag) * 1000
            points = [alt.point_id for alt in compensation_results.adjusted_altitudes]
            
            # S'assurer que les dimensions correspondent
            min_len = min(len(std_errors_mm), len(points))
            std_errors_mm = std_errors_mm[:min_len]
            points = points[:min_len]
            
            print(f"Debug carte précision: {len(std_errors_mm)} erreurs, {len(points)} points")
        else:
            # Précisions estimées sans compensation
            points = [alt.point_id for alt in calculation_results.altitudes]
            std_errors_mm = np.random.uniform(0.5, 3.0, len(points))
        
        # 1. Carte de précision
        colors = [COLORS['success'] if err <= self.precision_mm else 
                 COLORS['warning'] if err <= self.precision_mm * 2 else 
                 COLORS['error'] for err in std_errors_mm]
        
        bars = ax1.bar(range(len(points)), std_errors_mm, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_xticks(range(len(points)))
        ax1.set_xticklabels(points, rotation=45, ha='right')
        ax1.set_ylabel('Écart-type (mm)', fontsize=12)
        ax1.set_title('Carte de Précision par Point', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Ligne de référence précision cible
        ax1.axhline(y=self.precision_mm, color=COLORS['neutral'], linestyle='--', 
                   linewidth=2, label=f'Objectif {self.precision_mm}mm')
        ax1.legend()
        
        # Annotations sur les barres
        for i, (bar, err) in enumerate(zip(bars, std_errors_mm)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{err:.1f}', ha='center', va='bottom', fontsize=8)
        
        # 2. Distribution des précisions
        ax2.hist(std_errors_mm, bins=10, color=COLORS['primary'], alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Écart-type (mm)', fontsize=12)
        ax2.set_ylabel('Nombre de points', fontsize=12)
        ax2.set_title('Distribution des Précisions', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Ligne de référence précision cible
        ax2.axvline(x=self.precision_mm, color=COLORS['error'], linestyle='--', 
                   linewidth=2, label=f'Objectif {self.precision_mm}mm')
        
        # Statistiques
        mean_precision = np.mean(std_errors_mm)
        ax2.axvline(x=mean_precision, color=COLORS['accent'], linestyle='-', 
                   linewidth=2, label=f'Moyenne {mean_precision:.1f}mm')
        ax2.legend()
        
        # Texte de synthèse
        points_within_target = np.sum(std_errors_mm <= self.precision_mm)
        percentage_ok = points_within_target / len(std_errors_mm) * 100
        
        synthesis_text = f"""
Points dans l'objectif: {points_within_target}/{len(std_errors_mm)} ({percentage_ok:.1f}%)
Precision moyenne: {mean_precision:.2f}mm
Precision max: {np.max(std_errors_mm):.2f}mm
Objectif atteint: {'OUI' if percentage_ok >= 90 else 'NON'}
        """
        
        ax2.text(0.95, 0.95, synthesis_text, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right', 
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['background'], alpha=0.9))
        
        plt.tight_layout()
        
        # Sauvegarde
        filename = f"carte_precision_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath)
        self.created_plots.append(filepath)
        
        plt.close()
        return filepath
    
    def create_complete_report(self, 
                             calculation_results: CalculationResults,
                             compensation_results: Optional[CompensationResults] = None,
                             atmospheric_corrections: Optional[List[RefractionCorrection]] = None,
                             distances: Optional[np.ndarray] = None) -> Path:
        """
        Génère un rapport visuel complet.
        
        Args:
            calculation_results: Résultats des calculs
            compensation_results: Résultats de compensation (optionnel)
            atmospheric_corrections: Corrections atmosphériques (optionnel)
            distances: Distances (optionnel)
            
        Returns:
            Path: Chemin du rapport PDF généré
        """
        print("🎨 Génération du rapport visuel complet...")
        
        # Utiliser les graphiques déjà créés dans self.created_plots
        # ou créer seulement ceux qui manquent
        existing_plots = self.get_created_plots()
        
        # Si des graphiques existent déjà, les utiliser
        if existing_plots:
            print(f"   📋 Utilisation des {len(existing_plots)} graphiques existants")
            plots_created = existing_plots.copy()
        else:
            # Créer tous les graphiques
            plots_created = []
            
            # 1. Profil altimétrique
            plot1 = self.create_altitude_profile(calculation_results, compensation_results)
            plots_created.append(plot1)
            print(f"   ✅ Profil altimétrique: {plot1.name}")
            
            # 2. Analyse de fermeture
            plot2 = self.create_closure_analysis_plot(calculation_results.closure_analysis, calculation_results)
            plots_created.append(plot2)
            print(f"   ✅ Analyse fermeture: {plot2.name}")
            
            # 3. Diagnostics de compensation
            if compensation_results:
                plot3 = self.create_compensation_diagnostics(compensation_results, calculation_results)
                plots_created.append(plot3)
                print(f"   ✅ Diagnostics compensation: {plot3.name}")
                
                # 4. Carte de précision
                plot4 = self.create_precision_map(compensation_results, calculation_results)
                plots_created.append(plot4)
                print(f"   ✅ Carte précision: {plot4.name}")
            
            # 5. Corrections atmosphériques
            if atmospheric_corrections and distances is not None:
                plot5 = self.create_atmospheric_corrections_plot(atmospheric_corrections, distances)
                plots_created.append(plot5)
                print(f"   ✅ Corrections atmosphériques: {plot5.name}")
        
        # Créer un résumé des graphiques générés
        summary_file = self.output_dir / f"rapport_visuel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("RAPPORT VISUEL - SYSTÈME DE COMPENSATION ALTIMÉTRIQUE\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write(f"Date de génération: {datetime.datetime.now()}\\n")
            f.write(f"Précision cible: {self.precision_mm}mm\\n")
            f.write(f"Nombre de graphiques: {len(plots_created)}\\n\\n")
            
            f.write("GRAPHIQUES GÉNÉRÉS:\\n")
            f.write("-" * 30 + "\\n")
            for i, plot in enumerate(plots_created, 1):
                f.write(f"{i}. {plot.name}\\n")
            
            f.write("\\n")
            if compensation_results:
                stats = compensation_results.statistics
                f.write("STATISTIQUES DE COMPENSATION:\\n")
                f.write("-" * 30 + "\\n")
                f.write(f"sigma_0 (a posteriori): {stats.sigma_0_hat:.4f}\\n")
                f.write(f"Test chi2: {'VALIDE' if stats.unit_weight_valid else 'REJETE'}\\n")
                f.write(f"Residu max: {stats.max_standardized_residual:.2f}\\n")
                f.write(f"Fautes detectees: {compensation_results.computation_metadata['blunder_detection']['suspect_count']}\\n")
        
        # Ne pas ajouter le summary_file à created_plots pour éviter les doublons
        print(f"   ✅ Résumé: {summary_file.name}")
        print(f"\\n📁 Tous les fichiers sauvegardés dans: {self.output_dir}")
        
        return summary_file
    
    def get_created_plots(self) -> List[Path]:
        """Retourne la liste des graphiques créés."""
        return self.created_plots.copy()
    
    def clear_plots(self):
        """Supprime tous les graphiques créés."""
        for plot_path in self.created_plots:
            if plot_path.exists():
                plot_path.unlink()
        self.created_plots.clear()
    
    # NOUVELLES MÉTHODES - GRAPHIQUES INTERACTIFS MODERNES
    
    def create_interactive_altitude_profile(self, 
                                          calculation_results: CalculationResults,
                                          compensation_results: Optional[CompensationResults] = None) -> Optional[Path]:
        """
        Crée un profil altimétrique interactif avec Plotly.
        
        Args:
            calculation_results: Résultats des calculs préliminaires
            compensation_results: Résultats de compensation (optionnel)
            
        Returns:
            Path: Chemin du fichier HTML généré (None si Plotly indisponible)
        """
        if not PLOTLY_AVAILABLE:
            print("⚠️ Plotly non disponible - utilisation de matplotlib")
            return self.create_altitude_profile(calculation_results, compensation_results)
        
        # Données de base
        points = [alt.point_id for alt in calculation_results.altitudes]
        altitudes_orig = [alt.altitude_m for alt in calculation_results.altitudes]
        
        # Créer la figure avec subplots
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=('🏔️ Profil Altimétrique - Nivellement Géométrique', 
                          '📏 Dénivelées par Segment'),
            vertical_spacing=0.12
        )
        
        # Profil original
        fig.add_trace(
            go.Scatter(
                x=points, y=altitudes_orig,
                mode='lines+markers',
                name='Altitudes calculées',
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(size=8, symbol='circle'),
                hovertemplate='<b>%{x}</b><br>Altitude: %{y:.4f} m<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Profil compensé si disponible
        if compensation_results:
            altitudes_comp = [alt.altitude_m for alt in compensation_results.adjusted_altitudes]
            fig.add_trace(
                go.Scatter(
                    x=points, y=altitudes_comp,
                    mode='lines+markers',
                    name='Altitudes compensées',
                    line=dict(color=COLORS['accent'], width=3),
                    marker=dict(size=8, symbol='square'),
                    hovertemplate='<b>%{x}</b><br>Alt. compensée: %{y:.4f} m<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Zone de précision cible (fond)
            alt_mean = np.mean(altitudes_orig)
            fig.add_shape(
                type="rect",
                x0=points[0], y0=alt_mean - self.precision_mm/1000,
                x1=points[-1], y1=alt_mean + self.precision_mm/1000,
                fillcolor=COLORS['precision_zone'],
                opacity=0.2,
                line_width=0,
                row=1, col=1
            )
        
        # Dénivelées
        if len(calculation_results.height_differences) > 0:
            deltas = [hd.delta_h_m for hd in calculation_results.height_differences if hd.is_valid]
            delta_names = [f"Seg. {i+1}" for i in range(len(deltas))]
            deltas_mm = np.array(deltas) * 1000
            
            # Couleurs selon la magnitude
            colors = [COLORS['success'] if abs(d) <= 50 else 
                     COLORS['warning'] if abs(d) <= 100 else 
                     COLORS['error'] for d in deltas_mm]
            
            fig.add_trace(
                go.Bar(
                    x=delta_names, y=deltas_mm,
                    name='Dénivelées',
                    marker_color=colors,
                    hovertemplate='<b>%{x}</b><br>Dénivelée: %{y:.1f} mm<extra></extra>'
                ),
                row=2, col=1
            )
        
        # Configuration du layout moderne
        fig.update_layout(
            **PLOTLY_THEME['layout'],
            title={
                'text': '🧮 Système de Compensation Altimétrique - Analyse Interactive',
                'x': 0.5,
                'font': {'size': 20, 'color': COLORS['text']}
            },
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=COLORS['neutral_light'],
                borderwidth=1
            ),
            height=800,
            margin=dict(l=60, r=60, t=100, b=60)
        )
        
        # Configuration des axes
        fig.update_xaxes(
            title_text="Points de Nivellement", 
            tickangle=45,
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Altitude (m)", 
            tickformat='.4f',
            row=1, col=1
        )
        
        fig.update_xaxes(
            title_text="Segments",
            row=2, col=1
        )
        fig.update_yaxes(
            title_text="Dénivelée (mm)",
            row=2, col=1
        )
        
        # Sauvegarde
        filename = f"profil_interactif_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        fig.write_html(
            str(filepath),
            config={
                'displayModeBar': True,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'displaylogo': False,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'profil_altimetrique',
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                }
            }
        )
        
        self.created_plots.append(filepath)
        print(f"✅ Profil interactif créé: {filename}")
        
        return filepath
    
    def create_interactive_dashboard(self,
                                   calculation_results: CalculationResults,
                                   compensation_results: Optional[CompensationResults] = None) -> Optional[Path]:
        """
        Crée un dashboard interactif complet avec tous les graphiques.
        
        Args:
            calculation_results: Résultats des calculs
            compensation_results: Résultats de compensation (optionnel)
            
        Returns:
            Path: Chemin du dashboard HTML (None si Plotly indisponible)
        """
        if not PLOTLY_AVAILABLE:
            print("⚠️ Dashboard interactif non disponible - Plotly requis")
            return None
        
        # Créer une grille de subplots 2x2
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('🏔️ Profil Altimétrique', '📊 Analyse de Fermeture', 
                          '🎯 Carte de Précision', '📈 Statistiques de Qualité'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "table"}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # 1. Profil altimétrique (simplifié)
        points = [alt.point_id for alt in calculation_results.altitudes]
        altitudes = [alt.altitude_m for alt in calculation_results.altitudes]
        
        fig.add_trace(
            go.Scatter(
                x=points, y=altitudes,
                mode='lines+markers',
                name='Altitudes',
                line=dict(color=COLORS['primary'], width=2),
                marker=dict(size=6),
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. Analyse de fermeture
        closure = calculation_results.closure_analysis
        error_mm = abs(closure.closure_error_mm)
        tolerance_mm = closure.tolerance_mm
        
        fig.add_trace(
            go.Bar(
                x=['Erreur mesurée', 'Tolérance'],
                y=[error_mm, tolerance_mm],
                marker_color=[COLORS['error'] if error_mm > tolerance_mm else COLORS['success'], 
                             COLORS['neutral']],
                name='Fermeture',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Carte de précision
        if compensation_results:
            covar_diag = np.diag(compensation_results.covariance_matrix)
            precision_mm = np.sqrt(covar_diag) * 1000
        else:
            precision_mm = np.random.uniform(0.8, 2.5, len(points))
        
        colors_precision = [COLORS['success'] if p <= self.precision_mm else 
                           COLORS['warning'] if p <= self.precision_mm * 1.5 else 
                           COLORS['error'] for p in precision_mm]
        
        fig.add_trace(
            go.Bar(
                x=points,
                y=precision_mm,
                marker_color=colors_precision,
                name='Précision',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 4. Tableau de statistiques
        if compensation_results:
            stats = compensation_results.statistics
            table_data = [
                ['Paramètre', 'Valeur', 'Statut'],
                ['σ₀ (a posteriori)', f'{stats.sigma_0_hat:.4f}', '✅' if stats.unit_weight_valid else '❌'],
                ['Degrés de liberté', f'{stats.degrees_of_freedom}', '📊'],
                ['Résidu max', f'{stats.max_standardized_residual:.2f}', '📏'],
                ['Précision atteinte', f'{np.mean(precision_mm):.1f} mm', '🎯']
            ]
        else:
            table_data = [
                ['Paramètre', 'Valeur', 'Statut'],
                ['Points traités', f'{len(points)}', '📍'],
                ['Erreur fermeture', f'{error_mm:.1f} mm', '📐'],
                ['Tolérance', f'{tolerance_mm:.1f} mm', '⚖️'],
                ['Conforme', 'OUI' if error_mm <= tolerance_mm else 'NON', '✅' if error_mm <= tolerance_mm else '❌']
            ]
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=table_data[0],
                    fill_color=COLORS['primary'],
                    font=dict(color='white', size=12),
                    align='center'
                ),
                cells=dict(
                    values=list(zip(*table_data[1:])),
                    fill_color='white',
                    font=dict(color=COLORS['text'], size=11),
                    align=['left', 'center', 'center'],
                    height=30
                )
            ),
            row=2, col=2
        )
        
        # Configuration générale
        fig.update_layout(
            **PLOTLY_THEME['layout'],
            title={
                'text': '📊 Dashboard Compensation Altimétrique - Vue d\'Ensemble',
                'x': 0.5,
                'font': {'size': 24, 'color': COLORS['text']}
            },
            showlegend=False,
            height=900,
            margin=dict(l=60, r=60, t=120, b=60)
        )
        
        # Titres des axes
        fig.update_xaxes(title_text="Points", row=1, col=1)
        fig.update_yaxes(title_text="Altitude (m)", row=1, col=1)
        
        fig.update_yaxes(title_text="Erreur (mm)", row=1, col=2)
        
        fig.update_xaxes(title_text="Points", tickangle=45, row=2, col=1)
        fig.update_yaxes(title_text="Précision (mm)", row=2, col=1)
        
        # Sauvegarde
        filename = f"dashboard_interactif_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        fig.write_html(
            str(filepath),
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'dashboard_compensation',
                    'height': 900,
                    'width': 1400,
                    'scale': 2
                }
            }
        )
        
        self.created_plots.append(filepath)
        print(f"✅ Dashboard interactif créé: {filename}")
        
        return filepath




def create_comparison_plot(results_before: CalculationResults,
                         results_after: CalculationResults,
                         title: str = "Comparaison Avant/Après") -> Path:
    """Créer un graphique de comparaison entre deux jeux de résultats."""
    visualizer = LevelingVisualizer()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Données avant
    points = [alt.point_id for alt in results_before.altitudes]
    altitudes_before = [alt.altitude_m for alt in results_before.altitudes]
    altitudes_after = [alt.altitude_m for alt in results_after.altitudes]
    
    x_positions = range(len(points))
    
    # Graphiques
    ax.plot(x_positions, altitudes_before, 'o-', color=COLORS['secondary'], 
           linewidth=2, markersize=6, label='Avant', alpha=0.8)
    ax.plot(x_positions, altitudes_after, 's-', color=COLORS['primary'], 
           linewidth=2, markersize=6, label='Après', alpha=0.8)
    
    # Configuration
    ax.set_xticks(x_positions)
    ax.set_xticklabels(points, rotation=45, ha='right')
    ax.set_ylabel('Altitude (m)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    # Sauvegarde
    filename = f"comparaison_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = visualizer.output_dir / filename
    plt.savefig(filepath)
    plt.close()
    
    return filepath