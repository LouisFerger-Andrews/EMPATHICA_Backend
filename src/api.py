import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, PlainTextResponse

# import your existing function
from src.core.rag_controller import rag_inference   # adjust path if different

app = FastAPI()

@app.get("/health")
def health():
    return PlainTextResponse("ok")

async def run_rag_async(prompt: str):
    # rag_inference is sync -> offload to thread pool
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, rag_inference, prompt)

@app.post("/ask")
async def ask(req: Request):
    payload = await req.json()
    prompt = payload.get("prompt", "")

    task = asyncio.create_task(run_rag_async(prompt))

    async def streamer():
        # send something immediately
        yield "starting...\n"
        tick = 0
        while not task.done():
            await asyncio.sleep(10)
            tick += 1
            # keep-alive byte(s)
            yield f"--- keepalive {tick} ---\n"

        # task finished
        try:
            result = task.result()
        except Exception as e:
            yield f"ERROR: {repr(e)}\n"
            return

        # normalize result
        if isinstance(result, (dict, list)):
            yield json.dumps(result, ensure_ascii=False) + "\n"
        else:
            yield str(result) + "\n"

    return StreamingResponse(streamer(), media_type="text/plain")
