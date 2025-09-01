"""
Module d'importation des données pour la compensation altimétrique.

Ce module gère l'importation, la validation et la préparation des données
de nivellement depuis différents formats (Excel, CSV, etc.).

Algorithmes implémentés:
- Importation robuste Excel/CSV
- Détection automatique des colonnes AR/AV/DIST
- Validation structure et cohérence des données
- Préparation pour compensation (nettoyage, indexation)

Auteur: Système de Compensation Altimétrique
Version: 1.0
Précision: 2mm
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass

from .exceptions import FileImportError, DataValidationError
from .validators import DataStructureValidator, ValidationResult, FileValidator


@dataclass
class ImportedData:
    """Structure pour les données importées."""
    dataframe: pd.DataFrame
    ar_columns: List[str]
    av_columns: List[str]
    dist_columns: List[str]
    initial_point: str
    final_point: str
    metadata: Dict
    validation_result: ValidationResult


class DataImporter:
    """
    Importeur de données pour la compensation altimétrique.
    
    Gère l'importation depuis Excel/CSV avec validation automatique
    et préparation des données pour les calculs de compensation.
    """
    
    SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv']
    DEFAULT_ENCODING = 'utf-8'
    
    def __init__(self):
        self.validator = DataStructureValidator()
        self.last_import_result = None
    
    def import_file(self, filepath: Union[str, Path], 
                   sheet_name: Optional[str] = None,
                   header_row: int = 0,
                   encoding: str = None) -> ImportedData:
        """
        Importe un fichier de données de nivellement.
        
        Args:
            filepath: Chemin vers le fichier
            sheet_name: Nom de la feuille Excel (None = première feuille)
            header_row: Ligne d'en-tête (0 = première ligne)
            encoding: Encodage pour les CSV (None = auto-détection)
            
        Returns:
            ImportedData: Données importées et validées
            
        Raises:
            FileImportError: Erreur lors de l'importation
            DataValidationError: Données non conformes
        """
        filepath = Path(filepath)
        
        # Validation du fichier
        self._validate_file(filepath)
        
        try:
            # Importation selon le format
            if filepath.suffix.lower() in ['.xlsx', '.xls']:
                df = self._import_excel(filepath, sheet_name, header_row)
            elif filepath.suffix.lower() == '.csv':
                df = self._import_csv(filepath, encoding, header_row)
            else:
                raise FileImportError(
                    f"Format non supporté: {filepath.suffix}",
                    filename=str(filepath),
                    file_type=filepath.suffix
                )
            
            # Préparation et validation
            prepared_data = self._prepare_data(df, filepath)
            
            # Sauvegarde du résultat
            self.last_import_result = prepared_data
            
            return prepared_data
            
        except Exception as e:
            if isinstance(e, (FileImportError, DataValidationError)):
                raise
            else:
                raise FileImportError(
                    f"Erreur inattendue lors de l'importation: {str(e)}",
                    filename=str(filepath)
                )
    
    def _validate_file(self, filepath: Path):
        """Validation du fichier avant importation."""
        if not filepath.exists():
            raise FileImportError(
                f"Fichier non trouvé: {filepath}",
                filename=str(filepath)
            )
        
        if filepath.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise FileImportError(
                f"Format non supporté: {filepath.suffix}. "
                f"Formats acceptés: {', '.join(self.SUPPORTED_FORMATS)}",
                filename=str(filepath),
                file_type=filepath.suffix
            )
        
        if filepath.stat().st_size == 0:
            raise FileImportError(
                "Fichier vide",
                filename=str(filepath)
            )
        
        if filepath.stat().st_size > 100 * 1024 * 1024:  # 100 MB
            raise FileImportError(
                f"Fichier trop volumineux: {filepath.stat().st_size / (1024*1024):.1f} MB > 100 MB",
                filename=str(filepath)
            )
    
    def _validate_file_new(self, filepath: Path):
        """Validation du fichier - délègue au FileValidator."""
        validator = FileValidator()
        result = validator.validate_file(filepath)
        
        if not result.is_valid:
            raise FileImportError(
                f"Fichier invalide: {'; '.join(result.errors)}",
                filename=str(filepath)
            )
    
    def _import_excel(self, filepath: Path, sheet_name: Optional[str], 
                     header_row: int) -> pd.DataFrame:
        """Importation depuis Excel."""
        try:
            # Lecture du fichier Excel
            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                header=header_row,
                engine='openpyxl' if filepath.suffix.lower() == '.xlsx' else None
            )
            
            # Si sheet_name=None, pandas retourne un dict avec toutes les feuilles
            if isinstance(df, dict):
                # Prendre la première feuille
                sheet_names = list(df.keys())
                if not sheet_names:
                    raise FileImportError(
                        "Aucune feuille trouvée dans le fichier Excel",
                        filename=str(filepath),
                        file_type="Excel"
                    )
                df = df[sheet_names[0]]  # Prendre la première feuille
            
            if df.empty:
                raise FileImportError(
                    "Feuille Excel vide ou aucune donnée trouvée",
                    filename=str(filepath)
                )
            
            return df
            
        except pd.errors.EmptyDataError:
            raise FileImportError(
                "Fichier Excel vide ou corrompu",
                filename=str(filepath),
                file_type="Excel"
            )
        except pd.errors.ParserError as e:
            raise FileImportError(
                f"Erreur de lecture Excel: {str(e)}",
                filename=str(filepath),
                file_type="Excel"
            )
        except Exception as e:
            raise FileImportError(
                f"Erreur Excel inattendue: {str(e)}",
                filename=str(filepath),
                file_type="Excel"
            )
    
    def _import_csv(self, filepath: Path, encoding: Optional[str], 
                   header_row: int) -> pd.DataFrame:
        """Importation depuis CSV avec détection automatique de l'encodage."""
        if encoding is None:
            encoding = self._detect_encoding(filepath)
        
        try:
            # Tentative de lecture avec différents séparateurs
            separators = [',', ';', '\t', '|']
            df = None
            
            for sep in separators:
                try:
                    df = pd.read_csv(
                        filepath,
                        sep=sep,
                        header=header_row,
                        encoding=encoding
                    )
                    
                    # Vérifier si la lecture a du sens (plus d'une colonne)
                    if len(df.columns) > 1 and not df.empty:
                        break
                except:
                    continue
            
            if df is None or df.empty:
                raise FileImportError(
                    "Impossible de lire le fichier CSV ou fichier vide",
                    filename=str(filepath),
                    file_type="CSV"
                )
            
            return df
            
        except UnicodeDecodeError:
            raise FileImportError(
                f"Problème d'encodage. Essayez avec encoding='latin1' ou 'cp1252'",
                filename=str(filepath),
                file_type="CSV"
            )
        except Exception as e:
            raise FileImportError(
                f"Erreur CSV: {str(e)}",
                filename=str(filepath),
                file_type="CSV"
            )
    
    def _detect_encoding(self, filepath: Path) -> str:
        """Détection automatique de l'encodage."""
        encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)  # Essayer de lire les premiers 1024 caractères
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Si aucun encodage ne fonctionne, utiliser utf-8 par défaut
        return 'utf-8'
    
    def _prepare_data(self, df: pd.DataFrame, filepath: Path) -> ImportedData:
        """Préparation et validation des données importées."""
        # 1. Nettoyage initial
        df = self._clean_dataframe(df)
        
        # 2. Validation structure
        validation_result = self.validator.validate_dataframe(df)
        
        if not validation_result.is_valid:
            raise DataValidationError(
                f"Validation échouée: {'; '.join(validation_result.errors)}",
                invalid_data={'fichier': str(filepath)}
            )
        
        # 3. Extraction des informations
        ar_columns = validation_result.details.get('ar_columns', [])
        av_columns = validation_result.details.get('av_columns', [])
        dist_columns = validation_result.details.get('dist_columns', [])
        
        # 4. Identification des points initial et final
        initial_point, final_point = self._identify_endpoints(df)
        
        # 5. Métadonnées
        metadata = {
            'source_file': str(filepath),
            'import_timestamp': pd.Timestamp.now(),
            'total_points': len(df),
            'total_columns': len(df.columns),
            'file_size_bytes': filepath.stat().st_size,
            'statistics': validation_result.details.get('statistics', {})
        }
        
        return ImportedData(
            dataframe=df,
            ar_columns=ar_columns,
            av_columns=av_columns,
            dist_columns=dist_columns,
            initial_point=initial_point,
            final_point=final_point,
            metadata=metadata,
            validation_result=validation_result
        )
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoyage du DataFrame."""
        # Nettoyer les noms de colonnes - supprimer tous les espaces
        df.columns = df.columns.astype(str).str.strip().str.replace(' ', '_', regex=False)
        
        # Supprimer les lignes entièrement vides
        df = df.dropna(how='all')
        
        # Supprimer les colonnes entièrement vides
        df = df.dropna(axis=1, how='all')
        
        # Réindexer proprement
        df = df.reset_index(drop=True)
        
        # Supprimer les lignes sans Matricule (si la colonne existe)
        if 'Matricule' in df.columns:
            df = df.dropna(subset=['Matricule']).reset_index(drop=True)
        
        return df
    
    def _identify_endpoints(self, df: pd.DataFrame) -> Tuple[str, str]:
        """Identification des points initial et final."""
        if 'Matricule' not in df.columns:
            raise DataValidationError("Colonne 'Matricule' manquante pour identifier les points")
        
        matricules = df['Matricule'].dropna()
        if matricules.empty:
            raise DataValidationError("Aucun matricule valide trouvé")
        
        initial_point = str(matricules.iloc[0])
        final_point = str(matricules.iloc[-1])
        
        return initial_point, final_point
    
    def get_import_summary(self) -> str:
        """Résumé de la dernière importation."""
        if self.last_import_result is None:
            return "Aucune importation effectuée"
        
        data = self.last_import_result
        summary = f"""
