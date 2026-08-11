"""
Demo 07: Token Economics - The Full Cost Picture
=======================================================
Calculates the total cost of running the IT Helpdesk agent at scale.
Shows cost breakdown per feature and demonstrates optimization impact.

This is the "show me the money" slide of the demo.
"""
import boto3
import json
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import PRICING, REGION

console = Console()

# ============================================================
# Assumptions for a production IT Helpdesk
# ============================================================
SCENARIO = {
    "conversations_per_day": 1000,
    "avg_turns_per_conversation": 3,
    "working_days_per_month": 22,
    "avg_input_tokens_per_turn": 250,    # System prompt + user query + context
    "avg_output_tokens_per_turn": 200,   # Model response
    "avg_kb_retrieval_tokens": 500,      # RAG context injected
    "pct_simple_queries": 0.65,          # Goes to Haiku via routing
    "pct_complex_queries": 0.35,         # Goes to Sonnet
}

# Guardrail evaluation adds ~100 tokens overhead per call
GUARDRAIL_OVERHEAD_TOKENS = 100

# Evaluation runs (batch, not per-request)
EVAL_RUNS_PER_MONTH = 4  # Weekly eval batch
EVAL_SAMPLES_PER_RUN = 100


def fetch_real_metrics():
    """Try to fetch real CloudWatch metrics for Bedrock usage."""
    try:
        cw = boto3.client("cloudwatch", region_name=REGION)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)

        # Get InputTokenCount for last 7 days
        response = cw.get_metric_statistics(
            Namespace="AWS/Bedrock",
            MetricName="InputTokenCount",
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # Daily
            Statistics=["Sum"],
        )

        if response["Datapoints"]:
            total_input = sum(dp["Sum"] for dp in response["Datapoints"])
            days = len(response["Datapoints"])

            # Get OutputTokenCount
            response2 = cw.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName="OutputTokenCount",
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Sum"],
            )
            total_output = sum(dp["Sum"] for dp in response2["Datapoints"]) if response2["Datapoints"] else 0

            return {
                "available": True,
                "input_tokens_7d": int(total_input),
                "output_tokens_7d": int(total_output),
                "days": days,
            }
        return {"available": False}
    except Exception:
        return {"available": False}


def calculate_baseline_cost():
    """Cost without any optimization (all Sonnet, no routing, default max_tokens)."""
    daily_turns = SCENARIO["conversations_per_day"] * SCENARIO["avg_turns_per_conversation"]
    monthly_turns = daily_turns * SCENARIO["working_days_per_month"]

    # All queries go to Sonnet (no routing)
    input_tokens_per_turn = (
        SCENARIO["avg_input_tokens_per_turn"] +
        SCENARIO["avg_kb_retrieval_tokens"] +
        GUARDRAIL_OVERHEAD_TOKENS
    )
    output_tokens_per_turn = SCENARIO["avg_output_tokens_per_turn"]

    total_input_tokens = monthly_turns * input_tokens_per_turn
    total_output_tokens = monthly_turns * output_tokens_per_turn

    cost = (
        total_input_tokens * PRICING["claude-sonnet"]["input"] / 1000 +
        total_output_tokens * PRICING["claude-sonnet"]["output"] / 1000
    )

    return {
        "label": "Baseline (All Sonnet, No Optimization)",
        "monthly_turns": monthly_turns,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "monthly_cost": cost,
    }


def calculate_optimized_cost():
    """Cost WITH intelligent routing + prompt optimization."""
    daily_turns = SCENARIO["conversations_per_day"] * SCENARIO["avg_turns_per_conversation"]
    monthly_turns = daily_turns * SCENARIO["working_days_per_month"]

    # Split between models via routing
    haiku_turns = int(monthly_turns * SCENARIO["pct_simple_queries"])
    sonnet_turns = int(monthly_turns * SCENARIO["pct_complex_queries"])

    input_tokens_per_turn = (
        SCENARIO["avg_input_tokens_per_turn"] +
        SCENARIO["avg_kb_retrieval_tokens"] +
        GUARDRAIL_OVERHEAD_TOKENS
    )
    output_tokens_per_turn = SCENARIO["avg_output_tokens_per_turn"]

    # Haiku cost
    haiku_cost = (
        haiku_turns * input_tokens_per_turn * PRICING["claude-haiku"]["input"] / 1000 +
        haiku_turns * output_tokens_per_turn * PRICING["claude-haiku"]["output"] / 1000
    )

    # Sonnet cost
    sonnet_cost = (
        sonnet_turns * input_tokens_per_turn * PRICING["claude-sonnet"]["input"] / 1000 +
        sonnet_turns * output_tokens_per_turn * PRICING["claude-sonnet"]["output"] / 1000
    )

    total_cost = haiku_cost + sonnet_cost

    return {
        "label": "Optimized (Routing + Right-sized max_tokens)",
        "monthly_turns": monthly_turns,
        "haiku_turns": haiku_turns,
        "sonnet_turns": sonnet_turns,
        "haiku_cost": haiku_cost,
        "sonnet_cost": sonnet_cost,
        "monthly_cost": total_cost,
    }


