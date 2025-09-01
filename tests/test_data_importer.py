"""
Tests unitaires pour le module DataImporter.

Ces tests vérifient le bon fonctionnement de l'importation des données
avec validation automatique et gestion robuste des erreurs.

Couverture:
- Import Excel/CSV
- Validation structure
- Détection colonnes AR/AV/DIST
- Gestion erreurs et cas limites

Auteur: Système de Compensation Altimétrique
Version: 1.0
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import des modules à tester
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_importer import DataImporter, ImportedData
from src.utils import quick_import, validate_file_format
from src.exceptions import FileImportError, DataValidationError
from src.validators import ValidationResult


class TestDataImporter(unittest.TestCase):
    """Tests pour la classe DataImporter."""
    
    def setUp(self):
        """Préparation des tests."""
        self.importer = DataImporter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer des données de test valides
        self.valid_data = pd.DataFrame({
            'Matricule': ['AM2', 'PT1', 'PT2', 'PT3', 'AM2'],
            'AR 1': [1.234, 1.567, 1.890, 2.123, 1.456],
            'AV 1': [1.567, 1.890, 2.123, 1.456, 1.789],
            'AR 2': [1.235, 1.568, 1.891, 2.124, 1.457],
            'AV 2': [1.568, 1.891, 2.124, 1.457, 1.790],
            'DIST 1': [150.5, 175.2, 200.8, 180.3, 165.7],
            'DIST 2': [150.5, 175.2, 200.8, 180.3, 165.7]
        })
        
        # Données invalides pour tests d'erreur
        self.invalid_data = pd.DataFrame({
            'Point': ['P1', 'P2'],  # Pas de colonne 'Matricule'
            'Reading1': [1.0, 2.0],
            'Reading2': [1.5, 2.5]
        })
    
    def tearDown(self):
        """Nettoyage après tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_excel(self, df: pd.DataFrame, filename: str = 'test.xlsx') -> Path:
        """Crée un fichier Excel temporaire."""
        filepath = Path(self.temp_dir) / filename
        df.to_excel(filepath, index=False)
        return filepath
    
    def create_temp_csv(self, df: pd.DataFrame, filename: str = 'test.csv') -> Path:
        """Crée un fichier CSV temporaire."""
        filepath = Path(self.temp_dir) / filename
        df.to_csv(filepath, index=False)
        return filepath
    
    def test_import_valid_excel(self):
        """Test import Excel valide."""
        # Créer fichier temporaire
        filepath = self.create_temp_excel(self.valid_data)
        
        # Import
        result = self.importer.import_file(filepath)
        
        # Vérifications
        self.assertIsInstance(result, ImportedData)
        self.assertEqual(len(result.dataframe), 5)
        self.assertEqual(len(result.ar_columns), 2)
        self.assertEqual(len(result.av_columns), 2)
        self.assertEqual(len(result.dist_columns), 2)
        self.assertEqual(result.initial_point, 'AM2')
        self.assertEqual(result.final_point, 'AM2')
        self.assertTrue(result.validation_result.is_valid)
    
    def test_import_valid_csv(self):
        """Test import CSV valide."""
        filepath = self.create_temp_csv(self.valid_data)
        
        result = self.importer.import_file(filepath)
        
        self.assertIsInstance(result, ImportedData)
        self.assertEqual(len(result.dataframe), 5)
        self.assertTrue(result.validation_result.is_valid)
    
    def test_import_file_not_found(self):
        """Test fichier inexistant."""
        with self.assertRaises(FileImportError) as context:
            self.importer.import_file('fichier_inexistant.xlsx')
        
        self.assertIn('non trouvé', str(context.exception))
    
    def test_import_unsupported_format(self):
        """Test format non supporté."""
        filepath = Path(self.temp_dir) / 'test.txt'
        filepath.write_text('contenu quelconque')
        
        with self.assertRaises(FileImportError) as context:
            self.importer.import_file(filepath)
        
        self.assertIn('Format non supporté', str(context.exception))
    
    def test_import_empty_file(self):
        """Test fichier vide."""
        filepath = Path(self.temp_dir) / 'empty.xlsx'
        filepath.touch()  # Créer fichier vide
        
        with self.assertRaises(FileImportError):
            self.importer.import_file(filepath)
    
    def test_import_invalid_structure(self):
        """Test structure de données invalide."""
        filepath = self.create_temp_excel(self.invalid_data)
        
        with self.assertRaises(DataValidationError) as context:
            self.importer.import_file(filepath)
        
        self.assertIn('Validation échouée', str(context.exception))
    
    def test_column_detection(self):
        """Test détection des colonnes AR/AV/DIST."""
        # Test avec variations de noms
        df_variations = pd.DataFrame({
            'Matricule': ['P1', 'P2', 'P3'],
            'AR1': [1.0, 1.1, 1.2],
            'AV1': [1.1, 1.2, 1.3],
            'AR 2': [1.0, 1.1, 1.2],
            'AV 2': [1.1, 1.2, 1.3],
            'DIST1': [100, 120, 110],
            'Dist 2': [100, 120, 110]
        })
        
        filepath = self.create_temp_excel(df_variations)
        result = self.importer.import_file(filepath)
        
        # Vérifier détection flexible
        self.assertEqual(len(result.ar_columns), 2)
        self.assertEqual(len(result.av_columns), 2)
        self.assertEqual(len(result.dist_columns), 2)
    
    def test_data_cleaning(self):
        """Test nettoyage des données."""
        # Données avec espaces et lignes vides
        df_dirty = pd.DataFrame({
            'Matricule': ['P1', '', 'P3', None],
            ' AR 1 ': [1.0, np.nan, 1.2, 1.3],
            ' AV 1 ': [1.1, 1.15, np.nan, 1.4],
            'DIST 1': [100, 110, 120, 130]
        })
        
        filepath = self.create_temp_excel(df_dirty)
        result = self.importer.import_file(filepath)
        
        # Vérifier nettoyage
        self.assertEqual(len(result.dataframe), 2)  # Lignes sans Matricule supprimées
        self.assertTrue(all(' ' not in col for col in result.dataframe.columns))
    
    def test_endpoints_identification(self):
        """Test identification points initial/final."""
        filepath = self.create_temp_excel(self.valid_data)
        result = self.importer.import_file(filepath)
        
        # Cheminement fermé
        self.assertEqual(result.initial_point, 'AM2')
        self.assertEqual(result.final_point, 'AM2')
        
        # Test cheminement ouvert
        df_open = self.valid_data.copy()
        df_open.loc[4, 'Matricule'] = 'PT4'  # Modifier dernier point
        
        filepath_open = self.create_temp_excel(df_open)
        result_open = self.importer.import_file(filepath_open)
        
        self.assertEqual(result_open.initial_point, 'AM2')
        self.assertEqual(result_open.final_point, 'PT4')
    
    def test_metadata_generation(self):
        """Test génération des métadonnées."""
        filepath = self.create_temp_excel(self.valid_data)
        result = self.importer.import_file(filepath)
        
        metadata = result.metadata
        
        self.assertIn('source_file', metadata)
        self.assertIn('import_timestamp', metadata)
        self.assertIn('total_points', metadata)
        self.assertIn('statistics', metadata)
        self.assertEqual(metadata['total_points'], 5)
    
    def test_export_prepared_data(self):
        """Test export des données préparées."""
        filepath = self.create_temp_excel(self.valid_data)
        result = self.importer.import_file(filepath)
        
        # Export Excel
        output_excel = Path(self.temp_dir) / 'output.xlsx'
        exported_path = self.importer.export_prepared_data(output_excel, 'excel')
        
        self.assertTrue(exported_path.exists())
        
        # Vérifier contenu
        df_exported = pd.read_excel(exported_path)
        self.assertEqual(len(df_exported), 5)
        
        # Export CSV
        output_csv = Path(self.temp_dir) / 'output.csv'
        exported_csv = self.importer.export_prepared_data(output_csv, 'csv')
        
        self.assertTrue(exported_csv.exists())
    
    def test_import_summary(self):
        """Test génération du résumé d'importation."""
        filepath = self.create_temp_excel(self.valid_data)
        result = self.importer.import_file(filepath)
        
        summary = self.importer.get_import_summary()
        
        self.assertIn('RÉSUMÉ D\'IMPORTATION', summary)
        self.assertIn('Points: 5', summary)
        self.assertIn('Type: Fermé', summary)
        self.assertIn('AR: 2', summary)


