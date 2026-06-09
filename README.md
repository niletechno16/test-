# 🤖 Nile Techno — ChatWoot AI Support Reporter

An automated system that receives conversation closure notifications from ChatWoot, analyzes them using AI, and saves reports to a SQL Server database.

---

## 📋 Project Overview

When any support conversation is closed on ChatWoot, the system automatically:

1. Receives the closure notification via Webhook
2. Fetches the full conversation history from ChatWoot API
3. Analyzes the conversation using AI and extracts a summary and classification
4. Saves the data into two tables in SQL Server

---

## 🗂️ File Structure

```
├── Main.py           # Main application code
├── requirements.txt  # Required libraries
├── Dockerfile        # Docker configuration (optional)
└── README.md         # This file
```

---

## ⚙️ Requirements

### Libraries
```
fastapi
uvicorn
requests
groq
google-generativeai
cerebras-cloud-sdk
pymssql
```

### Python
Version 3.14 or higher

---

## 🔑 Environment Variables

Add the following variables in Render or any deployment environment:

### ChatWoot
| Variable | Description |
|---|---|
| `CHATWOOT_URL` | ChatWoot server URL |
| `ACCOUNT_ID` | ChatWoot account ID |
| `ACCESS_TOKEN` | ChatWoot API access token |

### Groq API Keys
| Variable | Description |
|---|---|
| `GROQ_KEY_1` to `GROQ_KEY_5` | Groq API keys (5 keys for fallback) |

### Gemini API Keys
| Variable | Description |
|---|---|
| `GEMINI_KEY_1` to `GEMINI_KEY_5` | Gemini API keys (5 keys for fallback) |

### Cerebras API Keys
| Variable | Description |
|---|---|
| `CEREBRAS_KEY_1` to `CEREBRAS_KEY_4` | Cerebras API keys (4 keys for fallback) |

### Database
| Variable | Description |
|---|---|
| `DB_SERVER` | SQL Server address |
| `DB_NAME` | Database name |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `DB_PORT` | Port number (default: 1433) |

---

## 🗄️ Database Schema

### Reports Table `Customer_service_reports_by_A`
| Column | Type | Description |
|---|---|---|
| `id` | INT | Auto-increment primary key |
| `customer_id` | INT | Permanent customer ID |
| `customer_name` | NVARCHAR(255) | Customer name |
| `customer_phone` | NVARCHAR(50) | Phone number |
| `classification` | NVARCHAR(500) | AI classification |
| `agent_id` | INT | Agent ID |
| `agent_name` | NVARCHAR(255) | Agent name |
| `conv_id` | NVARCHAR(50) | Conversation ID |
| `resolved_date` | BIGINT | Closure date |
| `resolved_time` | NVARCHAR(20) | Closure time |
| `summary` | NVARCHAR(MAX) | AI summary |
| `created_at` | DATETIME | Record creation time |

### Customers Table `customer_detail_by_A`
| Column | Type | Description |
|---|---|---|
| `customer_id` | INT | Primary key — never duplicated |
| `customer_name` | NVARCHAR(255) | Customer name |
| `customer_phone` | NVARCHAR(50) | Phone number |

> Each customer is saved only once regardless of how many times their conversations are closed.

---

## 🤖 AI System

The system uses an automatic fallback chain:

```
Groq (5 keys) → Gemini (5 keys) → Cerebras (4 keys)
```

If a key fails → tries the next one automatically.
If a provider is exhausted → moves to the next provider.

### AI Response Format
```
الخلاصة: Detailed description of the problem
التصنيف: تم حل مشكلة:... / لم يتم حل مشكلة:... / العميل لا يرد / سيتم التواصل مع العميل قريباً / لم يتم تعريف مشكلة / لم يتم تعريف حل
```

---

## 🔗 Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/webhook` | POST | Receives ChatWoot notifications |
| `/health` | GET | Health check to keep server alive |

---

## 🚀 Deploying on Render

1. Push files to GitHub
2. Create a new Web Service on Render
3. Select the repo
4. Add all environment variables
5. In ChatWoot → Settings → Integrations → Webhooks add:
```
https://your-app.onrender.com/webhook
```
Enable: **Conversation Status Changed**

---

## 🔧 SQL Server Connection Settings

The system uses `pymssql` with the following settings:
```python
tds_version='4.2'
charset='CP1256'
```

> These settings are required to connect to a Windows SQL Server from a Linux environment (Render).

---

## 🛡️ Uptime & Reliability

- **UptimeRobot** — Pings `/health` every 5 minutes to prevent sleep
- **Render Health Check** — Auto-restarts if the server goes down
- **Auto Deploy** — Deploys automatically on every GitHub push
