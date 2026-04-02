from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta


# 🔹 解析資料邏輯
def parse_flights(data, ddate, scrap_day): # 多傳入日期參數
    flights = []
    if not data or "itineraryList" not in data:
        return flights

    # 備援：從全局獲取幣別 (Trip.com 常見結構)
    global_currency = data.get("currency") or data.get("context", {}).get("currency", "TWD")

    for item in data.get("itineraryList", []):
        try:
            journey = item.get("journeyList", [{}])[0]
            sections = journey.get("transSectionList", [])
            if not sections: continue
            
            first_seg = sections[0]
            f_info = first_seg.get("flightInfo", {})
            
            # 安全取得價格
            policies = item.get("policies", [])
            price_info = policies[0].get("price", {}) if policies else {}

            # 優化：航空公司名稱取值邏輯
            # 優先順序：名稱 -> 代碼 -> 航班號前兩碼
            airline = (f_info.get("airlineName") or 
                       f_info.get("airlineCode") or 
                       f_info.get("flightNo")[:2] if f_info.get("flightNo") else "Unknown")

            flights.append({
                "search_date": ddate,
                "price": price_info.get("totalPrice"),
                "currency": price_info.get("currency") or global_currency, # 沒幣別就用全局的
                "airline": airline,
                "flight_no": f_info.get("flightNo"),
                "departure": first_seg.get("departDateTime"),
                "arrival": sections[-1].get("arriveDateTime"),
                "stops": len(sections) - 1
            })
        except Exception as e:
            print(f"⚠️ 出錯的資料: {item}")
            continue
    return flights