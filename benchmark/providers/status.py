"""Provider scorecard dimensions kept separate from calibration claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from benchmark.models import (
    CalibrationMaturity,
    CalibrationScope,
    EvidenceOrigin,
    ProviderLifecycle,
    ProviderRun,
    RunStatus,
)


@dataclass(frozen=True, slots=True)
class ProviderResearchStatus:
    provider: str
    product: str
    mode: str
    implementation: str
    access_and_auth: str
    api_reachability: str
    response_received: str
    mandarin_mode: str
    granularity: str
    tone_detection: str
    tone_diagnosis: str
    initial_detection: str
    final_detection: str
    native_false_rejection: str
    learner_false_rejection: str
    severe_error_false_acceptance: str
    tone_evidence: str
    timing_evidence: str
    error_coding: str
    audio_quality: str
    privacy_and_data_flow: str
    cost_status: str
    latency_status: str
    implementation_complexity: str
    fixture_status: str
    lifecycle: ProviderLifecycle
    calibration_maturity: CalibrationMaturity = CalibrationMaturity.RAW_EVIDENCE
    calibration_scope: CalibrationScope = CalibrationScope.NONE


STATIC_PROVIDER_STATUS: tuple[ProviderResearchStatus, ...] = (
    ProviderResearchStatus(
        provider="tencent_soe_n",
        product="Smart Oral Evaluation-New Age (product 1774)",
        mode="sentence / eval_mode=1 / F_TDET=true",
        implementation="production adapter implemented",
        access_and_auth="SecretId/SecretKey/AppId required; absent locally",
        api_reachability="not tested without credentials",
        response_received="documentation contract example only",
        mandarin_mode="16k_zh sentence",
        granularity="utterance, word/syllable, phone",
        tone_detection="unknown; no human-supported real runs",
        tone_diagnosis="unknown; no human-supported real runs",
        initial_detection="unknown; no human-supported real runs",
        final_detection="unknown; no human-supported real runs",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="explicit tone valid/ref/hypothesis when vendor marks valid",
        timing_evidence="provider millisecond offsets",
        error_coding="match tags and phone detail",
        audio_quality="not established from real response",
        privacy_and_data_flow="audio leaves Benma for Tencent Cloud when invoked",
        cost_status="unknown until account quote/billing observation",
        latency_status="unknown; no live run",
        implementation_complexity="blocking WSS transport; bounded worker required",
        fixture_status="documentation-contract parser fixture passing",
        lifecycle=ProviderLifecycle.FIXTURE_VALIDATED,
    ),
    ProviderResearchStatus(
        provider="tencent_soe_n",
        product="Smart Oral Evaluation-New Age (product 1774)",
        mode="pinyin / eval_mode=8 / F_TDET=true",
        implementation="production adapter implemented",
        access_and_auth="SecretId/SecretKey/AppId required; absent locally",
        api_reachability="not tested without credentials",
        response_received="documentation contract example only",
        mandarin_mode="16k_zh pinyin",
        granularity="utterance, word/syllable, phone",
        tone_detection="unknown; no human-supported real runs",
        tone_diagnosis="unknown; no human-supported real runs",
        initial_detection="unknown; no human-supported real runs",
        final_detection="unknown; no human-supported real runs",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="invalid vendor tone values normalize to missing evidence",
        timing_evidence="provider millisecond offsets",
        error_coding="match tags and phone detail",
        audio_quality="not established from real response",
        privacy_and_data_flow="audio leaves Benma for Tencent Cloud when invoked",
        cost_status="unknown until account quote/billing observation",
        latency_status="unknown; no live run",
        implementation_complexity="blocking WSS transport; pinyin serialization",
        fixture_status="documentation-contract invalid-tone fixture passing",
        lifecycle=ProviderLifecycle.FIXTURE_VALIDATED,
    ),
    ProviderResearchStatus(
        provider="iflytek_ise",
        product="Streaming Pronunciation Assessment /v2/open-ise",
        mode="cn_vip read_sentence full dimension",
        implementation="production streaming adapter implemented",
        access_and_auth="AppId/APIKey/APISecret required; absent locally",
        api_reachability="not tested without credentials",
        response_received="documentation-shaped XML example only",
        mandarin_mode="cn_vip",
        granularity="utterance, sentence, word/syllable, phone",
        tone_detection="unknown; no human-supported real runs",
        tone_diagnosis="unknown; no human-supported real runs",
        initial_detection="unknown; no human-supported real runs",
        final_detection="unknown; no human-supported real runs",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="tone score, phone tone/error fields when returned",
        timing_evidence="provider position units retained with documented inference",
        error_coding="DP and initial/final/tone error codes",
        audio_quality="rejection/exception fields retained",
        privacy_and_data_flow="audio leaves Benma for iFlytek when invoked",
        cost_status="unknown until account quote/billing observation",
        latency_status="unknown; no live run",
        implementation_complexity="multi-frame WSS plus base64 XML parsing",
        fixture_status="full-dimension XML parser fixture passing",
        lifecycle=ProviderLifecycle.FIXTURE_VALIDATED,
    ),
    ProviderResearchStatus(
        provider="azure_speech",
        product="Pronunciation Assessment zh-CN",
        mode="scripted phoneme assessment",
        implementation="existing production adapter retained",
        access_and_auth="Speech key/region required; absent locally",
        api_reachability="not tested in this pass",
        response_received="constructed replay coverage only",
        mandarin_mode="zh-CN scripted",
        granularity="utterance, word, phoneme (locale-dependent)",
        tone_detection="unsupported as explicit zh-CN hypothesis",
        tone_diagnosis="unsupported as explicit zh-CN hypothesis",
        initial_detection="unknown from real pilot",
        final_detection="unknown from real pilot",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="no supported zh-CN spoken-syllable/tone-label contract established",
        timing_evidence="provider offsets when returned",
        error_coding="provider error types retained",
        audio_quality="not established from real response",
        privacy_and_data_flow="audio leaves Benma for Azure Speech when invoked",
        cost_status="catalog estimate only; no observed bill",
        latency_status="unknown; no live Pass 4 run",
        implementation_complexity="single REST request; mainstream account path",
        fixture_status="constructed adapter fixtures passing",
        lifecycle=ProviderLifecycle.FIXTURE_VALIDATED,
    ),
    ProviderResearchStatus(
        provider="alibaba_ssecp",
        product="Smart Education Content Platform",
        mode="cn.raw.score / cn.word.score",
        implementation="documented; no transport adapter",
        access_and_auth="purchased access, warrant, and SDK provisioning required",
        api_reachability="blocked before provisioned access",
        response_received="none",
        mandarin_mode="documented Mandarin sentence/word scoring",
        granularity="sentence, word, syllable/phone fields documented",
        tone_detection="documented vector; unverified",
        tone_diagnosis="documented vector; unverified",
        initial_detection="documented; unverified",
        final_detection="documented; unverified",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="tone confidence vector documented",
        timing_evidence="documented fields require live verification",
        error_coding="documented fields require live verification",
        audio_quality="audio quality field documented",
        privacy_and_data_flow="requires vendor processing; retention terms need account review",
        cost_status="commercial access not obtained",
        latency_status="unknown",
        implementation_complexity="high until warrant/SDK provisioning is understood",
        fixture_status="none; documentation is not a captured response",
        lifecycle=ProviderLifecycle.DOCUMENTED,
    ),
    ProviderResearchStatus(
        provider="speechsuper",
        product="Mandarin scripted pronunciation assessment",
        mode="character/sentence evaluation",
        implementation="documented; no transport adapter",
        access_and_auth="trial/account and usable API documentation required",
        api_reachability="blocked before trial access",
        response_received="none",
        mandarin_mode="Mandarin demo advertises initial/final/tone",
        granularity="demo displays word/syllable dimensions",
        tone_detection="demo-visible; API unverified",
        tone_diagnosis="demo-visible; API unverified",
        initial_detection="demo-visible; API unverified",
        final_detection="demo-visible; API unverified",
        native_false_rejection="unknown; denominator 0",
        learner_false_rejection="unknown; denominator 0",
        severe_error_false_acceptance="unknown; denominator 0",
        tone_evidence="demo-visible tone dimension; API contract unverified",
        timing_evidence="unverified",
        error_coding="unverified",
        audio_quality="unverified",
        privacy_and_data_flow="requires vendor processing; terms need account review",
        cost_status="public pricing page exists; account-specific cost unverified",
        latency_status="unknown",
        implementation_complexity="unknown until trial contract is available",
        fixture_status="none",
        lifecycle=ProviderLifecycle.DOCUMENTED,
    ),
)


def provider_status_scorecard(runs: list[ProviderRun]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for status in STATIC_PROVIDER_STATUS:
        matching = [
            run
            for run in runs
            if run.provider == status.provider
            and run.status == RunStatus.SUCCEEDED
            and run.evidence_origin
            in {EvidenceOrigin.LIVE_PROVIDER, EvidenceOrigin.LIVE_CAPTURED_SANITIZED}
        ]
        row = asdict(status)
        row["observed_live_run_count"] = len(matching)
        if matching:
            row["lifecycle"] = ProviderLifecycle.LIVE_VALIDATED
            row["api_reachability"] = "reached in sanitized captured run"
            row["response_received"] = "real provider response captured and hashed"
        rows.append(row)
    return rows
