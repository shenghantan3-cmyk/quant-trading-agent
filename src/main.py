"""FastAPI主应用 - 量化交易系统网关"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from src.agents.data_agent import DataAgent
from src.agents.factor_agent import FactorAgent
from src.agents.decision_agent import DecisionAgent

app = FastAPI(
    title="Quant Trading Agent System",
    description="基于LangChain的分布式多智能体量化交易平台",
    version="0.1.0"
)

# 初始化所有Agent
data_agent = DataAgent()
factor_agent = FactorAgent()
decision_agent = DecisionAgent()

# 请求/响应模型
class StockRequest(BaseModel):
    codes: List[str]
    start_date: str
    end_date: str
    data_type: str = "daily"

class AnalysisRequest(BaseModel):
    codes: List[str]
    start_date: str
    end_date: str
    factors: List[str] = ["rsi", "macd", "ma"]
    threshold: float = 0.6

# ============ 健康检查 ============
@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Quant Trading Agent",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }

# ============ 数据API ============
@app.get("/stocks/list")
async def get_stock_list():
    """获取A股列表"""
    result = await data_agent.get_stock_list()
    return result

@app.post("/data/fetch")
async def fetch_data(request: StockRequest):
    """获取股票数据"""
    try:
        result = await data_agent.execute({
            "codes": request.codes,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "data_type": request.data_type
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{code}")
async def get_daily_data(code: str, days: int = 30):
    """获取某股票的日线数据"""
    try:
        result = await data_agent.get_daily_data(code, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ 分析API ============
@app.post("/analysis/factors")
async def analyze_factors(request: StockRequest):
    """计算技术因子"""
    try:
        # 第一步：获取数据
        data_result = await data_agent.execute({
            "codes": request.codes,
            "start_date": request.start_date,
            "end_date": request.end_date
        })
        
        if data_result["status"] != "success":
            raise Exception("Failed to fetch data")
        
        # 第二步：计算因子
        factor_result = await factor_agent.execute({
            "data": data_result["data"],
            "factors": ["rsi", "macd", "ma", "volatility"]
        })
        
        return factor_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/signals")
async def generate_signals(request: AnalysisRequest):
    """完整分析流程：数据 -> 因子 -> 信号"""
    try:
        # 第一步：获取数据
        data_result = await data_agent.execute({
            "codes": request.codes,
            "start_date": request.start_date,
            "end_date": request.end_date
        })
        
        if data_result["status"] != "success":
            raise Exception("Failed to fetch data")
        
        # 第二步：计算因子
        factor_result = await factor_agent.execute({
            "data": data_result["data"],
            "factors": request.factors
        })
        
        if factor_result["status"] != "success":
            raise Exception("Failed to calculate factors")
        
        # 第三步：生成信号
        signal_result = await decision_agent.execute({
            "factors": factor_result["factor_values"],
            "threshold": request.threshold
        })
        
        return {
            "status": "success",
            "pipeline": "DATA -> FACTORS -> SIGNALS",
            "data": data_result,
            "factors": factor_result,
            "signals": signal_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ Agent状态查询 ============
@app.get("/agents")
async def list_agents():
    """列出所有Agent及其状态"""
    return {
        "agents": [
            {
                "name": "DataAgent",
                "status": "active",
                "description": "数据获取Agent"
            },
            {
                "name": "FactorAgent",
                "status": "active",
                "description": "因子计算Agent"
            },
            {
                "name": "DecisionAgent",
                "status": "active",
                "description": "决策信号Agent"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
