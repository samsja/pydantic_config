import copy
from importlib.util import find_spec


class CliError(BaseException):
    def __init__(self, args: list[str], wrong_index: list[int]):
        super().__init__()
        self.args = copy.deepcopy(args)
        self.wrong_index = wrong_index
        self._program_name = None

    def error_msg(self):
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

        # Print error header with extra space
        console.print("\nERROR: Invalid argument: ", style="bold red")
        console.print("-" * console.width + "\n", style="red")

        # Print the error message with extra space
        console.print(self.error_msg())
        console.print("\n" + "-" * console.width, style="red")

        # Print helpful message with extra space
        console.print("Please check your input and try again.\n", style="yellow")

        # Print bottom separator line

    def render(self):
        if find_spec("rich"):
            return self._render_with_rich()
        else:
            return print(self.error_msg())

    @property
    def program_name(self) -> str:
        return self._program_name or ""

    @program_name.setter
    def program_name(self, program_name: str):
        self._program_name = program_name


if __name__ == "__main__":
    ## this is just to test vizually the error rendering. As there is no clear way to do this in pytests.
    e = CliError(["--a", "b", "c", "--c", "--d--"], [2, 3])
    e.program_name = "test.py"
    e.render()
