import fs from 'fs';
import path from 'path';

const filePath = path.resolve(__dirname, '../../docs/prompt-templates.json');

let templates: string[] = [];

function loadTemplates() {
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      templates = parsed.slice();
    } else {
      console.warn('prompt-templates.json does not contain an array');
      templates = [];
    }
  } catch (err: any) {
    const msg = err && err.message ? err.message : String(err);
    console.warn('Failed to load prompt-templates.json:', msg);
    templates = [];
  }
}

// initial load
loadTemplates();

// Watch file for changes and reload (simple cache invalidation for dev)
try {
  fs.watchFile(filePath, { interval: 1000 }, (curr, prev) => {
    if (curr.mtimeMs !== prev.mtimeMs) {
      console.log('prompt-templates.json changed; reloading templates');
      loadTemplates();
    }
  });
} catch (err) {
  // ignore watch errors on some environments
}

export function getTemplates() {
  return templates.slice();
}

export function reloadTemplates() {
  loadTemplates();
  return getTemplates();
}
