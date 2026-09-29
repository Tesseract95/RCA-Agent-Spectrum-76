# Complete Workflow Explanation - In Plain English

## The Investigation Journey: "Investigate anomaly a1f0c8e2-...000006"

Let's follow what happens when you type "Investigate anomaly a1f0c8e2-1b44-4d90-9c31-000000000006" in the chat.

---

## 🎬 Act 1: The Request Arrives

### Step 1: You Type in the Chat
```
You: "Investigate anomaly a1f0c8e2-1b44-4d90-9c31-000000000006"
```

**What happens:**
- The **React frontend** (your browser) captures your message
- It sends it to the **FastAPI backend** at `http://localhost:8000/chat`
- Includes a unique `thread_id` (like a conversation ID) so the system remembers your chat history

**Think of it like:** You walk into a detective agency and hand them a case file number.

---

## 🎬 Act 2: The Receptionist (FastAPI Endpoint)

### Step 2: FastAPI Receives the Request
**File:** `starter_code/main.py` - `/chat` endpoint

**What happens:**
```python
# Backend receives:
{
  "message": "Investigate anomaly a1f0c8e2-1b44-4d90-9c31-000000000006",
  "thread_id": "abc-123-xyz"  # Your conversation ID
}
```

**The backend:**
1. ✅ Checks that the agent system is ready
2. ✅ Creates or retrieves your conversation thread
3. ✅ Passes your message to the **LangGraph Agent System**

**Think of it like:** The receptionist takes your case file and hands it to the detective team.

---

## 🎬 Act 3: The Head Detective (Orchestrator Agent)

### Step 3: Orchestrator Analyzes Your Request
**File:** `starter_code/agent/orchestrator_agent.py`

**What the Orchestrator does:**
```
🧠 Thinking: "Let me read this message..."
   - Message says "investigate" → This is an investigation request
   - Found anomaly ID: a1f0c8e2-...000006
   - No previous investigation in progress
   
🎯 Decision: "Route this to the INVESTIGATION AGENT"
```

**The Orchestrator is like:** A detective chief who reads the case and assigns it to the right specialist.

**Other routing examples:**
- "List all anomalies" → Routes to List Handler
- "What is BGP?" → Routes to Explanation Agent
- "Show me device logs" → Routes to Data Retrieval Agent
- "Why did this happen?" (during investigation) → Routes to Analysis Agent

---

## 🎬 Act 4: The Specialist Detective (Investigation Agent)

### Step 4: Investigation Agent Takes Over
**File:** `starter_code/agent/investigation_agent.py`

**What the Investigation Agent does:**

#### 4A: Reads the Investigation Manual
**File:** `starter_code/agent/prompts/investigation_skills.md`

This file tells the agent:
```
"You are a network investigation specialist. When investigating:
1. First, get the anomaly details
2. Identify what devices are affected
3. Check telemetry data for that time period
4. Look for error logs
5. Correlate all evidence
6. Provide a root cause with confidence level"
```

**Think of it like:** The detective reads their case-solving checklist.

#### 4B: Gets Access to Investigation Tools

