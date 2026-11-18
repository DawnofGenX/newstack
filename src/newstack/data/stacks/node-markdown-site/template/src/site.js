import fs from 'node:fs';
import path from 'node:path';
import matter from 'gray-matter';
import { marked } from 'marked';

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

marked.use({
  renderer: {
    html(token) {
      return escapeHtml(token.text || token.raw || '');
    },
  },
});

function layout(title, body) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
</head>
<body>
<h1>${title}</h1>
<main>${body}</main>
</body>
</html>
`;
}

export function buildSite(inputDir, outputDir) {
  fs.mkdirSync(outputDir, { recursive: true });
  const files = fs.readdirSync(inputDir).filter((file) => file.endsWith('.md')).sort();
  for (const file of files) {
    const raw = fs.readFileSync(path.join(inputDir, file), 'utf8');
    const { data, content } = matter(raw);
    const title = escapeHtml(data.title || path.basename(file, '.md'));
    const body = marked.parse(content);
    const slug = `${data.slug || path.basename(file, '.md')}.html`;
    fs.writeFileSync(path.join(outputDir, slug), layout(title, body));
  }
  return files.length;
}