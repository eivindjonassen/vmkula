import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Firebase Hosting static export configuration
  output: 'export',
  
  // Image optimization for static export
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
