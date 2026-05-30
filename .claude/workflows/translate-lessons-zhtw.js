export const meta = {
  name: 'translate-lessons-zhtw',
  description: 'Translate all remaining chapter lessons to Traditional Chinese (zh-TW) as <name>.zh.md',
  phases: [{ title: 'Translate', detail: 'one agent per untranslated .md -> writes .zh.md' }],
}

// Phase 1 scope: every *.md (not *.zh.md) under the numbered chapter dirs 00-17
// that does NOT already have a <name>.zh.md sibling. Idempotent: re-running skips done files.
// The full list (113 files as of 2026-05-30) is passed via `args`, OR recomputed by a
// scout agent if args is empty. Each item is a repo-relative path like
// "06-retrieval-systems/02-chunking-strategies.md".

const ROOT = '/Users/mcgradymac/claude_prjs/ai-system-design-guide'

function rules(path) {
  const zh = path.replace(/\.md$/i, '.zh.md')
  return `You are translating a technical Markdown document into Traditional Chinese (繁體中文, Taiwan / zh-TW) for an AI system design study site.

TASK:
1. Read the file: ${ROOT}/${path}
2. Produce a faithful Traditional Chinese translation and WRITE it (Write tool) to: ${ROOT}/${zh}
3. Reply with ONLY the output path and the line count.

TRANSLATION RULES:
- Natural, professional Traditional Chinese as used in Taiwan (zh-TW). Audience: senior software / AI engineers.
- Translate: all prose, headings, list items, table cell text, blockquotes, image alt text, and link DISPLAY text.
- DO NOT translate or alter:
  - Code blocks (\`\`\` ... \`\`\`) and inline \`code\`.
  - Mermaid blocks (\`\`\`mermaid ...\`\`\`): keep node IDs, arrows, syntax EXACTLY; when unsure leave the whole block unchanged.
  - URLs, link targets, relative file paths — keep EXACTLY; only link TEXT is translated; do NOT change \`.md\` to \`.zh.md\` in links.
  - Technical terms / product / model / library names / acronyms — keep in English (RAG, MCP, A2A, LoRA, KV cache, vLLM, embedding, transformer, token, prompt, fine-tuning, model names, framework names, etc.). Mixing English terms into Chinese sentences is expected.
  - Numbers, units, prices, dates, status tokens.
  - Markdown structure: heading levels, tables (every | column + separator rows), lists, horizontal rules (---) — preserve exactly.
- Preserve exact section order and structure. Do NOT summarize, omit, add, or reorder. One-to-one translation.
- Output ONLY the translated Markdown to the file — no preamble, no translator notes, no surrounding code fence.`
}

let files = Array.isArray(args) ? args : null
if (!files) {
  // Fallback: ask a scout to list untranslated files (medium thoroughness).
  const scout = await agent(
    `List, one per line, every *.md file (NOT *.zh.md) under the numbered chapter directories ` +
    `00-* through 17-* of ${ROOT} that does NOT already have a sibling <name>.zh.md. ` +
    `Output ONLY repo-relative paths, no commentary.`,
    { label: 'scout', phase: 'Translate', agentType: 'Explore' }
  )
  files = (scout || '').split('\n').map(s => s.trim()).filter(s => /\.md$/.test(s) && !/\.zh\.md$/.test(s))
}

log(`Translating ${files.length} lessons to zh-TW`)

const results = await parallel(files.map(path => () =>
  agent(rules(path), { label: 'zh:' + path, phase: 'Translate' })
    .then(r => ({ path, ok: true, r }))
    .catch(e => ({ path, ok: false, err: String(e) }))
))

const done = results.filter(r => r && r.ok).map(r => r.path)
const failed = results.filter(r => r && !r.ok).map(r => r.path)
log(`Done: ${done.length} translated, ${failed.length} failed`)
return { translated: done, failed }
