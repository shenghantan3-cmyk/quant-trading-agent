"""决策Agent - 基于因子评分生成交易信号"""
from typing import Dict, Any, List
from src.agents.base import BaseAgent

class DecisionAgent(BaseAgent):
    """决策评分Agent - 多因子信号生成"""
    
    def __init__(self):
        super().__init__("DecisionAgent")
        # 因子权重配置
        self.factor_weights = {
            "rsi": 0.3,
            "macd": 0.4,
            "ma": 0.2,
            "volatility": 0.1
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成决策信号
        input: {
            "factors": {...},  # 来自FactorAgent的因子
            "threshold": 0.6
        }
        """
        factors = input_data.get("factors", {})
        threshold = input_data.get("threshold", 0.6)
        
        if not factors:
            return {"status": "failed", "error": "No factors provided"}
        
        try:
            signals = []
            scores = {}
            
            for code, factor_values in factors.items():
                if not isinstance(factor_values, dict):
                    continue
                
                # 计算综合评分
                score = self.calculate_score(factor_values)
                scores[code] = score
                
                # 生成交易信号
                if score >= threshold:
                    signal = {
                        "code": code,
                        "action": "BUY",
                        "score": score,
                        "confidence": min(score, 1.0),
                        "factors": factor_values
                    }
                elif score <= (1 - threshold):
                    signal = {
                        "code": code,
                        "action": "SELL",
                        "score": score,
                        "confidence": abs(score - 1),
                        "factors": factor_values
                    }
                else:
                    signal = {
                        "code": code,
                        "action": "HOLD",
                        "score": score,
                        "confidence": 0,
                        "factors": factor_values
                    }
                
                signals.append(signal)
            
            result = {
                "status": "success",
                "signals": signals,
                "scores": scores,
                "buy_signals": [s for s in signals if s["action"] == "BUY"],
                "sell_signals": [s for s in signals if s["action"] == "SELL"],
                "threshold": threshold
            }
            
            self.set_state("signals", result)
            return result
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def calculate_score(self, factors: Dict[str, Any]) -> float:
        """计算综合评分 (0-1)"""
        score = 0.5  # 初始中性值
        
        # RSI评分 (0-100)
        if "rsi" in factors:
            rsi = factors["rsi"]
            rsi_score = (rsi - 30) / 40  # 30-70为评分区间
            rsi_score = max(0, min(1, rsi_score))  # 限制在0-1之间
            score += rsi_score * self.factor_weights["rsi"] / 0.5
        
        # MACD评分
        if "macd" in factors:
            macd_data = factors["macd"]
            if isinstance(macd_data, dict):
                macd = macd_data.get("macd", 0)
                # macd > 0为看多信号
                macd_score = 0.5 + (0.5 if macd > 0 else -0.5)
                score += macd_score * self.factor_weights["macd"] / 0.5
        
        # MA评分
        if "ma_5" in factors and "ma_20" in factors:
            ma_score = 0.5 + (0.5 if factors["ma_5"] > factors["ma_20"] else -0.5)
            score += ma_score * self.factor_weights["ma"] / 0.5
        
        # 限制在0-1范围
        score = max(0, min(1, score / 2))
        
        return round(score, 3)
