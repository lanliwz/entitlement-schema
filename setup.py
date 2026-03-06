from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent.resolve()


def read_text(path: str, default: str = "") -> str:
    file_path = ROOT / path
    return file_path.read_text(encoding="utf-8").strip() if file_path.exists() else default


setup(
    name="entitlement-schema",
    version=read_text("VERSION", "0.0.0"),
    description="Policy-driven entitlement schema demo for relational databases with Neo4j governance.",
    long_description=read_text("README.md", ""),
    long_description_content_type="text/markdown",
    author="Onto2AI",
    license="MIT",
    python_requires=">=3.11",
    packages=find_packages(
        exclude=(
            "dist",
            "dist.*",
            "venv",
            "venv.*",
            "resource",
            "resource.*",
        )
    ),
    include_package_data=True,
    install_requires=[
        "langgraph>=0.2.33",
        "langchain>=1.2.0",
        "langchain-openai>=0.3.0",
        "neo4j",
        "sqlglot",
        "mysql-connector-python",
        "jaydebeapi",
        "datahub",
        "fastapi",
        "uvicorn[standard]",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
