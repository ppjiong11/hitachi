# Hitachi CN Elevator Runner

这是一个为日立电梯 Common Node 接口准备的现场联调项目，已经按模块拆分，方便演示、维护和交付。

## 项目结构

```text
hitachi/
├── docs/
│   └── DELIVERY_NOTE.md
├── hitachi_cn/
│   ├── app.py
│   ├── client.py
│   ├── config.py
│   ├── errors.py
│   ├── logger.py
│   ├── models.py
│   ├── parsers.py
│   ├── utils.py
│   └── workflows.py
├── scripts/
│   └── package_check.py
├── tests/
│   ├── test_config.py
│   └── test_parsers.py
├── framework.py
├── project_config.example.py
├── project_config.py
├── pyproject.toml
├── runner.py
├── runner_final.py
├── runner_reset.py
├── requirements.txt
└── logs/
```

## 入口说明

- `python runner_final.py`
  - 主入口，适合现场跑快照、开关门测试和乘梯流程。
- `python runner_reset.py`
  - 只发复位指令，适合电梯状态卡住时使用。
- `python framework.py`
  - 适合做单次 `login/status/config/command/demo_flow` 调试。
- `python runner.py`
  - 兼容入口，保留给旧使用方式。

## 推荐使用方式

1. 修改 `project_config.py`。
2. 先运行 `python scripts/package_check.py`。
3. 第一次联调先设置 `DRY_RUN=True`。
4. 需要复位时运行 `python runner_reset.py`。

## 当前重构点

- 将原本的大脚本拆为配置、日志、API 客户端、解析器、流程编排多个模块。
- 将用户现场配置集中到 `project_config.py`，减少分散修改。
- 增加 `docs/`、`tests/`、`scripts/`、`pyproject.toml`，让项目更像正式交付工程。
- 保留原有脚本入口，避免现场使用方式变化太大。

## 安装

```bash
pip install -r requirements.txt
```

## 配置

直接编辑 `project_config.py` 里的 `CONFIG` 即可，常用字段包括：

- `BASE_URL`
- `USERNAME`
- `PASSWORD`
- `LIFT_ID`
- `REQUEST_FLOOR`
- `DEST_FLOOR`
- `RUN_SNAPSHOT`
- `RUN_DOOR_TEST`
- `RUN_TRIP_TEST`
- `RUN_RESET_ONLY`

## 注意

- `runner_final.py` 默认会实际调用接口，现场使用前请确认楼层和梯号。
- 如果是第一次联调，建议先打开 `DRY_RUN=True`。
- 日志会输出到 `logs/` 目录。
- 可用 `python -m unittest discover tests` 进行基础回归检查。
