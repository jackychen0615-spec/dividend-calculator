#!/usr/bin/env node
// Phase 4F.1D — validates data/stocks.json's 32 fallback entries against each
// symbol's production GULICALC_PAGE_DATA (the canonical source of truth).
// Checks: price, dividend (== dividendAmount, cash-only), dividendYield (== yield),
// frequency (core term match, since stocks.json intentionally uses a compact label
// for the dropdown UI while the article page may carry a longer descriptive string),
// dividendYear (only asserted where the page exposes structured basis/year fields;
// pre-v2.1 pages without those fields are skipped rather than guessed at).

const fs = require('fs');
const path = require('path');

function extractPageData(html) {
  const m = html.match(/window\.GULICALC_PAGE_DATA\s*=\s*\{/);
  if (!m) return null;
  let start = m.index + m[0].length - 1;
  let depth = 0;
  for (let i = start; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}') {
      depth--;
      if (depth === 0) return html.slice(start, i + 1);
    }
  }
  return null;
}

function parseField(block, field, isStr) {
  const re = isStr
    ? new RegExp(field + ':\\s*"([^"]*)"')
    : new RegExp(field + ':\\s*([\\d.]+)');
  const m = block.match(re);
  return m ? m[1] : null;
}

function coreTerm(freq) {
  return (freq || '').replace(/[（(][^）)]*[）)]/g, '').trim();
}

function main() {
  const articlesDir = path.join(__dirname, '..', 'articles');
  const files = fs.readdirSync(articlesDir).filter(f => f.endsWith('.html') && !f.includes('prototype-v1'));

  const symbolMap = {};
  for (const f of files) {
    const html = fs.readFileSync(path.join(articlesDir, f), 'utf8');
    const block = extractPageData(html);
    if (!block) continue;
    const symbol = parseField(block, 'symbol', true);
    if (!symbol) continue;
    symbolMap[symbol] = {
      file: f,
      price: parseFloat(parseField(block, 'price')),
      dividend: parseFloat(parseField(block, 'dividendAmount') || parseField(block, 'annualDividend')),
      yield: parseFloat(parseField(block, 'yield')),
      frequency: parseField(block, 'frequency', true),
      basis: parseField(block, 'dividendBasis', true),
      earningsYear: parseField(block, 'earningsYear'),
      distributionYear: parseField(block, 'distributionYear'),
    };
  }

  const stocksPath = path.join(__dirname, '..', 'data', 'stocks.json');
  const d = JSON.parse(fs.readFileSync(stocksPath, 'utf8'));

  let allPass = true;
  const results = [];

  for (const s of d.stocks) {
    const canon = symbolMap[s.code];
    const issues = [];
    if (!canon) {
      issues.push('no matching production page found (no canonical to check against)');
    } else {
      if (Math.abs((s.price || 0) - canon.price) > 0.01) {
        issues.push(`price mismatch: stocks.json=${s.price} vs canonical=${canon.price}`);
      }
      if (Math.abs((s.dividend || 0) - canon.dividend) > 0.0005) {
        issues.push(`dividend mismatch: stocks.json=${s.dividend} vs canonical dividendAmount=${canon.dividend}`);
      }
      if (s.dividendYield == null || Math.abs(s.dividendYield - canon.yield) > 0.01) {
        issues.push(`dividendYield mismatch: stocks.json=${s.dividendYield} vs canonical yield=${canon.yield}`);
      }
      const sFreqCore = coreTerm(s.frequency);
      const cFreqCore = coreTerm(canon.frequency);
      if (sFreqCore && cFreqCore && sFreqCore !== cFreqCore && cFreqCore.indexOf(sFreqCore) === -1) {
        issues.push(`frequency core term mismatch: stocks.json="${s.frequency}" vs canonical="${canon.frequency}"`);
      }
      if (canon.basis === 'TTM' && s.dividendYear !== '近12個月') {
        issues.push(`TTM page dividendYear should be "近12個月", got "${s.dividendYear}"`);
      }
    }
    if (issues.length) allPass = false;
    results.push({ code: s.code, pass: issues.length === 0, issues });
  }

  console.log(`Checked ${results.length} stocks.json entries against production canonical data.\n`);
  for (const r of results) {
    console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.code}` + (r.issues.length ? `  — ${r.issues.join(' | ')}` : ''));
  }
  console.log(`\n=== Summary: ${results.filter(r => r.pass).length}/${results.length} PASS ===`);
  process.exit(allPass ? 0 : 1);
}

main();