def calculate_evaluation_cost():
    """Cost of running weekly evaluations (LLM-as-Judge)."""
    # Each eval = Sonnet judging one response
    tokens_per_eval = 800  # prompt + response + judgment
    total_evals = EVAL_RUNS_PER_MONTH * EVAL_SAMPLES_PER_RUN

    cost = (
        total_evals * tokens_per_eval * PRICING["claude-sonnet"]["input"] / 1000 +
        total_evals * 200 * PRICING["claude-sonnet"]["output"] / 1000  # judgment output
    )

    return {
        "label": "Quality Evaluation (LLM-as-Judge)",
        "total_evals": total_evals,
        "monthly_cost": cost,
    }


def main():
    console.print(Panel(
        "[bold green]Demo 07: Token Economics - The Full Cost Picture[/]\n"
        "Real numbers for running an IT Helpdesk agent at production scale.",
        style="green"
    ))

    # Scenario summary
    console.print("\n[bold cyan]Production Scenario:[/]")
    table_scenario = Table(show_header=False)
    table_scenario.add_column("Metric", style="green")
    table_scenario.add_column("Value", style="yellow")
    table_scenario.add_row("Conversations/day", f"{SCENARIO['conversations_per_day']:,}")
    table_scenario.add_row("Turns/conversation", f"{SCENARIO['avg_turns_per_conversation']}")
    table_scenario.add_row("Working days/month", f"{SCENARIO['working_days_per_month']}")
    table_scenario.add_row("Total turns/month", f"{SCENARIO['conversations_per_day'] * SCENARIO['avg_turns_per_conversation'] * SCENARIO['working_days_per_month']:,}")
    table_scenario.add_row("Simple queries (Haiku)", f"{SCENARIO['pct_simple_queries']*100:.0f}%")
    table_scenario.add_row("Complex queries (Sonnet)", f"{SCENARIO['pct_complex_queries']*100:.0f}%")
    console.print(table_scenario)

    # Detailed math breakdown
    daily_turns = SCENARIO["conversations_per_day"] * SCENARIO["avg_turns_per_conversation"]
    monthly_turns = daily_turns * SCENARIO["working_days_per_month"]
    input_tokens_per_turn = (SCENARIO["avg_input_tokens_per_turn"] +
                             SCENARIO["avg_kb_retrieval_tokens"] +
                             GUARDRAIL_OVERHEAD_TOKENS)
    output_tokens_per_turn = SCENARIO["avg_output_tokens_per_turn"]

    console.print("\n[bold cyan]How We Calculate (showing the math):[/]")
    console.print(f"  Daily turns     = {SCENARIO['conversations_per_day']:,} convos × {SCENARIO['avg_turns_per_conversation']} turns = {daily_turns:,}")
    console.print(f"  Monthly turns   = {daily_turns:,} × {SCENARIO['working_days_per_month']} days = {monthly_turns:,}")
    console.print(f"  Input/turn      = {SCENARIO['avg_input_tokens_per_turn']} (prompt) + {SCENARIO['avg_kb_retrieval_tokens']} (RAG context) + {GUARDRAIL_OVERHEAD_TOKENS} (guardrail) = {input_tokens_per_turn} tokens")
    console.print(f"  Output/turn     = {output_tokens_per_turn} tokens")
    console.print(f"")
    console.print(f"  [bold]Baseline (All Sonnet):[/]")
    console.print(f"    Input cost  = {monthly_turns:,} × {input_tokens_per_turn} tokens × ${PRICING['claude-sonnet']['input']}/1K = ${monthly_turns * input_tokens_per_turn * PRICING['claude-sonnet']['input'] / 1000:,.2f}")
    console.print(f"    Output cost = {monthly_turns:,} × {output_tokens_per_turn} tokens × ${PRICING['claude-sonnet']['output']}/1K = ${monthly_turns * output_tokens_per_turn * PRICING['claude-sonnet']['output'] / 1000:,.2f}")
    console.print(f"")

    haiku_turns = int(monthly_turns * SCENARIO["pct_simple_queries"])
    sonnet_turns = int(monthly_turns * SCENARIO["pct_complex_queries"])
    console.print(f"  [bold]Optimized (Routing splits traffic):[/]")
    console.print(f"    Haiku handles  = {monthly_turns:,} × 65% = {haiku_turns:,} turns")
    console.print(f"    Sonnet handles = {monthly_turns:,} × 35% = {sonnet_turns:,} turns")
    console.print(f"    Haiku input    = {haiku_turns:,} × {input_tokens_per_turn} × ${PRICING['claude-haiku']['input']}/1K = ${haiku_turns * input_tokens_per_turn * PRICING['claude-haiku']['input'] / 1000:,.2f}")
    console.print(f"    Haiku output   = {haiku_turns:,} × {output_tokens_per_turn} × ${PRICING['claude-haiku']['output']}/1K = ${haiku_turns * output_tokens_per_turn * PRICING['claude-haiku']['output'] / 1000:,.2f}")
    console.print(f"    Sonnet input   = {sonnet_turns:,} × {input_tokens_per_turn} × ${PRICING['claude-sonnet']['input']}/1K = ${sonnet_turns * input_tokens_per_turn * PRICING['claude-sonnet']['input'] / 1000:,.2f}")
    console.print(f"    Sonnet output  = {sonnet_turns:,} × {output_tokens_per_turn} × ${PRICING['claude-sonnet']['output']}/1K = ${sonnet_turns * output_tokens_per_turn * PRICING['claude-sonnet']['output'] / 1000:,.2f}")
    console.print(f"")
    console.print(f"  [bold]Model Pricing (per 1K tokens):[/]")
    console.print(f"    Sonnet: input=${PRICING['claude-sonnet']['input']}  output=${PRICING['claude-sonnet']['output']}")
    console.print(f"    Haiku:  input=${PRICING['claude-haiku']['input']}  output=${PRICING['claude-haiku']['output']}")

    # Calculate costs
    baseline = calculate_baseline_cost()
    optimized = calculate_optimized_cost()
    evaluation = calculate_evaluation_cost()

    # Main comparison
    console.print("\n")
    table = Table(title="Monthly Cost Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Strategy", style="green")
    table.add_column("Monthly Cost", justify="right", style="yellow")
    table.add_column("Annual Cost", justify="right")

    table.add_row(
        baseline["label"],
        f"${baseline['monthly_cost']:,.2f}",
        f"${baseline['monthly_cost'] * 12:,.2f}",
    )
    table.add_row(
        optimized["label"],
        f"${optimized['monthly_cost']:,.2f}",
        f"${optimized['monthly_cost'] * 12:,.2f}",
    )
    table.add_row(
        evaluation["label"],
        f"${evaluation['monthly_cost']:,.2f}",
        f"${evaluation['monthly_cost'] * 12:,.2f}",
    )

    total_optimized = optimized["monthly_cost"] + evaluation["monthly_cost"]
    savings = baseline["monthly_cost"] - total_optimized
    savings_pct = (savings / baseline["monthly_cost"]) * 100

    table.add_row("", "", "")
    table.add_row(
        "[bold]TOTAL (Optimized + Eval)[/]",
        f"[bold]${total_optimized:,.2f}[/]",
        f"[bold]${total_optimized * 12:,.2f}[/]",
    )
    table.add_row(
        "[bold green]MONTHLY SAVINGS[/]",
        f"[bold green]${savings:,.2f} ({savings_pct:.0f}%)[/]",
        f"[bold green]${savings * 12:,.2f}/year[/]",
    )

    console.print(table)

    # Breakdown
    console.print("\n[bold cyan]Optimized Cost Breakdown:[/]")
    table2 = Table(show_header=True, header_style="bold cyan")
    table2.add_column("Component", style="green")
    table2.add_column("Turns/month", justify="right")
    table2.add_column("Cost", justify="right", style="yellow")
    table2.add_column("% of Total", justify="right")

    table2.add_row(
        "Haiku (simple queries)",
        f"{optimized['haiku_turns']:,}",
        f"${optimized['haiku_cost']:,.2f}",
        f"{optimized['haiku_cost']/total_optimized*100:.0f}%",
    )
    table2.add_row(
        "Sonnet (complex queries)",
        f"{optimized['sonnet_turns']:,}",
        f"${optimized['sonnet_cost']:,.2f}",
        f"{optimized['sonnet_cost']/total_optimized*100:.0f}%",
    )
    table2.add_row(
        "Quality Evaluation",
        f"{evaluation['total_evals']:,}",
        f"${evaluation['monthly_cost']:,.2f}",
        f"{evaluation['monthly_cost']/total_optimized*100:.0f}%",
    )

    console.print(table2)

    # ============================================================
    # Real CloudWatch Metrics (if available)
    # ============================================================
    console.print("\n[bold cyan]Real Usage Metrics (from CloudWatch):[/]\n")
    metrics = fetch_real_metrics()
    if metrics["available"]:
        real_input = metrics["input_tokens_7d"]
        real_output = metrics["output_tokens_7d"]
        days = metrics["days"]
        daily_input = real_input / days
        daily_output = real_output / days
        daily_cost_sonnet = (daily_input * PRICING["claude-sonnet"]["input"] / 1000 +
                            daily_output * PRICING["claude-sonnet"]["output"] / 1000)

        console.print(f"  Last {days} days of actual Bedrock usage:")
        console.print(f"    Input tokens:  {real_input:,.0f} ({daily_input:,.0f}/day)")
        console.print(f"    Output tokens: {real_output:,.0f} ({daily_output:,.0f}/day)")
        console.print(f"    Estimated daily cost (Sonnet pricing): ${daily_cost_sonnet:.2f}")
        console.print(f"    Estimated monthly cost: ${daily_cost_sonnet * 22:.2f}")

        console.print(f"\n  [bold]Calculation breakdown:[/]")
        input_cost = daily_input * PRICING["claude-sonnet"]["input"] / 1000
        output_cost = daily_output * PRICING["claude-sonnet"]["output"] / 1000
        console.print(f"    Input cost/day  = {daily_input:,.0f} tokens × ${PRICING['claude-sonnet']['input']}/1K = ${input_cost:.4f}")
        console.print(f"    Output cost/day = {daily_output:,.0f} tokens × ${PRICING['claude-sonnet']['output']}/1K = ${output_cost:.4f}")
        console.print(f"    Daily total     = ${input_cost + output_cost:.4f}")
        console.print(f"    Monthly (×22 working days) = ${(input_cost + output_cost) * 22:.2f}")
        console.print(f"\n  [dim]Note: This is your ACTUAL demo usage. Production (1000 convos/day) would scale these numbers by ~300-500x.[/]")

    else:
        console.print("  [dim]No CloudWatch metrics available yet (enable invocation logging")
        console.print("  and run a few demo queries first to see real data here).[/]")
        console.print("  [dim]Showing calculated estimates based on scenario assumptions above.[/]")

    # Optimization tips
    console.print(Panel(
        "[bold green]5 OPTIMIZATION WINS (ranked by impact):[/]\n\n"
        "1. [bold]Intelligent Prompt Routing[/] - 30% savings, zero code change\n"
        "2. [bold]Set max_tokens explicitly[/] - prevents 99% of quota throttling\n"
        "3. [bold]Optimize system prompts[/] - shorter prompt = fewer input tokens per call\n"
        "4. [bold]Prompt Caching[/] - 90% savings on repeated context (RAG, system prompt)\n"
        "5. [bold]Cross-Region Inference[/] - free availability + 10% savings (global)\n\n"
        "[dim]Bonus: If 80% of queries are identical (password reset, VPN),"
        " cache responses at application layer.[/]",
        title="Production Cost Optimization Playbook",
        border_style="green",
    ))

    # Per conversation economics
    per_conv_baseline = baseline["monthly_cost"] / (SCENARIO["conversations_per_day"] * SCENARIO["working_days_per_month"])
    per_conv_optimized = total_optimized / (SCENARIO["conversations_per_day"] * SCENARIO["working_days_per_month"])

    console.print(f"\n[bold]Cost per conversation:[/]")
    console.print(f"  Baseline (all Sonnet):  ${per_conv_baseline:.4f}")
    console.print(f"  Optimized (routing):    ${per_conv_optimized:.4f}")
    console.print(f"  [green]Savings per conversation: ${per_conv_baseline - per_conv_optimized:.4f}[/]")


if __name__ == "__main__":
    main()
