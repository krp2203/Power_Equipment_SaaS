import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';

  // Extract the base domain (pes.bentcrankshaft.com)
  const isMainDomain = hostname === 'pes.bentcrankshaft.com' ||
    hostname === 'localhost:3005' ||
    hostname === 'localhost:3000';

  const isSubdomain = hostname.includes('.pes.bentcrankshaft.com') &&
    hostname !== 'pes.bentcrankshaft.com';

  const pathname = request.nextUrl.pathname;
  const isImpersonating = request.cookies.get('is_impersonating')?.value === 'true';

  // Check if organization is active for dealer sites (not API routes or admin)
  if (isSubdomain && !pathname.startsWith('/api') && !pathname.startsWith('/_next') && !pathname.startsWith('/admin')) {
    // Skip check for static assets (images, CSS, JS, etc.)
    const isStaticAsset = /\.(png|jpg|jpeg|gif|svg|ico|css|js|woff|woff2|ttf|eot)$/i.test(pathname);

    if (isStaticAsset) {
      return NextResponse.next();
    }

    // Skip check if super admin is impersonating
    if (!isImpersonating) {
      try {
        // Call backend API to get site info
        const apiUrl = `${request.nextUrl.protocol}//${hostname}/api/v1/site-info`;
        const response = await fetch(apiUrl, {
          headers: {
            'Host': hostname,
          },
          cache: 'no-store',
        });

        if (response.ok) {
          const data = await response.json();

          // If organization is inactive, show suspension page
          if (data.is_active === false) {
            // Rewrite to a suspension page
            return new NextResponse(
              `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temporarily Unavailable</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;
        }
        .container {
            background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px; width: 100%; padding: 60px 40px; text-align: center;
        }
        .icon {
            width: 400px; max-width: 90%; margin: 0 auto 30px;
            background: white;
            border-radius: 8px; display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); padding: 30px;
        }
        .icon img { max-width: 100%; max-height: 100%; object-fit: contain; }
        h1 { color: #2d3748; font-size: 32px; margin-bottom: 16px; font-weight: 700; }
        .subtitle { color: #718096; font-size: 18px; margin-bottom: 40px; line-height: 1.6; }
        .info-box {
            background: #ffffff; border-left: 4px solid #3182ce; padding: 20px;
            margin: 30px 0; text-align: left; border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        .info-box h3 { color: #2d3748; font-size: 16px; margin-bottom: 12px; font-weight: 600; }
        .contact-item { display: flex; align-items: center; margin: 12px 0; color: #4a5568; }
        .contact-item a { color: #3182ce; text-decoration: none; font-weight: 500; margin-left: 8px; }
        .contact-item a:hover { text-decoration: underline; }
        .footer {
            margin-top: 40px; padding-top: 30px; border-top: 1px solid #e2e8f0;
            color: #a0aec0; font-size: 14px;
        }
        @media (max-width: 600px) {
            .container { padding: 40px 24px; }
            h1 { font-size: 24px; }
            .subtitle { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            <img src="/bentcrankshaft_logo.png" alt="Bent Crankshaft">
        </div>
        <h1>Temporarily Unavailable</h1>
        <p class="subtitle">
            This site is temporarily down for maintenance. 
            We apologize for any inconvenience. Please check back soon.
        </p>
        <div class="info-box">
            <h3>Site Owner Contact</h3>
            <div class="contact-item">
                📧 Email:<a href="mailto:support@bentcrankshaft.com">support@bentcrankshaft.com</a>
            </div>
            <div class="contact-item">
                🌐 Visit:<a href="https://bentcrankshaft.com" target="_blank">bentcrankshaft.com</a>
            </div>
        </div>
        <div class="footer">
            Power Equipment SaaS Platform<br>
            Powered by Bent Crankshaft Solutions
        </div>
    </div>
</body>
</html>`,
              {
                status: 503,
                headers: {
                  'Content-Type': 'text/html',
                  'Retry-After': '3600',
                },
              }
            );
          }
        }
      } catch (error) {
        // If API call fails, allow the request to proceed
        console.error('Failed to check organization status:', error);
      }
    }
  }

  // Add header for admin routes
  if (pathname.startsWith('/admin')) {
    const response = NextResponse.next();
    response.headers.set('x-is-admin-route', 'true');
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
