import time


class MockBedrockClient:

    # =========================================================
    # MOCK CONVERSE API
    # =========================================================

    def converse(
        self,
        modelId,
        system,
        messages,
        inferenceConfig
    ):
        start_time = time.time()

        # Get the user's message
        query = messages[0]["content"][0]["text"]

        model_id_lower = modelId.lower()

        if "haiku" in model_id_lower:
            model_name = "Claude Haiku"
        elif "sonnet" in model_id_lower:
            model_name = "Claude Sonnet"
        else:
            model_name = "Mock Bedrock Model"

        # Detect whether this is a RAG request
        is_rag_request = "Context:" in query

        if is_rag_request:

            # Extract the context and question
            if "Question:" in query:
                context, question = query.split(
                    "Question:",
                    1
                )
            else:
                context = query
                question = query

            # Simulated grounded response
            response_text = f"""
[MOCK RAG RESPONSE — {model_name}]

Question:
{question.strip()}

Based on the retrieved knowledge base context:

The relevant company policy information is contained in
the retrieved source documents shown above.

This answer is grounded in the retrieved context rather
than using the model's general knowledge.

Source citation:
The answer is based on the source document(s) retrieved
from the local mock knowledge base.

[MOCK MODE — AWS Bedrock is not being used]
"""

        else:

            # Normal non-RAG response
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

        input_tokens = len(query.split()) + 30
        output_tokens = len(response_text.split())

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
            "_mock": True,
            "_latency": latency
        }


    # =========================================================
    # MOCK COUNT TOKENS API
    # =========================================================

    def count_tokens(self, modelId, input):
        """
        Simulate Amazon Bedrock CountTokens API.
        """

        total_tokens = 0

        converse_input = input.get(
            "converse",
            {}
        )

        # Count system prompt
        system_messages = converse_input.get(
            "system",
            []
        )

        for system_message in system_messages:
            text = system_message.get(
                "text",
                ""
            )

            total_tokens += len(
                text.split()
            )

        # Count messages
        messages = converse_input.get(
            "messages",
            []
        )

        for message in messages:

            content = message.get(
                "content",
                []
            )

            for content_item in content:

                text = content_item.get(
                    "text",
                    ""
                )

                total_tokens += len(
                    text.split()
                )

        # Small overhead
        total_tokens += 5

        return {
            "inputTokens": total_tokens,
            "_mock": True,
            "_modelId": modelId
        }


    # =========================================================
    # MOCK KNOWLEDGE BASE RETRIEVAL
    # =========================================================

    def retrieve(
        self,
        knowledgeBaseId,
        retrievalQuery
    ):
        """
        Simulate Amazon Bedrock Knowledge Base retrieval.

        Instead of querying an AWS Knowledge Base,
        we search a small local set of company-policy
        documents.
        """

        query = retrievalQuery.get(
            "text",
            ""
        ).lower()

        documents = [

            {
                "filename": "laptop_replacement_policy.txt",
                "content": """
Laptop Replacement Policy

Employees may request a replacement laptop when their
current device is damaged, defective, or more than four
years old.

To request a replacement, employees should create an IT
Service Desk ticket and select the category Hardware >
Laptop Replacement.

The IT Service Desk will review the request and confirm
whether the device qualifies for replacement.
"""
            },

            {
                "filename": "work_from_home_policy.txt",
                "content": """
Work From Home Policy

Employees are allowed to work from home up to three days
per week, subject to manager approval and business
requirements.

Employees should coordinate their work-from-home schedule
with their manager and maintain availability during normal
working hours.
"""
            },

            {
                "filename": "production_access_policy.txt",
                "content": """
Production Environment Access Policy

Access to the production environment requires manager
approval and a valid business justification.

Employees must submit a production-access request through
the IT Service Desk.

The security team reviews the request before production
access is granted.

Production credentials must not be shared with other users.
"""
            }
        ]

        results = []

        # Simple keyword-based retrieval
        for document in documents:

            document_text = (
                document["filename"]
                + " "
                + document["content"]
            ).lower()

            query_words = set(
                query.split()
            )

            document_words = set(
                document_text.split()
            )

            overlap = query_words.intersection(
                document_words
            )

            score = len(overlap)

            if score > 0:

                results.append(
                    {
                        "score": min(
                            0.99,
                            0.50 + (score * 0.05)
                        ),
                        "location": {
                            "s3Location": {
                                "uri": (
                                    "s3://mock-knowledge-base/"
                                    + document["filename"]
                                )
                            }
                        },
                        "content": {
                            "text": document["content"].strip()
                        }
                    }
                )

        # Sort most relevant first
        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # Return at most 3 chunks
        results = results[:3]

        return {
            "retrievalResults": results,
            "_mock": True
        }
