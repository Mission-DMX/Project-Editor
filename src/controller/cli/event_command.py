from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from controller.cli.command import Command
from model.events import EventSender, get_sender, insert_event

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext

logger = getLogger(__name__)


class EventCommand(Command):
    def __init__(self, context: CLIContext) -> None:
        super().__init__(context, "event")
        self.help_text = "Manipulate Events on fish."

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(help="Event management commands", dest="eventactions")
        add_parser = subparsers.add_parser("add-sender", exit_on_error=False, help="Add a new event sender to fish")
        add_parser.add_argument("name", help="The name of the new event sender", type=str)
        add_parser.add_argument("--sender-type", help="Specify the type of the sender to add",
                                default="fish.builtin.plain", const="fish.builtin.plain", nargs="?",
                                choices=["fish.builtin.plain", "fish.builtin.midi", "fish.builtin.midirtp",
                                         "fish.builtin.xtouchgpio", "fish.builtin.gpio", "fish.builtin.macrokeypad"])
        add_parser.add_argument("--enable-debug", help="Enable event debugging on the event sender",
                                action="store_true")
        add_parser.add_argument("--configure", nargs="+", action="extend")
        send_parser = subparsers.add_parser("send", exit_on_error=False, help="Send an event")
        id_group = send_parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument("-i", "--sender_id", help="The id of the originating sender", type=int, required=False)
        id_group.add_argument("-n", "--sender_name", help="Specify the sender by its name", type=str, required=False)
        send_parser.add_argument("--function", help="The sender function to be used", type=int, default=0)
        send_parser.add_argument("--type", default="single", choices=["single", "release", "start"])
        send_parser.add_argument("--args", nargs="+", type=int, action="extend", help="Specify the event arguments")
        # TODO add renaming of events

    def execute(self, args: Namespace) -> bool:
        match args.eventactions:
            case "add-sender":
                evs = EventSender(args.name)
                evs.type = args.sender_type
                if args.configure is not None:
                    for item in args.configure:
                        try:
                            if "=" in item:
                                k, v = item.split("=")
                                evs.configuration[str(k)] = str(v if v is not None else "")
                            else:
                                evs.configuration[str(item)] = ""
                        except ValueError as _:
                            logger.exception(
                                "Unable to parse event sender configuration entry %s."
                                " Expected format: <key>=<value>",
                                item)
                evs.debug_enabled = args.enable_debug
                return True
            case "send":
                effective_sender_id = get_sender(args.sender_name).index_on_fish if args.sender_name else args.sender_id
                insert_event(effective_sender_id, args.function, args.type, args.args or [])
                return True
        return False
