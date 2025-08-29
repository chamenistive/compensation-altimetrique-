#!/usr/bin/env python3
"""
Script de test des nouvelles visualisations modernisées.
Démontre les capacités des graphiques statiques et interactifs.

Utilisation:
    python test_visualizations.py
"""

import sys
import numpy as np
from pathlib import Path

# Ajouter le dossier src au PATH
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from visualizer import LevelingVisualizer, COLORS, PLOTLY_AVAILABLE
    print("✅ Visualizer chargé avec succès")
    
    # Créer des classes de démonstration si les modules ne sont pas disponibles
    try:
        from calculator import (
            CalculationResults, AltitudeCalculation, HeightDifference, 
            ClosureAnalysis, TraverseType
        )
        from compensator import CompensationResults, CompensationStatistics
        print("✅ Modules backend chargés")
    except ImportError:
        print("⚠️ Modules backend non disponibles - utilisation des classes de démo")
        
        # Classes de démonstration simplifiées
        from dataclasses import dataclass
        from typing import List
        from enum import Enum
        
        @dataclass
        class AltitudeCalculation:
            point_id: str
            altitude_m: float
            cumulative_delta_h: float
            is_reference: bool = False
        
        @dataclass  
        class HeightDifference:
            delta_h_m: float
            ar_reading: float
            av_reading: float
            instrument_id: int
            is_valid: bool = True
            control_residual: float = None
        
        class TraverseType(Enum):
            CLOSED = "fermé"
            OPEN = "ouvert" 
            UNKNOWN = "indéterminé"
            
        @dataclass
        class ClosureAnalysis:
            traverse_type: TraverseType
            closure_error_m: float
            closure_error_mm: float
            tolerance_mm: float
            total_distance_km: float
            is_acceptable: bool
            precision_ratio: float
            
        @dataclass
        class CalculationResults:
            height_differences: List[HeightDifference]
            altitudes: List[AltitudeCalculation]
            closure_analysis: ClosureAnalysis
            control_statistics: dict
            calculation_metadata: dict = None
            
        @dataclass
        class CompensationStatistics:
            sigma_0_hat: float
            degrees_of_freedom: int
            chi2_test_statistic: float
            chi2_critical_value: float
            unit_weight_valid: bool
            max_standardized_residual: float
            blunder_detection_threshold: float
            
        @dataclass
        class CompensationResults:
            adjusted_altitudes: List[AltitudeCalculation]
            adjusted_coordinates: any
            covariance_matrix: any
            residuals: any
            statistics: CompensationStatistics
            solution_method: str
            computation_metadata: dict

    print("✅ Toutes les classes prêtes pour les tests")
except ImportError as e:
    print(f"❌ Erreur d'import critique: {e}")
    print("💡 Vérifiez que src/visualizer.py existe")
    sys.exit(1)

def create_demo_data():
    """Crée des données de démonstration pour les tests."""
    print("🔧 Génération des données de démonstration...")
    
    # Points de nivellement factices
    point_ids = ['RN001', 'P001', 'P002', 'P003', 'P004', 'RN002']
    base_altitude = 125.456  # m
    
    # Altitudes avec une légère pente et du bruit
    altitudes = []
    cumulative_delta = 0.0
    for i, point_id in enumerate(point_ids):
        # Pente de 2mm/point + bruit aléatoire de ±0.5mm
        altitude = base_altitude + (i * 0.002) + np.random.normal(0, 0.0005)
        if i > 0:
            cumulative_delta += altitude - altitudes[-1].altitude_m
        altitudes.append(AltitudeCalculation(
            point_id=point_id,
            altitude_m=altitude,
            cumulative_delta_h=cumulative_delta,
            is_reference=(i == 0 or i == len(point_ids)-1)
        ))
    
    # Dénivelées entre points
    height_differences = []
    for i in range(len(altitudes) - 1):
        delta_h = altitudes[i+1].altitude_m - altitudes[i].altitude_m
        # Ajouter une petite erreur systématique
        delta_h += np.random.normal(0, 0.0008)
        
        height_differences.append(HeightDifference(
            delta_h_m=delta_h,
            ar_reading=np.random.uniform(1.2, 1.8),  # Lecture arrière simulée
            av_reading=np.random.uniform(1.2, 1.8),  # Lecture avant simulée
            instrument_id=i,
            is_valid=True
        ))
    
    # Analyse de fermeture
    total_distance = len(height_differences) * 200  # Distance simulée 200m par section
    closure_error = np.random.normal(0, 0.003)  # ±3mm d'erreur
    
    tolerance_mm = np.sqrt(total_distance / 1000) * 8  # 8mm/√km
    closure_analysis = ClosureAnalysis(
        traverse_type=TraverseType.CLOSED,
        closure_error_m=closure_error,
        closure_error_mm=closure_error * 1000,
        tolerance_mm=tolerance_mm,
        total_distance_km=total_distance / 1000,
        is_acceptable=abs(closure_error * 1000) <= tolerance_mm,
        precision_ratio=abs(closure_error * 1000) / tolerance_mm if tolerance_mm > 0 else 0
    )
    
    # Résultats des calculs
    calculation_results = CalculationResults(
        height_differences=height_differences,
        altitudes=altitudes,
        closure_analysis=closure_analysis,
        control_statistics={'demo_mode': True},
        calculation_metadata={
            'method': 'demo',
            'timestamp': '2025-08-28',
            'precision_target_mm': 2.0
        }
    )
    
    print(f"   📊 {len(altitudes)} points générés")
    print(f"   📏 {len(height_differences)} dénivelées")
    print(f"   🎯 Erreur de fermeture: {closure_error*1000:.1f}mm")
    
    return calculation_results

