# Hitachi CN Elevator Runner

这是一个为日立电梯 Common Node 接口准备的现场联调项目，已经拆成“查状态”和“做控制”两条独立路径，便于现场快速使用。

## 项目结构

```text
hitachi/
├── check.py
├── runner_final.py
├── runner_reset.py
├── framework.py
├── runner.py
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
├── pyproject.toml
├── requirements.txt
└── logs/
```

## 入口说明

- `python check.py`
  - 只负责查状态，适合第一次联调。
- `python runner_final.py`
  - 主控制入口，适合跑快照、开关门测试和乘梯流程。
- `python runner_reset.py`
  - 只发复位指令，适合电梯状态卡住时使用。
- `python framework.py`
  - 兼容入口，目前等同于 `check.py`。
- `python runner.py`
  - 兼容入口，保留给旧使用方式。

## 推荐使用方式

1. 查状态时修改 `check.py`。
2. 控制和联调时修改 `runner_final.py`。
3. 第一次联调先在 `runner_final.py` 里设置 `DRY_RUN=True`。
4. 需要复位时运行 `python runner_reset.py`。

## 安装

```bash
pip install -r requirements.txt
```

## 怎么查状态

直接编辑 `check.py`：

- `CONFIG`
  - 连接信息，比如 `BASE_URL`、`USERNAME`、`PASSWORD`
- `CHECK["LIFT_ID"]`
  - 查询哪台梯，设成 `None` 可以看全部
- `CHECK["SHOW_CONFIG"]`
  - 是否顺便打印配置字段

然后运行：

```bash
python3 check.py
```

## 怎么控制电梯

直接编辑 `runner_final.py` 里的 `CONFIG`：

- `LIFT_ID`
- `REQUEST_FLOOR`
- `DEST_FLOOR`
- `RUN_SNAPSHOT`
- `RUN_DOOR_TEST`
- `RUN_TRIP_TEST`
- `RUN_RESET_ONLY`
- `DRY_RUN`
- `DOOR_HOLD_SEC`

然后运行：

```bash
python3 runner_final.py
```

## HOLD DOOR 时间在哪改

`HOLD DOOR` 时间在 [runner_final.py](/Users/wangjianyu/code/hitachi/runner_final.py) 的 `CONFIG["DOOR_HOLD_SEC"]` 里控制，单位是秒。

比如：

```python
"DOOR_HOLD_SEC": 3.0,
```

这表示门打开后保持 3 秒再继续后续流程。

## 注意

- `runner_final.py` 默认可能会真实发控制命令，现场使用前请确认楼层和梯号。
- 如果只是第一次试联调，建议先把 `DRY_RUN=True`。
- 日志会输出到 `logs/` 目录。
- 可用 `python3 scripts/package_check.py` 和 `python3 -m unittest discover tests` 做基础检查。
