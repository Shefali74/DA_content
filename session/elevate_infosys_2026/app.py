"""
Bedrock Production Patterns - Streamlit Demo Launcher
=====================================================
A unified UI for running all demo scripts with terminal-style output.
Run with: streamlit run app.py
"""
import streamlit as st
import subprocess
import sys
import os

# Page config
st.set_page_config(
    page_title="Bedrock Production Patterns",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for terminal look
st.markdown("""
<style>
    .stApp { background-color: #0F1B2D; }
    .main .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #4EC400 !important; font-family: 'Fira Code', monospace !important; font-weight: bold !important; }
    p, span, li, div { color: #E8E8E8 !important; }
    .stMarkdown p { color: #E8E8E8 !important; font-size: 16px; }
    .stSidebar { background-color: #1A2332; }
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar p { color: #4EC400 !important; }
    .stSidebar .stRadio label { color: #FFFFFF !important; font-size: 15px !important; }
    .stSidebar .stRadio label span { color: #FFFFFF !important; }
    .stSidebar [data-testid="stMarkdownContainer"] p { color: #B0B0B0 !important; }
    /* Radio button dots */
    .stRadio [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
    /* Expander */
    .streamlit-expanderHeader { color: #FF9900 !important; }
    /* Button */
    .stButton button { background-color: #FF9900 !important; color: #000000 !important; font-weight: bold !important; border: none !important; }
    .stButton button:hover { background-color: #EC7211 !important; }
    /* Footer text */
    .stMarkdown a { color: #FF9900 !important; }
    /* Code blocks */
    code { color: #4EC400 !important; background-color: #1A2332 !important; }
    .demo-header { 
        color: #FF9900; 
        font-family: 'Fira Code', monospace; 
        font-size: 14px; 
        padding: 10px;
        border: 1px solid #FF9900;
        border-radius: 5px;
        background-color: #1A2332;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("BEDROCK")
    st.markdown("**Production Patterns**")
    st.markdown("---")

    demo_choice = st.radio(
        "SELECT DEMO",
        [
            "01 - Converse API + CRIS",
            "02 - Token Counter (Cost)",
            "03 - Knowledge Base (RAG)",
            "04 - Guardrails (Safety)",
            "05 - Model Evaluation",
            "06 - Prompt Routing",
            "07 - Cost Calculator",
            "08 - Observability",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("**MODELS**")
    st.code("Sonnet: us.anthropic.claude-sonnet-4\nHaiku:  us.anthropic.claude-3-5-haiku", language="text")

    st.markdown("---")
    st.markdown("**CONFIG**")
    region = st.text_input("AWS Region", value="us-east-1")
    st.markdown(f"```\nRegion: {region}\n```")

# Main content
st.title("Amazon Bedrock - Production Patterns")
st.markdown("*Building GenAI Applications at Production Scale*")

# Demo descriptions
DEMO_INFO = {
    "01 - Converse API + CRIS": {
        "title": "Unified Converse API + Cross-Region Inference",
        "description": "Write code ONCE, switch models instantly. Same API for Sonnet, Haiku, and cross-region inference profiles.",
        "lesson": "Use Converse API (not InvokeModel) for model portability. Always set maxTokens explicitly.",
        "script": "demo/01_converse_api.py",
    },
    "02 - Token Counter (Cost)": {
        "title": "CountTokens API - Know Before You Spend",
        "description": "Estimate token usage BEFORE inference. The max_tokens default trap that burns your budget silently.",
        "lesson": "max_tokens defaults to 64K for Sonnet. That's 64K of TPM quota RESERVED per request. Set it to 500.",
        "script": "demo/02_count_tokens.py",
    },
    "03 - Knowledge Base (RAG)": {
        "title": "Knowledge Base - Grounded Responses",
        "description": "RAG eliminates hallucinations by grounding responses in your actual data. Citations for compliance.",
        "lesson": "Without KB, the model invents plausible company policies. With KB, it quotes your real docs.",
        "script": "demo/03_knowledge_base_rag.py",
    },
    "04 - Guardrails (Safety)": {
        "title": "Guardrails - Safety at Scale",
        "description": "Block PII, deny topics, catch prompt injection. All without changing model code.",
        "lesson": "ApplyGuardrail API pre-screens input WITHOUT burning model tokens. Guardrails are model-agnostic.",
        "script": "demo/04_guardrails.py",
    },
    "05 - Model Evaluation": {
        "title": "Model Evaluation - LLM-as-a-Judge",
        "description": "Use Sonnet to evaluate Haiku's quality. Automated quality gates before deploying changes.",
        "lesson": "Never deploy a prompt change without evaluating. Cost: judging 100 responses ~ $0.50.",
        "script": "demo/05_model_evaluation.py",
    },
    "06 - Prompt Routing": {
        "title": "Intelligent Prompt Routing",
        "description": "Auto-route simple queries to Haiku, complex to Sonnet. Zero code changes, 30% savings.",
        "lesson": "65% of helpdesk queries are simple. Routing them to Haiku = massive cost reduction.",
        "script": "demo/06_prompt_routing.py",
    },
    "07 - Cost Calculator": {
        "title": "Token Economics - The Full Picture",
        "description": "Real cost calculations for 1000 conversations/day. Baseline vs optimized comparison.",
        "lesson": "5 optimization wins: Routing, max_tokens, prompt optimization, caching, CRIS.",
        "script": "demo/07_cost_calculator.py",
    },
    "08 - Observability": {
        "title": "Invocation Logging + CloudWatch Monitoring",
        "description": "Production observability: per-request token tracking, cost attribution per user/app, throttling alarms, dashboards.",
        "lesson": "Enable invocation logging DAY ONE. identity.arn enables per-app chargeback. Throttle alarms prevent silent failures.",
        "script": "demo/08_observability.py",
    },
}

info = DEMO_INFO[demo_choice]

# Display demo info
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(info["title"])
    st.markdown(info["description"])

with col2:
    st.markdown(f"""
    <div class="demo-header">
    PRODUCTION LESSON<br/>
    {info["lesson"]}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Show source code
with st.expander("VIEW SOURCE CODE", expanded=False):
    script_path = os.path.join(os.path.dirname(__file__), info["script"])
    if os.path.exists(script_path):
        with open(script_path) as f:
            st.code(f.read(), language="python")
    else:
        st.warning(f"Script not found: {script_path}")

# Custom query input for Demo 06
custom_query_arg = ""
run_mode = "default"
if "06_prompt_routing" in info["script"]:
    st.markdown("**Try your own query or run all test queries:**")
    st.markdown("""
    <p style="font-size:12px; color:#888 !important;">
    💡 <b>Simple example:</b> "How do I request a standing desk?"<br/>
    💡 <b>Complex example:</b> "Draft a migration plan to move our on-prem Active Directory to AWS SSO, including rollback procedures and a phased timeline for 5000 users across 3 regions."
    </p>
    """, unsafe_allow_html=True)
    custom_query_arg = st.text_input(
        "Custom query:",
        placeholder="Type or paste a query here...",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("▶ RUN CUSTOM QUERY", type="primary", use_container_width=True, disabled=not custom_query_arg.strip()):
            run_mode = "custom"
    with col_b:
        if st.button("▶ RUN ALL TEST QUERIES", use_container_width=True):
            run_mode = "all"

# Run button (for all other demos)
should_run = run_mode != "default"
if "06_prompt_routing" not in info["script"]:
    should_run = st.button("RUN DEMO", type="primary", use_container_width=True)
    custom_query_arg = ""  # No custom query for other demos

if should_run:
    st.markdown("### Terminal Output")
    st.markdown(f'<p style="color:#4EC400; font-family:monospace;">$ python {info["script"]}</p>', unsafe_allow_html=True)

    script_path = os.path.join(os.path.dirname(__file__), info["script"])

    try:
        env = os.environ.copy()
        env["AWS_REGION"] = region
        env["NO_COLOR"] = "1"
        env["COLUMNS"] = "100"
        env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output for streaming

        # Stream output in real-time (line by line)
        cmd = [sys.executable, "-u", script_path]
        if run_mode == "custom" and custom_query_arg.strip():
            cmd.append(custom_query_arg.strip())

        process = subprocess.Popen(
            cmd,  # -u = unbuffered, optional custom query arg
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.path.dirname(__file__),
        )

        # Real-time streaming output
        output_container = st.empty()
        full_output = ""

        for line in process.stdout:
            full_output += line
            # Update the terminal display in real-time
            output_container.code(full_output, language="text")

        # Capture any remaining stderr
        process.wait(timeout=60)
        stderr_output = process.stderr.read()

        if stderr_output:
            st.error(f"Errors:\n{stderr_output}")

        if process.returncode != 0 and not stderr_output:
            st.error(f"Script exited with code {process.returncode}")

    except subprocess.TimeoutExpired:
        process.kill()
        st.error("Script timed out (60s limit)")
    except Exception as e:
        st.error(f"Failed to run script: {e}")

# Footer
st.markdown("---")
st.markdown("""
**AWS Elevate Days 2026** | Amazon Bedrock - Building GenAI Applications at Production Scale  
GitHub: [bedrock-production-patterns](https://github.com/jatinmehrotra/bedrock-production-patterns)
""")
