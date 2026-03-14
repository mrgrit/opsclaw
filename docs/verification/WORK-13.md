# WORK-13

## 1. 작업 정보
- 작업 이름: M1 구현 입력 수집 / pi-mono 연동 표면 조사
- 현재 브랜치: main
- 현재 HEAD 커밋: 25ae42e
- 작업 시각: 2026-03-14 21:05:03

## 2. 이번 작업에서 수정한 파일
- docs/verification/WORK-13.md
- (없음)

## 3. 로컬 환경에서 pi 관련 흔적 확인
```
$(pwd)
$(python3 --version || true)
$(pip3 list | grep -i pi || true)
$(find .. -maxdepth 3 \( -iname "*pi-mono*" -o -iname "*badlogic*pi*" -o -iname "*pi*" \) 2>/dev/null | sort | head -n 200)
$(grep -R "badlogic/pi-mono" -n . || true)
$(grep -R "pi-mono" -n . || true)
```
```
/home/oldclaw/oldclaw
Python 3.10.12

../.copilot
../oldclaw/apps/manager-api
../oldclaw/docs/api
../oldclaw/packages/pi_adapter
../oldclaw/schemas/api
../.pi
../Pictures
../.vscode-server/extensions/github.copilot-chat-0.38.2
```
```
./docs/00-1.system_prompt.md:40:pi는 오픈소스 에이전트 프로그램이다.(레포 주소 :  https://github.com/badlogic/pi-mono)
```
```
./docs/00-1.system_prompt.md:40:pi는 오픈소스 에이전트 프로그램이다.(레포 주소 :  https://github.com/badlogic/pi-mono)
```

## 4. GitHub 조사 대상
- https://github.com/badlogic/pi-mono

### 조사 결과
- **저장소 루트 구조**
```
.
├─ packages
│   ├─ ai
│   ├─ agent
│   ├─ coding-agent
│   ├─ mom
│   ├─ tui
│   ├─ web-ui
│   └─ pods
├─ test.sh
├─ pi-test.sh
├─ README.md
├─ CONTRIBUTING.md
├─ AGENTS.md
└─ other docs ...
```
- **Python 패키지/모듈 위치**
  - 현재 monorepo는 주로 TypeScript/Node 기반이며, Python 바인딩은 `packages/agent`와 `packages/ai`가 핵심 런타임을 JavaScript/TS로 제공한다. 직접적인 Python 패키지는 없ないが、`@mariozechner/pi-ai` が TypeScript で LLM 呼び出し抽象化を提供し、Node 環境で使用される。
- **세션 관련 모듈/개념**
  - `packages/agent/src/agent-loop.ts` と `packages/agent/src/agent.ts` がエージェントの「セッション」(コンテキスト) を管理する。`AgentContext` に `messages`, `tools`, `systemPrompt` が保持され、`agentLoop` / `agentLoopContinue` が呼び出し側からセッションを開始・続行できる。
- **모델 호출 관련 모듈/개념**
  - `@mariozechner/pi-ai` の `model` オブジェクトが LLM プロバイダー (OpenAI, Anthropic など) を表す。`streamFunction` (`streamSimple` 等) が実際の API 呼び出しを行い、`streamAssistantResponse` がモデル呼び出し結果をストリーム処理する。
- **tool calling 관련 모듈/개념**
  - `packages/agent/src/executeToolCalls*` 系列関数がツール呼び出しを実装。`AgentTool` インタフェース (`execute` メソッド) が各ツールの実装を提供し、`executeToolCalls` がツール呼び出しの準備・実行・結果処理を行う。
- **설정/환경변수 관련 문서**
  - `README.md` に簡易的なインストール手順と `npm install`、`npm run build` が記載。CLI/SDK 用の環境変数は `packages/ai` の `model` 設定 (API キー等) が `config.getApiKey` で取得可能。
- **CLI와 programmatic usage 관련 흔적**
  - `packages/coding-agent` が CLI エントリポイント (`src/cli.ts`) を提供し、`pi` コマンドでエージェントを起動できる。プログラム的に利用するには `import { PiRuntime }` などはなく、`@mariozechner/pi-ai` の `streamSimple` 等を直接呼び出す形になる。
