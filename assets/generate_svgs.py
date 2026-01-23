"""Generate SVG terminal screenshots for README."""

import subprocess
import os

from rich.console import Console
from rich.text import Text


def capture_with_colors(cmd: list[str]) -> str:
    """Capture command output with ANSI colors using script."""
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["FORCE_COLOR"] = "1"

    result = subprocess.run(
        ["script", "-q", "-c", " ".join(cmd), "/dev/null"],
        capture_output=True,
        text=True,
        env=env,
    )
    # Combine stdout and stderr
    output = result.stdout + result.stderr
    return output


def ansi_to_svg(ansi_text: str, title: str, filename: str, width: int = 85):
    """Convert ANSI text to SVG using rich."""
    console = Console(record=True, width=width, force_terminal=True)

    # Parse ANSI and print to console
    text = Text.from_ansi(ansi_text.strip())
    console.print(text)

    # Export to SVG
    console.save_svg(filename, title=title)
    print(f"Saved {filename}")


def extract_box(output: str) -> str:
    """Extract just the box portion from output."""
    lines = output.split("\n")
    result = []
    in_box = False
    for line in lines:
        if "╭" in line:
            in_box = True
        if in_box:
            result.append(line)
        if "╯" in line and in_box:
            break
    return "\n".join(result)


def extract_help(output: str) -> str:
    """Extract help output (all boxes)."""
    lines = output.split("\n")
    result = []
    started = False
    box_count = 0
    for line in lines:
        if "usage:" in line.lower():
            started = True
        if started:
            result.append(line)
            if "╯" in line:
                box_count += 1
                # Stop after 4 boxes (options, train, data)
                if box_count >= 4:
                    break
    return "\n".join(result)


if __name__ == "__main__":
    # Change to repo root (parent of assets directory)
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Help output
    output = capture_with_colors(["uv", "run", "python", "examples/nested_cli.py", "--help"])
    help_text = extract_help(output)
    ansi_to_svg(help_text, "pydantic-config --help", "assets/help.svg", width=62)

    # Required error
    output = capture_with_colors(["uv", "run", "python", "examples/nested_cli.py"])
    box_text = extract_box(output)
    ansi_to_svg(box_text, "Missing Required Argument", "assets/required_error.svg", width=45)

    # Config validation error
    output = capture_with_colors(
        ["uv", "run", "python", "examples/nested_cli.py", "--train", "@", "examples/train_config.toml"]
    )
    box_text = extract_box(output)
    ansi_to_svg(box_text, "Config Validation Error", "assets/config_error.svg", width=82)

    # File not found
    output = capture_with_colors(["uv", "run", "python", "examples/nested_cli.py", "@", "nonexistent.toml"])
    box_text = extract_box(output)
    ansi_to_svg(box_text, "Config File Not Found", "assets/file_not_found.svg", width=82)
