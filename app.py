"""
Resume & Cover Letter Bot — Web App for Vasu Sood
Works on iPhone/Android/Desktop via browser.
Deploy free at: https://streamlit.io/cloud
"""

import streamlit as st
import anthropic
import re
import json

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Bot — Vasu Sood",
    page_icon="📄",
    layout="centered",
)

# Mobile-friendly CSS
st.markdown("""
<style>
    .main > div { padding: 1rem 1rem 2rem; }
    h1 { font-size: 1.6rem !important; }
    .stTextArea textarea { font-size: 14px; }
    .stButton button {
        width: 100%;
        background-color: #0073b1;
        color: white;
        font-size: 16px;
        padding: 0.6rem;
        border-radius: 8px;
    }
    .result-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        white-space: pre-wrap;
        font-family: monospace;
        font-size: 13px;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# BASE RESUME
# ──────────────────────────────────────────────
BASE_RESUME = """
VASU SOOD
Bangalore, India | +91 70155 54624 | vasusood0504@gmail.com
linkedin.com/in/vasu-sood-901592181

PROFILE SUMMARY
Quantitative Trader & Market Analyst with 4+ years of experience trading across global
commodities, energy, metals, and fixed income markets. Recognized as the 'Most Consistent
Trader of the Year' for consistent profitability and risk discipline. Generated over $2.1 million
in realized trading profits using mean reversion, spread, and volatility-based strategies. Strong
expertise in analyzing inter-commodity relationships, market structure, and macroeconomic trends.

PROFESSIONAL EXPERIENCE

Associate Market Analyst, Futures First
Nov 2021 - Present | Bangalore, India
- Traded over 25 global products including Brent, WTI, RBOB, Heating Oil, Natural Gas, Gold,
  Silver, Copper, Aluminum, Corn, Wheat, and Soymeal.
- Executed cross-commodity spread and volatility arbitrage trades such as Crack Spreads and
  Crush Spreads.
- Managed complex relative value structures across energy curves, metals, and agricultural markets.
- Delivered $2.1M in trading profits on $500K margin through disciplined risk management.
- Built analytical frameworks to monitor curve distortions, carry yields, and volatility shifts
  using Excel-based tools.

Market Analyst, OSTC
Jul 2021 - Nov 2021 | Mumbai, India
- Traded agricultural and energy commodities including Sugar, Coffee, Cocoa, Corn, and Gasoil
  across CBOT and NYMEX.
- Used seasonality and mean reversion to identify statistical trading opportunities.
- Focused on calendar spreads and volatility structures to balance directional and spread risk.
- Achieved steady alpha generation through exposure sizing and disciplined capital allocation.

EDUCATION
Birla Institute of Technology and Science (BITS), Pilani
B.E. Electrical & Electronics | M.Sc. Mathematics (2017 - 2022)

CORE SKILLS
Trading Strategies: Mean Reversion, Seasonality, Spread Trading, Volatility Arbitrage
Markets: Energy (Crude Oil, Gasoline, Natural Gas), Metals (Gold, Silver, Copper, Aluminum),
         Agriculture (Corn, Wheat, Soybean, Sugar)
Analytical Areas: Correlation Analysis, Market Microstructure, Carry Curve Modeling,
                  Term Structure Analysis
Tools: Bloomberg Terminal, Excel (Advanced), Market Data Analysis Frameworks
Risk Management: Hedging, Position Sizing, Correlation Risk, Portfolio Diversification

LEADERSHIP & ACHIEVEMENTS
- President, Wallstreet Club (BITS Pilani) - Led workshops on global markets and derivatives trading.
- Bronze Medalist, District Athletics (Haryana State Government).
- Represented India in Football Nationals.
"""

SYSTEM_PROMPT = """You are an expert career coach and professional resume writer specializing in
financial markets, commodity trading, and quantitative finance roles — particularly for
Switzerland, UK, USA, and Australia.

Guidelines:
- Keep the resume concise and impactful (max 1 page shown)
- Use strong action verbs and quantified achievements
- Mirror keywords from the job description naturally (ATS optimization)
- For Swiss/European roles: be direct, professional, no fluff
- Cover letter: 3-4 paragraphs, specific to the company and role
- Never fabricate experience — only reframe and emphasize what exists
- Format output clearly with section headers
"""


def is_url(text: str) -> bool:
    return bool(re.match(r'^https?://', text.strip(), re.IGNORECASE))


def fetch_job_from_url(url: str, api_key: str) -> dict:
    """Use Claude's web_fetch tool to pull job details from the URL."""
    client = anthropic.Anthropic(api_key=api_key)

    messages = [
        {
            "role": "user",
            "content": (
                f"Fetch this job posting and extract the details:\nURL: {url}\n\n"
                f"Return ONLY a JSON object with these exact fields:\n"
                f'{{"company": "company name", "role": "job title", '
                f'"job_description": "full job description text"}}\n\n'
                f"Include all requirements, responsibilities, and qualifications in job_description."
            ),
        }
    ]

    tools = [{"type": "web_fetch_20260209", "name": "web_fetch"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason in ("end_turn", "pause_turn"):
            break

        tool_results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": ""}
            for b in response.content if b.type == "tool_use"
        ]
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    final_text = "".join(b.text for b in response.content if hasattr(b, "text"))

    json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return {
                "company": data.get("company", "Unknown Company"),
                "role": data.get("role", "Unknown Role"),
                "job_description": data.get("job_description", final_text),
            }
        except json.JSONDecodeError:
            pass

    return {"company": "Unknown Company", "role": "Unknown Role", "job_description": final_text}


def generate_documents(job_description: str, company: str, role: str, api_key: str):
    """Stream tailored resume + cover letter from Claude."""
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""
Company: {company}
Role: {role}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S BASE RESUME:
{BASE_RESUME}

Please produce two things:

## 1. TAILORED RESUME

Rewrite the resume to best match this job description.
- Adjust Profile Summary to speak directly to this role
- Reorder and emphasize the most relevant bullet points
- Highlight the most relevant skills for THIS position
- Keep all facts accurate — do not invent experience
- Format cleanly, ready to copy-paste

## 2. COVER LETTER

Write a professional cover letter for Vasu Sood applying to {company} for {role}.
- Address: Hiring Manager at {company}
- Opening: Hook with the most impressive relevant achievement ($2.1M P&L or award)
- Para 2: Why this specific company/role excites him
- Para 3: Top 2-3 relevant skills and experiences he brings
- Closing: Call to action, mention open to relocation and visa sponsorship
- Tone: Confident, professional, not sycophantic
- Length: ~250-300 words
"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
st.title("📄 Resume Bot")
st.caption("Tailors your resume & writes a cover letter for any job")

# API Key input
with st.expander("🔑 API Key (required)", expanded=not st.session_state.get("api_key")):
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com — it's never stored",
        value=st.session_state.get("api_key", ""),
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.success("API key saved for this session ✓")

api_key = st.session_state.get("api_key", "")

st.divider()

# Input mode tabs
tab_url, tab_text = st.tabs(["🔗 Paste Job URL", "📋 Paste Job Text"])

job_description = ""
company = ""
role = ""

with tab_url:
    st.markdown("**Paste any LinkedIn, Indeed, or jobs.ch URL:**")
    url_input = st.text_input(
        "Job URL",
        placeholder="https://www.linkedin.com/jobs/view/...",
        label_visibility="collapsed",
    )

    if url_input and not is_url(url_input):
        st.warning("That doesn't look like a URL. Use the 'Paste Job Text' tab instead.")

    if url_input and is_url(url_input) and api_key:
        if st.button("🚀 Fetch & Generate", key="btn_url"):
            with st.spinner("Fetching job details from URL..."):
                try:
                    job_data = fetch_job_from_url(url_input, api_key)
                    st.session_state["job_data"] = job_data
                    st.session_state["source"] = "url"
                except Exception as e:
                    st.error(f"Failed to fetch URL: {e}")

    elif url_input and is_url(url_input) and not api_key:
        st.info("Enter your API key above first.")

with tab_text:
    st.markdown("**Paste the job description text:**")
    company_input = st.text_input("Company name", placeholder="e.g. Glencore, Trafigura, UBS")
    role_input = st.text_input("Role title", placeholder="e.g. Commodity Trader, Market Analyst")
    jd_input = st.text_area(
        "Job Description",
        placeholder="Paste the full job description here...",
        height=200,
        label_visibility="collapsed",
    )

    if jd_input and company_input and role_input and api_key:
        if st.button("🚀 Generate Documents", key="btn_text"):
            st.session_state["job_data"] = {
                "company": company_input,
                "role": role_input,
                "job_description": jd_input,
            }
            st.session_state["source"] = "text"

    elif jd_input and not api_key:
        st.info("Enter your API key above first.")

# ──────────────────────────────────────────────
# GENERATION
# ──────────────────────────────────────────────
if "job_data" in st.session_state and "source" in st.session_state:
    job_data = st.session_state["job_data"]
    company = job_data["company"]
    role = job_data["role"]
    job_description = job_data["job_description"]

    st.divider()
    st.markdown(f"### Generating for: **{role}** at **{company}**")

    if not st.session_state.get("generated"):
        output_area = st.empty()
        full_text = ""

        try:
            for chunk in generate_documents(job_description, company, role, api_key):
                full_text += chunk
                output_area.markdown(full_text)
            st.session_state["output"] = full_text
            st.session_state["generated"] = True
            # Clear job_data so it doesn't re-run on next interaction
            del st.session_state["job_data"]
            del st.session_state["source"]
        except anthropic.AuthenticationError:
            st.error("Invalid API key. Check your key at console.anthropic.com")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.get("generated") and st.session_state.get("output"):
        output = st.session_state["output"]
        st.markdown(output)
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download as .txt",
                data=output,
                file_name=f"{re.sub(r'[^\w]', '_', company.lower())}_{re.sub(r'[^\w]', '_', role.lower())}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            if st.button("🔄 Start Over", use_container_width=True):
                for key in ["output", "generated", "job_data", "source"]:
                    st.session_state.pop(key, None)
                st.rerun()
