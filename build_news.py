# -*- coding: utf-8 -*-
"""
每日股市新聞卡片產生器  ·  AI煉金術 堂1 收尾工作流
--------------------------------------------------
一天跑一次，做四件事：
  1. 抓  -- 六個來源（證交所 / 櫃買 / 期交所 / 鉅亨網 / MoneyDJ / DigiTimes）
  2. 整  -- 統一成同一種格式、去重、只留最近 N 小時
  3. 印  -- 產出 daily-news/index.html（卡片頁）+ news.json（給 AI 讀）
  4. 貼  -- 把前幾則塞回總頁 index.html 的插槽裡

用法：
    python build_news.py              # 正常跑
    python build_news.py --dry-run    # 只抓不寫檔，用來檢查來源通不通
    python build_news.py --no-hub     # 只產列表頁，不去動上一層的總頁（放 GitHub 用這個）
"""
import io, os, re, sys, json, time, html
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# -- 設定 ------------------------------------------------------------
HERE       = os.path.dirname(os.path.abspath(__file__))
HUB_HTML   = os.path.join(os.path.dirname(HERE), "index.html")   # 總頁
MAX_AGE_H  = 48      # 只收最近幾小時的新聞
PER_SOURCE = 25      # 每個來源最多留幾則（列表頁放得下，可以多收）

# 模板式的自動產文，資訊量低，直接濾掉。想留就把該行註解掉，想加就自己往下加。
NOISE = [
    r"鉅亨速報.*Factset",          # 每天數十則的分析師預估自動文
    r"^【公告】",                  # 純行政公告
]
TZ         = timezone(timedelta(hours=8))
UA         = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}


def gnews(q):
    """沒有官方 RSS 的站，用 Google News 的站內搜尋 RSS 代打。"""
    return ("https://news.google.com/rss/search?q=" +
            urllib.parse.quote(q) + "&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")


# kind: rss / twse_news / mops   （mops = 重大訊息 JSON，證交所與櫃買共用一個解析器）
SOURCES = [
    {"name": "證交所·新聞", "cat": "官方公告", "color": "#185FA5", "kind": "twse_news",
     "url": "https://openapi.twse.com.tw/v1/news/newsList",
     "note": "官方 OpenAPI"},
    {"name": "證交所·重大訊息", "cat": "重大訊息", "color": "#185FA5", "kind": "mops",
     "url": "https://openapi.twse.com.tw/v1/opendata/t187ap04_L",
     "note": "上市公司每日重大訊息", "snapshot": True},
    {"name": "櫃買·重大訊息", "cat": "重大訊息", "color": "#0F6E56", "kind": "mops",
     "url": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O",
     "note": "上櫃公司每日重大訊息", "snapshot": True},
    {"name": "期交所·公告", "cat": "官方公告", "color": "#B45309", "kind": "rss",
     "url": "https://www.taifex.com.tw/cht/11/RSS1",
     "note": "官方 RSS"},
    {"name": "期交所·新聞稿", "cat": "官方公告", "color": "#B45309", "kind": "rss",
     "url": "https://www.taifex.com.tw/cht/11/RSS2",
     "note": "官方 RSS"},
    {"name": "鉅亨網·台股", "cat": "媒體新聞", "color": "#C2410C", "kind": "rss",
     "url": "https://news.cnyes.com/rss/v1/news/category/tw_stock",
     "note": "官方 RSS"},
    {"name": "鉅亨網·頭條", "cat": "媒體新聞", "color": "#C2410C", "kind": "rss",
     "url": "https://news.cnyes.com/rss/v1/news/category/headline",
     "note": "官方 RSS"},
    {"name": "MoneyDJ", "cat": "媒體新聞", "color": "#7C3AED", "kind": "rss",
     "url": gnews("site:moneydj.com when:2d"),
     "note": "原生 RSS 已停用 → 改用 Google News 代打"},
    {"name": "DigiTimes", "cat": "媒體新聞", "color": "#0E7490", "kind": "rss",
     "url": gnews("site:digitimes.com.tw when:2d"),
     "note": "原生 RSS 需登入 → 改用 Google News 代打"},
]


