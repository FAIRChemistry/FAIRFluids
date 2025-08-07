#!/bin/bash

# Ensure md-models is available by activating conda and adding it to PATH
export PATH="$HOME/.local/bin:$PATH"

# Get current working directory
CURRENT_DIR=$(pwd)

echo "Current directory: $CURRENT_DIR"

echo "Converting model.md to mermaid..."
md-models convert -i "$CURRENT_DIR/specifications/model.md" -o "$CURRENT_DIR/schemes/mermaid.md" -t mermaid
echo "Mermaid conversion complete"

echo "Converting model.md to Python library..."
md-models convert -i "$CURRENT_DIR/specifications/model.md" -o "$CURRENT_DIR/core/lib.py" -t python-pydantic-xml
echo "Python library conversion complete"

