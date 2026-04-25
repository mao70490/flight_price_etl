from etl.crawler import TripCrawler
from etl.transform import FlightDataTransformer
from datetime import datetime
from utils.file_helper import save_json
# from service import FlightService




if __name__ == "__main__":
    
    # service = FlightService()

    # service.run_etl(
    #     depart="TPE",
    #     arrive="TYO",
    #     date="2026-05-20"
    # )


    #-------------  測試資料是否成功捉取以及成功轉成df格式  -----------------
    crawler = TripCrawler(headless=False)
    transformer = FlightDataTransformer()

    outbound, ret = crawler.fetch("TPE", "LON", "2026-05-20")

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

    # 存 JSON
    save_json(outbound, f"outbound_test.json")
    save_json(ret, f"return_test.json")

    # 在根目錄執行 python -m etl.main
    #------------------------------------------------------------------