# -- 小工具 ----------------------------------------------------------
def clean(s):
    """RSS 常夾雜換行與大量空白（期交所特別嚴重），一律壓成單行。"""
    if not s:
        return ""
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def fetch(url, timeout=25, retry=2):
    """抓不到就重試，最後仍失敗才丟例外（由 collect 接住，不讓整支掛掉）。"""
    last = None
    for i in range(retry + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def roc_to_date(s, hhmmss=None):
    """民國日期 1150914 -> datetime(2026, 9, 14)；有發言時間 070003 就一併補上。"""
    s = (s or "").strip()
    if len(s) != 7 or not s.isdigit():
        return None
    h = m = sec = 0
    t = (hhmmss or "").strip()
    if t.isdigit() and 5 <= len(t) <= 6:
        t = t.zfill(6)
        h, m, sec = int(t[:2]), int(t[2:4]), int(t[4:6])
    try:
        return datetime(int(s[:3]) + 1911, int(s[3:5]), int(s[5:7]),
                        min(h, 23), min(m, 59), min(sec, 59), tzinfo=TZ)
    except ValueError:
        return None


def parse_pubdate(s):
    s = clean(s)
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(s, fmt).astimezone(TZ)
        except Exception:
            pass
    return None


# -- 三種解析器 ------------------------------------------------------
def parse_rss(raw):
    root = ET.fromstring(raw.strip())
    out = []
    for it in root.iter("item"):
        t = clean(it.findtext("title"))
        if not t:
            continue
        out.append({"title": t,
                    "link": clean(it.findtext("link")),
                    "summary": clean(it.findtext("description"))[:160],
                    "dt": parse_pubdate(it.findtext("pubDate"))})
    return out


def parse_twse_news(raw):
    out = []
    for r in json.loads(raw.decode("utf-8")):
        t = clean(r.get("Title"))
        if not t:
            continue
        out.append({"title": t, "link": clean(r.get("Url")),
                    "summary": "", "dt": roc_to_date(r.get("Date"))})
    return out


def parse_mops(raw):
    """證交所與櫃買的重大訊息欄位名不同（而且證交所欄位名尾端有空白），兩邊都收。"""
    out = []
    for r in json.loads(raw.decode("utf-8")):
        r = {(k or "").strip(): v for k, v in r.items()}
        subj = clean(r.get("主旨"))
        if not subj:
            continue
        code = clean(r.get("公司代號") or r.get("SecuritiesCompanyCode"))
        name = clean(r.get("公司名稱") or r.get("CompanyName"))
        out.append({"title": "%s %s｜%s" % (code, name, subj[:60]),
                    "link": "https://mopsov.twse.com.tw/mops/web/t05st01",
                    "summary": clean(r.get("說明"))[:160],
                    "dt": roc_to_date(r.get("發言日期") or r.get("出表日期") or r.get("Date"),
                                      r.get("發言時間"))})
    return out


PARSERS = {"rss": parse_rss, "twse_news": parse_twse_news, "mops": parse_mops}


# -- 1+2. 抓 & 整 ----------------------------------------------------
def norm_title(t):
    t = re.sub(r"\s*-\s*[^-]{2,14}$", "", t)      # 砍掉 Google News 標題尾巴的「 - 來源」
    return re.sub(r"[^\w一-鿿]", "", t)[:40]


def collect():
    now = datetime.now(TZ)
    cutoff = now - timedelta(hours=MAX_AGE_H)
    items, status, seen = [], [], set()
    for s in SOURCES:
        try:
            rows = PARSERS[s["kind"]](fetch(s["url"]))
            kept, old, noise = [], 0, 0
            # snapshot 類來源（重大訊息）本身就是每日快照檔，不套時間窗，
            # 否則遇到連假沒有新申報時整區會空掉。
            snap = s.get("snapshot", False)
            for r in rows:
                if (not snap) and r["dt"] and r["dt"] < cutoff:
                    old += 1
                    continue
                if any(re.search(p, r["title"]) for p in NOISE):
                    noise += 1
                    continue
                key = norm_title(r["title"])
                if not key or key in seen:
                    continue
                seen.add(key)
                r["source"] = s["name"]
                r["color"] = s["color"]
                r["cat"] = s.get("cat", "其他")
                kept.append(r)
                if len(kept) >= PER_SOURCE:
                    break
            items += kept
            status.append({"name": s["name"], "ok": True, "n": len(kept), "note": s["note"],
                           "msg": "%d 則（原始 %d，過期 %d，雜訊 %d）" % (len(kept), len(rows), old, noise)})
        except Exception as e:
            status.append({"name": s["name"], "ok": False, "n": 0, "note": s["note"],
                           "msg": "抓取失敗：%s" % repr(e)[:80]})
    items.sort(key=lambda r: r["dt"] or datetime(1970, 1, 1, tzinfo=TZ), reverse=True)
    return items, status, now


# -- 3. 印成列表頁 --------------------------------------------------
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI","Microsoft JhengHei",sans-serif;
     background:#f5f7fa;color:#1c2530;min-height:100vh}
a{text-decoration:none}
.top{background:#fff;border-bottom:1px solid #e3e8ee;padding:18px 24px 14px}
.top .crumb{font-size:12.5px;color:#6b7785}
.top .crumb a{color:#2f6db5}
.top .crumb a:hover{text-decoration:underline}
.top h1{font-size:23px;margin:4px 0 2px}
.top .sub{font-size:12.5px;color:#6b7785}
.wrap{display:flex;align-items:flex-start;gap:0;max-width:1180px;margin:0 auto}
/* 左側分類 */
.side{width:166px;flex:0 0 166px;padding:20px 12px 40px;position:sticky;top:0}
.side .cat{display:block;padding:9px 12px;border-radius:8px;font-size:14px;color:#41506b;
           border-left:3px solid transparent;cursor:pointer;margin-bottom:2px}
.side .cat:hover{background:#eef2f7}
.side .cat.on{background:#fff;border-left-color:#185FA5;color:#12232a;font-weight:700;
              box-shadow:0 1px 2px rgba(20,40,70,.06)}
.side .cat b{float:right;font-weight:400;color:#8b95a3;font-size:12px}
/* 右側列表 */
.main{flex:1;min-width:0;padding:20px 20px 60px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.bar input,.bar select{font:inherit;font-size:13.5px;border:1px solid #d6dde6;border-radius:8px;
                       padding:8px 11px;background:#fff;color:#1c2530}
.bar input{flex:1;min-width:190px}
.bar input:focus,.bar select:focus{outline:2px solid #bcd3ee;outline-offset:-1px}
.bar .n{font-size:12.5px;color:#6b7785;margin-left:auto;white-space:nowrap}
.row{background:#fff;border:1px solid #e3e8ee;border-left:4px solid #185FA5;border-radius:10px;
     padding:11px 14px;margin-bottom:7px}
.row .meta{font-size:12px;color:#8b95a3;margin-bottom:3px;display:flex;gap:7px;
           flex-wrap:wrap;align-items:center}
.row .tag{background:#eef2f7;color:#41506b;border-radius:6px;padding:1px 7px;font-size:11px}
.row .t{font-size:15px;font-weight:600;line-height:1.5;color:#12232a;display:block}
.row .t:hover{text-decoration:underline}
.empty{padding:40px 6px;color:#8b95a3;font-size:14px;text-align:center}
/* 來源燈號 */
.hs{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}
.hs span{font-size:11px;border-radius:7px;padding:2px 8px}
.hs .ok{background:#e7f4ec;color:#1f9d55}
.hs .no{background:#fcebeb;color:#e23b3b}
.foot{margin:30px 0 0;font-size:11.5px;color:#9aa4b2;line-height:1.8}
@media(max-width:760px){
  .wrap{display:block}
  .side{width:auto;position:static;padding:12px 16px 0;display:flex;gap:6px;overflow-x:auto}
  .side .cat{white-space:nowrap;border-left:none;border-bottom:3px solid transparent;margin:0}
  .side .cat.on{border-left:none;border-bottom-color:#185FA5}
  .side .cat b{float:none;margin-left:6px}
  .main{padding:14px 16px 50px}
}
"""

JS = """
(function(){
  var q=document.getElementById('q'), sel=document.getElementById('src'),
      rows=[].slice.call(document.querySelectorAll('.row')),
      cats=[].slice.call(document.querySelectorAll('.cat')),
      n=document.getElementById('n'), empty=document.getElementById('empty'),
      cat='all';
  function apply(){
    var kw=q.value.trim().toLowerCase(), s=sel.value, shown=0;
    rows.forEach(function(r){
      var ok=(cat==='all'||r.dataset.cat===cat) &&
             (s==='all'||r.dataset.src===s) &&
             (!kw||r.dataset.k.indexOf(kw)>=0);
      r.hidden=!ok; if(ok) shown++;
    });
    n.textContent='顯示 '+shown+' / '+rows.length+' 則';
    empty.hidden=shown>0;
  }
  q.addEventListener('input',apply);
  sel.addEventListener('change',apply);
  cats.forEach(function(c){
    c.addEventListener('click',function(){
      cats.forEach(function(x){x.classList.remove('on')});
      c.classList.add('on'); cat=c.dataset.cat; apply();
    });
  });
  apply();
})();
"""

CATS = ["媒體新聞", "官方公告", "重大訊息"]


def row(r):
    """一列＝日期 + 來源 + 標題。標題自己點進去看，不放摘要。"""
    tm = r["dt"].strftime("%Y/%m/%d %H:%M") if r["dt"] else "時間不詳"
    return ('<div class="row" style="border-left-color:%s" data-cat="%s" data-src="%s" data-k="%s">'
            '<div class="meta"><span class="tag">%s</span><span>%s</span><span>%s</span></div>'
            '<a class="t" href="%s" target="_blank" rel="noopener">%s</a></div>'
            % (r["color"], html.escape(r["cat"]), html.escape(r["source"]),
               html.escape(r["title"].lower()),
               html.escape(r["cat"]), tm, html.escape(r["source"]),
               html.escape(r["link"]), html.escape(r["title"])))


def render_page(items, status, now):
    per_cat = {}
    for r in items:
        per_cat[r["cat"]] = per_cat.get(r["cat"], 0) + 1
    side = ('<a class="cat on" data-cat="all">全部<b>%d</b></a>' % len(items)) + "".join(
        '<a class="cat" data-cat="%s">%s<b>%d</b></a>' % (c, c, per_cat.get(c, 0))
        for c in CATS if per_cat.get(c))
    opts = '<option value="all">全部來源</option>' + "".join(
        '<option value="%s">%s</option>' % (html.escape(s["name"]), html.escape(s["name"]))
        for s in SOURCES if any(r["source"] == s["name"] for r in items))
    chips = "".join('<span class="%s">%s</span>'
                    % ("ok" if s["ok"] else "no",
                       html.escape(s["name"] + ("" if s["ok"] else " · 壞了")))
                    for s in status)
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            '<title>每日新聞 · %s</title><style>%s</style></head><body>'
            '<div class="top"><div class="crumb"><a href="../">AI 網頁部署中心</a> ／ 每日新聞</div>'
            '<h1>每日新聞</h1>'
            '<div class="sub">%s 更新 · 共 %d 則 · 證交所／櫃買／期交所／鉅亨網／MoneyDJ／DigiTimes</div></div>'
            '<div class="wrap"><nav class="side">%s</nav><div class="main">'
            '<div class="hs">%s</div>'
            '<div class="bar"><input id="q" type="search" placeholder="搜尋標題關鍵字，例如 台積電、可轉債、法說">'
            '<select id="src">%s</select><span class="n" id="n"></span></div>'
            '%s<div class="empty" id="empty" hidden>沒有符合的新聞，換個關鍵字試試。</div>'
            '<div class="foot">由 build_news.py 自動產生 · 資料來源為各站公開 RSS / OpenAPI<br>'
            '標題與連結屬原網站所有，本頁僅做索引 · 教學用途，非投資建議</div>'
            '</div></div><script>%s</script></body></html>'
            % (now.strftime("%Y-%m-%d"), CSS, now.strftime("%Y-%m-%d %H:%M"), len(items),
               side, chips, opts, "".join(row(r) for r in items), JS))


# -- 4. 總頁的「每日新聞」卡片 ---------------------------------------
START, END = "<!-- NEWS:START -->", "<!-- NEWS:END -->"


def hub_card(items, now):
    srcs = len({r["source"] for r in items})
    return ('%s<li class="bitem" style="border-left-color:#C2410C">'
            '<div class="ihead"><a class="ititle" style="color:#C2410C" href="daily-news/" '
            'target="_blank">每日新聞</a> <span class="tag"><span class="ok">可訪問</span></span></div>'
            '<div class="idesc">證交所／櫃買／期交所／鉅亨網／MoneyDJ／DigiTimes 每日彙整 · '
            '標題列表可搜尋、可依來源與分類篩選 · 每天早上 08:00 自動更新</div>'
            '<div class="imeta"><span class="latest">更新：%s · %d 則 / %d 個來源</span> · '
            '<a class="lk" href="daily-news/archive/" target="_blank">歷史快照</a></div></li>%s'
            % (START, now.strftime("%Y-%m-%d %H:%M"), len(items), srcs, END))


def inject_hub(items, now):
    """在總頁『分析 · Analysis』區塊的最前面放一張卡，用標記夾住，每天覆蓋。"""
    if not os.path.exists(HUB_HTML):
        print("  ! 找不到總頁 %s，跳過" % HUB_HTML)
        return
    src = io.open(HUB_HTML, encoding="utf-8").read()
    card_html = hub_card(items, now)
    if START in src and END in src:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END),
                     lambda m: card_html, src, flags=re.S)
        how = "更新卡片"
    else:
        m = re.search(r'<h3 class="sec-h">分析 · Analysis</h3>\s*<ul class="blist">', src)
        if not m:
            m = re.search(r'<ul class="blist">', src)
        if not m:
            print("  ! 總頁找不到可插入的位置，跳過")
            return
        io.open(HUB_HTML + ".bak_before_news", "w", encoding="utf-8").write(src)
        new = src[:m.end()] + "\n    " + card_html + src[m.end():]
        how = "新增卡片（原檔已備份為 index.html.bak_before_news）"
    io.open(HUB_HTML, "w", encoding="utf-8").write(new)
    print("  總頁 %s：%s" % (HUB_HTML, how))


# -- main ------------------------------------------------------------
def main():
    dry = "--dry-run" in sys.argv
    no_hub = "--no-hub" in sys.argv        # 放在 GitHub 之類沒有總頁的地方時用
    print("抓取中 ...")
    items, status, now = collect()
    for s in status:
        print("  [%s] %-14s %s" % ("OK  " if s["ok"] else "FAIL", s["name"], s["msg"]))
    print("合計 %d 則" % len(items))
    if dry:
        print("(--dry-run，不寫檔)")
        return 0
    if not items:
        print("! 一則都沒抓到，保留原本的頁面不覆蓋")
        return 1

    page = render_page(items, status, now)
    io.open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page)
    arc = os.path.join(HERE, "archive")
    os.makedirs(arc, exist_ok=True)
    io.open(os.path.join(arc, now.strftime("%Y-%m-%d") + ".html"), "w", encoding="utf-8").write(page)
    io.open(os.path.join(HERE, "news.json"), "w", encoding="utf-8").write(json.dumps(
        {"generated_at": now.isoformat(), "count": len(items), "sources": status,
         "items": [{"title": r["title"], "link": r["link"], "source": r["source"],
                    "category": r["cat"], "summary": r["summary"],
                    "time": r["dt"].isoformat() if r["dt"] else None} for r in items]},
        ensure_ascii=False, indent=2))
    print("  已寫出 index.html / news.json / archive/%s.html" % now.strftime("%Y-%m-%d"))
    if no_hub:
        print("  (--no-hub，不動總頁)")
    else:
        inject_hub(items, now)
    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