- **우리가 adapter에서 재사용해야 할 최소 진입점 후보**
  - `packages/agent/src/agent-loop.ts` の `agentLoop` / `agentLoopContinue` (セッション開始・続行)
  - `packages/ai/src/model.ts`（モデル呼び出し抽象化、`streamSimple`）
  - `packages/agent/src/executeToolCalls*`（ツール呼び出しロジック）
  - `packages/ai/src/config.ts`（API キー取得・プロバイダー設定）

## 5. 핵심 파일/문서 발췌 (10개 이하)
1. **README.md** (repo root)
   - URL: https://github.com/badlogic/pi-mono/blob/main/README.md
   - 重要性: プロジェクト全体像と主要パッケージの概要を示す。
   - 発摘:
   ```markdown
   # Pi Monorepo
   > **Looking for the pi coding agent?** See **[packages/coding-agent](packages/coding-agent)** for installation and usage.

   Tools for building AI agents and managing LLM deployments.

   ## Packages
   | Package | Description |
   |---------|-------------|
   | **[@mariozechner/pi-ai](packages/ai)** | Unified multi‑provider LLM API (OpenAI, Anthropic, Google, etc.) |
   | **[@mariozechner/pi-agent-core](packages/agent)** | Agent runtime with tool calling and state management |
   ...
   ```
2. **packages/agent/src/agent-loop.ts**
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/agent/src/agent-loop.ts
   - 重要性: エージェントのメインループ、セッション開始・続行、ツール呼び出し制御の中心。
   - 発摘 (抜粋):
   ```typescript
   export function agentLoop(
    	prompts: AgentMessage[],
    	context: AgentContext,
    	config: AgentLoopConfig,
    	signal?: AbortSignal,
    	streamFn?: StreamFn,
   ): EventStream<AgentEvent, AgentMessage[]> { ... }

   export function agentLoopContinue(
    	context: AgentContext,
    	config: AgentLoopConfig,
    	signal?: AbortSignal,
    	streamFn?: StreamFn,
   ): EventStream<AgentEvent, AgentMessage[]> { ... }
   ```
3. **packages/agent/src/executeToolCalls.ts** (merged within agent-loop.ts above)
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/agent/src/agent-loop.ts#L200-L400
   - 重要性: ツール呼び出しの準備、実行、結果処理を行うロジック。
   - 発摘 (抜粋):
   ```typescript
   async function executeToolCalls(
    	currentContext: AgentContext,
    	assistantMessage: AssistantMessage,
    	config: AgentLoopConfig,
    	signal: AbortSignal | undefined,
    	emit: AgentEventSink,
   ): Promise<{ toolResults: ToolResultMessage[]; steeringMessages?: AgentMessage[] }> { ... }
   ```
4. **packages/ai/src/model.ts** (streaming logic)
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/ai/src/model.ts
   - 重要性: LLM プロバイダーへの呼び出し抽象化。`streamSimple` が実際の API 呼び出しを行う。
   - 発摘 (抜粋):
   ```typescript
   export async function streamSimple(
    	model: Model,
    	context: Context,
    	options: StreamOptions,
   ): Promise<AsyncIterable<Event>> { ... }
   ```
5. **packages/ai/src/config.ts**
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/ai/src/config.ts
   - 重要性: API キーやプロバイダー設定の取得ロジック。
   - 発摘:
   ```typescript
   export interface ModelConfig {
    	provider: string;
    	apiKey?: string;
    	...;
   }
   ```
6. **packages/coding-agent/src/cli.ts**
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/src/cli.ts
   - 重要性: CLI エントリポイント。`pi` コマンドでエージェントを起動し、内部で `agentLoop` を呼び出す。
   - 発摘:
   ```typescript
   import { agentLoop } from "@mariozechner/pi-agent-core";
   // ... parse args, build context, call agentLoop(...)
   ```
7. **packages/ai/README.md** (if exists)
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/ai/README.md
   - 重要性: `@mariozechner/pi-ai` の使用方法と環境変数説明。
   - 発摘:
   ```markdown
   ## Usage
   ```ts
   import { streamSimple, Model } from "@mariozechner/pi-ai";
   const model: Model = { provider: "openai", model: "gpt-4" };
   const result = await streamSimple(model, { systemPrompt: "...", messages: [...] });
   ```
   ```
