import os
import requests
import yfinance as yf

# ==========================================
# 1. 노션 및 깃허브 설정 (깃허브 금고에서 가져오기)
# ==========================================

from dotenv import load_dotenv
load_dotenv() # 내 컴퓨터에 .env 파일이 있으면 열어라!

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
# 💡 3. 야후 파이낸스에서 데이터 가져오기 (시가총액 + 단위 변환)
# ==========================================
def get_market_cap(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        raw_market_cap = stock.info.get("marketCap")
        
        if raw_market_cap:
            # 한국 주식인지 미국 주식인지 판별
            is_korea = ticker_symbol.endswith('.KS') or ticker_symbol.endswith('.KQ')
            
            if is_korea:
                # 한국 주식: 1억 단위로 나누고 소수점 버림
                scaled_cap = round(raw_market_cap / 100000000)
            else:
                # 미국 주식: 10억 달러(Billion) 단위로 나누고 소수점 2자리까지 표시
                scaled_cap = round(raw_market_cap / 1000000000, 2)
                
            return scaled_cap
        else:
            return None
            
    except Exception as e:
        print(f"❌ {ticker_symbol} 데이터 수집 실패: {e}")
        return None

# ==========================================
# 💡 4. 노션 페이지 업데이트 하기 (시가총액 전용)
# ==========================================
def update_notion_page(page_id, market_cap):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # 노션의 "시가총액" 열에 숫자 업데이트
    properties = {
        "시가총액": {"number": market_cap}
    }
    
    payload = {"properties": properties}
    
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"  ✅ 업데이트 성공! (시가총액: {market_cap})")
    else:
        print(f"  ❌ 업데이트 실패: {response.text}")

# ==========================================
# 💡 5. 메인 실행 함수
# ==========================================
def main():
    print("🚀 시가총액 데이터 업데이트 시작...")
    pages = get_notion_pages()
    
    if len(pages) == 0:
        print("⚠️ 노션 표에서 아무 데이터도 찾지 못했습니다!")
        return

    for page in pages:
        props = page.get("properties", {})
        
        # 종목코드 추출
        ticker_prop = props.get("종목코드", {}).get("rich_text", [])
        if not ticker_prop:
            continue
            
        ticker_symbol = ticker_prop[0].get("plain_text", "")
        print(f"\n🔍 [{ticker_symbol}] 시가총액 확인 중...")
        
        # 야후 파이낸스에서 시가총액 조회
        market_cap = get_market_cap(ticker_symbol)
        
        # 시가총액 데이터가 정상적으로 있다면 노션 업데이트
        if market_cap is not None:
            update_notion_page(page["id"], market_cap)
        else:
            print(f"  ⚠️ {ticker_symbol}의 시가총액 정보를 찾지 못했습니다.")

if __name__ == "__main__":
    main()