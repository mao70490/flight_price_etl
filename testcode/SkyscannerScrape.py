import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

def scrape_skyscanner(departure_date):
    """
    departure_date 格式: '260520' (YYMMDD)
    """
    driver = None
    options = uc.ChromeOptions()
    
    # 這裡可以加入更多偽裝參數
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-authorizing')
    options.add_argument('--password-store=basic')
    
    try:
        print(f"🚀 正在啟動受保護的瀏覽器 (目標日期: {departure_date})...")
        driver = uc.Chrome(options=options)
        
        # 構建 URL (TPE -> HKD)
        url = f"https://www.skyscanner.com.tw/transport/flights/tpe/hkd/{departure_date}/?adults=1&rtn=0&cabinclass=economy"
        
        driver.get(url)
        
        # --- 反爬關鍵點：人工驗證緩衝 ---
        print("💡 觀察瀏覽器：如果出現『長按驗證』，請手動按住它。")
        print("等待資料載入中 (最長等待 40 秒)...")
        
        # 使用更具韌性的 XPath：搜尋包含 'Ticket_itinerary' 的 div
        # Skyscanner 的 class 名稱常變動，用 contains 比較安全
        card_xpath = "//div[contains(@class, 'Ticket_itineraryDataContainer')]"
        
        wait = WebDriverWait(driver, 40)
        wait.until(EC.presence_of_element_located((By.XPATH, card_xpath)))
        
        # 成功過關後，稍微多等一下讓價格跑完
        time.sleep(random.uniform(3, 5))
        
        # --- 解析資料 ---
        flights_data = []
        # 抓取所有航班容器
        cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'FlightsTicket_container')]")
        
        print(f"✅ 成功擷取！偵測到 {len(cards)} 個航班資訊。")
        
        for card in cards:
            try:
                # 航空公司 (從 img 的 alt 屬性抓取)
                airline = card.find_element(By.XPATH, ".//img[contains(@class, 'Logo_airlineLogo')]").get_attribute("alt")
                # 價格
                price_str = card.find_element(By.XPATH, ".//div[contains(@class, 'Price_mainPriceContainer')]").text
                # 時間 (通常會有出發跟抵達，我們抓第一個)
                times = card.find_elements(By.XPATH, ".//span[contains(@class, 'LegInfo_routeTime')]")
                dep_time = times[0].text if times else "N/A"
                
                # 清洗價格文字 (只留數字)
                clean_price = "".join(filter(str.isdigit, price_str))
                
                flights_data.append({
                    "日期": departure_date,
                    "航空公司": airline,
                    "出發時間": dep_time,
                    "價格": clean_price
                })
            except Exception as e:
                # 單一航班解析失敗則跳過，不影響整份報告
                continue

        # --- 儲存資料 ---
        if flights_data:
            df = pd.DataFrame(flights_data)
            filename = f"skyscanner_{departure_date}.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"💾 資料已儲存至: {filename}")
            print(df.head())
        else:
            print("⚠️ 雖然頁面載入成功，但未抓取到任何航班內容。")

    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        # 如果報錯了，不要立刻關掉，讓你檢查網頁長怎樣
        time.sleep(10)
        
    finally:
        if driver:
            print("🛑 關閉瀏覽器。")
            driver.quit()

if __name__ == "__main__":
    # 測試執行
    test_date = "260520" # 2026年5月20日
    scrape_skyscanner(test_date)