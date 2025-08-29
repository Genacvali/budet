#!/bin/bash
# Test build script for Budget PWA
set -euo pipefail

echo "🧪 Testing Budget PWA build process..."

cd frontend

echo "🧹 Cleaning old files..."
rm -rf node_modules package-lock.json build .svelte-kit 2>/dev/null || true

echo "📥 Installing dependencies with legacy peer deps..."
npm install --legacy-peer-deps

echo "🔍 Checking TailwindCSS config..."
if [ -f "tailwind.config.js" ]; then
  echo "✅ TailwindCSS config found"
else
  echo "❌ TailwindCSS config missing"
  exit 1
fi

echo "🔍 Checking PostCSS config..."
if [ -f "postcss.config.js" ]; then
  echo "✅ PostCSS config found"
else
  echo "❌ PostCSS config missing"
  exit 1
fi

echo "🔨 Building project..."
npm run build

if [ -d "build" ]; then
  echo "✅ Build successful!"
  echo "📁 Build directory contents:"
  ls -la build/
  
  # Проверяем что CSS содержит TailwindCSS классы
  if find build -name "*.css" -exec grep -l "tailwind\|tw-" {} \; | head -1 >/dev/null; then
    echo "✅ TailwindCSS compiled successfully"
  else
    echo "⚠️ TailwindCSS might not be working - no tailwind classes found in CSS"
  fi
  
  # Проверяем service worker
  if [ -f "build/service-worker.js" ]; then
    echo "✅ Service Worker generated"
  else
    echo "⚠️ Service Worker not found"
  fi
  
else
  echo "❌ Build failed - no build directory"
  exit 1
fi

cd ..

echo "🎉 Test build completed successfully!"
echo "Ready to deploy with: ./deploy-to-server.sh"