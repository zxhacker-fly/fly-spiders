# Python 中执行 JavaScript 全面笔记

> 场景：爬虫/逆向时还原前端加密；复用前端业务算法；运行混淆 / 压缩后的 JS；在后端嵌入少量 JS 逻辑。
> 提示：本文示例中的第三方包可能尚未在当前环境安装，属于演示代码。请按安装速查章节先安装依赖再运行。

## 1. 常见方案总览

| 方案 / 包 | 类型 | 依赖/安装 | 性能延迟 | ES 兼容 | 是否有 DOM | 适合场景 | 不适合 |
|-----------|------|-----------|----------|---------|-----------|-----------|---------|
| Node.js 子进程 (subprocess / execjs 调用 Node) | 外部进程 | 需安装 Node | 启动中等；复用后快 | 最新（取决于 Node 版本） | 否 | 复杂算法、现代语法、已有 Node 环境 | 高频微调用、沙箱隔离要求高 |
| PyExecJS (`execjs`) | 统一封装 | 自动探测多种运行时 | 与底层运行时一致；第一次编译有开销 | 取决于检测到的运行时 | 否 | 快速接入 JS 函数，无需关心具体引擎 | 高频并发、需要高级控制/超时 |
| PyMiniRacer | 嵌入式 V8 | 预编译 wheel（部分平台） | 非常低（内存中） | 较新 ES 特性 | 否 | 高频、签名算法、反混淆后执行 | 需要 DOM / 浏览器 API |
| quickjs (`python-quickjs`) | 嵌入式 QuickJS | 纯 C 小巧 | 很低 | ES2020 左右 | 否 | 轻量、部署简单、算法调用 | 需最新 ES 新特性、极大量并发（GC策略） |
| js2py | 纯 Python 解释 | 仅 Python | 慢 | 旧（部分 ES5/ES6 不完整） | 否 | 无编译环境、临时调试小函数 | 复杂/现代 JS、大量执行 |
| selenium | 真浏览器自动化 | 浏览器 + 驱动 | 高 | 浏览器完整 | 是 | 需要 DOM、页面事件、资源加载 | 仅算算法（太重）、高并发 |
| Playwright | 真浏览器自动化 | 安装浏览器内核 | 比 selenium 更稳，仍高 | 浏览器完整 | 是 | 逆向复杂请求、评估动态渲染 | 仅计算函数、小脚本 |
| PyV8 / v8eval / dukpy | 嵌入式 | 安装和编译难度各异 | 低 | 视维护度 | 否 | 老项目历史遗留 | 新项目（维护度低） |

## 2. 选型决策速览

按需求优先级：
- 纯算法 / 加密签名：PyMiniRacer > quickjs > Node 子进程 > PyExecJS > js2py
- 需最新语言特性：Node 子进程 (或新版 PyMiniRacer)
- 不能安装编译组件：js2py (权宜) > execjs + 本机 JScript (Windows 限制多)
- 需要 DOM、XHR、Cookie、渲染：Playwright 或 Selenium
- 高频低延迟调用：嵌入式 (PyMiniRacer / quickjs) 长驻上下文
- 需要多运行时自动适配：PyExecJS

## 3. 核心对比细节

### PyExecJS (`execjs`)
- 自动检测可用 JS 引擎：Node、JavaScriptCore、JScript 等。
- 接口统一：`compile(code)` 得到上下文，`call(func, *args)` 直接调用。
- 适合快速使用；劣势是缺乏执行超时、内存限制、原生沙箱控制。

### PyMiniRacer
- 直接嵌入 V8，启动即可，适合大量短时间内函数调用。
- 支持 `ctx.call` / `ctx.eval`；可设置 `timeout` 避免死循环。
- 不提供 DOM；处理加密、混淆 JS 表现优秀。

### quickjs
- QuickJS 体积小、启动快；适合服务化签名计算。
- 支持部分现代语法（BigInt、async/await 视版本）。
- 较少依赖，跨平台部署方便。

### js2py
- 将 JS AST 转成 Python 执行；速度慢，不适合大量调用。
- 兼容性不足：现代语法常失败；适合作为“应急方案”。

### Node 子进程
- 真实 V8 + 完整 npm 生态。
- 子进程启动成本：适合批量执行或保持驻留（可用长驻服务 / IPC）。
- 可通过 `--no-warnings`、`--input-type=module` 等参数控制行为。

