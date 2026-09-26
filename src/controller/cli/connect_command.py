"""Contains command to connect filter channels in batch mode."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError

from controller.cli.command import Command
from model import DataType

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from jinja2.environment import Template

    from controller.cli.cli_context import CLIContext


def _add(value: str, arg: str) -> str:
    return str(int(int(value) + int(arg)))


def _sub(value: str, arg: str) -> str:
    return str(int(int(value) - int(arg)))


def _mul(value: str, arg: str) -> str:
    return str(int(int(value) * int(arg)))


def _div(value: str, arg: str) -> str:
    """Divide the given value by the given divisor using integer floor division."""
    divisor = int(arg)
    if divisor == 0:
        raise ValueError("The 'div' filter requires a divisor other than zero.")
    return str(int(value) // divisor)


def _mod(value: str, arg: str) -> str:
    """Compute the integer modulo of the given value by the given divisor."""
    divisor = int(arg)
    if divisor == 0:
        raise ValueError("The 'mod' filter requires a divisor other than zero.")
    return str(int(int(value) % divisor))


class _FatalConnectError(Exception):
    """Fatal connect command error that requires the whole command to be aborted."""


class ConnectCommand(Command):
    """Command to connect filters."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize the command."""
        super().__init__(context, "connect")
        self._help_text = "Connect filter channels"
        self._jinja_env = Environment(undefined=StrictUndefined)  # NOQA: S701 the editor is not a web page.
        self._jinja_env.filters["add"] = _add
        self._jinja_env.filters["sub"] = _sub
        self._jinja_env.filters["mul"] = _mul
        self._jinja_env.filters["div"] = _div
        self._jinja_env.filters["mod"] = _mod

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("source", type=str, nargs=1, help="Source filter id and channel name, split by colon.")
        parser.add_argument("targets", type=str, nargs="+", help="Targets filter id and channel name, split by colon.")
        parser.add_argument(
            "-g", "--guard", type=str, nargs="*", default=[], help="Specify condition required to make the connection"
        )
        parser.add_argument(
            "-s", "--source-count", type=int, default=1, help="Specify the number of source channel iterations"
        )
        parser.add_argument(
            "-d",
            "--destination-count",
            type=int,
            default=1,
            help="Specify the number of destination channel iterations",
        )

    @override
    def execute(self, args: Namespace) -> bool:
        if self.context.selected_scene is None:
            self.context.print("Error: No scene selected.")
            return False
        success = True
        try:
            src_template = self._jinja_env.from_string(args.source[0])
        except TemplateSyntaxError as e:
            self.context.print(f"ERROR: Failed to parse the source filter template: {e}")
            return False
        try:
            dest_templates = [self._jinja_env.from_string(dest_template_str) for dest_template_str in args.targets]
        except TemplateSyntaxError as e:
            self.context.print(f"ERROR: Failed to parse a destination filter template: {e}")
            return False
        try:
            for i in range(args.source_count):
                for dest_template in dest_templates:
                    for j in range(args.destination_count):
                        success &= self._connect(src_template, dest_template, i, j, args.guard)
        except _FatalConnectError as e:
            self.context.print(f"ERROR: {e}")
            return False
        return success

    def _connect(
        self,
        source_template: Template,
        destination_template: Template,
        source_iter: int,
        destination_iter: int,
        guards: list[str],
    ) -> bool:
        """Connect a single rendered source channel to a rendered destination channel.

        Args:
            source_template: the template rendering the source filter id and channel name
            destination_template: the template rendering the destination filter id and channel name
            source_iter: the current source iteration index
            destination_iter: the current destination iteration index
            guards: the connection guards to evaluate

        Returns:
            whether the connection has been established. Guards may skip single connections without failing the
            command.

        Raises:
            _FatalConnectError: if a template cannot be evaluated or a guard is malformed. These errors do not
                depend on the iteration indices, so the whole command is aborted instead of retrying them.

        """
        scene = self.context.selected_scene
        if scene is None:
            self.context.print("Error: No scene selected.")
            return False
        try:
            rendered_source = source_template.render({"si": source_iter, "di": destination_iter})
        except (UndefinedError, ValueError) as e:
            raise _FatalConnectError(f"Failed to evaluate the source filter template: {e}") from e
        try:
            source_filter_id, source_channel_name = rendered_source.split(":")
        except ValueError as e:
            self.context.print(
                f"ERROR: The source filter format is invalid: {e}. Got: '{rendered_source}'."
                f" Use the following format: <source_filter_id>:<channel_name>"
            )
            return False
        source_filter = scene.get_filter_by_id(source_filter_id)
        if source_filter is None:
            self.context.print(f"Source filter '{source_filter_id}' does not exist in scene '{scene.scene_id}'.")
            return False
        try:
            rendered_destination = destination_template.render({"si": source_iter, "di": destination_iter})
        except (UndefinedError, ValueError) as e:
            raise _FatalConnectError(f"Failed to evaluate the destination filter template: {e}") from e
        try:
            destination_filter_id, destination_channel_name = rendered_destination.split(":")
        except ValueError as e:
            self.context.print(
                f"ERROR: The destination filter format is invalid: {e}. Got: '{rendered_destination}'."
                f" Use the following format: <destination_filter_id>:<channel_name>"
            )
            return False
        destination_filter = scene.get_filter_by_id(destination_filter_id)
        if destination_filter is None:
            self.context.print(
                f"Destination filter '{destination_filter_id}' does not exist in scene '{scene.scene_id}'."
            )
            return False
        source_data_type = source_filter.out_data_types.get(source_channel_name)
        if source_data_type is None:
            self.context.print(
                f"Source channel '{source_channel_name}' of filter '{source_filter_id}' does not exist "
                f"in scene '{scene.scene_id}'."
            )
            return False
        dest_data_type = destination_filter.in_data_types.get(destination_channel_name)
        if dest_data_type is None:
            self.context.print(
                f"Destination channel '{destination_channel_name}' of filter '{destination_filter_id}' "
                f"does not exist in scene '{scene.scene_id}'."
            )
            return False
        if source_data_type != dest_data_type:
            self.context.print(
                f"Source ({source_data_type}) and destination ({dest_data_type}) data "
                f"types do not match. Filters: {source_filter_id} and {destination_filter_id}."
            )
            return False
        can_run = True
        for guard in guards:
            try:
                g_filter, argument = guard.split(":")
                match g_filter:
                    case "smod":
                        divisor = int(argument)
                        if divisor == 0:
                            raise _FatalConnectError(f"Guard '{guard}' requires a divisor other than zero.")
                        can_run &= source_iter % divisor == 0
                    case "dmod":
                        divisor = int(argument)
                        if divisor == 0:
                            raise _FatalConnectError(f"Guard '{guard}' requires a divisor other than zero.")
                        can_run &= destination_iter % divisor == 0
                    case "dt":
                        required_dt = DataType.from_filter_str(argument)
                        can_run &= source_data_type == required_dt
                    case "sfid_contains":
                        can_run &= argument in source_filter_id
                    case "dfid_contains":
                        can_run &= argument in destination_filter_id
                    case "schan_contains":
                        can_run &= argument in source_channel_name
                    case "dchan_contains":
                        can_run &= argument in destination_channel_name
                    case _:
                        raise _FatalConnectError(f"The guard '{g_filter}' is unknown.")
            except ValueError as e:
                raise _FatalConnectError(
                    f"Guard '{guard}' is not in a valid format. Allowed: <guard>:<argument>"
                ) from e
        if can_run:
            destination_filter.channel_links[destination_channel_name] = source_filter_id + ":" + source_channel_name
        return True
