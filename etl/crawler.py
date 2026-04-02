from playwright.sync_api import sync_playwright
import json
import time
import random
from datetime import datetime, timedelta

def fetch_flights_playwright(depart_code, arrive_code, ddate, return_dt):
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

# 🔹 解析資料邏輯 (保持不變)
def parse_flights(data, ddate, scrap_day): # 多傳入日期參數
    flights = []
    if not data or "itineraryList" not in data:
        return flights

    # 備援：從全局獲取幣別 (Trip.com 常見結構)
    global_currency = data.get("currency") or data.get("context", {}).get("currency", "TWD")

    for item in data.get("itineraryList", []):
        try:
            journey = item.get("journeyList", [{}])[0]
            sections = journey.get("transSectionList", [])
            if not sections: continue
            
            first_seg = sections[0]
            f_info = first_seg.get("flightInfo", {})
            
            # 安全取得價格
            policies = item.get("policies", [])
            price_info = policies[0].get("price", {}) if policies else {}

            # 優化：航空公司名稱取值邏輯
            # 優先順序：名稱 -> 代碼 -> 航班號前兩碼
            airline = (f_info.get("airlineName") or 
                       f_info.get("airlineCode") or 
                       f_info.get("flightNo")[:2] if f_info.get("flightNo") else "Unknown")

            flights.append({
                "search_date": ddate,
                "price": price_info.get("totalPrice"),
                "currency": price_info.get("currency") or global_currency, # 沒幣別就用全局的
                "airline": airline,
                "flight_no": f_info.get("flightNo"),
                "departure": first_seg.get("departDateTime"),
                "arrival": sections[-1].get("arriveDateTime"),
                "stops": len(sections) - 1
            })
        except Exception as e:
            print(f"⚠️ 出錯的資料: {item}")
            continue
    return flights

# 🔹 批次抓取邏輯
def batch_search(depart, arrive, day_count):
    scrap_day = datetime.now().strftime("%Y-%m-%d")
    # Trip.com 預設通常從 +2 天開始比較穩
    start_dt = datetime.now() + timedelta(days=2)
    all_results = []

    for i in range(day_count):
        current_dt = start_dt + timedelta(days=i)
        date_str = current_dt.strftime("%Y-%m-%d")
        
        print(f"\n📅 [{i+1}/{day_count}] 正在搜尋起飛日期: {date_str}")
        
        raw_data = fetch_flights_playwright(depart, arrive, date_str)
        day_flights = parse_flights(raw_data, date_str, scrap_day)
        
        if day_flights:
            print(f"💰 成功！抓到 {len(day_flights)} 筆航班")
            all_results.extend(day_flights)
        else:
            print(f"❌ {date_str} 抓取失敗")
            
        # 隨機休息，模擬真人行為 (開發測試可設短一點，生產環境建議 10-20秒)
        if i < day_count - 1:
            sleep_time = random.uniform(5, 8)
            print(f"😴 休息 {round(sleep_time, 1)} 秒後繼續...")
            time.sleep(sleep_time)
    
    return all_results

# 🔹 執行進入點
if __name__ == "__main__":
    # --- 配置區 ---
    DEPART_CITY = "TPE"
    ARRIVE_CITY = "TYO"
    TEST_DAYS = 3  # 測試階段先抓 3 天份
    # --------------

    print(f"🚀 ETL 啟動 | 航線: {DEPART_CITY} -> {ARRIVE_CITY} | 預計抓取 {TEST_DAYS} 天份")
    
    final_data = batch_search(DEPART_CITY, ARRIVE_CITY, TEST_DAYS)

    if final_data:
        # 儲存結果
        output_file = f"flight_data_{DEPART_CITY}_{ARRIVE_CITY}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        
        print("\n" + "="*30)
        print(f"✅ 所有任務完成！")
        print(f"📊 總計抓取筆數: {len(final_data)}")
        print(f"💾 檔案已儲存至: {output_file}")
    else:
        print("\n❌ 最終未獲得任何資料，請檢查網路或反爬蟲機制。")