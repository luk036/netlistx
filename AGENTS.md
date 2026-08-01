# AGENTS.md - Agent Guidelines for netlistx

## Build/Lint/Test Commands

### Testing
```bash
# Run all tests
pytest

# Run single test
pytest tests/test_netlist.py::test_create_inverter

# Run tests matching a pattern
pytest -k "cover"

# Run via tox (isolated environment; installs mywheel from git)
tox
```

### Linting & Formatting
```bash
# Run all pre-commit hooks (recommended before committing)
pre-commit run --all-files

# Individual tools
black .               # Format code (line length 256)
isort .               # Sort imports
flake8 .              # Lint (max_line_length=256, ignores E203/W503)
mypy src/             # Type check (Python 3.12 target)
```

### Build & Docs
```bash
tox -e build          # Build sdist + wheel
tox -e clean          # Remove build artifacts
tox -e docs           # Build HTML docs
tox -e doctests       # Run doctests
tox -e linkcheck      # Check for broken doc links
```

## Code Style Guidelines

### Project Structure
- Source code: `src/netlistx/`
- Tests: `tests/` (test_netlist.py, test_netlist_algo.py, test_graph_algo.py, test_cover.py, test_pd_cover.py, test_hadlock.py, test_tsp.py, test_readwrite.py, test_yosys.py, test_rand_cover.py, hypothesis and stress variants)
- Version managed via setuptools_scm (`no-guess-dev` scheme)

### Naming Conventions
- **Classes**: PascalCase (e.g., `Netlist`, `SimpleGraph`, `TinyGraph`)
- **Functions/Methods**: snake_case (e.g., `create_inverter`, `read_yosys_json`, `min_vertex_cover_fast`, `get_module_weight`)
- **Module-level constants**: lowercase (e.g., `all_edge_dict`)
- **Unused parameters**: underscore `_` (e.g., `def get_net_weight(self, _: Any)`)

### Type Hints
- **Required**: All function parameters and return types
- Modern builtin generics used in newer code (e.g., `list[str]`, `dict[str, int]`, `set[int]`, `tuple[int, int]`)
- `# type: ignore` used for untyped third-party imports (e.g., `mywheel`, `ijson` with `# type: ignore[import-untyped]`)

### Docstrings
- **Primary style**: Sphinx/reStructuredText with `:param:`, `:type:`, `:return:`, `:rtype:`
- **Alternative**: Google-style `Args:`/`Returns:` sections
- **Examples**: doctest blocks with `>>>` (e.g., `vdc`, `vdcorput`)
- **Diagrams**: `.. svgbob::` ASCII art for graph/netlist topologies
- Long prose module docstrings describing each algorithm's intent

### Imports
- **Order**: stdlib → third-party → local (PEP8, enforced by isort)
- Third-party example: `from mywheel.array_like import RepeatArray`, `from networkx.algorithms import bipartite`
- `ijson` imported lazily inside the SAX reader function

### Error Handling
- **Minimal explicit error handling** — rely on natural exceptions
- Raise `ImportError`/`FileNotFoundError` documented in docstrings (e.g., `read_yosys_json_sax`)
- No `assert` preconditions in source; tests use plain `assert`
- Validation logic falls back to default weights (`return 1`) rather than raising

### Python Version
- No `python_requires` pin in setup.cfg
- CI tests on Python 3.11 and 3.12; mypy targets Python 3.12

### Configuration Files
- `setup.cfg`: package metadata, pytest options, flake8 config
- `.flake8`: formatter-friendly (ignores E1/E2/E3/E501/W1/W2/W3/W5)
- `.pre-commit-config.yaml`: pre-commit hooks
- `mypy.ini`: Python 3.12 target, `disable_error_code = import-untyped`, ignores setuptools/matplotlib/networkx
- `pyproject.toml`: build system (setuptools_scm)
- `tox.ini`: task automation (test, build, clean, docs, doctests, linkcheck, publish)
- `.coveragerc`: coverage config

### Pre-commit Hooks
- trailing-whitespace
- check-added-large-files
- check-ast
- check-json / check-yaml / check-xml
- check-merge-conflict
- debug-statements
- end-of-file-fixer
- requirements-txt-fixer
- mixed-line-ending (auto-fix)
- isort
- black
- flake8

### Testing Patterns
- Framework: pytest (no coverage in addopts; `testpaths = tests`)
- Hypothesis property-based tests in dedicated `test_*_hypothesis.py` files
- Plain `assert` statements, typed `def test_...() -> None`
- Fixtures built from `create_inverter`, `create_random_hgraph`, and `nx.Graph`
- `test_coverage_gaps_*.py` files target uncovered branches

## Key Project Context

netlistx provides netlist representations and graph algorithms for electronic design automation:
- **Netlist model**: circuits as bipartite graphs (`Netlist`, `SimpleGraph`, `TinyGraph`) with module/net weights via `mywheel.RepeatArray`
- **I/O**: JSON readers including Yosys JSON — DOM-style (`read_yosys_json`) and streaming SAX via `ijson` (`read_yosys_json_sax`)
- **Covering algorithms**: primal-dual approximation with reverse-delete post-processing (`pd_cover`, `min_vertex_cover`, `min_cycle_cover`, `min_odd_cycle_cover`, `min_hyper_vertex_cover`) for edges, cycles, and odd cycles
- **Routing/other**: Hadlock router (`hadlock.py`), TSP heuristics (`tsp.py`), random cover generators
- **Used by**: `ckpttnpy`; **key dependencies**: `networkx`, `numpy`, `numba`, `jsonschema`, `ijson`, `mywheel`
