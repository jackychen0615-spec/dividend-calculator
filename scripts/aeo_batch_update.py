#!/usr/bin/env python3
"""
AEO 批次優化腳本
1. 在 18 篇缺「直接回答」的文章加上 <strong> 開頭句
2. 在 41 篇只有 3 題 FAQ 的文章加第 4 題（JSON-LD + HTML）
"""
import re, os, sys

ARTICLES = "/Users/jackychen/Desktop/gulicalc-local/articles"

# ─── Part 1：直接回答 ────────────────────────────────────────────────
# 不處理自動生成的週/月報
DIRECT_ANSWERS = {
    "deposit-vs-etf-comparison.html":
        "把 100 萬分放定存與高股息 ETF 一年，ETF 多賺 37,000 元，是定存收益的 3.5 倍。",
    "dividend-yield-explained.html":
        "殖利率 = 每股配息 ÷ 股價 × 100%；股價 50 元、配息 3 元，殖利率就是 6%。",
    "emergency-fund-guide.html":
        "緊急備用金建議存 3～6 個月生活費，優先放高利活儲，不能投入股市等高風險資產。",
    "etf-recommendations-2026.html":
        "2026 年新手存股首選 0056 或 00878，殖利率約 5～7%，季配息穩定，適合長期持有。",
    "futures-vs-stock-saving.html":
        "期貨槓桿高、損失可超過本金；存股靠股利複利累積，兩者風險天差地別，存股族建議遠離期貨。",
    "high-yield-stock-trap.html":
        "殖利率越高不一定越好：股價下跌也會讓數字變高，選股前必須搭配財報確認配息是否可持續。",
    "how-to-buy-stocks-for-saving.html":
        "存股開戶只需身分證與健保卡，透過網路申辦最快 1 天完成，買 1 股即可開始存股。",
    "how-to-calculate-dividend.html":
        "股利計算公式：每股配息 × 持有股數；持有 1 張（1,000 股）、配息 3 元，可領 3,000 元。",
    "how-to-check-dividend-yield.html":
        "殖利率可在 Goodinfo 或證交所官網查詢，也可直接用股利計算器輸入股價與配息自動試算。",
    "income-tax-filing-guide.html":
        "股利所得可選合併計稅或分離計稅（28%），年收入偏低者通常合併計稅更省，可試算後再決定。",
    "labor-pension-self-contribution.html":
        "勞工每月自提退休金最高 6%，享稅前扣除優惠，長期投報率優於銀行定存。",
    "mortgage-guide-2026.html":
        "2026 年房貸利率約 2.1～2.5%，購屋前應先試算每月還款金額，確認不超過月收入 30～40%。",
    "salary-take-home-calculator.html":
        "月薪 5 萬元實領約 43,500 元，主要扣項為勞保（約 900 元）、健保（約 776 元）與勞退自提。",
    "stock-saving-recommendations-2026.html":
        "2026 年推薦 0056、00878、00919 追求高現金流；中華電（2412）、兆豐金（2886）最穩健。",
    "taiwan-stock-crash-june-2026.html":
        "台股大跌是短期恐慌，存股族持有高股息 ETF 無需賣出，等待填息、繼續領息即可。",
    "top-etf-dividend-yield-2026.html":
        "2026 年殖利率最高的是 00919（約 8%），最穩定的是 0056，兼顧 ESG 與配息選 00878。",
    "tsmc-revenue-record-2026.html":
        "台積電 5 月營收 4,169 億元刷新歷史紀錄，股價突破 1,000 元後存股族更需精算買入殖利率。",
    "xin-qing-an-loan-guide.html":
        "信用貸款無需抵押，年利率約 3～8%，適合短期周轉，但利率遠高於房貸，務必謹慎評估。",
}

