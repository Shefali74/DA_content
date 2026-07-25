# Speaker Notes

## When AI Becomes Your On-Call Engineer
### Devnovate AWS Mumbai Meetup | 45 minutes | Mixed audience (students + professionals)

---

## Slide 1: Title - "When AI Becomes Your On-Call Engineer"

*[Walk to center stage. Pause. Make eye contact with the audience.]*

Alright Mumbai, good evening. Before I start, let me ask you something.

How many of you have been woken up at 3 AM by a PagerDuty alert or a phone call from your team saying something is broken in production?

*[Raise your own hand. Wait for audience hands.]*

Yeah. That feeling of dread when your phone lights up in the dark. You know it. I know it. I have lived it more times than I would like to admit.

My name is Jatin Mehrotra. I am a Developer Advocate at AWS, and for the next 45 minutes, I am going to show you - live, on this stage - how we can make that 3 AM wake-up call a thing of the past.

Not by ignoring alerts. Not by turning off notifications. But by having AI do the job of the on-call engineer. Detect the problem. Diagnose the root cause. Apply the fix. And then - only then - send you a nice little notification in the morning saying "Hey, I fixed this for you while you slept."

Two live demos. Real clusters. Real incidents. Real AI fixing things. Let us go.

---

## Slide 2: About Me

*[Brief, keep moving.]*

Quick intro. I am Jatin, Developer Advocate at AWS in the DevEx APJC team. My journey has been DevOps and Platform Engineering for about 5 years - I worked with Japanese companies at Classmethod, got deep into Kubernetes, infrastructure automation, the whole nine yards.

Then I became an AWS Community Builder, started speaking at events, writing blogs, and eventually that turned into a full-time role as a Developer Advocate. My focus now is at the intersection of DevOps and GenAI - specifically, how can we use AI to make operations less painful.

Everything I show today - the code, the configurations, the demo scripts - will be on my GitHub. Link is at the end. Let us dive in.

---

## Slide 3: The 3 AM Problem

*[Slow down. Storytelling mode. Paint the picture.]*

Picture this. It is 3 AM. You are deep asleep. Your phone buzzes. You pick it up with one eye open. "ALERT: pod memory-hog OOMKilled in namespace production."

You drag yourself to your laptop. SSH into the bastion host. Start grepping through logs. Check CloudWatch metrics. Compare with recent deployments. Nothing obvious. You check resource limits. And there it is - the pod was given 64 megabytes of memory but it actually needs 128.

You increase the limit. Apply the change. Wait for the rollout. Verify the pod is healthy. 45 minutes have passed. You try to go back to sleep but your brain is wired now.

Here is the worst part - this exact same thing happened last month. Same pod. Same issue. Same fix. You even remember applying it.

*[Pause.]*

What if an AI could do this entire loop in 30 seconds? Detect the OOMKill, figure out the memory limit is too low, generate a new manifest with a higher limit, apply it, and verify the pod comes back healthy. All while you sleep.

That is exactly what I am going to show you today.

---

## Slide 4: Manual Operations Do Not Scale

*[Data slide. Speak with conviction. Point at each number.]*

Let me throw some data at you.

45 minutes. That is the average Mean Time To Resolution for common infrastructure issues. Not complex multi-service cascading failures. Common, everyday stuff. OOMKills. Misconfigured services. Missing ConfigMaps.

80 percent. Eight out of ten incidents that page you are patterns you have seen before. The same classes of problems, over and over and over.

60 percent. That is how much of an SRE's time goes to toil - repetitive, manual operational work - instead of building resilient systems, improving architecture, or shipping features.

This is not sustainable. This does not scale. And this is exactly the problem AI was born to solve. Not writing emails. Not generating images. Fixing infrastructure at 3 AM so humans can do higher-value work during the day.

---

## Slide 5: AI is Automating Operations

*[Transition slide. Set up the two-part structure.]*

So here is the big picture. AI is automating operations at every level of your stack. It does not matter if you are running a single Kubernetes cluster or managing a multi-account cloud environment with hundreds of services.

The pattern is the same. AI detects. AI diagnoses. AI fixes. Humans stay in the loop for oversight and policy - not for the grunt work.

Today I will show you both ends of this spectrum.

