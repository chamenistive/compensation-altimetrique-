#!/usr/bin/env python3
"""Test direct avec les fichiers de données trouvés."""

import sys
import os
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.data_importer import DataImporter

def test_file(filepath):
    """Test un fichier spécifique."""
    print(f"\n{'='*60}")
    print(f"🔄 TEST : {filepath}")
    print('='*60)
    
    if not Path(filepath).exists():
        print(f"❌ Fichier non trouvé : {filepath}")
        return False
    
    try:
        importer = DataImporter()
        result = importer.import_file(filepath)
        
        print("✅ IMPORT RÉUSSI !")
        print(f"\n📊 DONNÉES IMPORTÉES :")
        print(f"   • Fichier : {Path(filepath).name}")
        print(f"   • Lignes : {len(result.dataframe)}")
        print(f"   • Colonnes AR : {len(result.ar_columns)} {result.ar_columns}")
        print(f"   • Colonnes AV : {len(result.av_columns)} {result.av_columns}")
        print(f"   • Point initial : {result.initial_point}")
        print(f"   • Point final : {result.final_point}")
        print(f"   • Type : {'Fermé' if result.initial_point == result.final_point else 'Ouvert'}")
        
        print(f"\n📋 APERÇU (5 premières lignes) :")
        print(result.dataframe.head().to_string(index=False))
        
        print(f"\n✅ VALIDATION :")
        if result.validation_result.is_valid:
            print("   • ✅ Structure valide")
        else:
            print("   • ❌ Erreurs :")
            for error in result.validation_result.errors:
                print(f"     - {error}")
        
        if result.validation_result.warnings:
            print(f"   • ⚠️  {len(result.validation_result.warnings)} avertissement(s) :")
            for warning in result.validation_result.warnings:
                print(f"     - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {str(e)}")
        return False

if __name__ == "__main__":
    print("🧮 Test direct des données topographiques")
    
    # Tester les 3 fichiers principaux trouvés
    files_to_test = [
        "RG.xlsx",
        "exemple_donnees_nivellement.xlsx", 
        "data/exemple_nivellement.xlsx"
    ]
    
    results = {}
    for filepath in files_to_test:
        results[filepath] = test_file(filepath)
    
    print(f"\n{'='*60}")
    print("📈 RÉSUMÉ FINAL")
    print('='*60)
    for filepath, success in results.items():
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"   • {filepath:<35} {status}")
    
    success_count = sum(results.values())
    print(f"\n🎯 {success_count}/{len(results)} fichiers importés avec succès")
    
    if success_count > 0:
        print("\n✨ L'onglet Import Données est PRÊT pour vos données réelles !")
    else:
        print("\n⚠️  Vérifiez le format de vos fichiers")