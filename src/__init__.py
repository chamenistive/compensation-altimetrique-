# -*- coding: utf-8 -*-
"""
Package de compensation altimetrique.
Module principal d'import pour l'application.
"""

# Exports principaux pour faciliter les imports
from .exceptions import (
    LevelingError, DataValidationError, FileImportError, 
    CalculationError, PrecisionError, MatrixError, 
    ClosureError, ConfigurationError
)

from .data_importer import DataImporter, ImportedData
from .calculator import LevelingCalculator, CalculationResults
from .compensator import LevelingCompensator, CompensationResults

# Version du package
__version__ = "1.0.0"
__precision_mm__ = 2.0

# Exports publics
__all__ = [
    'LevelingError', 'DataValidationError', 'FileImportError',
    'CalculationError', 'PrecisionError', 'MatrixError',
    'ClosureError', 'ConfigurationError',
    'DataImporter', 'ImportedData',
    'LevelingCalculator', 'CalculationResults', 
    'LevelingCompensator', 'CompensationResults'
]