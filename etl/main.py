# from utils.file_helper import save_json
from service import FlightService




if __name__ == "__main__":
    
    service = FlightService()


    # -------------  測試資料是否成功轉成df格式  -----------------
    service.test_transform(
        depart="TPE",
        arrive="LON",
        date="2026-05-20"
    )
    # ---------------- 測試是否成功load進db ---------------------
    # service.run_etl(
    #     depart="TPE",
    #     arrive="TYO",
    #     date="2026-05-20"
    # )



    # 在根目錄執行 python -m etl.main
    