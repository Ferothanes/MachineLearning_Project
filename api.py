from fastapi import FastAPI
from backend.rag import rag_agent, save_to_memory, conversation_memory, get_video_summary, get_video_keywords
from backend.data_models import Prompt

app = FastAPI()


@app.get("/")
async def test():
    return {"test": "hello"}


# Endpoint calls rag_agent(prompt) to get answer
@app.post("/rag/query")
async def query_documentation(query: Prompt):
    result = await rag_agent.run(query.prompt)

    save_to_memory(query.prompt, result.output.answer)

    filename = result.output.filename or query.prompt
    youtube_title = filename.removesuffix(".md")

    summary = get_video_summary(filename)
    keywords = get_video_keywords(filename)

    full_answer = f"{result.output.answer}\n\nYouTube title: {youtube_title}"

    return {
        "answer": full_answer,
        "summary": summary,
        "keywords": keywords
    }


# # Endpoint for summeries
# @app.post("/video/summary")
# async def video_summary(query: Prompt):
#     filename = query.prompt
#     summary = get_video_summary(filename)
#     return {"summary": summary}


# # Endpoitnt for extracting keywords
# @app.post("/video/keywords")
# async def video_keywords(query: Prompt):
#     filename = query.prompt
#     keywords = get_video_keywords(filename)
#     return {"keywords": keywords}


@app.get("/history")
async def get_history():
    return [{"user": q, "bot": a} for q, a in conversation_memory]
