
# JSON 与 JSON5 深度对比

JSON5 是 JSON 的**超集扩展**，旨在解决 JSON 语法严格导致的可读性差、维护困难等问题。所有有效的 JSON 都兼容 JSON5，但反之不成立。

---

## 一、核心区别对比表

| 特性 | **JSON** (标准) | **JSON5** (扩展) |
| :--- | :--- | :--- |
| **注释** | ❌ 完全禁止 | ✅ 支持 `//` 单行和 `/* */` 多行注释 |
| **键名引号** | ✅ 必须双引号 `"key"` | ✅ 可省略引号 `{key: "value"}` |
| **字符串引号** | ✅ 仅双引号 `"str"` | ✅ 支持单引号 `'str'` 和双引号 |
| **尾部逗号** | ❌ 禁止 `{a:1,b:2,}` | ✅ 允许对象/数组末尾保留逗号 |
| **数字格式** | ❌ 严格格式，禁止前导零 | ✅ 支持十六进制 `0xFF`、前导零 `010`、Infinity/NaN |
| **多行字符串** | ❌ 必须转义 `\n` | ✅ 支持反斜杠换行 `"line1\<br>line2"` |
| **特殊字符** | ✅ 必须转义 | ✅ 允许部分未转义字符 |
| **标准状态** | RFC 8259 官方标准 | 社区提案，非官方标准 |

---

## 二、语法示例对比

### **1. 标准 JSON 写法**
```json
{
  "name": "HarmonyOS",
  "version": 3.0,
  "features": ["分布式", "ArkUI"],
  "config": {
    "debug": false,
    "apiLevel": 12
  }
}
```

### **2. 等效 JSON5 写法**
```json5
{
  // 应用基本信息
  name: 'HarmonyOS',           // 无引号键名 + 单引号字符串
  version: 3.0,
  features: [
    '分布式',
    'ArkUI',                  // 尾部逗号，方便增删
  ],
  config: {
    debug: false,
    apiLevel: 0xC,             // 十六进制数字
  }, /* 配置区块结束 */
}
```

---

## 三、Python 实现对比

### **标准库 `json`**
```python
import json

# 无需安装，开箱即用
data = json.loads('{"key": "value"}')
json_str = json.dumps(data, indent=2, ensure_ascii=False)
```

### **第三方库 `json5`**
```python
import json5

# 需手动安装: pip install json5
json5_text = """
{
  // 这是注释
  unquotedKey: '单引号值',
  trailingComma: true,
}
"""

data = json5.loads(json5_text)  # 解析JSON5
json5_str = json5.dumps(data, indent=2)  # 生成JSON5格式
```

---

## 四、适用场景分析

| 场景 | **推荐格式** | 理由 |
| :--- | :--- | :--- |
| **API 数据交换** | **JSON** | 所有系统/语言原生支持，兼容性最强 |
| **配置文件** | **JSON5** | 支持注释和灵活语法，便于维护和协作 |
| **日志存储** | **JSON** | 性能更好，体积更小，解析更快 |
| **调试/开发** | **JSON5** | 可添加注释，格式容错性高 |
| **跨平台项目** | **JSON** | 部分老旧工具链不支持 JSON5 |
| **前端工程化** | **JSON5** | 已被 `.eslintrc.json5` 等主流工具采纳 |

---

## 五、关键注意事项

### **⚠️ 兼容性问题**
- JSON5 **不是**官方标准，部分老旧工具、数据库、编程语言可能无法直接解析
- 生产环境使用前，确认所有消费方都支持 JSON5 解析
- 必要时可通过工具转换：`JSON5 → JSON` 再传输

### **性能差异**
- `json` (标准库) > `json5`  
  由于 `json5` 是纯 Python 实现且语法更复杂，性能比标准库慢 **2-5 倍**，不适合高频序列化场景

### **类型支持**
- `json` 仅支持基本类型（dict/list/str/int/float/bool/None）
- `json5` 额外支持 `Infinity`, `NaN`, `Hex` 等特殊值
- 如需高性能+复杂类型，应考虑 `orjson` 而非 `json5`

---

## 六、选型决策建议

```plaintext
需要处理配置/人类可读数据？
├── 是 → 文件需要注释或灵活语法？
│   ├── 是 → 使用 JSON5 (pip install json5)
│   └── 否 → 使用标准 JSON
└── 否 → 高性能数据交换？
    ├── 是 → 使用 orjson/ujson
    └── 否 → 使用标准库 json
```

### **最终建议**
- **默认选择：标准 JSON** - 兼容性和性能最优
- **配置文件：JSON5** - 提升可维护性，但需团队统一规范
- **避免误区**：不要在需要高性能或跨系统通信的场景使用 JSON5

如需将现有 JSON 配置文件迁移至 JSON5，可使用 `json5` 库直接解析，无需修改代码逻辑，只需扩展语法即可。

---


# Python JSON处理库对比与选型指南

Python生态中处理JSON的库可分为**核心处理库**和**专用工具库**两大类。以下是主流库的详细对比和选型建议：

---

## 一、核心JSON处理库对比

