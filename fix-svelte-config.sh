#!/bin/bash
set -e

echo "=== Fixing SvelteKit Config ==="

cd frontend

# Попробуем разные варианты импорта vitePreprocess
echo "Trying different vitePreprocess import strategies..."

# Вариант 1: современный импорт
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte/preprocess';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    alias: { $lib: 'src/lib' },
    serviceWorker: { register: true }
  }
};
EOF

echo "Testing build with vite-plugin-svelte import..."
if npm run build; then
    echo "✅ Success with vite-plugin-svelte import!"
    exit 0
fi

# Вариант 2: старый импорт  
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';
import preprocess from 'svelte-preprocess';

export default {
  preprocess: preprocess(),
  kit: {
    adapter: adapter(),
    alias: { $lib: 'src/lib' },
    serviceWorker: { register: true }
  }
};
EOF

echo "Installing svelte-preprocess..."
npm install --save-dev svelte-preprocess

echo "Testing build with svelte-preprocess..."
if npm run build; then
    echo "✅ Success with svelte-preprocess!"
    exit 0
fi

# Вариант 3: без препроцессора (только для экстренных случаев)
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter(),
    alias: { $lib: 'src/lib' },
    serviceWorker: { register: true }
  }
};
EOF

echo "Testing build without preprocessor..."
if npm run build; then
    echo "✅ Success without preprocessor (but TypeScript might not work in .svelte files)!"
    exit 0
fi

echo "❌ All attempts failed"
exit 1