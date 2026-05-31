from openai import AsyncOpenAI
import os, json
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_feedback(feedbacks: list) -> dict:
    if len(feedbacks) == 0:
        raise ValueError("No feedback found in PDF")
    if len(feedbacks) > 50:
        raise ValueError("Max 50 feedbacks allowed")

    feedback_text = "\n".join([f"{f['fb_id']}: {f['comment']}" for f in feedbacks])

    prompt = f"""You analyze customer feedback. Return JSON only matching this schema:
{{
  "summary": "2-3 sentence overview",
  "overall_sentiment": "positive|neutral|mixed|negative",
  "themes": [{{"name": "theme", "evidence_ids": ["fb_001"]}}],
  "recommended_actions": ["action 1", "action 2"],
  "limitations": "brief note or null"
}}

Rules: 3-7 themes max. Each theme must cite at least 1 feedback ID from the input.

Feedbacks:
{feedback_text}"""

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    return json.loads(resp.choices[0].message.content)