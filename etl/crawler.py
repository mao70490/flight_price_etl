from playwright.sync_api import sync_playwright
from transform import parse_flights_to_df
import json
from datetime import datetime, timedelta

def fetch_flights_by_url_logic(depart_code, arrive_code, ddate):
    # 1. 自動計算回程日期 (原本的邏輯)
    depart_dt_obj = datetime.strptime(ddate, "%Y-%m-%d")
    return_dt = (depart_dt_obj + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # 2. 根據你提供的樣板構造網址
    # 我們將 dcity, acity, ddate, rdate 替換成變數
    search_url = (
        f"https://tw.trip.com/flights/showfarefirst?"
        f"dcity={depart_code.lower()}&"
        f"acity={arrive_code.lower()}&"
        f"ddate={ddate}&"
        f"rdate={return_dt}&"
        f"triptype=rt&class=y&lowpricesource=searchform&"
        f"quantity=1&searchboxarg=t&nonstoponly=off&"
        f"locale=zh-TW&curr=TWD"
    )

    result_data = None

    with sync_playwright() as p:
        # headless=False 先觀察一次，確認沒問題後再改 True
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 監聽 Response (原本攔截 FlightListSearch 的邏輯)
        def handle_response(response):
            nonlocal result_data
            # 保持原本的攔截關鍵字
            if "FlightListSearch" in response.url and response.status == 200:
                try:
                    text = response.text()
                    for line in text.split("\n"):
                        if "data:" in line:
                            json_str = line.split("data:")[-1].strip()
                            data = json.loads(json_str)
                            if data.get("itineraryList"):
                                result_data = data

                                # --- 🚀 新增：Debug 存檔區 ---
                                # with open("flight_debug.json", "w", encoding="utf-8") as f:
                                #     json.dump(data, f, ensure_ascii=False, indent=4)
                                # print("💾 已將攔截到的原始數據存至 flight_debug.json")
                                # --------------------------
                except:
                    pass

        page.on("response", handle_response)

        try:
            print(f"🔗 正在直達搜尋結果頁...")
            
            # 直接跳轉，wait_until 使用 commit 或 domcontentloaded 即可，不用等 networkidle
            page.goto(search_url, wait_until="domcontentloaded")

            # 3. 監控與救援邏輯
            found_data = False
            for i in range(30): # 最多等 15 秒
                if result_data:
                    print(f"✅ 成功！在第 {i*0.5} 秒截獲數據")
                    found_data = True
                    break
                
                # 如果等了 5 秒都沒資料，檢查是否遇到驗證碼或軟 404
                if i == 10:
                    if "Robot Check" in page.title() or "驗證" in page.content():
                        print("🚨 遇到機器人驗證！請在視窗中手動點擊驗證...")
                        # 這裡可以暫停腳本等你手動點，或是直接報錯
                        # page.pause() 
                    else:
                        print("♻️ 數據未出現，執行一次輕微滾動觸發加載...")
                        page.mouse.wheel(0, 500)
                
                page.wait_for_timeout(500)

            if not found_data:
                print("❌ 最終未截獲數據。")

        except Exception as e:
            print(f"❌ 執行出錯: {e}")
        finally:
            # 調試時可先不關閉瀏覽器
            # browser.close()
            pass

    return result_data



if __name__ == "__main__":
    # --- 測試設定區 ---
    test_depart = "TPE"      # 出發地
    test_arrive = "TYO"      # 目的地
    test_date = "2026-05-20" # 出發日期 (格式必須為 YYYY-MM-DD)

    print("🚀 --- 開始執行 URL 構造法測試 ---")
    
    # 呼叫你的函式
    # 建議先確保 fetch_flights_by_url_logic 內部已經改成 page.goto(search_url) 邏輯
    final_result = fetch_flights_by_url_logic(test_depart, test_arrive, test_date)

    # --- 結果驗證區 ---
    print("\n--- 測試結果報告 ---")
    if final_result:
        df = parse_flights_to_df(final_result, ddate=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), scrap_day=test_date)

        print("✅ DataFrame 產生成功")
        print(df.head())
    else:
        print("❌ 測試失敗：未能攔截到 FlightListSearch 數據。")
        print("💡 建議：請檢查 headless 是否設為 False，觀察是否遇到了驗證碼。")