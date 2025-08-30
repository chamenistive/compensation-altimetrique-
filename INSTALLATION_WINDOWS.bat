@echo off
echo 🖥️ INSTALLATION AUTOMATIQUE - WINDOWS
echo Système de Compensation Altimétrique
echo =====================================
echo.

REM Vérifier Python
echo 1. 🔍 Vérification de Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo Téléchargez Python sur https://www.python.org/downloads/
    echo IMPORTANT: Cochez "Add Python to PATH" pendant l'installation
    pause
    exit /b 1
)

echo ✅ Python détecté
echo.

REM Créer environnement virtuel
echo 2. 🏗️ Création de l'environnement virtuel...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Erreur création environnement virtuel
    pause
    exit /b 1
)

echo ✅ Environnement virtuel créé
echo.

REM Activer environnement virtuel
echo 3. ⚡ Activation de l'environnement virtuel...
call venv\Scripts\activate

REM Mettre à jour pip
echo 4. 🔄 Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer dépendances
echo 5. 📦 Installation des dépendances...
echo Cette étape peut prendre 2-5 minutes...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️ Erreur installation dépendances, tentative alternative...
    pip install customtkinter matplotlib numpy pandas Pillow plotly scipy openpyxl xlrd
)

echo ✅ Dépendances installées
echo.

REM Tests de validation
echo 6. 🧪 Tests de validation...
python demo_core_features.py
if %errorlevel% neq 0 (
    echo ⚠️ Problème détecté lors des tests
    echo Consultez le guide GUIDE_WINDOWS_DEBUTANT.md
)

echo.
echo 🎉 INSTALLATION TERMINÉE !
echo.
echo 🚀 Pour lancer l'interface:
echo    python gui\main_window.py
echo.
echo 🧪 Pour tester sans GUI:
echo    python demo_core_features.py
echo    python test_phase2_simple.py
echo.
echo 📖 Guide complet: GUIDE_WINDOWS_DEBUTANT.md
echo.
pause