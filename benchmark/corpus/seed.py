"""Materialize the v0.1 pilot manifest from reviewable linguistic seed tables."""

from __future__ import annotations

from benchmark.models import (
    BenchmarkSample,
    CalibrationMode,
    CorpusManifest,
    DeliberateError,
    EnvironmentalCondition,
    ErrorType,
    SpeakerCategory,
)

CORPUS_VERSION = "0.1.0"


def _sample(
    sample_id: str,
    text: str | None,
    pinyin: tuple[str, ...] = (),
    tones: tuple[int, ...] = (),
    *,
    surface: tuple[str, ...] = (),
    category: SpeakerCategory = SpeakerCategory.LEARNER,
    error: DeliberateError | None = None,
    tags: tuple[str, ...] = (),
    condition: EnvironmentalCondition = EnvironmentalCondition.QUIET,
    calibration_mode: CalibrationMode | None = None,
    pair_id: str | None = None,
) -> BenchmarkSample:
    return BenchmarkSample(
        sample_id=sample_id,
        corpus_version=CORPUS_VERSION,
        speaker_category=category,
        intended_text=text,
        intended_pinyin=pinyin,
        lexical_tones=tones,
        expected_surface_tones=surface,
        deliberate_error=error,
        calibration_mode=calibration_mode,
        pair_id=pair_id,
        tags=frozenset(tags),
        environmental_condition=condition,
    )


