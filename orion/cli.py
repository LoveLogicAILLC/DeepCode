"""
ORION CLI — Command-line interface for the Eternal Architect platform.

Usage:
    python -m orion.cli boot          — Boot the platform and start the API server
    python -m orion.cli cycle         — Run one self-improvement cycle
    python -m orion.cli seed "..."    — Inject a vision seed and run a cycle
    python -m orion.cli status        — Print platform status
    python -m orion.cli validate      — Validate all module contracts
    python -m orion.cli mcp-tools     — List all available MCP tools
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from orion.platform import OrionPlatform
from orion.spine.config import OrionConfig


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, default=str))


async def cmd_boot(args: argparse.Namespace) -> None:
    """Boot the full platform with the API gateway."""
    config = OrionConfig.from_yaml(args.config)
    _setup_logging(config.log_level)

    platform = OrionPlatform(config)
    await platform.boot()

    print(f"\nORION platform booted — {len(platform.registry.modules)} modules active")
    print(f"API gateway: http://{config.api_host}:{config.api_port}")
    print("Press Ctrl+C to stop.\n")

    try:
        import uvicorn

        app = platform.create_fastapi_app()
        server_config = uvicorn.Config(
            app,
            host=config.api_host,
            port=config.api_port,
            log_level=config.log_level.lower(),
        )
        server = uvicorn.Server(server_config)
        await server.serve()
    except ImportError:
        print("uvicorn not installed — running without API server")
        print("Install with: pip install uvicorn")
        # Keep alive so the user can observe logs
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
    finally:
        await platform.shutdown()


async def cmd_cycle(args: argparse.Namespace) -> None:
    """Run one self-improvement cycle."""
    config = OrionConfig.from_yaml(args.config)
    _setup_logging(config.log_level)

    platform = OrionPlatform(config)
    await platform.boot()

    print("\n--- Running Eternal Architect Cycle ---\n")
    result = await platform.run_architect_cycle(vision_seed=args.seed)
    _print_json(result)

    await platform.shutdown()


async def cmd_status(args: argparse.Namespace) -> None:
    """Print platform status."""
    config = OrionConfig.from_yaml(args.config)
    _setup_logging("WARNING")

    platform = OrionPlatform(config)
    await platform.boot()
    _print_json(platform.status())
    await platform.shutdown()


async def cmd_validate(args: argparse.Namespace) -> None:
    """Validate all module contracts."""
    config = OrionConfig.from_yaml(args.config)
    _setup_logging("WARNING")

    platform = OrionPlatform(config)
    await platform.boot()

    all_ok = True
    for name, record in platform.registry.modules.items():
        # Registry-level validation
        reg_warnings = platform.registry.validate_contract(name)
        # File-level validation
        file_warnings: list[str] = []
        if record.instance and hasattr(record.instance, "validate_contract_file"):
            file_warnings = record.instance.validate_contract_file()

        warnings = reg_warnings + file_warnings
        if warnings:
            all_ok = False
            print(f"  [{name}] WARNINGS:")
            for w in warnings:
                print(f"    - {w}")
        else:
            print(f"  [{name}] OK")

    await platform.shutdown()
    sys.exit(0 if all_ok else 1)


async def cmd_mcp_tools(args: argparse.Namespace) -> None:
    """List MCP tools."""
    config = OrionConfig.from_yaml(args.config)
    _setup_logging("WARNING")

    platform = OrionPlatform(config)
    await platform.boot()
    _print_json(platform.mcp.list_tools())
    await platform.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="orion",
        description="ORION Eternal Architect — Self-Architecting AI Platform",
    )
    parser.add_argument(
        "--config",
        default="orion.yaml",
        help="Path to orion.yaml config file",
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("boot", help="Boot platform with API gateway")

    cycle_parser = sub.add_parser("cycle", help="Run one self-improvement cycle")
    cycle_parser.add_argument("seed", nargs="?", default=None, help="Vision seed")

    sub.add_parser("status", help="Print platform status")
    sub.add_parser("validate", help="Validate module contracts")
    sub.add_parser("mcp-tools", help="List MCP tools")

    args = parser.parse_args()

    commands = {
        "boot": cmd_boot,
        "cycle": cmd_cycle,
        "status": cmd_status,
        "validate": cmd_validate,
        "mcp-tools": cmd_mcp_tools,
    }

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    asyncio.run(handler(args))


if __name__ == "__main__":
    main()
