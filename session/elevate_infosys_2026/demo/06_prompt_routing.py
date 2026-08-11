"""
Demo 06: Intelligent Prompt Routing - Smart Cost Optimization
==============================================================
Shows how to route simple queries to cheaper models and complex queries
to powerful models. This pattern reduces cost by 30-50%.

Two approaches shown:
1. Manual routing (classify complexity → route to right model)
2. Mention of Bedrock Prompt Router (managed, zero-code option)

Production Lessons:
- 60-70% of helpdesk queries are simple → route to Haiku
- Complex multi-step queries need Sonnet's reasoning power
- Classification itself costs almost nothing (few tokens)
"""
import boto3
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import REGION, MODEL_SONNET, MODEL_HAIKU, PRICING

console = Console()
client = boto3.client("bedrock-runtime", region_name=REGION)

# Mix of simple and complex queries
TEST_QUERIES = [
    {
        "query": "What are the office hours?",
        "complexity": "Simple",
    },
    {
        "query": "How do I reset my password?",
        "complexity": "Simple",
    },
    {
        "query": "Compare the remote access policies across our US, EU, and APAC offices and summarize the key differences in approval workflows, considering the recent compliance updates.",
        "complexity": "Complex",
    },
    {
        "query": "I need to set up a multi-region disaster recovery plan for our internal tools. What are the dependencies between our VPN, SSO, and ticketing systems, and what's the recommended failover sequence?",
        "complexity": "Complex",
    },
    {
        "query": "Where is the cafeteria?",
        "complexity": "Simple",
    },
]

CLASSIFIER_PROMPT = """Classify the following user query as either SIMPLE or COMPLEX.

SIMPLE = factual, single-step, lookup-style (e.g., "what are office hours?", "how do I reset password?")
COMPLEX = multi-step reasoning, comparison, planning, or analysis required.

Query: {query}

Respond with ONLY one word: SIMPLE or COMPLEX"""

SYSTEM_PROMPT = "You are an IT Service Desk assistant. Be concise and helpful."


def classify_query(query: str) -> str:
    """Use Haiku to classify query complexity (cheap classification)."""
    response = client.converse(
        modelId=MODEL_HAIKU,
        messages=[{"role": "user", "content": [{"text": CLASSIFIER_PROMPT.format(query=query)}]}],
        inferenceConfig={"maxTokens": 10, "temperature": 0.0},
    )
    classification = response["output"]["message"]["content"][0]["text"].strip().upper()
    return "COMPLEX" if "COMPLEX" in classification else "SIMPLE"


def route_and_respond(query: str, classification: str) -> dict:
    """Route to appropriate model based on classification."""
    model = MODEL_SONNET if classification == "COMPLEX" else MODEL_HAIKU
    model_name = "Sonnet" if classification == "COMPLEX" else "Haiku"

    start = time.time()
    response = client.converse(
        modelId=model,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": query}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0.3},
    )
    latency = time.time() - start
    usage = response["usage"]

    return {
        "model_name": model_name,
        "response": response["output"]["message"]["content"][0]["text"],
        "input_tokens": usage["inputTokens"],
        "output_tokens": usage["outputTokens"],
        "latency_ms": int(latency * 1000),
    }


