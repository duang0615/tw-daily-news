# 每日股市新聞卡片工作流 · AI 接手規格書

> AI煉金術系列 · 堂 1「打造你的移動交易室」收尾作業 2
> 星系投資 AI墨達人 × 麥可鄧 · 2026-09-19 · 教方法，非投資建議

---

## 0. 這份文件怎麼用

**這份檔案是寫給 AI 看的，不是寫給你背的。**

你要做的事只有一件：把整份檔案貼給你的 AI（Hermes / Claude / ChatGPT 都可以），然後說：

```
請讀完這份規格書，然後幫我做出裡面描述的東西。
我的總頁在：（貼上你的 index.html 路徑）
不確定的地方先問我，不要自己猜。
```

AI 會照著下面的規格幫你把程式寫出來、跑起來、設好排程。
你負責的是**驗收**——第 3 節那張清單，每一格都要打勾。

---

## 1. 前提：你必須已經有這些

| 項目 | 哪一關做的 | 沒有的話 |
|---|---|---|
| 一個能跑的 Hermes / AI 助理 | 閘門 1 | 先回去把閘門 1 做完 |
| 一個「總頁」index.html | 收尾作業 1 | 先建一個英文資料夾，裡面放一個 index.html |
| Python 3.8 以上 | — | 讓 AI 帶你裝，只要標準函式庫，不用裝任何套件 |
| 電腦會開著、能連網 | 閘門 4 | 排程跑不起來就沒有「每天」 |

> 這支程式**只用 Python 標準函式庫**（urllib、xml、json、re）。
> 不需要 `pip install` 任何東西。如果 AI 叫你裝 feedparser、requests、beautifulsoup，
> 跟它說不用，照這份規格寫就好。

---

## 2. 目標：一句話

> **總頁上多一張「每日新聞」卡片，點進去是一份可以搜尋的當日新聞標題列表。**

你已經有一個總頁了。現在要在上面掛一張**每天自己更新的卡片**。

重點是**卡片只是入口**：總頁保持乾淨，新聞不要灌在總頁上。
點進去才是列表——標題一行一則，後面標上資料來源，
你自己搜尋、自己挑有興趣的點開，不需要它幫你摘要。

這是整個移動交易室的第一個**自動產出內容**的工作流。
學會這一個，之後換成法說會行事曆、盤後籌碼摘要、可轉債到期表，都是同一套骨架。

---

## 3. 驗收標準：做完要長這樣

做完之後，這十格全部要能打勾：

- [ ] 跑 `python build_news.py`，畫面印出每個來源抓到幾則
- [ ] 總頁「分析」區多了**一張**「每日新聞」卡片
- [ ] 點進去是一份標題列表，每一則都有**日期 + 來源**
- [ ] 上方搜尋框打關鍵字，列表即時縮短，右邊的「顯示 X / Y 則」會跟著變
- [ ] 左邊可以切「媒體新聞 / 官方公告 / 重大訊息」，右邊下拉可以挑單一來源
- [ ] 搜一個不存在的字，會出現「沒有符合的新聞」而不是一片空白
- [ ] 產生 `daily-news/news.json`，這份是給 AI 讀的
- [ ] **再跑一次**，總頁還是只有一張卡，不是兩張（這點最多人做錯）
- [ ] 列表頁上方有一排來源燈號，綠燈=通、紅燈=壞掉
- [ ] 工作排程設好，隔天早上不用你動手，卡片自己換了日期

---

## 4. 資料來源：六個來源，已經幫你驗證過

**驗證日期：2026-09-15。** 每一個都實際抓過，下面是當天的真實結果。

| 來源 | 取得方式 | 網址 | 狀態 |
|---|---|---|---|
| 證交所·新聞 | OpenAPI (JSON) | `https://openapi.twse.com.tw/v1/news/newsList` | ✅ 可用 |
| 證交所·重大訊息 | OpenAPI (JSON) | `https://openapi.twse.com.tw/v1/opendata/t187ap04_L` | ✅ 可用 |
| 櫃買·重大訊息 | OpenAPI (JSON) | `https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O` | ✅ 可用 |
| 期交所·公告 | RSS | `https://www.taifex.com.tw/cht/11/RSS1` | ✅ 可用 |
| 期交所·新聞稿 | RSS | `https://www.taifex.com.tw/cht/11/RSS2` | ✅ 可用 |
| 期交所·契約調整 | RSS | `https://www.taifex.com.tw/cht/11/RSS3` | ✅ 可用（預設沒開） |
| 鉅亨網·台股 | RSS | `https://news.cnyes.com/rss/v1/news/category/tw_stock` | ✅ 可用 |
| 鉅亨網·頭條 | RSS | `https://news.cnyes.com/rss/v1/news/category/headline` | ✅ 可用 |
| **MoneyDJ** | 原生 RSS **已停用** | `/KMDJ/RSS/` 整區回 404 | ⚠️ 改用 Google News |
| **DigiTimes** | 原生 RSS **需登入** | `/tech/rss/xml/*.xml` 匿名回 404 | ⚠️ 改用 Google News |

