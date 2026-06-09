import os
import requests
import yfinance as yf

# ==========================================
# 1. 노션 및 깃허브 설정 (깃허브 금고에서 가져오기)
# ==========================================
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ==========================================
# 2. 노션 데이터베이스 읽어오기
# ==========================================
def get_notion_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 노션 연결 실패! 에러: {response.text}")
        return []
    
    return response.json().get("results", [])

# ==========================================
# 3. 야후 파이낸스에서 데이터 가져오기 (주가 + 실적일)
# ==========================================
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. 현재 주가 가져오기
        current_price = stock.info.get("currentPrice") or stock.info.get("regularMarketPrice")
        
        # 2. 다음 실적 발표 예정일(Earnings Date) 가져오기
        earnings_date_str = ""
        calendar = stock.calendar
        
        if calendar is not None and len(calendar) > 0:
            try:
                if 'Earnings Date' in calendar:
                    first_date = calendar['Earnings Date'][0]
                    earnings_date_str = first_date.strftime("%Y-%m-%d")
            except Exception as e:
                pass
                
        return current_price, earnings_date_str
        
    except Exception as e:
        print(f"❌ {ticker_symbol} 데이터 수집 실패: {e}")
        return None, ""

# ==========================================
# 4. 노션 페이지 업데이트 하기
# ==========================================
def update_notion_page(page_id, price, earnings_date):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # 💡 노션 자체 '최종 편집 일시' 기능이 있으므로 파이썬 시간 계산 코드는 삭제함!
    # 오직 주가와 실적 발표일 데이터만 조립해서 보냅니다.
    properties = {
        "현재 주가": {"number": price}
    }
    
    # 실적 발표일 데이터가 있으면 속성에 추가
    if earnings_date:
         properties["실적 발표일"] = {
             "rich_text": [{"text": {"content": earnings_date}}]
         }

    payload = {"properties": properties}
    
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ 업데이트 성공! (주가: {price}, 실적일: {earnings_date})")
    else:
        print(f"❌ 업데이트 실패: {response.text}")

# ==========================================
# 5. 메인 실행 함수 (로봇 작동!)
# ==========================================
def main():
    print("🚀 주식 및 실적 데이터 업데이트 시작...")
    pages = get_notion_pages()
    
    for page in pages:
        props = page.get("properties", {})
        ticker_prop = props.get("종목 코드", {}).get("rich_text", [])
        
        if not ticker_prop:
            continue
            
        ticker_symbol = ticker_prop[0].get("plain_text", "")
        print(f"\n🔍 [{ticker_symbol}] 데이터 확인 중...")
        
        # 야후 파이낸스 조회
        price, earnings_date = get_stock_data(ticker_symbol)
        
        if price is not None:
            # 노션 업데이트
            update_notion_page(page["id"], price, earnings_date)

if __name__ == "__main__":
    main()