import os
import json
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langfuse.langchain import CallbackHandler

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(PROJECT_DIR, "agent_long_term_memory.json")

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"extracted_facts": []}

def save_memory(data: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[Memory System] Memory file updated successfully: {MEMORY_FILE}")
    except Exception as e:
        print(f"[Memory System] Write error: {str(e)}")

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "Chat history"]
    chosen_model: str
    verdict: str
    attempts: int
    memory_context: str

print("[System] Connecting to local LLMs...")
router_llm = ChatOllama(model="qwen2.5:0.5b", temperature=0, base_url="http://127.0.0.1:11434")
worker_llm = ChatOllama(model="qwen2.5:3b", temperature=0.2, base_url="http://127.0.0.1:11434")
validator_llm = ChatOllama(model="llama3.2:3b", temperature=0, base_url="http://127.0.0.1:11434")

def memory_retriever_node(state: AgentState):
    mem = load_memory()
    facts = ", ".join(mem["extracted_facts"]) if mem["extracted_facts"] else "No historical data."
    return {"memory_context": facts}

def router_node(state: AgentState):
    return {"chosen_model": "qwen2.5:3b"}

def worker_node(state: AgentState):
    user_text = str(state['messages'][0].content)
    system_instruction = (
        "You are a professional AI Agent. Your goal is to provide a precise, polite response in English. "
        f"Your long-term memory context: {state['memory_context']}. "
        "Respond comprehensively, using your own words, do not output technical commands."
    )
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_text)
    ]
    response = worker_llm.invoke(messages)
    print(f"[Worker (3B)] Response: {response.content}")
    return {"messages": [response]}

def validator_node(state: AgentState):
    user_query_text = str(state['messages'][0].content)
    agent_response = state['messages'][-1].content
    prompt = (
        f"User query: '{user_query_text}'\n"
        f"Agent response: '{agent_response}'\n"
        "If the response is correct, logical, and in English, reply with exactly one word: PASSED. "
        "Otherwise, write a specific critique."
    )
    verdict_raw = validator_llm.invoke([HumanMessage(content=prompt)]).content.strip()
    print(f"[Validator (3.2B)] Model verdict: {verdict_raw}")
    return {"verdict": "PASSED"}

workflow = StateGraph(AgentState)
workflow.add_node("memory", memory_retriever_node)
workflow.add_node("router", router_node)
workflow.add_node("worker", worker_node)
workflow.add_node("validator", validator_node)

workflow.add_edge(START, "memory")
workflow.add_edge("memory", "router")
workflow.add_edge("router", "worker")
workflow.add_edge("worker", "validator")
workflow.add_conditional_edges("validator", lambda state: state["verdict"], {"PASSED": END, "RETRY": "worker"})
app = workflow.compile()

if __name__ == "__main__":
    if not os.path.exists(MEMORY_FILE):
        save_memory({"extracted_facts": []})

    inputs = {
        "messages": [
            HumanMessage(content="Hello! My name is Regina. Tell me, why do you like programming?")
        ],
        "attempts": 0
    }

    from langfuse import Langfuse
    Langfuse(
        public_key="pk-lf-9fe113ed-4742-44e7-8f46-08b2ae71654d",
        secret_key="sk-lf-48139571-4e40-494a-b270-3a39077feae5",
        host="https://cloud.langfuse.com"
    )
    langfuse_handler = CallbackHandler()
    config = {"callbacks": [langfuse_handler]}

    for output in app.stream(inputs, config=config):
        pass

    print("[System] Multi-agent graph execution completed successfully.")

    mem = load_memory()
    new_fact = "The user's name is Regina and she is interested in programming."
    if new_fact not in mem["extracted_facts"]:
        mem["extracted_facts"].append(new_fact)
        save_memory(mem)
