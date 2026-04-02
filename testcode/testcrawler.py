from playwright.sync_api import sync_playwright
import json
import time

def fetch_flights_playwright(depart_code, arrive_code, ddate):
    result_data = None

    with sync_playwright() as p:
        # 💡 核心改變：headless=False (不使用無頭模式)，但透過 args 隱藏它
        browser = p.chromium.launch(
            headless=False, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--window-position=-2000,0", # 🚀 關鍵：把視窗丟到螢幕外面（你看不到的地方）
                "--window-size=1,1",         # 視窗縮到最小
                "--mute-audio"               # 靜音
            ]
        )
        
        # 建立一個像真人的 Context
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        
        page = context.new_page()
        
        # 監聽器與原本一致
        def handle_response(response):
            nonlocal result_data
            if "FlightListSearch" in response.url and response.status == 200:
                try:
                    for line in response.text().split("\n"):
                        if "data:" in line:
                            data = json.loads(line.split("data:")[-1].strip())
                            if data.get("itineraryList"): result_data = data
                except: pass

        page.on("response", handle_response)

        try:
            # 1. 回歸你最初成功的「手動輸入」流程，但在「視窗隱藏」狀態下執行
            print("🏠 正在背景(隱藏視窗)模擬輸入...")
            page.goto("https://tw.trip.com/?locale=zh-TW", wait_until="networkidle")
            
            # 點擊機票
            page.get_by_text("機票", exact=True).first.click()
            page.wait_for_timeout(1000)

            # 輸入地點
            page.locator("input[placeholder*='出發']").first.fill(depart_code)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
            page.locator("input[placeholder*='目的地']").first.fill(arrive_code)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)

            # 🔥 強勢點擊 (使用 JS 點擊最穩)
            print("🔍 觸發搜尋...")
            page.evaluate("window.scrollTo(0, 0)")
            page.evaluate("() => document.querySelector('[data-testid=\"search_btn\"]').click()")

            # 2. 監控結果 (這時網址應該會成功變成 /flights/...)
            print("📡 正在攔截 SSE 數據流...")
            for i in range(40):
                if result_data:
                    print("✨ 數據截獲成功！")
                    break
                # 只有在沒資料時才輕微滾動
                if i % 5 == 0:
                    page.mouse.wheel(0, 300)
                page.wait_for_timeout(1000)

            if not result_data:
                print(f"❌ 失敗。目前網址: {page.url}")
                page.screenshot(path="hidden_window_debug.png")

        except Exception as e:
            print(f"❌ 錯誤: {e}")
        finally:
            browser.close()

    return result_data

if __name__ == "__main__":
    data = fetch_flights_playwright("TPE", "TYO", "2026-04-01")
    if data:
        print("📊 資料抓取成功，第一筆價格：", data['itineraryList'][0]['policies'][0]['price']['totalPrice'])
    else:
        print("❌ 最終未能抓到資料，請觀察是否卡在驗證碼或 404")