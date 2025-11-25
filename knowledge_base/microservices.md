---
topic: microservices
domain: architecture
priority: high
source_type: seed
---
Microservices Architecture for Telecom Billing Systems

Microservices decompose the billing stack into independently deployable services (rating, invoicing, mediation, catalog). Benefits:
- Independent scaling per hotspot service
- Technology polyglot flexibility
- Fault isolation limits blast radius
- Smaller deploy units accelerate CI/CD

Challenges:
- Distributed data consistency (sagas, outbox)
- Increased operational overhead (service discovery, mesh)
- Observability requires tracing & correlation IDs
- More complex integration testing

Best Fit:
- High transaction volume
- Frequent product/pricing updates
- Need for rapid innovation & A/B experimentation

Migration Hint:
Start with strangler pattern around high-change domains (e.g., product catalog) before core rating engine.
