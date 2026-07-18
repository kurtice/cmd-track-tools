# cmd-track-tools

自动追踪本机通过各包管理器安装的 CLI 工具,生成并增量更新一份单文件 Markdown 清单(`TOOLS.md`),无需每次手动用 `which` / `pip show` / `brew list` 排查工具是怎么装的。

## 特性

- 支持检测 **Homebrew**、**pipx**、**pip3 (global)**、**npm (global)**、**cargo** 五种来源
- 增量更新,而非每次重新生成:
  - 新增的工具 → 追加为活跃条目,标注首次记录日期
  - 卸载的工具 → 不删除,标记删除线并注明卸载日期
  - 曾被标记删除、后来又重装的工具 → 自动恢复为活跃状态
- 若某来源的包管理器在本机未安装,对应分类保持原样,不会误判为"全部卸载"

## 环境要求

- Python 3.12.9(由 `pyenv local` 锁定,见 `.python-version`)
- 无第三方依赖,仅使用标准库

## 安装

```bash
git clone git@github.com:kurtice/cmd-track-tools.git
cd cmd-track-tools

pyenv local 3.12.9
python3 -m venv .venv
source .venv/bin/activate
```

## 使用方式

```bash
python3 track_tools.py --file <目标路径>/TOOLS.md
```

`--file` 不指定时默认在当前目录生成/更新 `TOOLS.md`。

### 建议配置 shell alias

由于项目使用独立虚拟环境,alias 需直接调用 `.venv` 内的 Python 解释器,不依赖 shell 是否已激活该环境:

```bash
alias tools-scan="~/Documents/Personal/Projects/Tools/scripts/cmd-track-tools/.venv/bin/python3 ~/Documents/Personal/Projects/Tools/scripts/cmd-track-tools/track_tools.py --file <PKM md 路径>/TOOLS.md"
```

## 输出示例

```markdown
## pipx
- yt-dlp _(since 2026-07-18)_
- ~~httpie~~ _(removed 2026-07-20)_
```

## 已知限制

- `npm ls -g` 会将 Node.js 自带的 `npm`、`corepack` 一并列入清单,目前未做过滤
- 生成的 `TOOLS.md` 建议保存在独立的 PKM/笔记路径下,而非本仓库内部,保持脚本仓库与数据分离
