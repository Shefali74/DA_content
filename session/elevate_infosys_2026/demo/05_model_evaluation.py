"""
Demo 05: Model Evaluation - Trust But Verify
=============================================
Shows how to evaluate model responses using:
1. Automatic evaluation (programmatic metrics)
2. LLM-as-a-Judge (Claude Sonnet judges Haiku's responses)

Production Lessons:
- Never deploy a prompt change without evaluating first
- LLM-as-Judge is cheap and catches quality regressions
- Evaluate on YOUR data, not generic benchmarks
"""
import os
import sys
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import REGION, MODEL_SONNET, MODEL_HAIKU


# =========================================================
# MOCK / AWS MODE
# =========================================================

USE_MOCK = os.getenv(
    "USE_MOCK_BEDROCK",
    "true"
).lower() == "true"


# 05_model_evaluation.py is inside demo/
# Go one level up to elevate_infosys_2026/

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)


if USE_MOCK:

    from mock_bedrock import MockBedrockClient

    client = MockBedrockClient()

else:

    import boto3

    client = boto3.client(
        "bedrock-runtime",
        region_name=REGION
    )


console = Console()


# Test dataset - questions with known ground truth answers
EVAL_DATASET = [
    {
        "query": "How do I reset my VPN password?",
        "ground_truth": "To reset your VPN password: 1) Go to the IT portal at portal.company.com/vpn 2) Click 'Reset Password' 3) Enter your employee ID 4) Follow the email verification steps. New password takes 15 minutes to propagate.",
        "category": "IT Support",
    },
    {
        "query": "What is the work from home policy?",
        "ground_truth": "Employees can work from home up to 3 days per week. WFH days must be pre-approved by your manager through the HR portal. Core hours (10am-4pm) must be maintained regardless of location.",
        "category": "HR Policy",
    },
    {
        "query": "How do I request access to production environment?",
        "ground_truth": "Production access requires: 1) Complete the Security Awareness training 2) Get manager approval 3) Submit a JIRA ticket to the Platform team 4) Complete the access review with the Security team. Typical turnaround is 3-5 business days.",
        "category": "Security",
    },
]

SYSTEM_PROMPT = """You are an IT Service Desk assistant. Provide concise, accurate 
answers based on company policies. Keep responses under 100 words."""


