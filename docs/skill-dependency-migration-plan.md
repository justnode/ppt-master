# Skill 与仓库根依赖关系治理方案

## 背景

当前仓库同时存在两套与 Python 运行相关的依赖定义：

- 仓库根目录的 `pyproject.toml`
- `skills/ppt-master/requirements.txt`

这两套定义分别服务于不同场景：

- 仓库根目录：面向 `git clone` 后的本地开发、维护与主工作流
- `skills/ppt-master`：面向 skill 被单独安装到全局目录后的独立运行

这次修复已经让全局安装后的 skill 可以通过 skill-local 依赖清单自举运行，但从长期维护角度看，仓库内外存在两套运行时依赖来源，仍然容易产生漂移、文档冲突和维护成本。

## 问题定义

当前结构的主要问题：

- 运行时依赖不是单一真相源，容易出现“根目录能跑，skill 单独安装后不能跑”或反过来的情况
- 文档需要同时解释两套依赖体系，增加理解成本
- 新增依赖时需要同步多个地方，容易漏改
- 运行时逻辑需要判断“当前是在仓库内还是全局 skill 内”，复杂度上升

## 目标

本方案的目标是：

- 明确唯一的运行时依赖真相源
- 让 `skills/ppt-master` 成为可以独立运行、独立分发的 Python 单元
- 保留仓库开发体验，不破坏现有主工作流
- 降低全局安装、文档维护和后续扩展的复杂度

## 设计原则

依赖治理应遵循以下原则：

1. 运行时依赖只维护一份真相源
2. 全局 skill 安装后，不应再隐式依赖仓库根目录文件
3. 仓库级配置与 skill 级配置职责分离
4. 向后兼容已有命令和用户习惯，避免一次性大破坏
5. 文档、运行时、自举逻辑必须一致

## 方案选型

### 方案 A：继续以仓库根 `pyproject.toml` 为真相源

做法：

- 根目录 `pyproject.toml` 保留所有运行时依赖
- `skills/ppt-master/requirements.txt` 不再手工维护，而是在发布或同步时自动导出
- 全局 skill 安装时，依赖该导出文件自举

优点：

- 保留现有仓库开发习惯，改动面较小
- 根目录 `uv sync` 逻辑不需要大改

缺点：

- 真正被分发的单元是 `skills/ppt-master`，但依赖真相源却不在 skill 内，结构上不够自然
- skill 脱离仓库后只是“发布副本”，不是完整独立项目
- 发布链路和同步脚本必须长期维护

### 方案 B：以 `skills/ppt-master/pyproject.toml` 为真相源

做法：

- 在 `skills/ppt-master/` 下建立正式的 `pyproject.toml`
- 所有运行时依赖迁移到 skill 内
- 根目录不再承载 skill 的运行时依赖，只保留仓库级开发配置
- 全局安装时，skill 本身就携带完整依赖定义

优点：

- 被分发的单元与依赖真相源一致，结构最清晰
- skill 可以真正独立运行和演化
- 更符合 `uv` 与现代 Python 项目组织方式

缺点：

- 迁移工作量略高
- 需要重新梳理根目录与 skill 目录的职责边界

## 推荐结论

推荐采用 **方案 B**：以 `skills/ppt-master/pyproject.toml` 作为唯一的运行时依赖真相源。

原因如下：

- `skills/ppt-master` 才是实际被安装、复制和分发的运行单元
- 全局安装场景是这个问题的根源，依赖真相源应跟着运行单元走
- 长期来看，这种结构最容易维护、最容易解释、也最不容易出现边界问题

## 目标结构

建议最终目录职责如下：

```text
repo-root/
├── pyproject.toml                  # 仓库级开发配置，可选
├── uv.lock                         # 仓库级锁文件，可选
├── docs/
├── skills/
│   └── ppt-master/
│       ├── pyproject.toml          # 唯一运行时依赖真相源
│       ├── uv.lock                 # skill 级锁文件
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       ├── templates/
│       └── workflows/
```

说明：

- `skills/ppt-master/pyproject.toml`：定义 skill 运行所需的全部 Python 依赖
- `skills/ppt-master/uv.lock`：锁定 skill 的实际依赖版本
- 根目录 `pyproject.toml`：仅用于仓库开发工具、质量检查、辅助脚本，不再承载 skill 运行时依赖

## 职责边界

迁移后建议明确以下边界：

### `skills/ppt-master/pyproject.toml`

负责：

- PPT Master skill 的运行时依赖
- Python 版本要求
- 可选依赖分组（如果未来需要）

不负责：

- 仓库级 lint、format、test、release 工具
- 与其他仓库模块无关的开发辅助配置

### 根目录 `pyproject.toml`

负责：

- 仓库开发工具依赖
- 开发时的统一命令入口
- 可选的 workspace 级配置

不负责：

- skill 自身运行所需的第三方依赖定义

## 分阶段迁移计划

### 第一阶段：确立 skill 级真相源

目标：

- 在 `skills/ppt-master/` 下建立正式 `pyproject.toml`

