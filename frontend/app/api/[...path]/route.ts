import type { NextRequest } from "next/server";

// Runtime proxy to the FastAPI backend. A route handler instead of a
// next.config rewrite for two reasons: the rewrite proxy enforces a ~30s
// timeout (real-document extraction takes longer) and buffers SSE, which
// broke chat streaming. This passes bodies through untouched in both
// directions and reads BACKEND_URL at runtime.
const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

async function proxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const url = `${BACKEND}/api/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const resp = await fetch(url, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
    // @ts-expect-error Node fetch requires duplex for streamed request bodies
    duplex: "half",
    cache: "no-store",
  });

  const out = new Headers();
  const respType = resp.headers.get("content-type");
  if (respType) out.set("content-type", respType);
  out.set("cache-control", "no-cache");
  return new Response(resp.body, { status: resp.status, headers: out });
}

export { proxy as GET, proxy as POST, proxy as DELETE };
