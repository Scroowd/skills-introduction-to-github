#!/usr/bin/env python3
"""
Resume & Cover Letter Bot for Vasu Sood
Tailors resume and generates cover letter based on a job description.
Usage: python resume_bot.py
"""

import anthropic
import sys
import os
from pathlib import Path

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


def get_job_description() -> str:
    """Get job description from user (multi-line input)."""
    print("\n" + "="*60)
    print("  RESUME & COVER LETTER BOT — Powered by Claude")
    print("="*60)
    print("\nPaste the job description below.")
    print("When done, press Enter twice (blank line) to submit:\n")

    lines = []
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

    return "\n".join(lines).strip()


def get_company_info() -> tuple[str, str]:
    """Get company name and role title."""
    print("\nCompany name (e.g. Glencore, Trafigura, UBS): ", end="")
    company = input().strip() or "the company"
    print("Role title (e.g. Commodity Trader, Market Analyst): ", end="")
    role = input().strip() or "the role"
    return company, role


def generate_tailored_resume_and_cover_letter(
    job_description: str,
    company: str,
    role: str,
) -> None:
    """Call Claude to tailor resume and generate cover letter."""
    client = anthropic.Anthropic()

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
- Closing: Call to action, open to relocation/visa sponsorship
- Tone: Confident, professional, not sycophantic
- Length: ~250-300 words
"""

    print("\n" + "="*60)
    print(f"  Generating tailored resume + cover letter for {company}...")
    print("="*60 + "\n")

    output_file = f"output_{company.replace(' ', '_').lower()}_{role.replace(' ', '_').lower()}.txt"

    with open(output_file, "w") as f:
        f.write(f"TAILORED APPLICATION: {role} at {company}\n")
        f.write("="*60 + "\n\n")

    # Stream the response
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        full_response = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    # Save to file
    with open(output_file, "a") as f:
        f.write(full_response)

    print(f"\n\n{'='*60}")
    print(f"  Saved to: {output_file}")
    print("="*60)


def main():
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Get your key at: https://console.anthropic.com/")
        print("Then run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    company, role = get_company_info()
    job_description = get_job_description()

    if not job_description:
        print("No job description provided. Exiting.")
        sys.exit(1)

    generate_tailored_resume_and_cover_letter(job_description, company, role)


if __name__ == "__main__":
    main()
