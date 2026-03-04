# 量化交易智能体系统 | Quant Trading Agent System

基于LangChain的分布式多智能体量化交易平台

## 架构

```
┌─────────────────────────────────────────┐
│        FastAPI Gateway / REST API        │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐  ┌─────▼─────┐  ┌──▼──────┐
│ 数据获取  │  因子选取   │  │决策评分  │
│ Agent   │  Agent     │  │ Agent   │
└─────┬──┘  └─────┬─────┘  └──┬──────┘
      │           │           │
      └───────────┼───────────┘
                  │
          ┌───────▼────────┐
          │  风控校验Agent │
          └───────┬────────┘
                  │
          ┌───────▼────────┐
          │ 交易执行Agent  │
          └───────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼──┐         ┌─────▼──┐
    │ Redis │         │MongoDB  │
    └───────┘         └─────────┘
```

## 核心模块

- **DataAgent**: 实时行情数据获取（tushare API）
- **FactorAgent**: 技术指标 + 基本面因子计算
- **DecisionAgent**: 多因子评分与信号生成
- **RiskAgent**: 风险控制与头寸管理
- **TradeAgent**: 模拟/实盘交易执行
- **Workflow Engine**: 动态工作流编排

## 快速开始

```bash
# 1. 环境设置
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 2. 配置
cp config/example.env config/.env
# 编辑 .env 填入 tushare token 等

# 3. 启动
python -m src.main

# 4. API测试
curl http://localhost:8000/health
```

## 开发进度

- [ ] 基础架构 & Agent框架
- [ ] 数据获取Agent
- [ ] 因子计算Agent
- [ ] 决策Agent
- [ ] 风控Agent
- [ ] 交易Agent
- [ ] FastAPI网关
- [ ] Docker部署
- [ ] 文档和测试

## 技术栈

- **后端**: Python 3.11+ / FastAPI / asyncio
- **Agent框架**: LangChain
- **数据源**: tushare API
- **数据库**: Redis / MongoDB
- **部署**: Docker / Docker Compose

## 贡献指南

欢迎PR和Issue！