# ─── Part 2：第 4 題 FAQ ──────────────────────────────────────────────
FOURTH_FAQ = {
    # ETF 單篇
    "0050-dividend-calculator.html": (
        "0050 的配息穩定嗎？有在成長嗎？",
        "0050 配息金額每年不固定，取決於成分股的整體獲利與市場狀況。近年配息呈成長趨勢，但非保證。0050 的投資價值更多在於長期資本增值，建議搭配<a href='/'>股利計算器</a>評估你的買入殖利率是否合理。"
    ),
    "006208-dividend-calculator.html": (
        "006208 和 0050 長期報酬差很多嗎？",
        "差異非常小。006208 與 0050 都追蹤「臺灣 50 指數」，成分股完全相同，長期報酬幾乎一致。主要差別是 006208 單價較低、經理費略低（0.12% vs 0.15%），若長期定額存市值型 ETF，006208 是省費的好選擇。"
    ),
    "00900-dividend-calculator.html": (
        "00900 的配息穩定嗎？適合存股嗎？",
        "00900（富邦特選高股息 30 ETF）採季配息，但每季配息金額可能波動。適合想要高現金流的投資人，但成立時間相對較短，建議查看近三年配息紀錄，再用<a href='/'>股利計算器</a>試算實際殖利率後再決定。"
    ),
    "00915-dividend-calculator.html": (
        "00915 的配息穩定嗎？適合存股嗎？",
        "00915（凱基優選高股息 30 ETF）採季配息，殖利率相對較高。建議查看近幾季的實際配息紀錄，並用<a href='/'>股利計算器</a>輸入你的買入成本確認合理殖利率，再做存股決定。"
    ),
    "00918-dividend-calculator.html": (
        "00918 的配息穩定嗎？適合存股嗎？",
        "00918（大華優利高填息 30 ETF）採季配息，注重填息表現。填息率高代表除息後股價較快回補，對存股族有利。建議搭配<a href='/'>股利計算器</a>計算你的實際殖利率，並關注近三季配息趨勢。"
    ),
    "00919-dividend-calculator.html": (
        "00919 成立時間短，配息能維持這麼高嗎？",
        "00919（群益台灣精選高息 ETF）成立於 2022 年，殖利率高達 7～9%，但成立時間較短，尚未經歷完整股災考驗。配息能否維持取決於每季選股結果，投資前建議查看最新持股內容，並用<a href='/'>股利計算器</a>評估。"
    ),
    "00927-dividend-calculator.html": (
        "00927 和其他高股息 ETF 相比有什麼特色？",
        "00927（群益半導體收益 ETF）主打半導體產業的高股息標的，比一般高股息 ETF 集中在科技產業，潛在成長性較高但波動也大。適合看好台灣半導體長期發展、同時想領股息的投資人。"
    ),
    "00932-dividend-calculator.html": (
        "00932 的選股邏輯是什麼？配息穩定嗎？",
        "00932（兆豐永續高息等權 ETF）採等權重配置，避免持股過度集中單一個股，並加入 ESG 篩選。殖利率表現穩定，適合追求分散風險且重視配息穩定性的投資人，可搭配<a href='/'>股利計算器</a>試算。"
    ),
    "00934-dividend-calculator.html": (
        "00934 的配息和填息表現如何？",
        "00934（中信成長高股息 ETF）強調兼顧股息與成長性，選股時同時考量殖利率與獲利成長潛力。配息與填息表現需查看近幾季實際紀錄，建議搭配<a href='/'>股利計算器</a>試算你的實際年化報酬。"
    ),
    "00936-dividend-calculator.html": (
        "00936 的選股邏輯和配息穩定性如何？",
        "00936（台新臺灣永續高息中小 ETF）專注中小型股，相較大型股波動較高但潛在殖利率也高。適合可接受較高波動、追求高現金流的投資人。建議用<a href='/'>股利計算器</a>評估合理買入區間。"
    ),
    "00939-dividend-calculator.html": (
        "00939 和 00929 有什麼差別？",
        "00939（台灣ESG永續高股息 ETF）和 00929 同樣為月配息，但 00939 加入 ESG 篩選標準，成分股更聚焦永續經營企業。兩者月配息特性相似，差異在於選股邏輯，可用<a href='/compare'>個股比較器</a>對照殖利率後決定。"
    ),
    "00943-dividend-calculator.html": (
        "00943 的配息特色是什麼？適合存股嗎？",
        "00943（元大台灣高息低波 ETF）主打低波動高股息，選股時同時篩選殖利率高且股價波動較低的標的，適合風險承受度較低、追求穩定配息的保守型投資人。建議搭配<a href='/'>股利計算器</a>試算。"
    ),
    # ETF 比較
    "0050-vs-006208.html": (
        "長期來看，0050 和 006208 哪個更值得選？",
        "長期來看兩者報酬幾乎相同，因為追蹤相同指數。若在意費用，006208 經理費略低（0.12% vs 0.15%），長期累積下來有些許差異。若在意流動性與知名度，0050 較佳。建議用<a href='/'>股利計算器</a>試算兩者在你買入價格下的殖利率。"
    ),
    "0056-vs-0050.html": (
        "長期總報酬（含股利）誰比較高？",
        "根據歷史數據，0050 的長期總報酬（含股利再投入）通常略高於 0056，因為市值型 ETF 能完整參與台股成長。但 0056 的現金配息更穩定，適合需要定期現金流的人。沒有絕對的好壞，取決於你的資金需求。"
    ),
    "0056-vs-00713.html": (
        "0056 和 00713 可以一起持有嗎？",
        "可以。0056 規模大、流動性佳、歷史較長；00713 加入財務品質篩選，持股較穩健。兩者都是高股息型，可同時持有以分散選股邏輯的差異。建議用<a href='/compare'>個股比較器</a>對照目前殖利率後決定比例。"
    ),
    "0056-vs-00878.html": (
        "0056 和 00878 的配息哪個更穩定？",
        "兩者都採季配息，穩定性相近。0056 歷史較長（2007 年成立），經歷過多次股市循環考驗；00878 加入 ESG 篩選，成立於 2020 年，殖利率略高但歷史較短。若重視歷史驗證選 0056，若看重 ESG 與稍高殖利率選 00878。"
    ),
    "0056-vs-00919.html": (
        "長期持有，0056 和 00919 哪個更適合？",
        "0056 歷史長、波動較低、配息穩定；00919 殖利率更高但成立時間短、尚未經過股災完整考驗。若是保守型投資人選 0056，若能接受更高波動追求高現金流則可考慮 00919。也可兩者各配置一部分。"
    ),
    "00878-vs-00919.html": (
        "00878 和 00919 的選股邏輯有什麼差異？",
        "00878 同時考量 ESG 與股息，選股較保守穩健；00919 純粹追求高殖利率，選股更積極，殖利率通常高出 1～2%。想兼顧 ESG 選 00878，純粹追求高配息選 00919。可用<a href='/compare'>個股比較器</a>即時對照殖利率。"
    ),
    "00878-vs-00940.html": (
        "00878 和 00940 哪個更適合存股新手？",
        "00878 成立較早（2020 年）、規模大、流動性佳，適合新手；00940 成立於 2024 年，歷史紀錄非常短，尚未驗證配息穩定性。新手建議先從 00878 開始，待 00940 有更多配息紀錄後再評估。"
    ),
    "00919-vs-00929.html": (
        "00919 季配息 vs 00929 月配息，哪個比較好？",
        "這取決於你對現金流的需求。00929 每月配息，現金流更平穩；00919 每季配息，但殖利率通常稍高。若需要每月固定收入選 00929，若不在乎配息頻率只看重整體配息金額選 00919。"
    ),
    "00919-vs-00939.html": (
        "00919 和 00939 可以一起存嗎？",
        "可以。兩者分別來自不同投信（群益 vs 台灣 ESG），選股邏輯略有差異，搭配持有可分散單一投信風險。00919 殖利率略高，00939 加入 ESG 篩選。可用<a href='/compare'>個股比較器</a>對照目前殖利率後決定配置比例。"
    ),
    "00929-vs-00878.html": (
        "00929 月配息和 00878 季配息，該選哪個？",
        "00929 月月配息，現金流更頻繁，適合想每月領錢的人；00878 季配息，但規模更大、ESG 篩選嚴謹、殖利率也不差。若生活需要月月補貼選 00929，若不需要那麼頻繁的現金流選 00878 更穩。"
    ),
    "00939-vs-00940.html": (
        "00939 和 00940 哪個比較值得存？",
        "00939 成立較早（2023 年）、有一定歷史配息紀錄可參考；00940 成立於 2024 年，歷史非常短，配息穩定性尚待驗證。目前更建議選擇 00939，待 00940 累積更多紀錄後再評估。"
    ),
    # 個股
    "cathay-financial-dividend.html": (
        "國泰金適合長期存股嗎？",
        "國泰金（2882）是台灣最大保險集團，配息相對穩定，近年殖利率約 4～6%。適合偏好金融股、追求穩定股息的長期存股者。但金融股受升降息週期影響，建議用<a href='/'>股利計算器</a>試算你的實際殖利率再決定。"
    ),
    "chunghwa-telecom-dividend.html": (
        "中華電近年配息穩定嗎？有下降風險嗎？",
        "中華電（2412）連續多年配發 4～5 元，是台股公認最穩健的存股標的之一，有「護城河」特性。但電信市場競爭激烈，配息金額近年有微幅下降趨勢，建議持續追蹤法說會。長期持有抗通膨效果佳。"
    ),
    "mediatek-dividend.html": (
        "聯發科殖利率偏低，為什麼還有人存？",
        "聯發科（2454）殖利率約 3～4%，低於高股息 ETF，但其成長性強、每股盈餘高。許多投資人看重的是長期資本利得而非股息，屬於「成長+股息」的混合型存股。若你需要穩定高現金流，高股息 ETF 更適合。"
    ),
    "mega-financial-dividend.html": (
        "兆豐金和第一金哪個更適合存股？",
        "兩者都是公股銀行，配息穩定度相近。兆豐金（2886）規模較大、獲利能力略強，配息歷史更穩定；第一金（2892）股價相對較低，投資門檻低。若預算有限可選第一金，若追求配息穩定性選兆豐金。"
    ),
    # 其他
    "dividend-payment-schedule.html": (
        "台股除息後多久才會入帳？",
        "通常除息後約 1 個月內入帳。實際入帳時間由各公司決定，一般為除息後 30～45 個工作日。可在公司公告的「配息基準日」後查詢你的券商帳戶，或至台灣股市資訊網確認入帳日期。"
    ),
    "dividend-reinvest-strategy.html": (
        "這個雙核心策略有沒有什麼風險或缺點？",
        "有幾個需注意：1. 高股息 ETF 每季配息金額不固定，若配息縮水，可買入的市值型 ETF 數量也會減少。2. 需要持續執行紀律，遇到市場下跌時仍需堅持再投入。3. 頻繁交易會產生手續費。整體而言仍是合理的長期策略。"
    ),
    "dividend-tax-calculator.html": (
        "股息所得要如何在報稅時申報？",
        "股息屬於「股利所得」，每年 5 月申報綜合所得稅時需列入。券商會寄送「股利扣繳憑單」，可選擇合併計稅（按個人稅率，可享 8.5% 抵減額）或分離計稅（固定 28%）。建議使用財政部的報稅軟體試算何者較省。"
    ),
    "e-sun-financial-dividend.html": (
        "玉山金和國泰金、富邦金相比，哪個配息較好？",
        "三者都是大型金控，各有優劣。富邦金規模最大、獲利能力強；國泰金配息歷史穩定；玉山金近年轉型數位金融，成長潛力較強但配息率相對偏低。建議用<a href='/compare'>個股比較器</a>對照殖利率後依個人偏好選擇。"
    ),
    "etf-stock-saving-guide.html": (
        "存股新手第一次買，建議從哪裡開始？",
        "建議從月配或季配的高股息 ETF 開始，例如 0056 或 00878，每月定期定額投入 3,000～5,000 元。先從小金額培養習慣，再逐步增加。可用<a href='/dca-calculator'>定期定額試算器</a>模擬長期累積效果，確認自己的投資目標是否合理。"
    ),
    "first-financial-dividend.html": (
        "第一金近幾年配息有成長嗎？未來展望如何？",
        "第一金（2892）近幾年配息相對穩定，但成長幅度不大，主要靠政策性業務維持穩健。公股銀行在利率上升環境下淨利差有所改善，配息維持穩定的可能性高。適合保守型存股族作為核心持股之一。"
    ),
    "formosa-plastics-dividend.html": (
        "台塑適合長期存股嗎？石化產業有什麼風險？",
        "台塑（1301）是傳統績優股，配息歷史穩定，但石化產業面臨能源轉型與環保壓力，長期成長性有限。若只看股息收入，殖利率尚可接受；但若追求資本增值，高科技或成長型標的可能更適合。建議做好產業分散。"
    ),
    "how-to-calculate-dividend.html": (
        "可以用什麼工具快速計算股利？",
        "最快的方式是使用<a href='/'>股利計算器</a>：輸入股價與每股配息，立即算出殖利率；輸入投入金額，即可算出預估年股利。也可查看<a href='/compound-calculator'>存股複利計算器</a>，試算長期複利累積效果。"
    ),
    "monthly-dividend-etf.html": (
        "月配息 ETF 有什麼缺點需要注意？",
        "主要有三點：1. 每次配息時要繳二代健保補充保費（超過 2 萬元扣 2.11%），頻繁配息若金額較大會重複扣繳。2. 每月配息不代表殖利率更高，需比較年化配息總額。3. 部分月配息 ETF 規模較小，流動性較差。"
    ),
    "quanta-dividend.html": (
        "廣達殖利率低，還適合存股嗎？",
        "廣達（2382）是台灣 AI 伺服器重要供應商，近年受惠 AI 熱潮獲利大幅成長，但股價也大漲導致殖利率下降。若看重現金股息，傳統高股息 ETF 更合適；若看好 AI 成長趨勢，廣達的資本利得潛力較強。"
    ),
    "taiwan-coop-dividend.html": (
        "合庫金近年配息有成長嗎？",
        "合庫金（5880）是公股銀行，配息相對穩定但成長幅度有限，近幾年約配 1.0～1.4 元。在利率上升環境下，銀行獲利有所改善，配息略有增加。適合保守型存股族搭配其他高股息 ETF 分散持有。"
    ),
    "taiwan-stock-dividend-guide.html": (
        "台股除息後，股價一般要多久才能填息？",
        "填息時間差異很大，從幾天到幾年都有，甚至部分標的永遠無法填息。高股息 ETF（如 0056、00878）歷史填息紀錄較佳，通常 3～12 個月內填息。個股的填息能力取決於公司獲利，可在 Goodinfo 查詢各股歷史填息天數。"
    ),
    "uni-president-dividend.html": (
        "統一企業配息穩定嗎？近年有成長嗎？",
        "統一企業（1216）是台灣食品龍頭，配息紀錄穩定，近年每股配息約 2～2.5 元，有緩步成長趨勢。食品股受景氣循環影響較小，適合保守型長期存股族。可用<a href='/'>股利計算器</a>試算目前買入的殖利率。"
    ),
}

