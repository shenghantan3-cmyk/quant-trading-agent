"""FastAPI主应用"""
from fastapi import FastAPI

app = FastAPI(
    title="Quant Trading Agent",
    description="Agent-based Quantitative Trading System",
    version="0.1.0"
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/agents")
async def list_agents():
    return {"agents": ["DataAgent", "FactorAgent", "DecisionAgent", "RiskAgent", "TradeAgent"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
