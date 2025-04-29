import argparse
import logging
import time
from logging import error, info, warning
from pathlib import Path
from typing import Optional

from watchdog.events import EVENT_TYPE_CLOSED, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

try:
    from watchdog.events import EVENT_TYPE_OPENED
except ImportError:
    EVENT_TYPE_OPENED = "opened"

from tumfl import format
from tumfl.AST import Assign, ASTNode, Name
from tumfl.basic_walker import NoneWalker
from tumfl.config import Config
from tumfl.dependency_resolver import resolve_recursive
from tumfl.error import TumflError


class ParameterGetter(NoneWalker):
    def __init__(self) -> None:
        super().__init__()
        self.parameters: dict[str, ASTNode] = {}

    def visit_Assign(self, node: Assign) -> None:
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], Name)
            and len(node.expressions) == 1
        ):
            name = node.targets[0]
            assert isinstance(name, Name)
            self.parameters[name.variable_name] = node.expressions[0]
        else:
            warning(f"Ignoring config parameter {node}")


def compile_file(filename: Path, config: Config) -> str:
    source_directory: Path = filename.parent
    result: ASTNode = resolve_recursive(
        filename, [source_directory], add_source_description=True, config=config
    )
    return format(result)


def run(source: Path, destination: Optional[Path], config: Config) -> None:
    if not destination:
        destination = source.with_stem(source.stem + "_result")
    try:
        compiled = compile_file(source, config)
    except RuntimeError:
        return
    except TumflError as e:
        error(e)
        return
    with destination.open("w") as f:
        f.write(compiled)


class EventHandler(FileSystemEventHandler):
    def __init__(self, source: Path, destination: Optional[Path], config: Config):
        self.source: Path = source
        self.destination: Optional[Path] = destination
        self.config: Config = config

    def execute(self) -> None:
        info("Files changed, recompiling")
        run(self.source, self.destination, self.config)

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.event_type not in (EVENT_TYPE_CLOSED, EVENT_TYPE_OPENED):
            self.execute()


def follow(source: Path, destination: Optional[Path], config: Config) -> None:
    run(source, destination, config)
    observer = Observer()
    event_handler = EventHandler(source, destination, config)
    observer.schedule(event_handler, str(source.parent), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def parse_config(file: Path) -> dict[str, ASTNode]:
    chunk: ASTNode = resolve_recursive(file, [file.parent])
    getter = ParameterGetter()
    getter.visit(chunk)
    return getter.parameters


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile lua files", prog="tumfl")
    parser.add_argument("source_file", type=Path, help="Source file to compile")
    parser.add_argument("-d", "--destination-file", type=Path, help="Destination file")
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose",
        action="count",
        default=0,
    )
    parser.add_argument(
        "-f", "--follow", action="store_true", help="Follow file changes"
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=Path,
        help="Replace placeholders using config file."
        " Config file is a normal lua file, with top level assignments of `name = value`, not limited to strings."
        " To use an replacement, just use a string int the target file like"
        ' `"$$name"` (if `$$` is your prefix, and `name` the name to look up).',
    )
    parser.add_argument(
        "--config-prefix",
        default="$$",
        help="Prefix for names to be replaced by config values (default: $$)",
    )
    args = parser.parse_args()
    loglevel = logging.WARN
    if args.verbose == 1:
        loglevel = logging.INFO
    elif args.verbose > 1:
        loglevel = logging.DEBUG
    logging.basicConfig(
        format="%(asctime)s|%(levelname)s| %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=loglevel,
    )
    config = Config({}, prefix=args.config_prefix)
    if args.config_file:
        config.replacements = parse_config(args.config_file)
    if args.follow:
        follow(args.source_file, args.destination_file, config)
    else:
        run(args.source_file, args.destination_file, config)


if __name__ == "__main__":
    main()
