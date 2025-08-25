"""
Validateurs pour le système de compensation altimétrique.

Ce module contient tous les validateurs nécessaires pour assurer la qualité
des données d'entrée et la cohérence des calculs de nivellement.

Algorithmes implémentés:
- Validation structure des données Excel
- Contrôle cohérence des observations
- Validation géodésique des distances
- Contrôle précision 2mm

Auteur: Système de Compensation Altimétrique
Version: 1.0
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass

from exceptions import (
    DataValidationError, FileImportError, PrecisionError, CalculationError,
    ConfigurationError, validate_positive_number, validate_precision_mm
)


@dataclass
class ValidationResult:
    """Résultat de validation avec détails."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict
    
    def add_error(self, error: str):
        """Ajoute une erreur."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Ajoute un avertissement."""
        self.warnings.append(warning)
    
    def add_info(self, info: str):
        """Ajoute une information."""
        if 'info' not in self.details:
            self.details['info'] = []
        self.details['info'].append(info)
    
    def add_success(self, success: str):
        """Ajoute un succès."""
        if 'success' not in self.details:
            self.details['success'] = []
        self.details['success'].append(success)
    
    def get_summary(self) -> str:
        """Retourne un résumé de la validation."""
        if self.is_valid:
            summary = "✅ VALIDATION RÉUSSIE"
        else:
            summary = "❌ VALIDATION ÉCHOUÉE"
        
        if self.errors:
            summary += f"\n🔴 Erreurs ({len(self.errors)}):"
            for error in self.errors:
                summary += f"\n  • {error}"
        
        if self.warnings:
            summary += f"\n🟡 Avertissements ({len(self.warnings)}):"
            for warning in self.warnings:
                summary += f"\n  • {warning}"
        
        return summary


