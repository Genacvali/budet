import adapter from '@sveltejs/adapter-static';
import sveltePreprocess from 'svelte-preprocess';

export default {
  preprocess: sveltePreprocess({
    postcss: true,
    typescript: {
      tsconfigFile: './tsconfig.json',
      compilerOptions: {
        verbatimModuleSyntax: true
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
    alias: { $lib: 'src/lib' }
  }
};