---
name: meragpt-decisions
description: Use meraGPT's Decider for cheap typed decisions inside a task (routing, triage, yes/no checks, scoring, guardrails, picking a tool), Restyler to make AI-written drafts read as human, and Fanout to predict the searches an AI assistant runs for a question.
---

Use these tools when a step in the task is a small, well-defined judgement or rewrite that does not need the main model's full reasoning.

## Tools

- `meragpt_decide`: typed questions about a piece of state, each answered with a probability.
  - `noul`: yes or no. The answer is the probability of yes.
  - `choice`: pick one label. Pass `criteria` as an object mapping each label to a short description (2 to 255 labels).
  - `score`: pick a level. Pass `criteria` as an ordered list of level descriptions, lowest first (2 to 32 levels).
- `meragpt_restyle`: rewrites AI-written prose so it reads as human, keeping every fact, number, link and name. `mode: "strict"` only removes AI tells and keeps the wording.
- `meragpt_fanout`: the web searches an AI assistant is likely to run before answering a buyer's question. Pass `category` and `brands` when you know them.

## How to ask Decider well

1. Put everything the decision depends on into `state`. Decider sees only the state and the questions.
2. Write `instructions` as the question itself, in plain words.
3. Describe each label or level the way you would explain it to a new colleague; the descriptions are read.
4. If the state might not contain the answer, offer `"unknown": "The state does not say"` as a choice label, so the answer can be "I don't know" instead of a confident guess.
5. Ask several questions about the same state in one call; each is answered independently.
6. Decide in advance how sure you need to be. Act when the probability clears that bar; otherwise ask the user or take the cautious path.

## Restyler

- A person should read the rewritten text before it is sent or published.
- Paragraphs that would have been rewritten wrongly come back unchanged; `blocks` says which.
- Use strict mode for the user's own writing that only needs tells removed.

## Fanout

- The output is a set of likely searches, not a guarantee. Merging two or three calls gives a fuller set.

## Errors and cost

- Every call is billed per token to the user's meraGPT credit. Don't call in loops without a reason.
- `402`: the account is out of credit. Tell the user; don't retry.
- `429` with `retry_after_seconds`: capacity is starting up. Wait that long before one more try, or move on.
- If `MERAGPT_API_KEY` is missing, tell the user to create a key at https://meragpt.com/dashboard/keys.
