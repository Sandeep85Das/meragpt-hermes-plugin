"""meraGPT Decider for Hermes Agent.

Registers four tools that call the meraGPT API (https://meragpt.com) with the user's own API key,
read through Hermes's secret scope from the MERAGPT_API_KEY secret declared in plugin.yaml, and one
workflow skill describing when to use them.
"""
from pathlib import Path

from . import schemas, tools

TOOLSET = "meragpt"


def register(ctx):
    ctx.register_tool(name="meragpt_decide", toolset=TOOLSET, schema=schemas.DECIDE, handler=tools.decide)
    ctx.register_tool(name="meragpt_extract", toolset=TOOLSET, schema=schemas.EXTRACT, handler=tools.extract)
    ctx.register_tool(name="meragpt_restyle", toolset=TOOLSET, schema=schemas.RESTYLE, handler=tools.restyle)
    ctx.register_tool(name="meragpt_fanout", toolset=TOOLSET, schema=schemas.FANOUT, handler=tools.fanout)

    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)
