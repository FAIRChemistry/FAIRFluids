#!/bin/bash
# FAIRFluids Conda Installation Script

set -e  # Exit on any error

echo "🚀 Setting up FAIRFluids conda environment..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo "Please install conda first: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if environment.yml exists
if [ ! -f "environment.yml" ]; then
    echo "❌ Error: environment.yml not found in current directory"
    echo "Please run this script from the FAIRFluids root directory"
    exit 1
fi

# Create conda environment
echo "📦 Creating conda environment 'fairfluids'..."
conda env create -f environment.yml

# Activate environment
echo "🔧 Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate fairfluids

# Test installation
echo "🧪 Testing installation..."
python -c "import fairfluids; print('✅ FAIRFluids imported successfully!')"

echo ""
echo "🎉 FAIRFluids installation complete!"
echo ""
echo "To activate the environment in the future:"
echo "  conda activate fairfluids"
echo ""
echo "To deactivate:"
echo "  conda deactivate"
echo ""
echo "To remove the environment:"
echo "  conda env remove -n fairfluids"
echo ""
echo "Happy coding! 🧪"
