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

## 단일 파렛트 동작 시연

실행:
```powershell
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/run_conveyor_demo.py
```

`Conveyor Demo - SIMULATED VISION` 창에서:
1. Start infeed: X=-750 mm에서 검사 위치 X=0으로 입고.
2. 2초 모의 검사 후 NG. 파렛트를 15 mm 들어 Y=1100 mm 버퍼로 이동 후 내려놓음.
3. 작업자 보완을 기다림. `Rework complete -> return` 버튼이 이때 활성화됨.
4. 버튼을 누르면 검사 위치로 복귀하고 2초 모의 재검사 후 OK.
5. X=750 mm 픽업 위치로 이동 후 정지. 이때 Pickup allowed=True.
6. Pause / Resume은 동작 정지/재개, Reset은 입구로 초기화.

실제 비전/AI 검사, 물리 접촉이나 모터 이송이 아닌 USD 위치 제어 데모다.
첫 검사 NG, 재검사 OK는 고정 시나리오이며 GUI에 명시한다.
한 대만 이송하므로 복귀 시 다른 파렛트와의 합류 제어는 아직 없다.
픽업 허용은 상태값만 표시하고 로봇 픽업은 수행하지 않는다.
횡이송 스트립의 승강은 단순 시각 표현이며 실제 기구 동작 검증이 아니다.
엔진/받침/파렛트는 상위 Xform으로 함께 움직이며 원본 USD는 세션 레이어로 보호한다.
Isaac Sim 타임라인 Play 대신 데모 창 버튼을 사용한다.

검증:
- `python -m unittest discover -s projects/engine-warehouse -p test_conveyor_cycle.py`
- `C:/isaacsim/python.bat projects/engine-warehouse/run_conveyor_demo.py --test`
  테스트 모드에서만 보완 완료 신호를 자동 입력하고 종료한다.
