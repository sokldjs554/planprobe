# PlanProbe

[![CI](https://github.com/sokldjs554/planprobe/actions/workflows/ci.yml/badge.svg)](https://github.com/sokldjs554/planprobe/actions/workflows/ci.yml)
[![Live smoke](https://github.com/sokldjs554/planprobe/actions/workflows/live-smoke.yml/badge.svg)](https://github.com/sokldjs554/planprobe/actions/workflows/live-smoke.yml)

**Live demo:** https://planprobe.onrender.com

> **AI가 코드를 쓰기 전에, 구현 계획이 기대는 전제를 실제 저장소에서 먼저 반증하는 개발 생산성 시스템.**

PlanProbe는 챗봇이 아니다. 기능 요청을 받은 AI coding workflow가 바로 소스 코드를 수정하지 못하게 하고, 먼저 구현 계획의 암묵적 전제를 꺼내 실제 코드·스키마·설정·기존 테스트에 연결된 실행 가능한 probe로 검증한다.

```text
기능 요청
  ↓
AI 구현 계획
  ↓
암묵적 전제 추출
  ↓
실행 가능한 Repository Probe
  ↓
거짓/미확인 전제면 코드 생성 차단
  ↓
증거 기반 재계획
  ↓
Source Patch
  ↓
기존 계약 + 신규 기능 검증
```

## 왜 이 주제인가

일반적인 coding agent는 잘못된 repository 전제를 가진 채 코드를 먼저 쓰고 테스트/수정 루프에서 뒤늦게 문제를 발견한다. PlanProbe는 그 비용을 **첫 source edit 전에** 줄이는 것을 목표로 한다.

현재 공개 생태계의 assumption ledger, assumption popup, plan citation gate와 겹치지 않도록 제품 경계를 더 좁혔다. 핵심은 **자동 추출된 implicit premise를 finite executable probe로 컴파일하고, 실제 실행 결과가 code-write interlock을 결정한다는 것**이다. 자세한 충돌 조사는 `docs/COLLISION_AUDIT.md`에 남겼다.

## 데모

공개 데모는 **https://planprobe.onrender.com** 에 배포되어 있다. 첫 화면의 **샘플 기능 검증 시작** 버튼 하나로 계획 → 전제 추출 → 저장소 probe → 사전 차단 → 근거 기반 재계획 → source patch → 회귀 검증까지 볼 수 있다. 채팅 UI는 사용하지 않는다.

### 로컬 실행


```bash
python -m pip install -e .
uvicorn planprobe.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 연다.

CLI 재현:

```bash
python -m planprobe.cli demo > packet.json
```

기본 데모는 credential이 필요 없는 deterministic provider를 사용한다. 이는 agent/verification orchestration을 재현하기 위한 것이며 실제 LLM 코딩 품질 결과로 주장하지 않는다.

## 모델 경로

- deterministic demo
- OpenAI-compatible local/open route (Ollama/vLLM/Qwen 계열)
- optional hosted Messages API route

어떤 모델도 자기 전제를 `verified`로 판정할 권한은 없다.

## 검증

```bash
python -m pytest -q
tsc -p web/tsconfig.json --noEmit
PYTHONPATH=. python scripts/evaluate_demo.py
```

현재 로컬 deterministic orchestration 측정:

| 항목 | 결과 |
|---|---:|
| Python 테스트 | **14 passed** |
| 반복 파이프라인 | **5/5 ready_with_evidence** |
| 코드 생성 전 거짓 전제 탐지 | **2/4** |
| Gate 이전 source edit | **0** |
| 기존 계약 검증 | **3 passed** |
| 신규 기능 acceptance | **2 passed** |
| 반복 실행 median | **4.490 s** |

이 수치는 deterministic provider의 파이프라인/검증 재현성 측정이며 LLM 품질 벤치마크가 아니다. 원시 요약은 `artifacts/evaluation.json`에 있다.

추가로 고정된 repository-contract suite를 만들었다. `schema`, `timezone/config`, `idempotency/retry`, `state order`, `backward compatibility`, `authorization/ownership` 6개 전제 유형 × 4개씩 총 **24개**다. 현재 로컬 결과는 **전제 판정 24/24**, **Gate 판정 24/24**, **probe 중 source 불변 24/24**, **false block 0**, **missed block 0**, 명시적 `unknown` 6개다. 이 역시 probe/gate 엔진 검증이지 LLM 품질 결과는 아니다. 원시는 `artifacts/probe-suite.json`에 저장된다.

실제 모델 경로도 보완했다. 원격 모델에게 로컬 경로 문자열만 넘기지 않고 bounded repository source context를 전달하며, provider가 usage를 반환하면 call/input/output token/latency를 기록한다. 실제 Qwen/hosted 비교는 아직 실행하지 않았고 수치도 주장하지 않는다. Direct coding / self-reflect와의 실제 모델 비교 실험 역시 별도 증거가 생기기 전까지 성능 우위를 주장하지 않는다.

GitHub Actions의 격리 환경에서 Python **3.11 / 3.12 / 3.13** 매트릭스로 설치, `pip check`, pytest, Ruff, mypy, TypeScript strict typecheck, 24-case repository-contract suite, 전체 deterministic pipeline을 실제 검증한다. 현재 main의 CI와 배포 대상 E2E smoke가 모두 통과한 상태다.

## 배포 검증

`live-smoke` workflow는 단순히 URL이 열리는지만 확인하지 않는다. Render의 `/api/release`가 **검증 중인 GitHub SHA와 정확히 일치할 때까지 기다린 뒤**, 공개 API에 실제 데모 요청을 제출하고 다음 조건을 검사한다.

- 첫 Gate가 `block`이며 차단 전 source edit가 **0**
- 차단된 전제가 데모 계약의 `A-UTC`, `A-REGION`과 일치
- 재계획·patch·최종 검증을 거친 verdict가 **`ready_with_evidence`**

따라서 README/문서만 바뀐 최종 커밋도 동일한 exact-commit 배포 검증을 다시 거친다.

## Fail-closed 경계

`unknown`인 핵심 전제가 하나라도 남으면 v0.1은 재계획을 추측으로 진행하지 않고 **source write 0 상태에서 종료**한다. `contradicted` 전제로 재계획할 때도 실제 실행된 evidence ID를 모두 연결해야 하며, 존재하지 않는 근거 ID를 만들거나 새로운 미검증 핵심 전제를 도입하면 patch 생성이 차단된다.

## 범위

합성 LiveOps 저장소만 사용하며 실제 게임스프링 내부 시스템, 플레이어 데이터, 비공개 workflow를 사용하거나 추정하지 않는다.

Copyright © 2026 윤기혁. All rights reserved. Portfolio project.
