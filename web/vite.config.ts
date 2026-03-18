import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  base: '/enrich/',
  build: {
    outDir: '../public/enrich',
    emptyOutDir: true,
  },
});
