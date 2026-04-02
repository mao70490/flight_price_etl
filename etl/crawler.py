from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta

def fetch_flights_playwright(depart_code, arrive_code, ddate):
    # 自動計算回程日期以解除日曆鎖定
    depart_dt_obj = datetime.strptime(ddate, "%Y-%m-%d")
    return_dt = (depart_dt_obj + timedelta(days=2)).strftime("%Y-%m-%d")
    
    result_data = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        page = context.new_page()

        # 注入 Stealth 腳本隱藏自動化特徵
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        def handle_response(response):
            nonlocal result_data
            if "FlightListSearch" in response.url and response.status == 200:
                try:
                    text = response.text()
                    for line in text.split("\n"):
                        if "data:" in line:
                            json_str = line.split("data:")[-1].strip()
                            data = json.loads(json_str)
                            if data.get("itineraryList"):
                                result_data = data
                except: pass

        page.on("response", handle_response)

        try:
            print("🏠 進入首頁...")
            page.goto("https://tw.trip.com/?locale=zh-TW", wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            print("✈️ 切換至機票標籤...")
            page.get_by_text("機票", exact=True).first.click()
            page.wait_for_timeout(1000)

            # 1. 填寫地點、日期
            print(f"🛫 設定: {depart_code} -> {arrive_code}")
            page.locator("input[placeholder*='出發']").first.fill(depart_code)
            page.wait_for_timeout(1500)
            page.keyboard.press("Enter")
            
            page.locator("input[placeholder*='目的地']").first.fill(arrive_code)
            page.wait_for_timeout(1500)
            page.keyboard.press("Enter")

            # 模擬人類點擊日曆 (處理 readonly 與 State 同步問題)
            print(f"📅 執行日曆操作：出發 {ddate} -> 回程 {return_dt}")
            
            # A. 打開日曆
            page.locator("[data-testid='search_date_depart0']").first.click()
            page.wait_for_timeout(800)

            # B. 點擊「出發日」格子
            depart_day_selector = f"div[data-date='{ddate}']"
            if page.locator(depart_day_selector).first.is_visible():
                page.locator(depart_day_selector).first.click()
                print(f"✅ 已點擊出發日: {ddate}")
            else:
                # 如果日期在下個月，可能需要點擊「下一月」按鈕
                print("⚠️ 找不到出發日格子，嘗試點擊下一月...")
                page.locator("i.fi-calendar-next, .calendar-next-btn").first.click()
                page.wait_for_timeout(500)
                page.locator(depart_day_selector).first.click()

            page.wait_for_timeout(500)

            # C. 點擊「回程日」格子 (解除 Range Picker 鎖定)
            return_day_selector = f"div[data-date='{return_dt}']"
            if page.locator(return_day_selector).first.is_visible():
                page.locator(return_day_selector).first.click()
                print(f"✅ 已點擊回程日: {return_dt} (解除鎖定)")
            
            page.wait_for_timeout(800)
            

            # 2.點擊搜尋按鈕
            try:
                print("🔍 準備點擊搜尋鈕...")
                
                # 1. 嘗試先置頂，確保 UI 狀態正確
                page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
                page.wait_for_timeout(300) 

                # 2. 定位按鈕
                search_btn = page.locator("div[data-testid='search_btn']").first
                
                # 3. 使用 JS 點擊 (最穩) + Playwright 備援點擊
                # 先試 JS 點擊，因為它不需要元素在可視範圍內
                page.evaluate("() => document.querySelector('[data-testid=\"search_btn\"]').click()")
                
                # 4. 如果沒跳轉，再用 Playwright 的強制點擊補刀
                if "date=" not in page.url: # 簡單判斷網址有沒有變化
                    search_btn.click(force=True, timeout=2000)
                    
                print("🚀 搜尋指令已送出")
            except Exception as e:
                print(f"⚠️ 點擊過程遇到小問題: {e}")

            # 3. 🔥 核心：軟 404 救援邏輯
            print("⏳ 監控結果頁狀態...")
            
            # 等待 5 秒讓它跑 Loading
            page.wait_for_timeout(5000)

            # 檢查是否發生「情況 A」：網址對但畫面是 404
            # 我們檢查頁面標題或特定文字
            if "404" in page.content() or "Not Found" in page.title():
                print("🚨 偵測到『軟 404』，執行原位刷新救援...")
                # 這裡不 goto，直接 reload，這樣最能保留 Session
                page.reload(wait_until="domcontentloaded")
                print("♻️ 頁面已刷新，等待 SSE 數據...")
                page.wait_for_timeout(3000)

            # 4. 靜態等待數據 (不再瘋狂滾動，避免跟網頁腳本衝突)
            print("📡 正在攔截 SSE 數據流...")
            found_data = False
            for i in range(40):
                if result_data:
                    print(f"✅ 成功！在第 {i*0.5} 秒截獲數據")
                    found_data = True
                    break
                
                # 只有在沒資料時，才輕輕地滾動一下 (200像素就好)
                if i % 4 == 0:
                    page.mouse.wheel(0, 200)
                
                page.wait_for_timeout(500)

            if not found_data:
                print("❌ 最終仍未截獲數據，可能需要檢查攔截 URL 關鍵字。")

        except Exception as e:
            print(f"❌ 錯誤: {e}")

    return result_data



