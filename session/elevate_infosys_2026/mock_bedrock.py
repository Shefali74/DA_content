import time


class MockBedrockClient:

    def converse(
        self,
        modelId,
        system,
        messages,
        inferenceConfig
    ):
        start_time = time.time()

        # Get the user's question
        query = messages[0]["content"][0]["text"]

        # Identify which model is being simulated
        model_id_lower = modelId.lower()

        if "haiku" in model_id_lower:
            model_name = "Claude Haiku"
        elif "sonnet" in model_id_lower:
            model_name = "Claude Sonnet"
        else:
            model_name = "Mock Bedrock Model"

        # Simulated response
        response_text = f"""
[MOCK RESPONSE — {model_name}]

User query:
"{query}"

Helpdesk response:

This is a simulated Amazon Bedrock response.

For this IT helpdesk request, you should:

1. Check the user's network connection.
2. Restart the affected application or service.
3. Verify that the required configuration is correct.
4. Check whether there are any known system issues.
5. If the problem continues, escalate the issue to the IT support team.

This response is being generated in MOCK MODE because
AWS Bedrock credentials are not configured.
"""

        # Simulate token usage
        input_tokens = len(query.split()) + 30
        output_tokens = len(response_text.split())

        # Simulate a small amount of processing time
        latency = time.time() - start_time

        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": response_text.strip()
                        }
                    ]
                }
            },
            "usage": {
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "totalTokens": input_tokens + output_tokens
            },
            "stopReason": "end_turn",

            # Extra information that can be useful for our demo
            "_mock": True,
            "_latency": latency
        }
