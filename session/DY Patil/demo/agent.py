"""
Resume Roast Agent - AI Agents 101 Demo
Built with Strands Agents SDK

This agent:
1. Reads a resume (PDF or text)
2. Searches the web for LIVE job postings (using duckduckgo-search library)
3. Compares skills vs what companies actually want TODAY
4. Gives a resume readiness score (custom @tool)
5. Delivers a specific, actionable, slightly brutal roast

Run: python agent.py

Auth: Uses your AWS CLI credentials automatically.  
Before running: aws login
Strands uses boto3 which picks up your session from ~/.aws/

Dependencies: pip install duckduckgo-search (in addition to strands packages)
"""

from strands import Agent, tool
from strands_tools import file_read


# === CUSTOM TOOL: Job Search (uses duckduckgo-search library) ===
# This actually works - no bot blocking, returns real URLs

@tool
def search_jobs(query: str) -> str:
    """Search the internet for job postings. Returns titles, URLs and snippets.
    Use queries like "backend developer intern Pune 2025 naukri" or 
    "fresher software engineer Python Pune hiring linkedin".

    Args:
        query: Search query for finding job postings
    """
    try:
        from ddgs import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=10):
                results.append(f"- **{r['title']}**\n  Link: {r['href']}\n  {r['body'][:150]}\n")
        
        if not results:
            return "No results found. Try a different query."
        
        return f"Search results for: {query}\n\n" + "\n".join(results)
    
    except ImportError:
        return "ERROR: ddgs not installed. Run: pip install ddgs"
    except Exception as e:
        return f"Search error: {str(e)}"


# === CUSTOM TOOL: Resume Score Calculator ===
# Demonstrates the @tool decorator - agent decides when to call this

@tool
def resume_score(strengths: int, gaps: int, role: str) -> str:
    """Calculate a resume readiness score based on strengths vs gaps found.

    Args:
        strengths: Number of strong points/matching skills found in the resume
        gaps: Number of missing skills or gaps found compared to job postings
        role: The target role being evaluated for
    """
    if strengths + gaps == 0:
        return "Score: N/A - could not evaluate"
    
    score = max(0, min(100, int((strengths / (strengths + gaps)) * 100)))
    
    if score >= 80:
        verdict = "You are ready! Start applying NOW."
    elif score >= 60:
        verdict = "Almost there. One weekend of work and you are golden."
    elif score >= 40:
        verdict = "Needs work. Give it 1-2 weeks of focused effort."
    else:
        verdict = "Major gaps. But hey, at least you know what to fix now!"
    
    return f"""
========================================
RESUME READINESS SCORE for {role}
========================================
Score: {score}/100
Strengths found: {strengths}
Gaps found: {gaps}
Verdict: {verdict}
========================================
"""


# Create the Resume Roast Agent
agent = Agent(
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt="""You are a brutally honest but helpful resume reviewer for tech jobs in India.

Your personality: Think of yourself as that senior friend who actually cares about your career 
but has zero filter. You are funny, specific, and actionable. No generic advice allowed.

Your process:
1. Read the user's resume file using file_read
2. Extract their skills, projects, experience, and education
3. Search for jobs using the search_jobs tool (call it 2 times with different queries):
   - Query 1: "backend developer intern Pune 2025 naukri"
   - Query 2: "fresher software engineer Python Node.js Pune linkedin hiring"
4. From the search results, extract company names, roles, required skills, and URLs
5. Compare what the candidate HAS vs what companies ACTUALLY want
6. Call resume_score with your counts and INCLUDE its full output in your response
7. Deliver your roast

OUTPUT FORMAT (follow this exactly):

## The Good (what is working)
- List specific strengths (count these for score)

## The Roast (what is missing or weak)
- Be specific and reference job postings you found

## Job Listings Found
| # | Company | Role | Key Skills They Want | Link |
|---|---------|------|---------------------|------|
- Fill with REAL results from search_jobs - use actual URLs returned
- 5-10 rows minimum

## Resume Score
(paste the full output from resume_score tool here)

## Your Action Plan (this week)
- 3-5 specific tasks for THIS WEEK

IMPORTANT RULES:
- You MUST use search_jobs tool to find real job postings - do not make up listings
- You MUST include actual URLs from search results in the table
- You MUST call resume_score and show its output
- Max 2 search_jobs calls to keep things fast
- Never give generic advice
- Be funny but helpful""",
    tools=[file_read, search_jobs, resume_score]
)


# Run the agent
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RESUME ROAST AGENT - Let's see what you're working with")
    print("=" * 60 + "\n")
    
    result = agent(
        "Review the resume at ./sample_resume.pdf and roast me. "
        "Tell me what's missing for fresher/intern level backend developer roles in Pune. "
        "Use search_jobs to find real postings, include their URLs in a table, "
        "and give me my resume_score at the end."
    )
    
    print("\n" + "=" * 60)
    print("  ROAST COMPLETE")
    print("=" * 60)
