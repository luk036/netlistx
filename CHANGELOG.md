# Changelog

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