### 這一節就是本關的重點

課堂上我請 AI 抓這六家，結果是：**四家有官方管道，兩家的 RSS 已經死了。**

- MoneyDJ 的 RSS 目錄頁整個變成 404 錯誤頁
- DigiTimes 的 RSS 網址還在，但要會員登入才給，匿名抓回來是 404

這不是程式寫錯，是**資料來源消失了**。

網路上任何一篇「台股 RSS 大全」的文章，抄下來直接用都會踩到這個。
**先驗證，再寫程式**——這是這一關真正要學的事。

### 死掉的來源怎麼救：Google News 代打

```
https://news.google.com/rss/search?q=site:moneydj.com+when:2d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant
```

把 `site:` 後面換成任何網域，就能拿到那個站最近的新聞 RSS。
`when:2d` 是「最近兩天」。這招對**任何沒有官方 RSS 的網站**都有效，
是這份工作流裡最值得你記住的一行網址。

> 代打的代價：標題後面會多一截「 - 來源名」，連結是 Google 的轉址。
> 程式裡要把那截尾巴砍掉再比對，不然去重會失效。

---

## 5. 工作流：四步

### 第 1 步 · 挑來源，先驗證

一個一個打開，確認真的抓得到東西，再開始寫。

驗證的方法（叫 AI 幫你跑）：對每個網址發一次請求，看回來的是不是 XML / JSON，
而不是一頁 HTML 錯誤頁。**HTTP 狀態碼是 200 不代表成功**——
MoneyDJ 和 DigiTimes 的 404 錯誤頁就是用 200 回你的。

### 第 2 步 · 抓下來，併成一張表

三種格式（RSS、證交所 JSON、重大訊息 JSON）轉成同一種欄位：

```
標題 title｜連結 link｜來源 source｜時間 dt｜摘要 summary
```

然後做三件事：

1. **去重** — 同一則新聞常常好幾家同時發
2. **濾舊** — 只留最近 48 小時（重大訊息例外，見第 6 節）
3. **濾雜訊** — 模板式自動產文（例如「鉅亨速報 - Factset 最新調查」一天幾十則）

單一來源抓不到就跳過那一家，**不要讓整支程式掛掉**。

### 第 3 步 · 印成列表

產出兩份檔案，同一份資料，兩種讀者：

| 檔案 | 給誰看 | 用途 |
|---|---|---|
| `daily-news/index.html` | 給**你**看 | 早上掃標題，有興趣的自己點開 |
| `daily-news/news.json` | 給 **AI** 讀 | 你可以問它「今天有沒有我持股的消息」 |

列表頁要有這四件事，缺一個就不好用：

1. **一則一行** — 日期、來源、標題。**不要放摘要**，摘要只會讓你滑不完
2. **搜尋框** — 打關鍵字即時過濾標題，這是你每天真正會用的功能
3. **左邊分類** — 媒體新聞 / 官方公告 / 重大訊息，三類分開看
4. **來源下拉** — 只想看鉅亨網的時候，一鍵篩掉其他家

全部用純前端 JavaScript 做，**不要另外架伺服器**。
資料在產出時就寫死在頁面裡，搜尋是在瀏覽器本機跑的，
所以這頁放在 NAS、放在隨身碟、直接用檔案打開，都一樣會動。

**JSON 那份才是真正的價值。**
有了它，你可以對 AI 說：「讀 news.json，挑出跟我庫存有關的，其他不用講。」

### 第 4 步 · 貼回總頁

在總頁挖一個插槽：

```html
<!-- NEWS:START -->
   ...每天被換掉的內容...
<!-- NEWS:END -->
```

程式每天把兩個標記之間的東西整段換掉。**裡面只有一張卡**，不是一堆新聞。

**這裡是最多人做錯的地方**：如果你用「附加」而不是「取代」，
跑三天總頁上就會有三張一樣的卡。一定要用標記夾住，然後整段覆蓋。

卡片上要顯示「更新時間 + 今天幾則 + 幾個來源」——
這樣你在總頁掃一眼，就知道它今天到底有沒有跑成功。

第一次跑的時候程式會自動建立插槽，並且**先備份原本的總頁**。

---

## 6. 陷阱：我踩過的，你不用再踩

### 陷阱 1 · 狀態碼 200 不等於成功

MoneyDJ、DigiTimes 的錯誤頁都是用 HTTP 200 回你的 HTML。
判斷成功要看**內容**（有沒有 `<item>` / 是不是合法 JSON），不是看狀態碼。

### 陷阱 2 · 重大訊息不能套時間窗

