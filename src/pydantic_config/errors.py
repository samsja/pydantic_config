import copy
from importlib.util import find_spec


class PydanticConfigError(BaseException): ...


class CliError(PydanticConfigError):
    def __init__(self, args: list[str], wrong_index: list[int], error_msg: str, suggestion: list[str] | None = None):
        super().__init__()
        self.args = copy.deepcopy(args)
        self.wrong_index = wrong_index
        self.suggestion = suggestion
        self.error_msg = error_msg
        self._program_name = None

    def error_list_args(self):
        bold_error = []
        for i, arg in enumerate(self.args):
            if i in self.wrong_index:
                bold_error.append(f"[red][bold]{arg}[/bold][/red]")
            else:
                bold_error.append(arg)

        error_msg = "[white]" + self.program_name + " " + " ".join(bold_error) + "[/white]"
        return error_msg

    def _render_with_rich(self):
        # inspired from cyclopts https://github.com/BrianPugh/cyclopts/blob/a6489e6f6e7e1b555c614f2fa93a13191718d44b/cyclopts/exceptions.py#L318
        from rich.console import Console

        console = Console()

        console.print("\nERROR: Invalid argument: ", style="bold red")
        console.print("\n" + self.error_msg, style="red")
        console.print("-" * console.width + "\n", style="red")

        console.print("[red]Input:[/red] \n" + self.error_list_args())
        if self.suggestion:
            console.print(" \n[green]Suggestion:[/green] \n" + self.program_name + " " + " ".join(self.suggestion))

        console.print("\n" + "-" * console.width, style="red")

        console.print("Please check your input and try again.\n", style="yellow")

    def render(self):
        if find_spec("rich"):
            return self._render_with_rich()
        else:
            return print(self.error_msg)

    @property
    def program_name(self) -> str:
        return self._program_name or ""

    @program_name.setter
    def program_name(self, program_name: str):
        self._program_name = program_name


class MergedConflictError(PydanticConfigError): ...
