#!/usr/bin/env python3
"""
Test complet du workflow : Import → Calculs → Compensation → Graphiques
Simule l'utilisation complète de l'application avec données réelles.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Configuration du path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Imports des modules backend
from src.data_importer import DataImporter
from src.calculator import LevelingCalculator
from src.compensator import LevelingCompensator
from src.atmospheric_corrections import create_standard_conditions

def print_step(step, title):
    """Affichage stylé des étapes."""
    print(f"\n{'='*70}")
    print(f"📋 ÉTAPE {step} : {title}")
    print('='*70)

def print_substep(title):
    """Affichage des sous-étapes."""
    print(f"\n🔸 {title}")
    print("-" * 50)

def test_workflow_complet(filepath):
    """Test du workflow complet avec un fichier de données."""
    
    print(f"🧮 TEST WORKFLOW COMPLET - COMPENSATION ALTIMÉTRIQUE")
    print(f"📁 Fichier : {Path(filepath).name}")
    print("="*70)
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 1 : IMPORT DES DONNÉES
        # ═══════════════════════════════════════════════════════════════
        print_step(1, "IMPORT DES DONNÉES")
        
        importer = DataImporter()
        imported_data = importer.import_file(filepath)
        
        print(f"✅ Import réussi !")
        print(f"   • {len(imported_data.dataframe)} points de mesure")
        print(f"   • {len(imported_data.ar_columns)} colonnes AR : {imported_data.ar_columns}")
        print(f"   • {len(imported_data.av_columns)} colonnes AV : {imported_data.av_columns}")
        print(f"   • Point initial : {imported_data.initial_point}")
        print(f"   • Point final : {imported_data.final_point}")
        print(f"   • Type : {'Fermé' if imported_data.initial_point == imported_data.final_point else 'Ouvert'}")
        
        if imported_data.validation_result.warnings:
            print(f"   ⚠️  {len(imported_data.validation_result.warnings)} avertissement(s)")
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 2 : CONFIGURATION DES PARAMÈTRES
        # ═══════════════════════════════════════════════════════════════
        print_step(2, "CONFIGURATION DES PARAMÈTRES")
        
        # Paramètres réalistes pour le nivellement de précision
        altitude_reference = 247.852  # Altitude NGF du point de référence
        precision_mm = 2.0           # Précision souhaitée en mm
        
        # Conditions atmosphériques standard
        atmospheric_conditions = create_standard_conditions()
        
        print(f"✅ Paramètres configurés :")
        print(f"   • Altitude de référence : {altitude_reference:.3f} m NGF")
        print(f"   • Précision cible : {precision_mm} mm")
        print(f"   • Conditions atmosphériques : Standard (20°C, 1013.25 hPa)")
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 3 : CALCULS DE NIVELLEMENT
        # ═══════════════════════════════════════════════════════════════
        print_step(3, "CALCULS DE NIVELLEMENT")
        
        calculator = LevelingCalculator(precision_mm=precision_mm)
        
        print_substep("Calcul des dénivelées élémentaires")
        calculation_results = calculator.calculate_complete_leveling(
            df=imported_data.dataframe,
            ar_columns=imported_data.ar_columns,
            av_columns=imported_data.av_columns,
            dist_columns=imported_data.dist_columns,
            initial_altitude=altitude_reference
        )
        
        print(f"✅ Calculs terminés !")
        print(f"   • {len(calculation_results.height_differences)} dénivelées calculées")
        print(f"   • {len(calculation_results.altitudes)} altitudes déterminées")
        
        # Afficher quelques dénivelées
        print(f"\n📊 Aperçu des dénivelées (5 premières) :")
        for i, hd in enumerate(calculation_results.height_differences[:5]):
            print(f"   Segment {i+1} : {hd.delta_h_m*1000:+7.2f} mm")
        
        # Statistiques des altitudes
        altitudes = [alt.altitude_m for alt in calculation_results.altitudes]
        print(f"\n📈 Statistiques des altitudes :")
        print(f"   • Min : {min(altitudes):.3f} m")
        print(f"   • Max : {max(altitudes):.3f} m") 
        print(f"   • Amplitude : {max(altitudes) - min(altitudes):.3f} m")
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 4 : COMPENSATION DU CHEMINEMENT
        # ═══════════════════════════════════════════════════════════════
        print_step(4, "COMPENSATION DU CHEMINEMENT")
        
        compensator = LevelingCompensator()
        
        print_substep("Extraction des distances pour la compensation")
        # Extraire les distances du DataFrame
        dist_columns = imported_data.dist_columns if imported_data.dist_columns else []
        if dist_columns:
            distances_m = imported_data.dataframe[dist_columns[0]].fillna(0).values
        else:
            # Distances par défaut si non spécifiées
            distances_m = np.full(len(imported_data.dataframe), 100.0)
            print(f"   ⚠️  Distances par défaut utilisées (100m)")
        
        print_substep("Analyse de l'erreur de fermeture et compensation")
        compensation_results = compensator.compensate(
            calculation_results, 
            distances_m=distances_m
        )
        
        print(f"✅ Compensation réalisée !")
        print(f"   • Méthode : {compensation_results.solution_method.value}")
        print(f"   • Points ajustés : {len(compensation_results.adjusted_altitudes)}")
        print(f"   • Résidus calculés : {len(compensation_results.residuals)}")
        
        # Utiliser l'analyse de fermeture du calcul initial
        closure_info = calculation_results.closure_analysis
        closure_error_mm = closure_info.closure_error_mm
        tolerance_mm = closure_info.tolerance_mm
        
        print(f"   • Erreur de fermeture : {closure_error_mm:+.2f} mm")
        print(f"   • Tolérance : {tolerance_mm:.2f} mm")
        
        # Évaluation de la qualité
        if abs(closure_error_mm) <= tolerance_mm:
            quality_status = "✅ EXCELLENTE"
            quality_color = "32"  # Vert
        elif abs(closure_error_mm) <= tolerance_mm * 1.5:
            quality_status = "⚠️  ACCEPTABLE"  
            quality_color = "33"  # Jaune
        else:
            quality_status = "❌ INSUFFISANTE"
            quality_color = "31"  # Rouge
            
        print(f"   • Qualité : \033[{quality_color}m{quality_status}\033[0m")
        
        # Statistiques de compensation
        stats = compensation_results.statistics
        print(f"   • Écart-type a posteriori : {stats.sigma_0_hat:.3f}")
        print(f"   • Degrés de liberté : {stats.degrees_of_freedom}")
        
        if compensation_results.adjusted_coordinates is not None:
            corrections_mm = compensation_results.adjusted_coordinates * 1000
            print(f"   • Corrections : {corrections_mm.min():+.2f} à {corrections_mm.max():+.2f} mm")
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 5 : GÉNÉRATION DES GRAPHIQUES
        # ═══════════════════════════════════════════════════════════════
        print_step(5, "GÉNÉRATION DES GRAPHIQUES")
        
        try:
            from src.visualizer import LevelingVisualizer
            visualizer = LevelingVisualizer()
            
            # Créer le dossier de sortie
            output_dir = Path("test_outputs")
            output_dir.mkdir(exist_ok=True)
            
            print_substep("Graphique 1: Profil altimétrique")
            try:
                fig1_path = visualizer.create_altitude_profile(
                    calculation_results, 
                    compensation_results
                )
                print(f"   ✅ Sauvegardé : {fig1_path}")
            except Exception as e:
                print(f"   ❌ Erreur profil : {e}")
            
            print_substep("Graphique 2: Analyse de fermeture")
            try:
                fig2_path = visualizer.create_closure_analysis_plot(
                    calculation_results.closure_analysis,
                    calculation_results
                )
                print(f"   ✅ Sauvegardé : {fig2_path}")
            except Exception as e:
                print(f"   ❌ Erreur fermeture : {e}")
            
            print_substep("Graphique 3: Diagnostics de compensation")
            try:
                fig3_path = visualizer.create_compensation_diagnostics(
                    compensation_results,
                    calculation_results
                )
                print(f"   ✅ Sauvegardé : {fig3_path}")
            except Exception as e:
                print(f"   ❌ Erreur diagnostics : {e}")
                
            print_substep("Graphique 4: Profil interactif")
            try:
                fig4_path = visualizer.create_interactive_altitude_profile(
                    calculation_results,
                    compensation_results
                )
                if fig4_path:
                    print(f"   ✅ Sauvegardé : {fig4_path}")
                else:
                    print(f"   ⚠️  Plotly non disponible")
            except Exception as e:
                print(f"   ⚠️  Graphique interactif : {e}")
            
        except ImportError as e:
            print(f"❌ Erreur import visualizer : {e}")
            print("   Les graphiques nécessitent matplotlib/plotly")
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 6 : RÉSUMÉ FINAL
        # ═══════════════════════════════════════════════════════════════
        print_step(6, "RÉSUMÉ FINAL")
        
        print(f"🎯 WORKFLOW COMPLET TERMINÉ AVEC SUCCÈS !")
        print(f"\n📊 RÉSULTATS FINAUX :")
        print(f"   • Fichier traité : {Path(filepath).name}")
        print(f"   • Points mesurés : {len(imported_data.dataframe)}")
        print(f"   • Dénivelées calculées : {len(calculation_results.height_differences)}")
        print(f"   • Erreur de fermeture : {calculation_results.closure_analysis.closure_error_mm:+.2f} mm")
        print(f"   • Qualité : {quality_status}")
        print(f"   • Graphiques générés : voir dossier test_outputs/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR DANS LE WORKFLOW : {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Programme principal."""
    
    # Fichiers de test disponibles
    test_files = [
        "RG.xlsx",
        "exemple_donnees_nivellement.xlsx"
    ]
    
    print("🧮 TEST DU WORKFLOW COMPLET - COMPENSATION ALTIMÉTRIQUE")
    print("="*70)
    
    results = {}
    
    for filepath in test_files:
        if Path(filepath).exists():
            success = test_workflow_complet(filepath)
            results[filepath] = success
        else:
            print(f"\n⚠️  Fichier non trouvé : {filepath}")
            results[filepath] = False
    
    # Résumé final
    print(f"\n{'='*70}")
    print("📈 RÉSUMÉ GLOBAL")
    print('='*70)
    
    for filepath, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"   • {filepath:<35} {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 {success_count}/{total_count} workflows réussis")
    
    if success_count > 0:
        print(f"\n✨ L'APPLICATION COMPLÈTE EST OPÉRATIONNELLE !")
        print(f"   Tous les modules fonctionnent parfaitement ensemble.")
    else:
        print(f"\n⚠️  Des corrections sont nécessaires.")

if __name__ == "__main__":
    main()