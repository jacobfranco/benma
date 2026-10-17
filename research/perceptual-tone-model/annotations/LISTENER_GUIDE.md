# 普通话听感标注 / Mandarin listener guide — version 1.0

主要问题：**在这句话里，你认为目标音节的发音可以接受吗？**

请先听完整语句或较宽的上下文（`full_utterance_audio` / `wide`），确认目标字及其
位置，再按需要重听 `local`。`target` 单独切片仅用于定位；不要只凭单字切片判断。
`syllable_index` 从 0 开始；音频中的目标时间在每个窗口的 metadata 中给出。
切片边界有问题时，可听完整录音；仍无法确认目标时选 UNGRADABLE。

| 选项 / JSON 值 | 判断标准 |
| --- | --- |
| ACCEPTABLE / `acceptable` | 听起来足够自然、可以接受；我不会纠正。Sounds normal enough; I would not correct it. |
| BORDERLINE / `borderline` | 有明显不自然或可疑之处，但我不能有把握地说它错了。Noticeably unusual or questionable, but not confidently wrong. |
| INCORRECT / `incorrect` | 声调或发音明显有误，到了我会纠正的程度。Clearly wrong enough that I would correct it. |
| UNGRADABLE / `ungradable` | 因音质、重叠、削波、切分或目标不清等原因，无法可靠判断。Cannot judge reliably because of recording or segmentation problems. |

请判断真实连读中的自然程度，不要比照教科书声调曲线。连读变调、轻声、弱化或
个人音高差异，不一定需要纠正。与典型声调曲线不同，也可能完全可以接受。
不要把“不够典型”自动标成 INCORRECT。听不清不是 BORDERLINE。

完成主要问题后，可选回答：**目标音节听起来最像哪类声调？**
`T1` / `T2` / `T3` / `T4` / `unclear`。不想回答可填 `null`。
这个答案独立于可接受程度；不要据此改写主要判断。

请独立标注，不查看其他听者的答案或系统评分。可选 `confidence` 范围 0–1，
不使用时填 `null`；不会用于自动加权。`notes` 可记录自然语言意见，模型不会读取。

复制 `responses.template.jsonl`，每行对应一个 item，填写自己的固定匿名
`annotator_id`、全局唯一 `judgment_id`、判断以及带时区的 ISO 8601 时间（例如
`2026-10-15T15:30:00Z`）。保留 `rubric_version: "1.0"`、`origin: "human"`。
每位听者每项先提交一次 (`version: 1`, `supersedes: null`)。如需修正，另加一行，
保留旧答案；新 `judgment_id`，`version` 加 1，`supersedes` 填上一次判断 ID。

Acceptability is the primary product label. The optional tone-family answer is
never substituted for it. Raw judgments and revisions are retained separately
from researcher-derived consensus. Do not share the researcher's private map.
