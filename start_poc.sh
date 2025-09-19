#!/bin/bash

# Lignum DPP PoC Quick Start Script
# This script sets up and runs the complete DPP proof-of-concept

echo "🚀 Starting Lignum DPP Proof of Concept"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "Installing API dependencies..."
    cd api && pip3 install -r requirements.txt && cd ..
}

python3 -c "import qrcode" 2>/dev/null || {
    echo "Installing QR code dependencies..."
    pip3 install qrcode pillow
}

echo ""
echo "🔄 Generating QR codes..."
python3 generate_qr_codes.py
echo ""

# Start the API server
# Determine a free port starting at 8000
BASE_PORT=8000
PORT=$BASE_PORT
while lsof -i :$PORT -sTCP:LISTEN -n -P >/dev/null 2>&1; do
    PORT=$((PORT+1))
done

echo "🌐 Starting DPP API server..."
echo "   API: http://localhost:$PORT"
echo "   Docs: http://localhost:$PORT/docs"
echo "   QR Viewer: file://$(pwd)/qr_codes/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Run with uvicorn, passing chosen PORT and enabling reload
cd api && PORT=$PORT HOST=0.0.0.0 RELOAD=true python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload
