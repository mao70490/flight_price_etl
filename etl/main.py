from crawler import TripCrawler
from transform import FlightDataTransformer
from service import FlightService
from datetime import datetime


if __name__ == "__main__":
    crawler = TripCrawler(headless=False)
    transformer = FlightDataTransformer()

    outbound, ret = crawler.fetch("TPE", "TYO", "2026-05-20")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n=== Outbound 測試 ===")
    if outbound:
        df_out = transformer.parse_flights_to_df(outbound, "outbound", now)
        print(df_out.head())
        # print(df_out.columns)
    else:
        print("❌ outbound 抓不到")

    print("\n=== Return 測試 ===")
    if ret:
        df_ret = transformer.parse_flights_to_df(ret, "return", now)
        print(df_ret.head())
        # print(df_ret.columns)
    else:
        print("❌ return 抓不到")