=== RÉSUMÉ D'IMPORTATION ===
📁 Fichier: {data.metadata['source_file']}
📊 Points: {data.metadata['total_points']}
📋 Colonnes: {data.metadata['total_columns']}
📏 Taille: {data.metadata['file_size_bytes'] / 1024:.1f} KB

🎯 Points de cheminement:
   Initial: {data.initial_point}
   Final: {data.final_point}
   Type: {'Fermé' if data.initial_point == data.final_point else 'Ouvert'}

📐 Colonnes détectées:
   AR: {len(data.ar_columns)} ({', '.join(data.ar_columns)})
   AV: {len(data.av_columns)} ({', '.join(data.av_columns)})
   DIST: {len(data.dist_columns)} ({', '.join(data.dist_columns)})

{data.validation_result.get_summary()}
"""
        return summary
    
    def export_prepared_data(self, output_path: Union[str, Path], 
                           format: str = 'excel') -> Path:
        """
        Export des données préparées.
        
        Args:
            output_path: Chemin de sortie
            format: Format ('excel' ou 'csv')
            
        Returns:
            Path: Chemin du fichier exporté
        """
        if self.last_import_result is None:
            raise DataValidationError("Aucune donnée à exporter")
        
        output_path = Path(output_path)
        df = self.last_import_result.dataframe
        
        try:
            if format.lower() == 'excel':
                if not output_path.suffix:
                    output_path = output_path.with_suffix('.xlsx')
                df.to_excel(output_path, index=False)
            elif format.lower() == 'csv':
                if not output_path.suffix:
                    output_path = output_path.with_suffix('.csv')
                df.to_csv(output_path, index=False, encoding='utf-8')
            else:
                raise ValueError(f"Format non supporté: {format}")
            
            return output_path
            
        except Exception as e:
            raise FileImportError(
                f"Erreur lors de l'export: {str(e)}",
                filename=str(output_path)
            )


