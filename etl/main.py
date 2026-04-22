import os, json, time, random
from datetime import datetime, timedelta
from crawler import fetch_flights_by_url_logic
from transform import parse_flights

# 🔹 批次抓取邏輯
def batch_search(depart, arrive, day_count):
    scrap_day = datetime.now().strftime("%Y-%m-%d")
    # Trip.com 預設通常從 +2 天開始比較穩
    start_dt = datetime.now() + timedelta(days=3)
    all_results = []

    for i in range(day_count):
        current_dt = start_dt + timedelta(days=i)
        date_str = current_dt.strftime("%Y-%m-%d")
        
        print(f"\n📅 [{i+1}/{day_count}] 正在搜尋起飛日期: {date_str}")
        
        raw_data = fetch_flights_by_url_logic(depart, arrive, date_str)
        day_flights = parse_flights(raw_data, date_str, scrap_day)
        
        if day_flights:
            print(f"💰 成功！抓到 {len(day_flights)} 筆航班")
            all_results.extend(day_flights)
        else:
            print(f"❌ {date_str} 抓取失敗")
            
        # 隨機休息，模擬真人行為 (開發測試可設短一點，生產環境建議 10-20秒)
        if i < day_count - 1:
            sleep_time = random.uniform(5, 8)
            print(f"😴 休息 {round(sleep_time, 1)} 秒後繼續...")
            time.sleep(sleep_time)
    
    return all_results

# 🔹 執行進入點
if __name__ == "__main__":
    # --- 配置區 ---
    DEPART_CITY = "TPE"
    ARRIVE_CITY = "TYO"
    TEST_DAYS = 1  # 測試階段先抓 3 天份
    # --------------

    print(f"🚀 ETL 啟動 | 航線: {DEPART_CITY} -> {ARRIVE_CITY} | 預計抓取 {TEST_DAYS} 天份")
    
    final_data = batch_search(DEPART_CITY, ARRIVE_CITY, TEST_DAYS)

    if final_data:
        # 儲存結果
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        output_dir = os.path.join(BASE_DIR, "data")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(
            output_dir,
            f"flight_data_{DEPART_CITY}_{ARRIVE_CITY}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        
        print("\n" + "="*30)
        print(f"✅ 所有任務完成！")
        print(f"📊 總計抓取筆數: {len(final_data)}")
        print(f"💾 檔案已儲存至: {output_file}")
    else:
        print("\n❌ 最終未獲得任何資料，請檢查網路或反爬蟲機制。")