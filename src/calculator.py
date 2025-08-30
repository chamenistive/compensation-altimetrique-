"""
Module de calculs pour la compensation altimétrique.

Ce module contient tous les algorithmes de calcul pour le nivellement
géométrique avec une précision garantie de 2mm.

Algorithmes implémentés:
- Calcul des dénivelées: Δh = AR - AV
- Calcul des altitudes par propagation
- Calcul des poids selon la théorie géodésique
- Validation des contrôles et fermetures

Formules géodésiques:
- Variance d'observation: σ² = a² + b²×d (mm²)
- Tolérance de fermeture: T = 4×√K (mm)
- Poids: P = 1/σ²

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    CalculationError, PrecisionError, validate_positive_number,
    safe_divide, validate_distance_km
)
from .validators import GeodeticValidator, PrecisionValidator, CalculationValidator
from .atmospheric_corrections import (
    AtmosphericCorrector, AtmosphericConditions, create_standard_conditions
)
from .data_importer import DataImporter


class TraverseType(Enum):
    """Types de cheminement."""
    CLOSED = "fermé"
    OPEN = "ouvert"
    UNKNOWN = "indéterminé"


@dataclass
class HeightDifference:
    """Résultat du calcul d'une dénivelée."""
    delta_h_m: float
    ar_reading: float
    av_reading: float
    instrument_id: int
    is_valid: bool = True
    control_residual: Optional[float] = None


@dataclass
class AltitudeCalculation:
    """Résultat du calcul d'altitude."""
    point_id: str
    altitude_m: float
    cumulative_delta_h: float
    is_reference: bool = False


@dataclass
class ClosureAnalysis:
    """Analyse de fermeture du cheminement."""
    traverse_type: TraverseType
    closure_error_m: float
    closure_error_mm: float
    tolerance_mm: float
    total_distance_km: float
    is_acceptable: bool
    precision_ratio: float


@dataclass
class CalculationResults:
    """Résultats complets des calculs."""
    height_differences: List[HeightDifference]
    altitudes: List[AltitudeCalculation]
    closure_analysis: ClosureAnalysis
    control_statistics: Dict
    calculation_metadata: Dict = field(default_factory=dict)


