import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  base: '/enrich/',
  build: {
    outDir: '../api/static/enrich',
    emptyOutDir: true,
  },
});
