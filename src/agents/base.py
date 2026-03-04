"""基础Agent类"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.state = {}
    
    def set_state(self, key: str, value: Any):
        """设置Agent状态"""
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None):
        """获取Agent状态"""
        return self.state.get(key, default)
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
