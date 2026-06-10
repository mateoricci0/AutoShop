import { NextRequest, NextResponse } from 'next/server'

const SERVICE_MAP: Record<string, string> = {
  auth: process.env.AUTH_SERVICE_URL ?? 'http://auth:8001',
  hunter: process.env.HUNTER_SERVICE_URL ?? 'http://product-hunter:8002',
  marketing: process.env.MARKETING_SERVICE_URL ?? 'http://marketing:8003',
  images: process.env.IMAGES_SERVICE_URL ?? 'http://image-pipeline:8004',
  publisher: process.env.PUBLISHER_SERVICE_URL ?? 'http://shopify-publisher:8005',
  analytics: process.env.ANALYTICS_SERVICE_URL ?? 'http://analytics:8006',
  notifications: process.env.NOTIFICATIONS_SERVICE_URL ?? 'http://notifications:8007',
}

const PUBLIC_PATHS = ['/auth/login', '/auth/logout']

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  return handleProxy(req, await params)
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  return handleProxy(req, await params)
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  return handleProxy(req, await params)
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  return handleProxy(req, await params)
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  return handleProxy(req, await params)
}

async function handleProxy(
  req: NextRequest,
  params: { proxy: string[] }
) {
  const [service, ...rest] = params.proxy

  if (!service) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  const targetBase = SERVICE_MAP[service]
  if (!targetBase) {
    return NextResponse.json({ error: 'Unknown service' }, { status: 404 })
  }

  const path = '/' + rest.join('/')
  const isPublic = PUBLIC_PATHS.some((p) => path.startsWith(p))

  const session = req.cookies.get('session')?.value

  if (!isPublic && !session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const url = `${targetBase}${path}${req.nextUrl.search}`

  const headers = new Headers()
  req.headers.forEach((value, key) => {
    // Skip hop-by-hop headers
    if (!['host', 'connection', 'keep-alive', 'transfer-encoding', 'te', 'trailers', 'upgrade'].includes(key.toLowerCase())) {
      headers.set(key, value)
    }
  })

  if (session) {
    headers.set('x-session-token', session)
  }

  const hasBody = !['GET', 'HEAD'].includes(req.method)
  const body = hasBody ? req.body : undefined

  try {
    const response = await fetch(url, {
      method: req.method,
      headers,
      body,
      // @ts-expect-error - duplex needed for streaming body forwarding
      duplex: 'half',
    })

    const resHeaders = new Headers()
    response.headers.forEach((value, key) => {
      // Forward set-cookie headers from backend (e.g., session cookie on login)
      if (key.toLowerCase() === 'set-cookie') {
        resHeaders.append(key, value)
      } else {
        resHeaders.set(key, value)
      }
    })

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: resHeaders,
    })
  } catch (err) {
    console.error(`[proxy] Error proxying to ${url}:`, err)
    return NextResponse.json(
      { error: 'Service unavailable', service },
      { status: 503 }
    )
  }
}
