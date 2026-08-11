"""
Demo 06: Intelligent Prompt Routing
====================================

Shows how to route simple queries to cheaper models
and complex queries to more powerful models.

Two approaches:

1. Manual routing
   Classify query complexity -> route to appropriate model.

2. Managed routing
   Amazon Bedrock also provides managed Prompt Routers
   for a similar concept without implementing the routing
   logic yourself.

Production Lessons:

- 60-70% of helpdesk queries are simple.
- Simple queries can be routed to Haiku.
- Complex multi-step queries can be routed to Sonnet.
- Classification itself is very cheap.
- Routing can reduce model inference cost significantly.
- Always monitor routing accuracy.
"""

import boto3
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import (
    REGION,
    MODEL_SONNET,
    MODEL_HAIKU,
    PRICING,
)


# ============================================================
# CLIENT
# ============================================================

console = Console()

client = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


# ============================================================
# TEST QUERIES
# ============================================================

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
        "query": (
            "Compare the remote access policies across our "
            "US, EU, and APAC offices and summarize the key "
            "differences in approval workflows, considering "
            "the recent compliance updates."
        ),
        "complexity": "Complex",
    },

    {
        "query": (
            "I need to set up a multi-region disaster recovery "
            "plan for our internal tools. What are the dependencies "
            "between our VPN, SSO, and ticketing systems, and "
            "what's the recommended failover sequence?"
        ),
        "complexity": "Complex",
    },

    {
        "query": "Where is the cafeteria?",
        "complexity": "Simple",
    },
]


# ============================================================
# CLASSIFIER PROMPT
# ============================================================

CLASSIFIER_PROMPT = """
Classify the following user query as either SIMPLE or COMPLEX.

SIMPLE = factual, single-step, lookup-style
(e.g., "what are office hours?", "how do I reset password?")

COMPLEX = multi-step reasoning, comparison, planning,
or analysis required.

Query: {query}

Respond with ONLY one word: SIMPLE or COMPLEX
"""


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = (
    "You are an IT Service Desk assistant. "
    "Be concise and helpful."
)


# ============================================================
# CLASSIFY QUERY
# ============================================================

def classify_query(
    query: str
) -> str:
    """
    Use Claude Haiku to classify query complexity.

    Haiku is used because classification is a simple task
    and does not require a powerful reasoning model.
    """

    response = client.converse(
        modelId=MODEL_HAIKU,

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": CLASSIFIER_PROMPT.format(
                            query=query
                        )
                    }
                ],
            }
        ],

        inferenceConfig={
            "maxTokens": 10,
            "temperature": 0.0,
        },
    )

    classification = (
        response["output"]["message"]["content"][0]["text"]
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # Normalize classifier response
    # --------------------------------------------------------

    if "COMPLEX" in classification:
        return "COMPLEX"

    return "SIMPLE"


# ============================================================
# ROUTE AND RESPOND
# ============================================================

def route_and_respond(
    query: str,
    classification: str
) -> dict:
    """
    Route the query to the appropriate model.

    SIMPLE  -> Claude Haiku
    COMPLEX -> Claude Sonnet
    """

    if classification == "COMPLEX":

        model = MODEL_SONNET
        model_name = "Sonnet"

    else:

        model = MODEL_HAIKU
        model_name = "Haiku"

    # --------------------------------------------------------
    # Start latency timer
    # --------------------------------------------------------

    start = time.time()

    response = client.converse(
        modelId=model,

        system=[
            {
                "text": SYSTEM_PROMPT
            }
        ],

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": query
                    }
                ],
            }
        ],

        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.3,
        },
    )

    # --------------------------------------------------------
    # Calculate latency
    # --------------------------------------------------------

    latency = time.time() - start

    # --------------------------------------------------------
    # Extract usage
    # --------------------------------------------------------

    usage = response.get(
        "usage",
        {}
    )

    input_tokens = usage.get(
        "inputTokens",
        0
    )

    output_tokens = usage.get(
        "outputTokens",
        0
    )

    return {
        "model_name": model_name,

        "model_id": model,

        "response": (
            response["output"]
            ["message"]
            ["content"][0]
            ["text"]
        ),

        "input_tokens": input_tokens,

        "output_tokens": output_tokens,

        "total_tokens": (
            input_tokens +
            output_tokens
        ),

        "latency_ms": int(
            latency * 1000
        ),
    }


# ============================================================
# CALCULATE MODEL COST
# ============================================================

