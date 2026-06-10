import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = [
  '/login',
  '/api/auth/login',
  '/api/auth/logout',
  '/_next',
  '/favicon.ico',
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow public paths without auth
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  const session = request.cookies.get('session')?.value

  if (!session) {
    const loginUrl = new URL('/login', request.url)
    // Preserve intended destination for post-login redirect (optional)
    loginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
