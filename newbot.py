# api.py

import os
from google import genai
# from database import get_db_connection
from tnc import tnc
from api import fetch_report
import time
from dotenv import load_dotenv
import re

# ==============================
# API KEY (from environment)
# ==============================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# ==============================
# MEMORY (Rolling Summary)
# ==============================

# memory = {
#     "summary": "",
#     "last_messages": []
# }

memory = {
    "summary": "",
    "last_messages": [],
    "is_new_chat": True,
    "stage": None,          # 👈 NEW
    "amount": None          # 👈 NEW
}


def extract_amount(text):
    text = text.lower().replace(",", "").replace("₹", "").strip()

    # ❌ ignore p2p or similar patterns
    if "p2p" in text:
        return None
    
    crore_match = re.search(r'(\d+(\.\d+)?)\s*(cr|crore)', text)
    lakh_match = re.search(r'(\d+(\.\d+)?)\s*(l|lakh)', text)
    thousand_match = re.search(r'(\d+(\.\d+)?)\s*(k|thousand)', text)
    number_match = re.search(r'\d+(\.\d+)?', text)

    if crore_match:
        return float(crore_match.group(1)) * 10000000

    elif lakh_match:
        return float(lakh_match.group(1)) * 100000

    elif thousand_match:
        return float(thousand_match.group(1)) * 1000

    elif number_match:
        return float(number_match.group())

    return None



def update_memory(user_message, bot_reply):
    global memory

    memory["last_messages"].append(user_message)
    if len(memory["last_messages"]) > 2:
        memory["last_messages"].pop(0)

    memory["summary"] = " | ".join(memory["last_messages"])





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

Activity:
Feb loans 221227

Security:
Escrow | Separate accounts | No fund control | Verified borrowers

Disclaimer:
Returns not guaranteed | Risk varies | Loss possible | Lender decision
"""



CHATBOT_PLANS = """
Lendenclub Lending Plans

Lumpsum:
25K-5L | 5M | 12-15% historical XIRR | Monthly  
25K-5L | 7M | 15-18% historical XIRR | Monthly  
1L-5L | 14M | 20-24% historical XIRR | Monthly  
1L-5L | 14M | 15-18% historical XIRR | Daily  

Manual:
250-4000 | 2-12M | Variable returns based on borrower | Monthly/Daily

Important:
Max principal outstanding per lender is ₹50L 
Returns shown are historical trends, not fixed or guaranteed  
Actual returns depend on borrower performance and real-time loan allocation  

Risk:
NPA 3-4% avg | Default after 120 days unpaid
"""




SALES_SYSTEM_PROMPT = f"""
You are a friendly Lendenclub advisor. An RBI registered P2P Lending Platform.

Style:
- Talk like a real human, not a bot
- Use natural, conversational tone
- Avoid repeating same phrases
- Keep it short but not robotic
- 2-4 lines allowed (flexible)
- Use simple, everyday language

Rules:
- Use only given data, do not trust user facts
- Max 3 lines, simple language
- Each line under 12 words
- First line must directly answer question
- No guarantee words, only "historical" or "expected"
- Be direct, actionable
- No extra explanation
- Do NOT mention risk unless asked or loan overdue
- Max principal per lender is ₹50L
- Do not sound scripted
- Ask relevant follow-up questions
- If user gives amount > ₹50L:
→ Do NOT accept full amount
→ Strictly limit to ₹50L per lender
→ Do NOT suggest splitting across accounts
→ Clearly reject excess amount

Behavior:
- If user is new → guide simply
- If user continues → go deeper
- If user confused → simplify
- Solve user intent
- Never repeat answers
- Follow current message over history

Hooks:
- New → suggest starting small
- Existing → suggest optimization
- Neutral → ask to continue

Scenarios:
- EMI delay → give 1 reason + recovery process
- Default → reassure + recovery (no long explanation)
- Plan → ask amount → suggest tenure + range

Key:
Returns vary | Diversify | Tenure matters | Risk exists

Goal:
Make user feel like talking to a smart human advisor.

