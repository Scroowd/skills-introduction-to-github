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
    page_title="Job Bot — Vasu Sood",
    page_icon="🎯",
    layout="centered",
)

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
    .job-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 4px solid #0073b1;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.8rem;
    }
    .job-title { font-size: 15px; font-weight: bold; color: #0073b1; }
    .job-meta  { font-size: 13px; color: #555; margin: 2px 0; }
    .match-badge {
        display: inline-block;
        background: #28a745;
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONSTANTS
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

RESUME_SYSTEM_PROMPT = """You are an expert career coach and professional resume writer specializing in
financial markets, commodity trading, portfolio management, and wealth management roles —
particularly for Switzerland, UK, USA, and Australia.

Guidelines:
- Keep the resume concise and impactful (max 1 page shown)
- Use strong action verbs and quantified achievements
- Mirror keywords from the job description naturally (ATS optimization)
- For Swiss/European roles: be direct, professional, no fluff
- Cover letter: 3-4 paragraphs, specific to the company and role
- Never fabricate experience — only reframe and emphasize what exists
- Format output clearly with section headers
"""

ROLE_CATEGORIES = {
    "🛢️ Commodity Trading": [
        "Commodity Trader", "Energy Trader", "Metals Trader", "Agricultural Trader",
        "Commodity Analyst", "Market Analyst commodities", "Oil Trader", "Gas Trader",
    ],
    "💼 Portfolio Management": [
        "Portfolio Manager", "Fund Manager", "Investment Manager",
        "Asset Manager", "Portfolio Analyst", "Investment Analyst",
    ],
    "🏦 Wealth Management": [
        "Wealth Manager", "Private Banker", "Relationship Manager wealth",
        "Wealth Advisor", "Private Wealth Analyst", "Client Advisor wealth management",
    ],
    "📊 All Finance Roles": [
        "Commodity Trader", "Portfolio Manager", "Wealth Manager",
        "Energy Trader", "Investment Manager", "Market Analyst",
    ],
}

LOCATION_QUERIES = {
    "🇨🇭 Switzerland": "Switzerland Geneva Zurich Basel",
    "🇬🇧 UK / Europe": "London UK Europe Frankfurt Amsterdam",
    "🇺🇸 USA": "New York Chicago Houston USA",
    "🇦🇺 Australia": "Sydney Melbourne Australia",
    "🌍 All Locations": "Europe USA Australia Switzerland UK",
}

JOB_BOARDS = {
    "🇨🇭 Switzerland": [
        ("jobs.ch", "https://www.jobs.ch/en/vacancies/?term={query}"),
        ("eFinancialCareers CH", "https://www.efinancialcareers.ch/search?q={query}&location=Switzerland"),
    ],
    "🇬🇧 UK / Europe": [
        ("eFinancialCareers UK", "https://www.efinancialcareers.co.uk/search?q={query}"),
        ("totaljobs.com", "https://www.totaljobs.com/jobs/{query}"),
    ],
    "🇺🇸 USA": [
        ("eFinancialCareers US", "https://www.efinancialcareers.com/search?q={query}&location=United+States"),
        ("Indeed US", "https://www.indeed.com/jobs?q={query}&l=United+States"),
    ],
    "🇦🇺 Australia": [
        ("SEEK Australia", "https://www.seek.com.au/{query}-jobs/in-All-Australia"),
        ("eFinancialCareers AU", "https://www.efinancialcareers.com.au/search?q={query}"),
    ],
    "🌍 All Locations": [
        ("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords={query}"),
        ("eFinancialCareers", "https://www.efinancialcareers.com/search?q={query}"),
    ],
}


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def is_url(text: str) -> bool:
    return bool(re.match(r'^https?://', text.strip(), re.IGNORECASE))


def search_jobs(role_category: str, location: str, api_key: str) -> list[dict]:
    """
    Use Claude web_search + web_fetch to find live job openings.
    Returns list of dicts: {title, company, location, summary, url, match_score}
    """
    client = anthropic.Anthropic(api_key=api_key)

    roles = ROLE_CATEGORIES[role_category]
    location_query = LOCATION_QUERIES[location]

    search_prompt = f"""Search for live job openings matching these criteria:

Roles (search ALL of these): {', '.join(roles)}
Locations: {location_query}
EXCLUDE: software engineer, developer, data scientist, quant developer, coding roles

Search job boards including: LinkedIn, eFinancialCareers, Indeed, jobs.ch (for Switzerland),
SEEK (for Australia), totaljobs (for UK).

For each job found, extract:
- Job title
- Company name
- Location (city, country)
- Brief 1-2 sentence description of the role
- Direct apply URL

Return a JSON array of up to 10 jobs:
[
  {{
    "title": "...",
    "company": "...",
    "location": "...",
    "summary": "...",
    "url": "https://...",
    "match_score": "High/Medium"
  }},
  ...
]

Only include real, currently open positions with valid apply links.
Prioritize roles that match a commodity trader / market analyst background with
$2.1M P&L track record, Bloomberg Terminal, spread trading experience.
"""

    messages = [{"role": "user", "content": search_prompt}]
    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
        {"type": "web_fetch_20260209", "name": "web_fetch"},
    ]

    max_iterations = 6
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "pause_turn":
            continue

        tool_results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": ""}
            for b in response.content if b.type == "tool_use"
        ]
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    final_text = "".join(b.text for b in response.content if hasattr(b, "text"))

    # Extract JSON array from response
    json_match = re.search(r'\[.*\]', final_text, re.DOTALL)
    if json_match:
        try:
            jobs = json.loads(json_match.group())
            return jobs if isinstance(jobs, list) else []
        except json.JSONDecodeError:
            pass

    return []


def fetch_job_from_url(url: str, api_key: str) -> dict:
    """Use Claude's web_fetch tool to pull job details from a URL."""
    client = anthropic.Anthropic(api_key=api_key)

    messages = [
        {
            "role": "user",
            "content": (
                f"Fetch this job posting and extract the details:\nURL: {url}\n\n"
                f"Return ONLY a JSON object:\n"
                f'{{"company": "...", "role": "...", "job_description": "full description"}}\n\n'
                f"Include all requirements, responsibilities, and qualifications."
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
    """Stream tailored resume + cover letter."""
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
        system=RESUME_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
st.title("🎯 Job Bot — Vasu Sood")
st.caption("Find jobs · Tailor resume · Generate cover letter")

# API Key
with st.expander("🔑 API Key (required)", expanded=not st.session_state.get("api_key")):
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com — never stored permanently",
        value=st.session_state.get("api_key", ""),
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.success("API key saved for this session ✓")

api_key = st.session_state.get("api_key", "")

st.divider()

# ── TABS ──
tab_find, tab_url, tab_text = st.tabs([
    "🔍 Find Jobs",
    "🔗 Apply via URL",
    "📋 Apply via Text",
])

# ────────────────────────────
# TAB 1: JOB FINDER
# ────────────────────────────
with tab_find:
    st.markdown("### Find live job openings matching your profile")
    st.caption("Searches LinkedIn, eFinancialCareers, jobs.ch, SEEK, Indeed in real time")

    col1, col2 = st.columns(2)
    with col1:
        role_choice = st.selectbox(
            "Role type",
            list(ROLE_CATEGORIES.keys()),
            index=3,  # default: All Finance Roles
        )
    with col2:
        location_choice = st.selectbox(
            "Location",
            list(LOCATION_QUERIES.keys()),
            index=0,  # default: Switzerland
        )

    # Show quick-search links for manual browsing
    with st.expander("🔗 Quick-search links (tap to browse manually)"):
        boards = JOB_BOARDS.get(location_choice, JOB_BOARDS["🌍 All Locations"])
        role_slug = ROLE_CATEGORIES[role_choice][0].replace(" ", "+")
        for board_name, board_url in boards:
            link = board_url.format(query=role_slug)
            st.markdown(f"- [{board_name}]({link})")

    if not api_key:
        st.info("Enter your API key above to use the live job search.")
    else:
        if st.button("🔍 Search Live Jobs Now", key="btn_search"):
            st.session_state.pop("job_results", None)
            with st.spinner(f"Searching for {role_choice} roles in {location_choice}..."):
                try:
                    results = search_jobs(role_choice, location_choice, api_key)
                    st.session_state["job_results"] = results
                    st.session_state["search_done"] = True
                except anthropic.AuthenticationError:
                    st.error("Invalid API key.")
                except Exception as e:
                    st.error(f"Search error: {e}")

    # Show results
    if st.session_state.get("job_results") is not None:
        results = st.session_state["job_results"]
        if not results:
            st.warning("No jobs found. Try a different role or location.")
        else:
            st.success(f"Found {len(results)} openings — tap Apply to generate your tailored documents")
            st.divider()

            for i, job in enumerate(results):
                match = job.get("match_score", "Medium")
                badge_color = "🟢" if match == "High" else "🟡"

                with st.container():
                    st.markdown(f"""
<div class="job-card">
  <div class="job-title">{job.get('title', 'Unknown Role')}</div>
  <div class="job-meta">🏢 {job.get('company', '—')} &nbsp;|&nbsp; 📍 {job.get('location', '—')} &nbsp;|&nbsp; {badge_color} {match} match</div>
  <div class="job-meta" style="margin-top:4px">{job.get('summary', '')}</div>
</div>
""", unsafe_allow_html=True)

                    col_apply, col_link = st.columns([1, 1])
                    with col_apply:
                        if st.button(
                            "✍️ Tailor Resume",
                            key=f"tailor_{i}",
                            use_container_width=True,
                        ):
                            st.session_state["pending_job_url"] = job.get("url", "")
                            st.session_state["pending_job"] = {
                                "company": job.get("company", "Unknown"),
                                "role": job.get("title", "Unknown"),
                            }
                            st.session_state["tailor_mode"] = "from_search"

                    with col_link:
                        url = job.get("url", "")
                        if url:
                            st.link_button("🔗 Apply Now", url, use_container_width=True)

                    st.markdown("---")

# ────────────────────────────
# TAB 2: APPLY VIA URL
# ────────────────────────────
with tab_url:
    st.markdown("**Paste any LinkedIn, Indeed, or jobs.ch URL:**")
    url_input = st.text_input(
        "Job URL",
        placeholder="https://www.linkedin.com/jobs/view/...",
        label_visibility="collapsed",
    )

    if url_input and not is_url(url_input):
        st.warning("That doesn't look like a URL. Use the 'Apply via Text' tab instead.")

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

# ────────────────────────────
# TAB 3: APPLY VIA TEXT
# ────────────────────────────
with tab_text:
    st.markdown("**Paste the job description text:**")
    company_input = st.text_input("Company name", placeholder="e.g. Glencore, Trafigura, UBS")
    role_input = st.text_input("Role title", placeholder="e.g. Commodity Trader, Portfolio Manager")
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
# GENERATION (shared by all tabs)
# ──────────────────────────────────────────────

# Handle "Tailor Resume" clicked from job search results
if st.session_state.get("tailor_mode") == "from_search":
    pending_url = st.session_state.pop("pending_job_url", "")
    pending_job = st.session_state.pop("pending_job", {})
    st.session_state.pop("tailor_mode", None)
    st.session_state.pop("generated", None)
    st.session_state.pop("output", None)

    if pending_url:
        with st.spinner(f"Fetching full job details for {pending_job.get('role')}..."):
            try:
                job_data = fetch_job_from_url(pending_url, api_key)
                # Use search result company/role if fetch didn't extract them well
                if job_data["company"] == "Unknown Company":
                    job_data["company"] = pending_job.get("company", "Unknown")
                if job_data["role"] == "Unknown Role":
                    job_data["role"] = pending_job.get("role", "Unknown")
                st.session_state["job_data"] = job_data
                st.session_state["source"] = "search"
            except Exception as e:
                st.error(f"Error fetching job: {e}")
    else:
        # No URL — use what we have from search result
        st.session_state["job_data"] = {
            "company": pending_job.get("company", "Unknown"),
            "role": pending_job.get("role", "Unknown"),
            "job_description": f"{pending_job.get('role')} at {pending_job.get('company')}",
        }
        st.session_state["source"] = "search"

if "job_data" in st.session_state and "source" in st.session_state:
    job_data = st.session_state["job_data"]
    company = job_data["company"]
    role = job_data["role"]
    job_description = job_data["job_description"]

    st.divider()
    st.markdown(f"### ✍️ Generating for: **{role}** at **{company}**")

    if not st.session_state.get("generated"):
        output_area = st.empty()
        full_text = ""

        try:
            for chunk in generate_documents(job_description, company, role, api_key):
                full_text += chunk
                output_area.markdown(full_text)
            st.session_state["output"] = full_text
            st.session_state["generated"] = True
            del st.session_state["job_data"]
            del st.session_state["source"]
        except anthropic.AuthenticationError:
            st.error("Invalid API key. Check console.anthropic.com")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.get("generated") and st.session_state.get("output"):
        output = st.session_state["output"]
        st.markdown(output)
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            fname = f"{re.sub(r'[^\w]','_', company.lower()[:20])}_{re.sub(r'[^\w]','_', role.lower()[:20])}.txt"
            st.download_button(
                label="⬇️ Download .txt",
                data=output,
                file_name=fname,
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            if st.button("🔄 Start Over", use_container_width=True):
                for key in ["output", "generated", "job_data", "source"]:
                    st.session_state.pop(key, None)
                st.rerun()
