/*
 * 최종 수정 - deque를 배열로 대체한 상태 머신 방식 코드
 * [변경점]
 * - 아두이노 환경에서 지원하지 않는 #include <deque>를 제거했습니다.
 * - 고정 크기 배열과 인덱스 변수를 사용하여 '최근 6개 값 저장' 기능을 직접 구현했습니다.
 */

#include <HX711_ADC.h>

// ========================[ 중요 설정 ]========================
const float TRIGGER_THRESHOLD = 10.0;
const int STABILITY_READINGS_COUNT = 6;
const float STABILITY_THRESHOLD = 1.0;
const long MEASUREMENT_INTERVAL = 250;
// =============================================================

enum LoadCellState { IDLE, MEASURING };

// --- 로드셀 1의 상태 변수 (deque 대신 배열 사용) ---
LoadCellState state1 = IDLE;
float lastStableWeight1 = 0.0;
float readings1[STABILITY_READINGS_COUNT];
int readingIndex1 = 0;
int readingCount1 = 0;
unsigned long lastMeasurementTime1 = 0;

// --- 로드셀 2의 상태 변수 ---
LoadCellState state2 = IDLE;
float lastStableWeight2 = 0.0;
float readings2[STABILITY_READINGS_COUNT];
int readingIndex2 = 0;
int readingCount2 = 0;
unsigned long lastMeasurementTime2 = 0;

// --- 로드셀 3의 상태 변수 ---
LoadCellState state3 = IDLE;
float lastStableWeight3 = 0.0;
float readings3[STABILITY_READINGS_COUNT];
int readingIndex3 = 0;
int readingCount3 = 0;
unsigned long lastMeasurementTime3 = 0;

// --- HX711 설정 ---
const int DT1_PIN = 2, SCK1_PIN = 3;
const int DT2_PIN = 4, SCK2_PIN = 5;
const int DT3_PIN = 6, SCK3_PIN = 7;
HX711_ADC LoadCell1(DT1_PIN, SCK1_PIN);
HX711_ADC LoadCell2(DT2_PIN, SCK2_PIN);
HX711_ADC LoadCell3(DT3_PIN, SCK3_PIN);
const float calFactor1 = 3241.130;
const float calFactor2 = -3239.660;
const float calFactor3 = 3307.355;

// 각 로드셀의 상태를 처리하는 함수 (deque 대신 배열과 인덱스 변수 사용)
void processLoadCell(int id, HX711_ADC &cell, LoadCellState &state, float &lastStableWeight, 
                     float readings[], int &readingIndex, int &readingCount, unsigned long &lastMeasurementTime) {
  if (!cell.update()) return;
  
  float currentWeight = cell.getData();

  if (state == IDLE) {
    if (abs(currentWeight - lastStableWeight) > TRIGGER_THRESHOLD) {
      Serial.print(">> 로드셀 "); Serial.print(id); Serial.println(": 측정 시작됨.");
      state = MEASURING;
      readingIndex = 0;
      readingCount = 0;
      // 배열을 0으로 초기화 (선택사항)
      for(int i=0; i<STABILITY_READINGS_COUNT; i++) { readings[i] = 0.0; }
      readings[readingIndex++] = currentWeight;
      readingCount++;
      lastMeasurementTime = millis();
    }
  } 
  else if (state == MEASURING) {
    if (millis() - lastMeasurementTime >= MEASUREMENT_INTERVAL) {
      lastMeasurementTime = millis();
      
      readings[readingIndex++] = currentWeight;
      if (readingIndex >= STABILITY_READINGS_COUNT) {
        readingIndex = 0; // 인덱스가 끝에 도달하면 처음으로 돌아감 (순환)
      }
      if (readingCount < STABILITY_READINGS_COUNT) {
        readingCount++;
      }

      if (readingCount == STABILITY_READINGS_COUNT) {
        float maxVal = readings[0], minVal = readings[0];
        float sum = 0;
        for (int i = 0; i < readingCount; i++) {
          if (readings[i] > maxVal) maxVal = readings[i];
          if (readings[i] < minVal) minVal = readings[i];
          sum += readings[i];
        }

        if (maxVal - minVal < STABILITY_THRESHOLD) {
          float stableWeight = sum / STABILITY_READINGS_COUNT;
          lastStableWeight = stableWeight;
          
          Serial.print("로드셀 "); Serial.print(id); Serial.print(" 무게: ");
          Serial.print(stableWeight, 2);
          Serial.println(" g");
          
          Serial.print(">> 로드셀 "); Serial.print(id); Serial.println(": 안정됨. 대기 상태로 전환.");
          state = IDLE;
        }
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("========================================");
  Serial.println("상태 머신 방식 측정을 시작합니다. (배열 Ver)");
  Serial.println("========================================");

  LoadCell1.begin(); LoadCell2.begin(); LoadCell3.begin();
  LoadCell1.start(2000, true); LoadCell2.start(2000, true); LoadCell3.start(2000, true);
  LoadCell1.setCalFactor(calFactor1); LoadCell2.setCalFactor(calFactor2); LoadCell3.setCalFactor(calFactor3);
  
  lastStableWeight1 = LoadCell1.getData();
  lastStableWeight2 = LoadCell2.getData();
  lastStableWeight3 = LoadCell3.getData();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "tare") {
      LoadCell1.tare(); LoadCell2.tare(); LoadCell3.tare();
      lastStableWeight1 = 0.0; lastStableWeight2 = 0.0; lastStableWeight3 = 0.0;
      state1 = IDLE; state2 = IDLE; state3 = IDLE;
      readingCount1 = 0; readingCount2 = 0; readingCount3 = 0;
      readingIndex1 = 0; readingIndex2 = 0; readingIndex3 = 0;
      Serial.println(">> 모든 로드셀 영점 재설정 및 상태 초기화.");
    }
  }

  processLoadCell(1, LoadCell1, state1, lastStableWeight1, readings1, readingIndex1, readingCount1, lastMeasurementTime1);
  processLoadCell(2, LoadCell2, state2, lastStableWeight2, readings2, readingIndex2, readingCount2, lastMeasurementTime2);
  processLoadCell(3, LoadCell3, state3, lastStableWeight3, readings3, readingIndex3, readingCount3, lastMeasurementTime3);
}
