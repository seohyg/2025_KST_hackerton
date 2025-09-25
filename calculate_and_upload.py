# -*- coding: utf-8 -*-
import pandas as pd
import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경 변수(API 키 등)를 불러옴
load_dotenv()

# ========================[ 설정 ]========================
# Supabase 연결 정보 (.env 파일에서 불러옴)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 원본 재고 스냅샷 데이터가 저장된 테이블
SOURCE_TABLE_NAME = "stockdata" 
# 판매량 계산 결과를 업로드할 테이블
TARGET_TABLE_NAME = "daily_inventory_consumption2"

# 로드셀 컬럼 이름과 DB 컬럼 이름 매핑
LOADCELL_DB_MAPPING = {
    "Loadcell_1": "caramel_syrup",
    "Loadcell_2": "coffee_beans",
    "Loadcell_3": "chocolate_powder"
}
# ========================================================

def calculate_and_upload_sales_from_db():
    """Supabase DB의 stockdata 테이블에서 데이터를 가져와 판매량을 계산하고,
       daily_inventory_consumption2 테이블에 직접 업로드합니다."""
    
    today = datetime.datetime.now()
    date_str_yyyy_mm_dd = today.strftime('%Y-%m-%d') # DB 쿼리용 날짜 형식

    # Supabase 클라이언트 생성
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # --- 1. 오늘 날짜의 재고 스냅샷 데이터 DB에서 가져오기 ---
    print(f"Supabase '{SOURCE_TABLE_NAME}' 테이블에서 '{date_str_yyyy_mm_dd}' 날짜의 데이터를 가져옵니다...")
    try:
        response = supabase.table(SOURCE_TABLE_NAME) \
                           .select('date, caramel_syrup, coffee_beans, chocolate_powder') \
                           .gte('date', f"{date_str_yyyy_mm_dd} 00:00:00") \
                           .lte('date', f"{date_str_yyyy_mm_dd} 23:59:59") \
                           .order('date', desc=False) \
                           .execute()
        
        db_data = response.data
        
        if not db_data:
            print(f"'{SOURCE_TABLE_NAME}' 테이블에 '{date_str_yyyy_mm_dd}' 날짜의 데이터가 없습니다.")
            return

        # DB 데이터를 Pandas DataFrame으로 변환
        df = pd.DataFrame(db_data)
        
        # 컬럼 이름을 Loadcell_X 형식으로 변환 (계산을 위해)
        df.rename(columns={
            "caramel_syrup": "Loadcell_1",
            "coffee_beans": "Loadcell_2",
            "chocolate_powder": "Loadcell_3"
        }, inplace=True)

        # 'date' 컬럼을 datetime 객체로 변환하여 정렬 확인 (선택 사항)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by='date', inplace=True)

        if len(df) < 2:
            print("DB에서 가져온 데이터가 부족하여 판매량을 계산할 수 없습니다.")
            return

        print(f"DB에서 '{len(df)}'개의 재고 스냅샷 데이터를 가져왔습니다.")

        # --- 2. 메모리에서 판매량 계산 ---
        loadcell_cols_for_calc = list(LOADCELL_DB_MAPPING.keys()) # ['Loadcell_1', 'Loadcell_2', 'Loadcell_3']
        sales_df = -df[loadcell_cols_for_calc].diff()
        sales_df = sales_df.clip(lower=0)
        daily_total_sales = sales_df.sum() # 하루치 총 판매량 (Pandas Series 형태)

        # --- 3. DB에 업로드할 데이터 준비 ---
        data_to_upload = {
            "date": date_str_yyyy_mm_dd, # 판매량은 날짜(YYYY-MM-DD) 기준
        }
        for loadcell_col, db_col_name in LOADCELL_DB_MAPPING.items():
            data_to_upload[db_col_name] = int(daily_total_sales.get(loadcell_col, 0))

        # --- 4. Supabase DB의 'daily_inventory_consumption2' 테이블에 업로드 ---
        print(f"'{TARGET_TABLE_NAME}' 테이블에 업로드할 데이터: {data_to_upload}")
        
        # 'date' 컬럼을 기준으로 데이터가 없으면 삽입(insert), 이미 존재하면 업데이트(update)
        response = supabase.table(TARGET_TABLE_NAME).upsert(data_to_upload, on_conflict='date').execute()
        
        if response.data:
             print(f"'{TARGET_TABLE_NAME}' 테이블에 계산된 판매량을 성공적으로 업로드(Upsert)했습니다.")
        else:
             print(f"'{TARGET_TABLE_NAME}' 테이블 업로드 중 에러가 발생했습니다:", response)

    except Exception as e:
        print(f"Supabase 연결, 데이터 조회 또는 업로드 중 오류 발생: {e}")


# --- 메인 프로그램 실행 ---
if __name__ == "__main__":
    calculate_and_upload_sales_from_db()