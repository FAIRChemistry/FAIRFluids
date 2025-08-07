@echo off
REM FAIRFluids Conda Installation Script for Windows

echo 🚀 Setting up FAIRFluids conda environment...

REM Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: conda is not installed or not in PATH
    echo Please install conda first: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

REM Check if environment.yml exists
if not exist "environment.yml" (
    echo ❌ Error: environment.yml not found in current directory
    echo Please run this script from the FAIRFluids root directory
    pause
    exit /b 1
)

REM Create conda environment
echo 📦 Creating conda environment 'fairfluids'...
conda env create -f environment.yml

REM Activate environment
echo 🔧 Activating environment...
call conda activate fairfluids

REM Test installation
echo 🧪 Testing installation...
python -c "import fairfluids; print('✅ FAIRFluids imported successfully!')"

echo.
echo 🎉 FAIRFluids installation complete!
echo.
echo To activate the environment in the future:
echo   conda activate fairfluids
echo.
echo To deactivate:
echo   conda deactivate
echo.
echo To remove the environment:
echo   conda env remove -n fairfluids
echo.
echo Happy coding! 🧪
pause