# ─── 執行函式 ──────────────────────────────────────────────────────────

def add_direct_answer(html, answer_text):
    """在 article-meta 結束後的第一個 <p> 開頭加入 <strong>"""
    pattern = r'(class="article-meta"[^>]*>.*?</div>\s*<p>)'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return html, False
    insert_pos = match.end()
    new_html = html[:insert_pos] + f'<strong>{answer_text}</strong> ' + html[insert_pos:]
    return new_html, True


def add_fourth_faq(html, question, answer):
    """在 FAQPage JSON-LD 和 HTML article-faq-item 加入第 4 題"""
    modified = html

    # 1. JSON-LD：找 FAQPage schema，在 mainEntity 最後一個 } 後加新問題
    def add_faq_json(m):
        block = m.group(0)
        # 找最後一個 acceptedAnswer 的結束
        last_answer_end = block.rfind('"@type": "Answer"')
        if last_answer_end == -1:
            return block
        # 找那個 Answer 區塊的結束 }}}
        close_pos = block.find('}', block.find('}', block.find('}', last_answer_end) + 1) + 1)
        if close_pos == -1:
            return block
        new_q = f''',
      {{
        "@type": "Question",
        "name": "{question}",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "{re.sub(r"<[^>]+>", "", answer)}"
        }}
      }}'''
        return block[:close_pos+1] + new_q + block[close_pos+1:]

    modified = re.sub(
        r'<script[^>]*application/ld\+json[^>]*>.*?"@type"\s*:\s*"FAQPage".*?</script>',
        add_faq_json,
        modified,
        flags=re.DOTALL
    )

    # 2. HTML：在最後一個 article-faq-item 後插入新的
    items = list(re.finditer(r'<div class="article-faq-item">.*?</div>', modified, re.DOTALL))
    if not items:
        return modified, False

    last_end = items[-1].end()
    new_item = f'''
        <div class="article-faq-item">
          <h3>{question}</h3>
          <p>{answer}</p>
        </div>'''
    modified = modified[:last_end] + new_item + modified[last_end:]
    return modified, True


