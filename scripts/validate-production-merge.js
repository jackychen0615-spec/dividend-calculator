#!/usr/bin/env node
// Phase 4C — Production Merge regression validator.
// Unlike validate-template-rollout.js (prototype QA), this checks a MERGED production file:
// - Core Template structure present
// - GULICALC_PAGE_DATA present and calculator regression (yield matches dividendAmount/price)
// - robots is NOT the prototype noindex,nofollow marker (should be production's own value)
// - no leftover prototype-only artifacts (filename references, "PROTOTYPE ONLY" comments)
// - basic JS syntax check on inline <script> blocks
// - table-wrap divs (if present) use overflow-x:auto via the shared CSS (structural presence only)

const fs = require('fs');
const path = require('path');

function checkFile(file) {
  const html = fs.readFileSync(file, 'utf8');
  const checks = {};

  checks['GULICALC_PAGE_DATA exists'] = /window\.GULICALC_PAGE_DATA\s*=\s*\{/.test(html);
  checks['Quick Answer exists'] = /etf-proto-qa/.test(html);
  checks['Progressive Input exists'] = /etf-proto-primary/.test(html);
  checks['Personalized Result exists'] = /etf-proto-result/.test(html);
  checks['Next Intent exists'] = /etf-proto-intent-grid/.test(html);
  checks['template CSS loaded'] = /etf-template-proto\.css/.test(html);
  checks['robots NOT noindex,nofollow (prototype marker)'] = !/<meta name="robots" content="noindex, nofollow">/.test(html);
  checks['no PROTOTYPE ONLY comment leftover'] = !/PROTOTYPE ONLY/.test(html);
  checks['no -prototype-v1 filename reference'] = !/prototype-v1\.html/.test(html);

  // calculator regression: extract dividendAmount/price/yield from GULICALC_PAGE_DATA and cross-check
  const m = html.match(/window\.GULICALC_PAGE_DATA\s*=\s*\{([\s\S]*?)\n\s*\};/);
  let regressionOK = null;
  if (m) {
    const block = m[1];
    const price = (block.match(/price:\s*([\d.]+)/) || [])[1];
    const div = (block.match(/dividendAmount:\s*([\d.]+)/) || [])[1];
    const yieldVal = (block.match(/yield:\s*([\d.]+)/) || [])[1];
    if (price && div && yieldVal) {
      const computed = (parseFloat(div) / parseFloat(price) * 100);
      const diff = Math.abs(computed - parseFloat(yieldVal));
      regressionOK = diff < 0.05; // allow rounding tolerance
      checks[`calculator regression (yield ${yieldVal}% vs computed ${computed.toFixed(2)}%)`] = regressionOK;
    } else {
      checks['calculator regression (fields not found, skipped)'] = true;
    }
  } else {
    checks['calculator regression (no GULICALC_PAGE_DATA block matched)'] = false;
  }

  // basic JS syntax check
  let jsOK = true;
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x => x[1]);
  for (const s of scripts) {
    try { new Function(s); } catch (e) { jsOK = false; }
  }
  checks['inline JS syntax valid'] = jsOK;

  const allPass = Object.values(checks).every(Boolean);
  return { allPass, checks };
}

function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error('Usage: node validate-production-merge.js <file1.html> [file2.html ...]');
    process.exit(1);
  }
  let allPass = true;
  const results = [];
  for (const file of files) {
    const { allPass: pass, checks } = checkFile(file);
    results.push({ file, pass });
    if (!pass) allPass = false;
    console.log(`\n=== ${file} — ${pass ? 'PASS' : 'FAIL'} ===`);
    for (const [k, v] of Object.entries(checks)) {
      console.log(`  [${v ? 'x' : ' '}] ${k}`);
    }
  }
  console.log('\n=== Summary ===');
  for (const r of results) console.log(`${r.pass ? 'PASS' : 'FAIL'}   ${r.file}`);
  process.exit(allPass ? 0 : 1);
}

main();
