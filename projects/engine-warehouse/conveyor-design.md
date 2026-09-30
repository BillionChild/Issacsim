# 입고 컨베이어 외형

- 승인 범위: 메인 롤러 + 측면 NG 보완 버퍼 1자리. 보완 후 메인 검사 위치로 복귀.
- 메인: 길이 2400 mm, 롤러 유효폭900 mm, 상단높이700 mm, Ø60/pitch100 mm.
- 메인 이송 +X. 엔진 파렛트는 X=0,Y=0 검사 위치에 정지한 외형.
- 측면 버퍼: +Y 방향, 중심 Y=1100 mm, 롤러 11개(중심 Y600~1600).
- 버퍼 파렛트 중심 Y1100에서 800 mm 파렛트는 Y700~1500을 차지한다.
- 검사 위치 북측 프레임/가이드를 분할하여 측면 출입 공간 확보.
- 횡이송 장치는 롤러 사이의 내려간 스트립으로 단순 표현. 벨트/승강 구동 및 실제 기구 검증 미구현.
- 빈 버퍼에는 엔진이나 파렛트를 추가하지 않았다. 기존 엔진+지지부+파렛트를 700 mm 높여 참조했다.
- 비전 카메라 모델/검사 알고리즘, 로봇, 센서, 물리, 무게 검증, 이송 동작은 포함하지 않는다.
- 흐름: 입고→비전→OK 픽업 / NG 측면→보완 완료 신호→검사 자리 비었을 때 복귀→재검사.

생성: `C:/isaacsim/kit/python/python.exe projects/engine-warehouse/build_inlet_conveyor.py`
미리보기: `preview_engine.py --stage`에 로컬 `external_assets/engines/caterham_duratec/usd/inlet_conveyor_preview.usda` 지정.