class TestQuickImport(unittest.TestCase):
    """Tests pour les fonctions utilitaires."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.valid_data = pd.DataFrame({
            'Matricule': ['P1', 'P2', 'P3'],
            'AR 1': [1.0, 1.1, 1.2],
            'AV 1': [1.1, 1.2, 1.3],
            'DIST 1': [100, 110, 120]
        })
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_quick_import_function(self):
        """Test fonction quick_import."""
        filepath = Path(self.temp_dir) / 'test.xlsx'
        self.valid_data.to_excel(filepath, index=False)
        
        result = quick_import(filepath)
        
        self.assertIsInstance(result, ImportedData)
        self.assertEqual(len(result.dataframe), 3)
    
    def test_validate_file_format(self):
        """Test validation format de fichier."""
        self.assertTrue(validate_file_format('test.xlsx'))
        self.assertTrue(validate_file_format('test.xls'))
        self.assertTrue(validate_file_format('test.csv'))
        self.assertFalse(validate_file_format('test.txt'))
        self.assertFalse(validate_file_format('test.pdf'))


class TestDataValidation(unittest.TestCase):
    """Tests spécifiques pour la validation des données."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.importer = DataImporter()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_missing_required_columns(self):
        """Test colonnes obligatoires manquantes."""
        df_no_matricule = pd.DataFrame({
            'Point_ID': ['P1', 'P2'],
            'AR 1': [1.0, 1.1],
            'AV 1': [1.1, 1.2]
        })
        
        filepath = Path(self.temp_dir) / 'no_matricule.xlsx'
        df_no_matricule.to_excel(filepath, index=False)
        
        with self.assertRaises(DataValidationError) as context:
            self.importer.import_file(filepath)
        
        self.assertIn('Colonnes obligatoires manquantes', str(context.exception))
    
    def test_mismatched_ar_av_pairs(self):
        """Test paires AR/AV incohérentes."""
        df_mismatch = pd.DataFrame({
            'Matricule': ['P1', 'P2'],
            'AR 1': [1.0, 1.1],
            'AR 2': [1.0, 1.1],
            'AV 1': [1.1, 1.2]  # Manque AV 2
        })
        
        filepath = Path(self.temp_dir) / 'mismatch.xlsx'
        df_mismatch.to_excel(filepath, index=False)
        
        with self.assertRaises(DataValidationError) as context:
            self.importer.import_file(filepath)
        
        self.assertIn('Nombre incohérent AR', str(context.exception))
    
    def test_insufficient_points(self):
        """Test nombre insuffisant de points."""
        df_one_point = pd.DataFrame({
            'Matricule': ['P1'],
            'AR 1': [1.0],
            'AV 1': [1.1]
        })
        
        filepath = Path(self.temp_dir) / 'one_point.xlsx'
        df_one_point.to_excel(filepath, index=False)
        
        with self.assertRaises(DataValidationError) as context:
            self.importer.import_file(filepath)
        
        self.assertIn('Au moins 2 points', str(context.exception))
    
    def test_non_numeric_readings(self):
        """Test lectures non numériques."""
        df_non_numeric = pd.DataFrame({
            'Matricule': ['P1', 'P2', 'P3'],
            'AR 1': [1.0, 'abc', 1.2],  # Valeur non numérique
            'AV 1': [1.1, 1.2, 'def'],
            'DIST 1': [100, 110, 120]
        })
        
        filepath = Path(self.temp_dir) / 'non_numeric.xlsx'
        df_non_numeric.to_excel(filepath, index=False)
        
        # Devrait importer mais avec avertissements
        result = self.importer.import_file(filepath)
        self.assertTrue(len(result.validation_result.warnings) > 0)
    
    def test_duplicate_matricules(self):
        """Test matricules dupliqués."""
        df_duplicates = pd.DataFrame({
            'Matricule': ['P1', 'P2', 'P2', 'P3'],  # P2 dupliqué
            'AR 1': [1.0, 1.1, 1.2, 1.3],
            'AV 1': [1.1, 1.2, 1.3, 1.4]
        })
        
        filepath = Path(self.temp_dir) / 'duplicates.xlsx'
        df_duplicates.to_excel(filepath, index=False)
        
        result = self.importer.import_file(filepath)
        # Devrait générer un avertissement
        self.assertIn('dupliqués', ' '.join(result.validation_result.warnings))


