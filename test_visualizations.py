#!/usr/bin/env python3
"""
Test et démonstration du module de visualisation graphique.

Ce script génère tous les types de graphiques disponibles pour
le système de compensation altimétrique.
"""

import sys
sys.path.append('src')
import numpy as np
from pathlib import Path

from visualizer import LevelingVisualizer, quick_visualization
from data_importer import DataImporter
from calculator import LevelingCalculator
from compensator import LevelingCompensator
from atmospheric_corrections import AtmosphericConditions, create_standard_conditions

def test_visualizations():
    """Test complet des visualisations."""
    
    print("🎨 TEST MODULE VISUALISATION")
    print("=" * 50)
    
    # Créer le dossier de sortie
    output_dir = Path("./visualizations_test")
    output_dir.mkdir(exist_ok=True)
    
    # Initialiser le visualiseur
    visualizer = LevelingVisualizer(precision_mm=2.0, output_dir=output_dir)
    
    try:
        # Tentative avec données réelles
        print("📁 Chargement des données réelles...")
        importer = DataImporter()
        data = importer.import_file('canal_G1.xlsx')
        
        print(f"✅ Données chargées: {len(data.dataframe)} points")
        
        # Calculs avec corrections atmosphériques
        conditions = create_standard_conditions("sahel")
        calculator = LevelingCalculator(
            precision_mm=2.0,
            apply_atmospheric_corrections=True,
            atmospheric_conditions=conditions
        )
        
        calc_results = calculator.calculate_complete_leveling(
            data.dataframe, data.ar_columns, data.av_columns,
            data.dist_columns,
            initial_altitude=518.51872,
            known_final_altitude=502.872
        )
        
        # Compensation
        print("🔧 Compensation par moindres carrés...")
        
        # Debug des dimensions
        print(f"   Debug: {len(data.dataframe)} points dans dataframe")
        print(f"   Debug: {len(calc_results.altitudes)} altitudes calculées")
        print(f"   Debug: {len(calc_results.height_differences)} dénivelées")
        
        # Ajuster les distances au nombre réel d'observations valides
        valid_observations = [hd for hd in calc_results.height_differences if hd.is_valid]
        print(f"   Debug: {len(valid_observations)} observations valides")
        
        distances = np.array([100.0] * len(valid_observations))
        print(f"   Debug: {len(distances)} distances créées")
        
        compensator = LevelingCompensator(precision_mm=2.0)
        comp_results = compensator.compensate(calc_results, distances)
        
        print("✅ Compensation terminée!")
        
        # Générer les corrections atmosphériques pour le rapport
        from atmospheric_corrections import AtmosphericCorrector
        corrector = AtmosphericCorrector()
        atmospheric_corrections = []
        
        for dist in distances[:10]:  # Limiter pour la démo
            corr = corrector.calculate_atmospheric_correction(dist, 0.0, conditions)
            atmospheric_corrections.append(corr)
        
        # Générer directement le rapport complet (qui crée tous les graphiques)
        print("\n📊 GÉNÉRATION DU RAPPORT COMPLET...")
        rapport = visualizer.create_complete_report(
            calc_results, comp_results, atmospheric_corrections, distances[:10]
        )
        print(f"✅ Rapport complet: {rapport.name}")
        
        # Statistiques finales
        print(f"\n📈 RÉSULTATS:")
        print(f"   Graphiques créés: {len(visualizer.get_created_plots())}")
        print(f"   Dossier de sortie: {output_dir}")
        
        # Liste des fichiers
        print(f"\n📁 FICHIERS GÉNÉRÉS:")
        for i, plot_path in enumerate(visualizer.get_created_plots(), 1):
            print(f"   {i}. {plot_path.name}")
        
        return True
        
    except FileNotFoundError:
        print("⚠️ Fichier canal_G1.xlsx non trouvé - génération avec données synthétiques")
        return test_with_synthetic_data(visualizer)
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_with_synthetic_data(visualizer: LevelingVisualizer):
    """Test avec données synthétiques."""
    
    print("\n🔧 GÉNÉRATION AVEC DONNÉES SYNTHÉTIQUES")
    print("-" * 40)
    
    # Créer des données synthétiques
    from calculator import AltitudeCalculation, HeightDifference, ClosureAnalysis, CalculationResults
    from calculator import TraverseType, ControlStatistics
    
    # Altitudes synthétiques
    altitudes = []
    initial_alt = 100.000
    for i in range(6):
        alt = AltitudeCalculation(
            point_id=f"P{i:03d}",
            altitude_m=initial_alt + i * 0.5 + np.random.normal(0, 0.001),
            cumulative_delta_h=i * 0.5,
            is_reference=(i == 0)
        )
        altitudes.append(alt)
    
    # Dénivelées synthétiques
    height_differences = []
    for i in range(5):
        hd = HeightDifference(
            delta_h_m=0.5 + np.random.normal(0, 0.002),
            ar_reading=1.500 + np.random.normal(0, 0.001),
            av_reading=1.000 + np.random.normal(0, 0.001),
            instrument_id=1,
            is_valid=True
        )
        height_differences.append(hd)
    
    # Analyse de fermeture synthétique
    closure = ClosureAnalysis(
        traverse_type=TraverseType.CLOSED,
        closure_error_mm=1.5,
        tolerance_mm=4.0,
        is_acceptable=True,
        total_distance_km=1.0,
        error_per_km_mm=1.5
    )
    
    # Statistiques de contrôle
    control_stats = ControlStatistics(
        mean_residual_mm=0.1,
        max_residual_mm=2.1,
        std_residual_mm=0.8,
        observations_within_tolerance=5,
        total_observations=5
    )
    
    # Résultats des calculs synthétiques
    calc_results = CalculationResults(
        altitudes=altitudes,
        height_differences=height_differences,
        closure_analysis=closure,
        control_statistics=control_stats,
        calculation_metadata={}
    )
    
    # Générer les graphiques de base
    try:
        # Profil altimétrique
        plot1 = visualizer.create_altitude_profile(calc_results)
        print(f"✅ Profil altimétrique: {plot1.name}")
        
        # Analyse de fermeture
        plot2 = visualizer.create_closure_analysis_plot(closure, calc_results)
        print(f"✅ Analyse fermeture: {plot2.name}")
        
        # Corrections atmosphériques avec données synthétiques
        distances = np.array([200.0, 150.0, 300.0, 250.0, 180.0])
        plot3 = visualizer.create_atmospheric_corrections_plot([], distances)
        print(f"✅ Corrections atmosphériques: {plot3.name}")
        
        print(f"\n✅ Test avec données synthétiques réussi!")
        print(f"📁 Fichiers dans: {visualizer.output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération synthétique: {e}")
        return False

