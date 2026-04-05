# api.py

import os
from google import genai
# from database import get_db_connection
from tnc import tnc
from api import fetch_report

# ==============================
# API KEY (from environment)
# ==============================

GEMINI_API_KEY = "AIzaSyBXV__Tn-Pdm7LsjBUbKfU58mbWmImkSAs"

client = genai.Client(api_key=GEMINI_API_KEY)


# ==============================
# MEMORY (Rolling Summary)
# ==============================

memory = {
    "summary": "",
    "last_messages": []
}



def update_memory(user_message, bot_reply):
    global memory

    memory["last_messages"].append(user_message)
    if len(memory["last_messages"]) > 2:
        memory["last_messages"].pop(0)

    # simple summary (no API call)
    memory["summary"] = " | ".join(memory["last_messages"])



# ==============================
# FACT SHEET DATA
# ==============================


# FACT_SHEET = """
# LenDenClub Platform Fact Sheet (Feb 2026)

# Company Overview:
# - Operating since 2015
# - RBI registered NBFC-P2P platform
# - Operational across 29 states and 5 UTs
# - T+1 settlement system
# - Escrow-based fund security

# Scale & Growth:
# - Total AUM: ₹1,455 Crore
# - Total amount disbursed: ₹18,440 Crore
# - Total loans disbursed: 3.14 Crore
# - Registered lenders: 41.63 Lakh
# - Registered borrowers: 3.64 Crore

# Financial Performance (FY25):
# - Revenue: ₹236 Crore
# - Profit: ₹34 Crore

# Platform Performance:
# - NPA: 3.53%
# - AUM: 1455 Cr
# - No of loans disbursed: 3.14 Cr
# - Amount disbursed: 18,440 Cr
# - Registered Lenders: 41.63 L
# - Registered Borrowers: 3.43 Cr
# - On-time repayment: 97.21%
# - T+1 maintenance success: 99.59%
# - Collection efficiency: 97%+

# Loan Product Risk:
# - Personal loan NPA: 4.08%
# - Merchant loan NPA: 3.30%

# Returns (Recent Trends):
# - 5 month lending: 6.13% absolute return
# - 7 month lending: 9.20% absolute return
# - Manual lending (6 months avg): 8.6%

# Recent Activity:
# - Loans disbursed in Feb 2026: 221,227

# Technology:
# - Proprietary AI system: OmniCredit
# - Enables automated borrower risk assessment

# Security & Structure:
# - Escrow mechanism ensures fund safety
# - Separate lender and borrower accounts
# - No direct control of funds by platform

# Risk Disclaimer:
# - Lending returns are not guaranteed
# - Risk depends on borrower profile
# - Loss of principal or interest is possible
# - Lending decisions are fully at lender’s discretion
# """



FACT_SHEET = """
LenDenClub Feb 2026

Overview:
Since 2015 | RBI NBFC-P2P | 29 states 5 UTs | T+1 settlement | Escrow system

Scale:
AUM ₹1455Cr | Disbursed ₹18440Cr | Loans 3.14Cr  
Lenders 41.63L | Borrowers 3.64Cr

FY25:
Revenue ₹236Cr | Profit ₹34Cr

Performance:
NPA 3.53% | On-time 97.21% | Collection 97%+ | T+1 success 99.59%

Risk:
Personal NPA 4.08% | Merchant NPA 3.30%

Returns:
5M 6.13% | 7M 9.20% | Manual 8.6%

Activity:
Feb loans 221227

Tech:
OmniCredit AI risk engine

Security:
Escrow | Separate accounts | No fund control

Disclaimer:
Returns not guaranteed | Risk varies | Loss possible | Lender decision
"""


# ==============================
# INVESTMENT PLAN DATA
# ==============================

# CHATBOT_PLANS = """
# Lendenclub Investment Plans (For Reference)

# 1) Lumpsum
# ₹25K-₹5L | 12% to 15% (Historical range)
# Tenure: 5 months
# Repayment: Monthly

