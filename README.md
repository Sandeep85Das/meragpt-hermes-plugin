# meraGPT Decider for Hermes Agent

Give Hermes agents meraGPT's task models as tools: typed decisions with calibrated probabilities, rewriting AI drafts so they read as human, and predicting the searches an AI assistant runs. Every call uses your own meraGPT API key and credit.

meraGPT is a product of Okyasoft Pte Ltd, Singapore.

## Tools

| Tool | Model | What it does |
|---|---|---|
| `meragpt_decide` | Decider | Answers typed questions about any state (a message, a conversation, an alert, an agent trace) with a probability for every answer: yes/no (`noul`), one of several labels (`choice`), or a level on a scale (`score`). It can answer "I don't know" when you offer that option. Good for routing, triage, guardrails and picking a tool mid-task. |
| `meragpt_restyle` | Restyler | Rewrites AI-written prose so it reads as if a person wrote it, keeping facts, numbers, links and names. `mode: "strict"` only removes AI tells. Have a person read the result before it is sent. |
| `meragpt_fanout` | Fanout | Returns the web searches an AI assistant is likely to run before answering a buyer's question, optionally guided by a category and known brands. |

The plugin also registers a skill, `meragpt:meragpt-decisions`, describing when and how to use the tools.

## Setup

1. Create an API key at <https://meragpt.com/dashboard/keys>. New accounts get $1 of free credit.
2. Install the plugin:

   ```bash
   hermes plugins install meragpt
   ```

   Hermes asks for `MERAGPT_API_KEY` and stores it as a secret. You can also set it later as a Hermes secret or environment variable.
3. Ask, for example: "Route this support email to the right team and tell me how urgent it is."

## Example: a routing decision

```json
{
  "state": {"channel": "email", "messages": [{"from": "customer", "text": "The export button is greyed out and I need this report for a 3pm meeting."}]},
  "questions": {
    "team": {"type": "choice", "instructions": "Which team should handle this?",
             "criteria": {"billing": "Charges, invoices and refunds.", "technical": "The product is not working as expected.", "account": "Login, plan changes and access."}},
    "refund_requested": {"type": "noul", "instructions": "Is the customer asking for money back?"}
  }
}
```

The answer gives a probability per label (here `technical` is the likely team) and the probability that a refund was asked for, so the agent acts only when it is sure enough.

## Pricing

Usage is billed per token from your meraGPT credit, after the $1 of free credit:

| Model | Input | Output |
|---|---|---|
| Decider | $0.04 per 1M tokens | free |
| Restyler | $0.04 per 1M tokens | $0.16 per 1M tokens |
| Fanout | $0.04 per 1M tokens | $0.16 per 1M tokens |

Current prices are at <https://meragpt.com>.

## Disclosure

- **Network calls:** every tool call sends its input (the state and questions, the text to rewrite, or the question) to `https://meragpt.com/v1`, run by Okyasoft Pte Ltd. Nothing else is contacted. See meraGPT's privacy policy at <https://meragpt.com/privacy>.
- **Credentials:** the plugin reads your API key only through Hermes's secret scope (`MERAGPT_API_KEY`). The key is never stored in this repository, logged, or returned to the model.
- **Cost:** calls are paid per token from your meraGPT credit after the $1 free credit. A 402 response means the credit has run out; the plugin reports it and does not retry.
- **No background activity:** no shell commands, no file reads outside the plugin, no background processes, no telemetry.

## Development

```bash
python -m unittest discover -s tests
hermes plugins validate . --install-deps
```

The tests mock HTTP and make no network calls.

## License

MIT