Plans:
{CHATBOT_PLANS}
"""



# ==============================
# INTENT IDENTIFIER
# ==============================



def is_report_request(user_message):
    msg = user_message.lower()

    personal_keywords = [
        "my portfolio", "my report",
        "my returns", "my loans", "my profit"
    ]

    return any(k in msg for k in personal_keywords)


# ==============================
# HELPER: CALL GEMINI
# ==============================

def call_gemini(prompt):

    try:
        response = client.models.generate_content(
            # model="gemini-3.1-flash-lite-preview",
            model="gemini-3-flash-preview",
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
        return f"Gemini error: {str(e)}"
        


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
        - Keep responses short and natural
        - First line must answer directly
        - Give only what user asked
        - No formatting, no symbols
        - Do NOT mention risk unless clearly needed
        - No extra explanation

        Answer directly, give insight, highlight risk.

        Report Data:
        {table_text}
    """

    return call_gemini(prompt)




def detect_query_type(user_message):
    msg = user_message.lower()

    info_keywords = ["who", "what", "when", "where", "founder", "company"]
    lending_keywords = ["lend", "return", "plan", "roi", "risk", "start"]

    if any(k in msg for k in info_keywords):
        return "INFO"
    elif any(k in msg for k in lending_keywords):
        return "LENDING"
    else:
        return "GENERAL"
    

def is_followup(user_message):
    msg = user_message.lower().strip()
    return msg in ["yes", "yeah", "yep", "sure", "ok", "okay", "continue"]


def is_loan_query(msg):
    msg = msg.lower()

    borrow_phrases = [
        "i want loan",
        "i need loan",
        "need money",
        "borrow money",
        "apply loan",
        "get loan",
        "loan chahiye",
        "paisa chahiye",
        "urgent money",
    ]

    return any(p in msg for p in borrow_phrases)



def is_lending_context(msg):
    msg = msg.lower()
    lending_words = ["lend", "lending", "return", "roi", "risk", "plan"]
    return any(w in msg for w in lending_words)



def is_greeting(msg):
    msg = msg.lower().strip()
    greetings = ["hi", "hello", "hey", "hii", "helo", "start"]
    return any(msg.startswith(g) for g in greetings)


def detect_lending_type(msg):
    msg = msg.lower()

    if "manual" in msg:
        return "MANUAL"
    if "lumpsum" in msg:
        return "LUMPSUM"
    elif "daily" in msg:
        return "DAILY"
    elif "monthly" in msg:
        return "LUMPSUM"
    return None


