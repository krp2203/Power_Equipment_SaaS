import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://web:5000/api/:path*', // Proxy to Backend
      },
      {
        source: '/static/:path*',
        destination: 'http://web:5000/static/:path*', // Proxy Static Assets (Logos)
      },
      {
        source: '/admin/:path*',
        destination: 'http://web:5000/admin/:path*', // Proxy Admin Routes
      },
      {
        source: '/auth/:path*', // Also auth routes if not under admin
        destination: 'http://web:5000/auth/:path*',
      },
      {
        source: '/dashboard/:path*', // In case dashboard works this way
        destination: 'http://web:5000/dashboard/:path*',
      },
      { // Catch-all for other flask modules if they aren't prefixed with /api or /admin?
        // Actually, main routes like /login, /logout are under auth -> /auth
        // Dashboard is usually /marketing/dashboard -> /marketing
        source: '/marketing/:path*',
        destination: 'http://web:5000/marketing/:path*',
      },
      {
        source: '/super_admin/:path*',
        destination: 'http://web:5000/super_admin/:path*',
      },
      {
        source: '/settings/:path*',
        destination: 'http://web:5000/settings/:path*',
      },
      {
        source: '/dealers/:path*',
        destination: 'http://web:5000/dealers/:path*',
      },
      {
        source: '/cases/:path*',
        destination: 'http://web:5000/cases/:path*',
      },
      {
        source: '/service_bulletins/:path*',
        destination: 'http://web:5000/service_bulletins/:path*',
      }
    ];
  },
};

export default nextConfig;
