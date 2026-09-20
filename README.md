# Isaac Sim 제조 시뮬레이션 학습 프로젝트

OpenUSD와 NVIDIA Isaac Sim으로 작은 제조 셀을 구성하고, 공정 배치·작업 순서·버퍼 조건을 비교하는 학습 저장소입니다.

## 첫 목표
공급대(Supply), 치구(Fixture), 배출대(Output)로 구성된 정적 장면을 만들고 저장·재실행합니다. 이후 로봇 동작, 공정 흐름, 지표 비교를 순서대로 추가합니다.

## 시작하기
1. [실행 환경 기록](docs/environment.md)에 설치 버전과 장비를 기록합니다.
2. [첫 실습](exercises/01-static-cell/README.md)을 진행합니다.
3. [학습 기록](docs/learning-log.md)에 실제 결과와 막힌 점을 남깁니다.
4. 변경 내용을 검토하고 의미 있는 작업 단위로 커밋·푸시합니다.

## 관리 구조
- docs/: 환경 및 학습 기록
- exercises/: 단계별 안내, 직접 작성한 스크립트, 작은 USD 장면
- 로컬 outputs/: 생성 데이터·영상·로그 (Git 제외)

## 단계
- [ ] 01: 정적 셀 배치와 좌표계
- [ ] 02: Python으로 장면 생성·배치 변경
- [ ] 03: 로봇 작업 시퀀스
- [ ] 04: 생산 흐름과 병목 분석
- [ ] 05: 대안 비교와 결과 보고서

## 기록 원칙
- 작성, 실행, 검증 완료를 구분합니다. 현재는 프로젝트 문서만 준비되었고 Isaac Sim 실행은 확인되지 않았습니다.
- 설치 버전과 같은 버전의 공식 문서를 사용하고 실습 중에는 환경을 고정합니다.
- 프로젝트에서 만든 작은 .usda/.usd 파일은 관리합니다. NVIDIA 원본 자산과 대용량 모델은 재배포하지 않고 출처·취득 방법을 기록합니다.
- 전 직장의 도면·실제 공정 데이터·비공개 자료 및 계정 정보는 올리지 않습니다.
- 현장 연동 전에는 결과물을 '가상 제조 셀 시뮬레이션'으로 설명합니다.
- 시뮬레이션 결과와 실제 설비 검증 결과를 구분합니다.

## 공식 자료
- [Learn OpenUSD](https://docs.nvidia.com/learn-openusd/latest/index.html)
- [Isaac Sim Basics](https://docs.isaacsim.omniverse.nvidia.com/latest/introduction/quickstart_index.html)

저장소 주소의 Issacsim 표기는 유지하며, 제품명은 Isaac Sim으로 표기합니다.
