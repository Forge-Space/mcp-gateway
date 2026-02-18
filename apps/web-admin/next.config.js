/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    ppr: false,
  },
  trailingSlash: false,
  generateEtags: false,
  output: 'standalone',
  images: {
    unoptimized: true,
  },
  // Disable static generation completely
  outputMode: 'ssr',
  // Force server-side rendering for all pages
  ssr: true,
};

export default nextConfig;
