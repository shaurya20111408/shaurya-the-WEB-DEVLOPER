import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def generate_ai_answer(query: str, results: list[dict]) -> str:
    """
    Top results ka content leke ek chhota, sources ke saath jawab banata hai.
    Local Ollama (llama3.2) use karta hai — koi data bahar nahi jata.
    """
    if not results:
        return ""

    context_parts = []
    for i, r in enumerate(results[:5], start=1):
        context_parts.append(
            f"[Source {i}] {r['title']}\nURL: {r['url']}\n{r.get('snippet', '')}"
        )
    context = "\n\n".join(context_parts)

    prompt = f"""Tum ek search assistant ho. Neeche diye gaye sources ke ALAWA tumhe kuch nahi pata — apni training ka koi extra knowledge use mat karo, chahe wo sahi hi kyun na ho.

Query: "{query}"

Sources:
{context}

Sakht Rules:
1. Jawab mein SIRF wahi facts likho jo upar ke sources mein shabd-sha shabd ya seedhe tarike se likhe hain.
2. Agar koi fact sources mein nahi hai, use mat likho — chahe wo sahi fact ho tumhare hisaab se.
3. Jawab 2-3 lines se zyada lamba na ho.
4. Har fact ke baad [Source N] likho jahan se wo liya.
5. Agar sources mein query ka seedha jawab nahi milta, sirf itna likho: "Sources mein ispe clear jawab nahi mila."
6. Koi introduction, koi "yahan hai jawab" jaisi line mat likho — seedha jawab se shuru karo.

"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.RequestException as e:
        print(f"AI answer error: {e}")
        return ""