First - inside the cluster. K8sGPT. A CNCF open-source project that scans your Kubernetes cluster, detects issues, explains them in plain English, and auto-fixes them using large language models.

Second - across the cloud. AWS DevOps Agent. A frontier agent that investigates infrastructure incidents autonomously - correlating metrics, logs, code changes, and deployment history to identify root cause and generate mitigation plans.

Two tools. Same philosophy. Zero human in the loop for that first 80 percent.

---

## Slide 6: What is K8sGPT?

*[Technical introduction. Be specific.]*

K8sGPT. It is a CNCF open-source project - you can find it on GitHub right now, go star it after this talk.

What does it do? It scans your Kubernetes cluster continuously. Every 30 seconds, it looks for problems - pods that are crashing, services with no endpoints, deployments stuck at zero replicas, missing ConfigMaps, misconfigured ingresses.

When it finds something broken, it calls a large language model - Amazon Bedrock in our case, running Claude - and asks it to do two things. One, explain what went wrong in plain English that a human can understand. Two, generate a fixed YAML manifest.

It supports multiple LLM backends. Amazon Bedrock, OpenAI, even local models if you are running Ollama. For our demo today, we are using Bedrock with the Claude Sonnet model - zero API keys stored in the cluster, authentication via EKS Pod Identity.

The feature that makes this special is the Operator mode. You install it via Helm, it runs inside your cluster 24/7, and it has a feature called auto-remediation that can actually apply the fixes it generates. That is what we are about to see.

---

## Slide 7: Auto-Remediation Flow

*[Process explanation. Walk through each step. Keep it crisp.]*

Here is how auto-remediation works under the hood. Four steps.

Step one - Detect. The K8sGPT Operator scans your cluster every 30 seconds. It has built-in analyzers for Pods, Deployments, Services, Ingresses, ConfigMaps - all the common resource types. When it finds something unhealthy, it flags it.

Step two - Diagnose. It calls Amazon Bedrock with the broken resource's YAML and the error context. Bedrock returns two things: a human-readable explanation stored as a Result custom resource, and a fixed YAML manifest stored as a Mutation custom resource.

Step three - Patch. The operator compares the proposed fix against the original resource. It computes a similarity score - basically, how different is the fix from what we had before? If the score is above your configured threshold - we set ours at 40 percent - it applies the patch via the Kubernetes API.

Step four - Verify. After applying the patch, it watches. If the Result disappears - meaning the issue is gone - the fix worked. If the Result persists, something else is wrong and it flags for human review.

The whole cycle takes about 30 to 60 seconds. From OOMKill to running pod. No human involved.

---

## Slide 8: DEMO - K8sGPT Self-Healing

*[Energy shift. Stand up straighter. This is the exciting part.]*

Alright, demo time. Let me switch to my terminal.

*[Switch to terminal]*

I have an EKS cluster running in us-east-1. K8sGPT Operator is installed, talking to Amazon Bedrock. Kyverno is installed with a policy that blocks AI mutations in the critical namespace.

I am going to deploy a pod that is designed to fail. It requests 64 megabytes of memory but the process inside needs 128. It will OOMKill immediately.

*[Run: kubectl apply -f memory-hog.yaml]*

See? The pod is crashing. OOMKilled. Exit code 137. Classic.

Now watch. K8sGPT is scanning right now. In about 30 seconds, it will detect this, call Bedrock, generate a fix, and apply it.

*[Run: kubectl get results -n k8sgpt-operator-system -w]*

There it is. Result created. K8sGPT detected the issue. And... there is the Mutation. It generated a fix. Similarity score above threshold. Applying...

*[Run: kubectl get mutations -n k8sgpt-operator-system]*

Successful. The fix was applied. Let me verify.

*[Run: kubectl get pods -n demo]*

Running. The pod is healthy. K8sGPT increased the memory limit automatically. That took about 45 seconds. No human involved.

Now for the plot twist. I am going to deploy the exact same broken pod in the critical namespace.

*[Run: kubectl apply -f memory-hog-critical.yaml]*

K8sGPT will detect this issue too. It will generate the same fix. But when it tries to apply the patch... Kyverno is going to step in and say "No."

*[Wait 60-90 seconds, then run: kubectl get mutations -n k8sgpt-operator-system]*

