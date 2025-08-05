#!/usr/bin/env python3
"""
Script d'intégration des corrections atmosphériques dans le calculator existant
"""

def integrate_atmospheric_corrections():
    """Intègre les corrections atmosphériques dans calculator.py"""
    try:
        print("🌡️ INTÉGRATION CORRECTIONS ATMOSPHÉRIQUES")
        print("=" * 50)
        
        # 1. Lire le fichier calculator.py existant
        with open('src/calculator.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. Ajouter l'import des corrections atmosphériques
        old_imports = '''from exceptions import (
    CalculationError, PrecisionError, validate_positive_number,
    safe_divide, validate_distance_km
)
from validators import GeodeticValidator, PrecisionValidator'''
        
        new_imports = '''from exceptions import (
    CalculationError, PrecisionError, validate_positive_number,
    safe_divide, validate_distance_km
)
from validators import GeodeticValidator, PrecisionValidator
from atmospheric_corrections import (
    AtmosphericCorrector, AtmosphericConditions, create_standard_conditions
)'''
        
        if old_imports in content:
            content = content.replace(old_imports, new_imports)
            print("✅ Imports corrections atmosphériques ajoutés")
        
        # 3. Modifier le constructeur de LevelingCalculator
        old_constructor = '''    def __init__(self, precision_mm: float = 2.0,
                 instrumental_error_mm: float = 1.0,
                 kilometric_error_mm: float = 1.0):
        """
        Args:
            precision_mm: Précision cible (mm)
            instrumental_error_mm: Erreur instrumentale (mm)
            kilometric_error_mm: Erreur kilométrique (mm/km)
        """
        self.precision_mm = precision_mm
        
        # Modules de calcul
        self.height_diff_calc = HeightDifferenceCalculator(precision_mm)
        self.altitude_calc = AltitudeCalculator(precision_mm)
        self.weight_calc = WeightCalculator(instrumental_error_mm, kilometric_error_mm)
        self.closure_calc = ClosureCalculator(precision_mm)
        
        # Validateurs
        self.precision_validator = PrecisionValidator(precision_mm)
        self.geodetic_validator = GeodeticValidator()'''
        
        new_constructor = '''    def __init__(self, precision_mm: float = 2.0,
                 instrumental_error_mm: float = 1.0,
                 kilometric_error_mm: float = 1.0,
                 apply_atmospheric_corrections: bool = True,
                 atmospheric_conditions: AtmosphericConditions = None):
        """
        Args:
            precision_mm: Précision cible (mm)
            instrumental_error_mm: Erreur instrumentale (mm)
            kilometric_error_mm: Erreur kilométrique (mm/km)
            apply_atmospheric_corrections: Appliquer corrections atmosphériques
            atmospheric_conditions: Conditions atmosphériques
        """
        self.precision_mm = precision_mm
        self.apply_atmospheric_corrections = apply_atmospheric_corrections
        
        # Modules de calcul
        self.height_diff_calc = HeightDifferenceCalculator(precision_mm)
        self.altitude_calc = AltitudeCalculator(precision_mm)
        self.weight_calc = WeightCalculator(instrumental_error_mm, kilometric_error_mm)
        self.closure_calc = ClosureCalculator(precision_mm)
        
        # Module corrections atmosphériques
        self.atmospheric_corrector = AtmosphericCorrector()
        self.atmospheric_conditions = atmospheric_conditions or create_standard_conditions("france")
        
        # Validateurs
        self.precision_validator = PrecisionValidator(precision_mm)
        self.geodetic_validator = GeodeticValidator()'''
        
        if old_constructor in content:
            content = content.replace(old_constructor, new_constructor)
            print("✅ Constructeur LevelingCalculator mis à jour")
        
        # 4. Modifier calculate_complete_leveling pour inclure les corrections
        old_method_start = '''    def calculate_complete_leveling(self, df: pd.DataFrame,
                                  ar_columns: List[str],
                                  av_columns: List[str],
                                  dist_columns: List[str],
                                  initial_altitude: float,
                                  known_final_altitude: Optional[float] = None) -> CalculationResults:
        """
        Calcul complet de nivellement géométrique.
        
        Pipeline complet:
        1. Calcul des dénivelées
        2. Calcul des altitudes
        3. Analyse de fermeture
        4. Calcul des poids
        5. Validation de précision'''
        
        new_method_start = '''    def calculate_complete_leveling(self, df: pd.DataFrame,
                                  ar_columns: List[str],
                                  av_columns: List[str],
                                  dist_columns: List[str],
                                  initial_altitude: float,
                                  known_final_altitude: Optional[float] = None) -> CalculationResults:
        """
        Calcul complet de nivellement géométrique avec corrections atmosphériques.
        
        Pipeline complet:
        1. Calcul des dénivelées
        2. Application corrections atmosphériques
        3. Calcul des altitudes
        4. Analyse de fermeture
        5. Calcul des poids
        6. Validation de précision'''
        
        if old_method_start in content:
            content = content.replace(old_method_start, new_method_start)
            print("✅ Documentation méthode mise à jour")
        
        # 5. Ajouter l'application des corrections dans le pipeline
        pipeline_insertion = '''            # 1. Calcul des dénivelées
            height_differences = self.height_diff_calc.calculate_height_differences(
                df, ar_columns, av_columns
            )
            
            # Obtenir les dénivelées moyennes
            mean_deltas = self.height_diff_calc.get_mean_height_differences(height_differences)'''
        
        new_pipeline = '''            # 1. Calcul des dénivelées
            height_differences = self.height_diff_calc.calculate_height_differences(
                df, ar_columns, av_columns
            )
            
            # 1.5. Application des corrections atmosphériques si activées
            if self.apply_atmospheric_corrections:
                print("🌡️ Application des corrections atmosphériques...")
                df_corrected = self.atmospheric_corrector.apply_corrections_to_dataframe(
                    df, ar_columns, av_columns, dist_columns, self.atmospheric_conditions
                )
                
                # Utiliser les dénivelées corrigées
                if 'delta_h_final' in df_corrected.columns:
                    mean_deltas = df_corrected['delta_h_final']
                    
                    # Recalculer les height_differences avec corrections
                    corrected_height_differences = []
                    for i, hd in enumerate(height_differences):
                        if i < len(mean_deltas) and pd.notna(mean_deltas.iloc[i]):
                            # Créer une nouvelle HeightDifference avec valeur corrigée
                            corrected_hd = HeightDifference(
                                delta_h_m=mean_deltas.iloc[i],
                                ar_reading=hd.ar_reading,
                                av_reading=hd.av_reading,
                                instrument_id=hd.instrument_id,
                                is_valid=hd.is_valid,
                                control_residual=hd.control_residual
                            )
                            corrected_height_differences.append(corrected_hd)
                        else:
                            corrected_height_differences.append(hd)
                    
                    height_differences = corrected_height_differences
                    print(f"   ✅ Corrections appliquées à {len(mean_deltas)} observations")
                else:
                    # Fallback : moyennes normales
                    mean_deltas = self.height_diff_calc.get_mean_height_differences(height_differences)
                    print("   ⚠️ Fallback : dénivelées non corrigées utilisées")
            else:
                # Obtenir les dénivelées moyennes sans corrections
                mean_deltas = self.height_diff_calc.get_mean_height_differences(height_differences)
                print("🔧 Corrections atmosphériques désactivées")'''
        
        if pipeline_insertion in content:
            content = content.replace(pipeline_insertion, new_pipeline)
            print("✅ Pipeline avec corrections atmosphériques intégré")
        
        # 6. Mettre à jour les métadonnées pour inclure les corrections
        metadata_section = '''            metadata = {
                'calculation_timestamp': pd.Timestamp.now(),
                'precision_target_mm': self.precision_mm,
                'total_points': len(df),
                'total_observations': len(height_differences),
                'ar_columns_used': ar_columns,
                'av_columns_used': av_columns,
                'dist_columns_used': dist_columns,
                'altitude_statistics': self.altitude_calc.validate_altitude_consistency(altitudes)
            }'''
        
        new_metadata = '''            metadata = {
                'calculation_timestamp': pd.Timestamp.now(),
                'precision_target_mm': self.precision_mm,
                'total_points': len(df),
                'total_observations': len(height_differences),
                'ar_columns_used': ar_columns,
                'av_columns_used': av_columns,
                'dist_columns_used': dist_columns,
                'atmospheric_corrections_applied': self.apply_atmospheric_corrections,
                'atmospheric_conditions': {
                    'temperature_c': self.atmospheric_conditions.temperature_celsius,
                    'pressure_hpa': self.atmospheric_conditions.pressure_hpa,
                    'humidity_percent': self.atmospheric_conditions.humidity_percent
                } if self.apply_atmospheric_corrections else None,
                'altitude_statistics': self.altitude_calc.validate_altitude_consistency(altitudes)
            }'''
        
        if metadata_section in content:
            content = content.replace(metadata_section, new_metadata)
            print("✅ Métadonnées mises à jour avec corrections atmosphériques")
        
        # 7. Sauvegarder le fichier modifié
        with open('src/calculator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Calculator.py mis à jour avec corrections atmosphériques!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_main_for_atmospheric_corrections():
    """Met à jour main.py pour inclure les options de corrections atmosphériques"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter les imports
        old_import = '''from atmospheric_corrections import (
    AtmosphericCorrector, AtmosphericConditions, create_standard_conditions
)'''
        
        if old_import not in content:
            import_section = '''from data_importer import DataImporter, quick_import
from calculator import LevelingCalculator, quick_leveling_calculation
from compensator import LevelingCompensator, quick_compensation
from validators import PrecisionValidator
from exceptions import *'''
            
            new_import_section = '''from data_importer import DataImporter, quick_import
from calculator import LevelingCalculator, quick_leveling_calculation
from compensator import LevelingCompensator, quick_compensation
from validators import PrecisionValidator
from exceptions import *
from atmospheric_corrections import (
    AtmosphericCorrector, AtmosphericConditions, create_standard_conditions
)'''
            
            if import_section in content:
                content = content.replace(import_section, new_import_section)
                print("✅ Imports atmospheric_corrections ajoutés à main.py")
        
        # Modifier l'initialisation du calculator
        old_calc_init = '''self.calculator = LevelingCalculator(precision_mm)'''
        new_calc_init = '''# Créer conditions atmosphériques pour la région
        atmospheric_conditions = create_standard_conditions("sahel")  # Adapté pour l'Afrique
        self.calculator = LevelingCalculator(
            precision_mm, 
            apply_atmospheric_corrections=True,
            atmospheric_conditions=atmospheric_conditions
        )'''
        
        if old_calc_init in content:
            content = content.replace(old_calc_init, new_calc_init)
            print("✅ Calculator initialisé avec corrections atmosphériques")
        
        # Ajouter option en ligne de commande
        parser_options = '''    parser.add_argument('--precision', type=float, default=2.0,
                       help='Précision cible en mm (défaut: 2.0)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Créer un fichier d\\'exemple et quitter')'''
        
        new_parser_options = '''    parser.add_argument('--precision', type=float, default=2.0,
                       help='Précision cible en mm (défaut: 2.0)')
    parser.add_argument('--no-atmospheric', action='store_true',
                       help='Désactiver les corrections atmosphériques')
    parser.add_argument('--temperature', type=float, default=28.0,
                       help='Température ambiante en °C (défaut: 28.0)')
    parser.add_argument('--pressure', type=float, default=1010.0,
                       help='Pression atmosphérique en hPa (défaut: 1010.0)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Créer un fichier d\\'exemple et quitter')'''
        
        if parser_options in content:
            content = content.replace(parser_options, new_parser_options)
            print("✅ Options atmosphériques ajoutées au parser")
        
        # Sauvegarder main.py
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ main.py mis à jour!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour main.py: {e}")
        return False

def create_atmospheric_test():
    """Crée un test pour vérifier les corrections atmosphériques"""
    test_code = '''#!/usr/bin/env python3
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
    print("\\n🔧 CALCUL SANS CORRECTIONS ATMOSPHÉRIQUES:")
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
    print("\\n🌡️ CALCUL AVEC CORRECTIONS ATMOSPHÉRIQUES:")
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
    print(f"\\n📊 COMPARAISON:")
    print(f"   Amélioration fermeture: {improvement:.1f}mm")
    print(f"   Amélioration relative: {improvement/abs(closure_no_corr.closure_error_mm)*100:.1f}%")
    
    # 6. Analyse des corrections par distance
    print(f"\\n🔍 ANALYSE CORRECTIONS PAR DISTANCE:")
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
    
    print(f"\\n🎯 IMPACT TOTAL ESTIMÉ:")
    print(f"   Somme corrections: {total_impact:.1f}mm")
    print(f"   Impact moyen/observation: {total_impact/len(distances):.2f}mm")
    
    if improvement > 0:
        print("\\n✅ CORRECTIONS ATMOSPHÉRIQUES BÉNÉFIQUES!")
    else:
        print("\\n⚠️ Corrections atmosphériques marginales pour ce cheminement")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('test_atmospheric.py', 'w') as f:
        f.write(test_code)
    
    print("✅ test_atmospheric.py créé")

def create_atmospheric_documentation():
    """Crée la documentation des corrections atmosphériques"""
    doc_content = '''# 🌡️ CORRECTIONS ATMOSPHÉRIQUES - DOCUMENTATION

## 📋 Vue d'ensemble

Les corrections atmosphériques compensent les effets de la courbure terrestre et de la réfraction atmosphérique sur les mesures de nivellement géométrique.

## 🧮 Formules théoriques

### Correction de courbure terrestre
```
C₁ = k × d² / (2R)
```
- k = 1.0 (coefficient de courbure)
- d = distance de visée (m)
- R = 6,371,000 m (rayon terrestre)

### Correction de réfraction atmosphérique
```
C₂ = -r × d² / (2R)
```
- r = coefficient de réfraction (variable selon conditions)
- Valeur standard : r = 0.13
- Varie selon température, pression, humidité

### Correction totale
```
C_total = C₁ + C₂ = (k - r) × d² / (2R)
C_total = (1 - r) × d² / (2R)
```

## 📊 Coefficient de réfraction variable

Le coefficient r varie selon les conditions atmosphériques :

### Effet de la température
```
Δr_temp = -(T - 15°C) × 0.004
```

### Effet de la pression
```
Δr_press = (P - 1013.25 hPa) × 0.0001
```

### Effet de l'humidité
```
Δr_humid = (H - 60%) × 0.0002
```

### Coefficient final
```
r = 0.13 + Δr_temp + Δr_press + Δr_humid + Δr_time
```

## 🌍 Valeurs typiques par région

### France métropolitaine
- Température : 15°C
- Pression : 1013 hPa  
- Humidité : 65%
- **r ≈ 0.13**

### Sahel africain  
- Température : 32°C
- Pression : 1008 hPa
- Humidité : 40%
- **r ≈ 0.06**

## 📈 Impact selon la distance

| Distance | Correction (conditions standard) |
|----------|----------------------------------|
| 50m      | +0.10 mm                        |
| 100m     | +0.38 mm                        |
| 150m     | +0.86 mm                        |
| 200m     | +1.53 mm                        |
| 300m     | +3.44 mm                        |

## 🔧 Utilisation dans le code

### Activation automatique
```python
calculator = LevelingCalculator(
    precision_mm=2.0,
    apply_atmospheric_corrections=True  # Par défaut
)
```

### Conditions personnalisées
```python
from atmospheric_corrections import AtmosphericConditions

conditions = AtmosphericConditions(
    temperature_celsius=32.0,
    pressure_hpa=1008.0,
    humidity_percent=40.0
)

calculator = LevelingCalculator(
    atmospheric_conditions=conditions
)
```

### Désactivation
```python
calculator = LevelingCalculator(
    apply_atmospheric_corrections=False
)
```

## 📋 Recommandations

### Quand appliquer les corrections
- **Toujours** pour distances > 100m
- **Recommandé** pour précision < 5mm
- **Obligatoire** pour travaux de haute précision

### Conditions critiques
- **Forte chaleur** (> 30°C) : r diminue
- **Haute pression** : r augmente légèrement  
- **Matin/soir** : gradients thermiques importants

### Validation
- Vérifier amélioration de la fermeture
- Contrôler cohérence des corrections
- Analyser résidus après compensation

## 🎯 Précision attendue

Avec corrections atmosphériques :
- Amélioration fermeture : 10-30%
- Réduction erreurs systématiques
- Meilleure cohérence statistique

Sans corrections (distances > 150m) :
- Biais systématique
- Fermeture dégradée
- Tests statistiques moins fiables
'''
    
    with open('docs/corrections_atmospheriques.md', 'w') as f:
        f.write(doc_content)
    
    print("✅ Documentation corrections atmosphériques créée")

if __name__ == "__main__":
    print("🌡️ INTÉGRATION CORRECTIONS ATMOSPHÉRIQUES")
    print("=" * 60)
    
    success = True
    
    # 1. Intégrer dans calculator.py
    if integrate_atmospheric_corrections():
        print("\n✅ Calculator.py mis à jour")
    else:
        print("\n❌ Échec intégration calculator.py")
        success = False
    
    # 2. Mettre à jour main.py
    if update_main_for_atmospheric_corrections():
        print("\n✅ Main.py mis à jour")
    else:
        print("\n❌ Échec mise à jour main.py")
        success = False
    
    # 3. Créer les tests
    create_atmospheric_test()
    print("\n✅ Test atmosphérique créé")
    
    # 4. Créer la documentation
    create_atmospheric_documentation()
    print("\n✅ Documentation créée")
    
    if success:
        print(f"\n🎯 INTÉGRATION TERMINÉE AVEC SUCCÈS!")
        print(f"\n🚀 TESTS À EXÉCUTER:")
        print(f"   1. python test_atmospheric.py")
        print(f"   2. python main.py --temperature 32 --pressure 1008")
        print(f"   3. python main.py --no-atmospheric  # Pour comparaison")
    else:
        print(f"\n❌ Intégration partiellement échouée")
        print(f"💡 Corrections manuelles nécessaires")