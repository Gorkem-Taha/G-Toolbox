// Copies the pinned Font Awesome Free build from node_modules into static/vendor
// so the app works offline. Only woff2 fonts are shipped (supported everywhere).
import { cpSync, mkdirSync, readdirSync, rmSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const src = "node_modules/@fortawesome/fontawesome-free";
const dst = "static/vendor/fontawesome";
rmSync(dst, { recursive: true, force: true });
mkdirSync(join(dst, "css"), { recursive: true });
mkdirSync(join(dst, "webfonts"), { recursive: true });
cpSync(join(src, "css/all.min.css"), join(dst, "css/all.min.css"));
cpSync(join(src, "LICENSE.txt"), join(dst, "LICENSE.txt"));
for (const f of readdirSync(join(src, "webfonts"))) {
  if (f.endsWith(".woff2")) cpSync(join(src, "webfonts", f), join(dst, "webfonts", f));
}
// Drop the .ttf fallbacks from the stylesheet since they are not shipped.
const cssPath = join(dst, "css/all.min.css");
const css = readFileSync(cssPath, "utf8").replace(/,url\(\.\.\/webfonts\/[^)]+\.ttf\) format\("truetype"\)/g, "");
writeFileSync(cssPath, css);
console.log("Font Awesome copied to", dst);
