# 학습 기록

## 프로젝트 시작
- 준비한 것: 저장소 안내, 환경 기록 양식, 첫 실습 안내.
- 아직 확인하지 않은 것: Isaac Sim 설치·실행, 장면 생성 및 재실행.
- 다음 행동: 환경 기록 후 exercises/01-static-cell/README.md 진행.

## 매 실습 기록 양식
아래 양식을 복사해 날짜별로 추가합니다.

### YYYY-MM-DD — 실습 제목
- 목표:
- 사용 버전:
- 변경한 파일:
- 실행 방법:
- 예상 결과:
- 실제 결과:
- 확인한 증거(로그/이미지/수치):
- 오류와 해결:
- 배운 개념:
- 다음 행동:
- 상태: 작성만 완료 / 실행 확인 / 완료 기준 충족

## 2026-09-20 — 첫 실습 준비
- 작업 폴더: C:\IssacsimProject\Issacsim
- GitHub main 동기화 확인, 시작 시 로컬 변경 없음.
- Isaac Sim Full 6.1.0 프로세스와 창 제목 확인.
- 다음 행동: 정적 셀을 직접 구성하고 저장·재열기 확인.
- 상태: 환경 확인. 장면 실습 미완료.
## 2026-09-20 — 정적 셀 저장 및 파일 검증
- 사용자 작업: Supply, Fixture, Output을 만들고 static-cell.usd로 저장.
- 검증: OpenUSD API로 저장 파일을 열어 메타데이터, Mesh 정점, 변환을 확인.
- 단위: metersPerUnit=1, upAxis=Z. World/Cell의 변환은 기본값.
- Supply: 중심 (-1.2, 0, 0.4), 크기 (0.8, 0.6, 0.8)m.
- Fixture: 중심 (0, 0, 0.4), 크기 (0.6, 0.6, 0.8)m.
- Output: 중심 (1.2, 0, 0.4), 크기 (0.8, 0.6, 0.8)m.
- 각 Mesh 원본은 축별 -0.5~0.5 범위이며 Scale 적용 후 세 물체의 바닥은 Z=0.
- 파일 형식: USDC 바이너리(.usd). 오류가 아니며 원본을 그대로 보존.
- 상태: 파일 구조·치수 확인 완료. Isaac Sim에서 재열기 및 좌표계 실험은 아직 미확인.
- 다음 행동: Cell의 Translate X를 1로 바꾸고 자식 로컬 좌표와 월드 위치 비교.
## 2026-09-21 — 첫 실습 완료
- 사용자 보고: 부모 이동·회전 실험, 원상복구 및 저장·재열기 실습 완료.
- 파일 검증: Cell 위치 (0,0,0), 회전 identity. 세 물체의 중심과 회전이 기준 배치로 복구됨.
- 다음 실습: Script Editor에서 현재 Stage와 Prim을 Python으로 읽고 위치 속성 조작.
- 다음 실습 실행 상태: 아직 실행 전.
## 2026-09-21 — 학습 종료 및 다음 작업 인계

### 오늘 확인한 내용
- 정적 셀 좌표 실습 이후 Script Editor의 Prim 조회, 속성 읽기/쓰기, 배치 간격 변경을 학습.
- Franka 공식 pick/place 실행에서 Done picking and placing 확인. 프로젝트 복사본은 완료 후 일시정지·창 유지로 수정됨.
- Hello Robot(Jetbot): 로봇 로딩, 바퀴 속도 제어, 좌우 속도 차이, 관절 이름으로 인덱스 선택을 실습. 사용자가 정상 동작 확인.
- 실제 앱 로그에서 Joint names=['left_wheel_joint', 'right_wheel_joint'], Wheel indices=[0 1], Number of DOFs=2 확인.
- Console의 Info 필터가 꺼져 print 출력이 숨겨졌던 문제 해결; 사용자 확인 완료.
- Python 학습: self와 인스턴스 속성, 메서드/콜백, print/f-string, list와 NumPy 배열, .numpy() 변환.

### 다음 세션 시작점
1. 프로젝트의 projects/franka-cell/pick_place.py를 읽어 현재 변경 상태 확인.
2. main()의 pick=(0.45, 0.0, 0.025), place=(0.45, 0.35, 0.025)를 찾아 의미 설명.
3. 기준 동작을 확인한 뒤 목표 위치 한 항목만 작게 바꾸고 실행 결과 비교. 도달·파지 성공은 직접 확인하며 단정하지 않음.
4. 이후 공급대·치구·배출대를 로봇 도달 범위에 맞춰 추가하고 투입→처리→배출 프로젝트로 확장.
- 기존 기초 조작을 처음부터 반복하지 말 것. 실제 포트폴리오 제작과 연결해 한 단계씩 지도.
- 각 단계마다 공식 문서의 위치와 사용자 프로젝트 파일을 명확히 구분해 안내.
- 사용자는 C#과 비교한 Python 문법 설명을 선호하며 Python은 초보 수준.

### 실행 및 주의사항
- 작업 폴더: C:\IssacsimProject\Issacsim
- 저장소: https://github.com/BillionChild/Issacsim
- 실행: C:\isaacsim\python.bat C:\IssacsimProject\Issacsim\projects\franka-cell\pick_place.py --robot franka
- 위 Franka 스크립트는 독립 실행용이며 Script Editor에 그대로 붙여넣지 않음.
- Hello Robot은 설치 폴더의 hello_world.py에서 학습함. hello_world_extension.py는 예제 등록용; 잘못 들어간 실습 코드를 백업하고 공식 v6.1.0 등록 파일로 복원했음.
- 수정 후 저장과 확장 재로드가 필요. LOAD만으로 코드 재로드를 보장하지 않음.
- set_dof_velocity_targets 중복 호출을 제거하도록 안내함; 실제 파일 수정 여부는 다음에 확인.
- 로컬 미커밋 장면: exercises/01-static-cell/static-cell.usd, exercises/02-robot-move.usd, exercises/jetbot_edit.usd. 이 세 장면은 이번 기록 커밋에 포함하지 않았으며 검증 후 관리할 것.
- 오늘은 사용자 요청으로 종료. 다음 작업을 자동 실행하거나 예약하지 않음.
