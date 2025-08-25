import adapter from '@sveltejs/adapter-static';
export default {
  kit: {
    adapter: adapter(),
    alias: { $lib: 'src/lib' },
    serviceWorker: { register: true }
  }
};