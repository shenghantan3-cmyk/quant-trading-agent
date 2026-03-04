"""增强版决策Agent - 集成Kimi LLM进行智能分析"""
from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.llm.kimi_llm import KimiLLM

class EnhancedDecisionAgent(BaseAgent):
    """增强的决策Agent - 支持LLM智能分析"""
    
    def __init__(self, use_llm: bool = True):
        super().__init__("EnhancedDecisionAgent")
        self.use_llm = use_llm
        self.llm = KimiLLM() if use_llm else None
        
        # 因子权重配置
        self.factor_weights = {
            "rsi": 0.3,
            "macd": 0.4,
            "ma": 0.2,
            "volatility": 0.1
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强的决策逻辑：数学评分 + LLM分析
        input: {
            "factors": {...},
            "threshold": 0.6,
            "use_llm_analysis": True
        }
        """
        factors = input_data.get("factors", {})
        threshold = input_data.get("threshold", 0.6)
        use_llm = input_data.get("use_llm_analysis", self.use_llm)
        
        if not factors:
            return {"status": "failed", "error": "No factors provided"}
        
        try:
            # 第一步：数学评分
            signals = []
            scores = {}
            
            for code, factor_values in factors.items():
                if not isinstance(factor_values, dict):
                    continue
                
                score = self.calculate_score(factor_values)
                scores[code] = score
                
                # 生成初始信号
                if score >= threshold:
                    action = "BUY"
                elif score <= (1 - threshold):
                    action = "SELL"
                else:
                    action = "HOLD"
                
                signal = {
                    "code": code,
                    "action": action,
                    "score": score,
                    "confidence": min(score, 1.0) if action == "BUY" else (1 - score if action == "SELL" else 0),
                    "factors": factor_values
                }
                
                signals.append(signal)
            
            result = {
                "status": "success",
                "signals": signals,
                "scores": scores,
                "buy_signals": [s for s in signals if s["action"] == "BUY"],
                "sell_signals": [s for s in signals if s["action"] == "SELL"],
                "method": "mathematical"
            }
            
            # 第二步：如果启用LLM，进行深层分析
            if use_llm and self.llm and signals:
                llm_result = self.llm.analyze_signals(signals)
                result["llm_analysis"] = llm_result
                result["method"] = "mathematical + llm"
            
            self.set_state("signals", result)
            return result
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def calculate_score(self, factors: Dict[str, Any]) -> float:
        """计算综合评分 (0-1)"""
        score = 0.5
        
        # RSI评分
        if "rsi" in factors:
            rsi = factors["rsi"]
            rsi_score = (rsi - 30) / 40
            rsi_score = max(0, min(1, rsi_score))
            score += rsi_score * self.factor_weights["rsi"] / 0.5
        
        # MACD评分
        if "macd" in factors:
            macd_data = factors["macd"]
            if isinstance(macd_data, dict):
                macd = macd_data.get("macd", 0)
                macd_score = 0.5 + (0.5 if macd > 0 else -0.5)
                score += macd_score * self.factor_weights["macd"] / 0.5
        
        # MA评分
        if "ma_5" in factors and "ma_20" in factors:
            ma_score = 0.5 + (0.5 if factors["ma_5"] > factors["ma_20"] else -0.5)
            score += ma_score * self.factor_weights["ma"] / 0.5
        
        score = max(0, min(1, score / 2))
        return round(score, 3)
