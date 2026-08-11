"""
Demo 08: Observability - Invocation Logging + CloudWatch Monitoring
====================================================================
Shows how to set up production-grade monitoring for your Bedrock workloads:
1. Invocation logging (per-request token tracking)
2. CloudWatch metrics (InputTokenCount, OutputTokenCount, InvocationThrottles)
3. Token attribution per user/app (for chargeback and cost allocation)
4. Alarm setup for throttling detection

Production Lessons:
- Invocation logging gives you per-request token + cost visibility
- CloudWatch metrics help detect throttling BEFORE users complain
- Token attribution enables multi-tenant chargeback
- This is NON-NEGOTIABLE for enterprise production deployments
"""
import boto3
import json
import time
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import REGION, MODEL_SONNET, MODEL_HAIKU, PRICING

console = Console()
bedrock_client = boto3.client("bedrock", region_name=REGION)
cloudwatch_client = boto3.client("cloudwatch", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)


def fetch_live_metrics():
    """Fetch REAL CloudWatch metrics for Bedrock in the last 24 hours."""
    console.print(Panel(
        "[bold cyan]LIVE METRICS: Real-time Bedrock CloudWatch Data[/]",
        title="CloudWatch - Last 24 Hours",
        border_style="cyan",
    ))

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

    metrics_to_fetch = [
        ("Invocations", "Sum", "Total API calls"),
        ("InputTokenCount", "Sum", "Total input tokens consumed"),
        ("OutputTokenCount", "Sum", "Total output tokens generated"),
        ("InvocationLatency", "Average", "Average latency (ms)"),
        ("InvocationThrottles", "Sum", "Throttled requests (429s)"),
        ("InvocationClientErrors", "Sum", "Client errors (4xx)"),
        ("InvocationServerErrors", "Sum", "Server errors (5xx)"),
    ]

    table = Table(title="Live Bedrock Metrics (Last 24h)", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="green")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Description", style="dim")

    has_data = False
    for metric_name, stat, description in metrics_to_fetch:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=[stat],
            )
            if response["Datapoints"]:
                has_data = True
                value = response["Datapoints"][0][stat]
                if metric_name == "InvocationLatency":
                    display_val = f"{value:,.0f} ms"
                elif "Token" in metric_name:
                    display_val = f"{value:,.0f} tokens"
                else:
                    display_val = f"{value:,.0f}"

                # Highlight problems in red
                if metric_name in ("InvocationThrottles", "InvocationServerErrors") and value > 0:
                    display_val = f"[red]{display_val} ALERT![/]"

                table.add_row(metric_name, display_val, description)
            else:
                table.add_row(metric_name, "[dim]No data[/]", description)
        except Exception as e:
            table.add_row(metric_name, f"[red]Error[/]", str(e)[:50])

    console.print(table)

    if not has_data:
        console.print("\n  [yellow]No metrics data yet. Run some demo scripts first (01-06)")
        console.print("  to generate Bedrock invocations, then re-run this demo.[/]")
    else:
        console.print("\n  [green]Data is LIVE from your AWS account's CloudWatch![/]")

    return has_data


LOG_GROUP_NAME = "/aws/bedrock/model-invocations"

def show_logging_setup():
    """Check and enable invocation logging."""
    console.print(Panel(
        "[bold cyan]STEP 1: Enable Invocation Logging[/]\n\n"
        "One-time setup via console or API. Logs every Bedrock call with:\n"
        "- Request/response content (optional)\n"
        "- Token counts (input + output)\n"
        "- Model ID used\n"
        "- Caller identity (IAM role/user ARN)\n"
        "- Latency and status",
        title="Invocation Logging Setup",
        border_style="cyan",
    ))

    # Check current logging status
    try:
        current_config = bedrock_client.get_model_invocation_logging_configuration()
        logging_config = current_config.get("loggingConfig", {})
        cw_config = logging_config.get("cloudWatchConfig", {})

        if cw_config.get("logGroupName"):
            console.print(f"  [green]Invocation logging is ALREADY ENABLED[/]")
            console.print(f"    Log group: {cw_config['logGroupName']}")
            console.print(f"    Text delivery: {logging_config.get('textDataDeliveryEnabled', 'N/A')}")
            console.print(f"    Image delivery: {logging_config.get('imageDataDeliveryEnabled', 'N/A')}")
        else:
            console.print("  [yellow]Invocation logging NOT enabled. Enabling now...[/]")
            _enable_invocation_logging()
    except Exception as e:
        console.print(f"  [yellow]Could not check logging status: {e}[/]")
        console.print("  [yellow]Attempting to enable invocation logging...[/]")
        _enable_invocation_logging()


