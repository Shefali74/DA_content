"""
Demo 01: Unified Converse API + Model Switching + Cross-Region Inference
========================================================================
Shows how the Converse API lets you write code ONCE and switch models instantly.
Same code works across Claude Sonnet, Haiku, and cross-region inference profiles.

Production Lessons:
- Use Converse API (not InvokeModel) for model portability
- Cross-Region Inference (CRIS) gives you higher availability at no extra cost
- Different models for different tasks = cost optimization
"""
import boto3
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import REGION, MODEL_SONNET, MODEL_HAIKU, MODEL_SONNET_CRIS, PRICING

console = Console()
client = boto3.client("bedrock-runtime", region_name=REGION)

# The same query - we'll send it to different models
QUERY = "A user's laptop is not connecting to the corporate VPN after a Windows update. What troubleshooting steps should I suggest?"

SYSTEM_PROMPT = """You are an IT Service Desk assistant. Provide concise, step-by-step 
troubleshooting guidance. Keep responses under 150 words. Be professional and helpful."""


def call_converse(model_id: str, label: str) -> dict:
    """Call Bedrock Converse API and return response with metrics."""
    start = time.time()

    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": QUERY}]}],
        inferenceConfig={
            "maxTokens": 300,  # PRODUCTION TIP: Always set this explicitly!
            "temperature": 0.3,
        },
    )

    latency = time.time() - start
    usage = response["usage"]

    return {
        "label": label,
        "model_id": model_id,
        "response": response["output"]["message"]["content"][0]["text"],
        "input_tokens": usage["inputTokens"],
        "output_tokens": usage["outputTokens"],
        "latency_ms": int(latency * 1000),
        "stop_reason": response["stopReason"],
    }


def calculate_cost(input_tokens: int, output_tokens: int, model_key: str) -> float:
    """Calculate cost in USD."""
    pricing = PRICING[model_key]
    return (input_tokens * pricing["input"] / 1000) + (output_tokens * pricing["output"] / 1000)


def main():
    console.print(Panel(
        "[bold green]Demo 01: Converse API - Write Once, Run Anywhere[/]\n"
        "Same code, same query, different models = different cost/speed tradeoffs",
        style="green"
    ))

    console.print("[dim]NOTE: Responses come from model's general knowledge (no Knowledge Base attached).[/]")
    console.print("[dim]This demo focuses on the API pattern and cost/speed comparison across models.[/]")
    console.print(f"\n[bold]Query:[/] {QUERY}\n")

    # Run against multiple models
    results = []

    console.print("[yellow]Calling Claude Sonnet (powerful, complex reasoning)...[/]")
    results.append(call_converse(MODEL_SONNET, "Claude Sonnet"))

    console.print("[yellow]Calling Claude Haiku (fast, cost-efficient)...[/]")
    results.append(call_converse(MODEL_HAIKU, "Claude Haiku"))

    console.print("[yellow]Calling Sonnet via Cross-Region Inference...[/]")
    results.append(call_converse(MODEL_SONNET_CRIS, "Sonnet (CRIS)"))

    # Display comparison table
    table = Table(title="Model Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Model", style="green")
    table.add_column("Latency", justify="right")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Cost", justify="right", style="yellow")

    for r in results:
        model_key = "claude-sonnet" if "Sonnet" in r["label"] or "CRIS" in r["label"] else "claude-haiku"
        cost = calculate_cost(r["input_tokens"], r["output_tokens"], model_key)
        table.add_row(
            r["label"],
            f"{r['latency_ms']}ms",
            str(r["input_tokens"]),
            str(r["output_tokens"]),
            f"${cost:.6f}",
        )

    console.print(table)

    # Show responses
    for r in results:
        console.print(Panel(r["response"], title=f"[bold]{r['label']}[/] Response", border_style="dim"))

    # Production lesson
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. Converse API = same code for ANY model. Switch model IDs, not code.\n"
        "2. Cross-Region Inference = same price, higher availability.\n"
        "3. Haiku handles L1 queries at 1/4 the cost of Sonnet.\n"
        "4. ALWAYS set maxTokens explicitly (default = model max = quota burn).",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
