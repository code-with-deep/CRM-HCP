"""Quick SSE stream smoke test."""

import json
import httpx

USER = "00000000-0000-0000-0000-000000000001"
HEADERS = {"X-User-Id": USER, "Content-Type": "application/json"}


def main() -> None:
    draft: dict = {}
    conv: str | None = None
    with httpx.Client(base_url="http://localhost:8000", timeout=60.0) as client:
        for message in [
            "I met Dr Sharma today to discuss CardioMax efficacy. Sentiment was positive.",
            "Shared CardioMax brochure and 2 sample packs.",
            "Change follow-up to Friday.",
        ]:
            response = client.post(
                "/chat/stream",
                json={
                    "message": message,
                    "user_id": USER,
                    "conversation_id": conv,
                    "current_interaction": draft,
                },
                headers=HEADERS,
            )
            response.raise_for_status()
            for part in response.text.split("\n\n"):
                if "event: complete" not in part:
                    continue
                for line in part.split("\n"):
                    if line.startswith("data:"):
                        payload = json.loads(line[5:])
                        resp = payload.get("response", {})
                        conv = resp.get("conversation_id", conv)
                        draft = resp.get("interaction_draft", draft)
                        print(
                            f"stream ok | tool={resp.get('selected_tool')} "
                            f"| hcp={draft.get('hcp_name')} "
                            f"| msg={message[:50]}"
                        )
    print("SSE stream demo flow: PASS")


if __name__ == "__main__":
    main()
