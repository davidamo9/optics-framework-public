# CLI Guide

This section describes the available commands for the `optics` CLI.

## Setup Optics Framework

To set up the Optics Framework, use the following command:

To list all possible drivers:

```bash
optics setup --list
```

TUI way:

```bash
optics setup
```

CLI way:

```bash
optics setup --install <driver_name1> <driver_name2> ...
```

## Executing Test Cases

Run test cases from a project folder (auto-discovers `config.yaml`, CSVs, and APIs):

```bash
optics execute <project_path> [--runner <runner_name>] [--no-use-printer]
```

**Options:**

- `<project_path>`: Path to the project directory.
- `--runner <runner_name>`: Test runner to use. Current support: `test_runner` (default).
- `--no-use-printer`: Disable the live result printer (enabled by default).

## Initializing a New Project

Use the following command to initialize a new project:

```bash
optics init --name <project_name> [--path <directory>] [--template <sample_name>] [--git-init] [--force]
```

**Options:**

- `--name <project_name>`: Name of the project.
- `--path <directory>`: Directory to create the project in.
- `--force`: Overwrite existing files if necessary.
- `--template <sample_name>`: Choose a predefined example.
- `--git-init`: Initialize a Git repository.

## Generating Code

Generate test framework boilerplate from a project folder:

```bash
optics generate <project_path> [--framework pytest|robot] [--output <file>]
```

**Options:**

- `<project_path>`: Path to the project folder containing CSV/YAML.
- `--framework`: Output framework (`pytest` default or `robot`).
- `--output`: Output file name (default: `test_generated.py` or `test_generated.robot`).

## Listing Available Keywords

Display a list of all available keywords:

```bash
optics list
```

## Executing Dry Run

Execute a dry run (parses files, no device actions):

```bash
optics dry_run <project_path> [--runner <runner_name>] [--no-use-printer]
```

**Options:**

- `<project_path>`: Path to the project directory.
- `--runner <runner_name>`: Test runner to use. Current support: `test_runner` (default).
- `--no-use-printer`: Disable the live result printer (enabled by default).

## Showing Help Information

Get help for the CLI:

```bash
optics --help
```

## Managing Configuration (TUI)

Open the interactive configuration editor (Textual UI):

```bash
optics config
```

Use arrow keys to navigate, Space to edit, S to save.

## Checking Version

Check the installed version of `optics-framework`:

```bash
optics --version
```

## Running the API Server

Start the built-in FastAPI server (exposes session and keyword endpoints):

```bash
optics serve [--host 127.0.0.1] [--port 8000]
```

Once running, check `GET /` for health and version.

## Additional Information

!!! info "Command Name"
    The CLI entry point is `optics`. Install the package and ensure your environment PATH is configured.

!!! tip "Optional Parameters"
    Options like `--runner`, `--force`, and `--git-init` are optional. Omit them to use defaults (e.g., `test_runner` for `--runner`).

!!! tip "Autocompletion"
    Enable shell completion for faster usage with: `optics completion`.

!!! note "Driver Installation"
    When using `optics setup --install`, ensure `<driver_name1> <driver_name2> ...` matches available drivers listed by `optics setup --list`.

!!! tip "Dry Run Specificity"
    Use `--test-case "<test-case-name>"` with `optics dry_run` to test a single case without affecting others, ideal for debugging.

!!! info "Configuration Persistence"
    Changes made with `optics-framework config --set` persist across sessions unless reset with `--reset`.
