#!/usr/bin/env python3
"""Test de redondance pour la compensation"""

import sys
sys.path.append('src')
import numpy as np

from data_importer import DataImporter
from calculator import LevelingCalculator
from compensator import LevelingCompensator

try:
    print("🔧 TEST REDONDANCE")
    print("=" * 30)
    
    # 1. Import et calculs
    importer = DataImporter()
    data = importer.import_file('exemple_donnees_nivellement.xlsx')
    
    calculator = LevelingCalculator(precision_mm=2.0)
    results = calculator.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, initial_altitude=100.0
    )
    
    print(f"Points: {len(results.altitudes)}")
    print(f"Height differences: {len(results.height_differences)}")
    print(f"Segments: {len(results.altitudes)-1}")
    print(f"Redondance théorique: {len(results.height_differences) - (len(results.altitudes)-1)}")
    
    # 2. Test compensation avec redondance
    distances = np.array([125.5] * len(results.height_differences))  # Une distance par observation
    
    compensator = LevelingCompensator(precision_mm=2.0)
    comp_results = compensator.compensate(results, distances)
    
    print("\n✅ COMPENSATION AVEC REDONDANCE RÉUSSIE!")
    
    # 3. Statistiques
    stats = comp_results.statistics
    print(f"\n📊 STATISTIQUES:")
    print(f"   Degrés de liberté: {stats.degrees_of_freedom}")
    print(f"   σ₀: {stats.sigma_0_hat:.4f}")
    print(f"   Test χ²: {'✅ VALIDÉ' if stats.unit_weight_valid else '❌ REJETÉ'}")
    
    max_correction = np.max(np.abs(comp_results.adjusted_coordinates)) * 1000
    print(f"   Correction max: {max_correction:.2f} mm")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
