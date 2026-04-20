# Hitachi Elevator Integration Handover

## 1. Document Purpose

本文件用于对日立电梯 Common Node 对接项目进行阶段性交接，目标读者包括：

- CEO / 管理层
- 后续接手开发或现场联调人员
- 需要理解当前项目投入、输出和剩余风险的项目相关方

本文档基于当前代码仓库、现场联调结论、以及日立 Common Node API Annex 资料引用信息整理而成。

## 1.1 Reference Documents

当前项目对应的原始规范文件路径如下：

- [SRD0000116_Common Node API Specification_Annex 1.pdf](/Users/wangjianyu/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_1vgeyjwszwwl22_47d0/msg/file/2026-04/SRD0000116_Common Node API Specification_Annex 1.pdf)
- [SRD0000116_Common Node API Specification_Annex 2.pdf](/Users/wangjianyu/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_1vgeyjwszwwl22_47d0/msg/file/2026-04/SRD0000116_Common Node API Specification_Annex 2.pdf)
- [SRD0000116_Common Node API Specification_Annex 3.pdf](/Users/wangjianyu/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_1vgeyjwszwwl22_47d0/msg/file/2026-04/SRD0000116_Common Node API Specification_Annex 3.pdf)

建议后续将这三份 PDF 正式复制到项目 `docs/` 目录或团队共享盘固定位置，避免微信容器路径后续变化。

## 2. Project Background

本项目目标是打通机器人与日立电梯 Common Node 接口之间的控制链路，逐步完成以下能力：

- 登录并获取 token
- 获取单梯状态字段
- 获取电梯配置字段
- 发送门控命令并验证生效
- 发送呼梯命令并验证电梯到达
- 发送目标楼层命令并验证到达
- 组合出可供机器人使用的完整乘梯流程

当前阶段，项目已经从“接口试通”推进到“可执行的测试脚本集合 + 手动机器人完整流程”。

## 3. Work Completed

### 3.1 Codebase Refactor and Packaging

原始脚本已经整理为模块化结构，核心逻辑拆分到 `hitachi_cn/` 包内，主要包含：

- API client
- logging
- parsing
- workflow orchestration
- error handling

同时根据现场实际操作习惯，拆出了多个独立 runner，避免一个脚本承担所有用途。

### 3.2 Working Test Entrypoints

当前仓库中的主要脚本如下：

- [check.py](/Users/wangjianyu/code/hitachi/check.py)
  - 查询单梯状态和配置
- [door_test.py](/Users/wangjianyu/code/hitachi/door_test.py)
  - 单独测试开门 / 关门 / cycle
- [call_test.py](/Users/wangjianyu/code/hitachi/call_test.py)
  - 单独测试呼梯
- [full_flow_test.py](/Users/wangjianyu/code/hitachi/full_flow_test.py)
  - 较完整的流程测试入口
- [robot_manual_runner.py](/Users/wangjianyu/code/hitachi/robot_manual_runner.py)
  - 手动确认机器人进出电梯的完整流程
- [runner_reset.py](/Users/wangjianyu/code/hitachi/runner_reset.py)
  - 清状态 / 复位入口

### 3.3 Validation Already Completed On Site

现场已经验证通过的内容包括：

- 登录 Common Node 成功
- 能稳定获取 `liftstatus`
- 能读取电梯配置
- 能发送门控命令
- 能控制开门和关门

这意味着最基础的通信链路、认证链路、状态读取链路、门控控制链路已经可用。

## 4. Confirmed On-Site Rules

以下结论不是纸面推测，而是通过现场调试逐步确认出来的，后续开发必须按这些规则理解：

### 4.1 Operation Mode

- `liftOperationMode = 4`
  - 现场定义为“正常可呼梯状态”
- 因此当前脚本默认将 `4` 视为正常模式

### 4.2 Registered Fields

以下字段用于判断命令是否已被系统登记：

- `frontReqFloorRegistered`
- `frontDestFloorRegistered`
- `frontDoorOpenRegistered`
- `rearReqFloorRegistered`
- `rearDestFloorRegistered`
- `rearDoorOpenRegistered`

当前项目中的正确理解是：

- command 只需要发送一次
- `registered` 字段只是用于 check / 验证
- 不需要因为 `registered = 1` 再补发同一条命令

这条结论是现场联调后确认并已经同步到现有代码逻辑中的。

### 4.3 Door Command Behavior

- `frontopen = 1`
  - 请求前门打开
- `frontopen = 0`
  - 请求前门关闭 / 释放开门命令
- 后门对应 `rearopen`

### 4.4 Floor Semantics

- `requestfloor`
  - 电梯来接机器人所在楼层
- `destinationfloor`
  - 机器人进入电梯后要去的目标楼层

这两个字段不能混用。

现场确认示例：

- 机器人当前在 1 楼时，如果要让电梯来接它，应发送 `requestfloor = 1`
- 机器人进入电梯后要去 2 楼，应发送 `destinationfloor = 2`

### 4.5 Robot In-Car Status

- `amrincar = 1`
  - 机器人已经进入轿厢
