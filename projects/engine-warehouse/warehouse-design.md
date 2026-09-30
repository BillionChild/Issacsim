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

## 대기 자세 및 평행 집게 수정

- J1=180°, J2=-20°, J3=-35°(URDF J3 축 -Y이므로 USD rotateY=+35°)의 빈손 대기 자세.
- 대기 시 컨베이어 반대 방향을 향한다. 빈손 자세는 기울어져도 되며 엔진 운반 중 수평 유지 제어는 아직 미구현.
- 기존 중간 ClampShoe/ClampPad 제거. 좌우 집게 암과 하부 보조 패드만 유지.
- 좌우 그룹이 로컬 Y축으로 각각 0~120mm 직선 이동. 하부 받침도 함께 움직임.
- 기본값 열림. 집게 내측 간격 닫힘430mm/열림670mm. 실제 엔진 형상에 맞춘 접촉/파지력 검증값은 아님.
- 집게 구동은 USD Xform 위치 제어이며 물리 프리즘 조인트나 액추에이터 제어가 아니다.
- 새 실행: `C:/isaacsim/python.bat projects/engine-warehouse/run_gripper_preview.py`
- Engine Gripper 창의 Open jaws / Close jaws 버튼 사용.
- `--test` 모드는 닫힘·열림 종단 도달을 Isaac Sim에서 확인 후 종료.
- 초기 로봇/지그의 메시·기본도형별 월드 AABB와 컨베이어/엔진/랙 경계상자 교차 0개 확인.
  이는 정적 외부 장애물 검증이며 자기충돌 및 대기→픽업 경로 검증을 대체하지 않는다.
- 전체 장면 로딩이 지연되어 열림/닫힘 실행 검증은 동일 지그를 참조하는 경량 상세 장면에서 수행한다.
- 상세 조작 창 실행: `C:/isaacsim/python.bat projects/engine-warehouse/run_gripper_preview.py --detail`
- 전체 셀 기본 실행은 새 대기 자세와 열린 집게로 시작한다.
- 최종 실행 검증: 전체 셀 GUI에서 Close jaws 입력 후 430mm 도달, Open jaws 복귀 확인.
- headless 자동 테스트는 시작 지연으로 완료하지 못해 종료했으며, 통과로 기록하지 않는다.
