# ppt-master Skill 调试指南

## 目的

这份文档只回答一个问题：**如何在本仓库中调试 `ppt-master` skill，以及如何验证它在全局安装后的真实行为。**

建议把调试分成两条路径：

1. **仓库内调试源码**
2. **全局安装后验收**

前者用于改代码、查脚本逻辑、看依赖是否正常；后者用于确认 `npx skill add ./skills` 之后，安装到 `~/.agents/skills/ppt-master` 的产物是否真的可用。

---

## 前提条件

建议本机具备以下工具：

- `python3` 3.10+
- `uv`
- `node`：仅在调试 `web_to_md.cjs` 或微信网页抓取时需要
- `pandoc`：仅在调试 DOCX / EPUB 等文档转换时需要

可先快速确认：

```bash
python3 --version
uv --version
node --version
pandoc --version
```

---

## 路径一：仓库内调试源码

这一条路径最适合日常开发。

### 1. 创建 skill 的本地环境

在仓库根目录执行：

```bash
cd /Users/justnode/codeRepos/github/ppt-master
uv sync --project skills/ppt-master
```

这会使用 `skills/ppt-master/pyproject.toml` 创建主环境，环境位置通常在：

```text
skills/ppt-master/.venv
```

### 2. 直接运行 skill 脚本

调试源码时，推荐始终显式指定 skill 项目：

```bash
cd /Users/justnode/codeRepos/github/ppt-master
uv run --project skills/ppt-master python skills/ppt-master/scripts/project_manager.py init demo --format ppt169
uv run --project skills/ppt-master python skills/ppt-master/scripts/source_to_md/ppt_to_md.py --help
uv run --project skills/ppt-master python skills/ppt-master/scripts/image_gen.py --list-backends
uv run --project skills/ppt-master python skills/ppt-master/scripts/svg_quality_checker.py examples/annual_report
```

适合优先验证这些问题：

- `pyproject.toml` 里的依赖是否完整
- `runtime_support.py` 的自动自举逻辑是否正常
- 各脚本在仓库开发态是否能直接运行
- 修改某个 Python 文件后，行为是否符合预期

### 3. 用最小命令调具体入口

如果只想验证某个脚本是否能启动，优先用这种“轻命令”：

```bash
uv run --project skills/ppt-master python skills/ppt-master/scripts/image_gen.py --list-backends
uv run --project skills/ppt-master python skills/ppt-master/scripts/source_to_md/ppt_to_md.py --help
uv run --project skills/ppt-master python skills/ppt-master/scripts/project_manager.py --help
```

这样更快，也更容易定位是“入口导入失败”还是“业务逻辑失败”。

### 4. 调试时加断点

如果要逐步排查 Python 逻辑，可以直接在仓库里跑 `pdb`：

```bash
cd /Users/justnode/codeRepos/github/ppt-master
uv run --project skills/ppt-master python -m pdb skills/ppt-master/scripts/project_manager.py init demo --format ppt169
```

如果你使用 IDE，也建议把解释器指向：

```text
/Users/justnode/codeRepos/github/ppt-master/skills/ppt-master/.venv
```

### 5. 仓库内 `.env` 怎么放

仓库内调试时，最省事的做法有两种：

- 把 `.env` 放在仓库根目录
- 或显式指定 `PPT_MASTER_ENV_FILE`

例如：

```bash
export PPT_MASTER_ENV_FILE=/absolute/path/to/.env
uv run --project skills/ppt-master python skills/ppt-master/scripts/image_gen.py --list-backends
```

---

## 路径二：全局安装后验收

这一条路径用于验证：**用户真正通过 `npx skill add ./skills` 安装后，skill 是否仍然能正常工作。**

这是发布前必须做的一步，因为仓库源码目录和全局安装目录不是同一个地方。

### 1. 重新安装 skill

每次改完 `skills/ppt-master` 相关内容后，都要重新安装一次：

```bash
cd /Users/justnode/codeRepos/github/ppt-master
npx skill add ./skills
```

安装完成后，skill 通常位于：

```text
~/.agents/skills/ppt-master
```