See? The demo namespace mutations show "Successful". The critical namespace mutations are stuck at "In Progress". Kyverno is blocking the mutation.

*[Run: kubectl logs -n kyverno -l app.kubernetes.io/component=admission-controller --tail=5 | grep "blocking admission"]*

There. "Blocking admission request. Policy: block-ai-remediation-critical. Resource: critical/Deployment/memory-hog." The AI detected the issue, generated the fix, but the policy guardrail said "Not here. A human must review this."

That is the power of combining AI with policy-as-code. You get the speed of automation where it is safe, and human oversight where it matters.

---

## Slide 9: Policy Guardrails - Kyverno

*[Slow down slightly. This is the "responsible AI" message.]*

Let me talk about why this matters.

With great power comes great responsibility. You do not want AI auto-fixing your payment service in production at 3 AM without any human approval. That is how you get incidents caused by the fix instead of the original problem.

Kyverno solves this elegantly. It is a Kubernetes-native policy engine - an admission controller. It intercepts API requests before they are applied to the cluster.

We wrote one ClusterPolicy. The logic is simple: if the mutation request comes from the K8sGPT service account, AND the target namespace is labeled critical - deny the request.

One YAML file. Namespace-scoped. Zero code changes to K8sGPT itself. You now have two zones in your cluster: AI-managed zones where the agent can fix things freely, and human-managed zones where the agent can detect and report, but only humans can apply fixes.

This is the pattern I recommend for production. Start with AI auto-fix in dev and staging. Once you build confidence in the fixes it generates, gradually expand to non-critical production workloads. Keep your payment service, your authentication service, your database operators in the human-managed zone.

---

## Slide 10: What is AWS DevOps Agent?

*[Transition to Part 2. Fresh energy.]*

Now let us zoom out from Kubernetes. What about incidents that span your entire cloud infrastructure? A Lambda throwing errors. An RDS connection issue. A networking misconfiguration across VPCs.

This is where AWS DevOps Agent comes in. It is what I call a frontier agent - always on, always watching, always ready to investigate.

The moment an incident occurs - an alarm fires, a ticket is created, a webhook is received - the agent starts investigating. It does not wait for a human to triage. It does not wait for the on-call engineer to wake up and start checking dashboards.

It pulls data from every connected source. CloudWatch metrics. Application logs. Distributed traces. Deployment history from GitHub. Infrastructure changes from CloudTrail. It correlates all of this and identifies the root cause.

And then it generates a specific, actionable mitigation plan. Not vague advice like "check your logs." Specific steps: "The security group rule allowing port 3306 was deleted by user X at 2:47 AM. Run this CLI command to restore it."

It supports AWS, multi-cloud, and hybrid environments. It integrates with CloudWatch, Datadog, Splunk, PagerDuty, GitHub, Slack. It is not AWS-only.

---

## Slide 11: Investigation Pipeline

*[Technical walkthrough. Match the K8sGPT four-step pattern.]*

The investigation follows four stages. Similar pattern to K8sGPT, but at cloud scale.

Stage one - Triage. When an alarm fires, the agent checks: is this related to something I am already investigating? If yes, it links them together into a single investigation. No duplicate work. No alert fatigue from five related alarms creating five separate investigations.

Stage two - Investigate. It goes deep. Pulls metrics from your monitoring tools. Analyzes application logs. Follows distributed traces. Checks recent deployments and code changes. Looks at infrastructure mutations in CloudTrail. It is doing what an experienced SRE would do - but in parallel, across all data sources, in minutes instead of hours.

Stage three - Root Cause. This is the key output. Not "CPU is high." But WHY CPU is high. Was it a bad deployment? A memory leak in the new code? A traffic spike from a marketing campaign? A database connection leak? The agent traces the causal chain.

Stage four - Mitigate. It generates an actionable plan. Specific steps. CLI commands. Configuration changes. Code fixes that can be handed to a coding agent. The plan is ready for a human to review and execute - or in some cases, ready for another agent to implement directly.

---

## Slide 12: Event-Driven Demo Architecture

*[Architecture slide. Keep it simple. Three boxes, two arrows.]*

For our demo, I built a simple event-driven pipeline using CDK. Three components.

