# Contributing

Welcome to the `netlistx` contributor's guide.

All participants are expected to be **open, considerate, reasonable, and
respectful**. When in doubt, the [Python Software Foundation's Code of Conduct]
is a good reference for behaviour.

## Issue Reports

If you experience bugs or general issues, please check the [issue tracker]
first (including closed issues) and then open a new report if needed.

Please include your environment (operating system, Python version) and a
minimal reproduction. Simplifying the reproduction helps identify the root
cause quickly.

## Documentation Improvements

`netlistx` documentation is built with [Sphinx] from the `docs/` directory.
Documents are written in Markdown with [MyST] extensions and reStructuredText.

You can propose documentation changes directly through the GitHub web interface:
open the relevant file in `docs/` and use the pencil icon.

Build the docs locally with:

```bash
tox -e docs
```

Preview the result at `http://localhost:8000`:

```bash
python3 -m http.server --directory docs/_build/html
```

## Code Contributions

### Architecture overview

- `src/netlistx/netlist.py` — `Netlist`, `SimpleGraph`, `TinyGraph`, and
  factory helpers.
- `src/netlistx/readwrite.py` — IBM `.net`/`.are`, JSON, and Yosys JSON readers
  (DOM, SAX, and direction-aware).
- `src/netlistx/cover.py` — primal-dual covering algorithms with reverse-delete
  post-processing.
- `src/netlistx/graph_algo.py`, `netlist_algo.py`, `rand_cover.py`,
  `rand_cover_gpu.py` — vertex-cover, matching, and randomized variants.
- `src/netlistx/tsp.py`, `hadlock.py` — TSP heuristics and planar MAX-CUT.

### Submit an issue

Before working on a non-trivial contribution, open an issue in the
[issue tracker] to discuss the change. This often surfaces constraints and
avoids duplicate work.

### Create an environment

Create an isolated environment, e.g. with [virtualenv]:

```bash
virtualenv .venv
source .venv/bin/activate
```

or [Miniconda]:

```bash
conda create -n netlistx python=3.12
conda activate netlistx
```

### Clone the repository

1. Fork the [repository] on GitHub.
2. Clone your fork and enter the directory:

   ```bash
   git clone git@github.com:YourLogin/netlistx.git
   cd netlistx
   ```

3. Install the package in editable mode with test extras:

   ```bash
   pip install -U pip setuptools
   pip install -e ".[testing]"
   ```

4. Install [pre-commit] hooks:

   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Implement your changes

1. Create a branch:

   ```bash
   git checkout -b my-feature
   ```

2. Add [docstrings] for new public functions, modules, and classes.
3. Add yourself to `AUTHORS.md`.
4. Commit your changes with a descriptive message.
5. Run the test suite and linters:

   ```bash
   pytest
   tox -e lint
   tox -e mypy
   ```

   `tox` alone runs the test environment. Use `tox -av` to list all
   configured environments.

### Submit your contribution

Push your branch and open a pull request:

```bash
git push -u origin my-feature
```

You may open it as a draft first and mark it ready after CI passes.

### Troubleshooting

1. Fetch tags from the upstream [repository] (needed for `setuptools_scm`):
   `git describe --abbrev=0 --tags`. If you are running CI in a fork, push all
   tags.
2. If `tox` misses a new dependency, recreate its environment with
   `tox -r -e <env>`.
3. `pytest --pdb` drops you into an interactive session on failure.

## Maintainer tasks

### Releases

If you have permission on [PyPI], release a new version with:

1. Ensure all tests pass.
2. Tag the main branch, e.g. `git tag 0.8.0`.
3. Push the tag: `git push upstream 0.8.0`.
4. Clean old artifacts: `tox -e clean`.
5. Build: `tox -e build` and verify the version and size in `dist/`.
6. Publish with trusted publishing via the `python-publish` GitHub workflow
   (or `tox -e publish -- --repository pypi` with a token).

[^contrib1]: These resources focus on open source, but the collaboration ideas
apply to private projects too.

[black]: https://pypi.org/project/black/
[commonmark]: https://commonmark.org/
[contribution-guide.org]: http://www.contribution-guide.org/
[creating a pr]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
[descriptive commit message]: https://chris.beams.io/posts/git-commit
[docstrings]: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
[flake8]: https://flake8.pycqa.org/en/stable/
[git]: https://git-scm.com
[github's fork and pull request workflow]: https://guides.github.com/activities/forking/
[guide created by freecodecamp]: https://github.com/freecodecamp/how-to-contribute-to-open-source
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[myst]: https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html
[other kinds of contributions]: https://opensource.guide/how-to-contribute
[pre-commit]: https://pre-commit.com/
[pypi]: https://pypi.org/
[pytest can drop you]: https://docs.pytest.org/en/stable/usage.html#dropping-to-pdb-python-debugger-at-the-start-of-a-test
[python software foundation's code of conduct]: https://www.python.org/psf/conduct/
[repository]: https://github.com/luk036/netlistx
[issue tracker]: https://github.com/luk036/netlistx/issues
[sphinx]: https://www.sphinx-doc.org/en/master/
[tox]: https://tox.readthedocs.io/en/stable/
[virtualenv]: https://virtualenv.pypa.io/en/stable/