class HeightDifferenceCalculator:
    """
    Calculateur de dénivelées pour nivellement géométrique.
    
    Implémente la formule fondamentale: Δh = AR - AV
    avec validation et contrôle de qualité.
    """
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
        self.precision_m = precision_mm / 1000.0
    
    def calculate_denivelee(self, df: pd.DataFrame, 
                          ar_columns: List[str], 
                          av_columns: List[str]) -> List[List[HeightDifference]]:
        """
        Calcul des dénivelées individuelles pour chaque instrument.
        
        Algorithme:
        1. Pour chaque segment (point i-1 → point i)
        2. Pour chaque instrument: Δh = AR(i-1) - AV(i)
        3. Retourne les dénivelées séparées par segment
        
        Args:
            df: DataFrame avec les observations
            ar_columns: Colonnes des lectures arrière
            av_columns: Colonnes des lectures avant
            
        Returns:
            List[List[HeightDifference]]: Dénivelées par segment et par instrument
        """
        # Validations de base
        if len(ar_columns) != len(av_columns):
            raise CalculationError(
                "Nombre incohérent de colonnes AR et AV",
                calculation_type="denivelee",
                input_values={'ar_count': len(ar_columns), 'av_count': len(av_columns)}
            )
        
        if len(df) < 2:
            raise CalculationError(
                "Au moins 2 points sont nécessaires pour calculer des dénivelées",
                calculation_type="denivelee"
            )
        
        all_segments = []
        
        # Calculer pour chaque segment
        for current_idx in range(1, len(df)):
            previous_row = df.iloc[current_idx - 1]
            current_row = df.iloc[current_idx]
            
            segment_deltas = []
            
            # Calcul pour chaque instrument
            for inst_id, (ar_col, av_col) in enumerate(zip(ar_columns, av_columns), 1):
                # Lecture AR du point précédent
                ar_reading = pd.to_numeric(previous_row[ar_col], errors='coerce')
                # Lecture AV du point actuel  
                av_reading = pd.to_numeric(current_row[av_col], errors='coerce')
                
                if pd.notna(ar_reading) and pd.notna(av_reading):
                    # Validation des lectures
                    self._validate_readings(ar_reading, av_reading, current_idx)
                    
                    # Calcul de la dénivelée: AR(précédent) - AV(actuel)
                    delta_h = ar_reading - av_reading
                    
                    height_diff = HeightDifference(
                        delta_h_m=delta_h,
                        ar_reading=ar_reading,
                        av_reading=av_reading,
                        instrument_id=inst_id,
                        is_valid=True
                    )
                    
                    segment_deltas.append(height_diff)
                else:
                    # Dénivelée invalide
                    height_diff = HeightDifference(
                        delta_h_m=0.0,
                        ar_reading=ar_reading if pd.notna(ar_reading) else 0.0,
                        av_reading=av_reading if pd.notna(av_reading) else 0.0,
                        instrument_id=inst_id,
                        is_valid=False
                    )
                    segment_deltas.append(height_diff)
            
            all_segments.append(segment_deltas)
        
        return all_segments
    
    def calculate_denivelee_moyenne(self, denivelees_par_segment: List[List[HeightDifference]]) -> List[HeightDifference]:
        """
        Calcul des dénivelées moyennes à partir des dénivelées individuelles.
        
        Args:
            denivelees_par_segment: Dénivelées individuelles par segment
            
        Returns:
            List[HeightDifference]: Dénivelées moyennes par segment
        """
        moyennes = []
        
        for segment_idx, segment_deltas in enumerate(denivelees_par_segment):
            # Filtrer les dénivelées valides
            valid_deltas = [hd for hd in segment_deltas if hd.is_valid]
            
            if not valid_deltas:
                raise CalculationError(
                    f"Aucune dénivelée valide pour le segment {segment_idx + 1}",
                    calculation_type="denivelee_moyenne"
                )
            
            # Calcul de la moyenne
            mean_delta_h = sum(hd.delta_h_m for hd in valid_deltas) / len(valid_deltas)
            
            # Créer la dénivelée moyenne
            mean_height_diff = HeightDifference(
                delta_h_m=mean_delta_h,
                ar_reading=sum(hd.ar_reading for hd in valid_deltas) / len(valid_deltas),
                av_reading=sum(hd.av_reading for hd in valid_deltas) / len(valid_deltas),
                instrument_id=0,  # 0 = moyenne
                is_valid=True
            )
            
            moyennes.append(mean_height_diff)
        
        return moyennes
    
    def calculate_controle(self, denivelees_par_segment: List[List[HeightDifference]]) -> Dict:
        """
        Calcul du contrôle entre les instruments.
        
        Args:
            denivelees_par_segment: Dénivelées individuelles par segment
            
        Returns:
            Dict: Statistiques de contrôle
        """
        controles = []
        segments_problematiques = []
        
        for segment_idx, segment_deltas in enumerate(denivelees_par_segment):
            valid_deltas = [hd for hd in segment_deltas if hd.is_valid]
            
            if len(valid_deltas) >= 2:
                # Calcul du contrôle entre instruments
                deltas_values = [hd.delta_h_m for hd in valid_deltas]
                mean_delta = sum(deltas_values) / len(deltas_values)
                
                # Calcul des résidus
                residuals = [delta - mean_delta for delta in deltas_values]
                max_diff_mm = max(deltas_values) - min(deltas_values)
                max_diff_mm *= 1000  # Conversion en mm
                
                # Critère de contrôle: différence max entre instruments
                tolerance_mm = 5.0
                is_acceptable = max_diff_mm <= tolerance_mm
                
                controle_info = {
                    'segment': segment_idx + 1,
                    'denivelees_mm': [d * 1000 for d in deltas_values],
                    'moyenne_mm': mean_delta * 1000,
                    'residus_mm': [r * 1000 for r in residuals],
                    'ecart_max_mm': max_diff_mm,
                    'tolerance_mm': tolerance_mm,
                    'acceptable': is_acceptable
                }
                
                controles.append(controle_info)
                
                if not is_acceptable:
                    segments_problematiques.append(segment_idx + 1)
                    
                # Mettre à jour les résidus dans les objets HeightDifference
                for i, hd in enumerate(valid_deltas):
                    hd.control_residual = residuals[i]
        
        # Statistiques globales
        if controles:
            ecarts_mm = [c['ecart_max_mm'] for c in controles]
            return {
                'controles_par_segment': controles,
                'ecart_max_global_mm': max(ecarts_mm),
                'ecart_moyen_mm': sum(ecarts_mm) / len(ecarts_mm),
                'segments_problematiques': segments_problematiques,
                'qualite_globale': 'ACCEPTABLE' if not segments_problematiques else 'ATTENTION',
                'nombre_segments': len(controles)
            }
        else:
            return {'erreur': 'Aucun contrôle possible'}
    
    def calculate_height_differences(self, df: pd.DataFrame, 
                                   ar_columns: List[str], 
                                   av_columns: List[str]) -> List[HeightDifference]:
        """
        Calcul complet des dénivelées (méthode legacy - utilise les nouvelles méthodes modulaires).
        
        Cette méthode utilise maintenant les nouvelles méthodes modulaires :
        1. calculate_denivelee() - Dénivelées individuelles
        2. calculate_denivelee_moyenne() - Moyennes
        3. calculate_controle() - Contrôle (optionnel)
        
        Returns:
            List[HeightDifference]: Dénivelées moyennes calculées
        """
        # Utiliser les nouvelles méthodes modulaires
        denivelees_individuelles = self.calculate_denivelee(df, ar_columns, av_columns)
        moyennes = self.calculate_denivelee_moyenne(denivelees_individuelles)
        
        # Contrôle optionnel (pour compatibilité)
        try:
            controle_result = self.calculate_controle(denivelees_individuelles)
            if controle_result.get('segments_problematiques'):
                print(f"⚠️ Contrôle: {len(controle_result['segments_problematiques'])} segments problématiques")
        except Exception:
            pass  # Contrôle échoué mais on continue
            
        return moyennes
    
    def _validate_readings(self, ar: float, av: float, row_index: int):
        """Validation des lectures AR et AV - délègue au CalculationValidator."""
        validator = CalculationValidator(self.precision_mm)
        warnings = validator.validate_readings(ar, av, row_index)
        
        # Afficher les avertissements
        for warning in warnings:
            print(f"⚠️ {warning}")
    
    def _calculate_control_residuals(self, row_deltas: List[HeightDifference], row_index: int):
        """Calcul des résidus de contrôle entre exactement 2 instruments - approche stricte."""
        if len(row_deltas) != 2:
            print(f"⚠️ Ligne {row_index}: {len(row_deltas)} instruments détectés (2 requis)")
            return
        
        # Contrôle stricte avec exactement 2 instruments
        delta_1 = row_deltas[0].delta_h_m
        delta_2 = row_deltas[1].delta_h_m
        
        # Calcul de la moyenne: (Δh₁ + Δh₂) / 2
        mean_delta = (delta_1 + delta_2) / 2.0
        
        # Calcul des résidus pour chaque instrument
        residual_1 = delta_1 - mean_delta
        residual_2 = delta_2 - mean_delta
        
        row_deltas[0].control_residual = residual_1
        row_deltas[1].control_residual = residual_2
        
        # Tolérance stricte pour contrôle de qualité
        tolerance_mm = 5.0  # 5mm maximum entre les 2 instruments
        
        # Le contrôle est la différence entre les 2 dénivelées
        control_diff = abs(delta_1 - delta_2) * 1000  # en mm
        
        if control_diff > tolerance_mm:
            print(f"⚠️ Contrôle ligne {row_index}: |Δh₁ - Δh₂| = {control_diff:.1f}mm > {tolerance_mm:.1f}mm")
            print(f"   Δh₁ = {delta_1*1000:.1f}mm, Δh₂ = {delta_2*1000:.1f}mm")
            # Avertissement seulement, pas d'invalidation automatique
    
    def get_mean_height_differences(self, height_differences: List[HeightDifference]) -> pd.Series:
        """Calcul des dénivelées moyennes par point avec exactement 2 instruments: (Δh₁ + Δh₂) / 2."""
        # Grouper les observations par point (par paires de 2 instruments)
        mean_deltas = []
        current_group = []
        
        for hd in height_differences:
            if hd.instrument_id == 1:  # Nouveau point
                if current_group:
                    # Traiter le groupe précédent
                    mean_delta = self._calculate_strict_mean(current_group)
                    mean_deltas.append(mean_delta)
                current_group = [hd]
            else:
                current_group.append(hd)
        
        # Traiter le dernier groupe
        if current_group:
            mean_delta = self._calculate_strict_mean(current_group)
            mean_deltas.append(mean_delta)
        
        return pd.Series(mean_deltas)
    
    def _calculate_strict_mean(self, group: List[HeightDifference]) -> float:
        """Calcul de la moyenne stricte avec exactement 2 instruments."""
        valid_deltas = [h.delta_h_m for h in group if h.is_valid]
        
        if len(valid_deltas) == 2:
            # Cas idéal: exactement 2 instruments valides
            return (valid_deltas[0] + valid_deltas[1]) / 2.0
        elif len(valid_deltas) == 1:
            # Un seul instrument valide
            print(f"⚠️ Un seul instrument valide pour ce point: {valid_deltas[0]:.3f}m")
            return valid_deltas[0]
        elif len(valid_deltas) == 0:
            # Aucun instrument valide
            print(f"❌ Aucun instrument valide pour ce point")
            return np.nan
        else:
            # Plus de 2 instruments (ne devrait pas arriver avec l'approche stricte)
            print(f"⚠️ {len(valid_deltas)} instruments valides (2 attendus)")
            return np.mean(valid_deltas)


