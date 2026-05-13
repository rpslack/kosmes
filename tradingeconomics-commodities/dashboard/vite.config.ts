import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const csvSource = path.join(__dirname, "..", "data", "commodities_hourly.csv");

function serveCommodityCsv(): import("vite").Plugin {
  return {
    name: "serve-commodity-csv",
    configureServer(server) {
      server.middlewares.use("/commodities_hourly.csv", (_req, res, next) => {
        try {
          if (!fs.existsSync(csvSource)) {
            res.statusCode = 404;
            res.setHeader("Content-Type", "text/plain; charset=utf-8");
            res.end("Missing ../data/commodities_hourly.csv — run save_commodities.py first.");
            return;
          }
          res.setHeader("Content-Type", "text/csv; charset=utf-8");
          res.setHeader("Cache-Control", "no-store");
          fs.createReadStream(csvSource).pipe(res);
        } catch (e) {
          next(e as Error);
        }
      });
    },
    writeBundle() {
      const out = path.join(__dirname, "dist", "commodities_hourly.csv");
      if (fs.existsSync(csvSource)) {
        fs.mkdirSync(path.dirname(out), { recursive: true });
        fs.copyFileSync(csvSource, out);
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), serveCommodityCsv()],
  server: { port: 5174 },
});
