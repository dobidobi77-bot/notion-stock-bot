import yfinance as yf
import requests

# ==========================================
# 1. 노션 API 출입증 설정 (여기에 복사한 값 붙여넣기!)
# ==========================================
NOTION_TOKEN = "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"
DATABASE_ID = "36eca601b534809abf18c65802a03a97"  # 노션 데이터베이스 ID (URL에서 복사한 긴 문자열)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # 노션 API 버전
}

# ==========================================
# 2. 노션 데이터베이스 읽어오기 (표 전체 스캔)
# ==========================================
def get_notion_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ 노션 연결 실패! 권한이나 ID를 확인하세요: {response.text}")
        return []
    
    return response.json().get("results", [])

# ==========================================
# 3. 노션 '현재 주가' 칸 업데이트 (데이터 쏘기)
# ==========================================
def update_notion_price(page_id, current_price):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # 노션의 '현재 주가' 열에 숫자를 덮어쓰는 명령
    data = {
        "properties": {
            "현재 주가": {
                "number": current_price
            }
        }
    }
    response = requests.patch(url, headers=HEADERS, json=data)
    
    if response.status_code == 200:
        print("   ✅ 노션 업데이트 완료!")
    else:
        print(f"   ❌ 업데이트 실패: {response.text}")

# ==========================================
# 4. 🚀 메인 실행 봇 작동!
# ==========================================
print("🤖 노션 주식 봇 작동을 시작합니다...\n")
pages = get_notion_pages()

for page in pages:
    page_id = page["id"]
    props = page["properties"]
    
    try:
        # 노션 표에서 '종목코드'와 '주식 종목 이름' 읽어오기
        ticker = props["종목코드"]["rich_text"][0]["text"]["content"]
        name = props["종목"]["title"][0]["text"]["content"]
    except (KeyError, IndexError):
        # 종목코드가 비어있는 줄은 건너뜁니다.
        continue
    
    print(f"🔍 [{name}] ({ticker}) 주가 확인 중...")
    
    try:
        # yfinance로 실시간 주가 긁어오기
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        print(f"   💰 현재가: {price:,.2f}")
        
        # 가져온 주가를 노션에 쏘기
        update_notion_price(page_id, price)
        
    except Exception as e:
        print(f"   ⚠️ 주가를 가져오는 데 실패했습니다 (티커 확인 요망): {e}")

print("\n🎉 모든 작업이 끝났습니다! 지금 바로 노션을 켜서 확인해 보세요!")