#!/usr/bin/env python3
"""
Script de test CLI pour l'import de données réelles.
Permet de tester l'onglet Import Données sans interface graphique.
"""

import sys
import os
from pathlib import Path
from tkinter import filedialog
import tkinter as tk

# Ajouter le répertoire parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.data_importer import DataImporter
from src.utils import quick_import

def test_import_cli():
    """Test interactif en ligne de commande."""
    print("🧮 Test du module d'import - Données topographiques")
    print("=" * 60)
    
    # Rechercher des fichiers Excel dans le projet
    excel_files = list(Path('.').rglob('*.xlsx')) + list(Path('.').rglob('*.xls'))
    csv_files = list(Path('.').rglob('*.csv'))
    
    if excel_files or csv_files:
        print("\n📁 Fichiers trouvés dans le projet :")
        all_files = excel_files + csv_files
        for i, file in enumerate(all_files, 1):
            print(f"  {i}. {file}")
        
        print(f"\n  {len(all_files) + 1}. Sélectionner un autre fichier...")
        
        try:
            choice = input(f"\nChoisissez un fichier (1-{len(all_files) + 1}) : ").strip()
            choice = int(choice)
            
            if 1 <= choice <= len(all_files):
                filepath = all_files[choice - 1]
            else:
                filepath = input("Chemin vers votre fichier : ").strip()
        except (ValueError, IndexError):
            filepath = input("Chemin vers votre fichier : ").strip()
    else:
        print("\n📂 Aucun fichier Excel/CSV trouvé dans le projet")
        filepath = input("Chemin vers votre fichier de données : ").strip()
    
    if not filepath or not Path(filepath).exists():
        print("❌ Fichier non trouvé !")
        return
    
    print(f"\n🔄 Import en cours : {filepath}")
    print("-" * 40)
    
    try:
        # Test avec DataImporter
        importer = DataImporter()
        result = importer.import_file(filepath)
        
        print("✅ IMPORT RÉUSSI !")
        print(f"\n📊 RÉSUMÉ DES DONNÉES :")
        print(f"   • Fichier : {Path(filepath).name}")
        print(f"   • Nombre de lignes : {len(result.dataframe)}")
        print(f"   • Colonnes AR : {len(result.ar_columns)} {result.ar_columns}")
        print(f"   • Colonnes AV : {len(result.av_columns)} {result.av_columns}")
        print(f"   • Colonnes DIST : {len(result.dist_columns)} {result.dist_columns}")
        print(f"   • Point initial : {result.initial_point}")
        print(f"   • Point final : {result.final_point}")
        print(f"   • Type : {'Fermé' if result.initial_point == result.final_point else 'Ouvert'}")
        
        print(f"\n📋 APERÇU DES DONNÉES (5 premières lignes) :")
        print(result.dataframe.head().to_string(index=False))
        
        print(f"\n✅ VALIDATION :")
        if result.validation_result.is_valid:
            print("   • Structure : ✅ Valide")
        else:
            print("   • Structure : ❌ Erreurs détectées")
            for error in result.validation_result.errors:
                print(f"     - {error}")
        
        if result.validation_result.warnings:
            print(f"   • Avertissements : {len(result.validation_result.warnings)}")
            for warning in result.validation_result.warnings:
                print(f"     ⚠️  {warning}")
        else:
            print("   • Avertissements : Aucun")
        
        print(f"\n📈 MÉTADONNÉES :")
        for key, value in result.metadata.items():
            print(f"   • {key} : {value}")
        
        print(f"\n🎯 L'onglet Import Données fonctionnerait parfaitement avec ce fichier !")
        
    except Exception as e:
        print(f"❌ ERREUR D'IMPORT : {str(e)}")
        print(f"\n🔍 Détails de l'erreur :")
        import traceback
        traceback.print_exc()

def test_quick_import():
    """Test avec la fonction quick_import."""
    print("\n" + "=" * 60)
    print("🚀 Test de l'import rapide (quick_import)")
    
    filepath = input("Chemin du fichier pour quick_import : ").strip()
    
    if not filepath or not Path(filepath).exists():
        print("❌ Fichier non trouvé !")
        return
    
    try:
        result = quick_import(filepath)
        print("✅ Quick import réussi !")
        print(f"Points : {len(result.dataframe)}")
        
    except Exception as e:
        print(f"❌ Erreur quick import : {str(e)}")

if __name__ == "__main__":
    test_import_cli()
    
    if input("\n🚀 Tester aussi quick_import ? (y/N) : ").lower().startswith('y'):
        test_quick_import()
    
    print("\n✨ Tests terminés !")