import { NextResponse, NextRequest } from 'next/server';
import { configs } from './configs/configs';

export async function middleware(req: NextRequest) {
  const url = new URL(`${configs.NEXT_PUBLIC_BACKEND_URL}/auth/session`, req.url);

  const res = await fetch(url, {
    headers: { cookie: req.headers.get('cookie') || '' },
    redirect: 'manual',
  });

  // your backend returns 204 if authenticated
  if (res.status === 200 || res.status === 204) {
    return NextResponse.next();
  }

  const redirectUrl = req.nextUrl.clone();
  redirectUrl.pathname = '/login';
  redirectUrl.searchParams.set('next', req.nextUrl.pathname);
  return NextResponse.redirect(redirectUrl);
}

export const config = {
  matcher: ['/admin/:path*'],
};