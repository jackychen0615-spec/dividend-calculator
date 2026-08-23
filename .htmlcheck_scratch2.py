import re, glob

files = sorted(glob.glob("articles/*.html") + glob.glob("*.html"))

heading_re = re.compile(r'<h([234])[^>]*>(.*?)</h\1>', re.S)
tag_strip = re.compile(r'<[^>]+>')
content_block_re = re.compile(r'<(p|ul|ol|table)[^>]*>.*?</\1>', re.S)

results = []

SKIP_EXACT = {"你覺得這個工具如何？"}

for f in files:
    content = open(f, encoding='utf-8').read()
    headings = list(heading_re.finditer(content))
    for i, m in enumerate(headings):
        qtext = tag_strip.sub('', m.group(2)).strip()
        if not (qtext.endswith('?') or qtext.endswith('？')):
            continue
        if qtext in SKIP_EXACT:
            continue
        start = m.end()
        end = headings[i+1].start() if i+1 < len(headings) else len(content)
        segment = content[start:end]
        full_blocks = content_block_re.finditer(segment)
        combined_text = ""
        for b in full_blocks:
            btext = tag_strip.sub(' ', b.group(0)).strip()
            combined_text += " " + btext
        combined_text = re.sub(r'\s+', ' ', combined_text).strip()

        flag = None
        if len(combined_text) < 10:
            flag = "empty-or-near-empty"
        elif len(combined_text) < 40 and ("參考" in combined_text or "詳見" in combined_text):
            flag = "redirect-only-short"
        results.append((f, qtext, combined_text[:70], flag, len(combined_text)))

flagged = [r for r in results if r[3]]
print("total question headings:", len(results))
print("flagged:", len(flagged))
files_flagged = sorted(set(r[0] for r in flagged))
print("distinct files flagged:", len(files_flagged))
print()
for r in flagged:
    print(r)