| 库名称 | 性能 | 特点 | 适用场景 | 安装方式 |
|--------|------|------|----------|----------|
| **`json`** (标准库) | 基准 | 内置、API简单、兼容性好 | 90%的日常场景 | 无需安装 |
| **`orjson`** | ⭐⭐⭐⭐⭐ (最快) | Rust编写、支持 datetime/UUid、返回 bytes | 高性能API服务 | `pip install orjson` |
| **`ujson`** | ⭐⭐⭐⭐ (快3-10倍) | C实现、速度极快、部分类型不支持 | 大规模数据解析 | `pip install ujson` |
| **`simplejson`** | ⭐⭐⭐ (略优于标准库) | 兼容标准库、功能增强、支持 Decimal | 需要额外功能的场景 | `pip install simplejson` |
| **`rapidjson`** | ⭐⭐⭐⭐ (比ujson更快) | C++实现、内存占用低 | 超大规模数据处理 | `pip install rapidjson` |
| **`pysimdjson`** | ⭐⭐⭐⭐⭐ (SIMD加速) | 按需解析、超低内存、接口兼容 | 流式处理大文件 | `pip install pysimdjson` |

### 1. **标准库 `json`**
- **优点**：无需安装，开箱即用，文档完善，兼容性最佳
- **缺点**：性能一般，不支持特殊类型（如 `datetime`）序列化
- **示例**：
  ```python
  import json
  data = json.loads('{"name": "Alice", "age": 25}')
  json_str = json.dumps(data, indent=2)  # 美化输出
  ```

### 2. **`orjson` (首选高性能方案)**
- **核心优势**：性能是标准库的**5-10倍**，支持 `datetime`, `UUID`, `dataclass` 等类型
- **重要限制**：`dumps()` 返回 **bytes** 而非 str，**不支持 `indent` 参数**（无法美化输出）
- **推荐场景**：FastAPI等高性能Web服务、需要序列化复杂类型的API接口
- **示例**：
  ```python
  import orjson
  data = {"timestamp": datetime.now()}
  json_bytes = orjson.dumps(data)  # 返回bytes
  # 需要主动解码：json_bytes.decode()
  ```

### 3. **`ujson` (UltraJSON)**
- **特点**：纯C实现，速度比标准库快3-10倍，但兼容性稍差
- **注意**：不支持自定义类的序列化，对异常JSON格式处理较严格
- **适合**：日志分析、数据管道等需要快速解析大规模JSON的场景

### 4. **`simplejson`**
- **定位**：标准库的增强版，完全兼容API，支持 `use_decimal=True` 等扩展参数
- **性能**：略优于标准库，但不及 `orjson`/`ujson`
- **适用**：需要处理 `Decimal`、`NaN` 等特殊值的项目

### 5. **`rapidjson` 和 `pysimdjson`**
- **极致性能**：两者都比 `ujson` 更快，`pysimdjson` 通过SIMD指令优化
- **特色**：`pysimdjson` 支持**按需解析**（无需加载整个文件），内存占用极低
- **适用**：处理GB级JSON文件、实时流数据处理

---

## 二、专用工具库（特定场景）

| 库名称 | 功能 | 适用场景 |
|--------|------|----------|
| **`pandas`** | 读取JSON为DataFrame | 数据科学分析 |
| **`json-repair`** | 修复损坏/无效的JSON字符串 | 处理LLM输出 |
| **`jsondiff`** | 对比两个JSON对象的差异 | 配置比对、测试断言 |
| **`jq`** | 类JSONPath的查询语法 | 复杂嵌套结构查询 |
| **`demjson`** | 支持JSONPath表达式 | 动态数据提取 |

---

## 三、选型决策树

```plaintext
需要处理JSON吗？
├── 是 → 数据量大吗？
│   ├── 否 → 使用标准库 json (简单可靠)
│   └── 是 → 需要特殊类型支持吗？
│       ├── 是 (datetime等) → 使用 orjson
│       └── 否 → 使用 ujson 或 rapidjson
├── 否 → 有其他需求吗？
    ├── 修复损坏JSON → json-repair
    ├── 对比差异 → jsondiff
    ├── 数据分析 → pandas.read_json()
    └── 复杂查询 → jq
```

---

## 四、最终推荐

### **⭐ 默认选择：标准库 `json`**
**理由**：99%的教程和代码库都使用它，无依赖，维护成本低。对于配置读取、小型API等场景完全够用。

### **⭐ 高性能场景：`orjson`**
**理由**：在FastAPI等现代Web框架中已成为事实标准。虽然返回bytes且不支持indent，但其性能优势和类型支持足以弥补。

### **⭐ 大数据处理：`pysimdjson`**
**理由**：内存占用极低，可流式处理，避免OOM。适合TB级日志分析。

### **⚠️ 不建议在新项目中使用：`ujson`**
**理由**：`orjson` 在各方面都已超越，且 `ujson` 维护活跃度下降，社区正逐步迁移。

---

## 五、性能参考数据

根据真实基准测试，序列化/反序列化耗时对比（越小越好）：
- `orjson` : 1.0x (基准)
- `ujson` : 1.5-2.0x
- `rapidjson` : 1.8-2.5x
- `json` (标准库) : 5.0-7.0x

## 总结

**新手/常规项目**：直接用 `json`，别纠结。  
**生产级API服务**：无脑选 `orjson`。  
**海量数据处理**：测试 `pysimdjson` 或 `rapidjson`。  
**特定需求**：查表选择专用工具库。

记住：** premature optimization is the root of all evil **。先让代码跑起来，遇到性能瓶颈再考虑更换JSON库。