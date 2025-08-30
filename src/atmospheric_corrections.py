"""
Module de corrections atmosphériques pour nivellement géométrique.

Ce module implémente les corrections de réfraction atmosphérique et de courbure
terrestre selon les standards géodésiques internationaux.

Formules appliquées:
- Correction courbure: C₁ = k × d² / (2R)
- Correction réfraction: C₂ = r × d² / (2R)  
- Correction totale: C = (k - r) × d² / (2R)

Références:
- IGN : Instructions techniques de nivellement
- IAG : Standards géodésiques internationaux
- ISO 17123-2 : Procédures d'essai instruments géodésiques

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm avec corrections atmosphériques
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import math

from .exceptions import CalculationError, validate_positive_number


# Constantes géodésiques
EARTH_RADIUS_M = 6371000.0  # Rayon moyen terrestre (m)
STANDARD_REFRACTION_COEFF = 0.13  # Coefficient de réfraction standard
CURVATURE_COEFF = 1.0  # Coefficient de courbure terrestre


@dataclass
class AtmosphericConditions:
    """Conditions atmosphériques pour calcul de réfraction."""
    temperature_celsius: float = 15.0  # Température (°C)
    pressure_hpa: float = 1013.25  # Pression atmosphérique (hPa)
    humidity_percent: float = 60.0  # Humidité relative (%)
    time_of_day: Optional[datetime] = None  # Heure de mesure
    weather_condition: str = "normal"  # Conditions météo


@dataclass
class RefractionCorrection:
    """Résultat d'une correction de réfraction."""
    distance_m: float
    raw_delta_h: float
    curvature_correction_mm: float
    refraction_correction_mm: float 
    total_correction_mm: float
    corrected_delta_h: float
    refraction_coefficient: float
    level_apparent_correction_mm: float = 0.0  # Nouvelle correction n.a

@dataclass 
class LevelApparentCorrection:
    """Correction de niveau apparent selon la réfraction atmosphérique."""
    distance_m: float
    delta_h_m: float
    module_refraction_atm: float
    correction_mm: float
    formula_used: str = "n.a = (1-m.r.a) × Dh²/(2×Rn)"


