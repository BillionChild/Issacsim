# Engine Warehouse Static Scene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엔진 자동창고 입고 셀의 재생성 가능한 정적 USD 장면을 만들고 사용자가 Isaac Sim에서 열어 배치를 확인하도록 한다.

**Architecture:** 순수 OpenUSD 장면 생성 함수를 Script Editor용 진입점과 분리한다. 장면은 새 메모리 stage에 생성하고 프로젝트의 지정된 USDA로 저장한다. 사용자가 열어 둔 stage를 수정하거나 자동 교체하지 않는다.

**Tech Stack:** Windows PowerShell, 설치된 Isaac Sim 6.1 계열의 Python과 pxr(Usd, UsdGeom, UsdLux, Gf, Sdf). 외부 패키지 설치와 모델 다운로드 없음.

**Spec:** [승인된 설계](../specs/2026-09-28-engine-warehouse-design.md)

## 사용자 지정 진행 방식 — 기존 일괄 구현 절차보다 우선

2026-09-28 사용자 요청: 설비 하나씩 구현 단계를 세분화하고, 사용할 모델을 사용자에게 확인받은 뒤 적용한다. 아래 기존 Task 1/2는 기술 참고용이며 전체를 한 번에 실행하도록 승인된 절차가 아니다. 기본 형상 대체도 먼저 확인받는다. 문서에 적힌 치수·배치는 후보이며 확정값이 아니다.

각 설비는 다음 순서로 진행한다.

1. 후보 조사: 모델 이름, 출처 링크, 미리보기 확보 여부, 파일 형식, 비용·라이선스, 수정 필요 사항을 정리한다. 공개 정보 조사와 로컬 파일 검토는 먼저 진행할 수 있다.
2. 사용자 선택: 추천 후보와 이유를 제시하고 사용할 모델을 확인받는다. 사용자가 선택하기 전 다운로드·변환·장면 적용을 진행하지 않는다.
3. 배치 확인: 선택된 모델의 크기, 위치, 방향, 적용 범위와 필요한 가정을 제시한다. 모델 선택과 함께 확정된 내용은 다시 묻지 않는다.
4. 해당 설비만 적용: 승인된 범위에서 모델을 준비하고 장면에 적용한다. 모델 교체나 유의미한 크기·구조 변경이 필요하면 다시 확인한다.
5. 확인과 기록: 적용 결과와 실행 방법을 보여주고 사용자 확인 후 다음 설비로 넘어간다. 승인된 변경과 출처를 기록하며 재배포 가능한 파일만 Git에 포함한다.

| 순서 | 독립 진행 단위 | 사용자와 결정할 내용 |
|---|---|---|
| 1 | 입고 컨베이어 | 롤러/체인 등 형식, 모델 출처, 길이·폭·높이, 진행 방향 |
| 2 | 인라인 파렛트 | 모델, 외형 치수, 엔진 지지 방식 |
| 3 | 엔진 모듈 | 모델, 크기, 기준 좌표와 초기 배치 |
| 4 | 외부 파렛트와 작업대 | 각 모델, 위치 결정 핀 구성, 안착 높이 |
| 5 | 창고 셀 1개 | 랙 모델, 개구부·받침 구조, 배치 |
| 6 | 산업용 6축 로봇 | 모델, 가반하중·작업 반경 검토, 설치 위치 |
| 7 | 툴과 교환 위치 | 엔진 그리퍼·파렛트 취급 방식과 모델 |
| 8 | 한 사이클 동작 | 승인된 설비로 동작을 하나씩 연결하고 검증 |

현재 실행할 다음 단계는 입고 컨베이어 후보 조사·제시이다. 아직 선택된 모델은 없다. 이후 로봇 도달성 때문에 기존 배치를 조정해야 할 경우 변경안을 먼저 보여준다.

## Global Constraints

- 단위는 m, Z-up을 사용한다.
- 기존 projects/franka-cell 실습은 유지하며 신규 코드는 projects/engine-warehouse에 둔다.
- 보호커버 공정은 사용하지 않는다.
- 첫 장면은 AI·파지·이송 성공이나 도달성 검증 결과가 아니다.
- 실제 공장 검증 전까지 가상 설비 시뮬레이션으로 소개한다.
- 첫 단계는 정적 장면만 구현한다. 로봇 선정·제어, 재고 상태 전이, 출고, 학습, 휴머노이드는 이번 계획의 구현 범위 밖이다.
- 기존 사용자 변경을 add/commit하거나 덮어쓰지 않는다.

## Review Focus

