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