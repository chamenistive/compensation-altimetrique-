#!/usr/bin/env python3
"""Test des corrections atmosphériques avec canal_G1.xlsx"""

import sys
sys.path.append('src')
import numpy as np

try:
    from data_importer import DataImporter
    from calculator import LevelingCalculator
    from atmospheric_corrections import AtmosphericConditions, create_standard_conditions
    
    print("🌡️ TEST CORRECTIONS ATMOSPHÉRIQUES")
    print("=" * 50)
    
    # 1. Import des données
    importer = DataImporter()
    data = importer.import_file('canal_G1.xlsx')
    print(f"✅ Données importées: {len(data.dataframe)} points")
    
    # 2. Conditions atmosphériques pour l'Afrique
    conditions_sahel = AtmosphericConditions(
        temperature_celsius=32.0,  # Chaud
        pressure_hpa=1008.0,       # Légèrement plus bas
        humidity_percent=40.0,     # Sec
        weather_condition="tropical_dry"
    )
    
    # 3. Test SANS corrections
    print("\n🔧 CALCUL SANS CORRECTIONS ATMOSPHÉRIQUES:")
    calculator_no_corr = LevelingCalculator(
        precision_mm=2.0,
        apply_atmospheric_corrections=False
    )
    
    results_no_corr = calculator_no_corr.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, 518.51872, 502.53  # Altitude finale corrigée
    )
    
    closure_no_corr = results_no_corr.closure_analysis
    print(f"   Fermeture sans corrections: {closure_no_corr.closure_error_mm:.1f}mm")
    
    # 4. Test AVEC corrections
    print("\n🌡️ CALCUL AVEC CORRECTIONS ATMOSPHÉRIQUES:")
    calculator_with_corr = LevelingCalculator(
        precision_mm=2.0,
        apply_atmospheric_corrections=True,
        atmospheric_conditions=conditions_sahel
    )
    
    results_with_corr = calculator_with_corr.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, 518.51872, 502.53
    )
    
    closure_with_corr = results_with_corr.closure_analysis
    print(f"   Fermeture avec corrections: {closure_with_corr.closure_error_mm:.1f}mm")
    
    # 5. Comparaison
    improvement = abs(closure_no_corr.closure_error_mm) - abs(closure_with_corr.closure_error_mm)
    print(f"\n📊 COMPARAISON:")
    print(f"   Amélioration fermeture: {improvement:.1f}mm")
    print(f"   Amélioration relative: {improvement/abs(closure_no_corr.closure_error_mm)*100:.1f}%")
    
    # 6. Analyse des corrections par distance
    print(f"\n🔍 ANALYSE CORRECTIONS PAR DISTANCE:")
    from atmospheric_corrections import AtmosphericCorrector
    
    corrector = AtmosphericCorrector()
    test_distances = [50, 100, 150, 200, 300]
    
    for distance in test_distances:
        correction = corrector.calculate_atmospheric_correction(
            distance, 0.0, conditions_sahel
        )
        print(f"   {distance}m: {correction.total_correction_mm:.2f}mm")
    
    # 7. Estimation impact total
    distances = data.dataframe[data.dist_columns[0]].dropna()
    total_impact = 0
    
    for distance in distances:
        if distance > 0:
            corr = corrector.calculate_atmospheric_correction(distance, 0.0, conditions_sahel)
            total_impact += abs(corr.total_correction_mm)
    
    print(f"\n🎯 IMPACT TOTAL ESTIMÉ:")
    print(f"   Somme corrections: {total_impact:.1f}mm")
    print(f"   Impact moyen/observation: {total_impact/len(distances):.2f}mm")
    
    if improvement > 0:
        print("\n✅ CORRECTIONS ATMOSPHÉRIQUES BÉNÉFIQUES!")
    else:
        print("\n⚠️ Corrections atmosphériques marginales pour ce cheminement")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
