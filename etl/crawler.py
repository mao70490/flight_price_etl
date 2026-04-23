from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta


class TripCrawler:

    def __init__(self, headless=True):
        self.headless = headless

    def _build_url(self, depart_code, arrive_code, ddate):
        depart_dt = datetime.strptime(ddate, "%Y-%m-%d")
        return_dt = (depart_dt + timedelta(days=2)).strftime("%Y-%m-%d")

        return (
            f"https://tw.trip.com/flights/showfarefirst?"
            f"dcity={depart_code.lower()}&"
            f"acity={arrive_code.lower()}&"
            f"ddate={ddate}&"
            f"rdate={return_dt}&"
            f"triptype=rt&class=y&lowpricesource=searchform&"
            f"quantity=1&searchboxarg=t&nonstoponly=off&"
            f"locale=zh-TW&curr=TWD"
        )

    def fetch(self, depart_code, arrive_code, ddate):
        search_url = self._build_url(depart_code, arrive_code, ddate)

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

                    # 🟢 去程
                    if "FlightListSearchSSE" in url:
                        text = response.text()

                        for line in text.split("\n"):
                            if "data:" in line:
                                data = json.loads(line.replace("data:", "").strip())

                                if data.get("itineraryList") and not outbound_data:
                                    outbound_data = data
                                    print("✅ 抓到去程")

                    # 🔵 回程
                    elif "FlightListSearch" in url:
                        data = response.json()

                        if data.get("itineraryList") and not return_data:
                            return_data = data
                            print("✅ 抓到回程")

                except Exception as e:
                    print("parse error:", e)

            page.on("response", handle_response)

            print("🔗 進入搜尋頁")
            page.goto(search_url, wait_until="domcontentloaded")

            # 等去程
            for _ in range(30):
                if outbound_data:
                    break
                page.wait_for_timeout(500)

            if not outbound_data:
                print("❌ 去程沒抓到")
                return None, None

            # 點擊觸發回程
            try:
                page.wait_for_selector('[data-testid="u_select_btn"]', timeout=10000)
                page.locator('[data-testid="u_select_btn"]').first.click()
            except Exception as e:
                print("❌ 點擊失敗:", e)
                return outbound_data, None

            # 等回程
            for _ in range(30):
                if return_data:
                    break
                page.wait_for_timeout(500)

            browser.close()

        return outbound_data, return_data