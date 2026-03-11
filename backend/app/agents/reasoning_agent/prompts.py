"""
Prompt templates for the LLM Reasoning Agent.

These prompts instruct Llama-3 to EXPLAIN analytics results,
NOT to perform calculations. The LLM receives pre-computed
data and generates human-readable explanations.
"""


SYSTEM_PROMPT = """You are an expert collections intelligence analyst at a bank.
Your role is to explain risk assessments and recovery strategy recommendations 
to collection agents in clear, professional language.

IMPORTANT RULES:
1. You DO NOT perform any calculations — all numbers are provided to you.
2. You EXPLAIN the results in plain language that a collection agent can understand.
3. You provide actionable guidance based on the data and policies provided.
4. You maintain a professional, empathetic tone — remember these are real customers.
5. Keep explanations concise but thorough — typically 3-5 paragraphs.
6. Reference specific data points (DPD, credit score, payment history) in your explanation.
7. If policy context is provided, reference relevant policies in your recommendation.
"""


RISK_EXPLANATION_PROMPT = """Based on the following risk assessment data and context, 
provide a clear explanation for the collection agent.

=== CUSTOMER PROFILE ===
Customer: {customer_name} ({customer_id})
Loan: {loan_id} ({loan_type})
Monthly Income: ₹{monthly_income:,.0f}
Employment: {employment_type}
Credit Score: {credit_score}

=== RISK ASSESSMENT ===
Days Past Due: {days_past_due}
DPD Classification: {dpd_classification}
Customer Segment: {customer_segment}
Self-Cure Probability: {self_cure_probability:.0%}
Value at Risk: ₹{value_at_risk:,.0f}

=== PAYMENT BEHAVIOR ===
Total Payments: {total_payments}
On-Time Payments: {on_time_payments}
Late Payments: {late_payments}
Payment Consistency: {payment_consistency:.0%}
Delay Trend: {delay_trend}

=== FINANCIAL EXPOSURE ===
Outstanding Balance: ₹{outstanding_balance:,.0f}
Overdue Amount: ₹{overdue_amount:,.0f}
Exposure Ratio: {exposure_ratio:.2%}

=== RECOMMENDED STRATEGY ===
Action: {recommended_action}
Risk Level: {risk_level}
Expected Recovery: ₹{expected_recovery:,.0f}
Estimated NPV: ₹{estimated_npv:,.0f}

=== CONTEXT FROM PAST INTERACTIONS & POLICIES ===
{rag_context}

Please provide:
1. **Risk Summary**: Why is this customer classified in this segment?
2. **Key Concerns**: What specific factors are worrying?
3. **Strategy Rationale**: Why is this the recommended action?
4. **Suggested Approach**: How should the collection agent handle this customer?
5. **Expected Outcome**: What is the likely result of following this strategy?
"""


CONVERSATION_SUMMARY_PROMPT = """Summarize the following customer interaction in 1-2 concise sentences.
Focus on: what the customer said, any commitments made, and the outcome.

Interaction:
Type: {interaction_type}
Date: {interaction_time}
Outcome: {interaction_outcome}
Transcript: {conversation_text}

Provide a brief professional summary:"""


MULTILINGUAL_RESPONSE_PROMPT = """You are a multilingual banking assistant.
Translate the following response to {target_language}.
Maintain a professional, empathetic banking tone.
Keep the meaning exactly the same.

English Response:
{english_response}

{target_language} Translation:"""


STRATEGY_DETAIL_PROMPT = """Based on the following data, provide a detailed 
recovery strategy explanation.

Customer Segment: {customer_segment}
Recommended Action: {recommended_action}
Self-Cure Probability: {self_cure_probability:.0%}
Days Past Due: {days_past_due}
Outstanding Balance: ₹{outstanding_balance:,.0f}

Relevant Policies:
{policy_context}

Provide:
1. Step-by-step action plan for the collection agent
2. Key talking points for customer communication
3. Escalation triggers (when to move to next level)
4. Compliance reminders (what NOT to do)
"""