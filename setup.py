from setuptools import setup, find_packages

setup(
    name="quant-trading-agent",
    version="0.1.0",
    description="Agent-based Quantitative Trading System",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=open("requirements.txt").readlines(),
)