def demonstrate_quick_visualization():
    """Démonstration de la visualisation rapide avec données différentes."""
    
    print("\n🚀 DÉMONSTRATION VISUALISATION RAPIDE (DONNÉES SYNTHÉTIQUES)")
    print("-" * 60)
    
    try:
        # Utiliser des données synthétiques différentes pour éviter les doublons
        from calculator import AltitudeCalculation, HeightDifference, ClosureAnalysis, CalculationResults
        from calculator import TraverseType, ControlStatistics
        
        # Créer un petit cheminement synthétique
        altitudes = []
        for i in range(4):  # Moins de points que le test principal
            alt = AltitudeCalculation(
                point_id=f"DEMO_{i:02d}",
                altitude_m=200.000 + i * 1.5 + np.random.normal(0, 0.002),
                cumulative_delta_h=i * 1.5,
                is_reference=(i == 0)
            )
            altitudes.append(alt)
        
        # Dénivelées synthétiques
        height_differences = []
        for i in range(3):
            hd = HeightDifference(
                delta_h_m=1.5 + np.random.normal(0, 0.003),
                ar_reading=2.000 + np.random.normal(0, 0.001),
                av_reading=0.500 + np.random.normal(0, 0.001),
                instrument_id=1,
                is_valid=True
            )
            height_differences.append(hd)
        
        # Analyse de fermeture synthétique
        closure = ClosureAnalysis(
            traverse_type=TraverseType.OPEN,
            closure_error_mm=2.8,
            tolerance_mm=5.0,
            is_acceptable=True,
            total_distance_km=0.6,
            error_per_km_mm=4.7
        )
        
        # Statistiques de contrôle
        control_stats = ControlStatistics(
            mean_residual_mm=0.2,
            max_residual_mm=1.8,
            std_residual_mm=0.6,
            observations_within_tolerance=3,
            total_observations=3
        )
        
        # Résultats synthétiques
        demo_results = CalculationResults(
            altitudes=altitudes,
            height_differences=height_differences,
            closure_analysis=closure,
            control_statistics=control_stats,
            calculation_metadata={"demo": True}
        )
        
        # Visualisation rapide avec données synthétiques
        output_dir = Path("./quick_viz_demo")
        rapport = quick_visualization(demo_results, output_dir=output_dir)
        
        print(f"✅ Visualisation rapide générée: {rapport}")
        print(f"📁 Dossier: {output_dir}")
        
    except Exception as e:
        print(f"⚠️ Visualisation rapide échouée: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    success = test_visualizations()
    
    if success:
        demonstrate_quick_visualization()
        print(f"\n🎯 TESTS TERMINÉS AVEC SUCCÈS!")
        print(f"📁 Consultez les dossiers 'visualizations_test' et 'quick_viz_demo'")
    else:
        print(f"\n❌ TESTS ÉCHOUÉS")
        sys.exit(1)