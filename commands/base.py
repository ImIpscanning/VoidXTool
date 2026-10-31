from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.commands.validator import Validator

console: Console = Console()

class BaseCommand:
    __firstlineno__ = 9

    def __init__(self, name: str):
        self.name = name
        self.command_arguments = Msg.get(f"commands.{self.name}.args")

    def validate_arguments(self, user_arguments: list) -> bool:
        '''
Base method to validate arguments length and
call the custom validation method.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        from voidxtool.security.scope import ScopePolicy

        scope_decision = ScopePolicy().check(self.name, [str(value) for value in user_arguments])
        if not scope_decision.allowed:
            console.print(f"[bold red]Scope denied:[/bold red] {scope_decision.reason}")
            return False
        if not Validator.validate_arguments_length(
            command_name=self.name,
            command_arguments=self.command_arguments,
            user_arguments=user_arguments
        ):
            return False
        return self.custom_validate_arguments(user_arguments)

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to be implemented by subclasses.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        raise NotImplementedError('Subclass not implemented.')

    __static_attributes__ = ('command_arguments', 'name')
