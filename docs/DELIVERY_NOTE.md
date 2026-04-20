# Delivery Note

## Purpose

本项目用于对接日立电梯 Common Node 接口，覆盖以下场景：

- 登录及 token 维护
- 单梯/全梯状态查询
- 配置查询
- 门控测试
- 乘梯联调流程
- 异常中断后的复位

## Delivery Packaging

当前版本已经按现场使用习惯拆成两条主线：

- `check.py`
  - 专门查状态。
- `runner_final.py`
  - 专门做控制和流程。
- `runner_reset.py`
  - 专门做复位。
- `framework.py`
  - 兼容查询入口。
- `hitachi_cn/`
  - 业务核心模块，便于二次开发。
- `tests/`
  - 基础回归测试。
- `scripts/`
  - 交付前自检脚本。

## Suggested Handover Steps

1. 修改 `check.py` 和 `runner_final.py` 中的设备地址和账号。
2. 先将 `runner_final.py` 中的 `DRY_RUN=True` 做连通性检查。
3. 确认 `LIFT_ID`、楼层编码、前后门策略。
4. 使用 `runner_reset.py` 作为现场兜底复位工具。