證交所和櫃買的「每日重大訊息」是**每日快照檔**，不是即時流。
遇到連假、或當天沒有新申報，裡面就是前幾天的資料。
如果你套「只收 48 小時內」，整區會空掉，看起來像壞了其實沒壞。

→ 解法：這兩個來源標成 `snapshot`，不套時間窗，永遠取最新一批。

### 陷阱 3 · 民國年 + 發言時間

證交所回的日期是 `1150914`（民國 115 年 9 月 14 日），要 `+1911`。
另外有一個獨立的 `發言時間` 欄位 `070003`（07:00:03）。
**只取日期會讓每一則都變成當天 00:00**，排序會亂掉。

### 陷阱 4 · 欄位名稱尾端有空白

證交所重大訊息的 JSON 欄位名是 `"主旨 "`——**後面有一個空格**。
直接 `r["主旨"]` 會抓不到。讀進來先把所有 key 做一次 `.strip()`。

### 陷阱 5 · 期交所的 RSS 裡全是換行

期交所 RSS 的 `<link>` 和 `<pubDate>` 前後夾了一大堆換行和 tab。
不清乾淨的話，連結是壞的、時間解析不出來。所有欄位讀進來一律先壓成單行。

### 陷阱 6 · 不要把新聞灌在總頁上

第一版我把六則新聞直接鋪在總頁最上面，結果是：
總頁變得又長又吵，而且六格全被最會發稿的鉅亨網一家包走。

→ 解法：**總頁只放一張卡當入口**，新聞全部收進列表頁。
總頁是目錄，不是內容——這個原則之後做任何新工具都適用。

### 陷阱 7 · 列表頁不要放摘要

摘要看起來很貼心，實際上一則佔三行，一百多則你根本滑不完。
你要的是「掃標題 → 挑有興趣的 → 點開看」。
摘要留在 news.json 裡給 AI 用就好，**人看的那頁只放標題**。

---

## 7. 設排程：這一步沒做，前面都白做

**沒有排程，它就只是一支「你想到才會跑一次」的程式。**

Windows 工作排程器：

```
建立工作 → 觸發程序：每日 08:00
         → 動作：程式  python
                 引數  「你的路徑\daily-news\build_news.py」
         → 勾選「不論使用者是否登入均執行」
```

**為什麼是 08:00？** 開盤前你會看手機。
前一晚的重大訊息、法人動向、國際盤消息，這時候都已經落地了。

設好之後，隔天早上不要碰電腦，直接打開總頁看它有沒有自己換。
**沒換，就是排程沒設成功**，不是程式的問題。

---

## 8. 照抄 · 給 AI 的指令

做完之後，把這段存進你的規則檔，之後每天可以這樣用：

```
讀 daily-news/news.json，然後：
1. 挑出跟我庫存（2330、2454、3661）有關的新聞，沒有就說沒有
2. 挑出三則你覺得今天最重要的，各用一句話說為什麼
3. 不要幫我判斷買賣，只要告訴我「今天盤前該知道什麼」
```

> 注意最後一句。**推播只叫你看，拍板的還是你**——
> 這是整堂課從第一頁講到最後一頁的同一件事。

---

## 9. 下一步：同一套骨架可以長出什麼

這支程式的骨架是「**抓 → 整 → 印 → 貼**」。
四個步驟裡，只有第 1 步（來源）需要換，其他三步幾乎原封不動：

| 換成什麼 | 來源換成 | 難度 |
|---|---|---|
| 法說會行事曆 | 公開資訊觀測站 | ★☆☆ |
| 每日籌碼摘要 | 證交所三大法人 OpenAPI | ★★☆ |
| 可轉債到期表 | 櫃買 CB 資料 | ★★☆ |
| 你持股的專屬新聞 | 上面的 news.json + 你的庫存表 | ★☆☆ |

**最後一項最值得做**，而且今天你已經有全部的材料了。

---

## 附錄 · 參考實作

下面是完整可跑的程式。你可以直接用，也可以讓 AI 照著改成你要的樣子。

存成 `daily-news/build_news.py`，然後：

```bash
python build_news.py --dry-run    # 先只抓不寫檔，確認來源都通
python build_news.py              # 確認沒問題再正式跑
```

`--dry-run` 這個開關很重要：**第一次跑一定先用它**，
確認九個來源的燈號都是綠的，再讓它去動你的總頁。

列表頁的搜尋與篩選是純前端，改版面只要改 `CSS` 和 `JS` 兩個字串，不會動到抓資料的部分。

```python
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
    inject_hub(items, now)
    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

*AI煉金術系列 · 堂 1 打造你的移動交易室 · 麥可鄧 × 星系投資 AI墨達人*
*本文件僅供教學使用。新聞標題與連結屬各原網站所有，本工作流僅做索引，不重製內容。*
*所有內容為教學示範，非投資建議。*
