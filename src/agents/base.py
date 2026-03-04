"""基础Agent类"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.state = {}
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
