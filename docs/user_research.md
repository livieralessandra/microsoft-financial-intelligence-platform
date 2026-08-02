# User research plan

## Purpose

Evaluate whether the Microsoft Financial Intelligence Platform helps its intended users understand current performance, explain material changes, identify approved business drivers, and decide what to investigate next. This is a research plan; no sessions or findings are claimed as completed.

## Proposed participants

- One finance or business student acting as a primary-user proxy.
- Two Microsoft software-engineering interns who can assess clarity and technical trust signals.
- One UTEP computer-science teaching assistant or technical reviewer.

Participation does not constitute Microsoft or UTEP endorsement. Interns participate in a personal capacity and should not share confidential employer information.

## Research questions

1. Can users determine whether Microsoft is performing well?
2. Can they identify what is driving performance?
3. Can they explain what changed from the comparison period?
4. Can they identify the main headwind?
5. Can they identify what deserves attention or further investigation?
6. Do source and classification labels improve trust or create confusion?
7. How does trust differ between AI-generated and deterministic insights?

## Neutral interview script

### Introduction

“Thank you for participating. I am evaluating the clarity and usability of a financial intelligence prototype, not your finance knowledge. The product uses public Microsoft financial disclosures. Some sessions may show deterministic insights, validated AI-generated insights, or both. Please think aloud. There are no right answers, and critical feedback is useful.”

### Background questions

1. How often do you review company financial results?
2. Which sources or tools do you normally use?
3. How comfortable are you with revenue growth and margin metrics?
4. What makes you trust or distrust an automatically generated summary?

### Task prompts

Avoid leading participants to a specific answer:

1. “Using this page, describe how Microsoft is performing in the latest period.”
2. “What appears to be driving the performance?”
3. “What changed relative to the most relevant comparison period?”
4. “What is the main headwind shown by the product?”
5. “What would you investigate next, and why?”
6. “Show me which sources or labels you used to reach your conclusions.”
7. “How confident are you in your summary, from 1 to 5?”

### Closing questions

1. What was easiest to understand?
2. What was confusing or missing?
3. Which insight presentation did you trust more, and why?
4. What would you change before using this in a meeting?

## Session procedure

1. Obtain consent and explain recording or note-taking.
2. Capture baseline familiarity without teaching the interface.
3. Start on Executive Overview and record time to the first complete answer.
4. Allow normal navigation without directing clicks.
5. Ask follow-up questions only after the participant completes each task.
6. If comparing AI and fallback content, counterbalance presentation order across participants.
7. Conduct a short debrief and confirm that no confidential information was shared.

## Observation sheet

| Participant ID | Role proxy | Task | Time | Accurate? | Confidence 1–5 | Sources used | Confusion points | Moderator notes |
|---|---|---|---:|---|---:|---|---|---|
| | | Current performance | | | | | | |
| | | Performance drivers | | | | | | |
| | | Comparison-period change | | | | | | |
| | | Main headwind | | | | | | |
| | | Investigate next | | | | | | |

Record separately whether the participant was viewing deterministic or validated AI content. Do not combine conditions in a way that obscures which experience produced the observation.

## Measures

- Time to answer each core task.
- Factual accuracy against approved context.
- Self-reported confidence on a five-point scale.
- Confusion points and navigation errors.
- Whether and how source IDs or source notes were used.
- Trust rating and explanation for AI-generated versus deterministic insights.
- Ability to distinguish reported facts, derived metrics, management explanations, and AI interpretations.

## Proposed success criteria

- At least three of four participants correctly identify latest-period revenue direction, the largest positive segment contributor, and the main headwind.
- Median time to a correct high-level performance summary is under one minute.
- No participant mistakes deterministic fallback content for AI-generated content.
- At least three participants can locate or describe the source-transparency mechanism.
- Average confidence is at least 4/5 for answers that are factually accurate.
- No critical issue causes unsupported causal or investment conclusions.

These thresholds are hypotheses for evaluation, not achieved results.

## Consent and privacy

- Participation is voluntary and may stop at any time.
- Explain whether audio, video, screen, or notes will be captured before starting.
- Use participant IDs rather than names in working notes.
- Collect only information necessary for usability analysis.
- Do not collect employer-confidential, student-record, account, credential, or financial information.
- Store notes securely and delete raw recordings according to an agreed retention period.

## Findings plan

After sessions, summarize recurring behaviors, factual errors, trust signals, and severity-ranked usability issues. Keep raw observations distinct from interpretation. Report the participant count and methodology, include contradictory evidence, and label all results as usability feedback rather than Microsoft endorsement. Until sessions occur, documentation must continue to state that user testing is pending.
