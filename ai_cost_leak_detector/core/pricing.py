# pricing.py
# OpenAI model pricing per 1,000 tokens (USD)
# Source: https://openai.com/pricing

PRICING: dict[str, dict[str, float]] = {
    "gpt-4.1-mini": {
        "input":  0.000400,  # $0.40 per 1M tokens = $0.0004 per 1K
        "output": 0.001600,  # $1.60 per 1M tokens = $0.0016 per 1K
    },
    "gpt-4.1": {
        "input":  0.002000,  # $2.00 per 1M tokens = $0.002 per 1K
        "output": 0.008000,  # $8.00 per 1M tokens = $0.008 per 1K
    },
}
