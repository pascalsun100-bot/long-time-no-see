# 《好久不见》— Long Time No See / Story Engine

基于 **Dify Chatflow + OceanBase PowerContext** 的中文现实校园互动游戏。玩家与旧日同学林知夏重新取得联系；Dify 控制人物对话、检索词改写、重要事件判断及条件分支，PowerContext 负责历史记忆存储与按需召回。

## 1. 提交内容与导入顺序

- `dify/long-time-no-see.yaml`：脱敏 Dify DSL（推荐优先导入）。
- `dify/long-time-no-see.ifpkg`：脱敏 Dify 应用包，属于可选导入形式，不需要和 YAML 重复导入。
- `deployment/`：环境变量示例、Nginx TLS 反向代理示例。
- `scripts/powercontext_demo.py`：创建 Scope、写入初始事实和检索验证的脚本。
- `examples/test-cases.md`：交互、写入、跨会话召回三组验收样例。

**两种导入文件是同一份应用的不同格式，只需导入其中一种。** YAML 来自 Dify Cloud 工作流导出结果，含 `version: 0.7.0`（DSL 格式版本，**不是 Dify Server 版本**）。原运行环境是 Dify Cloud，准确服务端版本未记录。兼容性需要在评审的 Dify 环境实测。

## 2. 依赖与分工

- Dify Cloud / 兼容的自部署 Dify；Chatflow 9 节点。需 Dify 的 HTTP 请求、条件分支和结构化输出能力。
- 模型：Gemini 3 Flash Preview（原环境所用模型名称）；Dify Marketplace `langgenius/gemini:0.9.12`。评审需自行安装/绑定模型凭证，模型可用性可能因地区及平台变化。
- PowerContext **1.4.1**，原部署环境 Ubuntu **24.04.2 LTS**、Python **3.12.3**，通过 `uv tool` 安装。
- HTTPS API 主机可使用作者演示站 `https://memory.lingxi100.cn`（服务可用性不保证），**完整复现推荐评审自建服务**。
- 当前流程没有调用外部 Embedding / Rerank API；采用关键词查询改写 + PowerContext `/v1/context/prepare`。自然语言召回质量存在限制。

## 3. 部署 PowerContext（Ubuntu 24.04）

确保已安装 Python3、curl 和 `uv`（参照 https://docs.astral.sh/uv/getting-started/installation/ ），执行：

```bash
uv tool install 'powercontext[cli,server]==1.4.1'
powercontext --version
mkdir -p ~/long-time-no-see/powercontext
cd ~/long-time-no-see/powercontext
powercontext server run
```

该前台模式用于初步验证；实际可采用 `powercontext service install --env-file .env` 安装个人持久服务，运行 `powercontext service status` 确认服务已启动。配置格式/鉴权变量以 PowerContext 1.4.1 官方配置说明为准：https://powercontext.oceanbase.io/en/docs/reference/configuration/ 。服务器监听本地 `127.0.0.1:8000`，不要直接将未验证鉴权的内部端口暴露公网。云端 Dify 若需访问评审自建服务，应使用可信 HTTPS 反向代理，开放 443 并转发必要 API。`deployment/nginx-memory.conf.example` 是可修改示例，不包含证书。

## 4. 鉴权与 Scope 初始化

**本仓库不包含 API Key、Token、密码或历史私人 Scope ID。**

```bash
export POWERCONTEXT_URL=http://127.0.0.1:8000
export POWERCONTEXT_TOKEN='评审部署生成的Bearer Token'
python3 scripts/powercontext_demo.py init
# 从输出中复制真实 scope_id
export POWERCONTEXT_SCOPE_ID='新生成的ScopeID'
python3 scripts/powercontext_demo.py remember
python3 scripts/powercontext_demo.py query
```

`init` 创建测试 Scope；`remember` 写入用于技术验证的专业事实；`query` 用关键词测试是否召回。若首次运行想验证应用自动写入，先运行 `init`，不要运行 `remember`，而由 Chatflow 写入该事实。

**Dify 导入后必须配置：**
1. 绑定 Gemini Provider 凭证、检查两个 LLM 节点及检索词改写节点模型可用。
2. `HTTP 请求` 和 `HTTP 请求 2` 的 URL 改为评审部署的公网 HTTPS 地址，分别以 `/v1/context/prepare` 与 `/v1/memory/remember` 结尾。
3. 两个 HTTP 节点将 `REPLACE_WITH_POWERCONTEXT_TOKEN` 替换为评审自己的 Bearer Token；`REPLACE_WITH_NEW_SCOPE_ID` 替换为 `init` 返回的同一 Scope ID。
4. 不更改 `query`、`kind`、`text`、`reason` 的 Dify 动态变量标签；检查 `HTTP 请求 → body` 已进入角色 SYSTEM，角色 LLM 的 USER 仍绑定 `用户输入 → query`。
5. 用 `examples/test-cases.md` 按顺序执行，确认 HTTP 返回体，不仅看节点绿色。

**固定 Scope 限制：** 当前作品是单人评审/演示原型，两个 HTTP 节点共用单个 Scope。多个玩家并发会造成数据混用；正式多用户部署应增加用户到 Scope 的持久映射。本仓库不将它描述为已实现的多租户功能。

## 5. 操作与验收

详见 [`examples/test-cases.md`](examples/test-cases.md)。推荐截取：Dify 图、事件提取 `structured_output`、PowerContext 写入 HTTP `200` + `changed:true`、独立新会话 HTTP 检索 body、自然语言召回以及去重分支 ELSE。

先前作者环境已观察到写入 `changed:true` / `state:active`，并经检索词改写后出现成功的跨会话专业记忆回复；这些是**作者环境证据**，不代替评审独立复现。当前提交包尚未在干净 Dify 工作区重新导入验证。

## 6. 已知限制和安全

- PowerContext 可能返回与用户问题不相关的记忆；检索改写改善但不保证完美召回。
- 自动事件提取依赖 LLM 判断，可能遗漏、重复或错误保存；需结合请求与历史上下文验证。
- 默认 Scope 是演示级静态配置；多玩家公开部署必须隔离。
- Dify Cloud 免费版与版本历史导出限制可能变化；本项目提供已脱敏的应用包及 DSL。
- 导出包若包含真实凭证不可公开；本仓库已使用占位符替换 HTTP Bearer 凭证和原 Scope ID。
- 示例脚本和 Nginx 模板仅用于评审自建测试环境，不包含公网证书或管理凭证。

## 7. 复用与来源

- [Dify](https://github.com/langgenius/dify) — Chatflow 平台。
- [OceanBase PowerContext](https://github.com/oceanbase/powercontext) — 长期记忆服务。
- [uv](https://docs.astral.sh/uv/) — Python 工具安装。
- 游戏剧情、角色设定、事件提取规则与工作流编排为本作品内容；未随附第三方原始仓库代码。作者须确保角色图片有合法使用授权。
