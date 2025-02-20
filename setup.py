from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="personal-assistant-rlhf",
    version="1.0.0",
    author="Personal Assistant Team",
    author_email="contact@example.com",
    description="Hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/github-303/personal-assistant-rlhf",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "numpy>=1.22.0",
        "PyYAML>=6.0",
        "tqdm>=4.64.0",
        "rich>=12.0.0",
        "argparse>=1.4.0",
        "python-dotenv>=0.20.0",
        "pydantic>=1.9.0",
        "colorlog>=6.7.0",
    ],
    entry_points={
        "console_scripts": [
            "passt=main:main",
        ],
    },
)