### 2. 进入已安装的 skill 根目录

```bash
cd ~/.agents/skills/ppt-master
```

从这里开始，下面的命令都以“已安装 skill 根目录”为当前目录。

### 3. 验证基础入口是否正常

先跑几个最轻量的命令：

```bash
python3 scripts/project_manager.py --help
python3 scripts/source_to_md/ppt_to_md.py --help
python3 scripts/image_gen.py --list-backends
```

如果本机已安装 `uv`，这些入口在缺依赖时会基于当前目录下的 `pyproject.toml` 自动自举。

### 4. 验证典型工作流命令

```bash
cd ~/.agents/skills/ppt-master
uv run --project . python scripts/project_manager.py init demo --format ppt169
uv run --project . python scripts/project_manager.py validate projects/demo
```

如果你想验证后处理链路，也要严格按顺序单独执行：

```bash
cd ~/.agents/skills/ppt-master
uv run --project . python scripts/total_md_split.py <project_path>
uv run --project . python scripts/finalize_svg.py <project_path>
uv run --project . python scripts/svg_to_pptx.py <project_path> -s final
```

不要把这三步合并成一个 shell 调用。

### 5. 验证“全局安装后依赖是否真的跟着走”

重点检查这几项：

- `~/.agents/skills/ppt-master/pyproject.toml` 是否存在
- `~/.agents/skills/ppt-master/uv.lock` 是否存在
- `python3 scripts/...` 是否能在缺包时自动拉起
- 文档中的命令是否与安装目录结构一致

可以直接看目录：

```bash
cd ~/.agents/skills/ppt-master
ls -la
ls -la scripts
```

### 6. 全局安装调试时 `.env` 怎么放

推荐顺序如下：

1. 最稳妥：设置 `PPT_MASTER_ENV_FILE`
2. 次优：把 `.env` 放在你执行命令时的当前工作目录
3. 不建议默认依赖 skill 安装目录里的 `.env`

例如：

```bash
export PPT_MASTER_ENV_FILE=/absolute/path/to/.env
cd ~/.agents/skills/ppt-master
python3 scripts/image_gen.py --list-backends
```

---

## 推荐调试节奏

日常开发建议固定采用下面这套节奏：

1. 在仓库内改代码
2. 用 `uv run --project skills/ppt-master ...` 验证源码逻辑
3. 改完后执行 `npx skill add ./skills`
4. 进入 `~/.agents/skills/ppt-master`
5. 再用安装产物跑一遍关键命令

这样可以同时覆盖：

- 源码是否正确
- 打包/安装后的 skill 是否正确
- 文档中的全局 skill 命令是否真实可执行

---

## 常见误区

### 误区 1：改了仓库代码，就等于改了全局 skill

不是。

`npx skill add ./skills` 安装的是一份复制出来的 skill 内容。仓库里的新改动不会自动同步到 `~/.agents/skills/ppt-master`。

### 误区 2：仓库内和全局安装后的命令可以混着写

不建议。

仓库内调试建议使用：

```bash
uv run --project skills/ppt-master python skills/ppt-master/scripts/...
```

全局安装后建议使用：

```bash
cd ~/.agents/skills/ppt-master
uv run --project . python scripts/...
```

### 误区 3：`update_repo.py` 也应该在全局 skill 里调试

不是。

`update_repo.py` 是仓库维护命令，不属于全局 skill 使用路径。它应该只在完整仓库中验证。

---

## 最小验收清单

每次涉及 skill 运行机制、依赖、自举或文档命令的改动后，至少检查以下项目：

- [ ] `uv sync --project skills/ppt-master` 成功
- [ ] 仓库内 `uv run --project skills/ppt-master python ... --help` 正常
- [ ] `npx skill add ./skills` 成功
- [ ] `~/.agents/skills/ppt-master/pyproject.toml` 存在
- [ ] 全局安装目录下 `python3 scripts/image_gen.py --list-backends` 正常
- [ ] 文档里的全局 skill 命令可以直接照抄执行

做到这一步，基本就能确认这次改动没有把 skill 的真实使用路径搞坏。
