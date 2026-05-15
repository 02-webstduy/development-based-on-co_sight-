from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import json
from transformers import AutoTokenizer

UPSTREAM = "http://127.0.0.1:8000"
MODEL_PATH = "/mnt/e/study/Qwen2.5"

app = FastAPI()
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

def count_message_tokens(messages):
    try:
        ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True
        )
        return len(ids)
    except Exception as e:
        return f"count_failed: {e}"

def count_text_tokens(text):
    try:
        return len(tokenizer(text, add_special_tokens=False)["input_ids"])
    except Exception as e:
        return f"count_failed: {e}"

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    body_bytes = await request.body()
    headers = dict(request.headers)

    if request.method == "POST":
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
            messages = payload.get("messages", [])
            tools = payload.get("tools", [])

            msg_tokens = count_message_tokens(messages) if messages else 0
            tool_tokens = count_text_tokens(json.dumps(tools, ensure_ascii=False, separators=(",", ":"))) if tools else 0

            print("\n" + "=" * 80)
            print(f"[PATH] /v1/{path}")
            print(f"[MODEL] {payload.get('model')}")
            print(f"[MSG_COUNT] {len(messages)}")
            print(f"[TOOL_COUNT] {len(tools)}")
            print(f"[TOKENS] messages≈{msg_tokens}, tools≈{tool_tokens}")

            for i, m in enumerate(messages):
                content = m.get("content", "")
                if isinstance(content, str):
                    print(f"[MSG {i}] role={m.get('role')} chars={len(content)}")
                else:
                    print(f"[MSG {i}] role={m.get('role')} content_type={type(content)}")

            for i, t in enumerate(tools):
                fn = t.get("function", {})
                print(f"[TOOL {i}] name={fn.get('name')} desc_chars={len(fn.get('description', ''))}")

            print("=" * 80 + "\n")
        except Exception as e:
            print(f"[PROXY_LOG_ERROR] {e}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        upstream_resp = await client.request(
            request.method,
            f"{UPSTREAM}/v1/{path}",
            headers={k: v for k, v in headers.items() if k.lower() != "host"},
            content=body_bytes
        )

    return JSONResponse(
        status_code=upstream_resp.status_code,
        content=upstream_resp.json()
    )