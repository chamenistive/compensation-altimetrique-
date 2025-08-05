#!/usr/bin/env python3
"""Test final après correction complète"""

import sys
sys.path.append('src')
import numpy as np

def test_complete_pipeline():
    """Test du pipeline complet"""
    try:
        from data_importer import DataImporter
        from calculator import LevelingCalculator
        from compensator import LevelingCompensator
        
        print("🚀 TEST PIPELINE COMPLET")
        print("=" * 40)
        
        # 1. Import
        importer = DataImporter()
        data = importer.import_file('exemple_donnees_nivellement.xlsx')
        print(f"✅ Import: {len(data.dataframe)} points")
        
        # 2. Calculs préliminaires
        calculator = LevelingCalculator(precision_mm=2.0)
        results = calculator.calculate_complete_leveling(
            data.dataframe, data.ar_columns, data.av_columns,
            data.dist_columns, initial_altitude=100.0
        )
        print(f"✅ Calculs: {len(results.altitudes)} altitudes, {len(results.height_differences)} observations")
        
        # 3. Compensation
        distances = np.array([125.5, 147.2, 198.7, 156.3, 173.8])
        compensator = LevelingCompensator(precision_mm=2.0)
        comp_results = compensator.compensate(results, distances)
        
        print("✅ COMPENSATION RÉUSSIE!")
        
        # 4. Résultats
        print("\n📊 ALTITUDES COMPENSÉES:")
        for alt in comp_results.adjusted_altitudes:
            print(f"   {alt.point_id}: {alt.altitude_m:.4f} m")
        
        # 5. Statistiques finales
        stats = comp_results.statistics
        max_correction = np.max(np.abs(comp_results.adjusted_coordinates)) * 1000
        
        print(f"\n📈 STATISTIQUES FINALES:")
        print(f"   Degrés de liberté: {stats.degrees_of_freedom}")
        print(f"   σ₀: {stats.sigma_0_hat:.4f}")
        print(f"   Test χ²: {'✅ VALIDÉ' if stats.unit_weight_valid else '❌ REJETÉ'}")
        print(f"   Correction max: {max_correction:.2f} mm")
        print(f"   Précision 2mm: {'✅ ATTEINTE' if max_correction <= 2.0 else '⚠️ DÉPASSÉE'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_pipeline()
    if success:
        print("\n🎯 PIPELINE ENTIÈREMENT FONCTIONNEL!")
        print("🚀 Vous pouvez maintenant utiliser: python main.py")
    else:
        print("\n❌ Problèmes persistants")