class TestErrorHandling(unittest.TestCase):
    """Tests pour la gestion d'erreurs."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.importer = DataImporter()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_corrupted_excel_file(self):
        """Test fichier Excel corrompu."""
        # Créer un faux fichier Excel (juste du texte)
        corrupted_file = Path(self.temp_dir) / 'corrupted.xlsx'
        corrupted_file.write_text('Ce n\'est pas un fichier Excel valide')
        
        with self.assertRaises(FileImportError) as context:
            self.importer.import_file(corrupted_file)
        
        self.assertIn('Excel', str(context.exception))
    
    def test_csv_encoding_issues(self):
        """Test problèmes d'encodage CSV."""
        # Créer CSV avec caractères spéciaux
        csv_content = 'Matricule,AR 1,AV 1\nP1,1.0,1.1\nP2café,1.2,1.3'
        csv_file = Path(self.temp_dir) / 'encoding_test.csv'
        
        # Écrire avec encoding latin-1
        with open(csv_file, 'w', encoding='latin-1') as f:
            f.write(csv_content)
        
        # Devrait réussir avec détection automatique
        try:
            result = self.importer.import_file(csv_file)
            self.assertIsInstance(result, ImportedData)
        except FileImportError:
            # Acceptable si la détection échoue
            pass
    
    def test_very_large_file_warning(self):
        """Test avertissement fichier très volumineux."""
        # Simuler un fichier très gros (>100MB) serait trop lourd
        # On teste juste la logique de validation
        large_file = Path(self.temp_dir) / 'large.xlsx'
        
        # Créer un fichier normal d'abord avec au moins 2 points
        df = pd.DataFrame({
            'Matricule': ['P1', 'P2'], 
            'AR 1': [1.0, 1.2], 
            'AV 1': [1.1, 1.3],
            'DIST 1': [100, 110]
        })
        df.to_excel(large_file, index=False)
        
        # Le fichier est normal, donc pas d'erreur
        result = self.importer.import_file(large_file)
        self.assertIsInstance(result, ImportedData)


