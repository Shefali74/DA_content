"""
Mock Amazon Bedrock client for local development.

This file allows the project demos to run WITHOUT an AWS account.

Supported simulated APIs:
    - Converse API
    - CountTokens API
    - Knowledge Base Retrieve API
    - ApplyGuardrail API

IMPORTANT:
This is a teaching/demo implementation.
It does NOT reproduce the real Amazon Bedrock behavior exactly.
"""

import re
import time


class MockBedrockClient:

    def __init__(self):
        print("[MOCK BEDROCK] Using local mock client. No AWS calls will be made.")

    # =========================================================
    # CONVERSE API
    # =========================================================

    def converse(
        self,
        modelId,
        system=None,
        messages=None,
        inferenceConfig=None,
        guardrailConfig=None,
        **kwargs
    ):
        """
        Simulate the Amazon Bedrock Converse API.

        Supports:
            - normal model responses
            - Guardrail evaluation
            - token usage
            - stop reason
            - guardrail trace
        """

        start_time = time.time()

        system = system or []
        messages = messages or []
        inferenceConfig = inferenceConfig or {}

        # -----------------------------------------------------
        # Extract user message
        # -----------------------------------------------------

        user_text = ""

        if messages:
            last_message = messages[-1]

            content = last_message.get("content", [])

            if content:
                user_text = content[0].get("text", "")

        # -----------------------------------------------------
        # Extract system prompt
        # -----------------------------------------------------

        system_text = ""

        if system:
            system_text = " ".join(
                item.get("text", "")
                for item in system
            )

        # -----------------------------------------------------
        # Guardrail processing
        # -----------------------------------------------------

        guardrail_trace = {}

        if guardrailConfig:

            guardrail_result = self.apply_guardrail(
                guardrailIdentifier=guardrailConfig.get(
                    "guardrailIdentifier",
                    "mock-guardrail"
                ),
                guardrailVersion=guardrailConfig.get(
                    "guardrailVersion",
                    "1"
                ),
                source="INPUT",
                content=[
                    {
                        "text": {
                            "text": user_text
                        }
                    }
                ]
            )

            guardrail_trace = {
                "inputAssessment": guardrail_result.get(
                    "assessments",
                    []
                )
            }

            # -------------------------------------------------
            # Guardrail BLOCK
            # -------------------------------------------------

            if guardrail_result["action"] == "GUARDRAIL_INTERVENED":

                blocked_response = guardrail_result["outputs"][0]["text"]

                latency_ms = int(
                    (time.time() - start_time) * 1000
                )

                return {
                    "output": {
                        "message": {
                            "content": [
                                {
                                    "text": blocked_response
                                }
                            ]
                        }
                    },

                    "usage": {
                        "inputTokens": self._estimate_tokens(user_text),
                        "outputTokens": self._estimate_tokens(
                            blocked_response
                        )
                    },

                    "stopReason": "guardrail_intervened",

                    "trace": {
                        "guardrail": guardrail_trace
                    },

                    "_mock": True,
                    "_latency_ms": latency_ms
                }

        # -----------------------------------------------------
        # Generate normal mock response
        # -----------------------------------------------------

        response_text = self._generate_mock_response(
            modelId=modelId,
            user_text=user_text,
            system_text=system_text
        )

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": response_text
                        }
                    ]
                }
            },

            "usage": {
                "inputTokens": self._estimate_tokens(
                    user_text + system_text
                ),
                "outputTokens": self._estimate_tokens(
                    response_text
                )
            },

            "stopReason": "end_turn",

            "trace": {
                "guardrail": guardrail_trace
            },

            "_mock": True,
            "_latency_ms": latency_ms
        }

    # =========================================================
    # MOCK MODEL RESPONSE
    # =========================================================

    def _generate_mock_response(
        self,
        modelId,
        user_text,
        system_text=""
    ):
        """
        Generate a deterministic response for the demos.

        This is NOT an actual LLM.
        """

        model_name = self._get_model_name(modelId)

        # -----------------------------------------------------
        # RAG / Knowledge Base context
        # -----------------------------------------------------

        if "Context:" in user_text:

            return self._generate_rag_response(
                user_text,
                model_name
            )

        # -----------------------------------------------------
        # Normal IT helpdesk response
        # -----------------------------------------------------

        return (
            f"[MOCK RESPONSE — {model_name}]\n\n"
            f"User query:\n"
            f"\"{user_text}\"\n\n"
            "Helpdesk response:\n\n"
            "This is a simulated Amazon Bedrock response.\n\n"
            "For this IT helpdesk request, you should:\n\n"
            "1. Check the user's network connection.\n"
            "2. Restart the affected application or service.\n"
            "3. Verify that the required configuration is correct.\n"
            "4. Check whether there are any known system issues.\n"
            "5. If the problem continues, escalate the issue "
            "to the IT support team.\n\n"
            "This response is being generated in MOCK MODE "
            "because AWS Bedrock credentials are not configured."
        )

    # =========================================================
    # MOCK RAG RESPONSE
    # =========================================================

    def _generate_rag_response(
        self,
        user_text,
        model_name
    ):
        """
        Generate a deterministic answer from the retrieved
        Knowledge Base context.

        This makes Demo 03 more realistic without requiring
        an actual LLM.
        """

        lower_text = user_text.lower()

        # -----------------------------------------------------
        # Laptop replacement
        # -----------------------------------------------------

        if "laptop_replacement_policy.txt" in lower_text:

            if (
                "replacement" in lower_text
                or "laptop" in lower_text
            ):

                return (
                    f"[MOCK RAG RESPONSE — {model_name}]\n\n"
                    "Employees may request a replacement laptop "
                    "when their current device is damaged, defective, "
                    "or more than four years old.\n\n"
                    "To request a replacement, create an IT Service "
                    "Desk ticket and select:\n\n"
                    "Hardware > Laptop Replacement\n\n"
                    "The IT Service Desk will review the request.\n\n"
                    "Source: laptop_replacement_policy.txt"
                )

        # -----------------------------------------------------
        # Work from home
        # -----------------------------------------------------

        if "work_from_home_policy.txt" in lower_text:

            if (
                "work from home" in lower_text
                or "wfh" in lower_text
                or "days" in lower_text
            ):

                return (
                    f"[MOCK RAG RESPONSE — {model_name}]\n\n"
                    "Employees are allowed to work from home "
                    "up to three days per week, subject to manager "
                    "approval and business requirements.\n\n"
                    "Employees should coordinate their WFH schedule "
                    "with their manager and remain available during "
                    "normal working hours.\n\n"
                    "Source: work_from_home_policy.txt"
                )

        # -----------------------------------------------------
        # Production access
        # -----------------------------------------------------

        if "production_access_policy.txt" in lower_text:

            if (
                "production" in lower_text
                or "access" in lower_text
            ):

                return (
                    f"[MOCK RAG RESPONSE — {model_name}]\n\n"
                    "Access to the production environment requires "
                    "manager approval and a valid business justification.\n\n"
                    "Employees must submit a production-access request "
                    "through the IT Service Desk.\n\n"
                    "The security team reviews the request before "
                    "access is granted.\n\n"
                    "Production credentials must not be shared.\n\n"
                    "Source: production_access_policy.txt"
                )

        # -----------------------------------------------------
        # No matching information
        # -----------------------------------------------------

        return (
            f"[MOCK RAG RESPONSE — {model_name}]\n\n"
            "I don't have information about that in our "
            "knowledge base."
        )

    # =========================================================
    # COUNT TOKENS API
    # =========================================================

    def count_tokens(
        self,
        modelId,
        input
    ):
        """
        Simulate Amazon Bedrock CountTokens API.

        This is only an approximation.

        Real Bedrock uses the model's tokenizer.
        Our mock uses word counting.
        """

        total_tokens = 0

        converse_input = input.get(
            "converse",
            {}
        )

        # -----------------------------------------------------
        # System prompt
        # -----------------------------------------------------

        system_messages = converse_input.get(
            "system",
            []
        )

        for system_message in system_messages:

            text = system_message.get(
                "text",
                ""
            )

            total_tokens += self._estimate_tokens(
                text
            )

        # -----------------------------------------------------
        # Messages
        # -----------------------------------------------------

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

                total_tokens += self._estimate_tokens(
                    text
                )

        return {
            "inputTokens": total_tokens,
            "_mock": True,
            "_modelId": modelId
        }

    # =========================================================
    # KNOWLEDGE BASE RETRIEVE API
    # =========================================================

    def retrieve(
        self,
        knowledgeBaseId,
        retrievalQuery
    ):
        """
        Simulate Bedrock Knowledge Base Retrieve API.

        Uses simple keyword matching instead of embeddings.
        """

        query = retrievalQuery.get(
            "text",
            ""
        )

        query_lower = query.lower()

        # -----------------------------------------------------
        # Mock company documents
        # -----------------------------------------------------

        documents = [

            {
                "filename": "laptop_replacement_policy.txt",

                "content": (
                    "Employees may request a replacement laptop "
                    "when their current device is damaged, defective, "
                    "or more than four years old.\n\n"
                    "To request a replacement, employees should create "
                    "an IT Service Desk ticket and select:\n\n"
                    "Hardware > Laptop Replacement\n\n"
                    "The IT Service Desk reviews the request."
                ),

                "keywords": [
                    "laptop",
                    "replacement",
                    "device",
                    "hardware",
                    "damaged",
                    "defective"
                ]
            },

            {
                "filename": "work_from_home_policy.txt",

                "content": (
                    "Employees are allowed to work from home up to "
                    "three days per week, subject to manager approval "
                    "and business requirements.\n\n"
                    "Employees should coordinate their WFH schedule "
                    "with their manager and remain available during "
                    "normal working hours."
                ),

                "keywords": [
                    "work",
                    "home",
                    "wfh",
                    "remote",
                    "days",
                    "manager"
                ]
            },

            {
                "filename": "production_access_policy.txt",

                "content": (
                    "Access to the production environment requires "
                    "manager approval and a valid business justification.\n\n"
                    "Employees must submit a production-access request "
                    "through the IT Service Desk.\n\n"
                    "The security team reviews the request before "
                    "access is granted.\n\n"
                    "Production credentials must not be shared."
                ),

                "keywords": [
                    "production",
                    "access",
                    "security",
                    "environment",
                    "credentials",
                    "approval"
                ]
            }
        ]

        # -----------------------------------------------------
        # Score documents
        # -----------------------------------------------------

        query_words = set(
            re.findall(
                r"\b[a-zA-Z]+\b",
                query_lower
            )
        )

        scored_documents = []

        for document in documents:

            document_keywords = set(
                document["keywords"]
            )

            matches = query_words.intersection(
                document_keywords
            )

            score = len(matches)

            if score > 0:

                scored_documents.append(
                    (
                        score,
                        document
                    )
                )

        # Highest score first
        scored_documents.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # -----------------------------------------------------
        # Convert to Bedrock-like response
        # -----------------------------------------------------

        retrieval_results = []

        for score, document in scored_documents[:3]:

            # Simple normalized score
            relevance_score = min(
                0.95,
                0.5 + (score * 0.1)
            )

            retrieval_results.append(
                {
                    "score": relevance_score,

                    "content": {
                        "text": document["content"]
                    },

                    "location": {
                        "s3Location": {
                            "uri": (
                                "s3://mock-knowledge-base/"
                                + document["filename"]
                            )
                        }
                    }
                }
            )

        return {
            "retrievalResults": retrieval_results,
            "_mock": True,
            "_knowledgeBaseId": knowledgeBaseId
        }

    # =========================================================
    # APPLY GUARDRAIL API
    # =========================================================

    def apply_guardrail(
        self,
        guardrailIdentifier,
        guardrailVersion,
        source,
        content
    ):
        """
        Simulate Amazon Bedrock ApplyGuardrail API.

        Checks:
            - PII
            - Prompt injection
            - Denied topics
            - Competitor mentions

        PII is masked.
        Other restricted content is blocked.
        """

        text = content[0]["text"]["text"]

        original_text = text
        output_text = text

        action = "NONE"

        assessments = []

        # =====================================================
        # 1. EMAIL
        # =====================================================

        email_pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )

        if re.search(
            email_pattern,
            output_text
        ):

            output_text = re.sub(
                email_pattern,
                "[EMAIL_REDACTED]",
                output_text
            )

            assessments.append(
                {
                    "type": "PII",
                    "category": "EMAIL",
                    "action": "ANONYMIZED"
                }
            )

            action = "ANONYMIZED"

        # =====================================================
        # 2. PHONE NUMBER
        # =====================================================

        phone_pattern = (
            r"\+?\d[\d\s\-()]{7,}\d"
        )

        if re.search(
            phone_pattern,
            output_text
        ):

            output_text = re.sub(
                phone_pattern,
                "[PHONE_REDACTED]",
                output_text
            )

            assessments.append(
                {
                    "type": "PII",
                    "category": "PHONE",
                    "action": "ANONYMIZED"
                }
            )

            action = "ANONYMIZED"

        # =====================================================
        # 3. SSN
        # =====================================================

        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"

        if re.search(
            ssn_pattern,
            output_text
        ):

            output_text = re.sub(
                ssn_pattern,
                "[SSN_REDACTED]",
                output_text
            )

            assessments.append(
                {
                    "type": "PII",
                    "category": "SSN",
                    "action": "ANONYMIZED"
                }
            )

            action = "ANONYMIZED"

        # =====================================================
        # 4. CREDIT CARD
        # =====================================================

        card_pattern = (
            r"\b(?:\d[ -]*?){13,19}\b"
        )

        if re.search(
            card_pattern,
            output_text
        ):

            output_text = re.sub(
                card_pattern,
                "[CARD_REDACTED]",
                output_text
            )

            assessments.append(
                {
                    "type": "PII",
                    "category": "CREDIT_CARD",
                    "action": "ANONYMIZED"
                }
            )

            action = "ANONYMIZED"

        # =====================================================
        # 5. EMPLOYEE / BADGE ID
        # =====================================================

        employee_id_pattern = (
            r"\b(?:EMP|BADGE)-?\d+\b"
        )

        if re.search(
            employee_id_pattern,
            output_text,
            re.IGNORECASE
        ):

            output_text = re.sub(
                employee_id_pattern,
                "[EMPLOYEE_ID_REDACTED]",
                output_text,
                flags=re.IGNORECASE
            )

            assessments.append(
                {
                    "type": "PII",
                    "category": "EMPLOYEE_ID",
                    "action": "ANONYMIZED"
                }
            )

            action = "ANONYMIZED"

        # =====================================================
        # 6. PROMPT INJECTION
        # =====================================================

        injection_patterns = [
            "ignore all previous instructions",
            "ignore previous instructions",
            "disregard previous instructions",
            "you are now",
            "reveal your instructions",
            "reveal the system prompt",
            "system prompt",
            "jailbreak",
            "admin password",
            "production database password"
        ]

        lower_text = text.lower()

        injection_found = any(
            pattern in lower_text
            for pattern in injection_patterns
        )

        if injection_found:

            assessments.append(
                {
                    "type": "PROMPT_INJECTION",
                    "action": "BLOCKED"
                }
            )

            action = "GUARDRAIL_INTERVENED"

            output_text = (
                "I can't help with that request because it "
                "violates the application's security policy."
            )

        # =====================================================
        # 7. DENIED TOPICS
        # =====================================================

        denied_topics = [
            "manager's salary",
            "manager salary",
            "salary information",
            "compensation data",
            "confidential salary",
            "employee compensation"
        ]

        denied_found = any(
            topic in lower_text
            for topic in denied_topics
        )

        if denied_found:

            assessments.append(
                {
                    "type": "DENIED_TOPIC",
                    "category": "SALARY",
                    "action": "BLOCKED"
                }
            )

            action = "GUARDRAIL_INTERVENED"

            output_text = (
                "I can't provide confidential compensation "
                "information."
            )

        # =====================================================
        # 8. COMPETITOR MENTIONS
        # =====================================================

        competitors = [
            "servicenow"
        ]

        competitor_found = any(
            competitor in lower_text
            for competitor in competitors
        )

        if competitor_found:

            assessments.append(
                {
                    "type": "COMPETITOR",
                    "category": "RESTRICTED_VENDOR",
                    "action": "BLOCKED"
                }
            )

            action = "GUARDRAIL_INTERVENED"

            output_text = (
                "I can't assist with requests involving "
                "restricted competitor information."
            )

        # =====================================================
        # Return Bedrock-like response
        # =====================================================

        return {
            "action": action,

            "outputs": [
                {
                    "text": output_text
                }
            ],

            "assessments": assessments,

            "usage": {
                "guardrailProcessingLatency": 0
            },

            "_mock": True,

            "_original_text": original_text,

            "_source": source,

            "_guardrailIdentifier": guardrailIdentifier,

            "_guardrailVersion": guardrailVersion
        }

    # =========================================================
    # HELPER METHODS
    # =========================================================

    @staticmethod
    def _estimate_tokens(text):
        """
        Very simple token approximation.

        Real LLM tokenization is NOT the same as word count.
        """

        if not text:
            return 0

        return len(text.split())

    @staticmethod
    def _get_model_name(model_id):
        """
        Convert model ID into a readable mock model name.
        """

        model_id_lower = model_id.lower()

        if "haiku" in model_id_lower:
            return "Claude Haiku"

        if "sonnet" in model_id_lower:
            return "Claude Sonnet"

        return "Mock Bedrock Model"