def seed_manifest() -> CorpusManifest:
    samples: list[BenchmarkSample] = []
    isolated = [
        ("ma1", "妈", "mā", 1),
        ("ma2", "麻", "má", 2),
        ("ma3", "马", "mǎ", 3),
        ("ma4", "骂", "mà", 4),
    ]
    for isolated_code, isolated_text, isolated_pinyin, isolated_tone in isolated:
        for repetition in range(1, 4):
            samples.append(
                _sample(
                    f"isolated_{isolated_code}_correct_r{repetition}",
                    isolated_text,
                    (isolated_pinyin,),
                    (isolated_tone,),
                    category=SpeakerCategory.NATIVE_CONTROL
                    if repetition == 1
                    else SpeakerCategory.LEARNER,
                    error=DeliberateError(error_type=ErrorType.NONE),
                    tags=("isolated_tone", f"tone_{isolated_tone}", "correct_control"),
                )
            )
        wrong = 2 if isolated_tone != 2 else 3
        samples.append(
            _sample(
                f"isolated_{isolated_code}_wrong_as_t{wrong}",
                isolated_text,
                (isolated_pinyin,),
                (isolated_tone,),
                category=SpeakerCategory.INTENTIONALLY_CORRUPTED,
                error=DeliberateError(
                    error_type=ErrorType.WRONG_TONE,
                    corrupted_syllable_index=0,
                    expected_form=f"T{isolated_tone}",
                    produced_form=f"T{wrong}",
                ),
                tags=("isolated_tone", f"tone_{isolated_tone}", "deliberate_error"),
            )
        )

    tone_targets = {
        1: ("妈", "mā"),
        2: ("麻", "má"),
        3: ("马", "mǎ"),
        4: ("骂", "mà"),
    }
    for expected_tone in range(1, 5):
        text, pinyin = tone_targets[expected_tone]
        for produced_tone in range(1, 5):
            if expected_tone == produced_tone:
                continue
            pair_id = f"tone-t{expected_tone}-as-t{produced_tone}"
            samples.extend(
                [
                    _sample(
                        f"cal_{pair_id}_correct",
                        text,
                        (pinyin,),
                        (expected_tone,),
                        surface=(f"T{expected_tone}",),
                        error=DeliberateError(error_type=ErrorType.NONE),
                        calibration_mode=CalibrationMode.LEARNER_CORRECT,
                        pair_id=pair_id,
                        tags=("paired_calibration", "tone_confusion_balance", "correct_control"),
                    ),
                    _sample(
                        f"cal_{pair_id}_error",
                        text,
                        (pinyin,),
                        (expected_tone,),
                        surface=(f"T{expected_tone}",),
                        category=SpeakerCategory.INTENTIONALLY_CORRUPTED,
                        error=DeliberateError(
                            error_type=ErrorType.WRONG_TONE,
                            corrupted_syllable_index=0,
                            expected_form=f"T{expected_tone}",
                            produced_form=f"T{produced_tone}",
                        ),
                        calibration_mode=CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR,
                        pair_id=pair_id,
                        tags=("paired_calibration", "tone_confusion_balance", "deliberate_error"),
                    ),
                ]
            )

    tone_pairs = [
        ("11", "今天", ("jīn", "tiān"), (1, 1), ("T1", "T1")),
        ("12", "中国", ("zhōng", "guó"), (1, 2), ("T1", "T2")),
        ("13", "开始", ("kāi", "shǐ"), (1, 3), ("T1", "half-T3")),
        ("14", "音乐", ("yīn", "yuè"), (1, 4), ("T1", "T4")),
        ("21", "明天", ("míng", "tiān"), (2, 1), ("T2", "T1")),
        ("22", "学习", ("xué", "xí"), (2, 2), ("T2", "T2")),
        ("23", "牛奶", ("niú", "nǎi"), (2, 3), ("T2", "phrase-final-T3")),
        ("24", "文化", ("wén", "huà"), (2, 4), ("T2", "T4")),
        ("31", "北京", ("běi", "jīng"), (3, 1), ("half-T3", "T1")),
        ("32", "旅行", ("lǚ", "xíng"), (3, 2), ("half-T3", "T2")),
        ("33", "水果", ("shuǐ", "guǒ"), (3, 3), ("T2-sandhi", "T3")),
        ("34", "考试", ("kǎo", "shì"), (3, 4), ("half-T3", "T4")),
        ("41", "大家", ("dà", "jiā"), (4, 1), ("T4", "T1")),
        ("42", "具体", ("jù", "tǐ"), (4, 2), ("T4", "T2")),
        ("43", "电脑", ("diàn", "nǎo"), (4, 3), ("T4", "T3")),
        ("44", "见面", ("jiàn", "miàn"), (4, 4), ("T4", "T4")),
    ]
    for pair_code, pair_text, pair_pinyin, pair_tones, pair_surface in tone_pairs:
        samples.append(
            _sample(
                f"tone_pair_{pair_code}",
                pair_text,
                pair_pinyin,
                pair_tones,
                surface=pair_surface,
                error=DeliberateError(error_type=ErrorType.NONE),
                tags=("tone_pair_matrix", f"pair_{pair_code}"),
            )
        )

    lexical = [
        ("mai_buy", "买", ("mǎi",), (3,)),
        ("mai_sell", "卖", ("mài",), (4,)),
        ("shui_water", "水", ("shuǐ",), (3,)),
        ("shui_sleep", "睡", ("shuì",), (4,)),
        ("shenghuo", "生活", ("shēng", "huó"), (1, 2)),
        ("houmian", "后面", ("hòu", "miàn"), (4, 4)),
        ("shuijiao", "睡觉", ("shuì", "jiào"), (4, 4)),
        ("wen_kiss", "吻", ("wěn",), (3,)),
        ("wen_ask", "问", ("wèn",), (4,)),
        ("tang_soup", "汤", ("tāng",), (1,)),
        ("tang_sugar", "糖", ("táng",), (2,)),
        ("tang_lie", "躺", ("tǎng",), (3,)),
        ("tang_hot", "烫", ("tàng",), (4,)),
    ]
    for lexical_code, lexical_text, lexical_pinyin, lexical_tones in lexical:
        samples.append(
            _sample(
                f"lexical_{lexical_code}",
                lexical_text,
                lexical_pinyin,
                lexical_tones,
                error=DeliberateError(error_type=ErrorType.NONE),
                tags=("tone_sensitive_lexeme", "required_lexical"),
            )
        )

    sandhi = [
        ("33_nihao", "你好", ("nǐ", "hǎo"), (3, 3), ("T2-sandhi", "T3")),
        ("31_haochi", "好吃", ("hǎo", "chī"), (3, 1), ("half-T3", "T1")),
        ("32_haoren", "好人", ("hǎo", "rén"), (3, 2), ("half-T3", "T2")),
        ("34_haokan", "好看", ("hǎo", "kàn"), (3, 4), ("half-T3", "T4")),
        ("yi1", "第一", ("dì", "yī"), (4, 1), ("T4", "T1")),
        ("yi2", "一年", ("yì", "nián"), (1, 2), ("T4-sandhi", "T2")),
        ("yi4", "一个", ("yí", "gè"), (1, 4), ("T2-sandhi", "T4")),
        ("bu1", "不高", ("bù", "gāo"), (4, 1), ("T4", "T1")),
        ("bu4", "不是", ("bú", "shì"), (4, 4), ("T2-sandhi", "T4")),
        ("neutral_mama", "妈妈", ("mā", "ma"), (1, 5), ("T1", "neutral")),
        ("neutral_dongxi", "东西", ("dōng", "xi"), (1, 5), ("T1", "neutral")),
        ("neutral_houzi", "猴子", ("hóu", "zi"), (2, 5), ("T2", "neutral")),
    ]
    for sandhi_code, sandhi_text, sandhi_pinyin, sandhi_tones, sandhi_surface in sandhi:
        samples.append(
            _sample(
                f"sandhi_{sandhi_code}",
                sandhi_text,
                sandhi_pinyin,
                sandhi_tones,
                surface=sandhi_surface,
                error=DeliberateError(error_type=ErrorType.NONE),
                tags=("tone_sandhi", "surface_tone"),
            )
        )

    segmentals = [
        ("z_zh", "早 / 找", ("zǎo", "zhǎo"), (3, 3)),
        ("c_ch", "擦 / 叉", ("cā", "chā"), (1, 1)),
        ("s_sh", "四 / 是", ("sì", "shì"), (4, 4)),
        ("j_zh", "鸡 / 知", ("jī", "zhī"), (1, 1)),
        ("q_ch", "七 / 吃", ("qī", "chī"), (1, 1)),
        ("x_sh", "西 / 师", ("xī", "shī"), (1, 1)),
        ("x_s", "洗 / 死", ("xǐ", "sǐ"), (3, 3)),
        ("u_v", "路 / 绿", ("lù", "lǜ"), (4, 4)),
        ("n_ng_en_eng", "真 / 争", ("zhēn", "zhēng"), (1, 1)),
        ("n_ng_in_ing", "亲 / 清", ("qīn", "qīng"), (1, 1)),
        ("asp_b_p", "八 / 趴", ("bā", "pā"), (1, 1)),
        ("asp_d_t", "到 / 套", ("dào", "tào"), (4, 4)),
        ("asp_g_k", "高 / 考", ("gāo", "kǎo"), (1, 3)),
        ("asp_j_q", "鸡 / 七", ("jī", "qī"), (1, 1)),
        ("asp_z_c", "早 / 草", ("zǎo", "cǎo"), (3, 3)),
        ("asp_zh_ch", "找 / 炒", ("zhǎo", "chǎo"), (3, 3)),
        ("mandarin_r", "人", ("rén",), (2,)),
        ("compound_xue", "学", ("xué",), (2,)),
        ("compound_qiong", "穷", ("qióng",), (2,)),
        ("compound_guang", "光", ("guāng",), (1,)),
    ]
    for segment_code, segment_text, segment_pinyin, segment_tones in segmentals:
        samples.append(
            _sample(
                f"segmental_{segment_code}",
                segment_text,
                segment_pinyin,
                segment_tones,
                tags=("initial_final_contrast", segment_code),
            )
        )

    segment_calibration = [
        ("initial_z_zh", ErrorType.WRONG_INITIAL, "早", "zǎo", 3, "zhǎo"),
        ("initial_zh_z", ErrorType.WRONG_INITIAL, "找", "zhǎo", 3, "zǎo"),
        ("initial_c_ch", ErrorType.WRONG_INITIAL, "擦", "cā", 1, "chā"),
        ("initial_q_ch", ErrorType.WRONG_INITIAL, "七", "qī", 1, "chī"),
        ("initial_s_sh", ErrorType.WRONG_INITIAL, "四", "sì", 4, "shì"),
        ("initial_j_zh", ErrorType.WRONG_INITIAL, "鸡", "jī", 1, "zhī"),
        ("initial_x_s", ErrorType.WRONG_INITIAL, "洗", "xǐ", 3, "sǐ"),
        ("final_u_v", ErrorType.WRONG_FINAL, "路", "lù", 4, "lǜ"),
        ("final_v_u", ErrorType.WRONG_FINAL, "绿", "lǜ", 4, "lù"),
        ("final_en_eng", ErrorType.WRONG_FINAL, "真", "zhēn", 1, "zhēng"),
        ("final_eng_en", ErrorType.WRONG_FINAL, "争", "zhēng", 1, "zhēn"),
        ("final_in_ing", ErrorType.WRONG_FINAL, "亲", "qīn", 1, "qīng"),
        ("final_ing_in", ErrorType.WRONG_FINAL, "清", "qīng", 1, "qīn"),
        ("final_an_ang", ErrorType.WRONG_FINAL, "饭", "fàn", 4, "fàng"),
    ]
    for pair_id, error_type, text, pinyin, tone, produced in segment_calibration:
        mode = (
            CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR
            if error_type == ErrorType.WRONG_INITIAL
            else CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR
        )
        samples.extend(
            [
                _sample(
                    f"cal_{pair_id}_correct",
                    text,
                    (pinyin,),
                    (tone,),
                    error=DeliberateError(error_type=ErrorType.NONE),
                    calibration_mode=CalibrationMode.LEARNER_CORRECT,
                    pair_id=pair_id,
                    tags=("paired_calibration", "segmental_calibration", "correct_control"),
                ),
                _sample(
                    f"cal_{pair_id}_error",
                    text,
                    (pinyin,),
                    (tone,),
                    category=SpeakerCategory.INTENTIONALLY_CORRUPTED,
                    error=DeliberateError(
                        error_type=error_type,
                        corrupted_syllable_index=0,
                        expected_form=pinyin,
                        produced_form=produced,
                    ),
                    calibration_mode=mode,
                    pair_id=pair_id,
                    tags=("paired_calibration", "segmental_calibration", "deliberate_error"),
                ),
            ]
        )

    sentences = [
        (
            "beijing",
            "我明天想去北京。",
            ("wǒ", "míng", "tiān", "xiǎng", "qù", "běi", "jīng"),
            (3, 2, 1, 3, 4, 3, 1),
        ),
        (
            "shuijiao",
            "他吃完饭以后想睡觉。",
            ("tā", "chī", "wán", "fàn", "yǐ", "hòu", "xiǎng", "shuì", "jiào"),
            (1, 1, 2, 4, 3, 4, 3, 4, 4),
        ),
        (
            "houmian",
            "商店就在学校后面。",
            ("shāng", "diàn", "jiù", "zài", "xué", "xiào", "hòu", "miàn"),
            (1, 4, 4, 4, 2, 4, 4, 4),
        ),
    ]
    variants = [
        ("control", ErrorType.NONE, None),
        ("wrong_tone", ErrorType.WRONG_TONE, 3),
        ("wrong_initial", ErrorType.WRONG_INITIAL, 1),
        ("wrong_final", ErrorType.WRONG_FINAL, 2),
        ("sub_syllable", ErrorType.SUBSTITUTED_SYLLABLE, 4),
        ("sub_word", ErrorType.SUBSTITUTED_WORD, None),
        ("omission", ErrorType.OMITTED_SYLLABLE, 2),
        ("americanized", ErrorType.AMERICANIZED, None),
        ("bad_prosody", ErrorType.DISTORTED_PROSODY, None),
    ]
    for sentence_index, (
        sentence_code,
        sentence_text,
        sentence_pinyin,
        sentence_tones,
    ) in enumerate(sentences):
        for variant, error_type, index in variants:
            error = DeliberateError(
                error_type=error_type,
                corrupted_syllable_index=index,
                expected_form=sentence_pinyin[index] if index is not None else None,
                produced_form="deliberately varied at recording time"
                if error_type != ErrorType.NONE
                else None,
            )
            samples.append(
                _sample(
                    f"sentence_{sentence_code}_{variant}",
                    sentence_text,
                    sentence_pinyin,
                    sentence_tones,
                    category=(
                        SpeakerCategory.NATIVE_CONTROL
                        if error_type == ErrorType.NONE
                        else SpeakerCategory.INTENTIONALLY_CORRUPTED
                    ),
                    error=error,
                    tags=(
                        "sentence_corruption",
                        variant,
                        "adversarial_context" if sentence_index < 2 else "sentence_set",
                    ),
                )
            )

    controls = [
        ("silence", None, EnvironmentalCondition.SILENCE, ("negative_control", "silence")),
        ("nonsense_1", None, EnvironmentalCondition.QUIET, ("negative_control", "nonsense")),
        ("nonsense_2", None, EnvironmentalCondition.QUIET, ("negative_control", "nonsense")),
        (
            "clipped",
            "今天天气很好。",
            EnvironmentalCondition.CLIPPED,
            ("negative_control", "clipped"),
        ),
        (
            "low_volume",
            "今天天气很好。",
            EnvironmentalCondition.LOW_VOLUME,
            ("negative_control", "low_volume"),
        ),
        ("room_noise", "今天天气很好。", EnvironmentalCondition.ROOM_NOISE, ("noise_control",)),
        (
            "background_talk",
            "今天天气很好。",
            EnvironmentalCondition.BACKGROUND_CONVERSATION,
            ("noise_control",),
        ),
        (
            "exaggerated",
            "你好。",
            EnvironmentalCondition.QUIET,
            ("delivery_control", "exaggerated"),
        ),
        ("very_slow", "你好。", EnvironmentalCondition.QUIET, ("delivery_control", "slow")),
        ("fast", "你好。", EnvironmentalCondition.QUIET, ("delivery_control", "fast")),
        (
            "omitted_target",
            "今天天气很好。",
            EnvironmentalCondition.QUIET,
            ("negative_control", "omitted_speech"),
        ),
        (
            "unrelated_clear_speech",
            "今天天气很好。",
            EnvironmentalCondition.QUIET,
            ("negative_control", "unrelated_speech"),
        ),
        (
            "distorted_audio",
            "今天天气很好。",
            EnvironmentalCondition.CLIPPED,
            ("negative_control", "distorted_audio"),
        ),
        (
            "mild_babble",
            "今天天气很好。",
            EnvironmentalCondition.BACKGROUND_CONVERSATION,
            ("negative_control", "mild_noise"),
        ),
        (
            "nonsense_3",
            None,
            EnvironmentalCondition.QUIET,
            ("negative_control", "mandarin_nonsense"),
        ),
    ]
    for control_code, control_text, control_condition, control_tags in controls:
        samples.append(
            _sample(
                f"control_{control_code}",
                control_text,
                category=SpeakerCategory.INTENTIONALLY_CORRUPTED,
                condition=control_condition,
                calibration_mode=(
                    CalibrationMode.NEGATIVE_CONTROL
                    if "negative_control" in control_tags
                    else None
                ),
                tags=control_tags,
            )
        )

    for code, text, native_pinyin, native_tones in (
        ("native_nihao", "你好", ("nǐ", "hǎo"), (3, 3)),
        ("native_zhongguo", "中国", ("zhōng", "guó"), (1, 2)),
        ("native_beijing", "北京", ("běi", "jīng"), (3, 1)),
    ):
        samples.append(
            _sample(
                code,
                text,
                native_pinyin,
                native_tones,
                category=SpeakerCategory.NATIVE_CONTROL,
                error=DeliberateError(error_type=ErrorType.NONE),
                calibration_mode=CalibrationMode.NATIVE_CONTROL,
                tags=("native_control", "calibration_control"),
            )
        )

    return CorpusManifest(
        corpus_id="benma-mandarin-truthfulness",
        corpus_version=CORPUS_VERSION,
        desired_sample_count=384,
        description=(
            "Pilot prompts for truthfulness, tone/segment diagnosis, sandhi, adversarial context, "
            "and controls. Planned entries become recordings without schema changes."
        ),
        samples=tuple(samples),
    )
