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

    def get_input_and_suggestion(self):
        input_ = []
        suggestion = []
        for i, arg in enumerate(self.args):
            if i in self.wrong_index:
                input_.append(f"[red][bold]{arg}[/bold][/red]")
                if self.suggestion:
                    suggestion.append(f"[green][bold]{self.suggestion[i]}[/bold][/green]")
            else:
                input_.append(arg)
                if self.suggestion:
                    suggestion.append(self.suggestion[i])

        input_ = self.program_name + " " + " ".join(input_)
        if self.suggestion:
            suggestion = self.program_name + " " + " ".join(suggestion)
        return input_, suggestion

    def _render_with_rich(self):
        # inspired from cyclopts https://github.com/BrianPugh/cyclopts/blob/a6489e6f6e7e1b555c614f2fa93a13191718d44b/cyclopts/exceptions.py#L318
        from rich.console import Console

        console = Console()

        console.print("\nERROR: Invalid argument: ", style="bold red")
        console.print("\n" + self.error_msg, style="red")
        console.print("-" * console.width + "\n", style="red")

        input_, suggestion = self.get_input_and_suggestion()
        console.print("[red]Input:[/red] \n" + input_)
        if self.suggestion:
            console.print(" \n[green]Suggestion:[/green] \n" + suggestion)

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
