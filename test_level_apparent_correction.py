#!/usr/bin/env python3
"""
Test de la correction de niveau apparent selon les formules des images.

Implémente la logique :
n.a = (1 - m.r.a) × Dh² / (2 × Rn)
Δh_corrigé = Δh_mesuré + n.a
"""

import sys
sys.path.append('src')
import numpy as np

from atmospheric_corrections import AtmosphericCorrector, AtmosphericConditions
from data_importer import DataImporter
from calculator import LevelingCalculator

def test_level_apparent_correction():
    """Test de la correction de niveau apparent."""
    
    print("🔧 TEST CORRECTION DE NIVEAU APPARENT")
    print("=" * 50)
    
    # 1. Créer des conditions atmosphériques test
    conditions = AtmosphericConditions(
        temperature_celsius=25.0,  # Température élevée (effet réfraction)
        pressure_hpa=1010.0,
        humidity_percent=70.0,
        weather_condition="chaud"
    )
    
    # 2. Initialiser le correcteur atmosphérique
    corrector = AtmosphericCorrector()
    
    # 3. Données de test (distances et dénivelées typiques)
    test_cases = [
        {"distance_m": 100.0, "delta_h_m": 0.150, "description": "Courte portée"},
        {"distance_m": 200.0, "delta_h_m": -0.250, "description": "Portée moyenne"},
        {"distance_m": 500.0, "delta_h_m": 1.200, "description": "Longue portée"},
        {"distance_m": 1000.0, "delta_h_m": -2.500, "description": "Très longue portée"}
    ]
    
    print("\n📊 CALCULS DE CORRECTION:")
    print("-" * 80)
    print(f"{'Distance':<10} {'Δh orig':<10} {'m.r.a':<8} {'n.a (mm)':<10} {'Δh corr':<12} {'Description'}")
    print("-" * 80)
    
    for case in test_cases:
        distance = case["distance_m"]
        delta_h = case["delta_h_m"]
        desc = case["description"]
        
        # Calculer la correction complète
        correction = corrector.calculate_atmospheric_correction(
            distance, delta_h, conditions
        )
        
        print(f"{distance:<10.0f} {delta_h:<10.3f} {correction.refraction_coefficient:<8.3f} "
              f"{correction.level_apparent_correction_mm:<10.2f} {correction.corrected_delta_h:<12.6f} {desc}")
    
    print("-" * 80)
    
    # 4. Test avec données réelles
    print(f"\n🔧 TEST AVEC DONNÉES RÉELLES:")
    try:
        importer = DataImporter()
        data = importer.import_file('canal_G1.xlsx')
        
        print(f"✅ Données chargées: {len(data.dataframe)} points")
        
        # Calculer avec corrections atmosphériques
        calculator = LevelingCalculator(
            precision_mm=2.0, 
            apply_atmospheric_corrections=True,
            atmospheric_conditions=conditions
        )
        
        results = calculator.calculate_complete_leveling(
            data.dataframe, data.ar_columns, data.av_columns,
            data.dist_columns, 
            initial_altitude=518.51872,
            known_final_altitude=502.872
        )
        
        # Analyser l'impact des corrections
        print(f"\n📈 IMPACT DES CORRECTIONS:")
        print(f"   Observations totales: {len(results.height_differences)}")
        
        corrected_count = 0
        max_correction = 0.0
        
        for hd in results.height_differences:
            if hasattr(hd, 'atmospheric_correction_mm') and hd.atmospheric_correction_mm != 0:
                corrected_count += 1
                max_correction = max(max_correction, abs(hd.atmospheric_correction_mm))
        
        print(f"   Observations corrigées: {corrected_count}")
        print(f"   Correction max: {max_correction:.2f}mm")
        
        # Analyser fermeture
        closure = results.closure_analysis
        print(f"\n📐 EFFET SUR LA FERMETURE:")
        print(f"   Erreur de fermeture: {abs(closure.closure_error_mm):.2f}mm")
        print(f"   Tolérance: ±{closure.tolerance_mm:.2f}mm")
        print(f"   Statut: {'✅ ACCEPTABLE' if closure.is_acceptable else '❌ DÉPASSEMENT'}")
        
    except FileNotFoundError:
        print("⚠️ Fichier canal_G1.xlsx non trouvé - test avec données synthétiques uniquement")
    except Exception as e:
        print(f"⚠️ Erreur test données réelles: {e}")
    
    print(f"\n✅ TEST TERMINÉ")

def demonstrate_formula_components():
    """Démonstration des composants de la formule."""
    print(f"\n🔬 DÉMONSTRATION FORMULE n.a = (1-m.r.a) × Dh²/(2×Rn)")
    print("=" * 60)
    
    # Paramètres de base
    distance_m = 200.0  # 200m
    rayon_terre_m = 6371000.0  # Rayon terrestre
    
    # Différents coefficients de réfraction
    coefficients = [0.10, 0.13, 0.15, 0.20]  # Différentes conditions atmosphériques
    
    print(f"Distance: {distance_m}m")
    print(f"Rayon terrestre: {rayon_terre_m/1000:.0f}km")
    print(f"\n{'m.r.a':<6} {'(1-m.r.a)':<10} {'Dh²':<12} {'2×Rn':<12} {'n.a (mm)':<10}")
    print("-" * 60)
    
    for coeff in coefficients:
        factor = 1.0 - coeff
        dh_square = distance_m ** 2
        two_rn = 2.0 * rayon_terre_m
        
        correction_m = factor * dh_square / two_rn
        correction_mm = correction_m * 1000
        
        print(f"{coeff:<6.2f} {factor:<10.3f} {dh_square:<12.0f} {two_rn:<12.0f} {correction_mm:<10.3f}")
    
    print("-" * 60)
    print("💡 Plus le coefficient de réfraction est élevé, plus la correction diminue")
    print("💡 La correction est proportionnelle au carré de la distance")

if __name__ == "__main__":
    test_level_apparent_correction()
    demonstrate_formula_components()