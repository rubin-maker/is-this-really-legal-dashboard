import { createReadStream, existsSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join } from "node:path";

const root = new URL(".", import.meta.url).pathname;
const port = Number(process.env.PORT || 3000);
const routes = new Map([
  ["/", "index.html"],
  ["/index.html", "index.html"],
  ["/dashboard.html", "dashboard.html"],
  ["/artifact.json", "artifact.json"],
]);
const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

createServer((request, response) => {
  const pathname = new URL(request.url || "/", "http://localhost").pathname;
  if (pathname === "/health") {
    response.writeHead(200, {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    });
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }

  const file = routes.get(pathname);
  if (!file) {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found\n");
    return;
  }

  const path = join(root, file);
  if (!existsSync(path)) {
    response.writeHead(503, { "content-type": "text/plain; charset=utf-8" });
    response.end("Dashboard has not been built yet.\n");
    return;
  }

  response.writeHead(200, {
    "content-type": contentTypes[extname(path)] || "application/octet-stream",
    "cache-control": file.endsWith(".html") ? "no-cache" : "public, max-age=3600",
    "content-security-policy": "default-src 'self' 'unsafe-inline' data: blob:; connect-src 'none'; frame-ancestors 'none'",
    "referrer-policy": "strict-origin-when-cross-origin",
    "x-content-type-options": "nosniff",
  });
  createReadStream(path).pipe(response);
}).listen(port, "0.0.0.0", () => {
  console.log(`Is This Really Legal dashboard listening on port ${port}`);
});
