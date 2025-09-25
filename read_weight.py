# -*- coding: utf-8 -*-
import serial
import time

SERIAL_PORT = '/dev/ttyUSB0' # 시리얼 포트 이름
BAUD_RATE = 115200           # 보드레이트

def read_serial_data():
    """
    아두이노로부터 시리얼 데이터를 지속적으로 읽어와 한 줄씩 반환(yield)하는 제너레이터 함수.
    """
    ser = None # ser 변수 초기화
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"[{__name__}] 시리얼 포트({SERIAL_PORT})가 연결되었습니다.")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline()
                try:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line: # 빈 줄이 아니면
                        yield decoded_line # 데이터를 반환하고 잠시 대기
                except UnicodeDecodeError:
                    pass # 디코딩 오류는 무시

    except serial.SerialException as e:
        print(f"[{__name__}] 시리얼 포트를 열 수 없습니다: {e}")
    except KeyboardInterrupt:
        print(f"\n[{__name__}] 데이터 읽기를 중단합니다.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print(f"[{__name__}] 시리얼 포트 연결을 닫았습니다.")

# 이 파일을 직접 실행했을 때만 아래 코드가 동작 (테스트용)
if __name__ == "__main__":
    print("데이터 수신 테스트를 시작합니다. (Ctrl+C로 종료)")
    # read_serial_data() 함수를 호출하고, 반환되는 데이터를 한 줄씩 출력
    for data in read_serial_data():
        print(f"수신된 원본 데이터: {data}")