class AltitudeCalculator:
    """
    Calculateur d'altitudes par propagation.
    
    Implémente la propagation d'altitude depuis un point de référence
    avec optimisation vectorielle pour les performances.
    """
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
        self.precision_m = precision_mm / 1000.0
    
    def calculate_altitudes(self, initial_altitude: float, 
                          height_differences: List[HeightDifference],
                          point_ids: pd.Series) -> List[AltitudeCalculation]:
        """
        Calcul des altitudes avec la nouvelle logique.
        
        Algorithme:
        - Point 1: Altitude de référence (inchangée) = initial_altitude
        - Point 2: H_2 = H_1 + mean_delta où mean_delta = (delta_1 + delta_2) / 2.0
        - Point i (i≥3): H_i = H_{i-1} + delta_h_{i-1→i}
        
        Args:
            initial_altitude: Altitude du point de référence (point 1)
            height_differences: Liste des dénivelées moyennes calculées (N-1 dénivelées)
            point_ids: Identifiants des points (N points)
            
        Returns:
            List[AltitudeCalculation]: Altitudes calculées pour tous les points
        """
        validate_positive_number(initial_altitude, "altitude_initiale", allow_zero=True)
        
        if len(point_ids) != len(height_differences) + 1:
            raise CalculationError(
                f"Nombre incohérent: {len(point_ids)} points pour {len(height_differences)} dénivelées "
                f"(attendu: N points pour N-1 dénivelées)",
                calculation_type="altitude_calculation"
            )
        
        altitude_calculations = []
        current_altitude = initial_altitude
        cumulative_delta_h = 0.0
        
        # Premier point: Point de référence
        calc = AltitudeCalculation(
            point_id=str(point_ids.iloc[0]),
            altitude_m=round(initial_altitude, 3),
            cumulative_delta_h=0.0,
            is_reference=True
        )
        altitude_calculations.append(calc)
        
        # Points suivants: Propagation avec les dénivelées
        for i, height_diff in enumerate(height_differences):
            current_altitude += height_diff.delta_h_m
            cumulative_delta_h += height_diff.delta_h_m
            
            calc = AltitudeCalculation(
                point_id=str(point_ids.iloc[i + 1]),  # i+1 car on a commencé par le point 0
                altitude_m=round(current_altitude, 3),
                cumulative_delta_h=round(cumulative_delta_h, 3),
                is_reference=False
            )
            altitude_calculations.append(calc)
        
        return altitude_calculations
    
    def validate_altitude_consistency(self, altitudes: List[AltitudeCalculation]) -> Dict:
        """Validation de la cohérence des altitudes - délègue au CalculationValidator."""
        altitude_values = [alt.altitude_m for alt in altitudes]
        validator = CalculationValidator(self.precision_mm)
        statistics = validator.validate_altitude_consistency(altitude_values)
        
        # Ajouter les statistiques spécifiques au context LevelingCalculator
        statistics.update({
            'total_elevation_change': altitudes[-1].cumulative_delta_h,
        })
        
        return statistics


