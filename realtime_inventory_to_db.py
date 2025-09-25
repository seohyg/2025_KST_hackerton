# -*- coding: utf-8 -*-
import serial
import time
import datetime
import os
import csv # CSV 관련 함수는 이제 사용하지 않지만, 기본 임포트는 유지 (필요 시 제거 가능)

from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일에서 환경 변수(API 키 등)를 불러옴
load_dotenv()

# ========================[ 설정 ]========================
# 아두이노가 연결된 시리얼 포트
SERIAL_PORT = '/dev/ttyUSB0'  # 환경에 따라 /dev/ttyACM0 일 수 있음
BAUD_RATE = 115200

# Supabase 연결 정보 (.env 파일에서 불러옴)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "stockdata" # 첫 번째 코드에서 사용한 테이블 이름

# 로드셀 컬럼 이름
LOADCELL_COLS = {
    "Loadcell_1": "caramel_syrup",
    "Loadcell_2": "coffee_beans",
    "Loadcell_3": "chocolate_powder"
}
# ========================================================

# 프로그램이 실행되는 동안 모든 로드셀의 현재 상태를 저장할 변수
current_inventory = {
    'Loadcell_1': 0,
    'Loadcell_2': 0,
    'Loadcell_3': 0
}

# Supabase 클라이언트 생성 (메인 함수 밖에서 한 번만 생성)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_inventory_snapshot_to_db():
    """현재 재고 상태 전체를 DB에 한 줄 추가하는 함수"""
    
    timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    # DB에 삽입할 데이터 딕셔너리 생성
    data_to_upload = {
        "date": datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for loadcell_id, db_col_name in LOADCELL_COLS.items():
        data_to_upload[db_col_name] = int(current_inventory.get(loadcell_id, 0))

    print(f"DB에 업로드할 데이터: {data_to_upload}")
    
    try:
        # 데이터 삽입 (새로운 행을 추가하는 방식)
        response = supabase.table(TABLE_NAME).insert(data_to_upload).execute()
        
        if response.data:
             print("실시간 재고 스냅샷을 DB에 성공적으로 삽입했습니다.")
        else:
             print("DB 삽입 중 에러가 발생했습니다:", response)

    except Exception as e:
        print(f"Supabase 연결 또는 삽입 중 오류 발생: {e}")

def parse_and_process(line):
    """아두이노 신호를 분석하여 재고 상태를 업데이트하고 DB에 업로드하는 함수"""
    global current_inventory
    try:
        if line.startswith("로드셀"):
            parts = line.split(":")
            cell_id_str = f"Loadcell_{parts[0].split(' ')[1]}"
            
            weight_str = parts[1].strip().split(" ")[0]
            rounded_weight = int(round(float(weight_str)))

            if cell_id_str in current_inventory and current_inventory[cell_id_str] != rounded_weight:
                current_inventory[cell_id_str] = rounded_weight
                # 재고 변화가 감지되면 즉시 DB에 업로드
                upload_inventory_snapshot_to_db()

    except (ValueError, IndexError):
        pass

# --- 메인 프로그램 ---
if __name__ == "__main__":
    print("재고 스냅샷 실시간 DB 업로드를 시작합니다. (Ctrl+C로 종료)")
    
    # Supabase 클라이언트가 제대로 초기화되었는지 확인
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("경고: Supabase URL 또는 KEY가 .env 파일에 설정되지 않았습니다.")
        exit()

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # 아두이노 초기화 시간 대기
        print(f"아두이노와 {SERIAL_PORT} 포트로 연결되었습니다.")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    parse_and_process(line)

    except serial.SerialException as e:
        print(f"시리얼 포트를 열 수 없습니다: {e}")
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("시리얼 포트 연결을 닫았습니다.")