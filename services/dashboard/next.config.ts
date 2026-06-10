import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'minio' },
      { protocol: 'https', hostname: '*.myshopify.com' },
    ],
  },
}

export default nextConfig
