import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
  // Optimisations pour le développement local
  reactCompiler: true,
  
  typescript: {
    // Ignorer les erreurs TypeScript pendant le build (accélère le build)
    ignoreBuildErrors: true,
  },
  
  // Optimisations de compilation
  experimental: {
    // Optimise le bundling des packages
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-dialog",
      "@radix-ui/react-select",
      "@radix-ui/react-alert-dialog",
      "@radix-ui/react-tooltip",
      "recharts",
    ],
  },
  
  // Désactiver la génération de source maps en production (plus rapide)
  productionBrowserSourceMaps: false,
  
  // Optimiser les images
  images: {
    unoptimized: true,
  },
};

export default withBundleAnalyzer(nextConfig);
