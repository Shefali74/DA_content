"""
Demo 03: Knowledge Base - RAG for Grounded Responses
=====================================================
Shows how Knowledge Bases eliminate hallucinations by grounding responses
in your actual data. Includes citation tracking for enterprise trust.

Production Lessons:
- RAG = no hallucinations about company policy
- Citations = audit trail for compliance
- Without KB, the model WILL make things up about your company
"""
import boto3
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from config import REGION, MODEL_SONNET, KNOWLEDGE_BASE_ID

console = Console()
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)


def query_knowledge_base(query: str, num_results: int = 3) -> dict:
    """Query the knowledge base and retrieve relevant documents."""
    response = bedrock_agent.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
    )
    return response


def generate_with_rag(query: str, context_chunks: list) -> dict:
    """Generate a response using retrieved context (RAG pattern)."""
    # Build context from retrieved chunks
    context = "\n\n---\n\n".join([
        f"Source: {chunk['location'].get('s3Location', {}).get('uri', 'unknown')}\n"
        f"Content: {chunk['content']['text']}"
        for chunk in context_chunks
    ])

    system_prompt = """You are an IT Service Desk assistant. Answer questions using ONLY 
the provided context. If the answer is not in the context, say "I don't have information 
about that in our knowledge base." Always cite which source document your answer comes from."""

    messages = [
        {
            "role": "user",
            "content": [{"text": f"Context:\n{context}\n\nQuestion: {query}"}],
        }
    ]

    response = bedrock_runtime.converse(
        modelId=MODEL_SONNET,
        system=[{"text": system_prompt}],
        messages=messages,
        inferenceConfig={"maxTokens": 500, "temperature": 0.2},
    )

    return {
        "response": response["output"]["message"]["content"][0]["text"],
        "usage": response["usage"],
    }


def generate_without_rag(query: str) -> dict:
    """Generate a response WITHOUT knowledge base (shows hallucination risk)."""
    system_prompt = """You are an IT Service Desk assistant for Acme Corp. 
Answer the employee's question about company policies."""

    messages = [{"role": "user", "content": [{"text": query}]}]

    response = bedrock_runtime.converse(
        modelId=MODEL_SONNET,
        system=[{"text": system_prompt}],
        messages=messages,
        inferenceConfig={"maxTokens": 500, "temperature": 0.3},
    )

    return {
        "response": response["output"]["message"]["content"][0]["text"],
        "usage": response["usage"],
    }


def main():
    console.print(Panel(
        "[bold green]Demo 03: Knowledge Base - Ground Truth, Not Hallucination[/]\n"
        "RAG retrieves your actual docs before generating. No more made-up policies.",
        style="green"
    ))

    queries = [
        "What is the laptop replacement policy? How do I request a new one?",
        "How many days of work from home are allowed per week?",
        "What's the process to get access to the production environment?",
    ]

    for i, query in enumerate(queries, 1):
        console.print(f"\n[bold cyan]Query {i}:[/] {query}\n")

        # Step 1: Retrieve from Knowledge Base
        console.print("[yellow]  Retrieving from Knowledge Base...[/]")
        retrieval = query_knowledge_base(query)
        chunks = retrieval["retrievalResults"]

        # Show retrieved sources
        console.print(f"  [green]Found {len(chunks)} relevant chunks[/]")
        for j, chunk in enumerate(chunks, 1):
            score = chunk.get("score", 0)
            uri = chunk.get("location", {}).get("s3Location", {}).get("uri", "unknown")
            filename = uri.split("/")[-1] if "/" in uri else uri
            console.print(f"    [{j}] {filename} (relevance: {score:.2f})")

        # Step 2: Generate with RAG
        console.print("[yellow]  Generating grounded response...[/]")
        rag_result = generate_with_rag(query, chunks)

        console.print(Panel(
            rag_result["response"],
            title=f"[green]WITH Knowledge Base (Grounded)[/]",
            border_style="green",
        ))

        # Step 3: Show what happens WITHOUT KB (only for first query)
        if i <= 2:
            console.print("[yellow]  Now generating WITHOUT Knowledge Base...[/]")
            no_rag_result = generate_without_rag(query)

            console.print(Panel(
                no_rag_result["response"],
                title=f"[red]WITHOUT Knowledge Base (Potential Hallucination)[/]",
                border_style="red",
            ))

            console.print(Panel(
                "[bold red]NOTICE:[/] Without KB, the model invented a policy!\n"
                "It sounds plausible but is NOT your company's actual policy.\n"
                "This is why RAG is non-negotiable for enterprise deployments.",
                border_style="yellow",
            ))

    # Production lessons
    console.print(Panel(
        "[bold green]PRODUCTION LESSONS:[/]\n\n"
        "1. ALWAYS use Knowledge Base for company-specific information\n"
        "2. Citations provide audit trail - essential for compliance\n"
        "3. Without RAG, models hallucinate plausible-sounding policies\n"
        "4. Managed KB handles chunking, embedding, indexing automatically\n"
        "5. Keep KB docs updated - stale docs = wrong answers",
        title="Key Takeaways",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
