# 인라인 파렛트 외형 초안

사용자 경험: 라운딩된 정사각형 금속 플레이트, 약 800 × 800 mm,
두께 15–20 mm. 대화에서 800 × 800 × 20 mm, 모서리 R50 mm를 승인했다.

- 파일: `assets/inline_pallet.usda`, 단위 m, Z-up.
- X/Y 범위 -0.4~0.4 m, 바닥 Z=0, 상면 Z=0.02 m.
- R50은 평면 모서리 반경이며 두께 방향 모서리는 직각이다.
- 원호는 코너당 16개 직선 구간으로 근사했다.
- 금속 외관용 재질만 적용했다. 특정 금속 등급/강도/질량을 가정하지 않는다.
- 받침, 위치결정 핀, 구멍, 충돌과 물리 설정은 다음 승인 단계다.
- 엔진 비교 배치는 XY 외곽 중심을 맞추고 최저점을 플레이트 상면에 맞춘다.
  이 배치는 크기 비교용이며 실제 엔진 지지 방법을 의미하지 않는다.

실행:

```powershell
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/build_inline_pallet.py
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/preview_engine.py --pallet
```

비교 장면은 로컬 `external_assets/engines/caterham_duratec/usd/engine_pallet_preview.usda`에 저장한다.
엔진 파일은 Git에 포함하지 않는다. 장면의 참조 경로는 현재 로컬 작업 경로를 사용한다.

검증: 외곽 800 × 800 × 20 mm, 폐곡면의 각 모서리 공유 횟수 2,
외향 면 방향 및 체적을 분석값과 비교(상대오차 0.1% 미만).

## 승인된 3점 지지 외형 (2026-09-30)

- A(-220,+100), B(-220,-100), C(+180,0) mm; 엔진 외곽 XY 중심 기준.
- 지지 기둥 Ø50 × 100 mm, 플레이트 상면 Z=20 mm부터 시작.
- 상단 핀 Ø16 × 돌출20 mm. 끝 5 mm는 Ø8까지 테이퍼.
- 가상 받침부의 아래쪽 막힌 홀 Ø18 × 깊이25 mm.
- 받침부 외경 Ø64는 표현용 구현값. 엔진 최저점을 Z=150 mm에 배치하고
  각 위치의 중심 수직선에서 처음 만나는 엔진 표면까지 연결 길이를 조정했다.
- 연결 상단은 해당 표면에 3 mm 겹쳐 외형상 연결을 표현한다.
  전체 받침부와 엔진의 정밀 간섭/강도/무게중심 검증은 하지 않았다.
- 받침부는 금색, 파렛트 측 기둥핀은 회색. 실물 생산라인 홀 재현이 아닌 가상 어댑터다.
- 핀-홀 반경 여유 1 mm, 핀 끝-홀 바닥 여유 5 mm.
- 충돌, 강체, 고정 조인트는 아직 적용하지 않았다.
- 엔진과 받침부는 현재 별도 시각 요소다. 향후 집기 구현 시 함께 움직이도록 묶어야 한다.

생성 및 미리보기:

```powershell
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/build_support_fixture.py
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/preview_engine.py --stage C:/IssacsimProject/Issacsim/external_assets/engines/caterham_duratec/usd/engine_supported_preview.usda
```

검증: 생성한 6개 메시의 폐곡면/외향 방향, USD 참조 및 Isaac Sim 화면 표시 확인.
