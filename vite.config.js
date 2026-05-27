import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  root: 'frontend',
  base: '/static/react-app/',
  plugins: [react()],
  build: {
    outDir: '../static/react-app',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        landing: resolve(__dirname, 'frontend/index.html'),
        dashboard: resolve(__dirname, 'frontend/dashboard.html')
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
});
