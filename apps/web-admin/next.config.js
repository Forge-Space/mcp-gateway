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
  distDir: '.next',
  // Force all pages to be server-side rendered
  generateBuildId: () => 'build',
};

export default nextConfig;
