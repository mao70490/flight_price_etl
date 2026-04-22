import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.by import By # 用來定位元素 (By.ID, By.XPATH)
from selenium.webdriver.common.action_chains import ActionChains # 用來模擬滑鼠長按
from selenium.webdriver.support.ui import WebDriverWait # 用來動態等待
from selenium.webdriver.support import expected_conditions as EC # 用來判斷元素是否出現
import random, time


def scrape_skyscanner_debug(departure_date):
    driver = None
    options = uc.ChromeOptions()
    
    # 這些參數能增加在 Windows 上的啟動成功率
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--headless') # 除錯階段千萬別開

    try:
        print("1. 🚀 正在初始化 undetected_chromedriver...")
        # use_subprocess=True 是修復 Windows 閃退的關鍵
        driver = uc.Chrome(options=options, use_subprocess=True)
        # 【關鍵位置】在進入網頁前注入 Stealth 偽裝
        print("🛡️ 正在注入 Stealth 偽裝層...")
        stealth(driver,
            languages=["zh-TW", "zh", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        
        print(f"2. 🔗 準備跳轉至 Skyscanner (日期: {departure_date})...")
        target_url = f"https://www.skyscanner.com.tw/transport/flights/tpe/lax/{departure_date}/"
        driver.get(target_url)
        
        print("3. 👀 頁面已跳轉。請觀察是否有驗證碼，若有請手動處理。")
        print("程式將保持開啟 30 秒供你觀察...")
        
        # 這裡停留久一點，讓你檢查網頁元件
        time.sleep(15) 

        # 呼叫長按邏輯
        bypass_akamai(driver)

        # 長按完後，等待航班出現
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Ticket_')]")))



    except Exception as e:
        print(f"❌ 發生錯誤！錯誤型態: {type(e).__name__}")
        print(f"❌ 錯誤詳細訊息: {e}")
        
    finally:
        if driver:
            print("🛑 測試結束，正在關閉瀏覽器...")
            driver.quit()
        else:
            print("⚠️ Driver 未能成功建立，請檢查 Chrome 版本或防火牆設定。")



def bypass_akamai(driver):
    try:
        print("📦 正在偵測驗證視窗...")
        
        # 1. 增加一段強制等待，確保 iframe 穩定載入
        time.sleep(5) 
        
        # 2. 用 JS 尋找所有 iframe，並找出含有 px 關鍵字的
        # 這樣比用 Selenium 定位更不容易噴 Stacktrace
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        target_frame = None
        for frame in iframes:
            try:
                # 檢查 iframe 屬性，避開廣告或無用的框架
                src = frame.get_attribute("src")
                if src and ("akamai" in src or "captcha" in src or "px" in src):
                    target_frame = frame
                    break
            except:
                continue
        
        if target_frame:
            driver.switch_to.frame(target_frame)
            print("📥 已進入驗證層")
        else:
            print("⚠️ 未發現明確驗證層，嘗試原地搜尋...")

        # 3. 定位按鈕 (使用文字搜尋，這是最穩定的)
        wait = WebDriverWait(driver, 10)
        btn = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Press & Hold')]")))
        
        # 4. 【核心改進】改用 ActionChains 但減少多餘動作
        print("🖱️ 開始長按...")
        actions = ActionChains(driver)
        # 直接對元素按下，不移動座標（減少 offset 錯誤）
        actions.click_and_hold(btn).perform()
        
        # 模擬長按 6.5 秒 (Skyscanner 通常需要 5 秒以上)
        time.sleep(6.5)
        
        actions.release().perform()
        print("✅ 長按釋放！")
        
        # 5. 爬出 iframe
        driver.switch_to.default_content()
        time.sleep(2) # 等待網頁跳轉回搜尋結果

    except Exception as e:
        print(f"❌ 深度錯誤訊息: {e}")
        driver.switch_to.default_content()



if __name__ == "__main__":
    # 執行測試
    scrape_skyscanner_debug("260520")