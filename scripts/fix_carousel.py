#!/usr/bin/env python3
import re, os

base = '/Users/jackychen/Desktop/gulicalc-local'
pages = ['compare','compound-calculator','mortgage-calculator','goal',
         'dca-calculator','payback-calculator','tax-calculator']

# 從 index.html 提取個股比較的 <img> 標籤（含 onerror fallback），避免手打轉義
idx = open(f'{base}/index.html', encoding='utf-8').read()
m = re.search(r'<img src="images/icon-compare\.png".*?>', idx)
IMG = m.group(0)

# 要被替換掉的 VS 文字方塊（個股比較）
VS_SPAN = ('<span style="display:flex;align-items:center;justify-content:center;'
           'width:44px;height:44px;border-radius:10px;background:#eef2ff;'
           'margin:0 auto .6rem;font-size:1.2rem;color:#4f46e5;font-weight:700;">VS</span>')

# 輪播結尾的錨點 style（每頁唯一）
ANCHOR = ('<style>.tool-carousel-sub::-webkit-scrollbar{display:none}'
          '@media(max-width:640px){.tool-carousel-sub{justify-content:flex-start!important;}}</style>')

# 要插入的箭頭控制區 + 拖曳腳本（scrollBy/拖曳都綁定 .tool-carousel-sub）
NAV = ANCHOR + '''
      <div class="carousel-nav" style="display:none;justify-content:center;align-items:center;gap:.8rem;margin-top:.5rem;">
        <button onclick="document.querySelector('.tool-carousel-sub').scrollBy({left:-160,behavior:'smooth'})" style="width:32px;height:32px;border-radius:50%;border:1px solid #e5e7eb;background:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;box-shadow:0 1px 3px rgba(0,0,0,.06);" onmouseover="this.style.borderColor='#0891b2';this.style.color='#0891b2'" onmouseout="this.style.borderColor='#e5e7eb';this.style.color=''" aria-label="上一個">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <span style="font-size:.7rem;color:#9ca3af;user-select:none;">9 個工具</span>
        <button onclick="document.querySelector('.tool-carousel-sub').scrollBy({left:160,behavior:'smooth'})" style="width:32px;height:32px;border-radius:50%;border:1px solid #e5e7eb;background:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;box-shadow:0 1px 3px rgba(0,0,0,.06);" onmouseover="this.style.borderColor='#0891b2';this.style.color='#0891b2'" onmouseout="this.style.borderColor='#e5e7eb';this.style.color=''" aria-label="下一個">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
        </button>
      </div>
      <style>@media(min-width:641px){.carousel-nav{display:flex!important}}@media(max-width:640px){.carousel-nav{display:none!important}}</style>
      <script>(function(){var el=document.querySelector('.tool-carousel-sub');if(!el)return;var down=false,sx,sl;el.addEventListener('mousedown',function(e){down=true;el.classList.add('dragging');sx=e.pageX-el.offsetLeft;sl=el.scrollLeft});el.addEventListener('mouseleave',function(){down=false});el.addEventListener('mouseup',function(){down=false});el.addEventListener('mousemove',function(e){if(!down)return;e.preventDefault();el.scrollLeft=sl-(e.pageX-el.offsetLeft-sx)})})();</script>'''

for p in pages:
    fp = f'{base}/{p}.html'
    s = open(fp, encoding='utf-8').read()
    vs = s.count(VS_SPAN)
    anc = s.count(ANCHOR)
    nav_exists = 'carousel-nav' in s
    s = s.replace(VS_SPAN, IMG)              # VS → 圖片
    if not nav_exists:
        s = s.replace(ANCHOR, NAV, 1)        # 插入箭頭區
    open(fp, 'w', encoding='utf-8').write(s)
    print(f'{p:24} VS→img:{vs}  錨點:{anc}  箭頭:{"已存在略過" if nav_exists else "已加入"}')
