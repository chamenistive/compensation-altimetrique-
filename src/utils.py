"""
Module utilitaire pour le système de compensation altimétrique.

Ce module contient les fonctions utilitaires et raccourcis pour faciliter
l'utilisation des différents modules du système.

Fonctions quick_* pour un usage rapide avec paramètres par défaut.

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional

from data_importer import DataImporter, ImportedData
from calculator import LevelingCalculator, CalculationResults
from compensator import LevelingCompensator, CompensationResults
from visualizer import LevelingVisualizer
from .exceptions import CalculationError


def quick_import(filepath: Union[str, Path], **kwargs) -> ImportedData:
    """Import rapide avec paramètres par défaut."""
    importer = DataImporter()
    return importer.import_file(filepath, **kwargs)


def quick_leveling_calculation(df: pd.DataFrame, 
                             initial_altitude: float,
                             precision_mm: float = 2.0) -> CalculationResults:
    """Calcul rapide avec détection automatique des colonnes."""
    
    # Import et validation automatique
    importer = DataImporter()
    importer.validator = DataImporter().validator
    validation_result = importer.validator.validate_dataframe(df)
    
    if not validation_result.is_valid:
        raise CalculationError(
            f"Données invalides: {'; '.join(validation_result.errors)}",
            calculation_type="quick_calculation"
        )
    
    # Extraction des colonnes
    ar_columns = validation_result.details.get('ar_columns', [])
    av_columns = validation_result.details.get('av_columns', [])
    dist_columns = validation_result.details.get('dist_columns', [])
    
    # Calcul
    calculator = LevelingCalculator(precision_mm)
    return calculator.calculate_complete_leveling(
        df, ar_columns, av_columns, dist_columns, initial_altitude
    )


def quick_compensation(calculation_results: CalculationResults,
                      distances_m: np.ndarray,
                      precision_mm: float = 2.0) -> CompensationResults:
    """Compensation rapide avec paramètres par défaut."""
    compensator = LevelingCompensator(precision_mm)
    return compensator.compensate(calculation_results, distances_m)


def quick_visualization(calculation_results: CalculationResults,
                       compensation_results: Optional[CompensationResults] = None,
                       output_dir: Optional[Path] = None) -> Path:
    """Visualisation rapide avec paramètres par défaut."""
    # S'assurer que output_dir est un Path et existe
    if output_dir is None:
        output_dir = Path("./quick_visualizations")
    else:
        output_dir = Path(output_dir)
    
    # Créer le dossier s'il n'existe pas
    output_dir.mkdir(exist_ok=True, parents=True)
    
    visualizer = LevelingVisualizer(precision_mm=2.0, output_dir=output_dir)
    return visualizer.create_complete_report(calculation_results, compensation_results)


def complete_workflow(filepath: Union[str, Path],
                     initial_altitude: float,
                     precision_mm: float = 2.0,
                     output_dir: Optional[Path] = None) -> dict:
    """
    Workflow complet : import → calcul → compensation → visualisation.
    
    Args:
        filepath: Chemin vers le fichier de données
        initial_altitude: Altitude de référence
        precision_mm: Précision cible en mm
        output_dir: Dossier de sortie pour les visualisations
        
    Returns:
        Dict contenant tous les résultats intermédiaires
    """
    # Import
    imported_data = quick_import(filepath)
    
    # Calcul
    calculation_results = quick_leveling_calculation(
        imported_data.dataframe, 
        initial_altitude, 
        precision_mm
    )
    
    # Préparation des distances
    if imported_data.dist_columns:
        distances = imported_data.dataframe[imported_data.dist_columns[0]].values
    else:
        n_points = len(imported_data.dataframe)
        distances = np.full(n_points-1, 100.0)  # 100m par défaut
    
    # Compensation
    compensation_results = quick_compensation(
        calculation_results, 
        distances, 
        precision_mm
    )
    
    # Visualisation
    report_path = quick_visualization(
        calculation_results,
        compensation_results,
        output_dir
    )
    
    return {
        'imported_data': imported_data,
        'calculation_results': calculation_results,
        'compensation_results': compensation_results,
        'report_path': report_path,
        'precision_achieved': compensation_results.computation_metadata.get('max_correction_mm', 0) <= precision_mm
    }


def validate_file_format(filepath: Union[str, Path]) -> bool:
    """Validation rapide du format de fichier."""
    try:
        filepath = Path(filepath)
        return filepath.suffix.lower() in DataImporter.SUPPORTED_FORMATS
    except:
        return False


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