def create_demo_compensation_results(calculation_results):
    """Crée des résultats de compensation factices."""
    print("⚖️ Génération des résultats de compensation...")
    
    n_points = len(calculation_results.altitudes)
    
    # Corrections simulées (compensation par moindres carrés)
    corrections = np.random.normal(0, 0.001, n_points)  # ±1mm
    
    # Altitudes ajustées
    adjusted_altitudes = []
    for i, alt in enumerate(calculation_results.altitudes):
        adjusted_altitudes.append(AltitudeCalculation(
            point_id=alt.point_id,
            altitude_m=alt.altitude_m + corrections[i],
            cumulative_delta_h=alt.cumulative_delta_h,
            is_reference=alt.is_reference
        ))
    
    # Matrice de covariance simulée
    covariance_matrix = np.eye(n_points) * (0.0015**2)  # 1.5mm d'écart-type
    # Ajouter des corrélations
    for i in range(n_points-1):
        covariance_matrix[i, i+1] = covariance_matrix[i+1, i] = 0.0008**2
    
    # Statistiques de compensation
    residuals = np.random.normal(0, 0.0008, n_points)
    dof = n_points - 2
    statistics = CompensationStatistics(
        sigma_0_hat=1.12,
        degrees_of_freedom=dof,
        chi2_test_statistic=dof * 1.12**2,
        chi2_critical_value=9.488,  # Chi² critique pour α=0.05
        unit_weight_valid=True,
        max_standardized_residual=np.max(np.abs(residuals)) / 0.0015,
        blunder_detection_threshold=2.5
    )
    
    # Résultats de compensation
    compensation_results = CompensationResults(
        adjusted_altitudes=adjusted_altitudes,
        adjusted_coordinates=corrections.reshape(-1, 1),
        covariance_matrix=covariance_matrix,
        residuals=residuals.reshape(-1, 1),
        statistics=statistics,
        solution_method="LSQ",
        computation_metadata={
            'iterations': 3,
            'convergence_threshold': 1e-8,
            'max_correction_mm': np.max(np.abs(corrections)) * 1000,
            'condition_number': 1.2e3,
            'blunder_detection': {'suspect_count': 0, 'outliers': []},
            'timestamp': '2025-08-28'
        }
    )
    
    print(f"   🔧 Corrections max: {np.max(np.abs(corrections))*1000:.1f}mm")
    print(f"   📈 σ₀: {statistics.sigma_0_hat:.3f}")
    
    return compensation_results

def test_matplotlib_visualizations():
    """Teste les visualisations matplotlib modernisées."""
    print("\n🎨 === TEST VISUALISATIONS MATPLOTLIB MODERNES ===")
    
    # Données de test
    calculation_results = create_demo_data()
    compensation_results = create_demo_compensation_results(calculation_results)
    
    # Créer le visualiseur
    visualizer = LevelingVisualizer(precision_mm=2.0, output_dir=Path("./test_visualizations"))
    
    try:
        # 1. Profil altimétrique
        print("\n📈 Test profil altimétrique...")
        profile_path = visualizer.create_altitude_profile(
            calculation_results, 
            compensation_results, 
            show_corrections=True
        )
        print(f"   ✅ Créé: {profile_path}")
        
        # 2. Analyse de fermeture
        print("\n🎯 Test analyse de fermeture...")
        closure_path = visualizer.create_closure_analysis_plot(
            calculation_results.closure_analysis, 
            calculation_results
        )
        print(f"   ✅ Créé: {closure_path}")
        
        # 3. Diagnostics de compensation
        print("\n⚙️ Test diagnostics compensation...")
        diagnostics_path = visualizer.create_compensation_diagnostics(
            compensation_results, 
            calculation_results
        )
        print(f"   ✅ Créé: {diagnostics_path}")
        
        # 4. Carte de précision
        print("\n🗺️ Test carte de précision...")
        precision_path = visualizer.create_precision_map(
            compensation_results, 
            calculation_results
        )
        print(f"   ✅ Créé: {precision_path}")
        
        print(f"\n📊 {len(visualizer.get_created_plots())} graphiques matplotlib créés")
        
    except Exception as e:
        print(f"❌ Erreur matplotlib: {e}")
        return False
    
    return True

