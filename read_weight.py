#-*- coding: utf-8 -*-
import serial
import time

# 아두이노가 연결된 시리얼 포트와 보드레이트를 설정합니다.
# 포트 이름은 2단계에서 확인한 이름으로 바꿔주세요. (보통 /dev/ttyACM0 또는 /dev/ttyUSB0)
# 보드레이트는 아두이노 코드의 Serial.begin()에 있는 숫자와 반드시 같아야 합니다. (115200)
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    # 시리얼 포트가 안정적으로 열릴 때까지 잠시 대기
    time.sleep(2) 
    print("시리얼 포드가 연결 되었습니다")

    while True:
        # 시리얼 버퍼에 데이터가 있는지 확인
        if ser.in_waiting > 0:
            # 라인 단위로 데이터를 읽어옴 (아두이노에서 println으로 보냈기 때문)
            line = ser.readline()
            
            # byte 형태의 데이터를 utf-8 문자열로 변환하고, 양쪽 공백(줄바꿈 문자 등)을 제거
            try:
                decoded_line = line.decode('utf-8').strip()
                print(f"수신된 데이터: {decoded_line}")
            except UnicodeDecodeError:
                # 가끔 통신 시작 시 깨진 데이터가 들어오는 경우를 대비
                print("데이터 디코딩 오류, 무시합니다.")

except serial.SerialException as e:
    print(f"시리얼 포트를 열 수 없습니다: {e}")
except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("시리얼 포트 연결을 닫았습니다.")