### Selenium / Playwright
- 当 JS 算法高度依赖 DOM / Web API / 网络请求 或 与页面上下文耦合，才使用。
- 成本高：资源占用、启动时间、并发困难（需池化）。

## 4. 主要使用示例

### 4.1 execjs 使用 Node
```python
import execjs

# 查看支持运行时（返回 dict）
print(execjs.available_runtimes())
runtime = execjs.get("Node")  # 指定 Node，可省略让它自动选
js_code = """
function sign(x){ return x.split('').reverse().join('') + ':' + x.length; }
function add(a,b){ return a+b; }
"""
ctx = runtime.compile(js_code)
print(ctx.call("add", 10, 32))
print(ctx.call("sign", "abcdef"))
print(execjs.eval("1 + 2 * 5"))
```

### 4.2 PyMiniRacer
```python
from py_mini_racer import py_mini_racer
ctx = py_mini_racer.MiniRacer()
ctx.eval("function enc(s){ return s.split('').reverse().join('') }")
print(ctx.call("enc", "hello"))
# 死循环示例（请勿真的执行在生产环境）
try:
    ctx.eval("while(true){}");
except Exception as e:
    print("执行异常", e)
```

### 4.3 quickjs
```python
import quickjs
ctx = quickjs.Context()
ctx.eval("function mul(a,b){ return a*b }")
print(ctx.call("mul", 7, 6))
```

### 4.4 js2py
```python
import js2py
context = js2py.EvalJs()
context.execute("function f(n){return n*n + 1}")
print(context.f(9))
```

### 4.5 Node 子进程 (手动)
```python
import subprocess, json
js = """
function calc(a,b){ return a*b + 7 }
console.log(JSON.stringify(calc(6,9)))
"""
cp = subprocess.run(["node", "-e", js], text=True, capture_output=True, check=True)
value = json.loads(cp.stdout.strip())
print(value)
```

### 4.6 Playwright（需要 DOM 或网络）
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    title = page.evaluate("() => document.title")
    print(title)
    browser.close()
```

## 5. 性能与架构建议
- 高频调用：使用嵌入式引擎，保持单例上下文，避免重复编译。
- Node：若多次调用，建议
  1) 启动常驻子进程（stdin/stdout JSON-RPC）；
  2) 或使用本地 HTTP/Unix Socket 服务。
- 浏览器自动化：建立浏览器池，限制最大实例数，复用页面（`page`）重置状态。

### 简易 Node RPC 服务思路
Python 端：发送 JSON {func:"sign", args:[...]}；Node 端：加载算法文件后监听 stdin，执行函数并返回结果。减少每次编译与启动成本。

示例（精简原型）：
```python
# rpc_client.py
import json, subprocess, threading

