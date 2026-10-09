// The API's Worker (docs/deploy.md#responses). It runs before the files in dist/
// (run_worker_first), because Cloudflare answers any method on a file's path with the file
// layer, which gives a CORS preflight a 405. It answers preflights and the base URL itself, and
// passes every other GET and HEAD to the files, served with the headers of public/_headers.
// Every response allows any origin, like the files.
const CORS = { 'Access-Control-Allow-Origin': '*' };
const CACHE = 'public, max-age=3600, stale-while-revalidate=86400';
const METHODS = 'GET, HEAD, OPTIONS';

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    // A CORS preflight, which a browser sends before a request with headers of its own
    if (request.method === 'OPTIONS') {
      const headers = { ...CORS, 'Access-Control-Allow-Methods': METHODS, 'Access-Control-Max-Age': '86400' };
      const asked = request.headers.get('Access-Control-Request-Headers');
      if (asked) {
        headers['Access-Control-Allow-Headers'] = asked;
        headers['Vary'] = 'Access-Control-Request-Headers';
      }
      return new Response(null, { status: 204, headers });
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return new Response(null, { status: 405, headers: { ...CORS, Allow: METHODS } });
    }
    // The base URL that index.json gives, /v1/, leads to index.json
    if (pathname === '/v1' || pathname === '/v1/') {
      return new Response(null, { status: 302, headers: { ...CORS, Location: '/v1/index.json', 'Cache-Control': CACHE } });
    }
    const response = await env.ASSETS.fetch(request);
    if (response.status !== 404) {
      return response;
    }
    // A file that doesn't exist, such as a commune code: a 404 with an empty body
    return new Response(null, {
      status: 404,
      headers: { ...CORS, 'Cache-Control': CACHE, 'X-Content-Type-Options': 'nosniff' },
    });
  },
};
