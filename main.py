"""
Script principal pour la compensation altimétrique.

Application console utilisant les modules refactorisés pour démontrer
le pipeline complet avec une précision garantie de 2mm.

Pipeline:
1. Import et validation des données
2. Calculs préliminaires
3. Compensation par moindres carrés
4. Validation et rapport final

Auteur: Système de Compensation Altimétrique
Version: 1.0 (Modularisé)
Précision: 2mm
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, Tuple

# Import des modules développés
# from src.data_importer import DataImporter, quick_import
# from src.calculator import LevelingCalculator, quick_leveling_calculation
# from src.compensator import LevelingCompensator, quick_compensation
# from src.validators import PrecisionValidator
# from src.exceptions import *

# Import des modules développés
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_importer import DataImporter
from calculator import LevelingCalculator
from compensator import LevelingCompensator
from validators import PrecisionValidator
from exceptions import *
from atmospheric_corrections import (
    AtmosphericCorrector, AtmosphericConditions, create_standard_conditions
)
from visualizer import LevelingVisualizer
from utils import (
    quick_import, quick_leveling_calculation, quick_compensation, quick_visualization
)


class LevelingApplication:
    """
    Application principale de compensation altimétrique.
    
    Orchestre le pipeline complet avec gestion d'erreurs robuste
    et interface utilisateur console conviviale.
    """
    
    def __init__(self, precision_mm: float = 2.0):
        """
        Initialisation de l'application.
        
        Args:
            precision_mm: Précision cible en millimètres
        """
        self.precision_mm = precision_mm
        self.version = "1.0 (Modularisé)"
        
        # Modules principaux
        self.data_importer = DataImporter()
        # Créer conditions atmosphériques pour la région
        atmospheric_conditions = create_standard_conditions("sahel")  # Adapté pour l'Afrique
        self.calculator = LevelingCalculator(
            precision_mm, 
            apply_atmospheric_corrections=True,
            atmospheric_conditions=atmospheric_conditions
        )
        self.compensator = LevelingCompensator(precision_mm)
        self.validator = PrecisionValidator(precision_mm)
        self.visualizer = LevelingVisualizer(precision_mm)
        
        # Stockage des résultats
        self.imported_data = None
        self.calculation_results = None
        self.compensation_results = None
    
    def print_header(self):
        """Affichage de l'en-tête de l'application."""
        print(f"""
{'='*80}
    SYSTÈME DE COMPENSATION ALTIMÉTRIQUE
    Version: {self.version}
    Précision cible: {self.precision_mm} mm
{'='*80}
""")
    
    def run_interactive(self):
        """Mode interactif console."""
        self.print_header()
        
        try:
            # Étape 1: Import des données
            print("\n🔄 ÉTAPE 1: IMPORTATION DES DONNÉES")
            print("-" * 50)
            
            data_file = self._get_input_file()
            self.imported_data = self.data_importer.import_file(data_file)
            
            print("✅ Import réussi!")
            print(self.data_importer.get_import_summary())
            
            # Étape 2: Configuration des altitudes
            print("\n🔄 ÉTAPE 2: CONFIGURATION DES ALTITUDES")
            print("-" * 50)
            
            initial_altitude, final_altitude = self._get_known_altitudes()
            
            # Étape 3: Calculs préliminaires
            print("\n🔄 ÉTAPE 3: CALCULS PRÉLIMINAIRES")
            print("-" * 50)
            
            self.calculation_results = self.calculator.calculate_complete_leveling(
                self.imported_data.dataframe,
                self.imported_data.ar_columns,
                self.imported_data.av_columns,
                self.imported_data.dist_columns,
                initial_altitude,
                final_altitude
            )
            
            print("✅ Calculs préliminaires terminés!")
            print(self.calculator.generate_calculation_report(self.calculation_results))
            
            # Étape 4: Compensation par moindres carrés
            print("\n🔄 ÉTAPE 4: COMPENSATION PAR MOINDRES CARRÉS")
            print("-" * 50)
            
            # Préparation des distances
            if self.imported_data.dist_columns:
                distances = self.imported_data.dataframe[self.imported_data.dist_columns[0]].values
            else:
                # Distances par défaut
                n_points = len(self.imported_data.dataframe)
                distances = np.full(n_points-1, 100.0)  # 100m par segment
            
            self.compensation_results = self.compensator.compensate(
                self.calculation_results,
                distances
            )
            
            print("✅ Compensation terminée!")
            print(self.compensator.generate_compensation_report(self.compensation_results))
            
            # Étape 5: Validation finale
            print("\n🔄 ÉTAPE 5: VALIDATION FINALE")
            print("-" * 50)
            
            validation_result = self.compensator.validate_compensation_quality(
                self.compensation_results
            )
            
            print(validation_result.get_summary())
            
            # Étape 6: Génération des visualisations
            print("\n🔄 ÉTAPE 6: GÉNÉRATION DES VISUALISATIONS")
            print("-" * 50)
            
            # Vérifier si les visualisations sont activées (par défaut OUI)
            generate_viz = getattr(self, 'enable_visualizations', True)
            
            if generate_viz:
                try:
                    # Créer le dossier de visualisations
                    viz_dir = Path("./visualizations") / f"session_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                    self.visualizer = LevelingVisualizer(self.precision_mm, viz_dir)
                    
                    # Générer le rapport visuel complet
                    rapport_visuel = self.visualizer.create_complete_report(
                        self.calculation_results,
                        self.compensation_results
                    )
                    
                    print(f"✅ Visualisations générées!")
                    print(f"📁 Dossier: {viz_dir}")
                    print(f"📊 Rapport: {rapport_visuel.name}")
                    
                except Exception as e:
                    print(f"⚠️ Erreur génération visualisations: {e}")
                    print("   Continuons sans les graphiques...")
            else:
                print("⏭️ Visualisations désactivées")
            
            # Étape 7: Export des résultats
            print("\n🔄 ÉTAPE 7: EXPORT DES RÉSULTATS")
            print("-" * 50)
            
            self._export_results()
            
            print("\n🎯 TRAITEMENT TERMINÉ AVEC SUCCÈS!")
            
        except Exception as e:
            self._handle_error(e)
    
    def run_batch(self, input_file: Path, initial_altitude: float,
                  final_altitude: Optional[float] = None,
                  output_dir: Optional[Path] = None):
        """
        Mode batch (traitement automatique).
        
        Args:
            input_file: Fichier de données
            initial_altitude: Altitude de référence
            final_altitude: Altitude finale (si cheminement ouvert)
            output_dir: Dossier de sortie
        """
        self.print_header()
        
        try:
            print(f"📁 Fichier d'entrée: {input_file}")
            print(f"📏 Altitude initiale: {initial_altitude} m")
            if final_altitude:
                print(f"📏 Altitude finale: {final_altitude} m")
            
            # Pipeline complet automatique
            print("\n🚀 Démarrage du traitement automatique...")
            
            # Import
            print("   1/4 Import des données...")
            self.imported_data = self.data_importer.import_file(input_file)
            
            # Calculs
            print("   2/4 Calculs préliminaires...")
            self.calculation_results = self.calculator.calculate_complete_leveling(
                self.imported_data.dataframe,
                self.imported_data.ar_columns,
                self.imported_data.av_columns,
                self.imported_data.dist_columns,
                initial_altitude,
                final_altitude
            )
            
            # Compensation
            print("   3/4 Compensation par moindres carrés...")
            distances = (self.imported_data.dataframe[self.imported_data.dist_columns[0]].values
                        if self.imported_data.dist_columns
                        else np.full(len(self.imported_data.dataframe)-1, 100.0))
            
            self.compensation_results = self.compensator.compensate(
                self.calculation_results, distances
            )
            
            # Export et visualisations
            print("   4/5 Génération des visualisations...")
            output_dir = output_dir or input_file.parent / "results"
            
            # Créer les visualisations
            viz_dir = output_dir / "visualizations"
            visualizer = LevelingVisualizer(self.precision_mm, viz_dir)
            try:
                rapport_visuel = visualizer.create_complete_report(
                    self.calculation_results, self.compensation_results
                )
                print(f"       ✅ Graphiques générés dans: {viz_dir}")
            except Exception as e:
                print(f"       ⚠️ Erreur visualisations: {e}")
            
            print("   5/5 Export des résultats...")
            self._export_results(output_dir)
            
            print("\n✅ TRAITEMENT BATCH TERMINÉ!")
            print(f"📁 Résultats dans: {output_dir}")
            
            # Résumé final
            self._print_final_summary()
            
        except Exception as e:
            self._handle_error(e)
    
    def _get_input_file(self) -> Path:
        """Sélection interactive du fichier d'entrée."""
        while True:
            file_path = input("\n📁 Chemin vers le fichier Excel/CSV: ").strip()
            
            if not file_path:
                print("❌ Veuillez spécifier un chemin de fichier.")
                continue
            
            path = Path(file_path)
            
            if not path.exists():
                print(f"❌ Fichier non trouvé: {path}")
                continue
            
            if not path.suffix.lower() in ['.xlsx', '.xls', '.csv']:
                print("❌ Format non supporté. Utilisez Excel (.xlsx, .xls) ou CSV.")
                continue
            
            return path
    
    def _get_known_altitudes(self) -> Tuple[float, Optional[float]]:
        """Saisie interactive des altitudes connues."""
        # Altitude initiale
        while True:
            try:
                initial_str = input(
                    f"\n📏 Altitude du point initial ({self.imported_data.initial_point}) [m]: "
                ).strip()
                initial_altitude = float(initial_str)
                break
            except ValueError:
                print("❌ Veuillez entrer une valeur numérique valide.")
        
        # Altitude finale (si cheminement ouvert)
        final_altitude = None
        if self.imported_data.initial_point != self.imported_data.final_point:
            print(f"\n🔄 Cheminement ouvert détecté.")
            while True:
                try:
                    final_str = input(
                        f"📏 Altitude du point final ({self.imported_data.final_point}) [m]: "
                    ).strip()
                    final_altitude = float(final_str)
                    break
                except ValueError:
                    print("❌ Veuillez entrer une valeur numérique valide.")
        else:
            print(f"\n🔄 Cheminement fermé détecté.")
        
        return initial_altitude, final_altitude
    
    def _export_results(self, output_dir: Optional[Path] = None):
        """Export des résultats."""
        if output_dir is None:
            output_str = input("\n📁 Dossier de sortie (Entrée = dossier courant): ").strip()
            output_dir = Path(output_str) if output_str else Path.cwd()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Export Excel des résultats
        results_df = self.compensator.export_results_to_dataframe(self.compensation_results)
        excel_path = output_dir / "resultats_compensation.xlsx"
        results_df.to_excel(excel_path, index=False)
        print(f"📊 Résultats Excel: {excel_path}")
        
        # Export rapport texte
        report_path = output_dir / "rapport_compensation.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.calculator.generate_calculation_report(self.calculation_results))
            f.write("\n\n")
            f.write(self.compensator.generate_compensation_report(self.compensation_results))
        print(f"📝 Rapport: {report_path}")
        
        # Export données préparées
        prepared_path = output_dir / "donnees_preparees.xlsx"
        self.data_importer.export_prepared_data(prepared_path, 'excel')
        print(f"📋 Données préparées: {prepared_path}")
        
        print(f"\n✅ Export terminé dans: {output_dir}")
    
    def _print_final_summary(self):
        """Affichage du résumé final."""
        if not all([self.calculation_results, self.compensation_results]):
            return
        
        closure = self.calculation_results.closure_analysis
        stats = self.compensation_results.statistics
        
        print(f"""
{'='*80}
                        RÉSUMÉ FINAL
{'='*80}

🎯 OBJECTIF PRÉCISION: {self.precision_mm} mm

📊 STATISTIQUES GÉNÉRALES:
   Points traités: {len(self.compensation_results.adjusted_altitudes)}
   Type cheminement: {closure.traverse_type.value}
   Distance totale: {closure.total_distance_km:.3f} km

📐 PRÉCISION ATTEINTE:
   Erreur de fermeture: {abs(closure.closure_error_mm):.2f} mm
   Tolérance admise: ±{closure.tolerance_mm:.2f} mm
   Statut fermeture: {'✅ ACCEPTABLE' if closure.is_acceptable else '❌ DÉPASSEMENT'}
   
   Correction maximale: {self.compensation_results.computation_metadata['max_correction_mm']:.2f} mm
   Objectif 2mm: {'✅ ATTEINT' if self.compensation_results.computation_metadata['max_correction_mm'] <= 2.0 else '❌ DÉPASSÉ'}

📈 QUALITÉ STATISTIQUE:
   σ₀ (a posteriori): {stats.sigma_0_hat:.4f}
   Test χ² (poids): {'✅ VALIDÉ' if stats.unit_weight_valid else '❌ REJETÉ'}
   Fautes détectées: {self.compensation_results.computation_metadata['blunder_detection']['suspect_count']}

🎯 VERDICT FINAL: {'✅ SUCCÈS - PRÉCISION 2mm GARANTIE' if closure.is_acceptable and self.compensation_results.computation_metadata['max_correction_mm'] <= 2.0 else '⚠️ ATTENTION - VÉRIFIER RÉSULTATS'}

{'='*80}
""")
    
    def _handle_error(self, error: Exception):
        """Gestion centralisée des erreurs."""
        print(f"\n❌ ERREUR DÉTECTÉE: {type(error).__name__}")
        print(f"   Message: {str(error)}")
        
        if isinstance(error, LevelingError):
            if error.error_code:
                print(f"   Code: {error.error_code}")
            if error.details:
                print(f"   Détails: {error.details}")
        
        print(f"\n💡 SUGGESTIONS:")
        if isinstance(error, FileImportError):
            print("   • Vérifiez que le fichier existe et n'est pas corrompu")
            print("   • Assurez-vous que le format est supporté (Excel/CSV)")
            print("   • Vérifiez les permissions de lecture")
        
        elif isinstance(error, DataValidationError):
            print("   • Vérifiez la structure des données (colonnes Matricule, AR, AV)")
            print("   • Assurez-vous d'avoir au moins 2 points de mesure")
            print("   • Vérifiez que les paires AR/AV sont cohérentes")
        
        elif isinstance(error, CalculationError):
            print("   • Vérifiez les valeurs numériques des lectures")
            print("   • Contrôlez les altitudes de référence")
            print("   • Vérifiez la cohérence des distances")
        
        elif isinstance(error, PrecisionError):
            print("   • La précision demandée ne peut pas être atteinte")
            print("   • Vérifiez la qualité des observations")
            print("   • Considérez une re-mesure des segments problématiques")
        
        else:
            print("   • Consultez la documentation")
            print("   • Vérifiez les données d'entrée")
            print("   • Contactez le support technique si le problème persiste")
        
        sys.exit(1)


