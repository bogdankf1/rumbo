import type { NextConfig } from "next";

// API calls are proxied by the route handler in app/api/[...path]/route.ts,
// which streams and has no rewrite-proxy timeout.
const nextConfig: NextConfig = {};

export default nextConfig;