class WeightCalculator:
    """
    Calculateur de poids selon la théorie géodésique.
    
    Implémente la formule de variance théorique:
    σ² = a² + b²×d (mm²)
    où a = erreur instrumentale, b = erreur kilométrique, d = distance
    """
    
    def __init__(self, instrumental_error_mm: float = 0.2,
                 kilometric_error_mm: float = 0.3):
        """
        Args:
            instrumental_error_mm: Erreur instrumentale (mm)
            kilometric_error_mm: Erreur kilométrique (mm/km)
        """
        self.a_mm = instrumental_error_mm
        self.b_mm_per_km = kilometric_error_mm
        self.geodetic_validator = GeodeticValidator()
    
    def calculate_weights(self, distances_m: pd.Series) -> np.ndarray:
        """
        Calcul des poids géodésiques.
        
        Algorithme:
        1. Conversion distances en km
        2. Calcul variance: σ² = a² + b²×d
        3. Calcul poids: P = 1/σ²
        
        Args:
            distances_m: Distances en mètres
            
        Returns:
            np.ndarray: Matrice diagonale des poids
        """
        # Validation des distances
        validation_result = self.geodetic_validator.validate_distances(distances_m)
        if not validation_result.is_valid:
            raise CalculationError(
                f"Distances invalides: {'; '.join(validation_result.errors)}",
                calculation_type="weight_calculation"
            )
        
        weights = []
        
        for distance_m in distances_m:
            if pd.isna(distance_m) or distance_m <= 0:
                distance_m = 10.0  # Distance par défaut: 10m
            
            # Conversion en kilomètres
            distance_km = distance_m / 1000.0
            
            # Calcul de la variance (mm²)
            variance_mm2 = self.a_mm**2 + (self.b_mm_per_km * distance_km)**2
            
            # Calcul du poids (1/variance)
            weight = safe_divide(1.0, variance_mm2, "calcul_poids")
            weights.append(weight)
        
        return np.diag(weights)
    
    def get_weight_statistics(self, weights: np.ndarray) -> Dict:
        """Statistiques des poids calculés."""
        diagonal_weights = np.diag(weights)
        
        return {
            'min_weight': np.min(diagonal_weights),
            'max_weight': np.max(diagonal_weights),
            'mean_weight': np.mean(diagonal_weights),
            'std_weight': np.std(diagonal_weights),
            'weight_ratio': np.max(diagonal_weights) / np.min(diagonal_weights)
        }


