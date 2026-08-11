"""
Demo 02: CountTokens API - The Tokenizer You Didn't Know You Needed
====================================================================
Shows how to estimate token usage BEFORE sending requests.
This is the #1 production optimization most teams miss.

Production Lessons:
- CountTokens lets you estimate cost before inference
- The max_tokens DEFAULT is a silent budget killer
- Optimizing prompts from 500 tokens to 200 tokens = 60% savings on input
"""
import os
import sys
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import REGION, MODEL_SONNET, MODEL_HAIKU, PRICING


# ---------------------------------------------------------
# MOCK / AWS MODE
# ---------------------------------------------------------

# Default to MOCK mode because we don't have AWS credentials.
USE_MOCK = os.getenv(
    "USE_MOCK_BEDROCK",
    "true"
).lower() == "true"


# 02_count_tokens.py is inside demo/
# Go one level up to elevate_infosys_2026/
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, PROJECT_ROOT)


if USE_MOCK:

    # Use our local mock instead of Amazon Bedrock.
    from mock_bedrock import MockBedrockClient

    client = MockBedrockClient()

else:

    # Use real Amazon Bedrock.
    import boto3

    client = boto3.client(
        "bedrock-runtime",
        region_name=REGION
    )


console = Console()

# CountTokens requires base model IDs (not cross-region inference profiles)
COUNT_TOKENS_MODEL_SONNET = "anthropic.claude-sonnet-4-5-20250929-v1:0"
COUNT_TOKENS_MODEL_HAIKU = "anthropic.claude-haiku-4-5-20251001-v1:0"


def count_tokens(model_id: str, messages: list, system: list = None) -> dict:
    """Count tokens for a given input without making an inference call."""
    converse_input = {
        "messages": messages
    }
    if system:
        converse_input["system"] = system

    response = client.count_tokens(
        modelId=model_id,
        input={"converse": converse_input}
    )
    return response


