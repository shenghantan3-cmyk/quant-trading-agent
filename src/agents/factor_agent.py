"""因子选取Agent - 计算技术指标和基本面因子"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.agents.base import BaseAgent

class FactorAgent(BaseAgent):
    """因子计算Agent - 技术指标计算"""
    
    def __init__(self):
        super().__init__("FactorAgent")
        self.factors = {}
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算因子
        input: {
            "data": [...],  # 来自DataAgent的行情数据
            "factors": ["rsi", "macd", "ma", "volatility"]
        }
        """
        data = input_data.get("data", [])
        factors_to_calc = input_data.get("factors", ["rsi", "macd"])
        
        if not data:
            return {"status": "failed", "error": "No data provided"}
        
        try:
            result = {
                "status": "success",
                "factors_calculated": factors_to_calc,
                "factor_values": {}
            }
            
            for item in data:
                code = item.get("code")
                df = pd.DataFrame(item.get("data", []))
                
                if df.empty:
                    continue
                
                factors = {}
                
                # 转换列名为数字格式以便计算
                df['close'] = pd.to_numeric(df.get('close', 0))
                df['high'] = pd.to_numeric(df.get('high', 0))
                df['low'] = pd.to_numeric(df.get('low', 0))
                df['vol'] = pd.to_numeric(df.get('vol', 0))
                
                # RSI (相对强度指标)
                if "rsi" in factors_to_calc:
                    factors["rsi"] = self.calculate_rsi(df['close'].values)
                
                # MACD
                if "macd" in factors_to_calc:
                    factors["macd"] = self.calculate_macd(df['close'].values)
                
                # 移动平均线
                if "ma" in factors_to_calc:
                    factors["ma_5"] = df['close'].rolling(5).mean().iloc[-1]
                    factors["ma_20"] = df['close'].rolling(20).mean().iloc[-1]
                
                # 波动率
                if "volatility" in factors_to_calc:
                    factors["volatility"] = df['close'].pct_change().std()
                
                result["factor_values"][code] = factors
            
            self.set_state("factors", result)
            return result
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period:
            return 0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_macd(self, prices: np.ndarray) -> Dict[str, float]:
        """计算MACD指标"""
        ema12 = self.calculate_ema(prices, 12)
        ema26 = self.calculate_ema(prices, 26)
        
        macd = ema12 - ema26
        signal = self.calculate_ema(np.array([macd]) if isinstance(macd, (int, float)) else np.array([macd]), 9)
        histogram = macd - signal
        
        return {
            "macd": round(macd, 4),
            "signal": round(signal, 4),
            "histogram": round(histogram, 4)
        }
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """计算EMA"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[:period].mean()
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return round(ema, 4)
