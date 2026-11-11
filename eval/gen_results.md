# Generation eval

| check | result |
|---|---|
| In-scope questions refused (want low) | 0/15 |
| Answers with valid citations (want all) | 15/15 |
| Answers fully supported by cited passages (judge) | 15/15 |
| Out-of-scope questions refused (want all) | 13/13 |
| Errors | 0 |

## Top judge score (use it to tune MIN_JUDGE_SCORE)

- in-scope lowest: 10.0
- out-of-scope highest: 8.0

## In-scope answers (read these yourself)

### IN SCOPE q001: Which Amazon EC2 instance family is specifically engineered for deep learning inference workloads?
refused: False (None) | top judge score: 10.0 | 8469 ms

Inf2 Instances are purpose-built for deep learning inference [1].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Compute
- judge: supported=True []
- MY VERDICT 

### IN SCOPE q003: What object storage service provides 11 9s of data durability along with lifecycle tiering and WORM compliance via Object Lock?
refused: False (None) | top judge score: 10.0 | 6404 ms

Amazon Simple Storage Service (Amazon S3) provides 11 9s of data durability along with lifecycle tiering and WORM compliance via Object Lock [1][2].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Storage
- [2] aws-overview > Overview of Amazon Web Services > AWS services by category > Storage
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q005: What fully managed, elastic POSIX-compliant file system allows concurrent access from multiple EC2 instances and containers?
refused: False (None) | top judge score: 10.0 | 6246 ms

Amazon Elastic File System (Amazon EFS) provides a simple, scalable, elastic file system for Linux-based workloads for use with AWS Cloud services and on-premises resources [1].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Storage
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q007: Which key-value and document NoSQL database provides single-digit millisecond performance at high scale?
refused: False (None) | top judge score: 10.0 | 5353 ms

Amazon DynamoDB is a key-value and document database that delivers single-digit millisecond performance at any scale [1][2].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Databases
- [2] aws-overview > Overview of Amazon Web Services > AWS services by category > Databases
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q009: Which serverless interactive query service lets users analyze S3 data directly using standard SQL syntax?
refused: False (None) | top judge score: 10.0 | 5735 ms

Amazon Athena lets users analyze S3 data directly using standard SQL syntax [1][2][3].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Analytics
- [2] aws-overview > Overview of Amazon Web Services > AWS services by category > Analytics
- [3] generative-ai-lens > Generative AI Lens > Sustainability > Consume sustainable data processing and storage services
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q011: Which end-to-end machine learning platform enables developers to build, train, tune, and deploy custom ML models at scale?
refused: False (None) | top judge score: 10.0 | 5633 ms

Amazon SageMaker enables developers to build, train, tune, and deploy custom ML models at scale [2][3].

- [2] aws-overview > Overview of Amazon Web Services > AWS services by category > Machine Learning (ML) and Artificial Intelligence (AI)
- [3] aws-overview > Overview of Amazon Web Services > AWS services by category > Machine Learning (ML) and Artificial Intelligence (AI)
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q013: In a Retrieval-Augmented Generation (RAG) system, what purpose does the Vector Data Store serve?
refused: False (None) | top judge score: 10.0 | 5528 ms

In a Retrieval-Augmented Generation (RAG) system, the Vector Data Store serves the purpose of efficient storage and retrieval of high-dimensional vector embeddings, which are used in semantic search and retrieval tasks [1].

- [1] generative-ai-lens > Generative AI Lens > Definitions
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q015: What is the main role of a Multi-Tenant Enterprise AI Gateway when deployed in front of foundation models?
refused: False (None) | top judge score: 10.0 | 5632 ms

The main role of a Multi-Tenant Enterprise AI Gateway when deployed in front of foundation models is to securely route inference requests across multiple foundation models and deployment backends [3].

- [3] generative-ai-lens > Generative AI Lens > Scenarios > Multi-tenant generative AI platform scenario
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q017: Which perimeter protection service inspects incoming HTTP/S requests to defend AI API endpoints against common web exploits?
refused: False (None) | top judge score: 10.0 | 6142 ms

