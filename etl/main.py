# from utils.file_helper import save_json
from etl.service import FlightService
from config.dbconfig import DB_CONN_STR




if __name__ == "__main__":
    
    service = FlightService(DB_CONN_STR)


    # -------------  測試資料是否成功轉成df格式  -----------------
    # service.test_transform(
    #     depart="TPE",
    #     arrive="LON",
    #     date="2026-05-20"
    # )
    # ---------------- 測試是否成功load進db ---------------------
    service.run(
        depart="TPE",
        arrive="LON",
        ddate="2026-05-20"
    )



    # 在根目錄執行 python -m etl.main
    