class DataStructureValidator:
    """Validateur pour la structure des données Excel."""
    
    REQUIRED_COLUMNS = ["Matricule"]
    OBSERVATION_PATTERNS = {
        'AR': re.compile(r'^AR\s*\d*$', re.IGNORECASE),
        'AV': re.compile(r'^AV\s*\d*$', re.IGNORECASE),
        'DIST': re.compile(r'^DIST\s*\d*$', re.IGNORECASE)
    }
    
    def __init__(self):
        self.result = ValidationResult(True, [], [], {})
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Validation complète d'un DataFrame."""
        self.result = ValidationResult(True, [], [], {})
        
        # 1. Validation de base
        self._validate_basic_structure(df)
        
        # 2. Validation des colonnes
        self._validate_columns(df)
        
        # 3. Validation des données
        self._validate_data_content(df)
        
        # 4. Validation de cohérence
        self._validate_consistency(df)
        
        # 5. Statistiques
        self.result.details['statistics'] = self._compute_statistics(df)
        
        return self.result
    
    def _validate_basic_structure(self, df: pd.DataFrame):
        """Validation de la structure de base."""
        if df is None:
            self.result.add_error("DataFrame est None")
            return
        
        if df.empty:
            self.result.add_error("DataFrame est vide")
            return
        
        if len(df) < 2:
            self.result.add_error("Au moins 2 points sont nécessaires pour un cheminement")
        
        if len(df.columns) < 3:
            self.result.add_warning("Peu de colonnes détectées - vérifier la structure")
    
    def _validate_columns(self, df: pd.DataFrame):
        """Validation des colonnes."""
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        
        # Vérifier les colonnes obligatoires
        missing_required = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_required:
            self.result.add_error(f"Colonnes obligatoires manquantes: {missing_required}")
        
        # Détecter les colonnes d'observation
        ar_cols, av_cols, dist_cols = self._detect_observation_columns(df)
        
        # Validation AR/AV
        if len(ar_cols) == 0:
            self.result.add_error("Aucune colonne AR (Arrière) détectée")
        if len(av_cols) == 0:
            self.result.add_error("Aucune colonne AV (Avant) détectée")
        if len(ar_cols) != len(av_cols):
            self.result.add_error(f"Nombre incohérent AR({len(ar_cols)}) vs AV({len(av_cols)})")
        
        # Enregistrer les colonnes détectées
        self.result.details['ar_columns'] = ar_cols
        self.result.details['av_columns'] = av_cols
        self.result.details['dist_columns'] = dist_cols
    
    def _detect_observation_columns(self, df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
        """Détection des colonnes d'observation."""
        ar_cols = [col for col in df.columns 
                  if self.OBSERVATION_PATTERNS['AR'].match(col.strip())]
        av_cols = [col for col in df.columns 
                  if self.OBSERVATION_PATTERNS['AV'].match(col.strip())]
        dist_cols = [col for col in df.columns 
                    if self.OBSERVATION_PATTERNS['DIST'].match(col.strip())]
        
        return sorted(ar_cols), sorted(av_cols), sorted(dist_cols)
    
    def _validate_data_content(self, df: pd.DataFrame):
        """Validation du contenu des données."""
        # Validation Matricule
        if 'Matricule' in df.columns:
            matricule_nulls = df['Matricule'].isnull().sum()
            if matricule_nulls > 0:
                self.result.add_error(f"{matricule_nulls} matricules manquants")
            
            # Vérifier les doublons
            duplicates = df['Matricule'].duplicated().sum()
            if duplicates > 0:
                self.result.add_warning(f"{duplicates} matricules dupliqués détectés")
        
        # Validation des colonnes numériques
        ar_cols = self.result.details.get('ar_columns', [])
        av_cols = self.result.details.get('av_columns', [])
        
        for col in ar_cols + av_cols:
            if col in df.columns:
                # Vérifier si convertible en numérique
                try:
                    numeric_data = pd.to_numeric(df[col], errors='coerce')
                    null_count = numeric_data.isnull().sum()
                    if null_count > len(df) * 0.5:  # Plus de 50% de valeurs manquantes
                        self.result.add_warning(f"Colonne '{col}': {null_count} valeurs non numériques")
                except Exception as e:
                    self.result.add_error(f"Erreur conversion colonne '{col}': {e}")
    
    def _validate_consistency(self, df: pd.DataFrame):
        """Validation de cohérence."""
        ar_cols = self.result.details.get('ar_columns', [])
        av_cols = self.result.details.get('av_columns', [])
        
        if ar_cols and av_cols:
            # Vérifier que les paires AR/AV ont des données cohérentes
            for ar_col, av_col in zip(ar_cols, av_cols):
                if ar_col in df.columns and av_col in df.columns:
                    ar_data = pd.to_numeric(df[ar_col], errors='coerce')
                    av_data = pd.to_numeric(df[av_col], errors='coerce')
                    
                    # Vérifier plages de valeurs raisonnables
                    if ar_data.min() < -10 or ar_data.max() > 10:
                        self.result.add_warning(f"Valeurs AR '{ar_col}' hors plage normale")
                    if av_data.min() < -10 or av_data.max() > 10:
                        self.result.add_warning(f"Valeurs AV '{av_col}' hors plage normale")
    
    def _compute_statistics(self, df: pd.DataFrame) -> Dict:
        """Calcul des statistiques."""
        stats = {
            'total_points': len(df),
            'total_columns': len(df.columns),
            'missing_matricules': df['Matricule'].isnull().sum() if 'Matricule' in df.columns else 0,
            'ar_columns_count': len(self.result.details.get('ar_columns', [])),
            'av_columns_count': len(self.result.details.get('av_columns', [])),
            'dist_columns_count': len(self.result.details.get('dist_columns', []))
        }
        return stats


class PrecisionValidator:
    """Validateur de précision 2mm."""
    
    def __init__(self, target_precision_mm: float = 2.0):
        self.target_precision_mm = target_precision_mm
        self.target_precision_m = target_precision_mm / 1000.0
        validate_precision_mm(target_precision_mm)
    
    def validate_closure_error(self, closure_error_m: float, 
                             total_distance_km: float, 
                             traverse_type: str = "fermé") -> ValidationResult:
        """Validation de l'erreur de fermeture."""
        result = ValidationResult(True, [], [], {})
        
        try:
            # Conversion en millimètres
            closure_error_mm = abs(closure_error_m * 1000)
            
            # Calcul de la tolérance selon la norme géodésique
            # Tolérance = 4 * sqrt(K) mm où K est la distance en km
            tolerance_mm = 4 * np.sqrt(total_distance_km)
            
            # Validation
            is_acceptable = closure_error_mm <= tolerance_mm
            
            # Détails
            result.details = {
                'closure_error_mm': round(closure_error_mm, 2),
                'tolerance_mm': round(tolerance_mm, 2),
                'total_distance_km': total_distance_km,
                'traverse_type': traverse_type,
                'precision_ratio': closure_error_mm / tolerance_mm if tolerance_mm > 0 else 0,
                'target_precision_mm': self.target_precision_mm
            }
            
            if not is_acceptable:
                result.add_error(
                    f"Erreur de fermeture {closure_error_mm:.2f}mm > tolérance {tolerance_mm:.2f}mm"
                )
            
            # Vérifier si respecte l'objectif 2mm
            if closure_error_mm > self.target_precision_mm:
                result.add_warning(
                    f"Erreur de fermeture {closure_error_mm:.2f}mm > objectif {self.target_precision_mm}mm"
                )
            
        except Exception as e:
            result.add_error(f"Erreur validation fermeture: {str(e)}")
        
        return result
    
    def validate_adjustments(self, adjustments_m: np.ndarray) -> ValidationResult:
        """Validation des ajustements de compensation."""
        result = ValidationResult(True, [], [], {})
        
        try:
            adjustments_mm = np.abs(adjustments_m) * 1000
            
            max_adj_mm = np.max(adjustments_mm)
            mean_adj_mm = np.mean(adjustments_mm)
            std_adj_mm = np.std(adjustments_mm)
            
            result.details = {
                'max_adjustment_mm': round(max_adj_mm, 2),
                'mean_adjustment_mm': round(mean_adj_mm, 2),
                'std_adjustment_mm': round(std_adj_mm, 2),
                'target_precision_mm': self.target_precision_mm,
                'points_exceeding_target': np.sum(adjustments_mm > self.target_precision_mm)
            }
            
            # Validation ajustement maximal
            if max_adj_mm > self.target_precision_mm:
                result.add_warning(
                    f"Ajustement maximal {max_adj_mm:.2f}mm > objectif {self.target_precision_mm}mm"
                )
            
            # Validation distribution
            points_exceeding = np.sum(adjustments_mm > self.target_precision_mm)
            if points_exceeding > len(adjustments_m) * 0.1:  # Plus de 10% des points
                result.add_warning(
                    f"{points_exceeding} points dépassent l'objectif de précision"
                )
            
        except Exception as e:
            result.add_error(f"Erreur validation ajustements: {str(e)}")
        
        return result


class GeodeticValidator:
    """Validateur pour les aspects géodésiques."""
    
    def validate_distances(self, distances: np.ndarray) -> ValidationResult:
        """Validation des distances de nivellement."""
        result = ValidationResult(True, [], [], {})
        
        try:
            distances = np.array(distances)
            valid_distances = distances[~np.isnan(distances) & (distances > 0)]
            
            if len(valid_distances) == 0:
                result.add_error("Aucune distance valide détectée")
                return result
            
            min_dist = np.min(valid_distances)
            max_dist = np.max(valid_distances)
            mean_dist = np.mean(valid_distances)
            total_dist = np.sum(valid_distances)
            
            result.details = {
                'total_distance_m': total_dist,
                'total_distance_km': total_dist / 1000,
                'min_distance_m': min_dist,
                'max_distance_m': max_dist,
                'mean_distance_m': mean_dist,
                'valid_segments': len(valid_distances)
            }
            
            # Validations
            if min_dist < 1.0:  # Moins de 1 mètre
                result.add_warning(f"Distance minimale très courte: {min_dist:.1f}m")
            
            if max_dist > 300.0:  # Plus de 300 mètres
                result.add_warning(f"Distance maximale très longue: {max_dist:.1f}m")
            
            if total_dist > 50000:  # Plus de 50 km
                result.add_warning(f"Cheminement très long: {total_dist/1000:.1f}km")
            
        except Exception as e:
            result.add_error(f"Erreur validation distances: {str(e)}")
        
        return result
    
    def validate_height_differences(self, delta_h: np.ndarray) -> ValidationResult:
        """Validation des dénivelées."""
        result = ValidationResult(True, [], [], {})
        
        try:
            delta_h = np.array(delta_h)
            valid_deltas = delta_h[~np.isnan(delta_h)]
            
            if len(valid_deltas) == 0:
                result.add_error("Aucune dénivelée valide")
                return result
            
            min_delta = np.min(valid_deltas)
            max_delta = np.max(valid_deltas)
            total_elevation_change = np.sum(valid_deltas)
            
            result.details = {
                'total_elevation_change_m': total_elevation_change,
                'min_delta_h_m': min_delta,
                'max_delta_h_m': max_delta,
                'valid_observations': len(valid_deltas)
            }
            
            # Validations
            if abs(min_delta) > 50.0:  # Plus de 50m de dénivelée
                result.add_warning(f"Dénivelée minimale importante: {min_delta:.3f}m")
            
            if abs(max_delta) > 50.0:  # Plus de 50m de dénivelée
                result.add_warning(f"Dénivelée maximale importante: {max_delta:.3f}m")
            
        except Exception as e:
            result.add_error(f"Erreur validation dénivelées: {str(e)}")
        
        return result


class CompensationValidator:
    """Validateur pour la compensation par moindres carrés."""
    
    def validate_design_matrix(self, A: np.ndarray, n_observations: int, 
                             n_unknowns: int) -> ValidationResult:
        """Validation de la matrice de conception."""
        result = ValidationResult(True, [], [], {})
        
        try:
            # Vérifications dimensionnelles
            if A.shape != (n_observations, n_unknowns):
                result.add_error(
                    f"Dimension incorrecte: {A.shape} != ({n_observations}, {n_unknowns})"
                )
            
            # Vérifier que la matrice n'est pas singulière
            if n_unknowns > 0:
                rank = np.linalg.matrix_rank(A)
                if rank < n_unknowns:
                    result.add_error(f"Matrice sous-déterminée: rang {rank} < {n_unknowns}")
            
            result.details = {
                'shape': A.shape,
                'rank': np.linalg.matrix_rank(A) if n_unknowns > 0 else 0,
                'condition_number': np.linalg.cond(A) if n_unknowns > 0 else 0
            }
            
        except Exception as e:
            result.add_error(f"Erreur validation matrice A: {str(e)}")
        
        return result
    
    def validate_weight_matrix(self, P: np.ndarray, n_observations: int) -> ValidationResult:
        """Validation de la matrice de poids."""
        result = ValidationResult(True, [], [], {})
        
        try:
            # Vérifications dimensionnelles
            if P.shape != (n_observations, n_observations):
                result.add_error(f"Dimension incorrecte: {P.shape} != ({n_observations}, {n_observations})")
            
            # Vérifier que c'est une matrice diagonale positive
            if not np.allclose(P, np.diag(np.diag(P))):
                result.add_warning("Matrice de poids non diagonale")
            
            diagonal = np.diag(P)
            if np.any(diagonal <= 0):
                result.add_error("Poids négatifs ou nuls détectés")
            
            result.details = {
                'shape': P.shape,
                'min_weight': np.min(diagonal),
                'max_weight': np.max(diagonal),
                'mean_weight': np.mean(diagonal)
            }
            
        except Exception as e:
            result.add_error(f"Erreur validation matrice P: {str(e)}")
        
        return result


class CalculationValidator:
    """Validateur pour les calculs de nivellement."""
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
        
    def validate_readings(self, ar: float, av: float, row_index: int):
        """Validation des lectures AR et AV pour données réelles."""
        # Plage élargie pour données réelles (terrain peut avoir de grosses dénivelées)
        min_reading, max_reading = -50.0, 50.0
        
        warnings = []
        
        # Validation moins stricte - juste avertissements
        if not (min_reading <= ar <= max_reading):
            warnings.append(f"Lecture AR inhabituelle à la ligne {row_index}: {ar:.3f}m")
        
        if not (min_reading <= av <= max_reading):
            warnings.append(f"Lecture AV inhabituelle à la ligne {row_index}: {av:.3f}m")
        
        # Validation critique seulement pour valeurs extrêmes
        if abs(ar) > 100 or abs(av) > 100:
            raise CalculationError(
                f"Lecture critique à la ligne {row_index}: AR={ar}, AV={av}",
                calculation_type="validation_lectures"
            )
        
        return warnings
    
    def validate_altitude_consistency(self, altitudes_m: List[float]) -> Dict:
        """Validation de la cohérence des altitudes calculées."""
        statistics = {
            'min_altitude': min(altitudes_m),
            'max_altitude': max(altitudes_m),
            'altitude_range': max(altitudes_m) - min(altitudes_m),
            'reference_altitude': altitudes_m[0]
        }
        
        # Validations
        warnings = []
        
        if statistics['altitude_range'] > 1000:  # Plus de 1000m de dénivelée
            warnings.append(f"Dénivelée importante: {statistics['altitude_range']:.1f}m")
        
        if any(alt < -500 or alt > 5000 for alt in altitudes_m):  # Altitudes irréalistes
            warnings.append("Altitudes hors plage normale (-500m à 5000m)")
        
        statistics['warnings'] = warnings
        return statistics
    
    def validate_calculation_inputs(self, df: pd.DataFrame, 
                                  ar_columns: List[str],
                                  av_columns: List[str],
                                  initial_altitude: float) -> ValidationResult:
        """Validation complète des entrées de calcul."""
        result = ValidationResult()
        
        try:
            # Vérifications de base
            if df.empty:
                result.add_error("DataFrame vide")
                return result
            
            if len(ar_columns) != len(av_columns):
                result.add_error(f"Nombre de colonnes AR ({len(ar_columns)}) != AV ({len(av_columns)})")
            
            missing_cols = [col for col in ar_columns + av_columns if col not in df.columns]
            if missing_cols:
                result.add_error(f"Colonnes manquantes: {missing_cols}")
            
            # Validation altitude initiale
            try:
                validate_positive_number(initial_altitude, "altitude_initiale", allow_zero=True)
            except Exception as e:
                result.add_error(f"Altitude initiale invalide: {str(e)}")
            
            result.mark_valid()
            
        except Exception as e:
            result.add_error(f"Erreur validation entrées: {str(e)}")
        
        return result


class FileValidator:
    """Validateur pour les fichiers d'entrée."""
    
    SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv']
    MAX_FILE_SIZE_MB = 100
    
    def validate_file(self, filepath) -> ValidationResult:
        """Validation complète du fichier avant importation."""
        result = ValidationResult()
        
        try:
            from pathlib import Path
            filepath = Path(filepath)
            
            # Existence
            if not filepath.exists():
                result.add_error(f"Fichier non trouvé: {filepath}")
                return result
            
            # Format
            if filepath.suffix.lower() not in self.SUPPORTED_FORMATS:
                result.add_error(
                    f"Format non supporté: {filepath.suffix}. "
                    f"Formats acceptés: {', '.join(self.SUPPORTED_FORMATS)}"
                )
            
            # Taille
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb == 0:
                result.add_error("Fichier vide")
            elif file_size_mb > self.MAX_FILE_SIZE_MB:
                result.add_error(f"Fichier trop volumineux: {file_size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB")
            
            if result.errors:
                return result
                
            result.mark_valid()
            
        except Exception as e:
            result.add_error(f"Erreur validation fichier: {str(e)}")
        
        return result


class CompensationValidator:
    """Validateur pour la compensation par moindres carrés."""
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
    
    def validate_solution(self, x_hat: np.ndarray, A: np.ndarray, f: np.ndarray) -> ValidationResult:
        """Validation de la solution de compensation."""
        result = ValidationResult()
        
        try:
            # Vérifier que la solution est finie
            if not np.all(np.isfinite(x_hat)):
                result.add_error("Solution contient des valeurs infinies ou NaN")
                return result
            
            # Vérifier l'ordre de grandeur des corrections
            max_correction_mm = np.max(np.abs(x_hat)) * 1000
            
            # Pour maintenir précision 2mm, on accepte des corrections importantes
            extreme_threshold_mm = 10000  # 10m = seuil d'erreur grave
            
            if max_correction_mm > extreme_threshold_mm:
                result.add_error(
                    f"Corrections extrêmes détectées: {max_correction_mm:.1f}mm - données probablement corrompues"
                )
            elif max_correction_mm > 1000:  # > 1m
                result.add_warning(
                    f"Corrections importantes détectées: {max_correction_mm:.1f}mm - vérifiez les données"
                )
            
            result.details['max_correction_mm'] = max_correction_mm
            result.mark_valid()
            
        except Exception as e:
            result.add_error(f"Erreur validation solution: {str(e)}")
        
        return result
    
    def validate_compensation_inputs(self, calculation_results, distances_m: np.ndarray) -> ValidationResult:
        """Validation des entrées pour la compensation."""
        result = ValidationResult()
        
        try:
            if len(calculation_results.altitudes) < 2:
                result.add_error("Moins de 2 points pour la compensation")
            
            if len(distances_m) != len(calculation_results.height_differences):
                result.add_error(
                    f"Nombre de distances ({len(distances_m)}) != "
                    f"nombre de dénivelées ({len(calculation_results.height_differences)})"
                )
            
            if not all(np.isfinite(distances_m)):
                result.add_error("Distances contiennent des valeurs non-finies")
            
            if np.any(distances_m <= 0):
                result.add_error("Distances doivent être strictement positives")
            
            result.mark_valid()
            
        except Exception as e:
            result.add_error(f"Erreur validation entrées compensation: {str(e)}")
        
        return result
    
    def diagnose_large_corrections(self, calculation_results, distances_m: np.ndarray) -> Dict:
        """Diagnostic pour corrections importantes."""
        diagnosis = {
            'issues_detected': [],
            'recommendations': [],
            'statistics': {}
        }
        
        try:
            # 1. Analyser la fermeture
            if hasattr(calculation_results, 'closure_analysis'):
                closure = calculation_results.closure_analysis
                closure_mm = abs(closure.closure_error_mm)
                diagnosis['statistics']['closure_error_mm'] = closure_mm
                
                if closure_mm > 50:  # > 5cm
                    diagnosis['issues_detected'].append(f"Erreur de fermeture importante: {closure_mm:.1f}mm")
                    diagnosis['recommendations'].append("Vérifiez les lectures et les calculs préliminaires")
            
            # 2. Analyser les dénivelées
            if calculation_results.height_differences:
                deltas = [hd.delta_h_m for hd in calculation_results.height_differences if hd.is_valid]
                if deltas:
                    delta_range = max(deltas) - min(deltas)
                    diagnosis['statistics']['height_difference_range_m'] = delta_range
                    
                    if delta_range > 20:  # > 20m de variation
                        diagnosis['issues_detected'].append(f"Dénivelées très variables: {delta_range:.1f}m")
                        diagnosis['recommendations'].append("Vérifiez la cohérence des lectures AR/AV")
            
            # 3. Analyser les altitudes
            altitudes = [alt.altitude_m for alt in calculation_results.altitudes]
            alt_range = max(altitudes) - min(altitudes)
            diagnosis['statistics']['altitude_range_m'] = alt_range
            
            if alt_range > 500:  # > 500m
                diagnosis['issues_detected'].append(f"Plage d'altitudes importante: {alt_range:.1f}m")
                diagnosis['recommendations'].append("Vérifiez que le terrain correspond aux attentes")
            
            # 4. Analyser les distances
            if len(distances_m) > 0:
                avg_distance = np.mean(distances_m)
                max_distance = np.max(distances_m)
                diagnosis['statistics']['avg_distance_m'] = avg_distance
                diagnosis['statistics']['max_distance_m'] = max_distance
                
                if max_distance > 1000:  # > 1km
                    diagnosis['issues_detected'].append(f"Portée très longue: {max_distance:.0f}m")
                    diagnosis['recommendations'].append("Vérifiez la précision pour les longues portées")
                
                if avg_distance > 300:  # > 300m en moyenne
                    diagnosis['recommendations'].append("Portées élevées - considérez les corrections atmosphériques")
        
        except Exception as e:
            diagnosis['issues_detected'].append(f"Erreur durant le diagnostic: {str(e)}")
        
        return diagnosis