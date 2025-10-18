# Valyrion RAG Architecture Documentation

## Overview

Valyrion is a dragon-powered autonomous financial research agent that performs deep analysis using task planning, self-reflection, real-time market data, and Retrieval-Augmented Generation (RAG).

## Architecture Diagram

See `valyrion-architecture-clean.mmd` for the complete system architecture.

## System Components

### 1. User Interface Layer
- **CLI Interface**: Command-line interface for interactive queries
- **Web API**: RESTful API built with FastAPI
- **WebSocket**: Real-time streaming for agent thinking process

### 2. Orchestration Layer (Multi-Agent System)
- **Planning Agent**: Decomposes user queries into structured tasks
- **Action Agent**: Executes tasks using RAG retrieval and tools
- **Validation Agent**: Checks task completion status
- **Answer Agent**: Synthesizes final responses with citations

### 3. RAG Intelligence Layer

#### Query Understanding
- **Intent Classification**: Categorizes query type (factual, comparison, trend analysis)
- **Entity Extraction**: Identifies companies, metrics, time periods
- **Query Rewriting**: Expands abbreviations, adds synonyms, fixes typos

#### Hybrid Retrieval Engine
- **Dense Retrieval**: Vector similarity search using embeddings (Qdrant)
- **Sparse Retrieval**: BM25 keyword search (Elasticsearch)
- **Knowledge Graph**: Cypher queries for relationship-based retrieval (Neo4j)

#### Re-Ranking Pipeline
- **Reciprocal Rank Fusion**: Combines results from multiple retrievers
- **Cross-Encoder Re-ranking**: Scores query-document pairs with full attention
- **Diversity Filtering**: MMR (Maximal Marginal Relevance) to avoid redundancy

### 4. Knowledge Storage Layer

#### Primary Databases
- **Qdrant**: Vector database for embeddings (3072-dim)
- **Neo4j**: Knowledge graph for entities and relationships
- **PostgreSQL**: Document store with full text and metadata
- **Elasticsearch**: Full-text search with BM25 ranking
- **Redis**: Cache layer for embeddings and query results
- **S3**: Object storage for raw documents

### 5. Data Ingestion Pipeline

#### Multi-Source Collectors
- SEC EDGAR (10-K, 10-Q, 8-K filings)
- Earnings call transcripts
- Financial APIs (Finnhub, Alpha Vantage, Yahoo Finance)
- News sources (via APIs)
- Research reports (PDF/HTML)

#### Document Processing
1. **Extraction**: Parse documents using Unstructured.io
2. **Chunking**: Hierarchical semantic chunking (parent/child)
3. **Enrichment**: NER, topic classification, sentiment analysis
4. **Embedding**: Generate vectors using OpenAI text-embedding-3-large
5. **Indexing**: Parallel writes to all databases

## Data Flow

### Query Processing Flow
1. User submits query via CLI/API
2. Planning Agent decomposes query into tasks
3. For each task:
   - Action Agent analyzes task
   - Query Understanding extracts intent and entities
   - Hybrid Retrieval searches all databases
   - Re-Ranking fuses and filters results
   - Action Agent validates results
4. Answer Agent synthesizes final response
5. Response returned to user with citations

### Ingestion Flow
1. Fetcher downloads documents from sources
2. RabbitMQ queues documents for processing
3. Document Pipeline processes each document:
   - Parse with Unstructured.io
   - Chunk semantically
   - Extract entities, topics, sentiment
4. Embedding service generates vectors
5. Parallel Indexer writes to all databases
6. Feedback notifications sent to queue

## Technology Stack

### Infrastructure (AWS)
- **Compute**: ECS Fargate for API and workers
- **Databases**: RDS PostgreSQL, ElastiCache Redis, OpenSearch
- **Storage**: S3 for documents
- **Networking**: VPC, ALB, NAT Gateway
- **IaC**: Terraform

### Application
- **Language**: Python 3.10+
- **Framework**: FastAPI, LangChain
- **AI**: OpenAI GPT-4o, text-embedding-3-large
- **Vector DB**: Qdrant
- **Graph DB**: Neo4j
- **Search**: Elasticsearch/OpenSearch

### ML/NLP Models
- **Embeddings**: OpenAI text-embedding-3-large (3072-dim)
- **LLM**: GPT-4o (reasoning), GPT-4o-mini (classification)
- **Re-ranker**: bge-reranker-large
- **NER**: dslim/bert-base-NER-uncased
- **Sentiment**: ProsusAI/finbert

## Deployment

All infrastructure is deployed on AWS using Terraform:
- No local dependencies
- Auto-scaling based on load
- Multi-AZ for high availability
- Encryption at rest and in transit

See `TASKS.md` for complete implementation plan.

## Performance Targets

- **Query Latency**: <2s (P95)
- **Answer Correctness**: >85%
- **Recall@10**: >90%
- **Cost per Query**: <$0.05
- **Uptime**: 99.5%

## Security

- **Authentication**: API key-based
- **Encryption**: TLS in transit, AES-256 at rest
- **IAM**: Least-privilege roles
- **Secrets**: AWS Secrets Manager
- **WAF**: Rate limiting, attack protection

## Monitoring

- **Metrics**: CloudWatch, Prometheus
- **Logging**: CloudWatch Logs
- **Tracing**: AWS X-Ray (optional)
- **Dashboards**: Grafana, CloudWatch Dashboards
- **Alerts**: SNS notifications

## References

- [Implementation Tasks](../TASKS.md)
- [Transition Proposal](../TRANSITION_PROPOSITION.md)
- [Architecture Diagram](../valyrion-architecture-clean.mmd)
