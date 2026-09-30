# FANUC 자동창고 정적 셀 초안

사용자 선택: FANUC R-2000iC/210L. 컨베이어 연장과 로봇/창고 외형만 구현.

## 소스
- https://github.com/FANUC-CORPORATION/fanuc_description
- fanuc_r2000_description/meshes/r2000ic_210l/visual (base, j1~j6 DAE)
- fanuc_r2000_description/urdf/r2000ic_210l_urdf_macro.xacro
- 원본 Xacro 표기 Apache-2.0, FANUC America / FANUC CORPORATION copyright 2026.
- 로컬 원본 폴더에 LICENSE.txt와 source-commit.txt 보존. 외부 모델은 Git 제외.
- DAE는 meter/Z_UP이며 링크 원점은 공식 Xacro를 적용했다.
- 관절 각도 0의 정적 계층만 구성. 물리 관절, 드라이브, 제어, 충돌은 미구현.

## 배치 (m)
- 기존 메인 X=-1.2~1.2에 X=1.2~2.4 연장부 추가: 총 3.6m.
- 기존 이송 데모는 수정하지 않았다. 정적 셀에서만 엔진 파렛트를 (1.8,0,0.7)에 둔다.
- 로봇 베이스 (2.1,1.9,0), 방향 Z=-90도.
- 창고: 2열(Y) × 2단(Z), 전면 -X. 범위 X3.7~4.8, Y0.6~3.0, 높이2.7.
- 선반 상면 Z=0.65/1.65, 셀별 바닥 1.02×1.02.
- 공정 변경 승인: 외부 파렛트/이적대를 제외하고 엔진을 셀 받침에 직접 안착.
- 배치는 시각적 초안. IK, 셀 삽입자세, 충돌, 하중, 안전설비 검증은 하지 않음.
- 자동창고는 로봇 직접 입고용 단순 랙 외형이며 별도 스태커 크레인 없음.

## 실행
```powershell
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/convert_fanuc.py
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/build_engine_jig.py
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/build_warehouse_cell.py
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/preview_engine.py --stage C:/IssacsimProject/Issacsim/external_assets/engines/caterham_duratec/usd/warehouse_cell_preview.usda
```

변환: 공식 시각 메시 7개, 86,232 triangles. 미터/Z_UP 유지, 링크 계층 및 메시 재질 구성.
검증: 추가 롤러12개, 랙 셀4개, 마지막 J6까지 참조 구성 확인.
fb40c9803a826ba68c7c8e28ba904a25efa7fcd2


## 엔진 전용 지그와 셀 받침 (2026-09-30)

사용자가 승인한 구조: 좌우 집기, 하부 보조 패드, 플라이휠측 위치결정 핀.
엔진 이송 시 roll/pitch 유지, yaw만 변경하는 것을 후속 제어 요구사항으로 기록한다.
현재는 정적 형상이며 자세 제어/집기/입고 동작은 구현하지 않았다.

- `assets/engine_jig.usda`: FANUC 순정품이 아닌 프로젝트 자체 가상 지그.
- 공식 Xacro의 J6→flange 오프셋 +X 240 mm에 부착. 어댑터 볼트 패턴은 미구현.
- 로컬 +X 접근, +Z 수직. 전폭800 mm, 두 집기 암, 좌우 클램프 패드와 하부 패드.
- 위치결정 핀 2개 Ø16 × 45 mm는 자리표시용. 실제 홀 위치/맞춤 미확인.
- 손가락/패드 등의 상세 치수는 시각 설계값. 현재 자세는 파지 완료 자세를 의미하지 않는다.
- `assets/engine_cell_cradle.usda`: 높이130 mm, 두 받침 레일과 두께20 mm 고무 패드.
- 고무 패드는 일반 평면 패드이며 엔진 하부 접촉면을 본뜬 맞춤 형상은 아직 아님.
- 명목 정렬에서 손가락 내측 Y=155 mm, 받침 외측Y=130 mm로 25 mm 통로 여유.
- 셀 전체 삽입/후퇴 swept collision, 실제 접촉, 고정력 검증은 하지 않았다. 무게 검증은 사용자 요청으로 제외.
- 상단 셀까지 적용한 패드 총8개. 이적대는 현재 장면에서 제거.
- 로컬 `jig_detail_preview.usda`는 지그와 셀 받침을 떨어뜨려 보여주는 별도 검토 장면.
- 기존 외부 파렛트 이적 관련 과거 문서보다 이 직접 입고 결정이 우선한다.

검증: USD 참조와 재질, 손목 계층 부착, 4셀 패드, 이적대 제거 및 Isaac Sim 화면 확인.
