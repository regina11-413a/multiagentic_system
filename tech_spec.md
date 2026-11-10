Technical Specifications:

#1. System Purpose
To create a local multi-agent system for automated analysis of text queries with automatic routing, use of custom skills, and mandatory verification of responses in an isolated environment.

#2. Architectural Requirements
- Architectural Pattern: Orchestration based on a deterministic graph (LangGraph).
- Models: Using three local LLMs via Ollama v0.40.0 to optimize computational resources.
- Validation layer: Mandatory independent audit of responses before being displayed to the user.

#3. Memory requirements
- Short-term memory: Storing the context of the current session within the graph state.
- Long-term memory: Extracting and accumulating important facts about the user in an external structured JSON storage (emulating the Mem0 concept).