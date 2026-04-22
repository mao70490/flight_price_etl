from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta

class FlightExtractor:
    def __init__(self, depart_code, arrive_code, ddate):
        self.depart_code = depart_code.lower()
        self.arrive_code = arrive_code.lower()
        self.ddate = ddate
        self.raw_data = None

    def _build_url(self):
        depart_dt = datetime.strptime(self.ddate, "%Y-%m-%d")
        return_dt = (depart_dt + timedelta(days=2)).strftime("%Y-%m-%d")
        return (f"https://tw.trip.com/flights/showfarefirst?"
                f"dcity={self.depart_code}&acity={self.arrive_code}&"
                f"ddate={self.ddate}&rdate={return_dt}&triptype=rt&locale=zh-TW&curr=TWD")

    def extract(self):
        url = self._build_url()
        with sync_playwright() as p:
            # headless=False 先觀察一次，確認沒問題後再改 True
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            def handle_response(response):
                if "FlightListSearch" in response.url and response.status == 200:
                    try:
                        text = response.text()
                        for line in text.split("\n"):
                            if "data:" in line:
                                json_str = line.split("data:")[-1].strip()
                                self.raw_data = json.loads(json_str)
                    except: pass

            page.on("response", handle_response)
            page.goto(url, wait_until="domcontentloaded")
            
            for _ in range(20): # 等待攔截
                if self.raw_data: break
                page.wait_for_timeout(500)
            
            browser.close()
        return self.raw_data