# ─── 主程式 ────────────────────────────────────────────────────────────

def main():
    changed_direct = []
    changed_faq = []
    errors = []

    # Part 1：加直接回答
    print("=== Part 1：加直接回答 ===")
    for fname, answer in DIRECT_ANSWERS.items():
        fpath = os.path.join(ARTICLES, fname)
        if not os.path.exists(fpath):
            print(f"  [SKIP] {fname} 不存在")
            continue
        html = open(fpath).read()
        new_html, ok = add_direct_answer(html, answer)
        if ok:
            open(fpath, 'w').write(new_html)
            changed_direct.append(fname)
            print(f"  [OK] {fname}")
        else:
            errors.append(fname)
            print(f"  [FAIL] {fname} 找不到插入點")

    # Part 2：加第 4 題 FAQ
    print(f"\n=== Part 2：加第 4 題 FAQ ===")
    for fname, (q, a) in FOURTH_FAQ.items():
        fpath = os.path.join(ARTICLES, fname)
        if not os.path.exists(fpath):
            print(f"  [SKIP] {fname} 不存在")
            continue
        html = open(fpath).read()
        # 先確認真的只有 3 題
        existing_qs = re.findall(r'"@type"\s*:\s*"Question"', html)
        if len(existing_qs) >= 4:
            print(f"  [SKIP] {fname} 已有 {len(existing_qs)} 題")
            continue
        new_html, ok = add_fourth_faq(html, q, a)
        if ok:
            open(fpath, 'w').write(new_html)
            changed_faq.append(fname)
            print(f"  [OK] {fname}")
        else:
            errors.append(fname)
            print(f"  [FAIL] {fname}")

    print(f"\n=== 結果 ===")
    print(f"加直接回答：{len(changed_direct)} 篇")
    print(f"加第 4 FAQ：{len(changed_faq)} 篇")
    print(f"錯誤：{len(errors)} 篇 → {errors}")

if __name__ == "__main__":
    main()
PYEOF