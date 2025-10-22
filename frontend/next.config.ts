import type { NextConfig } from "next";
import { configs } from "@/configs/configs";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    domains: ["pub-e4b54b6deac64819962f5e7bb6e3a147.r2.dev"],
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${configs.NEXT_PUBLIC_BACKEND_URL}/:path*` },
    ];
  },
};

export default nextConfig;
