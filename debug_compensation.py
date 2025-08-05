#!/usr/bin/env python3
"""Version debug pour diagnostiquer le problème de compensation"""

import sys
sys.path.append('src')

from data_importer import DataImporter
from calculator import LevelingCalculator

try:
    # 1. Import des données
    print("🔍 DIAGNOSTIC - Import des données")
    importer = DataImporter()
    data = importer.import_file('exemple_donnees_nivellement.xlsx')
    print(f"   Points importés: {len(data.dataframe)}")
    print(f"   Colonnes AR: {data.ar_columns}")
    print(f"   Colonnes AV: {data.av_columns}")
    print(f"   Colonnes DIST: {data.dist_columns}")
    
    # 2. Calculs préliminaires
    print("\n🔍 DIAGNOSTIC - Calculs préliminaires")
    calculator = LevelingCalculator(precision_mm=2.0)
    results = calculator.calculate_complete_leveling(
        data.dataframe, data.ar_columns, data.av_columns,
        data.dist_columns, initial_altitude=100.0
    )
    
    print(f"   Altitudes calculées: {len(results.altitudes)}")
    print(f"   Height differences: {len(results.height_differences)}")
    
    # Diagnostic détaillé
    print("\n🔍 DIAGNOSTIC - Détail des height_differences")
    for i, hd in enumerate(results.height_differences[:10]):  # 10 premiers
        print(f"   {i}: Instrument {hd.instrument_id}, Delta: {hd.delta_h_m:.4f}")
    
    print("\n🔍 DIAGNOSTIC - Altitudes")
    for i, alt in enumerate(results.altitudes):
        print(f"   {i}: {alt.point_id} = {alt.altitude_m:.4f}m")
    
    # Test simple de compensation
    print("\n🔍 DIAGNOSTIC - Test compensation simple")
    import numpy as np
    distances = np.array([125.5, 147.2, 198.7, 156.3, 173.8])  # 5 segments
    
    print(f"   Distances: {len(distances)} segments")
    print(f"   Altitudes: {len(results.altitudes)} points")
    print(f"   Height diff: {len(results.height_differences)} observations")
    
    # Calculer dénivelées par segment
    segments_deltas = []
    for i in range(len(results.altitudes)-1):
        delta = results.altitudes[i+1].altitude_m - results.altitudes[i].altitude_m
        segments_deltas.append(delta)
    
    print(f"   Segments deltas: {len(segments_deltas)}")
    for i, delta in enumerate(segments_deltas):
        print(f"     Segment {i}: {delta:.4f}m")

except Exception as e:
    print(f"❌ Erreur diagnostic: {e}")
    import traceback
    traceback.print_exc()
