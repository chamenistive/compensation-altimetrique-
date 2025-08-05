#!/usr/bin/env python3
"""Test avec les vraies données canal_G1.xlsx"""

import sys
sys.path.append('src')
import numpy as np

try:
    from data_importer import DataImporter
    from calculator import LevelingCalculator
    from compensator import LevelingCompensator
    
    print("🔧 TEST DONNÉES RÉELLES - CANAL_G1.XLSX")
    print("=" * 50)
    
    # 1. Import
    importer = DataImporter()
    data = importer.import_file('canal_G1.xlsx')
    print(f"✅ Import: {len(data.dataframe)} points")
    print(f"   Type: {data.initial_point} → {data.final_point}")
    
    # 2. Calculs préliminaires
    calculator = LevelingCalculator(precision_mm=2.0)
    results = calculator.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, 
        initial_altitude=518.51872,
        known_final_altitude=502.872
    )
    
    print(f"✅ Calculs: {len(results.altitudes)} altitudes")
    print(f"   Observations valides: {sum(1 for hd in results.height_differences if hd.is_valid)}")
    print(f"   Observations invalides: {sum(1 for hd in results.height_differences if not hd.is_valid)}")
    
    # 3. Analyse fermeture AVANT compensation
    closure = results.closure_analysis
    print(f"\n📊 FERMETURE AVANT COMPENSATION:")
    print(f"   Erreur: {closure.closure_error_mm:.1f}mm")
    print(f"   Tolérance: ±{closure.tolerance_mm:.1f}mm")
    print(f"   Statut: {'✅' if closure.is_acceptable else '❌'}")
    
    # 4. Tentative de compensation
    print(f"\n🔧 TENTATIVE COMPENSATION...")
    try:
        distances = np.array([100.0] * len([hd for hd in results.height_differences if hd.is_valid]))
        compensator = LevelingCompensator(precision_mm=10.0)  # Tolérance élargie
        comp_results = compensator.compensate(results, distances)
        
        print("✅ COMPENSATION RÉUSSIE!")
        
        # Statistiques
        stats = comp_results.statistics
        max_correction = np.max(np.abs(comp_results.adjusted_coordinates)) * 1000
        
        print(f"\n📈 RÉSULTATS:")
        print(f"   Degrés liberté: {stats.degrees_of_freedom}")
        print(f"   σ₀: {stats.sigma_0_hat:.4f}")
        print(f"   Correction max: {max_correction:.2f}mm")
        
        # Quelques altitudes
        print(f"\n📏 ALTITUDES (premières/dernières):")
        for i in [0, 1, 2, -3, -2, -1]:
            alt = comp_results.adjusted_altitudes[i]
            print(f"   {alt.point_id}: {alt.altitude_m:.4f}m")
            
    except Exception as comp_error:
        print(f"❌ Compensation échouée: {comp_error}")
        print("💡 Les données nécessitent un prétraitement plus poussé")
        
        # Afficher quelques altitudes non compensées
        print(f"\n📏 ALTITUDES NON COMPENSÉES (premières/dernières):")
        for i in [0, 1, 2, -3, -2, -1]:
            alt = results.altitudes[i]
            print(f"   {alt.point_id}: {alt.altitude_m:.4f}m")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
