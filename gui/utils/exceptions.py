"""
Exceptions minimalistes pour l'interface graphique.
Fallback si les modules backend ne sont pas disponibles.
"""

class AppError(Exception):
    """Erreur de base de l'application."""
    pass

class ImportError(AppError):
    """Erreur d'import de fichier."""
    pass

class ValidationError(AppError):
    """Erreur de validation des données."""
    pass