def _enable_invocation_logging():
    """Actually enable invocation logging via API."""
    try:
        # Create log group if it doesn't exist
        try:
            logs_client.create_log_group(logGroupName=LOG_GROUP_NAME)
            console.print(f"    Created log group: {LOG_GROUP_NAME}")
        except logs_client.exceptions.ResourceAlreadyExistsException:
            console.print(f"    Log group already exists: {LOG_GROUP_NAME}")

        bedrock_client.put_model_invocation_logging_configuration(
            loggingConfig={
                "cloudWatchConfig": {
                    "logGroupName": LOG_GROUP_NAME,
                },
                "textDataDeliveryEnabled": True,
                "imageDataDeliveryEnabled": False,
            }
        )
        console.print("  [green]Invocation logging ENABLED successfully![/]")
    except Exception as e:
        console.print(f"  [red]Could not enable logging: {e}[/]")
        console.print("  [dim]You may need to enable it manually in the Bedrock console.[/]")
        console.print("  [dim]Settings > Model invocation logging > Enable[/]")


def show_log_format():
    """Show what an invocation log entry looks like."""
    console.print(Panel(
        "[bold cyan]STEP 2: Understanding Invocation Log Format[/]",
        title="Log Structure",
        border_style="cyan",
    ))

    # Sample log entry
    sample_log = {
        "schemaType": "ModelInvocationLog",
        "schemaVersion": "1.0",
        "timestamp": "2026-08-10T10:30:00Z",
        "accountId": "111122223333",
        "identity": {
            "arn": "arn:aws:sts::111122223333:assumed-role/HelpDeskApp/session-user-123"
        },
        "region": "us-east-1",
        "requestId": "abc-123-def-456",
        "operation": "Converse",
        "modelId": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "input": {
            "inputContentType": "application/json",
            "inputTokenCount": 245,
        },
        "output": {
            "outputContentType": "application/json",
            "outputTokenCount": 156,
            "stopReason": "end_turn",
        },
    }

    console.print(json.dumps(sample_log, indent=2))
    console.print("\n[green]Key fields for cost attribution:[/]")
    console.print("  - identity.arn: WHO made the call (enables chargeback)")
    console.print("  - modelId: WHICH model was used")
    console.print("  - inputTokenCount + outputTokenCount: HOW MUCH it cost")


def show_cloudwatch_queries():
    """Show CloudWatch Logs Insights queries for token attribution."""
    console.print(Panel(
        "[bold cyan]STEP 3: Token Attribution Queries (CloudWatch Logs Insights)[/]\n"
        "Run these in CloudWatch Logs Insights against your invocation log group.",
        title="Cost Attribution",
        border_style="cyan",
    ))

    queries = [
        {
            "name": "Token usage by application/role",
            "query": """fields @timestamp, identity.arn, input.inputTokenCount, output.outputTokenCount
| stats sum(input.inputTokenCount) as totalInputTokens,
        sum(output.outputTokenCount) as totalOutputTokens,
        count(*) as invocationCount
  by identity.arn
| sort totalInputTokens desc""",
        },
        {
            "name": "Token usage by model (cost breakdown)",
            "query": """fields @timestamp, modelId, input.inputTokenCount, output.outputTokenCount
| stats sum(input.inputTokenCount) as inputTokens,
        sum(output.outputTokenCount) as outputTokens,
        count(*) as calls
  by modelId
| sort inputTokens desc""",
        },
        {
            "name": "Hourly cost trend (detect spikes)",
            "query": """fields @timestamp, input.inputTokenCount, output.outputTokenCount
| stats sum(input.inputTokenCount) as inputTokens,
        sum(output.outputTokenCount) as outputTokens
  by bin(1h) as hour
| sort hour desc""",
        },
    ]

    for q in queries:
        console.print(f"\n[bold yellow]{q['name']}:[/]")
        console.print(f"[dim]{q['query']}[/]")


