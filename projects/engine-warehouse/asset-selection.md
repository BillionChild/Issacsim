# 엔진 모델 선정 기록

2026-09-29 사용자가 Caterham 7 Duratec Engine (terradog)을 선택했다.

- 출처: https://embed-3dwarehouse-classic.sketchup.com/model/c413cb2d4973b215ac0c05b8eb4d8560/Caterham-7-Duratec-Engine
- 모델 ID: c413cb2d4973b215ac0c05b8eb4d8560
- 제작자 설명: 2Lt Cosworth Duratec, Caterham용 드라이섬프 사양.
- 페이지 표시: 단위 centimeter, Bounds 44 x 60 x 48, 57,751 polygons, 11 materials, 9MB.
- Bounds는 사이트 표시값이며 파일을 측정한 값이 아니다. 축 대응과 실제 치수 정확도는 미검증.
- 목적: 완성 엔진 외형을 이용한 물류 시뮬레이션. 상세 실물 치수·성능 검증은 선정 필수조건에서 제외.
- 엔진 확보·측정 후 파렛트와 롤러 컨베이어를 선정한다. 기존 임시 배치 치수는 확정값이 아니다.
- 원본 확보: `external_assets/engines/caterham_duratec/Duratec+Engine.zip` (Collada + JPG 2개).
- 사용 조건, 다운로드 형식, USD 변환 방법은 파일 확보 전후 확인한다. 원본 모델을 공개 저장소에 올리지 않는다.
- 모델 크기 변경, 파렛트 설계, 장면 배치는 사용자에게 제시하고 확인받은 뒤 적용한다.

## 2026-09-29 USD 변환

- 사용자 승인: 선택한 엔진의 USD 변환 및 Isaac Sim 미리보기.
- 설치된 omni.kit.asset_converter 6.0.5는 DAE 입력을 지원하지 않아 pycollada 0.9.3 + 설치된 USD 라이브러리로 변환.
- 원본 Z_UP, 1단위 = 0.0254m. 월드 변환을 적용한 삼각형을 미터 단위 USD에 저장. 임의 크기 조정 없음.
- 측정 외곽: X 604.685mm × Y 431.245mm × Z 479.228mm. 실제 엔진 실측치가 아니라 다운로드 모델의 치수.
- 결과: `external_assets/engines/caterham_duratec/usd/engine.usdc`, 979 mesh / 339,936 triangles / 텍스처 2개.
- SketchUp 선분 1,082개 세트는 제외. 삼각형과 UV, 법선, 색상/텍스처 유지. 재질은 UsdPreviewSurface로 근사하며 CAD 구조/물리 특성은 포함하지 않음.
- 원본 좌표는 유지. 미리보기 인스턴스만 XY 중심 및 바닥 Z=0에 정렬. 조명과 카메라는 미리보기 용도.
- 원본과 변환된 모델/텍스처는 Git 제외. 재배포 조건 검토 전 공개 저장소에 업로드하지 않음.

재현 (PowerShell, 저장소 루트):

```powershell
& C:/isaacsim/kit/python/python.exe -m pip install --target .venv/asset-tools pycollada==0.9.3
# ZIP을 external_assets/engines/caterham_duratec/source 에 먼저 풀기
& C:/isaacsim/kit/python/python.exe projects/engine-warehouse/convert_engine.py
& C:/isaacsim/python.bat projects/engine-warehouse/preview_engine.py
```

`preview_engine.py`는 새 Isaac Sim 창을 열고 닫을 때까지 유지한다.
검증 수치는 로컬 `usd/conversion-report.json`에 기록한다.
