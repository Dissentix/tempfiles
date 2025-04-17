from setuptools import setup

setup(
    name="dxwatch",
    version="1.0.0",
    packages=["dxwatch"],
    install_requires=["requests", "pyyaml", "rich", "discord-webhook"],
    entry_points={"console_scripts": ["dxwatch = dxwatch.main:main"]},
    author="Dissentix",
    description="A reconnaissance watchtower tool",
    url="https://github.com/Dissentix/dxwatch",
    data_files=[("dxwatch", ["resolvers.txt"])],
)
