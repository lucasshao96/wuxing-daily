# 贡献指南 (Contributing)

欢迎贡献！以下方向特别需要帮助：

## 你可以做什么

| 方向 | 说明 | 难度 |
|------|------|------|
| 🌐 节气数据补全 | 当前节气日期硬编码为固定日，需要补充 2020-2030 年精确到日的年际变化表 | 低 |
| 📖 黄历完善 | 补充十二建除、二十八宿、九星等内容 | 中 |
| 🧮 五行算法校验 | 用专业八字 App 交叉验证 `wuxing.py` 的分数，校准阈值 | 中 |
| 🌍 多语言 | 英文/日文/韩文版本 | 中 |
| 📱 推送渠道 | 钉钉/飞书/企业微信/LINE 等 | 低 |
| 🐛 修 Bug | 任何你发现的问题 | — |

## 开发流程

```bash
git clone https://github.com/lucasshao96/wuxing-daily.git
cd wuxing-daily
pip install -r requirements.txt

# 运行测试
python -m pytest tests/ -v

# 查日主工具
python find_day_master.py 1998-07-07 08:55 北京

# 本地 dry-run（不发送邮件）
USERS='[{"name":"测试","day_master":"丁","zodiac":"鼠","email":""}]' python main.py
```

## 提交规范

- 所有 PR 必须通过 `python -m pytest tests/`
- 新增功能请附带测试
- 五行算法修改请附验证用例

## 许可证

MIT — 随意使用、修改、分发。