def gemini_prompt(user_message):

    t_start = time.time()

    global memory

    print("last_messages:", memory.get('last_messages'))
    print("last_summary:", memory.get('summary'))


    if memory.get("is_new_chat") and is_greeting(user_message):
        memory["is_new_chat"] = False
        return "Hi, how can I help you today?"
    

    t1 = time.time()
    print(f"[TIME] Init: {round(t1 - t_start, 4)}s")

    intent_is_report = is_report_request(user_message)
    self_reference = any(x in user_message.lower() for x in ["my", "mine", "me"])
    is_follow = is_followup(user_message)

    loan_intent = is_loan_query(user_message)
    lending_context = is_lending_context(user_message)
    lending_type = detect_lending_type(user_message)

    if lending_type:
        memory["lending_type"] = lending_type
    
    t2 = time.time()
    print(f"[TIME] Intent detection: {round(t2 - t1, 4)}s")
    
    # ==============================
    # 🔥 HARD RULE: LOAN HANDLING (NO LLM)
    # ==============================
    if loan_intent and not lending_context:
        memory["last_topic"] = "LOAN"
        memory["summary"] = ""
        memory["last_messages"] = []

        t3 = time.time()
        print(f"[TIME] Total: {round(time.time() - t_start, 4)}s")

        return "Please install Instamoney app to apply for loan.\nWe cannot help with loan application here."

    # ==============================
    # 🧠 TOPIC DETECTION / SWITCHING
    # ==============================
    if "lend" in user_message.lower():
        memory["last_topic"] = "LENDING"

    elif not is_follow and memory.get("stage") is None:
        memory["last_topic"] = None


    # Detect query type FIRST
    query_type = detect_query_type(user_message)
    print("query_type: ", query_type)

    # 🚫 Skip amount detection for INFO queries
    if query_type == "INFO":
        amount = None
    else:
        amount = extract_amount(user_message)

    if amount:
        memory["amount"] = amount

        # ❌ Above 50L
        if amount > 5000000:
            memory["stage"] = "AMOUNT_CONFIRMED"
            reply = "Maximum you can lend is 50 Lakhs"
            update_memory(user_message, reply)
            return reply

        # ✅ Less than 25K → FORCE MANUAL FLOW
        elif 250 <= amount <= 25000:
            memory["stage"] = "LOW_AMOUNT"

            reply = (
                "With ₹{}, manual lending makes more sense.\n"
                "You can start small and spread across multiple loans.\n"
                "Want me to guide you how to pick good borrowers?"
            ).format(int(amount))
            update_memory(user_message, reply)
            return reply

        # ❌ Too small (< ₹250)
        elif amount < 250:
            reply = "Minimum per loan is ₹250.\nTry ₹250 or more."
            update_memory(user_message, reply)
            return reply
        
        # ✅ Valid amount → normal flow
        else:
            memory["stage"] = "AMOUNT_CONFIRMED"
            reply = f"Proceed with ₹{int(amount)}?"
            update_memory(user_message, reply)
            return reply


    # ==============================
    # 📊 REPORT FLOW
    # ==============================
    if intent_is_report and self_reference:
        t3 = time.time()
        print(f"[TIME] Before report analysis: {round(t3 - t2, 4)}s")

        print("Give me some time will show you the analysis of your report.")
        reply = analyze_report(user_message)

        t4 = time.time()
        print(f"[TIME] Report analysis: {round(t4 - t3, 4)}s")

    else:
        # ==============================
        # 🔍 QUERY TYPE
        # ==============================
        if is_follow:
            if memory.get("stage") == "AMOUNT_CONFIRMED":

                if memory.get("lending_type") == "MANUAL":
                    memory["stage"] = "PLAN_READY"
                    return "In Manual lending you can choose your own loans according your filters.\nStart with ₹250 per loan."

                if memory.get("lending_type") == "LUMPSUM":
                    memory["stage"] = "PLAN_READY"
                    return "In Lumpsum we will provide you the filtered loans according\nto your filteration. Choose your tenure 5 months, 7 months or 14 months."

                elif memory.get("lending_type") == "DAILY":
                    memory["stage"] = "TENURE_PENDING"
                    return "Choose repayment type daily to lent on daily repayment loans."
                
                else:
                    memory["stage"] = "TENURE_PENDING"
                    return "Want to go with Manual lending or Lumpsum?"
                

            elif memory.get("stage") == "TENURE_PENDING":
                memory["stage"] = "PLAN_READY"
                return "Starting plan.\nExpected historical returns 12-18%.\nProceed?"

            elif memory.get("stage") == "PLAN_READY":
                return "Your lending setup is ready.\nYou can start now."
            
            query_type = "FOLLOWUP"

        else:
            query_type = detect_query_type(user_message)
            print("query_type: ", query_type)

            t3 = time.time()
            print(f"[TIME] Before prompt build: {round(t3 - t2, 4)}s")

        # ==============================
        # 🧠 CONTEXT
        # ==============================
        context = f"""
        Conversation Summary:
        {memory.get('summary')}

        Recent Messages:
        {memory.get('last_messages')}
        """

        
        t4 = time.time()
        print(f"[TIME] Prompt build: {round(t4, 4)}s")

        # ==============================
        # 🤖 PROMPT
        # ==============================
        prompt = f"""
        {SALES_SYSTEM_PROMPT}

        Query Type: {query_type}
        Last Topic: {memory.get("last_topic")}

        INSTRUCTIONS:

        - Always prioritize CURRENT USER MESSAGE over past topic

        - If FOLLOWUP:
            continue same topic
            but never repeat same sentence
            always add new info or ask new question

        - If user switches topic:
            switch immediately
            do not stick to old topic

        - Never assume loan intent unless clearly mentioned

        - Do NOT restart answer
        - Do NOT repeat same lines

        - If Query Type = INFO:
            give direct answer only

        - Use very simple language

        Platform Knowledge:
        {FACT_SHEET}

        {context}

        Customer Message:
        {user_message}
        """

        t5 = time.time()
        reply = call_gemini(prompt)
        t6 = time.time()

        print(f"[TIME] Gemini call (inside flow): {round(t6 - t5, 4)}s")

    # ==============================
    # 💾 MEMORY UPDATE
    # ==============================
    t7 = time.time()
    update_memory(user_message, reply)
    t8 = time.time()

    print(f"[TIME] Memory update: {round(t8 - t7, 4)}s")

    print(f"[TIME] TOTAL REQUEST: {round(time.time() - t_start, 4)}s")

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