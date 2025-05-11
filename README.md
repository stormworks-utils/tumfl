# Tumfl: The Ultimate Minimizer For Lua

[![codecov](https://codecov.io/github/stormworks-utils/tumfl/branch/main/graph/badge.svg?token=X5TIVNJSZ7)](https://codecov.io/github/stormworks-utils/tumfl)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package contains the best minimizer you'll find on the market, or so I hope.

# Executable

Compile a source file into a destination file, resolving all requires. Optionally recompiles every time the source files
change (using `-f`). Optionally replaces placeholders (using `-c`).

## Placeholders

Using a lua config file like
```lua
parameter = "value"
numbered_parameter = 3.14
table_parameter = {foo = 1, "bar"}
```
it can replace placeholders like
```lua
foo("$$parameter")
bar = "$$numbered_parameter"
baz = "$$table_parameter"
```
by compiling using `tumfl source.lua -c config.lua` with
```lua
foo("value")
bar = 3.14
baz = {foo = 1, "bar"}
```

The prefix is configurable via `--config-prefix`


```
usage: tumfl [-h] [-d DESTINATION] [-v] [-f] [-c CONFIG_FILE] [--config-prefix CONFIG_PREFIX] source_file

Compile lua files

positional arguments:
  source_file           Source file to compile

options:
  -h, --help            show this help message and exit
  -d DESTINATION, --destination DESTINATION
                        Destination file
  -v, --verbose         Be verbose
  -f, --follow          Follow file changes
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Replace placeholders using config file. Config file is a normal lua file, with top level assignments of
                        `name = value`, not limited to strings. To use an replacement, just use a string int the target file like
                        `"$$name"` (if `$$` is your prefix, and `name` the name to look up).
  --config-prefix CONFIG_PREFIX
                        Prefix for names to be replaced by config values (default: $$)
  -m, --minify          Minify the output
```

# Current status

## Parser

 - On par with Lua
 - No support for arbitrary byte strings (only valid UTF-8)

## Formatter

 - Highly configurable formatter
 - Can produce both minified and prettyfied results
 - Minified results have minimal amount of characters (only required semicolons, etc.)
 - Lossy in the sense that it does not preserve (all) comments

## Minifier

> [!CAUTION]
> The minifier is very experimental, and may change the semantics of your program. Use at your own risk.
> If it breaks, please open an issue.

 - Minifies Names (normal variables)
 - Creates aliases (i.e. when `table` is used often, creates `a=table` and uses `a` instead of `table`)
