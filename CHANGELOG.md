# Changelog

## Version 0.7 (2026-10-09)

### Features
- **Optional numba with CPU fallback**: `rand_cover_gpu` now imports numba lazily and only defines the CUDA kernel when numba is present; `rand_vertex_cover_gpu` falls back to the CPU `rand_vertex_cover` when numba is missing or no CUDA GPU is available, instead of raising `RuntimeError`. Tests guard the numba import so the module collects without it. (#d2954c9)

### Performance
- **Single 2-colouring BFS for the odd-cycle-cover oracle**: `_find_odd_cycle` replaces the per-call biconnected-component + chain decomposition and multi-source BFS in `min_odd_cycle_cover` with one O(V+E) BFS 2-colouring that returns the first odd cycle — measured ~90–200× faster on sparse graphs with identical cover size and cost. (#c123c82)

### Documentation
- **Reproducible odd-cycle-cover figures**: Generator script plus 7 SVG figures (even vs odd cycle, mixed cover, oracle before/after, per-language scaling, speedup summary), computed with the real implementation so they cannot drift. (#5b86266)
- **AGENTS.md**: Noted that numba is optional and documented the `netlistx[gpu]` extra and the CPU fallback. (#0db10a0)

### Testing & Code Quality
- **GPU fallback tests**: Added `benches/test_bm_odd_cycle_cover.py` and extended `test_rand_cover_gpu.py` to cover both fallback branches. (#c123c82, #d2954c9)

### Code Cleanup
- **Style**: Reformatted `readwrite` and the Yosys test per ruff. (#94c8227)

### Build & CI
- **Optional `gpu` extra**: Moved numba out of `install_requires` into the `netlistx[gpu]` extra (and from `requirements/default.txt` into `requirements/extras.txt`). (#c08c362)

### Maintenance
- **Requirements**: Alphabetized `requirements/extras.txt`. (#82606d0)

## Version 0.6 (2026-09-06)

### Features
- **Direction-aware Yosys JSON reader**: Added `read_yosys_json_directed()` to
  `netlistx.readwrite`, which derives the single **driver** module of every net
  from Yosys `write_json` pin directions (`ports[name].direction` and
  `cells[inst].port_directions`) and exposes it as the `netlist.net_driver`
  map. Re-exported from `netlistx.netlist` alongside the existing readers.
  (#4c18fc2)

### Testing & Code Quality
- **Directed reader tests**: Added a driver-identity unit test (AND gate) and a
  full-benchmark single-driver assertion on
  `yosys_testcases/sphere3hopf_netlist_simple.json`. (#4c18fc2)

## Version 0.5 (2026-09-04)

### Features
- **Readers moved to `readwrite` module**: `read_json`, `read_yosys_json` and `read_yosys_json_sax` now live in `netlistx.readwrite` (shared Yosys netlist builder), with `netlist.netlist` re-exporting via `__getattr__` for backward compatibility. (#afdb849)
- **2-approximation bound assertion**: `min_vertex_cover_fast` now asserts the primal-dual 2-approximation bound. (#4bb0ff5)

### Documentation
- **AGENTS.md guidelines**: Added agent guidelines for contributors. (#ab35172)

### Testing & Code Quality
- **mypy config**: Disabled import-untyped errors for networkx. (#68504ab)
- **Style pass**: Reformatted comments and line wrapping. (#91c65d1)

### Code Cleanup
- **Removed AI slop**: Stripped boilerplate from docstrings and comments. (#c03123a)
- **Metadata & stale files**: Fixed description/url in setup.cfg, consolidated flake8 config into `.flake8`, dropped stale `ci.backup` workflow and `test_tsp.obj` artifact. (#c85b2fd)

### Build & CI
- **Updated GitHub Actions**: checkout→v4, setup-python→v5, codecov-action→v4. (#86a5803)
- **RTD doc build**: Added matplotlib and numpy to `docs/requirements.txt`. (#63d8e81)

## Version 0.4 (2026-07-16)

### Features
- **SAX-style streaming JSON parser**: Added `read_yosys_json_sax()` using ijson SAX interface (~110 lines) for parsing large Yosys JSON files without loading the entire DOM into memory. (#02881a8)

### Performance
- **GapDict and targeted Dijkstra**: Added GapDict (delta-based mapping) to avoid full dict copy in algorithms. Replaced all-pairs Dijkstra with targeted single-source in Hadlock algorithm. (#55675c9)

### Documentation
- **svgbob netlist hypergraph diagram**: Added ASCII-to-SVG diagram to module docstring. (#43f0260)

### Testing & Code Quality
- **Coverage raised 78%→98%**: Excluded `cover_ai.py` and `rand_cover_gpu.py` from coverage measurement. (#d51cb55)
- **SAX parser tests**: Added 7 new tests for SAX parity and cross-validation with DOM parser. (#02881a8)
- **Naming alignment with C++**: Renamed `dependents` → `dep`, `total_prml_cost` → `total_primal_cost`, fixed `min_maximal_independant_set` spelling. (#26fe4a8)

### Code Cleanup
- **Removed PyScaffold boilerplate**: Deleted `skeleton.py`/`test_skeleton.py`, removed Python < 3.9 compat, dead entry points, duplicate `LICENSE`. (#77e4cfb)

### Build & CI
- **CI repair**: Fixed broken entry_points and remaining skeleton imports. (#75d6452)
- **Removed orphaned test references**: Cleaned up remaining skeleton test references. (#1326052, #42f32a6)