def get_model_response(model_id: str, query: str) -> str:
    """Get a response from the specified model."""
    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": query}]}],
        inferenceConfig={"maxTokens": 200, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"]


def llm_as_judge(query: str, ground_truth: str, model_response: str) -> dict:
    """Use Claude Sonnet to judge a model's response quality."""
    judge_prompt = f"""You are an evaluation judge. Score the following model response 
on a scale of 1-5 for each criterion.

QUESTION: {query}

GROUND TRUTH ANSWER: {ground_truth}

MODEL RESPONSE TO EVALUATE: {model_response}

Score each criterion (1=Poor, 5=Excellent):
1. RELEVANCE: Does the response answer the question asked?
2. ACCURACY: Is the information factually correct compared to ground truth?
3. COMPLETENESS: Does it cover all key points from the ground truth?
4. CONCISENESS: Is it appropriately brief without unnecessary information?

Respond in this exact JSON format:
{{
    "relevance": <score>,
    "accuracy": <score>,
    "completeness": <score>,
    "conciseness": <score>,
    "overall": <average_score>,
    "reasoning": "<one sentence explaining the scores>"
}}"""

    response = client.converse(
        modelId=MODEL_SONNET,  # Sonnet judges Haiku
        messages=[{"role": "user", "content": [{"text": judge_prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0.0},
    )

    response_text = response["output"]["message"]["content"][0]["text"]

    # Parse JSON from response
    try:
        # Extract JSON from response (handle markdown code blocks)
        if "```" in response_text:
            json_str = response_text.split("```")[1].replace("json", "").strip()
        else:
            json_str = response_text.strip()
        scores = json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        scores = {
            "relevance": 0, "accuracy": 0, "completeness": 0,
            "conciseness": 0, "overall": 0, "reasoning": "Failed to parse"
        }

    # Ensure overall is calculated even if model didn't provide it
    if not scores.get("overall") or scores.get("overall") == 0:
        numeric_scores = [scores.get(k, 0) for k in ["relevance", "accuracy", "completeness", "conciseness"] if isinstance(scores.get(k), (int, float))]
        if numeric_scores:
            scores["overall"] = sum(numeric_scores) / len(numeric_scores)

    return scores


def main():
    console.print(Panel(
        "[bold green]Demo 05: Model Evaluation - LLM-as-a-Judge[/]\n"
        "Evaluate response quality systematically before deploying to production.",
        style="green"
    ))

    # ============================================================
    # Step 1: Get responses from the model being evaluated (Haiku)
    # ============================================================
    console.print("\n[bold cyan]Step 1: Generate responses from Claude Haiku[/]")
    console.print("(In production, this is the cheaper model handling L1 queries)\n")

    responses = []
    for item in EVAL_DATASET:
        console.print(f"  Querying: \"{item['query']}\"")
        response = get_model_response(MODEL_HAIKU, item["query"])
        responses.append(response)
        console.print(Panel(
            response[:250] + ("..." if len(response) > 250 else ""),
            title=f"[yellow]Haiku's Response[/]",
            border_style="dim",
        ))

    # ============================================================
    # Step 2: LLM-as-a-Judge (Sonnet evaluates Haiku)
    # ============================================================
    console.print("[bold cyan]Step 2: Claude Sonnet judges Haiku's responses[/]\n")

    all_scores = []
    for i, (item, response) in enumerate(zip(EVAL_DATASET, responses)):
        console.print(f"  Evaluating Q{i+1}: \"{item['query'][:50]}...\"")
        scores = llm_as_judge(item["query"], item["ground_truth"], response)
        scores["category"] = item["category"]
        all_scores.append(scores)
        console.print(f"    Overall: {scores.get('overall', 'N/A')}/5 - {scores.get('reasoning', 'N/A')}")

    # ============================================================
    # Step 3: Results Dashboard
    # ============================================================
    console.print("\n")
    table = Table(title="Evaluation Results: Claude Haiku on IT Helpdesk", show_header=True, header_style="bold cyan")
    table.add_column("Category", style="green")
    table.add_column("Relevance", justify="center")
    table.add_column("Accuracy", justify="center")
    table.add_column("Completeness", justify="center")
    table.add_column("Conciseness", justify="center")
    table.add_column("Overall", justify="center", style="bold yellow")

    for scores in all_scores:
        table.add_row(
            scores.get("category", "N/A"),
            f"{scores.get('relevance', 'N/A')}/5",
            f"{scores.get('accuracy', 'N/A')}/5",
            f"{scores.get('completeness', 'N/A')}/5",
            f"{scores.get('conciseness', 'N/A')}/5",
            f"{scores.get('overall', 'N/A')}/5",
        )

    # Average row
    avg_overall = sum(s.get("overall", 0) for s in all_scores) / len(all_scores)
    table.add_row("---", "---", "---", "---", "---", "---")
    table.add_row("[bold]AVERAGE[/]", "", "", "", "", f"[bold]{avg_overall:.1f}/5[/]")

    console.print(table)

    # Decision
    threshold = 3.5
    if avg_overall >= threshold:
        console.print(f"\n  [green]PASS: Average score {avg_overall:.1f} >= threshold {threshold}[/]")
        console.print("  [green]Haiku is suitable for L1 helpdesk queries.[/]")
    else:
        console.print(f"\n  [red]FAIL: Average score {avg_overall:.1f} < threshold {threshold}[/]")
        console.print("  [red]Consider using Sonnet or fine-tuning for this use case.[/]")

    # Production lessons
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. LLM-as-Judge: Use a stronger model to evaluate a cheaper model\n"
        "2. Define scoring criteria specific to YOUR use case\n"
        "3. Set quality thresholds - automate go/no-go decisions\n"
        "4. Evaluate on YOUR data (not generic benchmarks)\n"
        "5. Run evaluations in CI/CD before deploying prompt changes\n"
        "6. Cost: Judging 100 responses ~ $0.50 (cheap insurance!)",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
