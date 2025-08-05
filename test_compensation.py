#!/usr/bin/env python3
"""Test spécifique de la compensation corrigée"""

import sys
sys.path.append('src')
import numpy as np

from data_importer import DataImporter
from calculator import LevelingCalculator
from compensator import LevelingCompensator

try:
    print("🔧 TEST COMPENSATION CORRIGÉE")
    print("=" * 40)
    
    # 1. Import et calculs
    importer = DataImporter()
    data = importer.import_file('exemple_donnees_nivellement.xlsx')
    
    calculator = LevelingCalculator(precision_mm=2.0)
    results = calculator.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, initial_altitude=100.0
    )
    
    print(f"✅ Calculs préliminaires OK")
    print(f"   Points: {len(results.altitudes)}")
    print(f"   Height differences: {len(results.height_differences)}")
    
    # 2. Test compensation
    print("\n🔧 Test compensation...")
    distances = np.array([125.5, 147.2, 198.7, 156.3, 173.8])
    
    compensator = LevelingCompensator(precision_mm=2.0)
    comp_results = compensator.compensate(results, distances)
    
    print("✅ COMPENSATION RÉUSSIE!")
    
    # 3. Résultats
    print("\n📊 RÉSULTATS COMPENSÉS:")
    for alt in comp_results.adjusted_altitudes:
        print(f"   {alt.point_id}: {alt.altitude_m:.4f} m")
    
    # 4. Statistiques
    stats = comp_results.statistics
    print(f"\n📈 STATISTIQUES:")
    print(f"   σ₀: {stats.sigma_0_hat:.4f}")
    print(f"   Degrés liberté: {stats.degrees_of_freedom}")
    print(f"   Test χ²: {'✅ OK' if stats.unit_weight_valid else '❌'}")
    
    max_correction = np.max(np.abs(comp_results.adjusted_coordinates)) * 1000
    print(f"   Correction max: {max_correction:.2f} mm")
    print(f"   Précision 2mm: {'✅ ATTEINTE' if max_correction <= 2.0 else '⚠️ DÉPASSÉE'}")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
