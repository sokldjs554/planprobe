"use strict";
const $ = (id) => {
    const node = document.getElementById(id);
    if (!node)
        throw new Error(`missing #${id}`);
    return node;
};
const runButton = $("run-demo");
const requestText = $("request-text");
const stagePill = $("stage-pill");
const statusLine = $("status-line");
const resultOverview = $("result-overview");
const resultHeadline = $("result-headline");
const resultDetail = $("result-detail");
const metricAssumptions = $("metric-assumptions");
const metricFalse = $("metric-false");
const metricPreedit = $("metric-preedit");
const metricChecks = $("metric-checks");
const planNode = $("plan");
const assumptionsNode = $("assumptions");
const gateBanner = $("gate-banner");
const evidenceNode = $("evidence");
const eventsNode = $("events");
const replanNode = $("replan");
const diffNode = $("diff");
const checksNode = $("checks");
const STAGE_LABELS = {
    queued: "대기",
    planning: "AI 계획 생성",
    extracting: "핵심 전제 추출",
    probing: "저장소 검증",
    blocked: "코드 생성 차단",
    replanning: "근거 기반 재계획",
    coding: "코드 생성",
    verifying: "최종 검증",
    complete: "완료",
    failed: "실패",
};
function stageLabel(stage) {
    return STAGE_LABELS[stage] ?? stage.replaceAll("_", " ");
}
function esc(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}
function badge(verdict) {
    if (verdict === "verified")
        return '<span class="badge good">실제 저장소와 일치</span>';
    if (verdict === "contradicted")
        return '<span class="badge bad">거짓 전제</span>';
    return '<span class="badge warn">확인 불가</span>';
}
async function jsonFetch(url, init) {
    const response = await fetch(url, init);
    if (!response.ok)
        throw new Error(`${response.status} ${await response.text()}`);
    return await response.json();
}
function renderPlan(target, plan) {
    target.innerHTML = plan.steps.map(step => `<article class="plan-card"><span class="id">${esc(step.id)}</span><h4>${esc(step.title)}</h4><p>${esc(step.detail)}</p></article>`).join("");
}
function renderEvents(events) {
    eventsNode.innerHTML = events.map(item => `<div class="event"><b>${esc(stageLabel(item.stage))}</b><span>${esc(item.message)}</span></div>`).join("");
}
function renderResultSummary(packet) {
    const falseCount = Number(packet.metrics.contradicted_assumptions ?? 0);
    const preEdits = Number(packet.metrics.source_edits_before_gate ?? 0);
    const checksPassed = Number(packet.metrics.checks_passed ?? 0);
    const checksTotal = Number(packet.metrics.checks_total ?? 0);
    if (packet.verdict === "ready_with_evidence") {
        resultOverview.className = "result-overview success";
        resultOverview.querySelector(".result-icon").textContent = "✓";
        resultHeadline.textContent = `코드 작성 전에 잘못된 전제 ${falseCount}개를 차단하고, 재계획 후 ${checksPassed}/${checksTotal} 검증을 통과했습니다.`;
        resultDetail.textContent = `첫 Gate 이전 소스 수정 ${preEdits}개 · AI의 자기평가가 아니라 실제 저장소 probe와 테스트로 판정했습니다.`;
    }
    else {
        resultOverview.className = "result-overview blocked";
        resultOverview.querySelector(".result-icon").textContent = "!";
        resultHeadline.textContent = "검증 근거가 부족해 코드 생성을 멈췄습니다.";
        resultDetail.textContent = String(packet.metrics.block_reason ?? "확인되지 않은 핵심 전제가 남아 있습니다.");
    }
}
function renderPacket(packet) {
    metricAssumptions.textContent = String(packet.metrics.initial_assumptions);
    metricFalse.textContent = String(packet.metrics.contradicted_assumptions);
    metricPreedit.textContent = String(packet.metrics.source_edits_before_gate);
    metricChecks.textContent = `${packet.metrics.checks_passed}/${packet.metrics.checks_total}`;
    renderResultSummary(packet);
    renderPlan(planNode, packet.initial_plan);
    const resultMap = Object.fromEntries(packet.probe_results.map(result => [result.assumption_id, result]));
    assumptionsNode.innerHTML = packet.initial_plan.assumptions.map(assumption => {
        const result = resultMap[assumption.id];
        if (!result)
            return "";
        const klass = result.verdict === "contradicted" ? "false" : result.verdict === "verified" ? "true" : "";
        return `<article class="assumption ${klass}"><div class="assumption-head"><span class="badge">${esc(assumption.id)}</span>${badge(result.verdict)}</div><h4>${esc(assumption.claim)}</h4><p>${esc(assumption.why_it_matters)}</p></article>`;
    }).join("");
    if (packet.first_gate.status === "block") {
        gateBanner.className = "gate-banner block";
        gateBanner.innerHTML = `<strong>잘못된 핵심 전제 ${packet.first_gate.blocked_assumptions.length}개 발견 — 코드 생성 차단</strong><span>소스 파일 수정 ${packet.first_gate.source_edits_before_gate}개 · 코드 작성 전에 멈췄습니다.</span>`;
    }
    evidenceNode.innerHTML = packet.probe_results.map(result => {
        const evidence = result.evidence.map(item => `<code>${esc(item.path)}${item.line_start ? `:${item.line_start}` : ""}\n${esc(item.snippet)}</code>`).join("");
        return `<article class="evidence-row"><h4>${esc(result.assumption_id)} · ${badge(result.verdict)}</h4><div class="observed"><b>실제 관측:</b> ${esc(result.observed)}<br><b>AI 계획의 기대:</b> ${esc(result.expected)}</div>${evidence}</article>`;
    }).join("");
    if (packet.revised_plan) {
        renderPlan(replanNode, packet.revised_plan);
    }
    else {
        replanNode.innerHTML = '<div class="blocked-empty">확인할 수 없는 핵심 전제가 남아 있어 재계획을 추측으로 진행하지 않았습니다.</div>';
    }
    if (packet.patch) {
        diffNode.innerHTML = packet.patch.edits.map(edit => `<article class="diff-file"><h4>${esc(edit.path)}</h4><pre>- ${esc(edit.old)}\n+ ${esc(edit.new)}</pre></article>`).join("");
    }
    else {
        diffNode.innerHTML = '<div class="blocked-empty">코드 작성 잠금이 유지되어 소스 코드는 수정되지 않았습니다.</div>';
    }
    if (packet.checks.length) {
        checksNode.innerHTML = packet.checks.map(check => `<article class="check"><h4>✓ ${esc(check.name)}</h4><pre>${esc(check.detail)}</pre></article>`).join("");
    }
    else {
        checksNode.innerHTML = `<div class="blocked-empty">${esc(packet.metrics.block_reason ?? "코드 생성 전에 차단되었습니다.")}</div>`;
    }
    stagePill.textContent = packet.verdict === "ready_with_evidence" ? "검증 완료" : "차단";
}
function resetDemo() {
    resultOverview.className = "result-overview running";
    resultOverview.querySelector(".result-icon").textContent = "…";
    resultHeadline.textContent = "AI 계획을 실제 저장소와 대조하고 있습니다.";
    resultDetail.textContent = "거짓 전제가 있으면 소스 파일을 수정하기 전에 먼저 차단합니다.";
    metricAssumptions.textContent = "…";
    metricFalse.textContent = "…";
    metricPreedit.textContent = "…";
    metricChecks.textContent = "…";
}
async function run() {
    runButton.disabled = true;
    runButton.textContent = "검증 중…";
    stagePill.textContent = "실행 중";
    statusLine.textContent = "AI 계획을 만든 뒤 실제 저장소에서 핵심 전제를 확인합니다…";
    resetDemo();
    let didScroll = false;
    try {
        const created = await jsonFetch("/api/runs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_text: requestText.value, provider: "deterministic-demo" }),
        });
        for (let i = 0; i < 160; i += 1) {
            const record = await jsonFetch(`/api/runs/${created.id}`);
            stagePill.textContent = stageLabel(record.stage);
            statusLine.textContent = record.status_message;
            renderEvents(record.events);
            if (record.packet) {
                renderPacket(record.packet);
                if (!didScroll) {
                    resultOverview.scrollIntoView({ behavior: "smooth", block: "center" });
                    didScroll = true;
                }
            }
            if (record.stage === "complete" || record.stage === "failed")
                break;
            await new Promise(resolve => window.setTimeout(resolve, 250));
        }
    }
    catch (error) {
        stagePill.textContent = "실패";
        resultOverview.className = "result-overview blocked";
        resultOverview.querySelector(".result-icon").textContent = "!";
        resultHeadline.textContent = "데모 실행에 실패했습니다.";
        resultDetail.textContent = error instanceof Error ? error.message : String(error);
        statusLine.textContent = resultDetail.textContent;
    }
    finally {
        runButton.disabled = false;
        runButton.textContent = "30초 데모 다시 실행";
    }
}
runButton.addEventListener("click", () => { void run(); });
void jsonFetch("/api/health")
    .then(() => { statusLine.textContent = "준비 완료. ‘30초 데모 시작’을 누르면 잘못된 전제 차단부터 최종 검증까지 자동으로 볼 수 있습니다."; })
    .catch(() => { statusLine.textContent = "백엔드에 연결할 수 없습니다."; });