class NodeRPC:
    def __init__(self, script_path):
        self.proc = subprocess.Popen(
            ["node", script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        self.lock = threading.Lock()
    def call(self, func, *args):
        req = {"func": func, "args": args}
        line = json.dumps(req) + "\n"
        with self.lock:
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
            resp = self.proc.stdout.readline().strip()
        return json.loads(resp)
```
```javascript
// rpc_server.js
const fs = require('fs');
// 加载算法代码
// require('./algo.js'); 或 eval(fs.readFileSync('algo.js','utf8'))
function sign(x){return x.split('').reverse().join('')}

const readline = require('readline').createInterface({input: process.stdin});
readline.on('line', line => {
  try {
    const req = JSON.parse(line);
    const fn = req.func;
    let result;
    if(fn === 'sign') result = sign(...req.args);
    else result = null;
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch(e) {
    process.stdout.write(JSON.stringify({error: e.message}) + '\n');
  }
});
```

## 6. 类型与数据转换注意点
- BigInt：在 Node/QuickJS 中 `BigInt` -> 转字符串：`big.toString()` 后返回。
- Undefined / Null：Python 中通常映射为 `None`；注意区分 `0` / 空字符串。
- 日期：JS `Date.getTime()` -> Python `datetime.fromtimestamp(ms/1000)`。
- Buffer / Uint8Array：在 JS 侧转为 base64：`Buffer.from(arr).toString('base64')`；Python 用 `base64.b64decode`。
- 异步函数：嵌入式引擎通常不直接支持 `await`，可包装为同步：在 JS 中给出纯同步版本或使用 Promise.then 返回值序列化。

## 7. 常见逆向场景策略
| 场景 | 推荐路径 |
|------|----------|
| 前端混淆加密 (请求签名) | 抽取相关函数 -> 清理 IIFE -> PyMiniRacer/quickjs 调用 |
| 多模块 import/require | 保留 Node 项目结构 -> Node RPC |
| 依赖 DOM/window | Playwright/Selenium |
| 旧语法少量函数 | js2py / execjs |
| 超高并发签名 (1000+ QPS) | 引擎池：预建多个上下文轮询 |

## 8. 可靠性与安全
- 不执行来源不明或用户拼接的 JS。
- 超时控制：PyMiniRacer `timeout`；`subprocess.run(..., timeout=秒)`；Playwright 页面脚本可用 `page.evaluate` 限制总体超时。
- 进程隔离：高风险 JS -> 独立子进程，崩溃可重启。
- 输入输出统一走 JSON，避免字符串拼接注入。
- 对返回值做格式验证（长度、类型、正则）。

## 9. 调试与混淆还原建议
- 格式化：`prettier`、`js-beautify`。
- 去混淆：还原变量名、移除死代码、展开控制流。
- 逐步注释与打印：定位核心算法函数。
- Hook `eval`：将传入字符串打印保存再分析。
- 如果遇到 Webpack 包装：只提取需要模块函数，不要整包执行。

## 10. 统一封装示例（PyMiniRacer）
```python
from py_mini_racer import py_mini_racer
import threading

class JSExecutor:
    def __init__(self, scripts, timeout=2000):
        self.ctx = py_mini_racer.MiniRacer()
        self.timeout = timeout
        for path in scripts:
            with open(path, 'r', encoding='utf-8') as f:
                self.ctx.eval(f.read())
        self._lock = threading.Lock()
    def call(self, func, *args):
        with self._lock:
            return self.ctx.call(func, *args)
```

## 11. 快速对照总结
- 最轻：js2py（功能最弱）
- 综合易用 + 自动探测：execjs
- 高性能嵌入：PyMiniRacer / quickjs
- 完整浏览器：Playwright / Selenium
- 生态最强：Node 子进程

## 12. 推荐实践清单
- 抽取最小算法子集，不要整份前端打包文件直接跑。
- 初始化阶段编译所有 JS。
- 使用 JSON 作为跨语言协议。
- 加入超时、异常捕获、调用计数监控。
- 输出做校验（签名长度/格式）。
- 引擎池：预热 N 个上下文（不同线程争用时避免等待）。

## 13. 安装与兼容速查
```bash
pip install execjs          # 需要系统有 Node 或其他运行时
pip install py-mini-racer   # V8 嵌入（若平台有预编译）
pip install python-quickjs  # QuickJS
pip install js2py           # 纯 Python
pip install playwright && playwright install chromium  # 安装浏览器内核
pip install selenium        # 需要浏览器驱动 (ChromeDriver 等)
```
- Windows 没有 Node 时：可安装 Node 或让 execjs 退回 JScript（功能受限）。
- BigInt 需求：确保运行时支持（Node >=10，PyMiniRacer 新版支持）。

## 14. 决策流程（文字版）
1. 是否需要 DOM / 网络事件复用？需要 -> 浏览器 (Playwright/Selenium)；不需要 -> 继续。
2. JS 是否依赖大量模块/打包系统？是 -> Node 子进程/RPC；否 -> 继续。
3. 调用频率是否高 (>= 数百 QPS)？高 -> 嵌入式 (PyMiniRacer / quickjs)；低 -> 继续。
4. 部署是否允许编译/原生扩展？不允许 -> js2py / execjs；允许 -> 嵌入式或 Node。
5. 是否必须最新 ES 特性 (动态 import、私有字段等)？是 -> Node；否 -> 任一嵌入式。
6. 是否需要自动选择运行时？是 -> execjs；否 -> 针对性选择。

## 15. 常见问题 FAQ
- Q: execjs 调用频繁很慢怎么办？
  A: 改为长驻 Node RPC；或迁移到 PyMiniRacer/quickjs。
- Q: BigInt 返回报错？
  A: JS 侧 `return big.toString()`，Python 再解析或用 `int()`。
- Q: 混淆代码大量 `eval`？
  A: Hook `eval` 输出参数；手动展开后只保留必要函数。
- Q: 浏览器自动化太慢？
  A: 减少页面跳转；使用单页复位技术（重写变量、清理监听）；或迁移算法到纯 JS 文件在嵌入式执行。

---
最后决策：根据“是否需要 DOM”和“调用频率 & 部署限制”两要素初筛，再按语法特性与性能确定最终引擎。
