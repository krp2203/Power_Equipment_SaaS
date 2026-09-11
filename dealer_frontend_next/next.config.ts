import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Flask's blueprints require the trailing slash on their root routes
  // (e.g. /admin/pos/, /admin/equipment/) and redirect to add it back if
  // missing. Next.js's own default (trailingSlash: false) strips it before
  // the rewrite below ever proxies the request, which fights Flask's
  // redirect forever. Matching Flask's convention here breaks that loop.
  trailingSlash: true,
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
      // Exact-match rules for the four POS-epic blueprint roots, which Flask
      // requires to end in a trailing slash. Must come before the /admin/:path*
      // wildcard below: that pattern's :path* capture drops trailing slashes when
      // building the destination, so Flask always sees the no-slash form, issues
      // its own redirect to add it back, and the client's retry hits the same
      // lossy rewrite again - an infinite loop. An exact string match has no
      // capture group to lose the slash from.
      {
        source: '/admin/pos/',
        destination: 'http://web:5000/admin/pos/',
      },
      {
        source: '/admin/service-tickets/',
        destination: 'http://web:5000/admin/service-tickets/',
      },
      {
        source: '/admin/equipment/',
        destination: 'http://web:5000/admin/equipment/',
      },
      {
        source: '/admin/purchasing/',
        destination: 'http://web:5000/admin/purchasing/',
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
