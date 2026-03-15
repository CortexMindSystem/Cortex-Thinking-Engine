"""
CortexOS – setup.py
Install with: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="cortex-os",
    version="0.1.0",
    description="CortexOS: Your operating system for thinking",
    author="Pierre-Henry Soria",
    author_email="hi@ph7.me",
    url="https://github.com/pH-7/CortexOSLLM",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.0",
    ],
    extras_require={
        "openai": ["openai>=1.10.0"],
        "anthropic": ["anthropic>=0.18.0"],
        "all": ["openai>=1.10.0", "anthropic>=0.18.0"],
        "dev": ["pytest", "httpx", "ruff"],
    },
    entry_points={
        "console_scripts": [
            "cortexos=cortex_core.api.server:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
