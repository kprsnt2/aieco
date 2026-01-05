"""
AIEco - Skills Framework
Anthropic-style skills system for teaching AI specialized tasks
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class Skill:
    """Represents a skill that can be loaded by agents"""
    name: str
    description: str
    instructions: str
    examples: List[str] = None
    guidelines: List[str] = None
    tools: List[str] = None
    version: str = "1.0.0"
    author: str = None
    tags: List[str] = None
    path: str = None
    
    def to_prompt(self) -> str:
        """Convert skill to a prompt that can be injected into agent context"""
        prompt_parts = [
            f"# Skill: {self.name}",
            f"\n{self.description}\n",
            "## Instructions",
            self.instructions
        ]
        
        if self.examples:
            prompt_parts.append("\n## Examples")
            for example in self.examples:
                prompt_parts.append(f"- {example}")
        
        if self.guidelines:
            prompt_parts.append("\n## Guidelines")
            for guideline in self.guidelines:
                prompt_parts.append(f"- {guideline}")
        
        return "\n".join(prompt_parts)


class SkillLoader:
    """
    Loads and manages skills from SKILL.md files.
    
    Skills are folders containing:
    - SKILL.md: Main skill definition with YAML frontmatter
    - Optional supporting files (templates, examples, scripts)
    """
    
    def __init__(self, skills_dir: str = None):
        self.skills_dir = Path(skills_dir or "skills")
        self._cache: Dict[str, Skill] = {}
        self._reload_needed = True
    
    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """Load a skill from a SKILL.md file"""
        skill_file = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
        
        if not skill_file.exists():
            logger.warning(f"Skill file not found: {skill_file}")
            return None
        
        try:
            content = skill_file.read_text(encoding="utf-8")
            
            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    instructions = parts[2].strip()
                else:
                    logger.warning(f"Invalid SKILL.md format: {skill_file}")
                    return None
            else:
                # No frontmatter, treat as pure markdown
                frontmatter = {}
                instructions = content
            
            # Extract examples and guidelines from instructions
            examples = self._extract_section(instructions, "Examples")
            guidelines = self._extract_section(instructions, "Guidelines")
            
            skill = Skill(
                name=frontmatter.get("name", skill_path.name),
                description=frontmatter.get("description", ""),
                instructions=instructions,
                examples=examples,
                guidelines=guidelines,
                tools=frontmatter.get("tools", []),
                version=frontmatter.get("version", "1.0.0"),
                author=frontmatter.get("author"),
                tags=frontmatter.get("tags", []),
                path=str(skill_path)
            )
            
            logger.info(f"✅ Loaded skill: {skill.name}")
            return skill
            
        except Exception as e:
            logger.error(f"❌ Failed to load skill: {skill_file}", error=str(e))
            return None
    
    def _extract_section(self, text: str, section_name: str) -> List[str]:
        """Extract bullet points from a markdown section"""
        import re
        pattern = rf"##\s*{section_name}\s*\n((?:[-*]\s+.+\n?)+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            items = re.findall(r"[-*]\s+(.+)", match.group(1))
            return items
        return []
    
    def load_all_skills(self) -> Dict[str, Skill]:
        """Load all skills from the skills directory"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return {}
        
        skills = {}
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skill = self.load_skill(item)
                if skill:
                    skills[skill.name] = skill
        
        self._cache = skills
        self._reload_needed = False
        logger.info(f"📚 Loaded {len(skills)} skills")
        return skills
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        if self._reload_needed:
            self.load_all_skills()
        return self._cache.get(name)
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills"""
        if self._reload_needed:
            self.load_all_skills()
        
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "tags": skill.tags,
                "version": skill.version
            }
            for skill in self._cache.values()
        ]
    
    def get_skills_for_task(self, task: str, tags: List[str] = None) -> List[Skill]:
        """Find skills relevant to a task"""
        if self._reload_needed:
            self.load_all_skills()
        
        relevant = []
        task_lower = task.lower()
        
        for skill in self._cache.values():
            # Match by tags
            if tags and skill.tags:
                if any(t in skill.tags for t in tags):
                    relevant.append(skill)
                    continue
            
            # Match by description keywords
            if skill.description and any(
                word in skill.description.lower() 
                for word in task_lower.split()
            ):
                relevant.append(skill)
        
        return relevant


class SkillRegistry:
    """
    Central registry for managing skills across the application.
    Supports dynamic skill loading and hot-reloading.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loader = SkillLoader()
            cls._instance._active_skills: Dict[str, Skill] = {}
        return cls._instance
    
    def activate_skill(self, name: str) -> bool:
        """Activate a skill for use"""
        skill = self._loader.get_skill(name)
        if skill:
            self._active_skills[name] = skill
            return True
        return False
    
    def deactivate_skill(self, name: str) -> bool:
        """Deactivate a skill"""
        if name in self._active_skills:
            del self._active_skills[name]
            return True
        return False
    
    def get_active_skills_prompt(self) -> str:
        """Get combined prompt from all active skills"""
        if not self._active_skills:
            return ""
        
        prompts = [
            "# Active Skills\n",
            "The following skills are currently active and should guide your responses:\n"
        ]
        
        for skill in self._active_skills.values():
            prompts.append(skill.to_prompt())
            prompts.append("\n---\n")
        
        return "\n".join(prompts)
    
    def list_all_skills(self) -> List[Dict]:
        """List all available skills"""
        return self._loader.list_skills()
    
    def list_active_skills(self) -> List[str]:
        """List currently active skills"""
        return list(self._active_skills.keys())


# Global registry instance
skill_registry = SkillRegistry()


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry"""
    return skill_registry
