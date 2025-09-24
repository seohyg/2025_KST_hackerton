/*
 * 최종 개선 - 로드셀 3개용 변화 감지(Threshold) 방식 코드
 * [핵심 기능]
 * - 3개의 로드셀을 독립적으로 측정합니다.
 * - 설정된 문턱값(THRESHOLD) 이상의 큰 무게 변화가 발생할 때만 해당 로드셀의 무게를 출력합니다.
 * - 't' 입력 시 모든 로드셀의 영점을 동시에 재설정합니다.
 */

#include <HX711_ADC.h>

// --- 로드셀 1 설정 ---
const int DT1_PIN = 2;
const int SCK1_PIN = 3;
HX711_ADC LoadCell1(DT1_PIN, SCK1_PIN);
const float calFactor1 = 2939.31358; // 1번 로드셀의 보정값
const float THRESHOLD1 = 5.0;
float previousWeight1 = 0.0;

// --- 로드셀 2 설정 ---
const int DT2_PIN = 4;
const int SCK2_PIN = 5;
HX711_ADC LoadCell2(DT2_PIN, SCK2_PIN);
// !!! 중요: 2번 로드셀을 캘리브레이션하여 찾은 값으로 반드시 수정하세요 !!!
const float calFactor2 = 2939.31358; // 2번 로드셀의 보정값 (임시값)
const float THRESHOLD2 = 5.0;
float previousWeight2 = 0.0;

// --- 로드셀 3 설정 ---
const int DT3_PIN = 6;
const int SCK3_PIN = 7;
HX711_ADC LoadCell3(DT3_PIN, SCK3_PIN);
// !!! 중요: 3번 로드셀을 캘리브레이션하여 찾은 값으로 반드시 수정하세요 !!!
const float calFactor3 = 2939.31358; // 3번 로드셀의 보정값 (임시값)
const float THRESHOLD3 = 5.0;
float previousWeight3 = 0.0;


void setup() {
  Serial.begin(115200);
  Serial.println("========================================");
  Serial.println("로드셀 3개 무게 측정을 시작합니다.");
  Serial.println("'t'를 입력하면 모든 로드셀의 영점을 재설정합니다.");
  Serial.println("========================================");

  LoadCell1.begin();
  LoadCell2.begin();
  LoadCell3.begin();

  LoadCell1.start(2000, true);
  LoadCell2.start(2000, true);
  LoadCell3.start(2000, true);
  
  // 각 로드셀에 보정값 설정
  LoadCell1.setCalFactor(calFactor1);
  LoadCell2.setCalFactor(calFactor2);
  LoadCell3.setCalFactor(calFactor3);
  
  Serial.println(">> 측정을 시작합니다.");
  
  // 시작할 때의 초기 무게를 각 변수에 저장
  previousWeight1 = LoadCell1.getData();
  previousWeight2 = LoadCell2.getData();
  previousWeight3 = LoadCell3.getData();
}

void loop() {
  // 't'를 입력받아 모든 로드셀 영점 재설정
  if (Serial.available() > 0) {
    if (Serial.read() == 't') {
      LoadCell1.tare();
      LoadCell2.tare();
      LoadCell3.tare();
      Serial.println(">> 모든 로드셀의 영점을 재설정했습니다.");
      previousWeight1 = 0.0;
      previousWeight2 = 0.0;
      previousWeight3 = 0.0;
    }
  }

  // --- 로드셀 1 측정 ---
  if (LoadCell1.update()) {
    float currentWeight1 = LoadCell1.getData();
    if (abs(currentWeight1 - previousWeight1) > THRESHOLD1) {
      Serial.print("로드셀 1 무게: ");
      Serial.print(currentWeight1, 2);
      Serial.println(" g");
      previousWeight1 = currentWeight1;
    }
  }

  // --- 로드셀 2 측정 ---
  if (LoadCell2.update()) {
    float currentWeight2 = LoadCell2.getData();
    if (abs(currentWeight2 - previousWeight2) > THRESHOLD2) {
      Serial.print("로드셀 2 무게: ");
      Serial.print(currentWeight2, 2);
      Serial.println(" g");
      previousWeight2 = currentWeight2;
    }
  }

  // --- 로드셀 3 측정 ---
  if (LoadCell3.update()) {
    float currentWeight3 = LoadCell3.getData();
    if (abs(currentWeight3 - previousWeight3) > THRESHOLD3) {
      Serial.print("로드셀 3 무게: ");
      Serial.print(currentWeight3, 2);
      Serial.println(" g");
      previousWeight3 = currentWeight3;
    }
  }
}