def show_cloudwatch_metrics():
    """Show the key CloudWatch metrics to monitor."""
    console.print(Panel(
        "[bold cyan]STEP 4: CloudWatch Metrics for Bedrock[/]\n"
        "These metrics are emitted automatically - no setup needed.",
        title="Runtime Metrics",
        border_style="cyan",
    ))

    table = Table(title="Key Bedrock CloudWatch Metrics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="green")
    table.add_column("What It Tells You", style="white")
    table.add_column("Alert When", style="yellow")

    table.add_row("Invocations", "Total API calls made", "Sudden spike (runaway loop)")
    table.add_row("InvocationLatency", "Response time per call (ms)", "> 10s (user experience)")
    table.add_row("InvocationThrottles", "Requests rejected (429)", "> 0 (quota exhaustion)")
    table.add_row("InputTokenCount", "Tokens consumed (input)", "Exceeds budget projection")
    table.add_row("OutputTokenCount", "Tokens generated (output)", "Exceeds budget projection")
    table.add_row("InvocationClientErrors", "4xx errors", "> 5% of invocations")
    table.add_row("InvocationServerErrors", "5xx errors", "Any occurrence")

    console.print(table)


def show_alarm_setup():
    """Show how to set up CloudWatch Alarms for throttling."""
    console.print(Panel(
        "[bold cyan]STEP 5: Critical Alarms[/]\n"
        "Set these up BEFORE going to production.",
        title="Alarm Configuration",
        border_style="cyan",
    ))

    alarm_code = """
# Create alarm for throttling detection
import boto3
cloudwatch = boto3.client('cloudwatch')

# Alarm: Throttling detected (any 429 errors)
cloudwatch.put_metric_alarm(
    AlarmName='Bedrock-Throttling-Detected',
    MetricName='InvocationThrottles',
    Namespace='AWS/Bedrock',
    Statistic='Sum',
    Period=60,              # Check every 1 minute
    EvaluationPeriods=1,   # Alert after 1 period
    Threshold=1,           # ANY throttle is a problem
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    Dimensions=[
        {'Name': 'ModelId', 'Value': 'us.anthropic.claude-sonnet-4-20250514-v1:0'}
    ],
    AlarmActions=['arn:aws:sns:us-east-1:ACCOUNT:bedrock-alerts'],
    TreatMissingData='notBreaching',
)

# Alarm: Token budget exceeded (daily)
cloudwatch.put_metric_alarm(
    AlarmName='Bedrock-DailyTokenBudget-Exceeded',
    MetricName='InputTokenCount',
    Namespace='AWS/Bedrock',
    Statistic='Sum',
    Period=86400,           # Daily
    EvaluationPeriods=1,
    Threshold=5000000,     # 5M tokens/day budget
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:ACCOUNT:bedrock-alerts'],
)
"""
    console.print(f"[dim]{alarm_code}[/]")


def show_dashboard_structure():
    """Show REAL metrics in a dashboard-style layout using live CloudWatch data."""
    console.print(Panel(
        "[bold cyan]STEP 6: Production Dashboard (Live Data)[/]",
        title="Live Observability Dashboard",
        border_style="cyan",
    ))

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

    # Fetch multiple metrics for dashboard display
    dashboard_metrics = {}
    metric_requests = [
        ("Invocations", "Sum"),
        ("InputTokenCount", "Sum"),
        ("OutputTokenCount", "Sum"),
        ("InvocationLatency", "Average"),
        ("InvocationThrottles", "Sum"),
    ]

    for metric_name, stat in metric_requests:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # Hourly granularity
                Statistics=[stat],
            )
            datapoints = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
            dashboard_metrics[metric_name] = datapoints
        except Exception:
            dashboard_metrics[metric_name] = []

    # Build live dashboard table
    table = Table(title="BEDROCK OBSERVABILITY DASHBOARD (Last 24h - LIVE)", show_header=True, header_style="bold cyan")
    table.add_column("Panel", style="green")
    table.add_column("Current Value", justify="right", style="yellow")
    table.add_column("Status", justify="center")

    # Invocations
    inv_total = sum(dp["Sum"] for dp in dashboard_metrics.get("Invocations", []))
    table.add_row("Total Invocations", f"{inv_total:,.0f}", "[green]OK[/]" if inv_total > 0 else "[dim]No data[/]")

    # Input tokens
    input_total = sum(dp["Sum"] for dp in dashboard_metrics.get("InputTokenCount", []))
    table.add_row("Input Tokens", f"{input_total:,.0f}", "[green]OK[/]" if input_total > 0 else "[dim]No data[/]")

    # Output tokens
    output_total = sum(dp["Sum"] for dp in dashboard_metrics.get("OutputTokenCount", []))
    table.add_row("Output Tokens", f"{output_total:,.0f}", "[green]OK[/]" if output_total > 0 else "[dim]No data[/]")

    # Latency
    latency_points = dashboard_metrics.get("InvocationLatency", [])
    if latency_points:
        avg_latency = sum(dp["Average"] for dp in latency_points) / len(latency_points)
        latency_status = "[green]OK[/]" if avg_latency < 5000 else "[yellow]SLOW[/]"
        table.add_row("Avg Latency", f"{avg_latency:,.0f} ms", latency_status)
    else:
        table.add_row("Avg Latency", "[dim]No data[/]", "[dim]--[/]")

    # Throttles
    throttle_total = sum(dp["Sum"] for dp in dashboard_metrics.get("InvocationThrottles", []))
    throttle_status = "[red]ALERT![/]" if throttle_total > 0 else "[green]CLEAR[/]"
    table.add_row("Throttles (429s)", f"{throttle_total:,.0f}", throttle_status)

    # Estimated cost
    if input_total > 0 or output_total > 0:
        est_cost = (input_total * PRICING["claude-sonnet"]["input"] / 1000 +
                    output_total * PRICING["claude-sonnet"]["output"] / 1000)
        table.add_row("Est. Cost (24h, Sonnet pricing)", f"${est_cost:.4f}", "[bold]$$$[/]")

    console.print(table)

    if inv_total == 0:
        console.print("\n  [yellow]No invocation data in the last 24h.")
        console.print("  Run demos 01-06 first, then re-run this to see live dashboard data.[/]")
    else:
        console.print("\n  [green]All data above is LIVE from CloudWatch - not hardcoded![/]")

    console.print("\n[bold]Deploy a full dashboard:[/]")
    console.print("  Use CloudFormation or Terraform to create a CloudWatch Dashboard")
    console.print("  with these metrics. See AWS docs: Monitoring Amazon Bedrock.")


def main():
    console.print(Panel(
        "[bold green]Demo 08: Observability - See Everything, Control Everything[/]\n"
        "Production monitoring for Bedrock: logging, metrics, alarms, dashboards.",
        style="green"
    ))

    # First: Show LIVE metrics (real-time from CloudWatch)
    has_data = fetch_live_metrics()
    console.print("")

    # Then: Show setup patterns
    show_logging_setup()
    show_log_format()
    show_cloudwatch_queries()
    show_cloudwatch_metrics()
    show_alarm_setup()
    show_dashboard_structure()

    # Production lessons
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. Enable invocation logging DAY ONE - you need it for cost attribution\n"
        "2. identity.arn in logs enables per-app/per-user chargeback\n"
        "3. Set throttling alarms BEFORE launch (not after users complain)\n"
        "4. Monitor InputTokenCount daily to catch prompt bloat early\n"
        "5. Track OutputTokens/InputTokens ratio - high ratio = verbose model\n"
        "6. Dashboard = single pane of glass for ops team\n"
        "7. Log analysis reveals: which users burn most tokens, which queries\n"
        "   are expensive, and where optimization has the most ROI",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
