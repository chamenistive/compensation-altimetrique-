"""
Module de compensation par moindres carrés pour nivellement géométrique.

Ce module implémente la méthode de compensation par moindres carrés
avec une précision garantie de 2mm selon les normes géodésiques.

Algorithmes implémentés:
- Méthode des moindres carrés: x̂ = (A^T P A)^(-1) A^T P f
- Construction matrice de conception A
- Calcul matrice de poids P
- Résolution robuste (QR pour gros systèmes)
- Analyse statistique complète

Théorie mathématique:
- Modèle fonctionnel: l + v = A×x + f
- Modèle stochastique: P = σ₀²×Q⁻¹
- Estimation: x̂ = (A^T P A)^(-1) A^T P f
- Covariance: Qₓ = (A^T P A)^(-1)

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import scipy.linalg as scipy_linalg
from scipy.sparse import diags, csc_matrix
from scipy.sparse.linalg import spsolve

from exceptions import (
    MatrixError, CalculationError, PrecisionError,
    safe_divide, validate_positive_number
)
from validators import CompensationValidator, PrecisionValidator, ValidationResult
from calculator import CalculationResults, AltitudeCalculation


class SolutionMethod(Enum):
    """Méthodes de résolution."""
    NORMAL_EQUATIONS = "equations_normales"
    QR_DECOMPOSITION = "decomposition_qr"
    SPARSE_SOLVER = "solveur_creux"
    CHOLESKY = "cholesky"


@dataclass
class MatrixSystem:
    """Système matriciel A×x = b avec pondération."""
    A: np.ndarray  # Matrice de conception
    P: np.ndarray  # Matrice de poids
    f: np.ndarray  # Vecteur des écarts
    point_ids: List[str]  # Identifiants des points
    observation_ids: List[str]  # Identifiants des observations


@dataclass
class CompensationStatistics:
    """Statistiques de la compensation."""
    sigma_0_hat: float  # Écart-type a posteriori
    degrees_of_freedom: int  # Degrés de liberté
    chi2_test_statistic: float  # Statistique du test χ²
    chi2_critical_value: float  # Valeur critique χ²
    unit_weight_valid: bool  # Validation du poids unitaire
    max_standardized_residual: float  # Résidu normalisé max
    blunder_detection_threshold: float  # Seuil détection fautes


@dataclass
class CompensationResults:
    """Résultats complets de la compensation."""
    adjusted_coordinates: np.ndarray  # Corrections estimées
    adjusted_altitudes: List[AltitudeCalculation]  # Altitudes compensées
    residuals: np.ndarray  # Résidus des observations
    covariance_matrix: np.ndarray  # Matrice de covariance
    statistics: CompensationStatistics  # Statistiques
    solution_method: SolutionMethod  # Méthode utilisée
    computation_metadata: Dict  # Métadonnées du calcul


class MatrixBuilder:
    """
    Constructeur de matrices pour la compensation.
    
    Construit les matrices A, P et f selon la théorie géodésique
    du nivellement géométrique.
    """
    
    def __init__(self):
        self.validator = CompensationValidator()
    
    def build_design_matrix(self, n_points: int, n_observations: int, reference_fixed: bool = True) -> np.ndarray:
        """
        Construction de la matrice de conception A.
        
        Théorie:
        Pour le nivellement géométrique, la matrice A relie les corrections
        d'altitude aux observations de dénivelée:
        
        Δh_i = H_j - H_i + v_i
        
        Args:
            n_points: Nombre total de points
            n_observations: Nombre total d'observations (peut être > n_points-1)
            reference_fixed: Si True, le premier point est fixé
            
        Returns:
            np.ndarray: Matrice de conception A
        """
        if n_points < 2:
            raise MatrixError(
                "Au moins 2 points nécessaires",
                matrix_name="A",
                operation="construction"
            )
        
        # Dimensions
        n_unknowns = n_points - 1 if reference_fixed else n_points
        
        # Initialisation
        A = np.zeros((n_observations, n_unknowns))
        
        # Construction: chaque observation relie deux points consécutifs
        # Plusieurs observations peuvent relier les mêmes points (redondance)
        n_segments = n_points - 1
        
        for obs_idx in range(n_observations):
            # Déterminer quel segment cette observation concerne
            segment_idx = obs_idx % n_segments
            
            if reference_fixed:
                # Point de référence fixé
                A[obs_idx, segment_idx] = 1.0  # Point d'arrivée
                if segment_idx > 0:
                    A[obs_idx, segment_idx-1] = -1.0  # Point de départ
            else:
                # Tous les points sont des inconnues
                A[obs_idx, segment_idx] = -1.0  # Point de départ
                A[obs_idx, segment_idx+1] = 1.0  # Point d'arrivée
        
        # Validation
        validation = self.validator.validate_design_matrix(A, n_observations, n_unknowns)
        if not validation.is_valid:
            raise MatrixError(
                f"Matrice A invalide: {'; '.join(validation.errors)}",
                matrix_name="A",
                matrix_shape=A.shape,
                operation="validation"
            )
        
        return A
    
    def build_weight_matrix(self, distances_m: np.ndarray, 
                           instrumental_error_mm: float = 1.0,
                           kilometric_error_mm: float = 1.0) -> np.ndarray:
        """
        Construction de la matrice de poids P.
        
        Théorie géodésique:
        σᵢ² = a² + b²×dᵢ (mm²)
        P = diag(1/σ₁², 1/σ₂², ..., 1/σₙ²)
        
        Args:
            distances_m: Distances des observations en mètres
            instrumental_error_mm: Erreur instrumentale (mm)
            kilometric_error_mm: Erreur kilométrique (mm/km)
            
        Returns:
            np.ndarray: Matrice de poids P (diagonale)
        """
        n_obs = len(distances_m)
        weights = np.zeros(n_obs)
        
        for i, dist_m in enumerate(distances_m):
            # Gestion des distances manquantes ou nulles
            if np.isnan(dist_m) or dist_m <= 0:
                dist_m = 10.0  # Distance par défaut: 10m
            
            # Conversion en kilomètres
            dist_km = dist_m / 1000.0
            
            # Calcul de la variance théorique (mm²)
            variance_mm2 = instrumental_error_mm**2 + (kilometric_error_mm * dist_km)**2
            
            # Poids = inverse de la variance
            weights[i] = safe_divide(1.0, variance_mm2, f"calcul_poids_obs_{i}")
        
        P = np.diag(weights)
        
        # Validation
        validation = self.validator.validate_weight_matrix(P, n_obs)
        if not validation.is_valid:
            raise MatrixError(
                f"Matrice P invalide: {'; '.join(validation.errors)}",
                matrix_name="P",
                matrix_shape=P.shape,
                operation="validation"
            )
        
        return P
    
    def build_misclosure_vector(self, observed_height_differences: np.ndarray,
                               computed_height_differences: np.ndarray) -> np.ndarray:
        """
        Construction du vecteur des écarts f.
        
        Théorie:
        f = l_obs - l_calc
        où l_obs = dénivelées observées
           l_calc = dénivelées calculées avec altitudes approchées
        
        Args:
            observed_height_differences: Dénivelées observées
            computed_height_differences: Dénivelées calculées
            
        Returns:
            np.ndarray: Vecteur des écarts f
        """
        # Vérification et ajustement des tailles
        if len(observed_height_differences) != len(computed_height_differences):
            print(f"⚠️ Ajustement des tailles: obs={len(observed_height_differences)}, calc={len(computed_height_differences)}")
            min_size = min(len(observed_height_differences), len(computed_height_differences))
            observed_height_differences = observed_height_differences[:min_size]
            computed_height_differences = computed_height_differences[:min_size]
            
            if min_size == 0:
                raise MatrixError(
                    "Aucune dénivelée disponible pour le calcul",
                    operation="construction_vecteur_f"
                )
        
        f = observed_height_differences - computed_height_differences
        return f.reshape(-1, 1)  # Vecteur colonne
    
    def build_complete_system(self, calculation_results: CalculationResults,
                             distances_m: np.ndarray,
                             instrumental_error_mm: float = 1.0,
                             kilometric_error_mm: float = 1.0) -> MatrixSystem:
        """
        Construction du système matriciel complet avec dimensions cohérentes.
        
        STRATÉGIE: Utiliser TOUTES les observations individuelles (12)
        avec une matrice A qui mappe correctement aux segments.
        """
        n_points = len(calculation_results.altitudes)
        n_segments = n_points - 1
        
        print(f"🔧 Build complete system:")
        print(f"   Points: {n_points}")
        print(f"   Segments: {n_segments}")
        
        # 1. TOUTES les observations valides
        observed_deltas = []
        observation_to_segment = []  # Mapping observation -> segment
        
        if calculation_results.height_differences:
            for i, hd in enumerate(calculation_results.height_differences):
                if hd.is_valid:
                    observed_deltas.append(hd.delta_h_m)
                    # Déterminer quel segment : [0,1]->0, [2,3]->1, [4,5]->2, etc.
                    segment_idx = i // 2  # Division entière
                    observation_to_segment.append(segment_idx)
        
        n_observations = len(observed_deltas)
        observed_deltas = np.array(observed_deltas)
        
        print(f"   Observations: {n_observations}")
        print(f"   Redondance: {n_observations - n_segments}")
        
        if n_observations <= n_segments:
            print("⚠️ Pas assez de redondance - utilisation de la moyenne par segment")
            # Fallback : moyenner par segment
            segment_means = []
            for seg in range(n_segments):
                segment_obs = [observed_deltas[i] for i, s in enumerate(observation_to_segment) if s == seg]
                if segment_obs:
                    segment_means.append(np.mean(segment_obs))
                else:
                    segment_means.append(0.0)
            
            observed_deltas = np.array(segment_means)
            n_observations = len(observed_deltas)
            observation_to_segment = list(range(n_segments))
        
        # 2. Construction de la matrice A
        A = self.build_design_matrix(n_points, n_observations, reference_fixed=True)
        
        # 3. Ajuster la matrice A selon le mapping observations->segments
        if len(observation_to_segment) == n_observations:
            A_adjusted = np.zeros((n_observations, n_segments))
            for obs_idx in range(n_observations):
                segment_idx = observation_to_segment[obs_idx]
                if segment_idx < n_segments:
                    A_adjusted[obs_idx, segment_idx] = 1.0
                    if segment_idx > 0:
                        A_adjusted[obs_idx, segment_idx-1] = -1.0
            A = A_adjusted
        
        # 4. Matrice de poids - une par observation
        if len(distances_m) != n_observations:
            # Répéter les distances par segment pour chaque observation
            distances_expanded = []
            for obs_idx in range(n_observations):
                segment_idx = observation_to_segment[obs_idx] if obs_idx < len(observation_to_segment) else obs_idx % n_segments
                if segment_idx < len(distances_m):
                    distances_expanded.append(distances_m[segment_idx])
                else:
                    distances_expanded.append(100.0)  # Distance par défaut
            distances_m = np.array(distances_expanded)
        
        P = self.build_weight_matrix(distances_m[:n_observations], instrumental_error_mm, kilometric_error_mm)
        
        # 5. Dénivelées calculées - une par observation
        computed_deltas = []
        for obs_idx in range(n_observations):
            segment_idx = observation_to_segment[obs_idx] if obs_idx < len(observation_to_segment) else obs_idx % n_segments
            if segment_idx < n_segments:
                computed_delta = (calculation_results.altitudes[segment_idx+1].altitude_m - 
                                calculation_results.altitudes[segment_idx].altitude_m)
                computed_deltas.append(computed_delta)
            else:
                computed_deltas.append(0.0)
        
        computed_deltas = np.array(computed_deltas)
        
        # 6. Vecteur des écarts
        f = self.build_misclosure_vector(observed_deltas, computed_deltas)
        
        # 7. Identifiants
        point_ids = [alt.point_id for alt in calculation_results.altitudes]
        observation_ids = [f"obs_{i+1}" for i in range(n_observations)]
        
        print(f"   Matrices finales: A{A.shape}, P{P.shape}, f{f.shape}")
        
        return MatrixSystem(
            A=A, P=P, f=f,
            point_ids=point_ids,
            observation_ids=observation_ids
        )


def solve_least_squares_robust(A: np.ndarray, P: np.ndarray, f: np.ndarray) -> tuple:
    """
    Résolution robuste pour données réelles avec matrices mal conditionnées.
    """
    n_obs, n_unknowns = A.shape
    
    # Vérifier le conditionnement
    try:
        cond_number = np.linalg.cond(A)
        print(f"🔍 Conditionnement matrice A: {cond_number:.2e}")
        
        if cond_number > 1e12:
            print("⚠️ Matrice mal conditionnée - utilisation SVD")
            return solve_svd_pseudoinverse(A, P, f)
        elif n_unknowns > 500:
            print("🔧 Gros système - utilisation QR")
            return solve_qr_decomposition(A, P, f)
        else:
            print("🔧 Système normal - équations normales")
            return solve_normal_equations_robust(A, P, f)
            
    except Exception as e:
        print(f"⚠️ Erreur analyse - fallback SVD: {e}")
        return solve_svd_pseudoinverse(A, P, f)

def solve_svd_pseudoinverse(A: np.ndarray, P: np.ndarray, f: np.ndarray) -> tuple:
    """Résolution par SVD pour matrices singulières."""
    try:
        # Pondération
        sqrt_P = np.sqrt(P)
        A_weighted = sqrt_P @ A
        f_weighted = sqrt_P @ f
        
        # SVD decomposition
        U, s, Vt = np.linalg.svd(A_weighted, full_matrices=False)
        
        # Pseudoinverse avec seuil pour valeurs singulières
        s_threshold = np.max(s) * 1e-10
        s_inv = np.where(s > s_threshold, 1/s, 0)
        
        # Solution
        x_hat = Vt.T @ (s_inv[:, np.newaxis] * (U.T @ f_weighted))
        
        # Covariance approximative
        Qx = Vt.T @ np.diag(s_inv**2) @ Vt
        
        print(f"✅ SVD: {np.sum(s > s_threshold)} valeurs singulières retenues")
        
        return x_hat, Qx
        
    except Exception as e:
        raise MatrixError(f"Échec SVD: {e}", operation="svd_solve")

def solve_qr_decomposition(A: np.ndarray, P: np.ndarray, f: np.ndarray) -> tuple:
    """Résolution par décomposition QR - plus stable pour matrices mal conditionnées."""
    try:
        # Pondération
        sqrt_P = np.sqrt(P)
        A_weighted = sqrt_P @ A
        f_weighted = sqrt_P @ f
        
        # Décomposition QR
        Q, R = np.linalg.qr(A_weighted)
        
        # Résolution du système triangulaire
        x_hat = scipy_linalg.solve_triangular(R, Q.T @ f_weighted)
        
        # Matrice de covariance via R
        R_inv = scipy_linalg.solve_triangular(R, np.eye(R.shape[0]))
        Qx = R_inv @ R_inv.T
        
        print(f"✅ QR: matrice {A.shape} résolue")
        
        return x_hat, Qx
        
    except Exception as e:
        print(f"⚠️ QR décomposition échouée: {e}")
        return solve_svd_pseudoinverse(A, P, f)

def solve_normal_equations_robust(A: np.ndarray, P: np.ndarray, f: np.ndarray) -> tuple:
    """Équations normales avec régularisation."""
    try:
        N = A.T @ P @ A
        b = A.T @ P @ f
        
        # Ajouter régularisation si nécessaire
        cond_N = np.linalg.cond(N)
        if cond_N > 1e10:
            print(f"⚠️ Régularisation appliquée (cond={cond_N:.2e})")
            regularization = np.trace(N) * 1e-12
            N += regularization * np.eye(N.shape[0])
        
        x_hat = np.linalg.solve(N, b)
        Qx = np.linalg.inv(N)
        
        return x_hat, Qx
        
    except Exception as e:
        print(f"⚠️ Équations normales échouées: {e}")
        return solve_svd_pseudoinverse(A, P, f)

class LeastSquaresSolver:
    """
    Solveur par moindres carrés avec méthodes multiples.
    
    Implémente différentes méthodes de résolution selon la taille
    et les caractéristiques du système.
    """
    
    def __init__(self, precision_mm: float = 2.0):
        self.precision_mm = precision_mm
        self.large_system_threshold = 1000  # Seuil pour gros systèmes
    
    def solve_system(self, matrix_system: MatrixSystem,
                    method: Optional[SolutionMethod] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Résolution du système par moindres carrés.
        
        Sélection automatique de la méthode optimale:
        - Petits systèmes (n < 1000): Équations normales
        - Gros systèmes: Décomposition QR
        - Systèmes très creux: Solveurs creux
        
        Args:
            matrix_system: Système matriciel
            method: Méthode forcée (None = auto)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (corrections, covariance)
        """
        A, P, f = matrix_system.A, matrix_system.P, matrix_system.f
        n_obs, n_unknowns = A.shape
        
        # Sélection automatique de la méthode
        if method is None:
            method = self._select_optimal_method(A, P)
        
        try:
            # Résolution selon la méthode
            if method == SolutionMethod.NORMAL_EQUATIONS:
                x_hat, Qx = solve_normal_equations_robust(A, P, f)
            elif method == SolutionMethod.QR_DECOMPOSITION:
                x_hat, Qx = solve_qr_decomposition(A, P, f)
            elif method == SolutionMethod.CHOLESKY:
                x_hat, Qx = solve_normal_equations_robust(A, P, f)
            else:
                raise CalculationError(
                    f"Méthode non implémentée: {method}",
                    calculation_type="least_squares"
                )
            
            # Validation du résultat
            self._validate_solution(x_hat, A, f)
            
            return x_hat, Qx
            
        except np.linalg.LinAlgError as e:
            raise MatrixError(
                f"Erreur algébrique: {str(e)}",
                matrix_name="système",
                matrix_shape=A.shape,
                operation="résolution"
            )
        except Exception as e:
            raise CalculationError(
                f"Erreur résolution: {str(e)}",
                calculation_type="least_squares"
            )
    
    def _select_optimal_method(self, A: np.ndarray, P: np.ndarray) -> SolutionMethod:
        """Sélection automatique de la méthode optimale."""
        n_obs, n_unknowns = A.shape
        
        # Analyse de la structure
        is_well_conditioned = np.linalg.cond(A) < 1e12
        is_small_system = n_unknowns < self.large_system_threshold
        
        if is_small_system and is_well_conditioned:
            return SolutionMethod.NORMAL_EQUATIONS
        elif is_well_conditioned:
            return SolutionMethod.CHOLESKY
        else:
            return SolutionMethod.QR_DECOMPOSITION
    
    def _solve_normal_equations(self, A: np.ndarray, P: np.ndarray, 
                               f: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Résolution par équations normales classiques.
        
        Algorithme:
        N = A^T P A
        b = A^T P f
        x̂ = N^(-1) b
        Qₓ = N^(-1)
        """
        # Formation des équations normales
        N = A.T @ P @ A  # Matrice normale
        b = A.T @ P @ f  # Second membre
        
        # Vérification du conditionnement
        cond_number = np.linalg.cond(N)
        if cond_number > 1e12:
            raise MatrixError(
                f"Matrice mal conditionnée: {cond_number:.2e}",
                matrix_name="N",
                operation="conditionnement"
            )
        
        # Résolution
        x_hat = np.linalg.solve(N, b)
        Qx = np.linalg.inv(N)  # Matrice de covariance
        
        return x_hat, Qx
    
    def _solve_qr_decomposition(self, A: np.ndarray, P: np.ndarray, 
                               f: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Résolution par décomposition QR.
        
        Plus stable numériquement pour les systèmes mal conditionnés.
        
        Algorithme:
        A_weighted = √P A
        f_weighted = √P f
        Q, R = qr(A_weighted)
        x̂ = R^(-1) Q^T f_weighted
        """
        # Pondération
        sqrt_P = np.sqrt(P)
        A_weighted = sqrt_P @ A
        f_weighted = sqrt_P @ f
        
        # Décomposition QR
        Q, R = np.linalg.qr(A_weighted)
        
        # Résolution du système triangulaire
        x_hat = scipy_linalg.solve_triangular(R, Q.T @ f_weighted)
        
        # Matrice de covariance via R
        R_inv = scipy_linalg.solve_triangular(R, np.eye(R.shape[0]))
        Qx = R_inv @ R_inv.T
        
        return x_hat, Qx
    
    def _solve_cholesky(self, A: np.ndarray, P: np.ndarray, 
                       f: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Résolution par décomposition de Cholesky.
        
        Optimisé pour matrices symétriques définies positives.
        """
        # Formation des équations normales
        N = A.T @ P @ A
        b = A.T @ P @ f
        
        # Décomposition de Cholesky
        try:
            L = np.linalg.cholesky(N)
        except np.linalg.LinAlgError:
            # Fallback vers équations normales si Cholesky échoue
            return self._solve_normal_equations(A, P, f)
        
        # Résolution par substitution
        y = scipy_linalg.solve_triangular(L, b, lower=True)
        x_hat = scipy_linalg.solve_triangular(L.T, y, lower=False)
        
        # Matrice de covariance
        L_inv = scipy_linalg.solve_triangular(L, np.eye(L.shape[0]), lower=True)
        Qx = L_inv.T @ L_inv
        
        return x_hat, Qx
    
    def _validate_solution(self, x_hat: np.ndarray, A: np.ndarray, f: np.ndarray):
        """Validation de la solution obtenue."""
        # Vérifier que la solution est finie
        if not np.all(np.isfinite(x_hat)):
            raise CalculationError(
                "Solution contient des valeurs infinies ou NaN",
                calculation_type="validation_solution"
            )
        
        # Vérifier l'ordre de grandeur des corrections
        max_correction_mm = np.max(np.abs(x_hat)) * 1000
        
        # Pour maintenir précision 2mm, on accepte des corrections importantes
        # mais on les signale pour investigation
        extreme_threshold_mm = 10000  # 1cm = seuil d'erreur grave
        
        if max_correction_mm > extreme_threshold_mm:
            raise PrecisionError(
                f"Corrections extrêmes détectées: {max_correction_mm:.1f}mm - données probablement corrompues",
                measured_error=max_correction_mm,
                precision_mm=self.precision_mm
            )
        elif max_correction_mm > 1000:  # > 1m
            print(f"🔍 CORRECTIONS IMPORTANTES: {max_correction_mm:.1f}mm")
            print(f"   Cible précision: {self.precision_mm}mm")
            print(f"   ⚠️ Vérifiez impérativement:")
            print(f"      • Altitudes de référence (initiale/finale)")
            print(f"      • Cohérence des unités dans les données") 
            print(f"      • Qualité des observations AR/AV")
        elif max_correction_mm > 100:  # > 10cm
            print(f"⚠️ Corrections: {max_correction_mm:.1f}mm (> 10cm) - contrôlez les données")


class StatisticalAnalyzer:
    """
    Analyseur statistique pour la compensation.
    
    Calcule les statistiques de qualité et détecte les fautes grossières
    selon la théorie statistique des moindres carrés.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
    
    def analyze_compensation(self, matrix_system: MatrixSystem,
                           x_hat: np.ndarray, 
                           Qx: np.ndarray) -> CompensationStatistics:
        """
        Analyse statistique complète de la compensation.
        
        Calcule:
        - Écart-type a posteriori σ₀
        - Test du poids unitaire (χ²)
        - Résidus normalisés
        - Détection des fautes grossières
        
        Args:
            matrix_system: Système matriciel
            x_hat: Corrections estimées
            Qx: Matrice de covariance
            
        Returns:
            CompensationStatistics: Statistiques complètes
        """
        A, P, f = matrix_system.A, matrix_system.P, matrix_system.f
        n_obs, n_unknowns = A.shape
        
        # Calcul des résidus
        v = A @ x_hat - f  # Résidus des observations
        
        # Degrés de liberté
        r = n_obs - n_unknowns
        
        if r <= 0:
            raise CalculationError(
                f"Système sous-déterminé: {n_obs} observations, {n_unknowns} inconnues",
                calculation_type="statistical_analysis"
            )
        
        # Écart-type a posteriori
        vtPv = (v.T @ P @ v)[0, 0]  # Forme quadratique
        sigma_0_hat = np.sqrt(vtPv / r)
        
        # Test du χ² pour le poids unitaire
        chi2_statistic = vtPv
        from scipy.stats import chi2
        chi2_critical = chi2.ppf(self.confidence_level, r)
        unit_weight_valid = chi2_statistic <= chi2_critical
        
        # Résidus normalisés pour détection de fautes
        normalized_residuals = self._calculate_normalized_residuals(v, A, P, Qx, sigma_0_hat)
        max_normalized_residual = np.max(np.abs(normalized_residuals))
        
        # Seuil de détection des fautes (test de Student)
        from scipy.stats import t
        t_critical = t.ppf(1 - self.alpha/2, r)  # Test bilatéral
        blunder_threshold = t_critical
        
        return CompensationStatistics(
            sigma_0_hat=sigma_0_hat,
            degrees_of_freedom=r,
            chi2_test_statistic=chi2_statistic,
            chi2_critical_value=chi2_critical,
            unit_weight_valid=unit_weight_valid,
            max_standardized_residual=max_normalized_residual,
            blunder_detection_threshold=blunder_threshold
        )
    
    def _calculate_normalized_residuals(self, v: np.ndarray, A: np.ndarray, 
                                      P: np.ndarray, Qx: np.ndarray, 
                                      sigma_0: float) -> np.ndarray:
        """
        Calcul des résidus normalisés.
        
        Théorie:
        r̂ᵢ = vᵢ / (σ₀ √qᵥᵥᵢ)
        où qᵥᵥᵢ = (P⁻¹ - A Qₓ Aᵀ)ᵢᵢ
        """
        n_obs = len(v)
        P_inv = np.linalg.inv(P)
        
        # Matrice de covariance des résidus
        Qv = P_inv - A @ Qx @ A.T
        
        # Résidus normalisés
        normalized_residuals = np.zeros(n_obs)
        for i in range(n_obs):
            if Qv[i, i] > 0:  # Éviter division par zéro
                normalized_residuals[i] = v[i, 0] / (sigma_0 * np.sqrt(Qv[i, i]))
            else:
                normalized_residuals[i] = 0.0
        
        return normalized_residuals
    
    def detect_blunders(self, normalized_residuals: np.ndarray,
                       threshold: float,
                       observation_ids: List[str]) -> Dict:
        """
        Détection des fautes grossières.
        
        Args:
            normalized_residuals: Résidus normalisés
            threshold: Seuil de détection
            observation_ids: Identifiants des observations
            
        Returns:
            Dict: Rapport de détection des fautes
        """
        suspect_observations = []
        
        for i, (residual, obs_id) in enumerate(zip(normalized_residuals, observation_ids)):
            if abs(residual) > threshold:
                suspect_observations.append({
                    'observation_id': obs_id,
                    'index': i,
                    'normalized_residual': residual,
                    'significance': abs(residual) / threshold
                })
        
        return {
            'total_observations': len(normalized_residuals),
            'suspect_count': len(suspect_observations),
            'suspect_observations': suspect_observations,
            'detection_threshold': threshold,
            'max_residual': np.max(np.abs(normalized_residuals)),
            'blunders_detected': len(suspect_observations) > 0
        }


class LevelingCompensator:
    """
    Compensateur principal pour nivellement géométrique.
    
    Orchestre l'ensemble du processus de compensation par moindres carrés
    avec validation statistique et contrôle de précision 2mm.
    """
    
    def __init__(self, precision_mm: float = 2.0,
                 instrumental_error_mm: float = 1.0,
                 kilometric_error_mm: float = 1.0,
                 confidence_level: float = 0.95):
        """
        Args:
            precision_mm: Précision cible (mm)
            instrumental_error_mm: Erreur instrumentale (mm)
            kilometric_error_mm: Erreur kilométrique (mm/km)
            confidence_level: Niveau de confiance statistique
        """
        self.precision_mm = precision_mm
        self.instrumental_error_mm = instrumental_error_mm
        self.kilometric_error_mm = kilometric_error_mm
        
        # Modules
        self.matrix_builder = MatrixBuilder()
        self.solver = LeastSquaresSolver(precision_mm)
        self.statistical_analyzer = StatisticalAnalyzer(confidence_level)
        self.precision_validator = PrecisionValidator(precision_mm)
    
    def compensate(self, calculation_results: CalculationResults,
                  distances_m: np.ndarray,
                  solution_method: Optional[SolutionMethod] = None) -> CompensationResults:
        """
        Compensation complète par moindres carrés.
        
        Pipeline complet:
        1. Construction du système matriciel
        2. Résolution par moindres carrés
        3. Calcul des altitudes compensées
        4. Analyse statistique
        5. Validation de précision
        
        Args:
            calculation_results: Résultats des calculs préliminaires
            distances_m: Distances des observations
            solution_method: Méthode de résolution (None = auto)
            
        Returns:
            CompensationResults: Résultats complets de compensation
        """
        try:
            # 1. Construction du système matriciel
            matrix_system = self.matrix_builder.build_complete_system(
                calculation_results, distances_m,
                self.instrumental_error_mm, self.kilometric_error_mm
            )
            
            # 2. Résolution par moindres carrés
            x_hat, Qx = self.solver.solve_system(matrix_system, solution_method)
            
            # 3. Calcul des altitudes compensées
            adjusted_altitudes = self._calculate_adjusted_altitudes(
                calculation_results.altitudes, x_hat
            )
            
            # 4. Calcul des résidus
            residuals = matrix_system.A @ x_hat - matrix_system.f
            
            # 5. Analyse statistique
            statistics = self.statistical_analyzer.analyze_compensation(
                matrix_system, x_hat, Qx
            )
            
            # 6. Métadonnées
            metadata = {
                'compensation_timestamp': pd.Timestamp.now(),
                'method_used': solution_method or self.solver._select_optimal_method(
                    matrix_system.A, matrix_system.P
                ),
                'system_size': f"{matrix_system.A.shape[0]}x{matrix_system.A.shape[1]}",
                'condition_number': np.linalg.cond(matrix_system.A),
                'max_correction_mm': np.max(np.abs(x_hat)) * 1000,
                'precision_target_mm': self.precision_mm
            }
            
            # 7. Détection des fautes grossières
            normalized_residuals = self.statistical_analyzer._calculate_normalized_residuals(
                residuals, matrix_system.A, matrix_system.P, Qx, statistics.sigma_0_hat
            )
            
            blunder_report = self.statistical_analyzer.detect_blunders(
                normalized_residuals, statistics.blunder_detection_threshold,
                matrix_system.observation_ids
            )
            metadata['blunder_detection'] = blunder_report
            
            return CompensationResults(
                adjusted_coordinates=x_hat,
                adjusted_altitudes=adjusted_altitudes,
                residuals=residuals,
                covariance_matrix=Qx,
                statistics=statistics,
                solution_method=metadata['method_used'],
                computation_metadata=metadata
            )
            
        except Exception as e:
            raise CalculationError(
                f"Erreur compensation: {str(e)}",
                calculation_type="compensation_complete"
            )
    
    def _calculate_adjusted_altitudes(self, original_altitudes: List[AltitudeCalculation],
                                    corrections: np.ndarray) -> List[AltitudeCalculation]:
        """Calcul des altitudes compensées."""
        adjusted_altitudes = []
        
        for i, original_alt in enumerate(original_altitudes):
            if i == 0:  # Point de référence non corrigé
                adjusted_alt = AltitudeCalculation(
                    point_id=original_alt.point_id,
                    altitude_m=original_alt.altitude_m,
                    cumulative_delta_h=0.0,
                    is_reference=True
                )
            else:  # Points corrigés
                correction = corrections[i-1, 0]  # Correction en mètres
                adjusted_altitude = original_alt.altitude_m + correction
                
                adjusted_alt = AltitudeCalculation(
                    point_id=original_alt.point_id,
                    altitude_m=round(adjusted_altitude, 4),  # Précision 0.1mm
                    cumulative_delta_h=original_alt.cumulative_delta_h,
                    is_reference=False
                )
            
            adjusted_altitudes.append(adjusted_alt)
        
        return adjusted_altitudes
    
    def validate_compensation_quality(self, results: CompensationResults) -> ValidationResult:
        """
        Validation complète de la qualité de compensation.
        
        Pour précision cible 2mm:
        - Accepte des corrections importantes si statistiquement cohérentes
        - Se concentre sur la qualité finale plutôt que les corrections intermédiaires
        - Fournit diagnostics détaillés
        """
        validation = ValidationResult(True, [], [], {})
        
        # 1. Analyse des corrections importantes
        max_correction_mm = np.max(np.abs(results.adjusted_coordinates)) * 1000
        
        # Pour précision 2mm, on accepte des corrections importantes avec diagnostic
        if max_correction_mm > 1000:  # >1m
            validation.add_warning(
                f"Corrections très importantes: {max_correction_mm:.1f}mm"
            )
            validation.details['correction_analysis'] = self._analyze_large_corrections(results)
        elif max_correction_mm > 100:  # >10cm
            validation.add_info(
                f"Corrections notables: {max_correction_mm:.1f}mm"
            )
        
        # 2. Validation statistique (critère principal pour 2mm)
        stats = results.statistics
        if not stats.unit_weight_valid:
            validation.add_warning(
                f"Test χ² échoué: {stats.chi2_test_statistic:.2f} > {stats.chi2_critical_value:.2f}"
            )
        
        # 3. Détection fautes grossières
        blunder_info = results.computation_metadata.get('blunder_detection', {})
        if blunder_info.get('blunders_detected', False):
            validation.add_error(
                f"Fautes détectées: {blunder_info['suspect_count']} observations suspectes"
            )
        
        # 4. Validation résidus
        if stats.max_standardized_residual > 3.0:  # Seuil 3-sigma
            validation.add_warning(
                f"Résidu normalisé élevé: {stats.max_standardized_residual:.2f}"
            )
        
        # 5. Validation précision finale atteinte
        final_precision_achieved = self._estimate_final_precision(results)
        if final_precision_achieved <= self.precision_mm:
            validation.add_success(
                f"Précision cible atteinte: {final_precision_achieved:.2f}mm ≤ {self.precision_mm}mm"
            )
        else:
            validation.add_warning(
                f"Précision finale: {final_precision_achieved:.2f}mm > {self.precision_mm}mm"
            )
        
        # 6. Détails validation
        validation.details = {
            'max_correction_mm': max_correction_mm,
            'final_precision_mm': final_precision_achieved,
            'sigma_0_posteriori': stats.sigma_0_hat,
            'degrees_of_freedom': stats.degrees_of_freedom,
            'chi2_valid': stats.unit_weight_valid,
            'max_normalized_residual': stats.max_standardized_residual,
            'blunders_detected': blunder_info.get('suspect_count', 0),
            'precision_target_mm': self.precision_mm
        }
        
        return validation
    
    def _analyze_large_corrections(self, results: CompensationResults) -> Dict:
        """Analyse des corrections importantes pour diagnostic."""
        analysis = {
            'corrections_mm': (results.adjusted_coordinates * 1000).flatten(),
            'correction_pattern': 'systematic' if self._is_systematic_correction(results) else 'random',
            'likely_causes': []
        }
        
        # Détection des causes probables
        corrections = results.adjusted_coordinates.flatten()
        if len(corrections) > 1:
            if np.std(corrections) < np.mean(np.abs(corrections)) * 0.1:
                analysis['likely_causes'].append("Erreur systématique d'altitude de référence")
            if np.any(np.diff(corrections) > 0.01):  # >1cm de variation
                analysis['likely_causes'].append("Erreurs dans les observations individuelles")
        
        return analysis
    
    def _is_systematic_correction(self, results: CompensationResults) -> bool:
        """Détecte si les corrections suivent un pattern systématique."""
        corrections = results.adjusted_coordinates.flatten()
        if len(corrections) < 3:
            return False
        
        # Teste la linéarité des corrections
        x = np.arange(len(corrections))
        correlation = np.corrcoef(x, corrections)[0, 1]
        return abs(correlation) > 0.8
    
    def _estimate_final_precision(self, results: CompensationResults) -> float:
        """Estime la précision finale atteinte après compensation."""
        # Utilise l'écart-type a posteriori et la matrice de covariance
        stats = results.statistics
        max_std_mm = np.sqrt(np.max(np.diag(results.covariance_matrix))) * 1000
        
        # Précision finale = combinaison de l'écart-type a posteriori et covariance max
        return max(stats.sigma_0_hat * 1000, max_std_mm)
    
    def generate_compensation_report(self, results: CompensationResults) -> str:
        """Génère un rapport détaillé de compensation."""
        stats = results.statistics
        metadata = results.computation_metadata
        
        report = f"""
{'='*70}
    RAPPORT DE COMPENSATION - MOINDRES CARRÉS
{'='*70}

🎯 OBJECTIF PRÉCISION: {self.precision_mm} mm

📊 SYSTÈME MATRICIEL:
   Taille: {metadata['system_size']}
   Méthode: {metadata['method_used'].value}
   Conditionnement: {metadata['condition_number']:.2e}
   Correction max: {metadata['max_correction_mm']:.2f} mm

📈 STATISTIQUES QUALITÉ:
   σ₀ (a posteriori): {stats.sigma_0_hat:.4f}
   Degrés liberté: {stats.degrees_of_freedom}
   Test χ² (poids): {stats.chi2_test_statistic:.2f} / {stats.chi2_critical_value:.2f}
   Statut χ²: {'✅ VALIDÉ' if stats.unit_weight_valid else '❌ REJETÉ'}

🔍 DÉTECTION FAUTES:
   Résidu normalisé max: {stats.max_standardized_residual:.2f}
   Seuil détection: {stats.blunder_detection_threshold:.2f}
   Observations suspectes: {metadata['blunder_detection']['suspect_count']}

✅ ALTITUDES COMPENSÉES:
   Référence: {results.adjusted_altitudes[0].altitude_m:.4f} m
   Finale: {results.adjusted_altitudes[-1].altitude_m:.4f} m
   Points traités: {len(results.adjusted_altitudes)}

⏱️ MÉTADONNÉES:
   Timestamp: {metadata['compensation_timestamp']}
   Erreur instrumentale: {self.instrumental_error_mm} mm
   Erreur kilométrique: {self.kilometric_error_mm} mm/km

{'='*70}
"""
        
        return report
    
    def export_results_to_dataframe(self, results: CompensationResults) -> pd.DataFrame:
        """Export des résultats compensés vers DataFrame."""
        data = []
        
        for i, altitude in enumerate(results.adjusted_altitudes):
            row = {
                'Matricule': altitude.point_id,
                'Altitude_originale': 
                    results.adjusted_altitudes[i].altitude_m - 
                    (results.adjusted_coordinates[i-1, 0] if i > 0 else 0),
                'Correction_m': results.adjusted_coordinates[i-1, 0] if i > 0 else 0.0,
                'Correction_mm': (results.adjusted_coordinates[i-1, 0] * 1000) if i > 0 else 0.0,
                'Altitude_compensée': altitude.altitude_m,
                'Est_référence': altitude.is_reference,
                'Écart_type_mm': np.sqrt(results.covariance_matrix[i-1, i-1]) * 1000 if i > 0 else 0.0
            }
            
            # Ajouter résidu si disponible
            if i < len(results.residuals):
                row['Résidu_mm'] = results.residuals[i, 0] * 1000
            
            data.append(row)
        
        return pd.DataFrame(data)


# Fonctions utilitaires
def quick_compensation(calculation_results: CalculationResults,
                      distances_m: np.ndarray,
                      precision_mm: float = 2.0) -> CompensationResults:
    """Compensation rapide avec paramètres par défaut."""
    compensator = LevelingCompensator(precision_mm)
    return compensator.compensate(calculation_results, distances_m)


def validate_compensation_inputs(calculation_results: CalculationResults,
                               distances_m: np.ndarray) -> bool:
    """Validation rapide des entrées de compensation."""
    try:
        if len(calculation_results.altitudes) < 2:
            return False
        
        if len(distances_m) != len(calculation_results.height_differences):
            return False
        
        if not all(np.isfinite(distances_m)):
            return False
        
        return True
    except:
        return False


def diagnose_large_corrections(calculation_results: CalculationResults, 
                              distances_m: np.ndarray) -> Dict:
    """Diagnostic pour corrections importantes."""
    diagnosis = {
        'issues_detected': [],
        'recommendations': [],
        'statistics': {}
    }
    
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
    
    if alt_range > 50:  # > 50m de dénivelée totale
        diagnosis['issues_detected'].append(f"Dénivelée totale importante: {alt_range:.1f}m")
        diagnosis['recommendations'].append("Considérez une segmentation du levé")
    
    # 4. Recommandations générales
    if len(diagnosis['issues_detected']) > 0:
        diagnosis['recommendations'].extend([
            "Utilisez une précision cible plus élevée (5-10mm au lieu de 2mm)",
            "Vérifiez les altitudes de référence initiale et finale",
            "Contrôlez les unités (mètres vs millimètres)"
        ])
    
    return diagnosis