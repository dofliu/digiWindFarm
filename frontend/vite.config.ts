import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    // Load .env from project root (one level up from frontend/)
    const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
    // Also load frontend-local .env
    const localEnv = loadEnv(mode, '.', '');

    const backendPort = env.BACKEND_PORT || '8100';
    const frontendPort = parseInt(env.VITE_PORT || '3100', 10);
    const backendUrl = `http://localhost:${backendPort}`;
    const wsUrl = `ws://localhost:${backendPort}`;

    return {
      server: {
        port: frontendPort,
        host: '0.0.0.0',
        proxy: {
          '/api': {
            target: backendUrl,
            changeOrigin: true,
          },
          '/ws': {
            target: wsUrl,
            ws: true,
          },
        },
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(localEnv.GEMINI_API_KEY || env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(localEnv.GEMINI_API_KEY || env.GEMINI_API_KEY),
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
