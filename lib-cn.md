# Synopsys Liberty (.lib) 格式实战教程

## 目录
1. [Liberty 格式简介](#liberty-格式简介)
2. [理解 .lib 文件结构](#理解-lib-文件结构)
3. [操作 Liberty 文件](#操作-liberty-文件)
4. [转换为 JSON](#转换为-json)
5. [JSON Schema 验证](#json-schema-验证)
6. [从 Verilog 生成 Liberty](#从-verilog-生成-liberty)
7. [最佳实践与工具](#最佳实践与工具)
8. [端到端示例：Verilog → Liberty → JSON → 验证](#端到端示例verilog--liberty--json--验证)

---

## Liberty 格式简介

**Synopsys Liberty (.lib) 格式**是用于在电子设计自动化（EDA）工具中对半导体单元特性建模的行业标准 ASCII 格式。它为标准单元、宏单元和 I/O 焊盘提供时序、功耗和信号完整性数据。

### 关键特性
- **人类可读**的基于文本的格式
- 被所有主要 EDA 厂商使用（Synopsys、Cadence、Siemens）
- 对 PVT（工艺、电压、温度）角点下的单元行为建模
- 可编译为二进制 `.db` 格式供工具使用

### Liberty 文件提供的内容
- **时序**：单元延迟和输出转换时间（使用查找表）
- **功耗**：内部功耗、泄漏功耗和开关功耗
- **信号完整性**：噪声和串扰抗扰度
- **测试**：可测试性设计（DFT）信息

---

## 理解 .lib 文件结构

### 基本语法规则

```liberty
/* 注释使用 C 风格语法 */
group_name (optional_name) {
    attribute_name : attribute_value ;

    subgroup_name (subgroup_params) {
        /* 嵌套内容 */
        attribute_name : attribute_value ;
    }
}
```

### 完整的最小示例

以下是一个功能丰富的示例，展示了大多数关键的 Liberty 元素：

```liberty
library(example_minimal) {
    /* Library Header */
    technology ("cmos") ;
    time_unit : "1ns" ;
    voltage_unit : "1V" ;
    current_unit : "1mA" ;
    capacitive_load_unit (1, "pf") ;
    leakage_power_unit : "1nW" ;
    default_fanout_load : 1.0 ;
    default_input_pin_cap : 0.5 ;
    delay_model : "table_lookup" ;

    /* Operating Conditions (PVT) */
    nom_process : 1.0 ;
    nom_temperature : 25.0 ;
    nom_voltage : 1.2 ;

    operating_conditions (typical) {
        process : 1.0 ;
        temperature : 25.0 ;
        voltage : 1.2 ;
        tree_type : "balanced_tree" ;
    }

    /* Lookup Table Templates */
    lu_table_template (delay_template_2x2) {
        variable_1 : "input_net_transition" ;
        variable_2 : "total_output_net_capacitance" ;
        index_1 ("0.1, 1.0") ;
        index_2 ("0.05, 0.5") ;
    }

    lu_table_template (power_template_1x1) {
        variable_1 : "input_net_transition" ;
        variable_2 : "total_output_net_capacitance" ;
        index_1 ("0.1") ;
        index_2 ("0.05") ;
    }

    lu_table_template (constraint_template_2x1) {
        variable_1 : "related_constraint" ;
        variable_2 : "related_pin_transition" ;
        index_1 ("0.1, 1.0") ;
        index_2 ("0.05") ;
    }

    /* Combinational Cell: 2-input AND gate */
    cell (AND2_X1) {
        area : 5.0 ;
        is_macro : false ;

        pin (A) {
            direction : input ;
            capacitance : 0.8 ;
            fanout_load : 1.0 ;
        }

        pin (B) {
            direction : input ;
            capacitance : 0.8 ;
            fanout_load : 1.0 ;
        }

        pin (Z) {
            direction : output ;
            function : "(A & B)" ;
            max_capacitance : 1.5 ;

            timing () {
                related_pin : "A" ;
                timing_sense : positive_unate ;

                cell_rise (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.12, 0.24", "0.38, 0.52") ;
                }

                rise_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.09, 0.18", "0.70, 0.95") ;
                }

                cell_fall (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.10, 0.20", "0.32, 0.45") ;
                }

                fall_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.08, 0.16", "0.65, 0.88") ;
                }
            }

            timing () {
                related_pin : "B" ;
                timing_sense : positive_unate ;

                cell_rise (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.14, 0.26", "0.40, 0.55") ;
                }

                rise_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.10, 0.20", "0.72, 0.98") ;
                }
            }
        }

        /* Power Modeling */
        internal_power () {
            related_pin : "A" ;
            rise_power (power_template_1x1) { values ("0.05") ; }
            fall_power (power_template_1x1) { values ("0.04") ; }
        }

        leakage_power () {
            value : 0.002 ;
        }
    }

    /* Sequential Cell: D Flip-Flop */
    cell (DFF_X1) {
        area : 15.0 ;
        ff : "IQ" ;

        pin (CK) {
            direction : input ;
            clock : true ;
            capacitance : 0.7 ;
        }

        pin (D) {
            direction : input ;
            capacitance : 0.6 ;
        }

        pin (Q) {
            direction : output ;
            function : "IQ" ;

            timing () {
                related_pin : "CK" ;
                timing_type : "rising_edge" ;
                cell_rise (delay_template_2x2) {
                    values ("0.35, 0.62", "0.51, 0.78") ;
                }
                rise_transition (delay_template_2x2) {
                    values ("0.25, 0.45", "0.55, 0.82") ;
                }
            }
        }

        pin (QN) {
            direction : output ;
            function : "!IQ" ;

            timing () {
                related_pin : "CK" ;
                timing_type : "rising_edge" ;
                cell_fall (delay_template_2x2) {
                    values ("0.30, 0.55", "0.48, 0.72") ;
                }
                fall_transition (delay_template_2x2) {
                    values ("0.22, 0.40", "0.50, 0.76") ;
                }
            }
        }

        /* Timing Constraints */
        timing () {
            related_pin : "CK" ;
            timing_type : "setup_rising" ;
            rise_constraint (constraint_template_2x1) {
                values ("0.15, 0.22") ;
            }
        }

        timing () {
            related_pin : "CK" ;
            timing_type : "hold_rising" ;
            rise_constraint (constraint_template_2x1) {
                values ("0.05, 0.10") ;
            }
        }

        leakage_power () { value : 0.01 ; }
    }

    /* Combinational Cell: Inverter */
    cell (INV_X1) {
        area : 3.0 ;
        is_macro : false ;

        pin (A) {
            direction : input ;
            capacitance : 0.5 ;
        }

        pin (ZN) {
            direction : output ;
            function : "(!A)" ;
            max_capacitance : 2.0 ;

            timing () {
                related_pin : "A" ;
                timing_sense : negative_unate ;
                cell_rise (delay_template_2x2) {
                    values ("0.08, 0.18", "0.30, 0.42") ;
                }
                rise_transition (delay_template_2x2) {
                    values ("0.06, 0.14", "0.55, 0.78") ;
                }
                cell_fall (delay_template_2x2) {
                    values ("0.07, 0.16", "0.28, 0.38") ;
                }
                fall_transition (delay_template_2x2) {
                    values ("0.05, 0.12", "0.50, 0.72") ;
                }
            }
        }

        leakage_power () { value : 0.001 ; }
    }
}
```

特性展示：
- **3 种单元类型**：组合逻辑（AND2_X1、INV_X1）和时序逻辑（DFF_X1）
- **时序弧**：每个引脚多个 `timing()` 组，多种查找表类型（cell_rise、rise_transition、cell_fall、fall_transition）
- **功耗建模**：带有 rise_power/fall_power 的 internal_power，静态 leakage_power
- **时序单元**：`ff : "IQ"`、`clock : true`、时序约束（建立/保持时间）
- **查找表**：2×2（一维/二维模板），多模板引用
- **库头文件**：工艺、单位、标称 PVT 工作条件

---

## 操作 Liberty 文件

### 开源工具

多种开源工具可以解析和操作 Liberty 文件：

| 工具 | 语言 | 读取 | 写入 | 适用场景 |
|------|----------|------|-------|----------|
| `liberty-parser` | Python | ✅ | ⚠️* | 脚本编写、分析 |
| `liberty-io` | Rust | ✅ | ✅ | 生产环境、超大文件 |
| `libertyparse` | Rust | ✅ | ❌ | 内存高效解析 |
| `OpenSTA` | C++ | ✅ | ❌ | 静态时序分析 |
| `convert-lib-to-json`（技能） | Python | ✅ | ✅† | Liberty ↔ JSON 转换与 Schema 验证 |
| `lib-for-verilog`（技能） | Python | ❌ | ✅ | 通过 Yosys 从 Verilog 生成 Liberty |

*可格式化为字符串，但无专用写入器 API。
†转换为 JSON 文件；往返需要 JSON 到 Liberty 的重建。

### Python：使用 liberty-parser

**安装：**
```bash
pip install liberty-parser
```

**基本用法：**

```python
from liberty.parser import parse_liberty

# 解析 Liberty 文件
with open("your_library.lib", "r") as f:
    library = parse_liberty(f.read())

# 遍历单元
for cell_group in library.get_groups('cell'):
    cell_name = cell_group.args[0]
    print(f"Cell: {cell_name}")

    # 检查引脚
    for pin_group in cell_group.get_groups('pin'):
        pin_name = pin_group.args[0]

        if 'direction' in pin_group:
            print(f"  Pin {pin_name}: {pin_group['direction']}")

        # 提取时序表为 NumPy 数组
        timing = pin_group.get_groups('timing')
        if timing:
            # cell_rise 是子组（SUBGROUP），不是属性
            cr_groups = timing[0].get_groups('cell_rise')
            if cr_groups:
                # 值在子组内部作为数组存放
                delay_table = cr_groups[0].get_array('values')
                print(f"  Delay table shape: {delay_table.shape}")

# 修改属性
library['time_unit'] = '1ps'  # 更改时间单位

# 写回字符串
modified_lib = str(library)
with open("modified.lib", "w") as f:
    f.write(modified_lib)
```

> **API 说明**：在 `liberty-parser` v0.0.29 中，`Group` 类使用 `group_name`（而非 `.name`），`attributes` 是一个 `Attribute` 对象的**列表**（而非字典——每个对象有 `.name` 和 `.value`），而 `cell_rise` 等时序表是**子组**，而非时序组的直接属性。通过 `get_groups(name)[0].get_array('values')` 访问它们的值。

### Rust：使用 liberty-io

**Cargo.toml:**
```toml
[dependencies]
liberty-io = "0.1"
```

**Basic Usage:**
```rust
use liberty_io;
use std::fs::File;
use std::io::BufReader;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let f = File::open("library.lib")?;
    let mut buf = BufReader::new(f);

    // Parse library
    let library = liberty_io::read_liberty_bytes(&mut buf)?;

    // Access cells
    for group in &library.groups {
        if group.name == "cell" {
            println!("Cell: {}", group.arguments[0]);

            // Find pins
            for pin in &group.groups {
                if pin.name == "pin" {
                    println!("  Pin: {}", pin.arguments[0]);
                }
            }
        }
    }

    // Modify and write back
    library.groups.push(
        liberty_io::liberty::Group::new("comment", vec!["Modified by script"])
    );

    let output = File::create("modified.lib")?;
    liberty_io::write_liberty(&library, output)?;

    Ok(())
}
```

### C++: Using OpenSTA

OpenSTA provides a production-quality Liberty parser in C++:

```cpp
#include "liberty/LibertyReader.hh"
#include "liberty/LibertyVisitor.hh"

// Custom visitor to extract information
class MyLibertyVisitor : public Liberty::Visitor {
public:
    void visit(const Liberty::Group* group) override {
        if (group->name() == "cell") {
            std::cout << "Cell: " << group->argument(0) << std::endl;
        }
    }
};

int main() {
    // Parse Liberty file
    Liberty::Library* lib = Liberty::readLibertyFile("library.lib");

    if (lib) {
        // Traverse the parsed data
        MyLibertyVisitor visitor;
        lib->accept(&visitor);

        // Access attributes
        const auto& cells = lib->cells();
        for (auto* cell : cells) {
            std::cout << "Cell area: " << cell->area() << std::endl;
        }
    }

    return 0;
}
```

---

## 转换为 JSON

### 方法一：使用 libertymetric（专用工具）

```bash
pip install libertymetric
```

```python
from libertymetric.classLiberty import liberty as lutil

# 将 Liberty 转换为 JSON
lnode = lutil.read_lib('your_library.lib')
lutil.dump_json(lnode, out='output.json')

# 将 JSON 转换回 Liberty
lnode = lutil.load_json('output.json')
lutil.write_lib('reconstructed.lib', lnode)
```

### 方法二：使用 liberty-parser 的自定义 JSON 序列化

该方法递归地将 Liberty 组树结构转换为 JSON。每个组都成为一个包含 `type`、`args`、`attributes` 和可选 `groups` 的 JSON 对象。

```python
import json
from liberty.parser import parse_liberty
from liberty.types import EscapedString

def _json_safe(value):
    """Convert liberty-parser types (EscapedString, NumPy arrays) to JSON-safe types."""
    if isinstance(value, EscapedString):
        return value.value.strip('"')
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "tolist"):  # NumPy array
        return value.tolist()
    return value

def liberty_to_dict(group):
    """Recursively convert a Liberty Group to a dictionary."""
    result = {
        "type": group.group_name,  # NOT group.name
        "args": list(group.args),
    }
    # attributes is a LIST of Attribute objects (not a dict)
    attrs = {}
    for a in group.attributes:
        attrs[a.name] = _json_safe(a.value)
    if attrs:
        result["attributes"] = attrs

    if group.groups:
        result["groups"] = [liberty_to_dict(g) for g in group.groups]

    return result

# Parse and convert
with open("library.lib", "r") as f:
    library = parse_liberty(f.read())

json_data = liberty_to_dict(library)

with open("library.json", "w") as f:
    json.dump(json_data, f, indent=2)
```

The output JSON follows this recursive structure:
```json
{
  "type": "library",
  "args": ["library_name"],
  "attributes": { "time_unit": "1ns", ... },
  "groups": [
    {
      "type": "cell",
      "args": ["AND2_X1"],
      "attributes": { "area": 5.0, ... },
      "groups": [
        {
          "type": "pin",
          "args": ["Z"],
          "attributes": { "direction": "output", "function": "(A & B)" },
          "groups": [
            {
              "type": "timing",
              "args": [],
              "attributes": { "related_pin": "A", "timing_sense": "positive_unate" },
              "groups": [
                {
                  "type": "cell_rise",
                  "args": ["delay_template_2x2"],
                  "attributes": { "values": ["0.12, 0.24", "0.38, 0.52"] }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 方法三：选择性 JSON 提取

提取特定数据用于分析，而非导出整个递归结构：

```python
import json
from liberty.parser import parse_liberty
from liberty.types import EscapedString

def _json_safe(value):
    if isinstance(value, EscapedString):
        return value.value.strip('"')
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value

def extract_timing_data(lib_file):
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())

    timing_data = {}

    for cell in library.get_groups('cell'):
        cell_name = cell.args[0]
        timing_data[cell_name] = {
            "area": float(cell.get_attribute('area', 0)),
            "is_sequential": 'ff' in cell,
            "pins": {}
        }

        for pin in cell.get_groups('pin'):
            pin_name = pin.args[0]
            pin_info = {
                "direction": _json_safe(pin.get_attribute('direction', 'unknown')),
                "capacitance": float(pin.get_attribute('capacitance', 0))
            }

            # Extract timing arcs
            arcs = []
            for timing in pin.get_groups('timing'):
                arc = {
                    "related_pin": _json_safe(timing.get_attribute('related_pin', 'unknown')),
                    "timing_sense": _json_safe(timing.get_attribute('timing_sense', 'unknown')),
                    "timing_type": _json_safe(timing.get_attribute('timing_type', 'unknown')),
                }
                # Extract delay values from subgroups
                for table_name in ["cell_rise", "cell_fall", "rise_transition", "fall_transition"]:
                    tbl_grp = timing.get_groups(table_name)  # subgroup check
                    if tbl_grp:
                        table = tbl_grp[0].get_array('values')  # 'values' attribute inside
                        arc[table_name] = {
                            "shape": list(table.shape),
                            "min": float(table.min()),
                            "max": float(table.max()),
                            "mean": float(table.mean()),
                            "values": table.tolist(),
                        }
                arcs.append(arc)

            if arcs:
                pin_info["timing_arcs"] = arcs
            timing_data[cell_name]["pins"][pin_name] = pin_info

        # Extract leakage power
        leakage = cell.get_groups('leakage_power')
        if leakage:
            timing_data[cell_name]["leakage_power"] = float(
                leakage[0].get_attribute('value', 0)
            )

    return timing_data

data = extract_timing_data("library.lib")
with open("timing_analysis.json", "w") as f:
    json.dump(data, f, indent=2)
```

### 方法四：使用 convert-lib-to-json 代理技能

`convert-lib-to-json` 代理技能将方法二和方法三封装为单一命令行工具，并带有自动 Schema 验证：

```bash
# 一步完成转换和验证
python /path/to/convert-lib-to-json/convert_lib_to_json.py library.lib output.json

# 或在任务上下文中使用该技能
# task(load_skills=["convert-lib-to-json"], prompt="Convert my lib file")
```

该技能：
- 使用 `liberty-parser` 解析 .lib 文件
- 转换为方法二的 JSON 格式
- 输出人类可读的单元摘要
- 根据捆绑的 JSON Schema 进行验证
- 成功时返回退出码 0，验证失败时返回 2

---

## JSON Schema 验证

一套全面的**JSON Schema（Draft-07）**适用于方法二转换格式，位于 `liberty_json_schema.json`。该 Schema 覆盖以下内容：

| 组类型 | 覆盖内容 |
|---|---|---|
| `library`（根） | technology、time_unit、voltage_unit、delay_model、标称 PVT |
| `cell` | area、is_macro、ff、dont_use、dont_touch + 任意参数 |
| `pin` | direction、capacitance、clock、function、max_capacitance、fanout_load |
| `timing` | related_pin、timing_sense、timing_type |
| `cell_rise` / `cell_fall` / `rise_transition` / `fall_transition` | index_1、index_2、values |
| `rise_constraint` / `fall_constraint` | values |
| `internal_power` | related_pin → rise_power / fall_power 表 |
| `leakage_power` | value |
| `lu_table_template` | variable_1、variable_2、variable_3、index_1/2/3 |
| `operating_conditions` | process、temperature、voltage、tree_type |

### Schema 设计

- **递归性**：基于 `any_group` 基本类型，通过 `anyOf` 分发到特定组类型
- **宽松性**：未知组类型和属性通过 `additionalProperties` 机制落入通用的 `any_group` 捕获全部
- **类型化属性**：`attribute_value` 覆盖字符串、数字、布尔值及其数组
- **特定约束**：已知的 Liberty 组类型具有经过验证的 `required` 字段和适当的 `enum` 值

### 验证用法

```python
import json
import jsonschema

with open("library.json") as f:
    data = json.load(f)
with open("liberty_json_schema.json") as f:
    schema = json.load(f)

try:
    jsonschema.validate(instance=data, schema=schema)
    print("验证通过")
except jsonschema.ValidationError as e:
    print(f"验证失败: {e.message}")
```

---

## 从 Verilog 生成 Liberty

`lib-for-verilog` 代理技能通过使用 **Yosys** 综合 Verilog RTL 源文件并提取所有技术原语单元类型，生成人工 Liberty .lib 文件。

### 工作流程

```
Verilog (.v)
    │
    ▼  Yosys 综合（proc → opt → techmap → clean）
    │
    ▼ 临时 Yosys JSON 网表
    │
    ▼ 单元类型提取（已映射 100+ 种已知单元类型）
    │
    ▼ Liberty .lib 生成
         ├── 库头文件（工艺、单位、PVT）
         ├── 工作条件
         ├── 查找表模板（delay_template_2x2）
         └── 每个原语类型对应的单元
              ├── area、ff、参数
              ├── 引脚（方向、时钟标志、功能）
              ├── 时序桩（cell_rise/fall、rise/fall_transition）
              └── 泄漏功耗
```

### 用法

```bash
python /path/to/lib-for-verilog/lib_for_verilog.py my_design.v \
    --top top_module \
    --output cells.lib \
    --json --validate
```

输出结果：
- `cells.lib` — 包含映射原语单元的 Liberty 库
- `cells.json` — JSON 转换（通过 `convert-lib-to-json` 内部）
- 输出的 JSON 的 Schema 验证

### 提取的单元类型

该脚本知道 **100 多种 Yosys 单元类型**的端口方向，分为两类：

**Techmap 前**（`techmap` 前）：`$add`、`$mul`、`$sub`、`$mux`、`$pmux`、`$eq`、`$lt`、`$shr`、`$dff`、`$adff` 等。

**Techmap 后技术原语**（`techmap` 后）：`$_AND_`、`$_OR_`、`$_XOR_`、`$_NOT_`、`$_MUX_`、`$_DFF_P_`（上升沿 DFF）、`$_DFF_N_`（下降沿 DFF）、`$_DFF_PN0_`（带异步复位上升沿）、`$_DLATCH_P_` 等。

### 单元名称清理

Liberty 标识符不能包含 `$`。脚本会转换：
- `$` → `_dollar_`（例如 `$_AND_` → `_dollar__AND_`）
- 去掉前导 `\`（Yosys 的转义字符，用于 `\$memrd` 等）

### 实际示例：32 阶 FIR 滤波器

```bash
# A 32-tap FIR filter after Yosys synthesis produces:
python lib_for_verilog.py fir_filter.v --top fir_filter --json --validate
```
Yields 7 primitive cell types:
| Liberty 单元 | Yosys 原语 | 功能 | 引脚 |
|---|---|---|---|---|
| `_dollar__AND_` | `$_AND_` | 与门 | A, B → Y |
| `_dollar__DFF_PN0_` | `$_DFF_PN0_` | 上升沿 DFF，异步低电平复位 | C, D, R → Q |
| `_dollar__DFF_P_` | `$_DFF_P_` | 上升沿 DFF | C, D → Q |
| `_dollar__MUX_` | `$_MUX_` | 2 选 1 选择器 | A, B, S → Y |
| `_dollar__NOT_` | `$_NOT_` | 反相器 | A → Y |
| `_dollar__OR_` | `$_OR_` | 或门 | A, B → Y |
| `_dollar__XOR_` | `$_XOR_` | 异或门 | A, B → Y |

---

## 最佳实践与工具

### 编译 .lib 到 .db（Synopsys）

用于生产环境时，将 Liberty 文件编译为二进制 `.db` 格式：

```bash
# 使用 Library Compiler
lc_shell
lc_shell> read_lib my_library.lib
lc_shell> write_lib -format db my_library -output my_library.db
lc_shell> exit

# 在 Design Compiler 中使用
# dc_shell> set target_library "my_library.db"
```

### 验证方法

由于 Liberty 没有官方 Schema，验证通过以下工具进行：

1. **Synopsys Library Compiler** — 权威验证器（商业软件）
2. **开源解析器** — 语法错误时会报错
3. **JSON Schema**（`liberty_json_schema.json`）— 针对结构化的 Draft-07 Schema 验证 JSON 转换，覆盖所有已知的 Liberty 组类型
4. **Liberty 参考手册** — 官方规范文档

### 常见陷阱

| 问题 | 解决方案 |
|-------|----------|
| 缺少查找表模板 | 在使用前定义 `lu_table_template` |
| 单位不一致 | 检查 `time_unit`、`capacitive_load_unit` 设置 |
| 函数语法错误 | 使用 Liberty 表达式语法：`"(A & B)"`、`"(!A)"` |
| PVT 角点不匹配 | 确保工作条件与库数据匹配 |
| `AttributeError: 'Group' object has no attribute 'name'` | 使用 `.group_name` 替代 `.name`（liberty-parser v0.0.29 API） |
| `dict(group.attributes)` 失败 | `attributes` 是 `Attribute` 对象的**列表**——遍历并访问 `.name` / `.value` |
| 时序表返回空值 | `cell_rise` 等是**子组**而非属性——使用 `get_groups("cell_rise")` 然后调用 `.get_array("values")` |
| `EscapedString` 无法 JSON 序列化 | 通过 `.value.strip('"')` 转换（参见上面的 `_json_safe` 辅助函数） |
| `$` 出现在单元名称中（Liberty 语法错误） | 替换为 `_dollar_` 前缀 — `$` 不是有效的 Liberty 标识符字符 |
| Yosys `dfflibmap` 无法映射单元 | Techmap 后 Liberty 单元在 Yosys 0.9 中需要特定的命名约定；改用 `read_liberty -lib` 进行库注册 |
| Techmap 后的 `opt` 过程使设计归零 | 对于单元类型提取，使用 `techmap; clean` 替代 `techmap; opt` — `opt` 的激进优化可能会移除复杂设计中的所有单元 |
| Yosys 拒绝带有 `integer` 索引的过程式 `for` 循环 | 预先展开循环，或使用 `genvar` 声明 generate 循环的循环变量 |

### 资源

- **Liberty 参考手册** — 可向 Synopsys 获取（数百页）
- **Liberty 技术咨询委员会（LTAB）** — 行业治理机构
- **开源工具** — 参见「操作 Liberty 文件」章节中的表格
- **liberty-parser** — https://pypi.org/project/liberty-parser/
- **liberty-io** — https://crates.io/crates/liberty-io
- **OpenSTA** — https://github.com/The-OpenROAD-Project/OpenSTA

### 何时使用各工具

| 使用场景 | 推荐工具 |
|----------|------------------|
| 快速脚本编写和分析 | `liberty-parser`（Python） |
| 与 JSON 互转 | `convert-lib-to-json` 代理技能（Python，带 Schema 验证） |
| 处理超大型库文件（GB+） | `liberty-io`（Rust） |
| 生产级静态时序分析 | OpenSTA（C++） |
| 编写/修改 Liberty 文件 | `liberty-io`（Rust） |
| 从 RTL/Verilog 生成 Liberty | `lib-for-verilog` 代理技能（Python + Yosys） |
| Liberty JSON 的 Schema 验证 | `liberty_json_schema.json` + `jsonschema` |
| Liberty ↔ JSON 往返转换 | `libertymetric`（Python） |

---

## 端到端示例：Verilog → Liberty → JSON → 验证

从 Verilog 源文件到经过验证的 Liberty JSON 的完整流水线：

```bash
# 步骤 1：从 Verilog 生成 Liberty
python lib_for_verilog.py my_design.v --top my_top --output my_design.lib

# 步骤 2：转换为 JSON 并验证
python convert_lib_to_json.py my_design.lib my_design_converted.json

# 步骤 3（编程方式）：在 Python 中使用
from liberty.parser import parse_liberty
with open("my_design.lib") as f:
    lib = parse_liberty(f.read())

for cell in lib.get_groups("cell"):
    print(f"{cell.args[0]}: {len(cell.get_groups('pin'))} pins")
```

本教程项目包含以下可运行的示例文件：

| 文件 | 描述 |
|---|---|---|
| `example_minimal.lib` | 手工编写的 Liberty 库，包含 3 个单元 |
| `tutorial_parse_lib.py` | 基础解析：遍历单元和引脚，提取时序表为 NumPy 数组 |
| `tutorial_convert_json.py` | JSON 转换（方法一至三） |
| `tutorial_extract_timing.py` | 详细的时序/功耗提取，含统计数据 |
| `liberty_json_schema.json` | Liberty 转换的 JSON Schema（Draft-07） |
| `yosys_to_liberty.py` | Yosys JSON → Liberty .lib 转换器 |
| `yosys_sphere.lib` | 从 Yosys 网表生成的 Liberty（20 个单元） |
| `yosys_sphere_tech.lib` | 从 techmap 后原语生成的 Liberty（8 个单元） |
| `fir_filter.lib` | 从 32 阶 FIR 滤波器生成的 Liberty（7 个单元） |

---

## 总结

Synopsys Liberty 格式是一种强大且人类可读的半导体库表征标准。虽然它缺乏正式的机器可读 Schema 验证，但开源工具生态系统已经显著成熟：

- **Python** 用户有 `liberty-parser` 和 `libertymetric` 等优秀选择
- **Rust** 通过 `liberty-io` 提供高性能解析和写入器支持
- **C++** 生产级应用可以借助 OpenSTA 的解析器
- **JSON 转换**带 Schema 验证由 `convert-lib-to-json` 技能和 `liberty_json_schema.json` 提供
- **Verilog 到 Liberty 的生成**可通过 Yosys 综合和 `lib-for-verilog` 技能实现
- **JSON Schema (Draft-07)** 为 Liberty 派生的 JSON 提供了首个结构化验证，覆盖所有已知的组类型

理解此格式对于从事 ASIC 设计流程、静态时序分析或功耗估算工具的任何人来说都是必不可少的。
