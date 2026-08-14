# Coding Rules

## Architecture

Dependencies must flow:

api → services → repositories → models

Do not introduce reverse dependencies.

## Python

- Python 3.12+
- Use type hints
- No `Any` unless necessary
- No `eval`
- No `exec`
- Do not use `shell=True`

## Tests

Every behavioral change must have tests.

## Dependencies

Do not add dependencies unless necessary.

## Changes

Keep changes minimal.
Do not modify unrelated files.