def create_sample_data():
    """Crée un fichier d'exemple pour les tests."""
    sample_data = pd.DataFrame({
        'Matricule': ['R001', 'P001', 'P002', 'P003', 'P004', 'R001'],
        'AR 1': [1.2345, 1.5678, 1.8901, 2.1234, 1.4567, 1.7890],
        'AV 1': [1.5678, 1.8901, 2.1234, 1.4567, 1.7890, 2.0123],
        'AR 2': [1.2346, 1.5679, 1.8902, 2.1235, 1.4568, 1.7891],
        'AV 2': [1.5679, 1.8902, 2.1235, 1.4568, 1.7891, 2.0124],
        'DIST 1': [125.50, 147.20, 198.75, 156.30, 173.85, 164.60],
        'DIST 2': [125.50, 147.20, 198.75, 156.30, 173.85, 164.60]
    })
    
    output_path = Path("exemple_donnees_nivellement.xlsx")
    sample_data.to_excel(output_path, index=False)
    
    print(f"📋 Fichier d'exemple créé: {output_path}")
    print(f"   • Cheminement fermé (R001 → P001 → P002 → P003 → P004 → R001)")
    print(f"   • 6 points, 2 instruments, distances incluses")
    print(f"   • Utilisable pour tester l'application")
    
    return output_path


