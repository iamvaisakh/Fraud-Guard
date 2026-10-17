import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/stats': 'http://localhost:8000',
      '/score': 'http://localhost:8000',
      '/verify': 'http://localhost:8000',
    },
  },
})