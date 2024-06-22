from rich.panel import Panel
from rich import box


def _get_error_panel(error: str, n_errors: int) -> Panel:
    # inspired from cyclopts https://github.com/BrianPugh/cyclopts/blob/a6489e6f6e7e1b555c614f2fa93a13191718d44b/cyclopts/exceptions.py#L318
    return Panel(
        error,
        title=f"{n_errors} errors",
        box=box.ROUNDED,
        expand=True,
        title_align="left",
        style="red",
    )