def test_plotly_visualizations():
    """Teste les visualisations Plotly interactives."""
    print("\n🌐 === TEST VISUALISATIONS PLOTLY INTERACTIVES ===")
    
    if not PLOTLY_AVAILABLE:
        print("⚠️ Plotly non installé - tests interactifs ignorés")
        print("💡 Installez avec: pip install plotly kaleido")
        return False
    
    # Données de test
    calculation_results = create_demo_data()
    compensation_results = create_demo_compensation_results(calculation_results)
    
    # Créer le visualiseur
    visualizer = LevelingVisualizer(precision_mm=2.0, output_dir=Path("./test_visualizations"))
    
    try:
        # 1. Profil interactif
        print("\n🏔️ Test profil altimétrique interactif...")
        interactive_profile = visualizer.create_interactive_altitude_profile(
            calculation_results, 
            compensation_results
        )
        if interactive_profile:
            print(f"   ✅ Créé: {interactive_profile}")
            print(f"   🌐 Ouvrez dans votre navigateur: file://{interactive_profile.absolute()}")
        
        # 2. Dashboard interactif
        print("\n📊 Test dashboard interactif...")
        dashboard = visualizer.create_interactive_dashboard(
            calculation_results, 
            compensation_results
        )
        if dashboard:
            print(f"   ✅ Créé: {dashboard}")
            print(f"   🌐 Ouvrez dans votre navigateur: file://{dashboard.absolute()}")
        
        print(f"\n🎯 Visualisations interactives HTML disponibles!")
        
    except Exception as e:
        print(f"❌ Erreur Plotly: {e}")
        return False
    
    return True

def test_color_palette():
    """Teste et affiche la palette de couleurs géodésiques."""
    print("\n🎨 === TEST PALETTE COULEURS GÉODÉSIQUES ===")
    
    print("Couleurs principales:")
    for name, color in COLORS.items():
        if not name.endswith('_light'):  # Éviter les doublons
            print(f"   {name:20} : {color}")
    
    # Test avec matplotlib si disponible
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Créer des patches colorés
        y_pos = 0
        patches = []
        labels = []
        
        for name, color in COLORS.items():
            if not name.endswith('_light'):
                rect = mpatches.Rectangle((0, y_pos), 2, 0.8, 
                                        facecolor=color, edgecolor='black')
                ax.add_patch(rect)
                ax.text(2.1, y_pos + 0.4, f"{name}: {color}", 
                       va='center', fontsize=11, fontfamily='monospace')
                y_pos += 1
        
        ax.set_xlim(0, 8)
        ax.set_ylim(0, y_pos)
        ax.set_title('🎨 Palette de Couleurs Géodésiques Moderne', 
                    fontsize=16, fontweight='bold')
        ax.axis('off')
        
        # Sauvegarde
        palette_path = Path("./test_visualizations/palette_couleurs.png")
        palette_path.parent.mkdir(exist_ok=True)
        plt.savefig(palette_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ Palette sauvegardée: {palette_path}")
        
    except Exception as e:
        print(f"   ⚠️ Impossible de créer la palette visuelle: {e}")

def main():
    """Fonction principale de test."""
    print("🧮 === TEST COMPLET VISUALISATIONS MODERNISÉES ===")
    print("Système de Compensation Altimétrique - Nouvelles Visualisations")
    print("=" * 60)
    
    # Test de la palette
    test_color_palette()
    
    # Tests matplotlib
    matplotlib_ok = test_matplotlib_visualizations()
    
    # Tests Plotly
    plotly_ok = test_plotly_visualizations()
    
    # Résumé
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ DES TESTS")
    print(f"   📊 Matplotlib (statique): {'✅ OK' if matplotlib_ok else '❌ ERREUR'}")
    print(f"   🌐 Plotly (interactif): {'✅ OK' if plotly_ok else '⚠️ NON TESTÉ'}")
    
    # Instructions
    if matplotlib_ok or plotly_ok:
        print("\n📁 Fichiers générés dans: ./test_visualizations/")
        print("💡 Pour les graphiques HTML, ouvrez-les dans votre navigateur")
        if plotly_ok:
            print("🎮 Les graphiques Plotly sont interactifs: zoom, hover, export PNG")
    
    print("\n🎉 Tests terminés!")

if __name__ == "__main__":
    main()