1. Script Editor에서 반복 실행: 동일 이름의 객체가 누적되지 않는다. Task 1에서 두 번 생성해 prim 경로 목록을 비교한다.
2. 사용자 stage가 열린 상태: 저장 파일 생성만 수행한다. Task 2에서 실행 전후 현재 stage 식별자를 비교한다.
3. 단위·높이 오류: 엔진 하단과 인라인 파렛트 상단이 일치한다. Task 1에서 월드 경계상자로 확인한다.
4. 다른 작업 디렉터리에서 실행: 스크립트 위치 기준으로 출력한다. Task 2에서 다른 cwd와 한글·공백이 포함된 임시 출력 경로를 검증한다.
5. 출력 파일이 이미 존재: 명시적인 overwrite 옵션 없이 실패하고 기존 파일을 보존한다. Task 2에서 파일 내용 보존을 확인한다.

## 파일 구성

| 파일 (저장소 기준) | 역할 |
|---|---|
| projects/engine-warehouse/scene.py | 배치 상수, 기본 형상 생성, build_stage(), save_scene() |
| projects/engine-warehouse/create_scene.py | Script Editor 및 명령 실행 진입점, 출력 경로 안내 |
| projects/engine-warehouse/verify_scene.py | 저장 결과의 구조·높이·반복 실행·파일 보존 검사 |
| projects/engine-warehouse/assets/warehouse_static.usda | 검증 후 추적할 생성 장면 |
| projects/engine-warehouse/README.md | 실행 절차, 좌표표, 한계, 첫 확인 항목 |
| docs/learning-log.md | 이번 단계의 작성·실행·검증 결과를 구분해 추가 |

## 배치 계약

모든 값은 설명용 가정이다. 로봇 도달성에 대한 판정은 하지 않는다. 위치는 월드 좌표이며 표의 크기는 X/Y/Z 전체 길이다.

| 대상 | 중심 좌표 m | 크기 m |
|---|---|---|
| 입고 컨베이어 상판 | (-1.8, 0, 0.6) | (2.4, 1.0, 0.2) |
| 인라인 파렛트 | (-1.2, 0, 0.8) | (1.0, 0.8, 0.2) |
| 엔진 대체 형상 | (-1.2, 0, 1.25) | (0.7, 0.6, 0.7) |
| 외부 파렛트 작업대 | (0, 1.6, 0.35) | (1.4, 1.2, 0.7) |
| 외부 파렛트 | (0, 1.6, 0.8) | (1.1, 0.9, 0.2) |
| 창고 셀 받침판 | (1.8, 0, 0.65) | (1.4, 1.2, 0.1) |
| 로봇 설치 표시 | (0, 0, 0.05) | (0.8, 0.8, 0.1) |
| 툴 교환 위치 표시 | (0, -1.4, 0.35) | (1.2, 0.6, 0.7) |

외부 파렛트의 원점은 형상의 중심으로 통일한다. 설명용 위치 결정 핀 두 개를 추가한다.

## Task 1: 정적 장면 생성과 구조 검증

**Files:** Create scene.py, verify_scene.py.

**Interfaces:** `build_stage() -> Usd.Stage`, `save_scene(output: Path, overwrite: bool = False) -> Path`. build_stage는 현재 Isaac Sim stage와 독립적이고 매번 새 stage를 반환한다.

- [ ] 검증 스크립트에서 아래 필수 조건을 먼저 정의한다. 초기 실행은 scene 모듈 미구현으로 실패해야 한다. unittest와 tempfile 등 표준 라이브러리를 사용한다.

```python
stage = build_stage()
assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
root = '/World/EngineWarehouse'
for name in ('Infeed', 'TransferStation', 'Storage', 'RobotStation', 'ToolStation', 'Loads'):
    assert stage.GetPrimAtPath(f'{root}/{name}').IsValid()
paths = lambda s: [str(p.GetPath()) for p in s.Traverse()]
assert paths(stage) == paths(build_stage())
```

- [ ] pxr 모듈 로딩은 설치된 Isaac Sim Python 또는 Script Editor에서 확인한다. 기존 실습의 독립 SimulationApp 실행 패턴은 참고하되 Script Editor에서 SimulationApp을 새로 생성하지 않는다.
- [ ] Cube는 size=1과 scale=전체 길이로 작성한다. 컨테이너는 Xform, 조명은 DomeLight를 사용한다. 기본 prim은 /World로 지정한다. 정적 단계에서는 RigidBodyAPI나 가짜 파지 joint를 추가하지 않는다.

```python
stage = Usd.Stage.CreateInMemory()
world = UsdGeom.Xform.Define(stage, '/World')
stage.SetDefaultPrim(world.GetPrim())
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
```

