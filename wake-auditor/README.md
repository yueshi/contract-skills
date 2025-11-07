# Wake Auditor Skill

专门用于自动化 Solidity 智能合约安全审计的 Claude Code 技能，基于 Wake Printer 系统实现高效的静态分析和漏洞检测。

## 🚀 快速开始

### 1. 激活技能
```bash
/skill wake-auditor
```

### 2. 环境设置
```bash
python scripts/wake_setup.py
```

### 3. 基础审计
```bash
# 扫描整个项目
python scripts/contract_scanner.py --path ./contracts/

# 扫描特定合约
python scripts/contract_scanner.py --contract ./contracts/MyToken.sol
```

### 4. 漏洞检测
```bash
python scripts/vulnerability_detector.py --path ./contracts/
```

## 📁 项目结构

```
wake-auditor/
├── SKILL.md                    # 技能核心指令
├── scripts/                    # 核心分析脚本
│   ├── wake_setup.py          # 环境设置
│   ├── contract_scanner.py    # 合约扫描器
│   └── vulnerability_detector.py # 漏洞检测器
├── references/                # 参考文档
│   ├── wake_documentation.md  # Wake 工具文档
│   └── solidity_security_patterns.md # 安全模式参考
├── assets/                   # 资源文件
│   └── audit_report_template.html # 报告模板
└── README.md                 # 项目说明
```

## 🔍 主要功能

### 1. 自动化合约扫描
- 递归扫描项目中的所有 Solidity 文件
- 使用 Wake 中间表示进行深度分析
- 生成结构化的扫描报告

### 2. 安全漏洞检测
- **重入攻击**: 检测外部调用后的状态改变
- **访问控制**: 识别权限控制缺失
- **整数溢出**: 检测算术运算安全性
- **外部调用**: 验证返回值检查
- **时间戳依赖**: 分析可操纵的外部数据

### 3. 自定义审计规则
- 基于 Python 的脚本化检测逻辑
- 可扩展的漏洞检测模式
- 灵活的报告生成机制

## 🛡️ 安全检查模式

### 高危漏洞
- 重入攻击风险
- 访问控制漏洞
- 整数溢出/下溢

### 中危漏洞
- 未检查的外部调用
- 时间戳依赖
- Gas 限制问题

### 低危漏洞
- 代码优化建议
- 最佳实践偏差

## 📊 报告输出

审计完成后将生成以下报告：

1. **JSON 格式**: 机器可读的结构化数据
2. **HTML 格式**: 可视化的网页报告
3. **Markdown 格式**: 技术文档格式

报告包含：
- 漏洞摘要统计
- 详细漏洞信息
- 代码片段和修复建议
- 风险评估和优先级

## 🎯 使用场景

### 适合使用的情况
- DeFi 协议安全审计
- ICO 智能合约检查
- 企业级区块链项目
- 开源项目安全评估

### 审计类型
- **快速扫描**: 日常开发中的安全检查
- **深度分析**: 上线前的全面审计
- **定期检查**: 代码维护后的重新评估
- **合规审计**: 满足监管要求的安全评估

## ⚙️ 配置选项

### 基础配置
```json
{
  "audit_settings": {
    "scan_depth": "deep",
    "check_patterns": [
      "reentrancy",
      "access_control",
      "integer_overflow",
      "unchecked_call",
      "logic_vulnerabilities"
    ],
    "output_formats": ["json", "html", "markdown"]
  }
}
```

### 高级配置
- 自定义检测规则
- 批量处理设置
- CI/CD 集成配置
- 性能优化参数

## 🔧 最佳实践

### 1. 开发流程集成
```bash
# 在 CI/CD 中集成
python scripts/wake_setup.py
python scripts/vulnerability_detector.py --path ./contracts/
```

### 2. 定期审计
- 代码变更后立即重新审计
- 合约部署前进行全面检查
- 定期进行安全评估

### 3. 多工具配合
- 结合 Slither 进行交叉验证
- 使用测试框架进行漏洞重现
- 参考第三方审计报告

## 🚨 注意事项

### 局限性
- 静态分析无法检测运行时漏洞
- 需要结合人工审计进行确认
- 复杂的业务逻辑需要额外分析

### 兼容性
- 支持 Solidity 0.5.0+
- 需要 Python 3.8+ 环境
- 推荐使用最新版本的 Wake 工具

## 📚 学习资源

- [Wake 官方文档](references/wake_documentation.md)
- [Solidity 安全模式](references/solidity_security_patterns.md)
- [智能合约安全最佳实践](https://consensys.github.io/smart-contract-best-practices/)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个技能：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**免责声明**: 本工具提供的安全分析仅供参考，不能替代专业的人工审计。在部署智能合约前，建议寻求专业的安全审计服务。