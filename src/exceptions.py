"""
Exceptions personnalisées pour le système de compensation altimétrique.

Ce module définit toutes les exceptions spécifiques au domaine de la compensation
altimétrique, permettant une gestion d'erreurs précise et informative.

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm
"""
# Import nécessaire
import numpy as np

class LevelingError(Exception):
    """Exception de base pour toutes les erreurs de nivellement."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        base_msg = f"[{self.error_code}] {self.message}" if self.error_code else self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_msg} | Détails: {details_str}"
        return base_msg


class DataValidationError(LevelingError):
    """Erreur de validation des données d'entrée."""
    
    def __init__(self, message: str, invalid_data: dict = None, expected_format: str = None):
        details = {}
        if invalid_data:
            details['données_invalides'] = invalid_data
        if expected_format:
            details['format_attendu'] = expected_format
        
        super().__init__(
            message=message,
            error_code="DATA_VALIDATION",
            details=details
        )


class FileImportError(LevelingError):
    """Erreur lors de l'importation de fichier."""
    
    def __init__(self, message: str, filename: str = None, file_type: str = None):
        details = {}
        if filename:
            details['fichier'] = filename
        if file_type:
            details['type'] = file_type
        
        super().__init__(
            message=message,
            error_code="FILE_IMPORT",
            details=details
        )


class CalculationError(LevelingError):
    """Erreur lors des calculs de compensation."""
    
    def __init__(self, message: str, calculation_type: str = None, 
                 input_values: dict = None, expected_range: tuple = None):
        details = {}
        if calculation_type:
            details['type_calcul'] = calculation_type
        if input_values:
            details['valeurs_entrée'] = input_values
        if expected_range:
            details['plage_attendue'] = f"{expected_range[0]} à {expected_range[1]}"
        
        super().__init__(
            message=message,
            error_code="CALCULATION",
            details=details
        )


class PrecisionError(LevelingError):
    """Erreur de précision - dépassement des tolérances."""
    
    def __init__(self, message: str, measured_error: float = None, 
                 tolerance: float = None, precision_mm: float = 2.0):
        details = {
            'précision_cible': f"{precision_mm}mm"
        }
        if measured_error is not None:
            details['erreur_mesurée'] = f"{measured_error:.3f}mm"
        if tolerance is not None:
            details['tolérance'] = f"{tolerance:.3f}mm"
        
        super().__init__(
            message=message,
            error_code="PRECISION",
            details=details
        )


class MatrixError(LevelingError):
    """Erreur lors des opérations matricielles."""
    
    def __init__(self, message: str, matrix_name: str = None, 
                 matrix_shape: tuple = None, operation: str = None):
        details = {}
        if matrix_name:
            details['matrice'] = matrix_name
        if matrix_shape:
            details['dimension'] = f"{matrix_shape[0]}x{matrix_shape[1]}"
        if operation:
            details['opération'] = operation
        
        super().__init__(
            message=message,
            error_code="MATRIX",
            details=details
        )


class ClosureError(LevelingError):
    """Erreur de fermeture du cheminement."""
    
    def __init__(self, message: str, closure_error_mm: float = None, 
                 tolerance_mm: float = None, traverse_type: str = None):
        details = {}
        if closure_error_mm is not None:
            details['erreur_fermeture'] = f"{closure_error_mm:.2f}mm"
        if tolerance_mm is not None:
            details['tolérance_admise'] = f"{tolerance_mm:.2f}mm"
        if traverse_type:
            details['type_cheminement'] = traverse_type
        
        super().__init__(
            message=message,
            error_code="CLOSURE",
            details=details
        )


class ConfigurationError(LevelingError):
    """Erreur de configuration ou paramètres invalides."""
    
    def __init__(self, message: str, parameter: str = None, 
                 value: any = None, valid_range: tuple = None):
        details = {}
        if parameter:
            details['paramètre'] = parameter
        if value is not None:
            details['valeur'] = str(value)
        if valid_range:
            details['plage_valide'] = f"{valid_range[0]} à {valid_range[1]}"
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION",
            details=details
        )


# Fonctions utilitaires pour la gestion d'erreurs
def validate_positive_number(value: float, name: str, allow_zero: bool = False):
    """Valide qu'un nombre est positif."""
    if value is None:
        raise DataValidationError(f"La valeur '{name}' ne peut pas être None")
    
    if not isinstance(value, (int, float)):
        raise DataValidationError(
            f"'{name}' doit être un nombre", 
            invalid_data={'valeur': value, 'type': type(value).__name__}
        )
    
    if not allow_zero and value <= 0:
        raise DataValidationError(
            f"'{name}' doit être positif", 
            invalid_data={'valeur': value}
        )
    elif allow_zero and value < 0:
        raise DataValidationError(
            f"'{name}' doit être positif ou nul", 
            invalid_data={'valeur': value}
        )
    
    return True


def validate_precision_mm(precision_mm: float):
    """Valide la précision en millimètres."""
    validate_positive_number(precision_mm, "précision")
    
    if precision_mm < 0.1 or precision_mm > 50:
        raise ConfigurationError(
            "Précision hors limites réalistes",
            parameter="précision_mm",
            value=precision_mm,
            valid_range=(0.1, 50)
        )
    
    return True


def validate_distance_km(distance: float):
    """Valide une distance en kilomètres."""
    validate_positive_number(distance, "distance")
    
    if distance > 1000:  # Limite raisonnable : 1000 km
        raise DataValidationError(
            "Distance de cheminement irréaliste",
            invalid_data={'distance_km': distance}
        )
    
    return True


def safe_divide(numerator: float, denominator: float, operation_name: str = "division"):
    """Division sécurisée avec gestion d'erreurs."""
    if denominator == 0:
        raise CalculationError(
            f"Division par zéro dans {operation_name}",
            calculation_type=operation_name,
            input_values={'numérateur': numerator, 'dénominateur': denominator}
        )
    
    try:
        result = numerator / denominator
        # Vérifier si le résultat est fini
        if not np.isfinite(result):
            raise CalculationError(
                f"Résultat invalide dans {operation_name}",
                calculation_type=operation_name,
                input_values={'résultat': result}
            )
        return result
    except Exception as e:
        raise CalculationError(
            f"Erreur de calcul dans {operation_name}: {str(e)}",
            calculation_type=operation_name
        )


# Import nécessaire
import numpy as np