# 2) Lumpsum
# ₹25K-₹5L | 15% to 18% (Historical range)
# Tenure: 7 months
# Repayment: Monthly

# 3) Lumpsum
# ₹1L-₹5L | 20% to 24% (Historical range)
# Tenure: 14 months
# Repayment: Monthly

# 4) Lumpsum
# ₹1L-₹5L | 15% to 18% (Historical range)
# Tenure: 14 months
# Repayment: Daily

# 5) Manual Lending
# ₹250-₹4000
# ROI varies borrower to borrower
# Tenure: 2-12 months
# Repayment: Monthly or Daily

# NPA risk:
# Platform average 3% to 4%

# Recovery time period:
# 120 days. If borrower does not pay between this then duration then will be marked as defaulted.
# """


CHATBOT_PLANS = """
Lendenclub Lending Plans

Lumpsum:
25K-5L | 5M | 12-15% XIRR | Monthly  
25K-5L | 7M | 15-18% XIRR | Monthly  
1L-5L | 14M | 20-24% XIRR | Monthly  
1L-5L | 14M | 15-18% XIRR | Daily  

Manual:
250-4000 | 2-12M | Variable ROI | Monthly/Daily  

Risk:
NPA 3-4% avg | Default after 120 days unpaid
"""



# ==============================
# SALES SYSTEM PROMPT
# ==============================


# SALES_SYSTEM_PROMPT = f"""
# You are a professional lending advisor for Lendenclub, an RBI-registered P2P lending platform.

# Your role is to guide retail lenders in a smart, practical and persuasive way.

# -------------------------
# RESPONSE STYLE (VERY IMPORTANT)
# -------------------------
# - Max 5 lines
# - No long paragraphs
# - No markdown, no bullets, no symbols
# - Simple, clean, human conversational tone
# - Each line should add value (no filler)
# - Start by directly addressing user intent
# - Always keep tone confident + problem solving

# -------------------------
# CORE BEHAVIOR
# -------------------------
# - Think like advisor, not explainer
# - Focus on solving user's problem
# - Keep answers actionable
# - Be persuasive
# - Never guarantee returns

# -------------------------
# HOOK STRATEGY (VERY IMPORTANT)
# -------------------------

# Always end response with a HOOK

# Hooks must differ based on lender type:

# 1) NEW LENDER (no or very recent lending)
# - Encourage starting small
# - Build confidence
# - Example hooks:
#   "Want me to suggest a safe way to start lending?"
#   "Should I show how you can start with small amount?"

# 2) EXISTING LENDER (has past lending)
# - Focus on optimization
# - Suggest better allocation
# - Example hooks:
#   "Want me to improve your current returns?"
#   "Should I check where you can reduce risk in your lending?"

# -------------------------
# INVESTOR TYPE DETECTION
# -------------------------
# - If report data available:
#     Check Disbursement_Date
#     If no past loans → NEW LENDER
#     If loans exist → EXISTING LENDER

# - If no report:
#     Assume NEW LENDER by default

# -------------------------
# SCENARIO HANDLING
# -------------------------

# If EMI delayed or loan default:
# - Reassure calmly
# - Explain recovery process briefly
# - Reinforce diversification

# If user asks best plan:
# - Ask investment amount first
# - Suggest suitable tenure
# - Mention historical return range (no guarantee)

# -------------------------
# IMPORTANT REMINDERS
# -------------------------
# - Returns depend on borrower to borrower
# - Diversification reduces risk
# - Tenure impacts risk and returns
# - Platform fees vary

# -------------------------
# INVESTMENT PLANS
# -------------------------
# {CHATBOT_PLANS}

# If user wants loan → suggest Instamoney app.
# """


