#!/usr/bin/env node
/**
 * Template Rollout Validator (Phase 3B)
 *
 * Structural integrity check only — never judges whether financial
 * numbers are correct. Numeric Consistency is checked separately by
 * hand per the existing Phase 3 rules (same-period conflicts vs
 * legitimate different-period figures need human judgment).
 *
 * Usage:
 *   node scripts/validate-template-rollout.js <prototype-file.html> [more files...]
 *   node scripts/validate-template-rollout.js articles/*-prototype-v1.html
 *
 * For each prototype file, finds its production counterpart by
 * stripping "-prototype-v1" from the filename, and checks:
 *   1. template CSS loaded      (etf-template-proto.css link present)
 *   2. GULICALC_PAGE_DATA        (window.GULICALC_PAGE_DATA present)
 *   3. Quick Answer               (.etf-proto-qa present)
 *   4. Progressive Input          (.etf-proto-primary + <details class="etf-proto-advanced")
 *   5. Personalized Result        (.etf-proto-result present)
 *   6. Next Intent                (.etf-proto-intent-grid present)
 *   7. canonical retained         (byte-identical <link rel="canonical"> vs production)
 *   8. title retained             (byte-identical <title> vs production)
 *   9. H1 retained                (byte-identical first <h1> vs production)
 *  10. prototype robots           (noindex, nofollow present)
 *
 * Exits 0 if all files PASS, 1 if any FAIL.
 */

const fs = require('fs');
const path = require('path');

const CHECKS = [
  { key: 'template_css', label: 'template CSS loaded' },
  { key: 'page_data', label: 'GULICALC_PAGE_DATA exists' },
  { key: 'quick_answer', label: 'Quick Answer exists' },
  { key: 'progressive_input', label: 'Progressive Input exists' },
  { key: 'personalized_result', label: 'Personalized Result exists' },
  { key: 'next_intent', label: 'Next Intent exists' },
  { key: 'canonical', label: 'canonical retained' },
  { key: 'title', label: 'title retained' },
  { key: 'h1', label: 'H1 retained' },
  { key: 'robots_noindex', label: 'prototype robots = noindex,nofollow' },
];

function extractTag(html, regex) {
  const m = html.match(regex);
  return m ? m[0] : null;
}

function findProductionCounterpart(protoPath) {
  const dir = path.dirname(protoPath);
  const base = path.basename(protoPath).replace(/-prototype-v1(\.html)$/, '$1');
  const candidate = path.join(dir, base);
  return fs.existsSync(candidate) ? candidate : null;
}

function validateFile(protoPath) {
  const result = { file: protoPath, checks: {}, notes: [] };

  if (!fs.existsSync(protoPath)) {
    result.fatal = `file not found: ${protoPath}`;
    return result;
  }
  const html = fs.readFileSync(protoPath, 'utf8');

  const prodPath = findProductionCounterpart(protoPath);
  if (!prodPath) {
    result.notes.push(`no production counterpart found (expected ${path.basename(protoPath).replace(/-prototype-v1/, '')}) — canonical/title/H1 checks will FAIL by default`);
  }
  const prodHtml = prodPath ? fs.readFileSync(prodPath, 'utf8') : null;

  // 1. template CSS loaded
  result.checks.template_css = /etf-template-proto\.css/.test(html);

  // 2. GULICALC_PAGE_DATA exists
  result.checks.page_data = /window\.GULICALC_PAGE_DATA\s*=/.test(html);

  // 3. Quick Answer
  result.checks.quick_answer = /class="etf-proto-qa"/.test(html);

  // 4. Progressive Input
  result.checks.progressive_input =
    /class="etf-proto-primary"/.test(html) &&
    /<details[^>]*class="etf-proto-advanced"/.test(html);

  // 5. Personalized Result
  result.checks.personalized_result = /class="etf-proto-result"/.test(html);

  // 6. Next Intent
  result.checks.next_intent = /class="etf-proto-intent-grid"/.test(html);

  // 7-9: compare against production (byte-identical)
  const protoCanonical = extractTag(html, /<link rel="canonical"[^>]*>/);
  const protoTitle = extractTag(html, /<title>[\s\S]*?<\/title>/);
  const protoH1 = extractTag(html, /<h1[^>]*>[\s\S]*?<\/h1>/);

  if (prodHtml) {
    const prodCanonical = extractTag(prodHtml, /<link rel="canonical"[^>]*>/);
    const prodTitle = extractTag(prodHtml, /<title>[\s\S]*?<\/title>/);
    const prodH1 = extractTag(prodHtml, /<h1[^>]*>[\s\S]*?<\/h1>/);

    result.checks.canonical = !!protoCanonical && protoCanonical === prodCanonical;
    result.checks.title = !!protoTitle && protoTitle === prodTitle;
    result.checks.h1 = !!protoH1 && protoH1 === prodH1;

    if (!result.checks.canonical) result.notes.push(`canonical mismatch:\n  prod:  ${prodCanonical}\n  proto: ${protoCanonical}`);
    if (!result.checks.title) result.notes.push(`title mismatch:\n  prod:  ${prodTitle}\n  proto: ${protoTitle}`);
    if (!result.checks.h1) result.notes.push(`H1 mismatch:\n  prod:  ${prodH1}\n  proto: ${protoH1}`);
  } else {
    result.checks.canonical = false;
    result.checks.title = false;
    result.checks.h1 = false;
  }

  // 10. prototype robots
  result.checks.robots_noindex = /<meta name="robots" content="noindex,\s*nofollow"/.test(html);

  return result;
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node scripts/validate-template-rollout.js <prototype-file.html> [more files...]');
    process.exit(2);
  }

  let allPass = true;
  const summary = [];

  for (const file of args) {
    const r = validateFile(file);
    if (r.fatal) {
      console.log(`\n=== ${file} ===`);
      console.log(`  FATAL: ${r.fatal}`);
      allPass = false;
      summary.push({ file, status: 'FATAL' });
      continue;
    }

    const failed = CHECKS.filter(c => !r.checks[c.key]);
    const status = failed.length === 0 ? 'PASS' : 'FAIL';
    if (status === 'FAIL') allPass = false;
    summary.push({ file, status, failedChecks: failed.map(c => c.label) });

    console.log(`\n=== ${file} — ${status} ===`);
    for (const c of CHECKS) {
      console.log(`  [${r.checks[c.key] ? 'x' : ' '}] ${c.label}`);
    }
    if (r.notes.length) {
      console.log('  notes:');
      r.notes.forEach(n => console.log('    ' + n.replace(/\n/g, '\n    ')));
    }
  }

  console.log('\n=== Summary ===');
  summary.forEach(s => {
    console.log(`${s.status.padEnd(6)} ${s.file}${s.failedChecks && s.failedChecks.length ? '  (' + s.failedChecks.join(', ') + ')' : ''}`);
  });

  process.exit(allPass ? 0 : 1);
}

main();
