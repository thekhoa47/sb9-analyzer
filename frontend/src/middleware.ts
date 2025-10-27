import { NextResponse, NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  const url = new URL("/api/auth/session", req.url);

  const res = await fetch(url, {
    headers: { cookie: req.headers.get("cookie") || "" },
  });

  if (res.ok) return NextResponse.next();

  const redirectUrl = req.nextUrl.clone();
  redirectUrl.pathname = "/login";
  redirectUrl.searchParams.set("next", req.nextUrl.pathname);
  return NextResponse.redirect(redirectUrl);
}

export const config = { matcher: ['/admin/:path*'] };