The agent now has access to 8 tools (like a detective's toolbox):
1. 🔍 `get_anomaly_details` - Read the incident report
2. 📋 `get_device_information` - Check device records
3. 📊 `query_device_telemetry` - Check performance metrics
4. 📝 `query_device_syslogs` - Read system logs
5. 🔎 `search_syslogs_by_keyword` - Search logs for keywords
6. 🔗 `search_related_anomalies` - Find similar cases
7. 📊 `sql_query_executor` - Run custom database queries
8. 📋 `list_all_anomalies` - See all open cases

---

## 🎬 Act 5: The Investigation Begins

### Step 5: Tool Call #1 - Get Anomaly Details
**File:** `starter_code/agent/tools.py` → `get_anomaly_details()`

**Agent's thought process:**
```
🤔 "First, I need to see what this anomaly is about"
🔧 Uses tool: get_anomaly_details("a1f0c8e2-...000006")
```

**What the tool does:**
1. Opens a connection to the **DuckDB database**
2. Runs SQL: `SELECT * FROM detected_anomalies WHERE anomaly_id = 'a1f0c8e2-...000006'`
3. Returns the data in JSON format

**Data returned:**
```json
{
  "anomaly_id": "a1f0c8e2-...000006",
  "severity": "high",
  "anomaly_date": "2026-07-12",
  "model_output": {
    "detector": "bgp_session",
    "window": {
      "start": "2026-07-12T08:00:00Z",
      "end": "2026-07-12T09:30:00Z"
    },
    "impacted_hostnames": ["RIVERDALE-RTR01"],
    "host_count": 1,
    "criticality": "high",
    "event_summary": {
      "bgp_peer_loss_events": 3,
      "upstream_trigger_hint": "xe-0/0/5 interface flap"
    }
  }
}
```

**Agent learns:**
- 🎯 This is a **BGP session problem**
- 📅 It happened on **July 12, 2026 from 8:00-9:30 AM**
- 🖥️ Affected device: **RIVERDALE-RTR01**
- 💡 Hint: **Interface xe-0/0/5 might have flapped**

**Think of it like:** The detective opens the case file and reads the initial report.

---

### Step 6: Tool Call #2 - Get Device Information
**Agent's thought process:**
```
🤔 "Let me check what this device is and where it's located"
🔧 Uses tool: get_device_information("RIVERDALE-RTR01")
```

**What the tool does:**
1. Runs SQL: `SELECT * FROM network_devices WHERE hostname = 'RIVERDALE-RTR01'`

**Data returned:**
```json
{
  "device_id": "DEV-0042",
  "hostname": "RIVERDALE-RTR01",
  "device_type": "router",
  "role": "internet_zone_router",
  "site_code": "RIVERDALE",
  "city": "Riverdale",
  "region": "Northeast",
  "notes": "Internet edge router. xe-0/0/5 is primary BGP peer to ISP."
}
```

**Agent learns:**
- 🌐 This is an **internet edge router** (critical!)
- 📍 Located in **Riverdale, Northeast region**
- 🔌 Interface xe-0/0/5 connects to the **ISP** (internet provider)
- ⚠️ If this interface fails, internet connectivity is affected

**Think of it like:** The detective checks the building blueprints to understand what broke.

---

### Step 7: Tool Call #3 - Check Telemetry Data
**Agent's thought process:**
```
🤔 "Let me see the performance metrics during that time window"
🔧 Uses tool: query_device_telemetry(
      device_id="DEV-0042",
      start_time="2026-07-12 08:00:00",
      end_time="2026-07-12 09:30:00"
    )
```

**What the tool does:**
1. Runs SQL: `SELECT * FROM device_telemetry WHERE device_id = 'DEV-0042' AND timestamp BETWEEN '...' AND '...'`

**Data returned:**
```json
[
  {
    "timestamp": "2026-07-12 08:00:00",
    "cpu_utilization_pct": 45.2,
    "bgp_established_peers": 4,
    "interface_flap_count": 0
  },
  {
    "timestamp": "2026-07-12 08:15:00",
    "cpu_utilization_pct": 47.1,
    "bgp_established_peers": 3,  // ⚠️ Lost 1 peer!
    "interface_flap_count": 2     // ⚠️ Interface flapped!
  },
  {
    "timestamp": "2026-07-12 08:30:00",
    "cpu_utilization_pct": 46.8,
    "bgp_established_peers": 3,  // Still missing 1 peer
    "interface_flap_count": 5     // More flaps!
  }
]
```

**Agent learns:**
- 📉 **BGP peers dropped from 4 to 3** at 8:15 AM
- 🔄 **Interface flapped 7 times** during the incident
- 💻 CPU was normal (no performance issue)

**Think of it like:** The detective reviews the security camera footage showing what happened.

---

### Step 8: Tool Call #4 - Check System Logs
**Agent's thought process:**
```
🤔 "Let me see the error logs from that device during the incident"
🔧 Uses tool: query_device_syslogs(
      device_id="DEV-0042",
      start_time="2026-07-12 08:00:00",
      end_time="2026-07-12 09:30:00",
      severity="error"
    )
```

**What the tool does:**
1. Runs SQL: `SELECT * FROM device_syslogs WHERE device_id = 'DEV-0042' AND severity = 'error' AND ...`

**Data returned:**
```json
[
  {
    "timestamp": "2026-07-12 08:14:32",
    "severity": "error",
    "message_type": "interface",
    "message": "xe-0/0/5: Interface went down"
  },
  {
    "timestamp": "2026-07-12 08:14:35",
    "severity": "error",
    "message_type": "bgp",
    "message": "BGP peer 203.0.113.1 (ISP-MAIN) session closed"
  },
  {
    "timestamp": "2026-07-12 08:14:45",
    "severity": "error",
    "message_type": "interface",
    "message": "xe-0/0/5: Interface came back up"
  },
  {
    "timestamp": "2026-07-12 08:15:12",
    "severity": "error",
    "message_type": "bgp",
    "message": "BGP peer 203.0.113.1 failed to re-establish"
  }
]
```

**Agent learns:**
- 🔴 **Interface xe-0/0/5 went down** at 8:14:32 AM
- 🔴 **BGP session to ISP closed** immediately after
- 🟢 **Interface came back up** 13 seconds later
- 🔴 **BGP session couldn't reconnect** (this is the problem!)

**Think of it like:** The detective reads witness statements about what went wrong.

---

## 🎬 Act 6: The Analysis (Claude AI Brain)

### Step 9: Agent Thinks and Connects the Dots

**The Investigation Agent (using Claude Haiku 4.5) now processes all this information:**

```
🧠 AI Thinking Process:

1. TIMELINE RECONSTRUCTION:
   - 08:14:32: Interface xe-0/0/5 goes down
   - 08:14:35: BGP session to ISP closes (expected - interface is down)
   - 08:14:45: Interface comes back up (13 seconds of downtime)
   - 08:15:12: BGP fails to re-establish (THIS IS THE ISSUE)
   
2. ROOT CAUSE ANALYSIS:
   - Interface flapped (went down and up quickly)
   - BGP session closed during the flap
   - When interface came back, BGP couldn't reconnect
   - Likely reason: BGP hold timer expired, or authentication issue
   
3. IMPACT ASSESSMENT:
   - Device: RIVERDALE-RTR01 (internet edge router)
   - Interface: xe-0/0/5 (primary ISP connection)
   - Result: Lost BGP route advertisements to internet
   - Severity: HIGH - Internet connectivity impacted
   
4. CONFIDENCE LEVEL:
   - Evidence: Strong (telemetry, logs, timeline all align)
   - Correlation: Clear (interface flap → BGP loss)
   - Confidence: HIGH
```

**Think of it like:** The detective connects all the clues and figures out exactly what happened and why.

---

## 🎬 Act 7: The Report (Agent's Response)

### Step 10: Investigation Agent Writes the Conclusion

**The agent creates a detailed report:**

```markdown
## Root Cause Analysis - Anomaly a1f0c8e2-...000006

### Summary
BGP session failure on RIVERDALE-RTR01 caused by interface flap on xe-0/0/5.

### Timeline
- **08:14:32 UTC**: Interface xe-0/0/5 went down
- **08:14:35 UTC**: BGP peer session to ISP (203.0.113.1) closed
- **08:14:45 UTC**: Interface came back up (13 seconds downtime)
- **08:15:12 UTC**: BGP session failed to re-establish

### Root Cause
The interface xe-0/0/5 experienced a brief flap (went down for 13 seconds).
When it came back up, the BGP session to the ISP could not re-establish,
likely due to BGP hold timer expiration or authentication timeout.

### Affected Systems
- **Device**: RIVERDALE-RTR01 (Internet edge router)
- **Interface**: xe-0/0/5 (Primary ISP uplink)
- **Impact**: Lost internet route advertisements
- **Duration**: 1 hour 30 minutes (08:00 - 09:30 UTC)

### Supporting Evidence
1. **Interface Telemetry**: Showed 7 interface flaps during incident window
2. **BGP Metrics**: BGP peer count dropped from 4 to 3
3. **System Logs**: Confirmed interface down/up events and BGP failures
4. **Device Role**: Internet edge router - critical for connectivity

### Confidence Level
**HIGH** - Strong correlation between interface flap and BGP failure,
clear timeline, multiple data sources confirm the sequence of events.

### Recommended Actions
1. Investigate physical layer on xe-0/0/5 (fiber, optics, cable)
2. Check with ISP for any issues on their side
3. Review BGP timers - may need to increase hold timer
4. Consider implementing BFD (Bidirectional Forwarding Detection) for faster failover
```

**Think of it like:** The detective writes up the case report with all findings and recommendations.

---

## 🎬 Act 8: The Response Returns

### Step 11: Back Through the System

**The response travels back:**

```
Investigation Agent
    ↓ (returns report)
Orchestrator Agent
    ↓ (passes it along)
LangGraph System
    ↓ (saves to conversation memory)
FastAPI Backend
    ↓ (packages as JSON)
React Frontend
    ↓ (displays in chat)
YOUR SCREEN! 🎉
```

**What gets saved:**
- Your conversation thread remembers this investigation
- The `current_anomaly_id` is stored in memory
- You can now ask follow-up questions like:
  - "What was the impact?"
  - "Show me the logs"
  - "What should we do to fix this?"

---

## 🎬 Bonus Act: Follow-Up Questions

### If You Ask: "What interfaces were affected?"

**What happens:**
```
1. Orchestrator reads: "User asking about investigation details"
2. Orchestrator sees: current_anomaly_id is set (there's an active investigation)
3. Orchestrator routes to: ANALYSIS AGENT (not Investigation Agent)
4. Analysis Agent:
   - Reads the previous investigation from memory
   - Extracts: "Interface xe-0/0/5 was affected"
   - Responds: "The affected interface was xe-0/0/5 on device RIVERDALE-RTR01,
              which is the primary BGP peer connection to the ISP."
```

**No need to investigate again!** The system remembers.

---

## 📊 Visual Flow Diagram

```
┌─────────────────┐
│   YOU TYPE      │
│   "Investigate  │
│    anomaly..."  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  REACT FRONTEND                     │
│  - Captures message                 │
│  - Sends to /chat endpoint          │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  FASTAPI BACKEND                    │
│  - Receives request                 │
│  - Checks agent is ready            │
│  - Passes to LangGraph              │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  ORCHESTRATOR AGENT                 │
│  - Reads message                    │
│  - Extracts anomaly ID              │
│  - Routes to Investigation Agent    │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  INVESTIGATION AGENT                │
│  - Reads investigation_skills.md    │
│  - Gets 8 tools                     │
│                                     │
│  Tool 1: get_anomaly_details()      │
│     ↓ Gets: detector, time, hosts   │
│                                     │
│  Tool 2: get_device_information()   │
│     ↓ Gets: device role, location   │
│                                     │
│  Tool 3: query_device_telemetry()   │
│     ↓ Gets: performance metrics     │
│                                     │
│  Tool 4: query_device_syslogs()     │
│     ↓ Gets: error logs              │
│                                     │
│  AI THINKING:                       │
│     - Connects all evidence         │
│     - Identifies root cause         │
│     - Assesses confidence           │
│                                     │
│  Generates: RCA Report              │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  LANGGRAPH SYSTEM                   │
│  - Saves to conversation memory     │
│  - Updates current_anomaly_id       │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  FASTAPI RESPONSE                   │
│  - Packages as JSON                 │
│  - Returns to frontend              │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  REACT FRONTEND                     │
│  - Displays report in chat          │
│  - Renders markdown formatting      │
│  - Ready for follow-up questions    │
└─────────────────────────────────────┘
```

---

## 🔑 Key Concepts Explained

### 1. What is LangGraph?
**Simple explanation:** It's like a flowchart for AI agents. Each box (node) is an agent that does something, and arrows show where to go next.

### 2. What are Tools?
**Simple explanation:** They're like apps on your phone. The AI can "open" a tool to do something specific (like checking the database, running a query, etc.)

### 3. What is State?
**Simple explanation:** It's the AI's notepad. It writes down:
- What you said
- What anomaly you're investigating
- What it found so far
- Where it is in the process

### 4. What is Thread ID?
**Simple explanation:** It's like a conversation ID. Each chat session has a unique ID so the system remembers your conversation even if you close the browser.

### 5. What is Claude Haiku 4.5?
**Simple explanation:** It's the AI brain (like ChatGPT) that reads all the data and figures out what happened. It's fast and good at reasoning.

---

## 🎯 Why This Architecture?

### Multiple Agents = Better Organization
```
One big agent = Jack of all trades, master of none
Multiple specialized agents = Experts in their field

Like having:
- Detective Chief (Orchestrator) - assigns cases
- Crime Scene Investigator (Investigation Agent) - gathers evidence
- Data Analyst (Analysis Agent) - finds patterns
- Teacher (Explanation Agent) - answers general questions
```

### Database Tools = Reliable Information
```
Instead of AI making up answers, it:
1. Queries real database
2. Gets actual data
3. Analyzes facts
4. Provides evidence-based conclusions
```

### Memory = Conversational
```
Without memory: Each question is brand new
With memory: AI remembers your investigation
Result: You can ask follow-ups naturally
```

---

## 🚀 Summary in 5 Sentences

1. **You type** "Investigate anomaly..." in the chat
2. **Orchestrator** reads it and sends it to the Investigation Agent
3. **Investigation Agent** uses tools to query the database 4-5 times (gets anomaly, device info, telemetry, logs)
4. **Claude AI** connects all the evidence and writes a root cause analysis report
5. **Report appears** in your chat, and you can ask follow-up questions!

---

## 🎓 The Magic Ingredient: AI Reasoning

The real power is that the Investigation Agent **decides** what to investigate:
- ❌ Not hardcoded: "If BGP, then query X, Y, Z"
- ✅ AI-driven: "Let me see what tools I have... I need to understand the timeline... Let me check the logs..."

This means it can handle **any** type of anomaly without being programmed for each one specifically!

---

**That's the complete journey from your keyboard to the detective's report! 🕵️‍♂️**