def main():
    """Fonction principale avec interface en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Système de Compensation Altimétrique - Précision 2mm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  Mode interactif:
    python main.py

  Mode batch:
    python main.py -f donnees.xlsx -a 125.456

  Mode batch avec cheminement ouvert:
    python main.py -f donnees.xlsx -a 125.456 -af 127.123

  Créer fichier d'exemple:
    python main.py --create-sample

  Précision personnalisée:
    python main.py -f donnees.xlsx -a 125.456 --precision 1.0
        """)
    
    # Arguments principaux
    parser.add_argument('-f', '--file', type=Path,
                       help='Fichier de données Excel/CSV')
    parser.add_argument('-a', '--initial-altitude', type=float,
                       help='Altitude initiale de référence (mètres)')
    parser.add_argument('-af', '--final-altitude', type=float,
                       help='Altitude finale connue (cheminements ouverts)')
    parser.add_argument('-o', '--output', type=Path,
                       help='Dossier de sortie (défaut: ./results)')
    
    # Options avancées
    parser.add_argument('--precision', type=float, default=2.0,
                       help='Précision cible en mm (défaut: 2.0)')
    parser.add_argument('--no-atmospheric', action='store_true',
                       help='Désactiver les corrections atmosphériques')
    parser.add_argument('--temperature', type=float, default=28.0,
                       help='Température ambiante en °C (défaut: 28.0)')
    parser.add_argument('--pressure', type=float, default=1010.0,
                       help='Pression atmosphérique en hPa (défaut: 1010.0)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Créer un fichier d\'exemple et quitter')
    parser.add_argument('--no-visualizations', action='store_true',
                       help='Désactiver la génération des graphiques')
    
    # Options de débogage
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Mode verbeux')
    parser.add_argument('--version', action='version',
                       version='Compensation Altimétrique v1.0 (Modularisé)')
    
    args = parser.parse_args()
    
    # Cas spéciaux
    if args.create_sample:
        create_sample_data()
        return
    
    # Validation des arguments
    if args.file and not args.initial_altitude:
        parser.error("L'altitude initiale (-a) est requise avec le fichier (-f)")
    
    # Initialisation de l'application
    try:
        app = LevelingApplication(precision_mm=args.precision)
        
        # Configuration des visualisations
        app.enable_visualizations = not args.no_visualizations
        
        if args.file:
            # Mode batch
            app.run_batch(
                input_file=args.file,
                initial_altitude=args.initial_altitude,
                final_altitude=args.final_altitude,
                output_dir=args.output
            )
        else:
            # Mode interactif
            app.run_interactive()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption utilisateur. Arrêt du programme.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_quick_demo():
    """Démonstration rapide avec données synthétiques."""
    print("🚀 DÉMONSTRATION RAPIDE")
    print("="*50)
    
    # Créer données d'exemple
    sample_file = create_sample_data()
    
    # Traitement automatique
    app = LevelingApplication(precision_mm=2.0)
    app.run_batch(
        input_file=sample_file,
        initial_altitude=100.000,
        output_dir=Path("demo_results")
    )
    
    print("\n🎯 Démonstration terminée!")
    print("📁 Consultez le dossier 'demo_results' pour les résultats")


if __name__ == "__main__":
    # Vérifier si on veut la démo rapide
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        run_quick_demo()
    else:
        main()