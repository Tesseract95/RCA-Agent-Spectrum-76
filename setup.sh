#!/bin/bash

# Setup script for Network Investigation Agent
# Run this after cloning the repository

set -e

echo "🚀 Setting up Network Investigation Agent..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your ANTHROPIC_API_KEY"
else
    echo "✓ .env file already exists"
fi

# Setup Python backend
echo ""
echo "📦 Installing Python dependencies..."

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "Using uv for Python package management..."
    uv sync
else
    echo "uv not found. Using pip..."
    pip install -e .
fi

# Initialize DuckDB database
echo ""
echo "🗄️  Initializing DuckDB database..."
cd starter_code
python -c "from db_duckdb import list_tables; tables = list_tables(); print(f'✓ Database initialized with {len(tables)} tables')"
cd ..

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "✓ Node modules already installed"
fi

cd ..

# Create .gitignore for DuckDB file if not exists
if ! grep -q "network_rca.duckdb" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# DuckDB database" >> .gitignore
    echo "network_rca.duckdb" >> .gitignore
    echo "network_rca.duckdb.wal" >> .gitignore
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Test the CLI: cd starter_code && python main.py"
echo "  3. Or start the API: cd starter_code && python api.py"
echo "  4. Or start the frontend: cd frontend && npm run dev"
echo ""
echo "📚 See README.md for detailed usage instructions"
