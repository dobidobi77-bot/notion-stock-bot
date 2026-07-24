import os
import yfinance as yf
import requests

print("🚀 노션 시가총액 자동 업데이트 봇 가동!\n")

# ==========================================
# 🚨 1. 나의 노션 API 정보 입력 (필수)
# ==========================================
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ==========================================
# 💡 2. 노션에서 '종목코드' 읽어오기
# ==========================================
def get_notion_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    return response.json().get('results', [])

# ==========================================
# 💡 3. 노션의 '시가총액' 빈칸 채워넣기
# ==========================================
def update_notion_market_cap(page_id, scaled_market_cap):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # 노션의 '시가총액' 열(숫자형)에 변환된 단위를 덮어씁니다.
    data = {
        "properties": {
            "시가총액": {
                "number": scaled_market_cap
            }
        }
    }
    requests.patch(url, headers=headers, json=data)

# ==========================================
# 🚀 4. 메인 실행 로직 (단위 자동 변환 포함)
# ==========================================
def main():
    pages = get_notion_data()
    
    if not pages:
        print("🚨 노션에서 데이터를 찾을 수 없습니다. 설정 확인 요망.")
        return

    for page in pages:
        page_id = page['id']
        props = page['properties']
        
        # '종목코드' 열(제목 속성)에서 티커 추출
        try:
            ticker = props['종목코드']['title'][0]['plain_text']
        except (KeyError, IndexError):
            continue # 종목코드가 비어있으면 패스
            
        print(f"🔍 [{ticker}] 야후 파이낸스에서 시가총액 조회 중...")
        
        # yfinance로 원본 시가총액(marketCap) 가져오기
        stock = yf.Ticker(ticker)
        raw_market_cap = stock.info.get('marketCap')
        
        if raw_market_cap:
            # 🌟 핵심: 한국 주식인지 미국 주식인지 판별하여 단위 축소
            is_korea = ticker.endswith('.KS') or ticker.endswith('.KQ')
            
            if is_korea:
                # 한국 주식: 1억 단위로 나누고 소수점 버림 (정수)
                scaled_cap = round(raw_market_cap / 100000000)
                unit = "억 원"
            else:
                # 미국 주식: 10억 달러(Billion) 단위로 나누고 소수점 2자리까지 남김
                scaled_cap = round(raw_market_cap / 1000000000, 2)
                unit = "Billion 달러"
                
            # 변환된 숫자를 노션에 업데이트
            update_notion_market_cap(page_id, scaled_cap)
            print(f"  ✅ 업데이트 성공! 시가총액: {scaled_cap:,} {unit}")
        else:
            print(f"  ❌ {ticker}의 시가총액 정보를 찾지 못했습니다.")

if __name__ == "__main__":
    main()