def main():
    console.print(Panel(
        "[bold green]Demo 06: Intelligent Prompt Routing[/]\n"
        "Classify query complexity → route to cheapest capable model.\n"
        "Simple queries (65%) → Haiku. Complex queries (35%) → Sonnet.",
        style="green"
    ))

    console.print("\n[bold]Routing Strategy:[/]")
    console.print("  1. Haiku classifies query as SIMPLE or COMPLEX (costs ~$0.00001)")
    console.print("  2. SIMPLE → Haiku responds (cheap + fast)")
    console.print("  3. COMPLEX → Sonnet responds (powerful reasoning)\n")

    # Interactive query selection
    console.print("[bold cyan]Available test queries:[/]")
    all_queries = TEST_QUERIES + [
        {"query": "What's the WiFi password for the guest network?", "complexity": "Simple"},
        {"query": "Draft a migration plan to move our on-prem Active Directory to AWS SSO, including rollback procedures and a phased timeline for 5000 users across 3 regions.", "complexity": "Complex"},
    ]
    for idx, q in enumerate(all_queries, 1):
        console.print(f"  [{idx}] {q['query'][:70]}{'...' if len(q['query']) > 70 else ''}")
    console.print(f"\n  [bold]Running all pre-defined queries:[/]\n")

    # Check for custom query passed as command-line argument
    custom_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None

    results = []

    if custom_query:
        console.print(f"[bold magenta]CUSTOM QUERY:[/] \"{custom_query}\"\n")
        selected_queries = [{"query": custom_query, "complexity": "Custom"}]
    else:
        selected_queries = TEST_QUERIES

    for tc in selected_queries:
        query_short = tc["query"][:60] + "..." if len(tc["query"]) > 60 else tc["query"]
        console.print(f"[yellow]  Query: \"{query_short}\"[/]")

        # Step 1: Classify
        classification = classify_query(tc["query"])
        console.print(f"    Classification: [bold]{classification}[/] (expected: {tc['complexity']})")

        # Step 2: Route and respond
        result = route_and_respond(tc["query"], classification)
        result["classification"] = classification
        result["expected"] = tc["complexity"]
        result["query"] = tc["query"]
        results.append(result)

        console.print(f"    Routed to: [bold]{result['model_name']}[/] | Latency: {result['latency_ms']}ms\n")

    # Results table
    console.print("")
    table = Table(title="Routing Decisions", show_header=True, header_style="bold cyan")
    table.add_column("Query", style="green", max_width=40)
    table.add_column("Classified", justify="center")
    table.add_column("Routed To", justify="center")
    table.add_column("Tokens", justify="right")
    if not custom_query:
        table.add_column("Expected", justify="center")
        table.add_column("Match", justify="center")

    for r in results:
        row = [
            r["query"][:40] + ("..." if len(r["query"]) > 40 else ""),
            r["classification"],
            r["model_name"],
            f"{r['input_tokens']+r['output_tokens']}",
        ]
        if not custom_query:
            match = "[green]YES[/]" if r["classification"].upper() == r["expected"].upper() else "[yellow]MISMATCH[/]"
            row.extend([r["expected"], match])
        table.add_row(*row)

    console.print(table)

    # Cost comparison
    console.print("\n[bold cyan]Cost Comparison: Routing vs Always-Sonnet[/]\n")

    total_routing_cost = 0
    total_sonnet_cost = 0

    for r in results:
        # Actual routing cost
        pricing_key = "claude-haiku" if r["model_name"] == "Haiku" else "claude-sonnet"
        routing_cost = (r["input_tokens"] * PRICING[pricing_key]["input"] / 1000 +
                       r["output_tokens"] * PRICING[pricing_key]["output"] / 1000)

        # If we always used Sonnet
        sonnet_cost = (r["input_tokens"] * PRICING["claude-sonnet"]["input"] / 1000 +
                      r["output_tokens"] * PRICING["claude-sonnet"]["output"] / 1000)

        total_routing_cost += routing_cost
        total_sonnet_cost += sonnet_cost

    savings_pct = ((total_sonnet_cost - total_routing_cost) / total_sonnet_cost) * 100

    table2 = Table(show_header=True, header_style="bold cyan")
    table2.add_column("Strategy", style="green")
    table2.add_column(f"Total Cost ({len(results)} {'query' if len(results) == 1 else 'queries'})", justify="right", style="yellow")
    table2.add_column("Projected Monthly (10K/day)", justify="right", style="bold yellow")

    table2.add_row("Always Sonnet", f"${total_sonnet_cost:.6f}", f"${total_sonnet_cost * 10000 * 30:.2f}")
    table2.add_row("Intelligent Routing", f"${total_routing_cost:.6f}", f"${total_routing_cost * 10000 * 30:.2f}")
    table2.add_row("[bold]SAVINGS[/]", f"[green]{savings_pct:.0f}%[/]", f"[green]${(total_sonnet_cost - total_routing_cost) * 10000 * 30:.2f}/month[/]")

    console.print(table2)

    # Production lessons
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. Classification with Haiku costs ~$0.00001 per query (negligible)\n"
        "2. 60-70% of helpdesk traffic is simple → massive savings routing to Haiku\n"
        "3. Bedrock also offers managed Prompt Routers (zero-code, same concept)\n"
        "4. Monitor routing accuracy - if complex queries go to Haiku, quality drops\n"
        "5. Combine with CRIS for both cost optimization AND availability",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
