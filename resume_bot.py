#!/usr/bin/env python3
"""
Resume & Cover Letter Bot for Vasu Sood
Paste a LinkedIn/Indeed job URL OR raw job description text.
Claude fetches the URL, extracts job details, then tailors your resume + cover letter.

Usage: python resume_bot.py
"""

import anthropic
import sys
import os
import json
import re

# ──────────────────────────────────────────────
# BASE RESUME DATA
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

Your job is to:
1. Analyze the job description provided
2. Tailor the candidate's resume to highlight the most relevant experience and skills
3. Write a compelling, personalized cover letter

Guidelines:
- Keep the resume concise (max 1 page for the tailored version shown)
- Use strong action verbs and quantified achievements
- Mirror keywords from the job description naturally (ATS optimization)
- For Swiss/European roles: be direct, professional, no fluff
- Cover letter: 3-4 paragraphs, specific to the company and role, not generic
- Never fabricate experience — only reframe and emphasize what exists
- Format output clearly with section headers
"""


def is_url(text: str) -> bool:
    """Check if the input looks like a URL."""
    text = text.strip()
    return bool(re.match(r'^https?://', text, re.IGNORECASE))


def fetch_job_from_url(url: str, client: anthropic.Anthropic) -> dict:
    """
    Use Claude's web_fetch tool to fetch the job page and extract:
    - company name
    - role title
    - full job description
    """
    print(f"\n  Fetching job details from URL...")

    messages = [
        {
            "role": "user",
            "content": (
                f"Please fetch this job posting URL and extract the following information:\n"
                f"URL: {url}\n\n"
                f"Extract and return ONLY a JSON object with these fields:\n"
                f'{{"company": "...", "role": "...", "job_description": "...full description..."}}\n\n'
                f"The job_description should include: role summary, responsibilities, requirements, "
                f"qualifications, and any other relevant details from the posting. Be thorough."
            ),
        }
    ]

    tools = [{"type": "web_fetch_20260209", "name": "web_fetch"}]

    # Agentic loop — Claude fetches the URL and returns structured data
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            tools=tools,
            messages=messages,
        )

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "pause_turn":
            # Server-side tool hit iteration limit — continue
            continue

        # Handle tool results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                # web_fetch is server-side — result comes back automatically
                # We just need to pass an empty result to continue
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "",
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    # Extract the JSON from Claude's final text response
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    # Try to parse JSON from response
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

    # Fallback: return raw text as job description
    return {
        "company": "Unknown Company",
        "role": "Unknown Role",
        "job_description": final_text,
    }


def get_input() -> tuple[str, str, str]:
    """
    Get input from user — either a URL or pasted job description.
    Returns (company, role, job_description).
    """
    print("\n" + "="*60)
    print("  RESUME & COVER LETTER BOT — Powered by Claude")
    print("="*60)
    print()
    print("Paste a LinkedIn/Indeed job URL  →  bot fetches it automatically")
    print("OR paste the job description text (press Enter twice when done)")
    print()
    print("Input: ", end="", flush=True)

    first_line = input().strip()

    if is_url(first_line):
        return first_line, None, None  # Signal to fetch URL

    # Multi-line text input
    print("(paste remaining lines, press Enter twice to finish)")
    lines = [first_line]
    consecutive_blanks = 0
    while True:
        try:
            line = input()
            if line == "":
                consecutive_blanks += 1
                if consecutive_blanks >= 2:
                    break
                lines.append(line)
            else:
                consecutive_blanks = 0
                lines.append(line)
        except EOFError:
            break

    job_text = "\n".join(lines).strip()

    print("\nCompany name (e.g. Glencore, Trafigura, UBS): ", end="")
    company = input().strip() or "the company"
    print("Role title (e.g. Commodity Trader, Market Analyst): ", end="")
    role = input().strip() or "the role"

    return None, company, role, job_text  # type: ignore


def generate_tailored_resume_and_cover_letter(
    job_description: str,
    company: str,
    role: str,
    client: anthropic.Anthropic,
) -> None:
    """Call Claude to tailor resume and generate cover letter."""
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
- Reorder and emphasize bullet points that are most relevant
- Adjust the Profile Summary to speak directly to this role
- Highlight the most relevant skills for THIS position
- Keep all facts accurate — do not invent experience
- Format it cleanly, ready to copy-paste

## 2. COVER LETTER

Write a professional cover letter for Vasu Sood applying to {company} for the {role} position.
- Address it to the Hiring Manager at {company}
- Opening: Hook with the most impressive relevant achievement
- Para 2: Why this specific company and role excites him
- Para 3: What he brings (top 2-3 relevant skills/experiences)
- Closing: Call to action, mention open to relocation and visa sponsorship
- Tone: Confident, professional, not sycophantic
- Length: ~250-300 words
"""

    print("\n" + "="*60)
    print(f"  Generating tailored resume + cover letter for {company}...")
    print("="*60 + "\n")

    safe_company = re.sub(r'[^\w]', '_', company.lower())[:30]
    safe_role = re.sub(r'[^\w]', '_', role.lower())[:30]
    output_file = f"output_{safe_company}_{safe_role}.txt"

    with open(output_file, "w") as f:
        f.write(f"TAILORED APPLICATION: {role} at {company}\n")
        f.write("="*60 + "\n\n")

    full_response = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    with open(output_file, "a") as f:
        f.write(full_response)

    print(f"\n\n{'='*60}")
    print(f"  Saved to: {output_file}")
    print("="*60)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Get your key at: https://console.anthropic.com/")
        print("Then run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    client = anthropic.Anthropic()

    result = get_input()

    # URL mode
    if result[0] is not None:
        url = result[0]
        job_data = fetch_job_from_url(url, client)
        company = job_data["company"]
        role = job_data["role"]
        job_description = job_data["job_description"]

        print(f"\n  Detected: {role} at {company}")
        print("  Press Enter to confirm, or type a correction: ", end="")
        correction = input().strip()
        if correction:
            # Allow overriding company/role if extraction was wrong
            parts = correction.split(" at ", 1)
            if len(parts) == 2:
                role, company = parts[0].strip(), parts[1].strip()
    else:
        # Text mode
        _, company, role, job_description = result

    if not job_description:
        print("Could not extract job description. Exiting.")
        sys.exit(1)

    generate_tailored_resume_and_cover_letter(job_description, company, role, client)


if __name__ == "__main__":
    main()
