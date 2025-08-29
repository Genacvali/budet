#!/bin/bash
# Fix TypeScript issues in Budget PWA
set -euo pipefail

echo "🔧 Fixing TypeScript configuration issues..."

cd frontend

# Создаем простую конфигурацию без современных опций
cat > tsconfig.json << 'EOF'
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext", 
    "moduleResolution": "node",
    "strict": false,
    "lib": ["ES2020", "DOM"],
    "types": ["vite/client"],
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noEmit": true
  }
}
EOF

# Альтернативный svelte.config.js с минимальными опциями
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';
import sveltePreprocess from 'svelte-preprocess';

export default {
  preprocess: sveltePreprocess({
    postcss: true,
    typescript: {
      compilerOptions: {
        target: "ES2020",
        module: "ESNext"
      }
    }
  }),
  kit: {
    adapter: adapter({
      fallback: 'index.html',
      strict: false
    }),
    serviceWorker: { 
      register: true,
      files: (filepath) => !/\.DS_Store/.test(filepath)
    },
    alias: { 
      $lib: 'src/lib' 
    }
  }
};
EOF

echo "✅ TypeScript configuration simplified!"
echo "Now try: npm run build"