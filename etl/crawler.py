from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta


class TripCrawler:

    def __init__(self, headless=True):
        self.headless = headless

    def _build_url(self, depart_code, arrive_code, ddate, trip_type="rt", return_date=None):
        base_url = (
            f"https://tw.trip.com/flights/showfarefirst?"
            f"dcity={depart_code.lower()}&"
            f"acity={arrive_code.lower()}&"
            f"ddate={ddate}&"
            f"triptype={trip_type}&"
            f"class=y&lowpricesource=searchform&"
            f"quantity=1&searchboxarg=t&nonstoponly=off&"
            f"locale=zh-TW&curr=TWD"
        )

        # 只有 RT 才加 rdate
        if trip_type == "rt":
            if not return_date:
                depart_dt = datetime.strptime(ddate, "%Y-%m-%d")
                return_date = (depart_dt + timedelta(days=2)).strftime("%Y-%m-%d")

            base_url += f"&rdate={return_date}"

        return base_url

    def fetch(self, depart_code, arrive_code, ddate, trip_type="rt", return_date=None):
        search_url = self._build_url(depart_code, arrive_code, ddate, trip_type, return_date)

        outbound_data = None
        return_data = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            def handle_response(response):
                nonlocal outbound_data, return_data

                if response.status != 200:
                    return

                try:
                    url = response.url

                    # 🟢 去程（RT / OW 都會進來）
                    if "FlightListSearchSSE" in url:

                        if outbound_data:
                            return
                        
                        body = response.body()
                        text = body.decode("utf-8", errors="ignore")

                        for line in text.split("\n"):
                            if "data:" in line:
                                data = json.loads(line.replace("data:", "").strip())

                                if data.get("itineraryList") and not outbound_data:
                                    outbound_data = data
                                    print("✅ 抓到去程")

                    # 🔵 回程（只有 RT 才需要）
                    elif "FlightListSearch" in url:

                        if return_data:
                            return
                        
                        data = response.json()

                        if data.get("itineraryList") and not return_data:
                            return_data = data
                            print("✅ 抓到回程")

                except Exception as e:
                    print("parse error:", e)

            page.on("response", handle_response)

            print(f"🔗 進入搜尋頁 ({trip_type.upper()})")
            page.goto(search_url, wait_until="domcontentloaded")

            # 等去程（OW / RT 共用）
            for _ in range(30):
                if outbound_data:
                    break
                page.wait_for_timeout(500)

            if not outbound_data:
                print("❌ 去程沒抓到")
                return None 

            
            # RT 才需要點擊回程
            if trip_type == "rt":

                try:
                    page.wait_for_selector('[data-testid="u_select_btn"]', timeout=10000)
                    page.locator('[data-testid="u_select_btn"]').first.click()
                except Exception as e:
                    print("❌ 點擊失敗:", e)

                # 等回程
                for _ in range(30):
                    if return_data:
                        break
                    page.wait_for_timeout(500)

            browser.close()

        return {
            "trip_type": trip_type,
            "depart_date": ddate,
            "return_date": return_date,
            "outbound": outbound_data,
            "return": return_data
        }
    
    # 多日期 OW 抓取 (測試)
    def fetch_ow_range(self, depart, arrive, start_date, days=5):
        results = []

        start = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(days):
            ddate = (start + timedelta(days=i)).strftime("%Y-%m-%d")

            print(f"📅 OW 抓取: {ddate}")

            result = self.fetch(depart, arrive, ddate, trip_type="ow")

            if result:
                results.append(result)

        return results
    
    # 多日期 RT 抓取 (測試)
    def fetch_rt_range(self, depart, arrive, start_date, days=5, stay_days=3):
        results = []

        start = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(days):
            depart_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")

            for j in range(1, stay_days + 1):
                return_date = (start + timedelta(days=i + j)).strftime("%Y-%m-%d")

                print(f"📅 RT 抓取: {depart_date} → {return_date}")

                result = self.fetch(
                    depart,
                    arrive,
                    depart_date,
                    trip_type="rt",
                    return_date=return_date
                )

                if result:
                    results.append(result)

        return results