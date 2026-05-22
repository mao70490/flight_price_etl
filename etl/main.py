# from utils.file_helper import save_json
from etl.service import FlightService
from config.dbconfig import DB_CONN_STR




if __name__ == "__main__":
    
    service = FlightService(DB_CONN_STR)

    # ---------------- 測試來回是否成功load進db ---------------------
    # service.run(
    #     depart="TPE",
    #     arrive="LON",
    #     ddate="2026-06-20",
    #     trip_type="rt"
    # )
    # # ---------------- 測試單程是否成功load進db ---------------------
    # service.run(
    #     depart="TPE",
    #     arrive="LON",
    #     ddate="2026-06-20",
    #     trip_type="ow"
    # )
    # --------------------- RT 多日期搜尋 ---------------------------
    service.run_rt_range(
        depart="TPE",
        arrive="LON",
        start_date="2026-07-20",
        days=5,
        stay_days=3
    )

    # --------------------- OW 多日期搜尋 ---------------------------
    # service.run_ow_range(
    #     depart="TPE",
    #     arrive="LON",
    #     start_date="2026-07-20",
    #     days=5
    # )



    # 在根目錄執行 python -m etl.main
    