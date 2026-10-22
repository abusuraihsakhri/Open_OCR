export const MAX_FILES = 20;
export const MAX_BYTES = 25 * 1024 * 1024;
export const MAX_PAGES = 50;
const EXTENSIONS = new Set(["png", "jpg", "jpeg", "webp", "bmp", "pdf"]);
export function extension(name) { return String(name).split(".").pop().toLowerCase(); }
export function validateFiles(files, existing = []) {
  const selected = [...existing], errors = [];
  for (const file of files) {
    if (selected.length >= MAX_FILES) { errors.push("Maximum " + MAX_FILES + " files reached."); break; }
    if (!EXTENSIONS.has(extension(file.name))) { errors.push("Unsupported file: " + file.name); continue; }
    if (!file.size || file.size > MAX_BYTES) { errors.push("File must be between 1 byte and 25 MB: " + file.name); continue; }
    if (selected.some(other => other.name === file.name && other.size === file.size && other.lastModified === file.lastModified)) continue;
    selected.push(file);
  }
  return { selected, errors };
}
export function markdownFor(results) {
  return results.map(item => "## " + item.source + (item.page ? " — Page " + item.page : "") + "\n\n" + (item.text || "") + "\n").join("\n---\n\n");
}
export function jsonFor(results) { return JSON.stringify(results, null, 2); }
export function filenameSafe(name) { return String(name).replace(/[^a-z0-9_-]+/gi, "_").replace(/^_+|_+$/g, "").slice(0, 60) || "openocr"; }
