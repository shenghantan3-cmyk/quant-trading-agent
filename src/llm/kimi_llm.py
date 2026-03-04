"""LLM集成模块 - 使用Kimi 2.5进行智能决策"""
import httpx
import json
from typing import Dict, Any, List
from src.config import settings

class KimiLLM:
    """Moonshot Kimi LLM集成"""
    
    def __init__(self):
        self.api_key = settings.moonshot_api_key
        self.model = "moonshot-v1-8k"
        self.base_url = "https://api.moonshot.cn/v1"
    
    def analyze_signals(self, signals: List[Dict]) -> Dict[str, Any]:
        """
        用Kimi分析交易信号
        输入: 交易信号列表
        输出: AI分析意见
        """
        prompt = f"""你是一个专业的量化交易分析师。基于以下交易信号，给出分析意见：

交易信号：
{json.dumps(signals, ensure_ascii=False, indent=2)}

请分析：
1. 这些信号的可信度如何？
2. 整体的交易方向是什么？
3. 有什么风险需要注意？
4. 推荐的操作是什么？

请用JSON格式返回分析结果。"""
        
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return {
                    "status": "success",
                    "analysis": content,
                    "model": self.model
                }
            else:
                return {
                    "status": "failed",
                    "error": f"API error: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
