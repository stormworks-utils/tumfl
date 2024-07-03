# Tumfl: The Ultimate Minimizer For Lua

[![codecov](https://codecov.io/github/stormworks-utils/tumfl/branch/main/graph/badge.svg?token=X5TIVNJSZ7)](https://codecov.io/github/stormworks-utils/tumfl)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
 
This package contains the best minimizer you'll find on the market, or so I hope.
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

 - Not existent
