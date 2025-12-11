from pydantic_ai import Agent
from backend.data_models import RagResponse
from backend.constants import VECTOR_DATABASE_PATH
from frontend.app import clean_text
import lancedb

# stores past interactions
conversation_memory = [] 

vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)


# connects to LanceDB, retrieves top documents, and generates answers based strictly on transcripts.
rag_agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    retries=2,
    system_prompt=(
        "You are a quirky and fun YouTuber who is an expert in Data Engineering and tech.",
        "Answer questions like a pedagogical teacher but add humor and fun facts.",
        "Always base your answers strictly on the retrieved transcript content.",
        "If the question is outside the transcripts, say 'I'm not sure' and optionally include a fun fact.",
        "Always mention the transcript title your answer comes from. NEVER include file paths or system locations.",
        "Keep answers concise, clear, and in your fun teaching style, max 6 sentences."
    ),
    output_type=RagResponse,
)


# Queries local LanceDB db, returns top k transcripts as string 
@rag_agent.tool_plain
def retrieve_top_documents(query: str, k: int = 3) -> str:
    results = vector_db["articles"].search(query=query).limit(k).to_list()
    if not results:
        return "No relevant transcripts found."

    return "\n\n".join(
        f"Transcript title: {r['filename']}\n{clean_text(r['content'])}"
        for r in results
    )


# summary of transcript with LLM assistance
def get_video_summary(filename: str) -> str:
    results = vector_db["articles"].search(query=filename).limit(1).to_list()
    if not results:
        return "No transcript found to summarize."

    content = results[0]["content"]

    try:
        # Use LLM to generate a concise summary
        prompt = f"""
        Summarize this YouTube transcript in 2-3 sentences, 
        keeping it clear and informative. Only return the summary.

        Transcript:
        {content}
        """
        response = rag_agent.run(prompt)
        summary = response.output.answer.strip()

    # simple fallback if LLM fails. Show first 3 lines as a simple summary using an existing function that cleans text
    except Exception:
        lines = content.splitlines()
        summary = " ".join(lines[:3])  
    return clean_text(summary) 



# extract keywords from transcript with LLM assistance
def get_video_keywords(filename: str, max_keywords: int = 30) -> str:
    results = vector_db["articles"].search(query=filename).limit(1).to_list()
    if not results:
        return ""

    # Clean transcript first
    content = clean_text(results[0]["content"])

    try:
        prompt = f"""
        Extract {max_keywords} concise and relevant keywords from this cleaned YouTube transcript.
        Ignore filler words like 'this', 'where', 'we'll', 'into', 'some', etc.
        Output only comma-separated words, no explanations.

        Transcript:
        {content}
        """
        response = rag_agent.run(prompt)
        keywords = response.output.answer
        # Remove duplicates and extra spaces
        keywords = ",".join(dict.fromkeys([kw.strip() for kw in keywords.split(",") if kw.strip()]))
        return keywords
    except Exception:
        # fallback: simple word extraction
        words = [w.lower().strip(".,!?()[]{}") for w in content.split()]
        keywords = list(dict.fromkeys([w for w in words if len(w) > 3]))
        return ",".join(keywords[:max_keywords])



def save_to_memory(user_prompt: str, bot_answer: str):
    conversation_memory.append((user_prompt, bot_answer))


