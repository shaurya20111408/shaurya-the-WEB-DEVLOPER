import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_ai_answer(query: str, results: list[dict]) -> str:
    """
    Top results ka content leke ek chhota, sources ke saath jawab banata hai.
    Agar pakka na ho, toh "pata nahi" jaisa jawab dega.
    """
    if not results:
        return ""

    context_parts = []
    for i, r in enumerate(results[:5], start=1):
        context_parts.append(
            f"[Source {i}] {r['title']}\nURL: {r['url']}\n{r.get('snippet', '')}"
        )
    context = "\n\n".join(context_parts)

    prompt = f"""Neeche diye gaye search results ke aadhar par, is query ka chhota jawab do: "{query}"

Search results:
{context}

Rules:
- Sirf diye gaye sources ke content ka use karo, apni taraf se kuch mat jodo.
- Jawab 3-4 lines se zyada lamba na ho.
- Jawab ke end mein [Source 1], [Source 2] jaise reference do jahan se info li.
- Agar sources mein pakka jawab nahi milta, toh seedha likho "Pata nahi — sources mein ispe clear info nahi hai."
- User ki koi pehchaan is prompt mein nahi hai, aage bhi mat socho.
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        print(f"AI answer error: {e}")
        return ""