AWS WAF inspects incoming HTTP/S requests to defend AI API endpoints against common web exploits [1][2].

- [1] generative-ai-lens > Generative AI Lens > Scenarios > Multi-tenant generative AI platform scenario
- [2] aws-overview > Overview of Amazon Web Services > AWS services by category > Security, identity, and compliance
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q019: Which API call mechanism captures real-time end-user sentiment and quality feedback in Amazon Q?
refused: False (None) | top judge score: 10.0 | 5531 ms

The `PutFeedback` API action captures real-time end-user sentiment and quality feedback in Amazon Q [1].

- [1] generative-ai-lens > Generative AI Lens > Operational excellence > Model performance evaluation
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q021: What request strategy should clients adopt to handle Foundation Model quota rate limits (InvocationThrottles) gracefully?
refused: False (None) | top judge score: 10.0 | 5624 ms

Clients should implement request buffering using a message queue service to handle Foundation Model quota rate limits gracefully [1].

- [1] generative-ai-lens > Generative AI Lens > Reliability > Manage throughput quotas
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q023: What feature gives developers step-by-step insight into the reasoning paths and tool calls executed by autonomous AI agents?
refused: False (None) | top judge score: 10.0 | 5840 ms

Tracing provides a detailed view of the agent's step-by-step reasoning process [1].

- [1] generative-ai-lens > Generative AI Lens > Operational excellence > Observability in workloads
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q025: Which EC2 instance family uses AWS Trainium accelerators for high-performance deep learning training?
refused: False (None) | top judge score: 10.0 | 5641 ms

Trn1 Instances use AWS Trainium accelerators for high-performance deep learning training [1].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Compute
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q027: Which shared network drive can many servers and containers read and write at the same time?
refused: False (None) | top judge score: 10.0 | 5531 ms

Amazon EFS [1]

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Storage
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

### IN SCOPE q029: How can I block malicious web requests such as SQL injection before they reach my AI application?
refused: False (None) | top judge score: 10.0 | 5836 ms

You can block malicious web requests such as SQL injection before they reach your AI application using AWS WAF [1].

- [1] aws-overview > Overview of Amazon Web Services > AWS services by category > Security, identity, and compliance
- judge: supported=True []
- MY VERDICT (correct / partly / wrong): 

## Out-of-scope answers

### OUT OF SCOPE o001: Who won the 2022 FIFA World Cup?
refused: True (low_relevance) | top judge score: 0.0 | 3583 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o002: What is a good recipe for banana bread?
refused: True (low_relevance) | top judge score: 0.0 | 3274 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o003: How do I reverse a linked list in Python?
refused: True (low_relevance) | top judge score: 0.0 | 3484 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o004: What is the capital of Australia?
refused: True (low_relevance) | top judge score: 0.0 | 2969 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o005: What is the hourly price of an m5.large EC2 instance in us-east-1?
refused: True (low_relevance) | top judge score: 0.0 | 4300 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o006: How do I configure Azure Active Directory conditional access policies?
refused: True (low_relevance) | top judge score: 0.0 | 4506 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o007: What kubectl command scales a Kubernetes deployment to 5 replicas?
refused: True (low_relevance) | top judge score: 0.0 | 3993 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o008: How do I configure Google Cloud Armor security policies?
refused: True (low_relevance) | top judge score: 0.0 | 3890 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o009: How much does AWS Lambda cost per million requests?
refused: True (model_refused) | top judge score: 7.0 | 5120 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o010: What is the default limit on the number of VPCs per Region?
refused: True (low_relevance) | top judge score: 0.0 | 3788 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o012: How do I set up AWS Direct Connect with a link aggregation group?
refused: True (model_refused) | top judge score: 5.0 | 5119 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o013: Which AWS Region has the lowest latency from Mumbai?
refused: True (low_relevance) | top judge score: 0.0 | 3481 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 

### OUT OF SCOPE o014: What are the steps to migrate an Oracle database to Aurora using DMS?
refused: True (model_refused) | top judge score: 8.0 | 4709 ms

I couldn't find the answer to that in the AWS whitepapers I have indexed, so I won't guess.

- MY VERDICT (correct / partly / wrong): 