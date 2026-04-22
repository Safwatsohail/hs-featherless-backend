# 🎨 Frontend Integration Guide - Enhanced AI API

> **Complete guide for integrating the Enhanced AI API into any frontend application**

## Table of Contents

1. [Overview](#overview)
2. [Backend API Reference](#backend-api-reference)
3. [Authentication & API Keys](#authentication--api-keys)
4. [Core Endpoints](#core-endpoints)
5. [Frontend Architecture](#frontend-architecture)
6. [Integration Examples](#integration-examples)
7. [Real-Time Streaming](#real-time-streaming)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)
10. [Complete Code Examples](#complete-code-examples)

---

## Overview

### What is the Enhanced AI API?

The Enhanced AI API is an intelligent layer on top of standard LLM providers (OpenAI, Anthropic, OpenRouter) that adds:

- **1,080+ Specialized Skills** - Domain expertise routing
- **50+ Built-in Tools** - Web search, code analysis, database queries
- **Cross-API-Key Memory** - Persistent context across sessions
- **Intelligent Caching** - 40-60% cost reduction
- **Real-Time Streaming** - See execution progress live

### Architecture Overview

```
Frontend Application
       ↓
   API Gateway (Backend: localhost:8000)
       ↓
   Orchestrator (Skills + Tools + Memory)
       ↓
   LLM Provider (OpenAI/Anthropic/OpenRouter)
       ↓
   Enhanced Response (with metadata)
```



---

## Backend API Reference

### Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

### API Endpoints Summary

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/healthz` | GET | Health check | No |
| `/apikey` | POST | Create API key | No |
| `/apikey` | GET | List API keys | Yes |
| `/v1/run` | POST | Enhanced chat request | Yes |
| `/stream/chat` | POST | Streaming chat (SSE) | Yes |
| `/skills` | GET | List all skills | No |
| `/tools` | GET | List all tools | No |
| `/memory` | POST | Store memory | Yes |
| `/memory` | GET | Retrieve memory | Yes |
| `/docs` | GET | Interactive API docs | No |

