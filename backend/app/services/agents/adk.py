"""
AIEco - Google ADK-Inspired Agent Framework
Multi-agent orchestration with Sequential, Parallel, and Loop workflows
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import asyncio
import structlog

logger = structlog.get_logger()


class AgentType(str, Enum):
    """Types of agents in the ADK framework"""
    LLM = "llm"           # LLM-powered agent
    SEQUENTIAL = "sequential"  # Run sub-agents in sequence
    PARALLEL = "parallel"      # Run sub-agents in parallel
    LOOP = "loop"             # Run agent in a loop until condition
    ROUTER = "router"         # Route to different agents based on input


@dataclass
class AgentContext:
    """Context passed between agents during execution"""
    input: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    parent_agent: str = None
    depth: int = 0
    max_depth: int = 10
    
    def with_input(self, new_input: str) -> "AgentContext":
        """Create new context with different input"""
        return AgentContext(
            input=new_input,
            history=self.history.copy(),
            variables=self.variables.copy(),
            parent_agent=self.parent_agent,
            depth=self.depth,
            max_depth=self.max_depth
        )
    
    def add_to_history(self, agent_name: str, output: str):
        """Add agent output to history"""
        self.history.append({
            "agent": agent_name,
            "output": output
        })


@dataclass
class AgentResult:
    """Result from agent execution"""
    output: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_results: List["AgentResult"] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all agents in the ADK framework.
    
    Agents can be composed hierarchically to create complex workflows.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        tools: List[Dict] = None,
        sub_agents: List["BaseAgent"] = None
    ):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.sub_agents = sub_agents or []
    
    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent with given context"""
        pass
    
    async def stream(self, context: AgentContext) -> AsyncGenerator[Dict, None]:
        """Stream agent execution (default: run and yield final result)"""
        result = await self.run(context)
        yield {"type": "result", "content": result.output}
    
    def add_tool(self, tool: Dict):
        """Add a tool to this agent"""
        self.tools.append(tool)
    
    def add_sub_agent(self, agent: "BaseAgent"):
        """Add a sub-agent"""
        self.sub_agents.append(agent)


class LLMAgent(BaseAgent):
    """
    LLM-powered agent that uses a language model for reasoning.
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str = "",
        llm_client = None,
        model: str = None,
        **kwargs
    ):
        super().__init__(name, **kwargs)
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.model = model
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Run the LLM agent"""
        if not self.llm_client:
            from app.core.llm import get_llm_client
            self.llm_client = get_llm_client()
        
        # Build messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add history context
        if context.history:
            history_text = "\n".join([
                f"[{h['agent']}]: {h['output']}" 
                for h in context.history[-5:]  # Last 5 entries
            ])
            messages.append({
                "role": "system", 
                "content": f"Previous agent outputs:\n{history_text}"
            })
        
        messages.append({"role": "user", "content": context.input})
        
        try:
            response = await self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                tools=self.tools if self.tools else None
            )
            
            output = response["choices"][0]["message"]["content"]
            context.add_to_history(self.name, output)
            
            return AgentResult(output=output, success=True)
            
        except Exception as e:
            logger.error(f"LLM agent error: {e}")
            return AgentResult(output="", success=False, error=str(e))
    
    async def stream(self, context: AgentContext) -> AsyncGenerator[Dict, None]:
        """Stream LLM response"""
        if not self.llm_client:
            from app.core.llm import get_llm_client
            self.llm_client = get_llm_client()
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context.input}
        ]
        
        full_output = ""
        async for chunk in self.llm_client.stream_chat_completion(
            messages=messages,
            model=self.model
        ):
            content = chunk.get("delta", {}).get("content", "")
            if content:
                full_output += content
                yield {"type": "stream", "content": content}
        
        context.add_to_history(self.name, full_output)
        yield {"type": "done", "content": full_output}


class SequentialAgent(BaseAgent):
    """
    Runs sub-agents in sequence, passing output to next agent.
    
    Example:
        planner = LLMAgent("planner", "Plan the task...")
        executor = LLMAgent("executor", "Execute the plan...")
        reviewer = LLMAgent("reviewer", "Review the result...")
        
        pipeline = SequentialAgent(
            "task-pipeline",
            sub_agents=[planner, executor, reviewer]
        )
    """
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Run agents in sequence"""
        results = []
        current_input = context.input
        
        for agent in self.sub_agents:
            logger.info(f"🔄 Sequential: Running {agent.name}")
            
            sub_context = context.with_input(current_input)
            result = await agent.run(sub_context)
            results.append(result)
            
            if not result.success:
                return AgentResult(
                    output="",
                    success=False,
                    error=f"Agent {agent.name} failed: {result.error}",
                    sub_results=results
                )
            
            # Pass output to next agent
            current_input = result.output
            context.add_to_history(agent.name, result.output)
        
        return AgentResult(
            output=current_input,
            success=True,
            sub_results=results
        )


class ParallelAgent(BaseAgent):
    """
    Runs sub-agents in parallel and combines results.
    
    Example:
        researcher = LLMAgent("researcher", "Research the topic...")
        analyst = LLMAgent("analyst", "Analyze the data...")
        
        parallel = ParallelAgent(
            "multi-perspective",
            sub_agents=[researcher, analyst],
            combiner=lambda results: "\n\n".join(r.output for r in results)
        )
    """
    
    def __init__(
        self, 
        name: str, 
        combiner: Callable[[List[AgentResult]], str] = None,
        **kwargs
    ):
        super().__init__(name, **kwargs)
        self.combiner = combiner or self._default_combiner
    
    def _default_combiner(self, results: List[AgentResult]) -> str:
        """Default: concatenate outputs"""
        return "\n\n---\n\n".join(r.output for r in results if r.success)
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Run agents in parallel"""
        logger.info(f"⚡ Parallel: Running {len(self.sub_agents)} agents")
        
        tasks = []
        for agent in self.sub_agents:
            sub_context = context.with_input(context.input)
            tasks.append(agent.run(sub_context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    output="",
                    success=False,
                    error=str(result)
                ))
            else:
                agent_results.append(result)
        
        # Combine results
        combined = self.combiner(agent_results)
        
        return AgentResult(
            output=combined,
            success=all(r.success for r in agent_results),
            sub_results=agent_results
        )