def main():
    console.print(Panel(
        "[bold green]Demo 02: CountTokens - Know Your Cost Before You Spend[/]\n"
        "Estimate token usage BEFORE inference. Optimize prompts. Save money.",
        style="green"
    ))

    # ============================================================
    # Scenario 1: Verbose prompt vs Optimized prompt
    # ============================================================
    console.print("\n[bold cyan]SCENARIO 1: Verbose vs Optimized Prompt[/]\n")

    console.print("[bold]User query:[/] \"My laptop won't connect to VPN after the Windows update last night.\"\n")

    console.print("[bold red]VERBOSE system prompt (what most teams write):[/]")
    console.print("  [dim]\"You are an advanced artificial intelligence powered IT Service Desk[/]", highlight=False)
    console.print("  [dim]assistant that has been specifically designed and trained to help employees...[/]", highlight=False)
    console.print("  [dim]...Always ask clarifying questions if the user query is ambiguous or unclear.\"[/]", highlight=False)

    console.print("\n[bold green]OPTIMIZED system prompt (same quality, fewer tokens):[/]")
    console.print("  [dim]\"IT helpdesk assistant. Provide concise step-by-step troubleshooting.[/]", highlight=False)
    console.print("  [dim]Be professional. Ask clarifying questions if the query is ambiguous.\"[/]\n", highlight=False)

    verbose_system = """You are an advanced artificial intelligence powered IT Service Desk 
    assistant that has been specifically designed and trained to help employees of our 
    organization with their technology-related questions, issues, and concerns. Your primary 
    objective is to provide detailed, comprehensive, step-by-step troubleshooting guidance 
    that is easy to follow and understand. You should always maintain a professional and 
    helpful demeanor in all of your interactions with users. Please ensure that your 
    responses are thorough and cover all possible angles of the problem being presented to 
    you. Always ask clarifying questions if the user's query is ambiguous or unclear."""

    optimized_system = """IT helpdesk assistant. Provide concise step-by-step troubleshooting. 
    Be professional. Ask clarifying questions if the query is ambiguous."""

    user_message = "My laptop won't connect to VPN after the Windows update last night."

    messages = [{"role": "user", "content": [{"text": user_message}]}]

    # Count tokens for verbose prompt
    verbose_result = count_tokens(
        COUNT_TOKENS_MODEL_SONNET,
        messages,
        system=[{"text": verbose_system}]
    )

    # Count tokens for optimized prompt
    optimized_result = count_tokens(
        COUNT_TOKENS_MODEL_SONNET,
        messages,
        system=[{"text": optimized_system}]
    )

    table = Table(title="Token Count Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Prompt Version", style="green")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Est. Input Cost (Sonnet)", justify="right", style="yellow")
    table.add_column("Savings", justify="right", style="bold green")

    verbose_tokens = verbose_result["inputTokens"]
    optimized_tokens = optimized_result["inputTokens"]
    savings_pct = ((verbose_tokens - optimized_tokens) / verbose_tokens) * 100

    verbose_cost = verbose_tokens * PRICING["claude-sonnet"]["input"] / 1000
    optimized_cost = optimized_tokens * PRICING["claude-sonnet"]["input"] / 1000

    table.add_row("Verbose", str(verbose_tokens), f"${verbose_cost:.6f}", "-")
    table.add_row("Optimized", str(optimized_tokens), f"${optimized_cost:.6f}", f"{savings_pct:.0f}%")

    console.print(table)

    # ============================================================
    # Scenario 2: The max_tokens TRAP
    # ============================================================
    console.print("\n[bold cyan]SCENARIO 2: The max_tokens Default Trap[/]\n")

    console.print(Panel(
        "[bold red]THE SILENT BUDGET KILLER[/]\n\n"
        "When you DON'T set max_tokens, Bedrock reserves the model's MAXIMUM:\n"
        "- Claude Sonnet: [bold]64,000 tokens reserved per request[/]\n"
        "- Your actual output: ~150 tokens\n\n"
        "This means Bedrock reserves 64K of your TPM quota PER REQUEST.\n"
        "With 100 concurrent requests, that's 6.4M tokens/min of quota burned!\n\n"
        "[bold green]FIX:[/] Always set maxTokens to your expected output size + buffer.\n"
        "For helpdesk responses: maxTokens=500 is plenty.",
        title="WARNING: max_tokens Default",
        border_style="red",
    ))

    # Show the math
    console.print("\n[bold]Quota Impact Calculation:[/]")

    table2 = Table(show_header=True, header_style="bold cyan")
    table2.add_column("Setting", style="green")
    table2.add_column("Reserved per Request", justify="right")
    table2.add_column("100 Concurrent Reqs", justify="right")
    table2.add_column("TPM Quota Used", justify="right", style="yellow")

    table2.add_row("max_tokens NOT SET", "64,000 tokens", "6,400,000 TPM", "[red]THROTTLED[/]")
    table2.add_row("max_tokens = 500", "500 tokens", "50,000 TPM", "[green]SAFE[/]")

    console.print(table2)

    # ============================================================
    # Scenario 3: Compare costs across models
    # ============================================================
    console.print("\n[bold cyan]SCENARIO 3: Same Input - Different Model Costs[/]\n")

    # Count for both models
    sonnet_count = count_tokens(COUNT_TOKENS_MODEL_SONNET, messages, [{"text": optimized_system}])
    haiku_count = count_tokens(COUNT_TOKENS_MODEL_HAIKU, messages, [{"text": optimized_system}])

    table3 = Table(title="Cost per Model (same input)", show_header=True, header_style="bold cyan")
    table3.add_column("Model", style="green")
    table3.add_column("Input Tokens", justify="right")
    table3.add_column("Cost per Call", justify="right", style="yellow")
    table3.add_column("Cost per 10K Calls", justify="right", style="bold yellow")

    for model_name, count, pricing_key in [
        ("Claude Sonnet", sonnet_count, "claude-sonnet"),
        ("Claude Haiku", haiku_count, "claude-haiku"),
    ]:
        tokens = count["inputTokens"]
        cost_per_call = tokens * PRICING[pricing_key]["input"] / 1000
        cost_10k = cost_per_call * 10000
        table3.add_row(model_name, str(tokens), f"${cost_per_call:.6f}", f"${cost_10k:.2f}")

    console.print(table3)

    # Production lessons
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. Use CountTokens API to estimate costs BEFORE inference\n"
        "2. Optimize system prompts - shorter = cheaper (same quality!)\n"
        "3. ALWAYS set max_tokens explicitly (prevents quota starvation)\n"
        "4. Route simple queries to Haiku (4x cheaper than Sonnet)\n"
        "5. At scale: 10K calls/day, prompt optimization saves $100s/month",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
