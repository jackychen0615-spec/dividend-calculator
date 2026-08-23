import re, glob

files = sorted(glob.glob("articles/*.html") + glob.glob("*.html"))

# match each article-faq-item div (assume no nested divs inside, verified pattern is simple)
div_re = re.compile(r'<div class="article-faq-item">(.*?)</div>', re.S)
h3_re = re.compile(r'<h3[^>]*>(.*?)</h3>', re.S)
p_re = re.compile(r'<p[^>]*>(.*?)</p>', re.S)
tag_strip = re.compile(r'<[^>]+>')

total = 0
no_h3 = 0
no_p = 0
short_p = 0
title_files = {}

for f in files:
    content = open(f, encoding='utf-8').read()
    for dm in div_re.finditer(content):
        block = dm.group(1)
        total += 1
        hm = h3_re.search(block)
        pm = p_re.search(block)
        if not hm:
            no_h3 += 1
            continue
        qtext = tag_strip.sub('', hm.group(1)).strip()
        if not pm:
            no_p += 1
            print("NO-P:", f, qtext)
            continue
        atext = tag_strip.sub(' ', pm.group(1)).strip()
        atext = re.sub(r'\s+', ' ', atext)
        if len(atext) < 15:
            short_p += 1
            print("SHORT:", f, qtext, "->", atext)

print()
print("total article-faq-item divs:", total)
print("no_h3:", no_h3, "no_p:", no_p, "short_p:", short_p)
