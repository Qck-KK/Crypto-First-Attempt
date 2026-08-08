# Dune + Gemini 链上数据分析助手

用 Gemini 的 function calling（工具调用）驱动 Dune API，实现「自然语言问题 → 链上数据 → AI 分析」的完整闭环。

## 架构流程

```
① 用户问题（如"这个钱包过去7天做了什么"）
        │
        ▼
② Gemini API 理解意图，决定调用哪个工具（function calling）
        │
        ▼
③ Python 执行对应函数，调用 Dune API
        │
        ▼
④ Dune 返回链上数据（余额 / 交易 / 转账 / 自定义SQL结果）
        │
        ▼
⑤ Python 把数据打包成 function_response 交回 Gemini
        │
        ▼
⑥ Gemini 结合数据生成自然语言分析
        │
        ▼
"这个钱包过去7天进行了 xx 笔交易，主要与 xxx 合约交互……"
```

## 文件结构

```
dune_gemini_agent/
├── config.py          # 读取 API Key 等配置
├── dune_client.py      # Dune API 的底层封装（SQL query + 链上数据接口）
├── tools.py            # Gemini 工具（function calling）schema + 调度表
├── gemini_agent.py      # 核心编排逻辑：意图识别 → 调用工具 → 分析总结
├── main.py             # 命令行入口
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置密钥
复制 `.env.example` 为 `.env`，填入你的 key：
```bash
cp .env.example .env
```
```
GEMINI_API_KEY=你的 Gemini API Key      # https://aistudio.google.com/apikey
DUNE_API_KEY=你的 Dune API Key          # https://dune.com/settings/api
GEMINI_MODEL=gemini-2.0-flash           # 可换成其他支持 function calling 的模型
```

### 3. 运行
```bash
python main.py
```
示例交互：
```
你: 帮我看看钱包 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 最近的代币转账情况
```

## 两种"生成 SQL / 查询意图"的方式

Gemini 目前提供了 **4 个工具**，对应两类使用方式：

1. **直接调用 Dune 的链上数据接口**（无需自己写 SQL，响应快）
   - `get_wallet_balances`：当前代币余额快照
   - `get_wallet_transactions`：近期原生交易记录
   - `get_token_transfers`：近期代币转入/转出记录

2. **执行自定义 SQL Query**（`run_dune_sql_query`）
   - 适合复杂聚合统计，例如"过去7天该钱包与哪些合约交互次数最多""某代币近30天净流入"等。
   - **前提**：需要先在 [Dune 网页端](https://dune.com/) 用 SQL 写好并保存一个 query，
     拿到 `query_id`。可以在 SQL 里用 `{{wallet_address}}`、`{{days}}` 这类占位符做成参数化查询，
     Gemini 会在调用时把参数以 `params` 传入。
   - 示例 SQL（Dune SQL / Trino 语法，仅供参考）：
     ```sql
     select
         to_address,
         count(*) as tx_count,
         sum(value / 1e18) as total_eth
     from ethereum.transactions
     where "from" = {{wallet_address}}
       and block_time >= now() - interval '{{days}}' day
     group by to_address
     order by tx_count desc
     limit 20
     ```

## 让 Gemini 更"聪明"地选工具

`gemini_agent.py` 里的 `SYSTEM_INSTRUCTION` 已经告诉模型：
- 简单的"看看最近交易/余额" → 优先用现成的链上数据接口（更快、更省 token）；
- 涉及聚合统计、复杂时间窗口计算的问题 → 优先用 `run_dune_sql_query`（前提是已有对应 query_id）。

你可以根据实际业务，在 `tools.py` 里继续扩展工具，比如：
- `get_token_price`（代币价格）
- `get_nft_holdings`（NFT 持仓）
- 针对某个高频分析场景，直接封装一个专用的 Dune saved query 工具

## 注意事项

- **速率限制/费用**：Dune 和 Gemini 都有各自的调用额度和计费，生产环境建议加缓存、限流。
- **数据量控制**：链上数据可能非常大，代码里对返回结果做了截断（`rows[:200]`、JSON 长度截断），
  避免把过大的数据直接塞进 Gemini 的上下文；如果需要更精细的分析，建议在 SQL 层面先聚合，
  而不是把明细数据全部丢给模型。
- **Dune API 端点可能变化**：`dune_client.py` 里的链上数据接口路径（`api/echo/v1/...`）
  是按 Dune 公开文档实现的参考实现，实际使用前请对照 [Dune 官方文档](https://docs.dune.com/) 
  核实一遍最新的路径和字段名，必要时做相应调整。
- **安全**：不要把 `.env` 提交到 git 仓库，注意 API Key 泄露风险。
