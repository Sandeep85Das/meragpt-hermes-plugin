"""Tool schemas. The descriptions are what the model reads to decide when and how to call each tool."""

DECIDE = {
    "name": "meragpt_decide",
    "description": (
        "Ask meraGPT's Decider one or more typed questions about a piece of state (a message, a conversation, "
        "an alert, an agent trace, a form, a receipt) and get a calibrated probability for every answer. "
        "Use it for cheap, fast decisions mid-task: routing and triage, yes/no checks, picking a label, "
        "scoring urgency or quality, guardrails on a draft, or choosing the next tool. "
        "Question types: 'noul' is yes/no and returns the probability of yes; 'choice' picks one of the labels "
        "in criteria (an object mapping each label to a short description, 2 to 255 labels); 'score' picks a level "
        "from criteria (an ordered list of level descriptions, lowest first, 2 to 32 levels) and returns the "
        "expected level. Write 'instructions' as the question in plain words, and describe labels and levels as you "
        "would to a new colleague; the descriptions are part of what is read. When the state may not contain the "
        "answer, offer a label such as \"unknown\": \"The state does not say\" so the answer can be 'I don't know' "
        "instead of a confident guess. Act on an answer only when its probability is high enough for the task. "
        "Up to 64 questions per call; they are answered independently. Paid per input token from the user's "
        "meraGPT credit."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "state": {
                "description": "What the questions are about. Any JSON: a string, or an object such as "
                               "{\"channel\": \"email\", \"messages\": [{\"from\": \"customer\", \"text\": \"...\"}]}.",
            },
            "questions": {
                "type": "object",
                "description": "A name for each question mapped to the question, e.g. "
                               "{\"team\": {\"type\": \"choice\", \"instructions\": \"Which team should handle this?\", "
                               "\"criteria\": {\"billing\": \"Charges and refunds\", \"technical\": \"The product is not working\"}}, "
                               "\"refund\": {\"type\": \"noul\", \"instructions\": \"Is the customer asking for money back?\"}, "
                               "\"urgency\": {\"type\": \"score\", \"instructions\": \"How urgent is this?\", "
                               "\"criteria\": [\"Can wait a week\", \"Within a few days\", \"Today\", \"Immediately\"]}}",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["noul", "choice", "score"]},
                        "instructions": {"type": "string"},
                        "criteria": {"description": "choice: object label -> description. score: list of levels, lowest first. "
                                                    "noul: optional {\"true\": ..., \"false\": ...}."},
                    },
                    "required": ["type", "instructions"],
                },
            },
        },
        "required": ["state", "questions"],
    },
}

RESTYLE = {
    "name": "meragpt_restyle",
    "description": (
        "Rewrite AI-written prose with meraGPT's Restyler so it reads as if a person wrote it, keeping every fact, "
        "number, link and name. Formatting (headings, lists, code, tables) comes back as sent; a paragraph whose "
        "rewrite would have been wrong comes back unchanged. Set mode to 'strict' to keep the wording and only remove "
        "common AI tells (em dashes, exclamation marks, filler openers). A person should still read the result before "
        "it is sent or published. Up to 60,000 characters per call. Paid per token from the user's meraGPT credit."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to rewrite. Paragraphs separated by blank lines."},
            "mode": {"type": "string", "enum": ["default", "strict"],
                     "description": "'default' rewrites the prose; 'strict' only removes AI tells and changes nothing else."},
        },
        "required": ["text"],
    },
}

FANOUT = {
    "name": "meragpt_fanout",
    "description": (
        "Predict the web searches an AI assistant (ChatGPT, Claude, Gemini) is likely to run before answering a "
        "question, with meraGPT's Fanout. Use it for content and SEO/GEO research: the searches a buyer's question "
        "triggers are the searches a page has to rank for to be cited in the answer. Optionally pass the category "
        "and the brands that compete in it, so an unfamiliar brand stays in the right category. The model samples, "
        "so calling it more than once and merging the results gives a fuller picture. Paid per token from the "
        "user's meraGPT credit."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "One question someone would ask an AI assistant."},
            "category": {"type": "string", "description": "Optional. The category the question is about, e.g. 'project management tools'."},
            "brands": {"type": "array", "items": {"type": "string"},
                       "description": "Optional. Brands known to compete in the category (first 12 used)."},
        },
        "required": ["question"],
    },
}

# TODO: add meragpt_extract (POST /v1/extract) when that endpoint is generally available.