- [ ] 인라인 파렛트는 Infeed/InlinePallet, 엔진은 Loads/Engine_001, 외부 파렛트는 Loads/ExternalPallet_001에 만든다. 각 물체는 Xform 아래 Geometry를 두고 물체 중심을 원점으로 사용한다. 엔진은 주황, 인라인 파렛트는 회색, 외부 파렛트는 파랑으로 구분한다.
- [ ] 외부 파렛트의 설명용 핀은 로컬 (±0.25, 0, 0.14)에 반지름 0.02, 높이 0.08인 Z축 Cylinder 두 개로 만든다. 실제 엔진 결합 구멍이나 공차를 재현한 것으로 설명하지 않는다.
- [ ] 엔진의 GraspFrame은 로컬 (0,0,0.35), SeatFrame은 (0,0,-0.35), 외부 파렛트의 SeatFrame은 (0,0,0.1)에 Xform으로 표시한다. USD customData에 엔진·파렛트 ID와 셀 EMPTY 상태를 기록한다. 첫 버전에 상태 전이 코드는 없다.
- [ ] 셀 받침판 네 모서리에 기둥을 배치하되 전면 개구부를 막지 않는다. 표시 형상과 실제 로봇을 혼동하지 않도록 RobotStation에는 placeholder=true 메타데이터를 둔다.
- [ ] BBoxCache의 ComputeWorldBound로 Engine_001/Geometry 하단 Z=0.9와 InlinePallet/Geometry 상단 Z=0.9를 오차 1e-6 이내로 확인한다. 엔진 prim이 하나뿐이고 셀 상태가 EMPTY인지 검사한다.
- [ ] 검증 통과 후 새 코드와 검증 파일만 선택적으로 커밋한다.

## Task 2: 저장·실행 진입점과 사용자 안내

**Files:** Create create_scene.py, README.md, assets/warehouse_static.usda; extend verify_scene.py and docs/learning-log.md.

**Interfaces:** Task 1의 save_scene을 호출한다. 기본 출력 경로는 scene.py 부모의 assets/warehouse_static.usda이며 cwd와 무관하다.

- [ ] save_scene은 부모 폴더를 만들고 stage.GetRootLayer().Export(str(output)) 결과를 검사한다. 기존 파일이 있고 overwrite=False면 FileExistsError를 발생시킨다. 실패를 성공 메시지로 처리하지 않는다.
- [ ] 임시 폴더에서 저장 후 Usd.Stage.Open으로 재개방하여 Task 1 검사를 반복한다. 두 번째 저장은 FileExistsError인지, 기존 바이트가 유지되는지 확인한다. overwrite=True는 명시적 재생성 테스트에만 사용한다.
- [ ] create_scene.py는 자신의 절대 경로를 기준으로 scene 모듈을 매 실행 새로 로드한다. Script Editor 실행에서는 argparse로 Isaac 앱 인자를 읽지 않는다. 자동 stage 열기와 play는 하지 않고 생성 경로만 출력한다.
- [ ] README에 다음 실행 방식을 포함한다. 실행 전에 수정 중인 장면을 저장하고, 생성 후 File > Open으로 출력 USDA를 연다.

```python
# Isaac Sim Script Editor에서 실행
import runpy
runpy.run_path(
    r'C:\IssacsimProject\Issacsim\projects\engine-warehouse\create_scene.py',
    run_name='__main__',
)
```

- [ ] Script Editor에서 실행 전후 `omni.usd.get_context().get_stage().GetRootLayer().identifier`가 같은지 확인한다. 현재 stage가 없는 경우에도 생성은 가능해야 한다. 이 검사는 GUI 실행이 가능한 경우 수행하고 아니면 미검증으로 기록한다.
- [ ] README에 좌표표, 출력 파일, 덮어쓰기 옵션, 모델·물리·도달성 미검증 범위와 사용자 화면 확인 항목을 넣는다. 화면에서 엔진이 입고 측에 하나, 외부 파렛트가 비어 있음, 셀 하나, 핀 두 개, 로봇 위치 표시를 확인한다.
- [ ] 기본 USDA를 생성·재개방하고 검증한다. GUI 화면 확인이 불가능하면 사용자에게 열기 절차를 안내하고 구조 검사만 통과했다고 보고한다.
- [ ] learning-log에 설계 승인, 실제 생성 결과, 검사 결과를 추가한다. git diff --check 후 이 단계의 파일만 커밋·푸시한다. 기존 실습 변경은 포함하지 않는다.

## 계획 자체 검토

- 승인 설계의 첫 단계 완료 기준은 Task 1의 구조·높이 검증과 Task 2의 저장·사용자 확인으로 대응한다.
- 후속 동적 제어·재고·AI 지표는 설계 계약으로 유지하며 이번 구현 완료 주장에 포함하지 않는다.
- 동작 검증은 실제 Isaac 환경에서 수행하고, 모듈 import 성공이나 USD 생성 성공을 로봇 동작 성공으로 해석하지 않는다.