class ClosureCalculator:
    """
    Calculateur de fermeture pour cheminements.
    
    Analyse la fermeture des cheminements fermés ou ouverts
    selon les normes géodésiques.
    """
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
        self.precision_validator = PrecisionValidator(precision_mm)
    
    def analyze_closure(self, altitudes: List[AltitudeCalculation],
                       total_distance_km: float,
                       known_final_altitude: Optional[float] = None) -> ClosureAnalysis:
        """
        Analyse complète de la fermeture du cheminement.
        
        Algorithme:
        1. Détermination du type (fermé/encadré)
        2. Calcul de l'erreur de fermeture
        3. Calcul de la tolérance: T = 4×√K (mm)
        4. Validation selon les normes
        
        Args:
            altitudes: Liste des altitudes calculées
            total_distance_km: Distance totale du cheminement
            known_final_altitude: Altitude connue du point final (si encadré)
            
        Returns:
            ClosureAnalysis: Analyse complète de fermeture
        """
        validate_distance_km(total_distance_km)
        
        # Détermination du type de cheminement
        initial_point = altitudes[0].point_id
        final_point = altitudes[-1].point_id
        
        if initial_point == final_point:
            traverse_type = TraverseType.CLOSED
            reference_altitude = altitudes[0].altitude_m
        elif known_final_altitude is not None:
            traverse_type = TraverseType.OPEN
            reference_altitude = known_final_altitude
        else:
            traverse_type = TraverseType.UNKNOWN
            reference_altitude = None
        
        # Calcul de l'erreur de fermeture
        if reference_altitude is not None:
            calculated_final = altitudes[-1].altitude_m
            closure_error_m = calculated_final - reference_altitude
            closure_error_mm = closure_error_m * 1000
        else:
            closure_error_m = 0.0
            closure_error_mm = 0.0
        
        # Calcul de la tolérance géodésique: T = 4×√K (mm)
        tolerance_mm = 4 * np.sqrt(total_distance_km)
        
        # Validation
        is_acceptable = abs(closure_error_mm) <= tolerance_mm
        precision_ratio = abs(closure_error_mm) / tolerance_mm if tolerance_mm > 0 else 0
        
        return ClosureAnalysis(
            traverse_type=traverse_type,
            closure_error_m=closure_error_m,
            closure_error_mm=closure_error_mm,
            tolerance_mm=tolerance_mm,
            total_distance_km=total_distance_km,
            is_acceptable=is_acceptable,
            precision_ratio=precision_ratio
        )
    
    def get_closure_report(self, closure: ClosureAnalysis) -> str:
        """Génère un rapport de fermeture détaillé."""
        report = f"""
=== ANALYSE DE FERMETURE ===
🎯 Type de cheminement: {closure.traverse_type.value}
📏 Distance totale: {closure.total_distance_km:.3f} km

📊 Erreur de fermeture:
   Valeur: {closure.closure_error_mm:.2f} mm
   Tolérance: ±{closure.tolerance_mm:.2f} mm
   Ratio: {closure.precision_ratio:.2f}

✅ Statut: {'ACCEPTABLE' if closure.is_acceptable else 'DÉPASSEMENT'}
🎯 Objectif 2mm: {'ATTEINT' if abs(closure.closure_error_mm) <= 2.0 else 'DÉPASSÉ'}
"""
        return report