- `amrincar = 0`
  - 机器人已经离开轿厢

完整流程中，`amrincar` 必须作为显式步骤处理，不能省略。

## 5. Current Code Logic

### 5.1 Status Check

[check.py](/Users/wangjianyu/code/hitachi/check.py) 负责：

- 登录
- 获取 `liftstatus`
- 可选获取 `liftconfig`

这是最安全、最适合第一次联调的入口。

### 5.2 Door Test

[door_test.py](/Users/wangjianyu/code/hitachi/door_test.py) 当前支持三种模式：

- `DOOR_TEST_ACTION="1"` 或 `"open"`
  - 只开门
- `DOOR_TEST_ACTION="0"` 或 `"close"`
  - 只关门
- `DOOR_TEST_ACTION="cycle"`
  - 开门 -> 等待 `DOOR_HOLD_SEC` -> 关门

### 5.3 Call Test

[call_test.py](/Users/wangjianyu/code/hitachi/call_test.py) 负责：

- 发 `requestfloor`
- 检查 `frontReqFloorRegistered` / `rearReqFloorRegistered`
- 可选等待 `liftArriveReqFloor == 1`
- 可选测试结束后清零请求

### 5.4 Manual Robot Full Flow

[robot_manual_runner.py](/Users/wangjianyu/code/hitachi/robot_manual_runner.py) 负责：

1. 呼梯到 `REQUEST_FLOOR`
2. 到达后开门
3. 人工确认机器人进入
4. 发送 `amrincar = 1`
5. 发送 `destinationfloor`
6. 关门
7. 等待到目标楼层
8. 开门
9. 人工确认机器人离开
10. 发送 `amrincar = 0`
11. 关门并清状态

这是当前最贴近“机器人真实接入”的脚本。

## 6. Practical Attention Points

### 6.1 DRY_RUN

所有关键控制脚本中都支持 `DRY_RUN` 概念。

- `DRY_RUN=True`
  - 只打印命令，不真实发送
- `DRY_RUN=False`
  - 真实发送命令到电梯

现场真测前，必须确认是否已经切换到 `False`。

### 6.2 Snapshot

门控或呼梯测试不需要每次都先获取完整 snapshot。  
当前脚本已经尽量把 `RUN_SNAPSHOT` 关掉，避免浪费时间和干扰判断。

### 6.3 Mode Check

当前代码默认认为：

- `NORMAL_OPERATION_MODE = 4`

如果未来现场协议变动，这里需要统一调整。

### 6.4 Reset

每轮测试前后都可能需要清状态。  
当前项目提供：

- [runner_reset.py](/Users/wangjianyu/code/hitachi/runner_reset.py)

用于统一清理：

- `requestfloor`
- `destinationfloor`
- `frontopen`
- `rearopen`
- `amrincar`
- `hallcalldisable`

### 6.5 Manual Confirmation Still Exists

当前机器人完整流程仍然是“半自动”：

- 机器人进入确认：人工回车
- 机器人离开确认：人工回车
- `amrincar = 1/0` 的切换也保留在人工确认之后执行

这不是缺陷，而是当前阶段为了降低现场联调风险，故意保留的人机确认节点。

## 7. Project Output Value

从管理视角看，当前这部分工作的价值已经不只是“写了几个脚本”，而是完成了以下交付：

- 对接目标接口并完成认证链路验证
- 梳理电梯关键状态字段含义
- 明确现场真实协议理解，纠正了若干初始误判
- 打通门控控制
- 形成呼梯和完整流程测试能力
- 形成可交接、可复用、可继续扩展的测试脚本体系
- 形成针对现场操作的半自动 SOP 型 runner

这意味着项目已经完成了从“未知接口探索”到“可执行联调资产沉淀”的阶段转换。

## 8. Remaining Work / Next Step Recommendations

建议下一阶段按以下顺序推进：

### 8.1 Complete Destination Floor Validation

继续验证：

- `destinationfloor` 注册逻辑
- `liftArriveDestFloor` 稳定性
- 到站后开门逻辑的鲁棒性

### 8.2 Integrate Real Robot Events

将当前 `robot_manual_runner.py` 中的人工确认替换为真实机器人事件：

- 机器人已进入轿厢
- 机器人已离开轿厢

### 8.3 Standardize Config Management

目前各 runner 的配置是独立内嵌式，适合现场快速修改。  
后续如果项目转入正式产品化，建议再统一成：

- 环境配置文件
- 设备映射配置
- 楼层映射配置

### 8.4 Archive Annex Files

当前原始资料已经定位到微信容器正式路径。  
但该路径依然不适合作为长期归档位置，建议后续将 PDF 正式归档到仓库 `docs/` 或项目共享盘中，避免资料失联。

## 9. Handover Summary

当前项目已具备：

- 可查询状态
- 可查询配置
- 可控制开门关门
- 可测试呼梯
- 可跑手动确认版完整机器人流程

从“阶段性交付”角度，这已经形成了一套完整的现场联调资产。  
如果后续继续推进，只需要在当前脚本体系基础上逐步替换人工确认、加强异常处理和配置管理即可。