class LoopAgent(BaseAgent):
    """
    Runs an agent in a loop until a condition is met.
    
    Example:
        refiner = LLMAgent("refiner", "Improve the code...")
        
        loop = LoopAgent(
            "iterative-refinement",
            agent=refiner,
            max_iterations=5,
            stop_condition=lambda result: "DONE" in result.output
        )
    """
    
    def __init__(
        self,
        name: str,
        agent: BaseAgent = None,
        max_iterations: int = 5,
        stop_condition: Callable[[AgentResult], bool] = None,
        **kwargs
    ):
        super().__init__(name, **kwargs)
        self.agent = agent
        self.max_iterations = max_iterations
        self.stop_condition = stop_condition or (lambda r: False)
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Run agent in a loop"""
        results = []
        current_input = context.input
        
        for i in range(self.max_iterations):
            logger.info(f"🔁 Loop iteration {i + 1}/{self.max_iterations}")
            
            sub_context = context.with_input(current_input)
            result = await self.agent.run(sub_context)
            results.append(result)
            
            if not result.success:
                break
            
            if self.stop_condition(result):
                logger.info(f"✅ Loop stopped: condition met at iteration {i + 1}")
                break
            
            current_input = result.output
        
        return AgentResult(
            output=results[-1].output if results else "",
            success=results[-1].success if results else False,
            metadata={"iterations": len(results)},
            sub_results=results
        )


class RouterAgent(BaseAgent):
    """
    Routes to different agents based on input classification.
    
    Example:
        router = RouterAgent(
            "task-router",
            routes={
                "code": code_agent,
                "research": research_agent,
                "general": general_agent
            },
            classifier=lambda input: "code" if "code" in input.lower() else "general"
        )
    """
    
    def __init__(
        self,
        name: str,
        routes: Dict[str, BaseAgent] = None,
        classifier: Callable[[str], str] = None,
        default_route: str = None,
        **kwargs
    ):
        super().__init__(name, **kwargs)
        self.routes = routes or {}
        self.classifier = classifier
        self.default_route = default_route
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Route to appropriate agent"""
        if self.classifier:
            route_key = self.classifier(context.input)
        else:
            route_key = self.default_route
        
        if route_key not in self.routes:
            route_key = self.default_route
        
        if not route_key or route_key not in self.routes:
            return AgentResult(
                output="",
                success=False,
                error=f"No route found for input"
            )
        
        agent = self.routes[route_key]
        logger.info(f"🔀 Router: Directing to {agent.name}")
        
        return await agent.run(context)


# ===== Agent Builder =====

class AgentBuilder:
    """
    Fluent builder for creating agents.
    
    Example:
        agent = (AgentBuilder("my-agent")
            .with_system_prompt("You are a helpful assistant")
            .with_tool(calculator_tool)
            .with_sub_agent(helper_agent)
            .build())
    """
    
    def __init__(self, name: str, agent_type: AgentType = AgentType.LLM):
        self.name = name
        self.agent_type = agent_type
        self._config = {}
    
    def with_system_prompt(self, prompt: str) -> "AgentBuilder":
        self._config["system_prompt"] = prompt
        return self
    
    def with_description(self, desc: str) -> "AgentBuilder":
        self._config["description"] = desc
        return self
    
    def with_tool(self, tool: Dict) -> "AgentBuilder":
        if "tools" not in self._config:
            self._config["tools"] = []
        self._config["tools"].append(tool)
        return self
    
    def with_sub_agent(self, agent: BaseAgent) -> "AgentBuilder":
        if "sub_agents" not in self._config:
            self._config["sub_agents"] = []
        self._config["sub_agents"].append(agent)
        return self
    
    def with_llm_client(self, client) -> "AgentBuilder":
        self._config["llm_client"] = client
        return self
    
    def with_model(self, model: str) -> "AgentBuilder":
        self._config["model"] = model
        return self
    
    def build(self) -> BaseAgent:
        """Build the agent"""
        if self.agent_type == AgentType.LLM:
            return LLMAgent(self.name, **self._config)
        elif self.agent_type == AgentType.SEQUENTIAL:
            return SequentialAgent(self.name, **self._config)
        elif self.agent_type == AgentType.PARALLEL:
            return ParallelAgent(self.name, **self._config)
        elif self.agent_type == AgentType.LOOP:
            return LoopAgent(self.name, **self._config)
        elif self.agent_type == AgentType.ROUTER:
            return RouterAgent(self.name, **self._config)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")