def calculate_cost(
    result: dict,
    pricing_key: str
) -> float:
    """
    Calculate inference cost using the configured
    input/output pricing.
    """

    input_cost = (
        result["input_tokens"]
        * PRICING[pricing_key]["input"]
        / 1000
    )

    output_cost = (
        result["output_tokens"]
        * PRICING[pricing_key]["output"]
        / 1000
    )

    return input_cost + output_cost


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # TITLE
    # ========================================================

    console.print(
        Panel(
            "[bold green]"
            "Demo 06: Intelligent Prompt Routing"
            "[/]\n"

            "Classify query complexity → "
            "route to cheapest capable model.\n"

            "Simple queries → Haiku. "
            "Complex queries → Sonnet.",

            style="green"
        )
    )

    # ========================================================
    # ROUTING STRATEGY
    # ========================================================

    console.print(
        "\n[bold]Routing Strategy:[/]"
    )

    console.print(
        "  1. Haiku classifies the query as "
        "SIMPLE or COMPLEX."
    )

    console.print(
        "  2. SIMPLE → Haiku responds "
        "(cheap + fast)."
    )

    console.print(
        "  3. COMPLEX → Sonnet responds "
        "(stronger reasoning).\n"
    )

    # ========================================================
    # AVAILABLE TEST QUERIES
    # ========================================================

    console.print(
        "[bold cyan]Available test queries:[/]"
    )

    all_queries = TEST_QUERIES + [

        {
            "query": (
                "What's the WiFi password for "
                "the guest network?"
            ),

            "complexity": "Simple",
        },

        {
            "query": (
                "Draft a migration plan to move our "
                "on-prem Active Directory to AWS SSO, "
                "including rollback procedures and a "
                "phased timeline for 5000 users across "
                "3 regions."
            ),

            "complexity": "Complex",
        },
    ]

    for idx, q in enumerate(
        all_queries,
        1
    ):

        query_preview = q["query"][:70]

        if len(q["query"]) > 70:
            query_preview += "..."

        console.print(
            f"  [{idx}] {query_preview}"
        )

    console.print(
        "\n  [bold]Running all pre-defined queries:[/]\n"
    )

    # ========================================================
    # CUSTOM QUERY
    # ========================================================

    custom_query = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else None
    )

    results = []

    if custom_query:

        console.print(
            f"[bold magenta]"
            f"CUSTOM QUERY:"
            f"[/] \"{custom_query}\"\n"
        )

        selected_queries = [
            {
                "query": custom_query,
                "complexity": "Custom",
            }
        ]

    else:

        selected_queries = TEST_QUERIES

    # ========================================================
    # PROCESS QUERIES
    # ========================================================

    for tc in selected_queries:

        query = tc["query"]

        if len(query) > 60:

            query_short = (
                query[:60] + "..."
            )

        else:

            query_short = query

        console.print(
            f"[yellow]"
            f"  Query: \"{query_short}\""
            f"[/]"
        )

        # ----------------------------------------------------
        # Step 1: Classification
        # ----------------------------------------------------

        classification = classify_query(
            query
        )

        console.print(
            f"    Classification: "
            f"[bold]{classification}[/] "
            f"(expected: {tc['complexity']})"
        )

        # ----------------------------------------------------
        # Step 2: Route
        # ----------------------------------------------------

        result = route_and_respond(
            query,
            classification
        )

        result["classification"] = (
            classification
        )

        result["expected"] = (
            tc["complexity"]
        )

        result["query"] = query

        # ----------------------------------------------------
        # Step 3: Calculate routing cost
        # ----------------------------------------------------

        if result["model_name"] == "Haiku":

            pricing_key = "claude-haiku"

        else:

            pricing_key = "claude-sonnet"

        result["routing_cost"] = (
            calculate_cost(
                result,
                pricing_key
            )
        )

        results.append(result)

        console.print(
            f"    Routed to: "
            f"[bold]{result['model_name']}[/] "
            f"| Tokens: {result['total_tokens']} "
            f"| Latency: "
            f"{result['latency_ms']}ms"
        )

        console.print(
            Panel(
                result["response"][:300]
                + (
                    "..."
                    if len(result["response"]) > 300
                    else ""
                ),
                title=(
                    f"[green]"
                    f"{result['model_name']} Response"
                    f"[/]"
                ),
                border_style="dim",
            )
        )

    # ========================================================
    # ROUTING RESULTS TABLE
    # ========================================================

    console.print("\n")

    table = Table(
        title="Routing Decisions",
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column(
        "Query",
        style="green",
        max_width=40
    )

    table.add_column(
        "Classified",
        justify="center"
    )

    table.add_column(
        "Routed To",
        justify="center"
    )

    table.add_column(
        "Tokens",
        justify="right"
    )

    table.add_column(
        "Latency",
        justify="right"
    )

    if not custom_query:

        table.add_column(
            "Expected",
            justify="center"
        )

        table.add_column(
            "Match",
            justify="center"
        )

    # --------------------------------------------------------
    # Add rows
    # --------------------------------------------------------

    for r in results:

        query_preview = r["query"][:40]

        if len(r["query"]) > 40:
            query_preview += "..."

        row = [

            query_preview,

            r["classification"],

            r["model_name"],

            str(
                r["total_tokens"]
            ),

            f"{r['latency_ms']}ms",
        ]

        if not custom_query:

            match = (
                "[green]YES[/]"
                if (
                    r["classification"].upper()
                    ==
                    r["expected"].upper()
                )
                else
                "[yellow]MISMATCH[/]"
            )

            row.extend(
                [
                    r["expected"],
                    match,
                ]
            )

        table.add_row(*row)

    console.print(table)

    # ========================================================
    # CLASSIFICATION ACCURACY
    # ========================================================

    if not custom_query and results:

        correct = sum(
            1
            for r in results
            if (
                r["classification"].upper()
                ==
                r["expected"].upper()
            )
        )

        accuracy = (
            correct / len(results)
        ) * 100

        console.print(
            "\n[bold cyan]"
            "Classification Accuracy:"
            "[/]"
        )

        console.print(
            f"  Correct classifications: "
            f"{correct}/{len(results)}"
        )

        console.print(
            f"  Accuracy: "
            f"[bold]{accuracy:.0f}%[/]"
        )

    # ========================================================
    # COST COMPARISON
    # ========================================================

    console.print(
        "\n[bold cyan]"
        "Cost Comparison: "
        "Routing vs Always-Sonnet"
        "[/]\n"
    )

    total_routing_cost = 0.0

    total_sonnet_cost = 0.0

    # --------------------------------------------------------
    # Calculate costs
    # --------------------------------------------------------

    for r in results:

        # Actual routing cost
        routing_cost = r[
            "routing_cost"
        ]

        # Cost if this exact request
        # had been handled by Sonnet
        sonnet_result = {
            "input_tokens": r[
                "input_tokens"
            ],

            "output_tokens": r[
                "output_tokens"
            ],
        }

        sonnet_cost = calculate_cost(
            sonnet_result,
            "claude-sonnet"
        )

        total_routing_cost += (
            routing_cost
        )

        total_sonnet_cost += (
            sonnet_cost
        )

    # --------------------------------------------------------
    # Savings
    # --------------------------------------------------------

    if total_sonnet_cost > 0:

        savings_pct = (
            (
                total_sonnet_cost
                - total_routing_cost
            )
            / total_sonnet_cost
        ) * 100

    else:

        savings_pct = 0

    # ========================================================
    # PROJECTED MONTHLY COST
    # ========================================================

    queries_per_day = 10000

    days_per_month = 30

    monthly_sonnet = (
        total_sonnet_cost
        * queries_per_day
        * days_per_month
        / len(results)
    )

    monthly_routing = (
        total_routing_cost
        * queries_per_day
        * days_per_month
        / len(results)
    )

    monthly_savings = (
        monthly_sonnet
        - monthly_routing
    )

    # ========================================================
    # COST TABLE
    # ========================================================

    table2 = Table(
        show_header=True,
        header_style="bold cyan"
    )

    table2.add_column(
        "Strategy",
        style="green"
    )

    table2.add_column(
        f"Test Cost ({len(results)} "
        f"{'query' if len(results) == 1 else 'queries'})",
        justify="right",
        style="yellow"
    )

    table2.add_column(
        "Projected Monthly (10K/day)",
        justify="right",
        style="bold yellow"
    )

    table2.add_row(
        "Always Sonnet",
        f"${total_sonnet_cost:.6f}",
        f"${monthly_sonnet:.2f}"
    )

    table2.add_row(
        "Intelligent Routing",
        f"${total_routing_cost:.6f}",
        f"${monthly_routing:.2f}"
    )

    table2.add_row(
        "[bold]SAVINGS[/]",
        f"[green]{savings_pct:.0f}%[/]",
        f"[green]"
        f"${monthly_savings:.2f}/month"
        f"[/]"
    )

    console.print(table2)

    # ========================================================
    # MODEL DISTRIBUTION
    # ========================================================

    haiku_count = sum(
        1
        for r in results
        if r["model_name"] == "Haiku"
    )

    sonnet_count = sum(
        1
        for r in results
        if r["model_name"] == "Sonnet"
    )

    console.print(
        "\n[bold cyan]"
        "Model Distribution:"
        "[/]"
    )

    console.print(
        f"  Haiku:  {haiku_count} "
        f"queries"
    )

    console.print(
        f"  Sonnet: {sonnet_count} "
        f"queries"
    )

    # ========================================================
    # PRODUCTION LESSONS
    # ========================================================

    console.print(
        Panel(
            "[bold green]"
            "PRODUCTION LESSONS:"
            "[/]\n\n"

            "1. Use a cheap model such as Haiku "
            "for query classification.\n\n"

            "2. Route simple factual queries to "
            "Haiku for lower cost and latency.\n\n"

            "3. Route complex reasoning, planning, "
            "comparison, and analysis queries to Sonnet.\n\n"

            "4. Classification itself requires very "
            "few tokens and is relatively inexpensive.\n\n"

            "5. Monitor routing accuracy. If complex "
            "queries are incorrectly routed to Haiku, "
            "response quality can decrease.\n\n"

            "6. Amazon Bedrock also provides managed "
            "Prompt Routers for routing between models.\n\n"

            "7. Combine routing with other production "
            "patterns such as RAG, Guardrails, and "
            "model evaluation.",

            title="Key Takeaways",

            border_style="green"
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
