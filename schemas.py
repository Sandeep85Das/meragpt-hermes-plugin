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

EXTRACT = {
    "name": "meragpt_extract",
    "description": (
        "Pull the fields you define out of a document with meraGPT's Extractor: an email, a contract, a form, a "
        "conversation, or a photo or scan of a receipt, invoice or page. Give it a JSON Schema for what you want and "
        "it returns one JSON object that fits the schema, with typed values: numbers as numbers, dates as YYYY-MM-DD, "
        "lists in document order. A field the document does not state comes back null instead of being guessed, so "
        "treat null as 'not in the document'. Long documents are read in windows and merged. Send either text or "
        "images (up to 6 pages of one document), not both. Paid per input token from the user's meraGPT credit; "
        "output is free."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "schema": {
                "type": "object",
                "description": "A JSON Schema object for the result, e.g. {\"type\": \"object\", \"properties\": "
                               "{\"invoice_number\": {\"type\": \"string\"}, \"total\": {\"type\": \"number\"}, "
                               "\"due_date\": {\"type\": \"string\", \"format\": \"date\"}, \"items\": {\"type\": \"array\", "
                               "\"items\": {\"type\": \"object\", \"properties\": {\"description\": {\"type\": \"string\"}, "
                               "\"amount\": {\"type\": \"number\"}}}}}}. Field descriptions are read, so say what each field means.",
            },
            "text": {"type": "string", "description": "The document as text. Leave out when sending images."},
            "images": {"type": "array", "items": {"type": "string"},
                       "description": "Pages of one document as https image URLs or base64 data URLs (up to 6). Leave out when sending text."},
            "reference_date": {"type": "string", "description": "Optional. Today's date (YYYY-MM-DD), for relative dates such as 'last Tuesday'."},
            "question": {"type": "string", "description": "Optional. A question that narrows what to extract."},
        },
        "required": ["schema"],
    },
}
