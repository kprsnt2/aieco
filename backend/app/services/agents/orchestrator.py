"""
AIEco - Agent Orchestrator
LangGraph-based multi-agent system
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
from enum import Enum
import structlog

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = structlog.get_logger()


class AgentState(Dict):
    """State passed between agent nodes"""
    messages: List[Any]
    task: str
    tools_used: List[str]
    iterations: int
    output: Optional[str]
    error: Optional[str]


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents using LangGraph.
    Supports code, research, file, and custom agents.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.max_iterations = 10
        
    async def run(
        self,
        agent_type: str,
        task: str,
        context: Dict[str, Any] = {},
        tools: Optional[List[str]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Run an agent to completion"""
        self.max_iterations = max_iterations
        
        # Build agent graph based on type
        graph = self._build_agent_graph(agent_type, tools)
        
        # Initial state
        state = AgentState(
            messages=[],
            task=task,
            tools_used=[],
            iterations=0,
            output=None,
            error=None
        )
        
        # Add context to state
        state.update(context)
        
        # Run the graph
        logger.info("🤖 Running agent", agent_type=agent_type, task=task[:50])
        
        try:
            final_state = await graph.ainvoke(state)
            return {
                "output": final_state.get("output", ""),
                "steps": final_state.get("steps", []),
                "tools_used": final_state.get("tools_used", []),
                "iterations": final_state.get("iterations", 0)
            }
        except Exception as e:
            logger.error("❌ Agent failed", error=str(e))
            raise
    
    async def stream_run(
        self,
        agent_type: str,
        task: str,
        context: Dict[str, Any] = {},
        tools: Optional[List[str]] = None,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent execution steps"""
        
        # Simplified streaming - yield thought/action/observation steps
        yield {"type": "thought", "content": f"Starting {agent_type} agent for task: {task}"}
        
        # Get system prompt for agent type
        system_prompt = self._get_system_prompt(agent_type)
        
        # Call LLM with streaming
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}"}
        ]
        
        # Add available tools
        available_tools = self._get_tools_for_agent(agent_type, tools)
        
        yield {"type": "action", "content": "Analyzing task and planning approach..."}
        
        # Stream the response
        full_response = ""
        async for chunk in self.llm_client.stream_chat_completion(
            messages=messages,
            tools=available_tools if available_tools else None
        ):
            delta = chunk.get("delta", {})
            if content := delta.get("content"):
                full_response += content
                yield {"type": "stream", "content": content}
        
        yield {"type": "result", "content": full_response}
    
    def _build_agent_graph(self, agent_type: str, tools: Optional[List[str]] = None) -> StateGraph:
        """Build a LangGraph for the specified agent type"""
        
        # Create graph
        graph = StateGraph(AgentState)
        
        # Add nodes based on agent type
        if agent_type == "code":
            graph.add_node("plan", self._code_plan_node)
            graph.add_node("execute", self._code_execute_node)
            graph.add_node("review", self._code_review_node)
            
            graph.set_entry_point("plan")
            graph.add_edge("plan", "execute")
            graph.add_edge("execute", "review")
            graph.add_edge("review", END)
            
        elif agent_type == "research":
            graph.add_node("search", self._research_search_node)
            graph.add_node("summarize", self._research_summarize_node)
            
            graph.set_entry_point("search")
            graph.add_edge("search", "summarize")
            graph.add_edge("summarize", END)
            
        else:
            # Default simple agent
            graph.add_node("process", self._default_process_node)
            graph.set_entry_point("process")
            graph.add_edge("process", END)
        
        return graph.compile()
    
    async def _code_plan_node(self, state: AgentState) -> AgentState:
        """Plan the coding task"""
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a coding expert. Plan how to complete the coding task."},
                {"role": "user", "content": f"Plan how to: {state['task']}"}
            ],
            max_tokens=1024
        )
        state["plan"] = response["choices"][0]["message"]["content"]
        state["iterations"] += 1
        return state
    
    async def _code_execute_node(self, state: AgentState) -> AgentState:
        """Execute the coding task"""
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a coding expert. Write clean, well-documented code."},
                {"role": "user", "content": f"Task: {state['task']}\n\nPlan: {state.get('plan', '')}\n\nWrite the code:"}
            ],
            max_tokens=4096
        )
        state["code"] = response["choices"][0]["message"]["content"]
        state["iterations"] += 1
        return state
    
    async def _code_review_node(self, state: AgentState) -> AgentState:
        """Review and finalize the code"""
        code = state.get("code", "")
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "Review the code, fix any issues, and provide the final version."},
                {"role": "user", "content": f"Review this code:\n\n{code}"}
            ],
            max_tokens=4096
        )
        state["output"] = response["choices"][0]["message"]["content"]
        state["iterations"] += 1
        return state
    
    async def _research_search_node(self, state: AgentState) -> AgentState:
        """Search for information"""
        # Simulated search - in production, call actual search tools
        state["search_results"] = f"Research findings for: {state['task']}"
        state["iterations"] += 1
        return state
    
    async def _research_summarize_node(self, state: AgentState) -> AgentState:
        """Summarize research findings"""
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "Summarize the research findings clearly."},
                {"role": "user", "content": f"Task: {state['task']}\n\nFindings: {state.get('search_results', '')}"}
            ],
            max_tokens=2048
        )
        state["output"] = response["choices"][0]["message"]["content"]
        state["iterations"] += 1
        return state
    
    async def _default_process_node(self, state: AgentState) -> AgentState:
        """Default processing node"""
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": state["task"]}
            ],
            max_tokens=4096
        )
        state["output"] = response["choices"][0]["message"]["content"]
        state["iterations"] += 1
        return state
    
    def _get_system_prompt(self, agent_type: str) -> str:
        """Get system prompt for agent type"""
        prompts = {
            "code": """You are an expert coding assistant. You can:
- Write clean, efficient, and well-documented code
- Debug and fix issues
- Refactor and optimize code
- Explain code and concepts
Always provide complete, working code with proper error handling.""",

            "research": """You are a research assistant. You can:
- Search for information
- Analyze and summarize content
- Extract key insights
- Provide citations and sources
Be thorough and accurate in your research.""",

            "file": """You are a file management assistant. You can:
- List and navigate directories
- Read and write files
- Organize project structures
- Search for files by pattern
Be careful with file operations and always confirm destructive actions.""",

            "custom": """You are a versatile AI assistant with access to various tools.
Complete the user's task efficiently and accurately."""
        }
        return prompts.get(agent_type, prompts["custom"])
    
    def _get_tools_for_agent(self, agent_type: str, custom_tools: Optional[List[str]] = None) -> List[Dict]:
        """Get available tools for an agent type"""
        all_tools = {
            "execute_code": {
                "type": "function",
                "function": {
                    "name": "execute_code",
                    "description": "Execute Python code in a sandboxed environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"]
                    }
                }
            },
            "read_file": {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    }
                }
            },
            "write_file": {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            "web_search": {
                "type": "function", 
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        }
        
        agent_tools = {
            "code": ["execute_code", "read_file", "write_file"],
            "research": ["web_search", "read_file"],
            "file": ["read_file", "write_file"],
            "custom": list(all_tools.keys())
        }
        
        tool_names = custom_tools or agent_tools.get(agent_type, [])
        return [all_tools[t] for t in tool_names if t in all_tools]