工作项：

- 从根目录提取当前运行时依赖
- 在 skill 目录下写入 `project.name`、`version`、`requires-python`、`dependencies`
- 生成 skill-local `uv.lock`

产出：

- `skills/ppt-master/pyproject.toml`
- `skills/ppt-master/uv.lock`

### 第二阶段：运行时逻辑切换到 skill 级项目

目标：

- 所有入口脚本优先基于 skill 目录内的 `pyproject.toml` 自举

工作项：

- 调整运行时支持逻辑，不再优先读取 `requirements.txt`
- 统一使用 `uv run --project <skill_dir> ...` 或等价方式运行
- 保留必要的兼容提示信息

产出：

- 运行时只认 skill 内依赖定义
- 全局 skill 与仓库内运行行为一致

### 第三阶段：压缩根目录运行时职责

目标：

- 根目录不再维护 skill 的运行时依赖

工作项：

- 清理根目录 `pyproject.toml` 中与 skill 运行直接相关的依赖
- 保留开发工具依赖或转为可选分组
- 评估 `update_repo.py` 等脚本是否需要基于 skill 目录执行依赖同步

产出：

- 根目录 `pyproject.toml` 仅保留仓库级配置

### 第四阶段：移除重复依赖清单

目标：

- 删除或降级 `skills/ppt-master/requirements.txt`

可选方式：

- 直接删除该文件
- 或仅作为自动导出的兼容产物，不再人工维护

推荐：

- 最终不要保留人工维护的双份清单

## `.env` 配置策略

依赖治理与配置治理应一起理顺。

建议 `.env` 策略如下：

- 默认从当前工作目录开始向上查找 `.env`
- 允许通过 `PPT_MASTER_ENV_FILE` 指定显式路径
- 不推荐把 `.env` 默认放到全局 skill 安装目录

原因：

- 工作目录更符合用户项目语义
- 避免把用户敏感配置混入“程序安装位置”
- 仓库运行与全局 skill 运行可以使用同一套查找逻辑

## 文档调整方案

迁移完成后，文档需同步统一：

### README / README_CN

应说明：

- 仓库开发使用的命令入口
- skill 自身是独立 Python 单元
- 全局安装后如何自动使用 skill 内依赖定义

### `skills/ppt-master/SKILL.md`

应说明：

- skill 运行时依赖由 skill 自己管理
- 全局安装后不再依赖仓库根目录
- 哪些命令是仓库限定命令

### `scripts/README.md`

应说明：

- 仓库内运行方式
- skill 全局安装后的运行方式
- `update_repo.py` 等命令的边界

## 兼容策略

为避免一次性切换带来混乱，建议采用兼容过渡：

1. 先引入 `skills/ppt-master/pyproject.toml`
2. 保持一小段时间的双路径兼容
3. 在日志和文档中标记 `requirements.txt` 为过渡方案
4. 确认稳定后再删除重复依赖清单

过渡期建议加提示：

- 若检测到仍在使用旧的 `requirements.txt` 自举方式，输出一次迁移提示
- 若检测到根目录运行时依赖与 skill 内版本不一致，提示维护者同步

## 风险与应对

### 风险 1：仓库内现有命令失效

应对：

- 为根目录常用命令提供兼容包装
- 在迁移期间保留旧命令入口

### 风险 2：锁文件和实际环境不一致

应对：

- 将锁文件下沉到 skill 目录
- 明确“谁生成、谁更新、谁提交”

### 风险 3：文档与实现再度分叉

应对：

- 每次调整依赖结构时，同时更新 README、SKILL、脚本说明
- 在 PR 检查中加入文档一致性检查

### 风险 4：全局安装器仍只复制部分文件

应对：

- 明确要求安装器复制 `pyproject.toml` 与锁文件
- 将这些文件纳入 skill 分发最小必要集合

## 验收标准

完成迁移后，应满足以下标准：

1. 在仓库内可正常运行所有主入口脚本
2. 将 `skills/ppt-master/` 单独复制到任意目录后，仍可独立运行
3. 新增依赖时，只需要修改一处运行时真相源
4. 文档不再出现“根目录依赖”和“skill 目录依赖”冲突描述
5. `update_repo.py` 等仓库限定命令边界明确

## 推荐执行顺序

建议按以下顺序实施：

1. 在 `skills/ppt-master/` 建立 `pyproject.toml`
2. 生成并提交 skill-local 锁文件
3. 修改运行时自举逻辑，切换到 skill 项目
4. 更新文档
5. 缩减根目录运行时依赖
6. 删除或降级 `requirements.txt`

## 最终结论

要真正把 skill 与仓库根依赖关系理顺，关键不是继续补丁式维护两套依赖文件，而是明确：

- `skills/ppt-master` 是否是独立运行单元

如果答案是“是”，那么运行时依赖真相源就应该放在 `skills/ppt-master/` 内，并以 `pyproject.toml` 为核心；根目录只保留仓库开发层面的配置。这是最清晰、最稳定、最适合长期维护的结构。