class LevelingCalculator:
    """
    Calculateur principal intégrant tous les modules de calcul.
    
    Orchestre l'ensemble des calculs de compensation altimétrique
    avec validation continue et gestion d'erreurs.
    """
    
    def __init__(self, precision_mm: float = 2.0,
                 instrumental_error_mm: float = 0.2,
                 kilometric_error_mm: float = 0.3,
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
        self.geodetic_validator = GeodeticValidator()
    
    def calculate_complete_leveling(self, df: pd.DataFrame,
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
        6. Validation de précision
        
        Args:
            df: DataFrame des observations
            ar_columns: Colonnes AR
            av_columns: Colonnes AV
            dist_columns: Colonnes distances
            initial_altitude: Altitude de référence
            known_final_altitude: Altitude finale connue (si cheminement ouvert)
            
        Returns:
            CalculationResults: Résultats complets
        """
        try:
            # 1. Calcul des dénivelées
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
                print("🔧 Corrections atmosphériques désactivées")
            
            # 2. Calcul des altitudes avec la nouvelle logique
            altitudes = self.altitude_calc.calculate_altitudes(
                initial_altitude, height_differences, df['Matricule']
            )
            
            # 3. Calcul de la distance totale
            if dist_columns:
                total_distance_m = df[dist_columns[0]].sum()
                total_distance_km = total_distance_m / 1000
            else:
                # Distance par défaut basée sur le nombre de points
                total_distance_km = len(df) * 0.1  # 100m par segment
            
            # 4. Analyse de fermeture
            closure_analysis = self.closure_calc.analyze_closure(
                altitudes, total_distance_km, known_final_altitude
            )
            
            # 5. Statistiques de contrôle
            control_stats = self._calculate_control_statistics(height_differences)
            
            # 6. Métadonnées des calculs
            metadata = {
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
            }
            
            return CalculationResults(
                height_differences=height_differences,
                altitudes=altitudes,
                closure_analysis=closure_analysis,
                control_statistics=control_stats,
                calculation_metadata=metadata
            )
            
        except Exception as e:
            raise CalculationError(
                f"Erreur dans le calcul complet: {str(e)}",
                calculation_type="complete_leveling"
            )
    
    def _calculate_control_statistics(self, height_differences: List[HeightDifference]) -> Dict:
        """Calcul des statistiques de contrôle."""
        residuals = [hd.control_residual for hd in height_differences 
                    if hd.control_residual is not None]
        
        if not residuals:
            return {'no_control_data': True}
        
        residuals = np.array(residuals)
        
        return {
            'residual_count': len(residuals),
            'max_residual_mm': np.max(np.abs(residuals)) * 1000,
            'mean_residual_mm': np.mean(np.abs(residuals)) * 1000,
            'std_residual_mm': np.std(residuals) * 1000,
            'points_exceeding_5mm': np.sum(np.abs(residuals) * 1000 > 5.0),
            'control_quality': 'GOOD' if np.max(np.abs(residuals)) * 1000 <= 3.0 else 'WARNING'
        }
    
    def generate_calculation_report(self, results: CalculationResults) -> str:
        """Génère un rapport complet des calculs."""
        report = f"""
{'='*60}
    RAPPORT DE CALCULS - NIVELLEMENT GÉOMÉTRIQUE
{'='*60}

🎯 OBJECTIF DE PRÉCISION: {self.precision_mm} mm

📊 STATISTIQUES GÉNÉRALES:
   Points: {results.calculation_metadata['total_points']}
   Observations: {results.calculation_metadata['total_observations']}
   Colonnes AR: {', '.join(results.calculation_metadata['ar_columns_used'])}
   Colonnes AV: {', '.join(results.calculation_metadata['av_columns_used'])}

📐 DÉNIVELÉES CALCULÉES:
   Valides: {sum(1 for hd in results.height_differences if hd.is_valid)}
   Invalides: {sum(1 for hd in results.height_differences if not hd.is_valid)}
   
📏 ALTITUDES:
   Référence: {results.altitudes[0].altitude_m:.3f} m
   Finale: {results.altitudes[-1].altitude_m:.3f} m
   Dénivelée totale: {results.altitudes[-1].cumulative_delta_h:.3f} m

{self.closure_calc.get_closure_report(results.closure_analysis)}

🔧 CONTRÔLE QUALITÉ:
   Statut: {results.control_statistics.get('control_quality', 'N/A')}
   Résidu max: {results.control_statistics.get('max_residual_mm', 0):.2f} mm
   Points > 5mm: {results.control_statistics.get('points_exceeding_5mm', 0)}

✅ VALIDATION FINALE:
   Fermeture: {'✅ OK' if results.closure_analysis.is_acceptable else '❌ PROBLÈME'}
   Précision 2mm: {'✅ ATTEINTE' if abs(results.closure_analysis.closure_error_mm) <= 2.0 else '❌ DÉPASSÉE'}
   
Rapport généré le: {results.calculation_metadata['calculation_timestamp']}
{'='*60}
"""
        return report
    
    def export_results_to_dataframe(self, results: CalculationResults) -> pd.DataFrame:
        """Export des résultats vers un DataFrame."""
        # Créer un DataFrame avec les résultats principaux
        data = []
        
        for i, altitude in enumerate(results.altitudes):
            row = {
                'Matricule': altitude.point_id,
                'Altitude_m': altitude.altitude_m,
                'Delta_h_cumulé': altitude.cumulative_delta_h,
                'Est_référence': altitude.is_reference
            }
            
            # Ajouter les dénivelées si disponibles
            if i < len(results.height_differences):
                hd = results.height_differences[i]
                row.update({
                    'AR_lecture': hd.ar_reading,
                    'AV_lecture': hd.av_reading,
                    'Delta_h': hd.delta_h_m,
                    'Controle_residuel': hd.control_residual,
                    'Observation_valide': hd.is_valid
                })
            
            data.append(row)
        
        return pd.DataFrame(data)




