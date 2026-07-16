import argparse
import logging
import time
from logging import error, info
from pathlib import Path
from typing import Optional

from watchdog.events import EVENT_TYPE_CLOSED, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

try:
    from watchdog.events import EVENT_TYPE_OPENED  # pylint: disable=ungrouped-imports
except ImportError:
    EVENT_TYPE_OPENED = "opened"  # type: ignore

from tumfl import ParserError, format, minifier
from tumfl.AST import ASTNode
from tumfl.config import Config, parse_config
from tumfl.dependency_resolver import resolve_recursive
from tumfl.error import TumflError
from tumfl.formatter import MinifiedStyle


class RunConfig:
    # pylint: disable=too-few-public-methods
    def __init__(
        self, source: Path, destination: Optional[Path], config: Config, minify: bool
    ) -> None:
        self.source: Path = source
        self.destination: Optional[Path] = destination
        self.config: Config = config
        self.minify: bool = minify


def compile_file(filename: Path, config: Config, minify: bool) -> str:
    source_directory: Path = filename.parent
    result: ASTNode = resolve_recursive(
        filename, [source_directory], add_source_description=True, config=config
    )
    if minify:
        minifier.minify(result)
        return format(result, MinifiedStyle)
    return format(result)


def run(config: RunConfig) -> None:
    if not config.destination:
        config.destination = config.source.with_stem(config.source.stem + "_result")
    try:
        compiled = compile_file(config.source, config.config, config.minify)
    except RuntimeError:
        return
    except TumflError as e:
        if isinstance(e, ParserError):
            error(e.full_error)
        else:
            error(e)
        return
    with config.destination.open("w") as f:
        f.write(compiled)


class EventHandler(FileSystemEventHandler):
    def __init__(self, config: RunConfig):
        self.config: RunConfig = config

    def execute(self) -> None:
        info("Files changed, recompiling")
        run(self.config)

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.event_type not in (EVENT_TYPE_CLOSED, EVENT_TYPE_OPENED):
            self.execute()


def follow(config: RunConfig) -> None:
    run(config)
    observer = Observer()
    event_handler = EventHandler(config)
    observer.schedule(event_handler, str(config.source.parent), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


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
    parser.add_argument(
        "-m",
        "--minify",
        action="store_true",
        help="Minify the output",
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
    config = Config({})
    if args.config_file:
        config = parse_config(args.config_file)
    config.prefix = args.config_prefix
    run_config = RunConfig(args.source_file, args.destination_file, config, args.minify)
    if args.follow:
        follow(run_config)
    else:
        run(run_config)


if __name__ == "__main__":
    main()