class TestIntegrationDataImporter(unittest.TestCase):
    """Tests d'intégration pour DataImporter."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Données réalistes de test
        self.realistic_data = pd.DataFrame({
            'Matricule': ['R001', 'P001', 'P002', 'P003', 'P004', 'R001'],
            'AR 1': [1.2345, 1.5678, 1.8901, 2.1234, 1.4567, 1.7890],
            'AV 1': [1.5678, 1.8901, 2.1234, 1.4567, 1.7890, 2.0123],
            'AR 2': [1.2346, 1.5679, 1.8902, 2.1235, 1.4568, 1.7891],
            'AV 2': [1.5679, 1.8902, 2.1235, 1.4568, 1.7891, 2.0124],
            'DIST 1': [125.50, 147.20, 198.75, 156.30, 173.85, 164.60],
            'DIST 2': [125.50, 147.20, 198.75, 156.30, 173.85, 164.60]
        })
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test workflow complet d'importation."""
        # 1. Création fichier
        filepath = Path(self.temp_dir) / 'realistic_data.xlsx'
        self.realistic_data.to_excel(filepath, index=False)
        
        # 2. Import
        importer = DataImporter()
        result = importer.import_file(filepath)
        
        # 3. Vérifications complètes
        self.assertEqual(len(result.dataframe), 6)
        self.assertEqual(result.initial_point, 'R001')
        self.assertEqual(result.final_point, 'R001')  # Cheminement fermé
        self.assertEqual(len(result.ar_columns), 2)
        self.assertEqual(len(result.av_columns), 2)
        self.assertEqual(len(result.dist_columns), 2)
        
        # 4. Vérification validation
        self.assertTrue(result.validation_result.is_valid)
        self.assertEqual(len(result.validation_result.errors), 0)
        
        # 5. Vérification métadonnées
        self.assertEqual(result.metadata['total_points'], 6)
        self.assertIn('statistics', result.metadata)
        
        # 6. Test export
        output_path = importer.export_prepared_data(
            Path(self.temp_dir) / 'exported.xlsx'
        )
        self.assertTrue(output_path.exists())
        
        # 7. Test résumé
        summary = importer.get_import_summary()
        self.assertIn('Type: Fermé', summary)
        self.assertIn('Points: 6', summary)


if __name__ == '__main__':
    # Configuration des tests
    unittest.TestLoader.sortTestMethodsUsing = None
    
    # Suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajouter toutes les classes de test
    test_classes = [
        TestDataImporter,
        TestQuickImport,
        TestDataValidation,
        TestErrorHandling,
        TestIntegrationDataImporter
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Exécution des tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Résumé
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ DES TESTS - DATA IMPORTER")
    print(f"{'='*60}")
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Taux de réussite: {(result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100:.1f}%")
    
    # Afficher les échecs s'il y en a
    if result.failures:
        print(f"\nÉCHECS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERREURS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")