from playwright.sync_api import sync_playwright
import json, os
from transform import parse_flights_to_df
from datetime import datetime, timedelta


def fetch_flights_full_flow(depart_code, arrive_code, ddate):
    # 🔹 1. 計算回程日期
    depart_dt = datetime.strptime(ddate, "%Y-%m-%d")
    return_dt = (depart_dt + timedelta(days=2)).strftime("%Y-%m-%d")

    # 🔹 2. 組 URL
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

    outbound_data = None
    return_data = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 🔥 3. 監聽所有 response（核心）
        def handle_response(response):
            nonlocal outbound_data, return_data

            if response.status != 200:
                return

            try:
                url = response.url

                # 🟢 去程：SSE
                if "FlightListSearchSSE" in url:
                    text = response.text()

                    for line in text.split("\n"):
                        if "data:" in line:
                            data = json.loads(line.replace("data:", "").strip())

                            if data.get("itineraryList") and not outbound_data:
                                outbound_data = data
                                print("✅ 抓到去程")

                # 🔵 回程：一般 API
                elif "FlightListSearch" in url:
                    data = response.json()

                    if data.get("itineraryList") and not return_data:
                        return_data = data
                        print("✅ 抓到回程")

            except Exception as e:
                print("parse error:", e)

        page.on("response", handle_response)

        # 🔹 4. 進入搜尋頁（觸發去程 API）
        print("🔗 進入搜尋頁")
        page.goto(search_url, wait_until="domcontentloaded")

        # 🔹 5. 等去程資料
        for _ in range(30):
            if outbound_data:
                break
            page.wait_for_timeout(500)

        if not outbound_data:
            print("❌ 去程沒抓到")
            return None, None

        # 🔥 6. 點擊「選取」→ 觸發回程
        try:
            print("👉 點擊航班觸發回程")

            page.wait_for_selector('[data-testid="u_select_btn"]', timeout=10000)

            page.locator('[data-testid="u_select_btn"]').first.click()

        except Exception as e:
            print("❌ 點擊失敗:", e)
            return outbound_data, None

        # 🔹 7. 等回程資料
        for _ in range(30):
            if return_data:
                break
            page.wait_for_timeout(500)

        if not return_data:
            print("⚠️ 沒抓到回程")

        browser.close()

    return outbound_data, return_data


if __name__ == "__main__":
    # --- 測試設定區 ---
    test_depart = "TPE"      # 出發地
    test_arrive = "TYO"      # 目的地
    test_date = "2026-05-20" # 出發日期 (格式必須為 YYYY-MM-DD)
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(output_dir, exist_ok=True)
    # ------------------

    outbound, ret = fetch_flights_full_flow(test_depart, test_arrive, test_date)

    print("\n=== 測試結果 ===")

    if outbound:
        print(f"✅ 去程抓到：{len(outbound.get('itineraryList', []))} 筆")
        # with open(os.path.join(output_dir, "outbound.json"), "w", encoding="utf-8") as f:
        #     json.dump(outbound, f, ensure_ascii=False, indent=2)
        df_out = parse_flights_to_df(outbound, "outbound", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(df_out.head())

    else:
        print("❌ 去程失敗")

    if ret:
        print(f"✅ 回程抓到：{len(ret.get('itineraryList', []))} 筆")
        # with open(os.path.join(output_dir, "return.json"), "w", encoding="utf-8") as f:
        #     json.dump(ret, f, ensure_ascii=False, indent=2)
        df_ret = parse_flights_to_df(ret, "return", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(df_ret.head())

    else:
        print("❌ 回程失敗")