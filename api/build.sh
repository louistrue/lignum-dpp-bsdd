#!/bin/bash
# Vercel build script: installs Python deps AND builds the web frontend
# This ensures api/static/enrich/ always matches the latest web/src/ code
set -e

pip install -r requirements.txt

cd ../web
npm ci
npm run build
cd ..

rm -rf api/static/enrich api/static/emissions
cp -r public/enrich api/static/enrich
cp -r public/emissions api/static/emissions

echo "Build complete: Python deps + web frontend rebuilt"