class AtmosphericCorrector:
    """
    Calculateur de corrections atmosphériques pour nivellement géométrique.
    
    Implémente les corrections selon les normes internationales avec
    adaptation aux conditions locales.
    """
    
    def __init__(self, 
                 earth_radius_m: float = EARTH_RADIUS_M,
                 standard_refraction: float = STANDARD_REFRACTION_COEFF):
        """
        Initialisation du correcteur atmosphérique.
        
        Args:
            earth_radius_m: Rayon terrestre local (m)
            standard_refraction: Coefficient de réfraction par défaut
        """
        self.earth_radius = earth_radius_m
        self.standard_refraction = standard_refraction
        
    def calculate_refraction_coefficient(self, 
                                       conditions: AtmosphericConditions) -> float:
        """
        Calcul du coefficient de réfraction selon conditions atmosphériques.
        
        Formule empirique basée sur :
        - Température et pression (effet principal)
        - Humidité (effet secondaire)
        - Heure de mesure (gradient thermique)
        
        Args:
            conditions: Conditions atmosphériques
            
        Returns:
            float: Coefficient de réfraction ajusté
        """
        try:
            # Base standard
            k_base = self.standard_refraction
            
            # Correction température (effet principal)
            # Référence : 15°C
            temp_correction = -(conditions.temperature_celsius - 15.0) * 0.004
            
            # Correction pression
            # Référence : 1013.25 hPa
            pressure_correction = (conditions.pressure_hpa - 1013.25) * 0.0001
            
            # Correction humidité (effet mineur)
            humidity_correction = (conditions.humidity_percent - 60.0) * 0.0002
            
            # Correction heure de mesure (gradient thermique)
            time_correction = 0.0
            if conditions.time_of_day:
                hour = conditions.time_of_day.hour
                if 10 <= hour <= 16:  # Heures chaudes
                    time_correction = 0.02
                elif hour <= 8 or hour >= 18:  # Heures fraîches
                    time_correction = -0.01
            
            # Coefficient final
            k_adjusted = (k_base + temp_correction + pressure_correction + 
                         humidity_correction + time_correction)
            
            # Limites de sécurité
            k_adjusted = max(0.05, min(0.25, k_adjusted))
            
            return k_adjusted
            
        except Exception as e:
            print(f"⚠️ Erreur calcul coefficient réfraction: {e}")
            return self.standard_refraction
    
    def calculate_level_apparent_correction(self, 
                                          distance_m: float, 
                                          delta_h_m: float,
                                          refraction_coeff: float) -> float:
        """
        Calcul de la correction de niveau apparent selon la réfraction atmosphérique.
        
        Implémente les formules des images :
        n.a = (1 - m.r.a) × Dh² / (2 × Rn)
        
        Où :
        - m.r.a = module de réfraction atmosphérique
        - Dh = distance réduite à l'horizon (≈ distance_m pour courtes portées)
        - Rn = rayon normal de la Terre (6371000 m)
        
        Args:
            distance_m: Distance de visée (m)
            delta_h_m: Dénivelée mesurée (m)
            refraction_coeff: Coefficient de réfraction calculé
            
        Returns:
            float: Correction niveau apparent en millimètres
        """
        try:
            # Module de réfraction atmosphérique (m.r.a)
            # Basé sur le coefficient de réfraction ajusté aux conditions
            module_refraction_atm = refraction_coeff
            
            # Distance réduite à l'horizon (approximation pour courtes portées)
            # Dh ≈ distance horizontale pour des portées < 2km
            dh_horizon = distance_m
            
            # Rayon normal de courbure (Rn)
            # Pour la géodésie, on utilise le rayon moyen terrestre
            rayon_normal = self.earth_radius
            
            # Formule principal : n.a = (1 - m.r.a) × Dh² / (2 × Rn)
            correction_niveau_apparent_m = (
                (1.0 - module_refraction_atm) * 
                (dh_horizon ** 2) / 
                (2.0 * rayon_normal)
            )
            
            # Conversion en millimètres
            correction_mm = correction_niveau_apparent_m * 1000
            
            # La correction a le signe de la correction de sphéricité
            # Selon les images, elle dépend du signe de la correction de sphéricité
            return correction_mm
            
        except Exception as e:
            print(f"⚠️ Erreur calcul niveau apparent: {e}")
            return 0.0
    
    def calculate_atmospheric_correction(self, 
                                       distance_m: float,
                                       raw_delta_h: float,
                                       conditions: Optional[AtmosphericConditions] = None) -> RefractionCorrection:
        """
        Calcul de la correction atmosphérique complète.
        
        Théorie:
        C_total = (k - r) × d² / (2R)
        
        Où:
        - k = 1.0 (courbure terrestre)
        - r = coefficient de réfraction variable
        - d = distance de visée (m)
        - R = rayon terrestre (m)
        
        Args:
            distance_m: Distance de visée (m)
            raw_delta_h: Dénivelée brute observée (m)
            conditions: Conditions atmosphériques
            
        Returns:
            RefractionCorrection: Correction calculée
        """
        validate_positive_number(distance_m, "distance", allow_zero=False)
        
        if conditions is None:
            conditions = AtmosphericConditions()
        
        try:
            # Coefficient de réfraction ajusté
            refraction_coeff = self.calculate_refraction_coefficient(conditions)
            
            # Distance au carré pour les formules
            d_squared = distance_m ** 2
            
            # Correction de courbure terrestre (toujours positive)
            curvature_correction_m = CURVATURE_COEFF * d_squared / (2 * self.earth_radius)
            
            # Correction de réfraction atmosphérique (généralement négative)
            refraction_correction_m = -refraction_coeff * d_squared / (2 * self.earth_radius)
            
            # Correction totale
            total_correction_m = curvature_correction_m + refraction_correction_m
            
            # Conversion en millimètres
            curvature_mm = curvature_correction_m * 1000
            refraction_mm = refraction_correction_m * 1000
            total_mm = total_correction_m * 1000
            
            # Dénivelée corrigée
            corrected_delta_h = raw_delta_h + total_correction_m
            
            # Calcul de la correction de niveau apparent selon les images
            level_apparent_correction_mm = self.calculate_level_apparent_correction(
                distance_m, raw_delta_h, refraction_coeff
            )
            
            # Dénivelée finale avec correction niveau apparent
            final_corrected_delta_h = raw_delta_h + total_correction_m + (level_apparent_correction_mm / 1000)
            
            return RefractionCorrection(
                distance_m=distance_m,
                raw_delta_h=raw_delta_h,
                curvature_correction_mm=curvature_mm,
                refraction_correction_mm=refraction_mm,
                total_correction_mm=total_mm,
                corrected_delta_h=final_corrected_delta_h,
                refraction_coefficient=refraction_coeff,
                level_apparent_correction_mm=level_apparent_correction_mm
            )
            
        except Exception as e:
            raise CalculationError(
                f"Erreur calcul correction atmosphérique: {str(e)}",
                calculation_type="atmospheric_correction",
                input_values={'distance': distance_m, 'delta_h': raw_delta_h}
            )
    
    def apply_corrections_to_dataframe(self, 
                                     df: pd.DataFrame,
                                     ar_columns: List[str],
                                     av_columns: List[str], 
                                     dist_columns: List[str],
                                     conditions: Optional[AtmosphericConditions] = None) -> pd.DataFrame:
        """
        Application des corrections atmosphériques à un DataFrame complet.
        
        Args:
            df: DataFrame avec observations
            ar_columns: Colonnes lectures arrière
            av_columns: Colonnes lectures avant
            dist_columns: Colonnes distances
            conditions: Conditions atmosphériques
            
        Returns:
            pd.DataFrame: DataFrame avec corrections appliquées
        """
        df_corrected = df.copy()
        
        if conditions is None:
            conditions = AtmosphericConditions()
        
        # Appliquer corrections pour chaque paire AR/AV
        for i, (ar_col, av_col) in enumerate(zip(ar_columns, av_columns)):
            # Colonnes de sortie
            delta_h_raw_col = f"delta_h_raw_{i+1}"
            delta_h_corrected_col = f"delta_h_corrected_{i+1}"
            correction_col = f"atmospheric_correction_mm_{i+1}"
            
            # Calculer dénivelées brutes
            df_corrected[delta_h_raw_col] = df_corrected[ar_col] - df_corrected[av_col]
            
            # Initialiser colonnes de correction
            df_corrected[delta_h_corrected_col] = np.nan
            df_corrected[correction_col] = np.nan
            
            # Distance pour les corrections
            if i < len(dist_columns) and dist_columns[i] in df_corrected.columns:
                dist_col = dist_columns[i]
            else:
                # Distance par défaut si manquante
                df_corrected[f'dist_default_{i+1}'] = 100.0
                dist_col = f'dist_default_{i+1}'
            
            # Appliquer corrections ligne par ligne
            for idx, row in df_corrected.iterrows():
                try:
                    raw_delta = row[delta_h_raw_col]
                    distance = row[dist_col]
                    
                    if pd.notna(raw_delta) and pd.notna(distance) and distance > 0:
                        correction = self.calculate_atmospheric_correction(
                            distance, raw_delta, conditions
                        )
                        
                        df_corrected.loc[idx, delta_h_corrected_col] = correction.corrected_delta_h
                        df_corrected.loc[idx, correction_col] = correction.total_correction_mm
                        
                except Exception as e:
                    print(f"⚠️ Erreur correction ligne {idx}: {e}")
                    # Garder valeur brute en cas d'erreur
                    df_corrected.loc[idx, delta_h_corrected_col] = row[delta_h_raw_col]
                    df_corrected.loc[idx, correction_col] = 0.0
        
        # Calculer dénivelée finale (moyenne des instruments corrigés)
        corrected_cols = [col for col in df_corrected.columns if col.startswith('delta_h_corrected_')]
        if corrected_cols:
            df_corrected['delta_h_final'] = df_corrected[corrected_cols].mean(axis=1, skipna=True)
        
        return df_corrected
    
    def generate_correction_report(self, corrections: List[RefractionCorrection]) -> str:
        """Génère un rapport des corrections atmosphériques."""
        if not corrections:
            return "Aucune correction calculée"
        
        total_corrections = [c.total_correction_mm for c in corrections]
        distances = [c.distance_m for c in corrections]
        
        report = f"""
=== RAPPORT CORRECTIONS ATMOSPHÉRIQUES ===

📊 STATISTIQUES GÉNÉRALES:
   Observations corrigées: {len(corrections)}
   Distance min: {min(distances):.1f} m
   Distance max: {max(distances):.1f} m
   Distance moyenne: {np.mean(distances):.1f} m

🌡️ CORRECTIONS APPLIQUÉES:
   Correction min: {min(total_corrections):.2f} mm
   Correction max: {max(total_corrections):.2f} mm
   Correction moyenne: {np.mean(total_corrections):.2f} mm
   Correction totale: {sum(total_corrections):.2f} mm

🎯 IMPACT SUR PRÉCISION:
   Écart-type corrections: {np.std(total_corrections):.2f} mm
   Correction RMS: {np.sqrt(np.mean([c**2 for c in total_corrections])):.2f} mm

📈 ANALYSE PAR DISTANCE:"""
        
        # Analyse par tranches de distance
        distance_ranges = [(0, 50), (50, 100), (100, 200), (200, float('inf'))]
        
        for min_d, max_d in distance_ranges:
            range_corrections = [c.total_correction_mm for c in corrections 
                               if min_d <= c.distance_m < max_d]
            if range_corrections:
                range_label = f"{min_d}-{max_d if max_d != float('inf') else '∞'}m"
                mean_corr = np.mean(range_corrections)
                count = len(range_corrections)
                report += f"\n   {range_label}: {count} obs, moyenne {mean_corr:.2f}mm"
        
        return report


def create_standard_conditions(location: str = "france") -> AtmosphericConditions:
    """Crée des conditions atmosphériques standard selon la localisation."""
    
    if location.lower() == "france":
        return AtmosphericConditions(
            temperature_celsius=15.0,
            pressure_hpa=1013.25,
            humidity_percent=65.0,
            weather_condition="temperate"
        )
    elif location.lower() in ["sahel", "africa"]:  # Pour vos projets en Afrique
        return AtmosphericConditions(
            temperature_celsius=28.0,
            pressure_hpa=1010.0,
            humidity_percent=45.0,
            weather_condition="tropical_dry"
        )
    else:
        return AtmosphericConditions()  # Conditions standard


def calculate_correction_significance(distance_m: float) -> Dict[str, float]:
    """
    Évalue la significativité des corrections selon la distance.
    
    Returns:
        Dict avec corrections en mm pour différentes distances
    """
    corrector = AtmosphericCorrector()
    conditions = AtmosphericConditions()
    
    correction = corrector.calculate_atmospheric_correction(distance_m, 0.0, conditions)
    
    return {
        'distance_m': distance_m,
        'correction_mm': correction.total_correction_mm,
        'significance': 'négligeable' if abs(correction.total_correction_mm) < 0.1 
                       else 'faible' if abs(correction.total_correction_mm) < 1.0
                       else 'modérée' if abs(correction.total_correction_mm) < 5.0
                       else 'importante'
    }


# Exemple d'utilisation et tests
if __name__ == "__main__":
    print("🌡️ TEST MODULE CORRECTIONS ATMOSPHÉRIQUES")
    print("=" * 50)
    
    # Test avec différentes distances
    corrector = AtmosphericCorrector()
    conditions = create_standard_conditions("france")
    
    test_distances = [50, 100, 150, 200, 300]
    
    for distance in test_distances:
        correction = corrector.calculate_atmospheric_correction(
            distance, 0.1, conditions  # 0.1m de dénivelée test
        )
        
        print(f"Distance {distance}m:")
        print(f"  Correction totale: {correction.total_correction_mm:.2f}mm")
        print(f"  Courbure: {correction.curvature_correction_mm:.2f}mm")
        print(f"  Réfraction: {correction.refraction_correction_mm:.2f}mm")
        print()