SALES_SYSTEM_PROMPT = f"""
You are a lending advisor for Lendenclub (RBI P2P).

Style:
Max 5 lines | short sentences | no markdown/symbols  
Clear, human, confident, problem-solving  
Start direct, no filler

Behavior:
Act like advisor  
Give actionable answers
Be persuasive, no return guarantee  

Hook (must end with question):
New lender → start small, build confidence  
Existing lender → optimize returns, reduce risk  

Lender Type:
If loans exist → Existing  
Else → New  

Scenarios:
Delay/default → reassure + recovery + diversify  
Best plan → ask amount → suggest tenure + return range  

Reminders:
Returns vary | Diversify | Tenure impacts risk | Fees apply  

Plans:
{CHATBOT_PLANS}

Loan need → suggest Instamoney app
"""


def is_report_request(user_message):

    prompt = f"""
Classify:
{user_message}

Answer: PERSONAL or GENERAL
"""

    result = call_gemini(prompt)

    print("result: ", result)

    return "PERSONAL" in result


# ==============================
# HELPER: CALL GEMINI
# ==============================

def call_gemini(prompt):

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            # model="gemini-3-flash-preview",
            contents=prompt
        )

        output = ""

        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                output += part.text

        # ✅ HARD WORD REPLACEMENT (final safety layer)
        output = output.replace("investment", "lending")
        output = output.replace("invest", "lend")
        output = output.replace("investor", "lender")

        return output.strip()

    except Exception as e:
        return f"AI error: {str(e)}"


# ==============================
# REPORT ANALYSIS
# ==============================

def analyze_report(user_message):

    report_data = fetch_report()

    if not report_data:
        return "No investment records found."

    headers = [
        "Order_ID","Loan_ID","Interest_Rate","Tenure","Repayment_Type",
        "LenDenClub_Score","Disbursement_Date","Disbursed_Amount",
        "Loan_Status","Principal_Received","Interest_Received",
        "Fee_Charges_Deducted","Total_Amount_Received",
        "Profit_Loss","days_past_due","NPA","Loan_Closure"
    ]

    table_text = ",".join(headers) + "\n"

    for row in report_data:
        row_values = [str(row.get(col, "")) for col in headers]
        table_text += ",".join(row_values) + "\n"

    # 🧠 Inject memory context
    context = f"""
Conversation Summary:
{memory['summary']}

Recent Messages:
{memory['last_messages']}
"""

    prompt = f"""
You are a financial portfolio advisor.

User question:
{user_message}

Context:
{context}

STRICT RULES:
- Max 5 lines ONLY
- Each line under 15 words
- No formatting, no symbols

Answer directly, give insight, highlight risk, end with hook.

Report Data:
{table_text}
"""

    return call_gemini(prompt)


# ==============================
# MAIN CHAT FUNCTION
# ==============================

def gemini_prompt(user_message):

    global memory

    intent_is_report = is_report_request(user_message)
    self_reference = any(x in user_message.lower() for x in ["my", "mine", "me"])

    # 🧠 Context detection from summary
    summary_has_portfolio = "portfolio" in memory["summary"].lower() or "npa" in memory["summary"].lower()

    # ✅ REPORT FLOW (with memory awareness)
    if intent_is_report and self_reference or summary_has_portfolio:
        print("Give me some time will show you the analysis of your report.")
        reply = analyze_report(user_message)

    else:
        # 🧠 Inject memory into sales prompt
        context = f"""
        Conversation Summary:
        {memory['summary']}

        Recent Messages:
        {memory['last_messages']}
        """

        prompt = f"""
            {SALES_SYSTEM_PROMPT}

            Platform Knowledge:
            {FACT_SHEET}

            {context}

            Customer Message:
            {user_message}
        """

        reply = call_gemini(prompt)

    # ✅ Update memory after response
    update_memory(user_message, reply)

    return reply





# if __name__ == "__main__":

#     print("Lendenclub AI Advisor\n")

#     while True:

#         user_input = input("You: ")

#         if user_input.lower() in ["exit","quit"]:
#             break

#         reply = gemini_prompt(user_input)

#         print("\nAI:", reply)
#         print()