CloudWatch Alarm - watching a Lambda function for errors. When error count hits 3 in one minute, the alarm fires.

Lambda Function - the webhook bridge. It receives the alarm event via SNS, reads the DevOps Agent webhook credentials from Secrets Manager, signs the payload with HMAC SHA-256, and POSTs it to the DevOps Agent webhook endpoint.

DevOps Agent - receives the webhook, validates the signature, and starts an autonomous investigation. It will look at the Lambda function's error logs, check for recent deployments, analyze the error patterns, and produce a root cause analysis with mitigation steps.

The key point: zero human intervention from alarm to diagnosis. The alarm fires. The agent investigates. You wake up to a root cause and a fix, not a blinking red alert.

---

## Slide 13: DEMO - AWS DevOps Agent

*[Second demo. Same energy as first.]*

Alright, second demo. Let me show you this in action.

*[Switch to terminal]*

I have a Lambda function deployed that intentionally throws errors - simulating a database connection pool exhaustion. It always fails. I am going to invoke it 5 times. That will trigger the CloudWatch Alarm. The alarm will fire through SNS to our webhook Lambda. The webhook Lambda will call the DevOps Agent. And we will watch the investigation happen.

*[Run: ./trigger-alarm.sh]*

Five invocations done. Now we wait about a minute for CloudWatch to evaluate the alarm window.

*[Switch to browser - DevOps Agent web app]*

While we wait, let me show you the DevOps Agent web app. This is where investigations appear. Right now it is quiet.

*[Wait, narrate]*

The alarm should be transitioning to ALARM state now. SNS is notifying our Lambda. Lambda is signing the payload and calling the webhook...

*[Investigation appears]*

There it is. "CloudWatch Alarm: devnovate-demo-lambda-errors." Investigation started. See the status - it is actively investigating.

The agent is now looking at the Lambda function's CloudWatch Logs. It sees the error messages - "Database connection pool exhausted." It is checking for recent deployments. It is analyzing the pattern.

*[Wait for investigation to complete, narrate what appears]*

And there is the root cause analysis. And the mitigation plan. Specific steps to resolve the connection pool issue. All generated autonomously, no human in the loop.

From alarm to root cause to fix recommendation. In minutes. While you sleep.

---

## Slide 14: Key Takeaways

*[Summary. Energetic but clear. Land the four points.]*

Let me leave you with four things to take home tonight.

One - K8sGPT. It is open-source. It is CNCF. It works today with Amazon Bedrock. You can install it on your cluster this weekend with a Helm chart. Give it a try. Even if you do not enable auto-remediation, just the detection and plain-English explanations are incredibly useful.

Two - Guardrails. Always add policy guardrails. Kyverno, OPA, whatever policy engine you prefer. Control where AI can act autonomously and where it needs human approval. Start narrow, expand as you build confidence.

Three - AWS DevOps Agent. If your incidents span beyond a single cluster - into networking, databases, serverless, multi-account environments - this is the tool that scales to that complexity. It is an always-on frontier agent.

Four - the paradigm shift. We are moving from "alert fires, human wakes up, human investigates, human fixes" to "alert fires, AI investigates, AI fixes, human gets notified." The human is still in the loop - but at the oversight layer, not the execution layer. That is the future. And it is available today.

---

## Slide 15: Thank You

*[Warm closing. Slow down. Connect.]*

Thank you, Mumbai. You have been an incredible audience.

If any of this resonated with you - if you want to try K8sGPT on your cluster, if you want to explore DevOps Agent, if you just want to chat about DevOps and AI - please connect with me.

Scan this QR code for my LinkedIn. I post regularly about Kubernetes, GenAI, and infrastructure automation. The demo code from today is on my GitHub - jatinmehrotra. Everything I showed you is there - the EKS cluster config, the K8sGPT settings, the Kyverno policy, the CDK stack for the DevOps Agent pipeline. Fork it, break it, improve it.

One last thought. The best time to start automating your operations was yesterday. The second best time is tonight after this meetup. Go install K8sGPT on a dev cluster. Break a pod on purpose. Watch the AI fix it. That feeling of "wait, it actually works" - that is the moment you will never go back to manual.

Thank you. Enjoy the rest of the meetup.

*[Stay on stage for questions.]*
