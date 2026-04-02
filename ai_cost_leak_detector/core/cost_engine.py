# cost_engine.py
# Calculates the USD cost of an OpenAI API call given model and token counts.

try:
    # Package-relative import (when used as part of a package)
    from .pricing import PRICING
except ImportError:
    # Fallback for direct execution or flat project structure
    from pricing import PRICING


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the total cost of an API call in USD.

    Args:
        model (str):          The model name (must exist in PRICING).
        input_tokens (int):   Number of prompt tokens. Must be >= 0.
        output_tokens (int):  Number of completion tokens. Must be >= 0.

    Returns:
        float: Total cost in USD.

    Raises:
        ValueError: If the model is not found in the pricing table,
                    or if token counts are negative.
    """
    if model not in PRICING:
        raise ValueError(
            f"Unknown model '{model}'. Available models: {list(PRICING.keys())}"
        )

    if input_tokens < 0:
        raise ValueError(f"input_tokens must be >= 0, got {input_tokens}.")

    if output_tokens < 0:
        raise ValueError(f"output_tokens must be >= 0, got {output_tokens}.")

    rates = PRICING[model]

    # Cost = (tokens / 1000) * rate_per_1k
    input_cost  = (input_tokens  / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]

    return input_cost + output_cost


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    examples = [
        ("gpt-4.1-mini", 1500, 300),
        ("gpt-4.1",      2000, 800),
    ]

    for model, inp, out in examples:
        cost = calculate_cost(model, inp, out)
        print(f"{model} | input={inp} tokens, output={out} tokens => ${cost:.6f}")