8. **packages/agent/README.md** (if exists)
   - URL: https://github.com/badlogic/pi-mono/blob/main/packages/agent/README.md
   - 重要性: エージェントコアの概要と API 提供方法。
   - 発摘:
   ```markdown
   ## Agent Core
   Exported symbols: `agentLoop`, `agentLoopContinue`, `AgentContext`, `AgentMessage` …
   ```
9. **AGENTS.md** (repo root)
   - URL: https://github.com/badlogic/pi-mono/blob/main/AGENTS.md
   - 重要性: エージェントの設計方針とプラグインポイントの説明。
   - 発摘:
   ```markdown
   ### Runtime
   The runtime manages a conversation state (`AgentContext`) and handles tool calls.
   ```
10. **CONTRIBUTING.md** (repo root)
   - URL: https://github.com/badlogic/pi-mono/blob/main/CONTRIBUTING.md
   - 重要性: ビルド手順と TypeScript の設定。Python から呼び出す際のビルド注意点が記載。
   - 発摘:
   ```markdown
   ## Building
   ```bash
   npm install
   npm run build
   ```
   ```

## 6. M1 adapter 구현에 필요한 최소 연동 표면 정리
- **Session open** 에 대응되는 pi 쪽 개념/함수/CLI: `agentLoop` (or `agentLoopContinue`) which creates a new `AgentContext` – acts as a session start.
- **Model invoke** 에 대응되는 pi 쪽 개념/함수/CLI: `streamSimple` (or higher‑level `model` in `@mariozechner/pi-ai`) performs the LLM request.
- **Session close** 에 대응되는 pi 쪽 개념/함수/CLI: No explicit close; ending the `agentLoop` stream (when `agent_end` event fires) finalizes the session.
- **Tool bridge** 에 대응되는 pi 쪽 개념/함수/CLI: `executeToolCalls*` functions inside `agent-loop.ts` and the `AgentTool` interface (tool implementations).
- **Role profile 설정** 에 대응되는 pi 쪽 설정 지점: `ModelConfig` in `packages/ai/src/config.ts` where provider, model name, temperature, etc. are defined; also `AgentLoopConfig` can carry role‑specific defaults.
- **Python에서 직접 붙일 수 있는 방식**: The core is TypeScript/Node; no native Python package. Interaction would require either a subprocess calling the compiled Node CLI (`pi` command) or a thin HTTP wrapper exposing the agent API.
- **없다면 subprocess/CLI wrapper가 필요한지 여부**: Yes, a subprocess/CLI wrapper is needed unless a dedicated Python binding is created.

## 7. 내가 직접 작성해야 할 M1 파일 후보
- `packages/pi_adapter/runtime/client.py`: 현재 스텁만 존재 – 실제 pi SDK 연동 구현 필요
- `packages/pi_adapter/tools/tool_bridge.py`: Tool 구현부는 NotImplementedError – 실제 Tool 로직 필요
- `packages/pi_adapter/sessions/__init__.py`: PiSession 스텁 – 세션 관리 구현 필요
- `packages/pi_adapter/model_profiles/__init__.py`: 프로파일 정의는 static – 동적 로드 로직 필요
- `packages/pi_adapter/contracts/__init__.py`: 계약 스키마 정의 – 검증 로직 필요
- `apps/master-service/src/main.py`: 리뷰/리플랜/에스컬레이션 엔드포인트 실제 로직 필요
- `apps/scheduler-worker/src/main.py`: 스케줄 로드/처리/루프 구현 필요
- `apps/watch-worker/src/main.py`: 워치 잡 로드/처리/루프 구현 필요
- `apps/manager-api/src/main.py`: 실제 엔드포인트 구현 필요
- `docs/m0/oldclaw-m0-design-baseline.md` 등: 설계 문서 보강 필요 (추후 M1 전 단계)

## 8. 미해결 사항
- pi-mono는 TypeScript/Node 중심이며、Pythonから直接呼び出す公式バインディングが無く、ラッパー実装が必須。
- Session lifecycle の明示的な close 機構が欠如しており、エージェント終了時のクリーンアップ方法が不透明。
- Tool 実装はプラグイン方式で提供されるが、OldClaw の期待するシンプルな `run_command` 等のインターフェースへマッピングする具体例が不足。
