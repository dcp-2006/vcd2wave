# vcd2wave

将 VCD (Value Change Dump) 波形文件转换为美观的 HTML 可视化页面的轻量级工具。

不再需要打开笨重的 EDA 工具来看波形——一条命令，浏览器里直接看。

## ✨ 特性

- 🚀 **零依赖** — 纯 Python 3 标准库，无需安装任何额外包
- 🎨 **美观输出** — 生成干净、可交互的 HTML 波形页面
- 📊 **多信号支持** — 单比特、多比特总线信号都能渲染
- 🔍 **递归解析** — 自动提取顶层及子模块的所有信号
- ⏱️ **自适应时间轴** — 自动缩放，ns/us/ms 智能切换
- 📦 **即拿即用** — 单个文件，复制到任何地方都能跑

## 🚀 快速开始

```bash
# 基本用法
python vcd2wave.py dump.vcd

# 指定输出文件名
python vcd2wave.py dump.vcd my_waveform.html

# 批量转换 (PowerShell)
Get-ChildItem *.vcd | ForEach-Object { python vcd2wave.py $_ }
```

转换完成后会自动在浏览器中打开生成的 HTML 文件。

## 📋 示例

```bash
# 使用 iverilog 生成 VCD 并查看
iverilog -o test.vvp test.v tb_test.v
vvp test.vvp -lxt2
python vcd2wave.py dump.vcd
```

## 🧪 测试

```bash
python -m pytest tests/
```

## 📁 项目结构

```
vcd2wave/
├── vcd2wave/          # 核心模块
│   ├── __init__.py
│   ├── parser.py      # VCD 解析器
│   └── renderer.py    # HTML 渲染器
├── tests/             # 单元测试
├── examples/          # 示例文件
├── .github/           # CI 配置
├── README.md
├── LICENSE
├── setup.py
└── .gitignore
```

## 🔧 技术细节

VCD 解析器支持：
- `$var` 定义的标量和向量信号
- 嵌套 `$scope` / `$upscope` 层次结构
- 标量值变化 (`0`, `1`, `x`, `z`)
- 向量值变化 (`b` 格式)
- 时间戳 (`#` 格式)

## 📄 许可证

MIT License — 自由使用、修改和分发。

---

_Generated with ❤️ by 老婆 for 老公_
