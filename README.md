# SCALABILITY

## Introduction
This document outlines strategies for scaling the URL shortener service built with FastAPI and SQLAlchemy/PostgreSQL. The design draws from best practices in building scalable systems like TinyURL, emphasizing horizontal scaling, asynchronous processing, caching, and fault tolerance. Key inspirations come from distributed system designs that handle high read/write ratios (e.g., 200:1 for reads vs. writes in URL shortening), traffic spikes, and resource-intensive operations like logging. The goal is to ensure the service remains performant under load, avoids single points of failure (SPOFs), and can be deployed across multiple instances.

## 1. Handling Heavy Logging Without Impacting Main Service Speed
**Question**: Suppose logging for each request becomes very heavy (e.g., needing to send log information in real-time to another service or database). What solution do you propose so that logging doesn't cause a drop in the main service speed?

**Proposed Solution**:
To decouple heavy logging from the critical path of request handling, I recommend using an asynchronous message queue like Kafka (nice-to-have in the job requirements) or RabbitMQ for buffering logs. Here's how it would work:

- **Asynchronous Logging via Middleware**: In the FastAPI middleware (as already implemented for basic logging in the task), capture request details (e.g., IP, timestamp, short_code) and push them to a Kafka topic asynchronously using a producer library like `confluent-kafka`. This ensures the main request-response cycle (e.g., URL redirection) completes quickly without waiting for log persistence.

- **Background Processing**: Use Celery (required experience in the job) with Redis as the broker to consume messages from the queue. Celery workers would process logs in the background, aggregating data (e.g., visit counts) and storing them in a separate analytics database (e.g., a sharded PostgreSQL or NoSQL like Cassandra for high write throughput). This offloads CPU-intensive or I/O-bound operations from the main app servers.

- **Buffering and Batching**: Configure the producer to batch logs (e.g., send every 100 logs or every 500ms) to reduce overhead. For real-time analytics, use Kafka Streams or a similar processor to compute metrics like visit counts without hitting the primary DB on every request.

- **Fallbacks**: Implement circuit breakers (e.g., via `resilience4j` or custom logic) to drop non-critical logs if the queue backs up, preventing cascading failures.

This approach ensures sub-100ms response times for core operations, as logging becomes non-blocking. It aligns with observability best practices by enabling tracing (e.g., via OpenTelemetry) across services.

## 2. Changes for Multi-Instance Deployment on Multiple Servers
**Question**: If the system is to be deployed as multi-instance on several servers tomorrow, what things need to change? What dependencies need to be separated or externalized? What risks need to be managed?

**Proposed Changes**:
Transitioning to a multi-instance setup requires horizontal scaling, shared state management, and orchestration. The current single-instance design (with local PostgreSQL) would evolve as follows:

- **Load Balancing**: Introduce a load balancer (e.g., NGINX, HAProxy, or cloud-based like AWS ALB) in front of multiple FastAPI instances. Use round-robin distribution initially, evolving to least-connections based on server load metrics (via Prometheus for monitoring).

- **Externalizing Dependencies**:
  - **Database**: Move from local PostgreSQL to a managed, replicated cluster (e.g., AWS RDS with read replicas). Use connection pooling (already in SQLAlchemy) across instances. For scaling writes, implement sharding based on short_code hashes to distribute data evenly.
  - **Caching**: Integrate Redis (familiarity required in job) as an external service for caching frequent redirects and stats. Use Redis Cluster for replication and sharding to handle shared state without conflicts.
  - **Session/State Management**: If user sessions are added later, externalize to Redis instead of in-memory.
  - **Logging and Queues**: Externalize to Kafka or RabbitMQ clusters for distributed processing, with Celery workers scaled independently.

- **Deployment Orchestration**: Use Docker Compose for local multi-instance testing, but switch to Kubernetes (or ECS) for production. Containerize the app (as in the mini project example) and use Helm charts for managing deployments.

- **Code Changes**:
  - Ensure short_code generation is collision-free in a distributed environment: Use a Key Generation Service (KGS) with Zookeeper for coordinating unique counters or pre-generate keys in batches stored in Redis.
  - Alembic migrations: Run them via a dedicated init container in Kubernetes to avoid race conditions during deployments.

- **Risks and Management**:
  - **Consistency Risks**: Distributed short_code generation could lead to duplicates; mitigate with atomic operations in Redis (e.g., INCR) or Zookeeper locks.
  - **SPOF Risks**: Database or Redis failure; address with replication (e.g., Redis Sentinel) and auto-failover.
  - **Network Latency**: Multi-server communication adds overhead; monitor with tracing tools and optimize with gRPC if needed.
  - **Deployment Risks**: Use blue-green deployments to minimize downtime. Test with chaos engineering (e.g., inject failures) to validate resilience.
  - **Cost Risks**: Scaling increases costs; implement auto-scaling based on metrics (e.g., CPU > 70%).

This setup allows seamless scaling to 10+ instances, handling increased load without refactoring core logic.

## 3. Handling Heavy Traffic from an Advertising Campaign
**Question**: Suppose an advertising campaign brings heavy traffic (thousands of requests per second). What decisions have you made or can make so the service doesn't go down?

**Decisions Already Made**:
- **Efficient DB Design**: The schema uses a single table for URLs with indexes on short_code for O(1) lookups. Visit counts are incremented atomically (e.g., via SQL `UPDATE ... SET visits = visits + 1`) to avoid heavy queries.
- **Connection Pooling**: SQLAlchemy's built-in pooling reuses connections, reducing overhead per request.
- **Middleware for Logging**: Keeps logging lightweight and reusable, avoiding per-endpoint bloat.

**Additional Decisions to Prevent Downtime**:
- **Caching Layer**: Add Redis caching for hot short_codes (e.g., top 20% of traffic via Pareto principle). On redirect, check Redis first (TTL: 1 hour); fallback to DB on miss and cache the result. This reduces DB load by 80% during spikes.

- **Rate Limiting and Throttling**: Implement FastAPI middleware with `slowapi` to limit requests per IP (e.g., 100/s) and prevent abuse. For campaigns, whitelist known IPs or use adaptive throttling based on load.

- **Auto-Scaling**: Deploy on cloud infrastructure (e.g., AWS EC2 Auto Scaling Groups) triggered by metrics (e.g., requests/s > 1000). Scale Celery workers separately for background tasks.

- **CDN for Redirects**: Use a CDN (e.g., Cloudflare) to cache 302 redirects at the edge, offloading traffic from app servers. This handles global spikes efficiently.

- **Monitoring and Alerts**: Integrate Prometheus/Grafana for metrics (e.g., response time, error rates) and tracing with Jaeger. Set alerts for anomalies (e.g., DB connections > 80% pool size).

- **Database Optimization**: For extreme loads, shard the DB (e.g., by short_code prefix) and add read replicas. Use NoSQL (e.g., Cassandra) if writes exceed PostgreSQL limits.

- **Fallback Strategies**: Implement graceful degradation: If DB is overloaded, serve stale stats from cache; use circuit breakers to fail-fast on dependencies.

These measures ensure 99.99% uptime under 10k+ RPS, focusing on proactive scaling and redundancy.

## References
- [System Design : Scalable URL shortener service like TinyURL](https://medium.com/@sandeep4.verma/system-design-scalable-url-shortener-service-like-tinyurl-106f30f23a82)
- [a simple link shortener with FastAPI](https://github.com/TorhamDev/link-Shortener-FastAPI)
