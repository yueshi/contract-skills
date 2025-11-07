# Solidity 安全模式参考

## 常见安全漏洞模式

### 1. 重入攻击 (Reentrancy)

**漏洞描述：**
恶意合约在接收到以太币时反复调用原合约的函数，可能导致资金被重复提取。

**检测模式：**
- 外部调用 (`call()`, `transfer()`, `send()`) 后进行状态改变
- 缺少重入保护机制

**安全模式：**
```solidity
// Checks-Effects-Interactions 模式
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount, "Insufficient balance");

    // 1. 检查 (Checks)
    require(amount > 0, "Amount must be greater than 0");

    // 2. 效果 (Effects) - 先改变状态
    balances[msg.sender] -= amount;

    // 3. 交互 (Interactions) - 最后进行外部调用
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}

// 使用 Reentrancy Guard
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract MyContract is ReentrancyGuard {
    function withdraw(uint amount) public nonReentrant {
        // 函数实现
    }
}
```

### 2. 访问控制漏洞 (Access Control)

**漏洞描述：**
关键函数缺少适当的访问控制，允许未授权用户执行敏感操作。

**检测模式：**
- 公共函数缺少访问修饰符
- 硬编码的特权地址
- 角色管理不当

**安全模式：**
```solidity
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract MyContract is Ownable, AccessControl {
    // 创建角色
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    // 只有管理员可以调用
    function adminFunction() public onlyRole(ADMIN_ROLE) {
        // 敏感操作
    }

    // 只有所有者可以调用
    function ownerFunction() public onlyOwner {
        // 敏感操作
    }
}
```

### 3. 整数溢出/下溢 (Integer Overflow/Underflow)

**漏洞描述：**
算术运算超出数值范围，导致意外结果。

**检测模式：**
- 未检查的算术运算
- 缺少 SafeMath 使用 (Solidity < 0.8.0)

**安全模式：**
```solidity
// Solidity 0.8.0+ 内置溢出检查
pragma solidity ^0.8.0;

contract SafeMath {
    function add(uint a, uint b) public pure returns (uint) {
        uint c = a + b;
        require(c >= a, "SafeMath: addition overflow");
        return c;
    }

    function sub(uint a, uint b) public pure returns (uint) {
        require(b <= a, "SafeMath: subtraction overflow");
        uint c = a - b;
        return c;
    }

    function mul(uint a, uint b) public pure returns (uint) {
        if (a == 0) {
            return 0;
        }
        uint c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");
        return c;
    }
}

// 使用 OpenZeppelin SafeMath
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract UsingSafeMath {
    using SafeMath for uint256;

    function calculateTotal(uint256 price, uint256 quantity) public pure returns (uint256) {
        return price.mul(quantity);
    }
}
```

### 4. 未检查的外部调用 (Unchecked External Call)

**漏洞描述：**
外部调用返回值未检查，可能导致调用失败但程序继续执行。

**检测模式：**
- `.call()`, `.delegatecall()`, `.send()`, `.transfer()` 返回值未检查
- 外部调用后缺少错误处理

**安全模式：**
```solidity
// 正确检查外部调用
function withdraw(address payable to, uint amount) public {
    require(amount > 0, "Amount must be greater than 0");

    (bool success, ) = to.call{value: amount}("");
    require(success, "Transfer failed");

    // 或者使用更详细的错误处理
    if (!success) {
        revert("Transfer failed");
    }
}

// 使用低级调用的完整模式
function externalCall(address target, bytes calldata data) public payable {
    (bool success, bytes memory returnData) = target.call{value: msg.value}(data);

    if (!success) {
        if (returnData.length > 0) {
            assembly {
                let returnDataSize := mload(returnData)
                revert(add(32, returnData), returnDataSize)
            }
        } else {
            revert("External call failed");
        }
    }
}
```

### 5. 时间戳依赖 (Timestamp Dependence)

**漏洞描述：**
依赖 `block.timestamp` 进行关键逻辑判断，矿工可以操纵时间戳。

**安全模式：**
```solidity
// 避免依赖精确时间戳
uint256 public constant WINDOW_SIZE = 1 days;

function canExecute() public view returns (bool) {
    return block.timestamp > deadline + WINDOW_SIZE;
}

// 使用 block.number 替代时间戳
uint256 public constant BLOCKS_PER_DAY = 6500; // 约每天出块数

function afterDelay() public view returns (bool) {
    return block.number > startBlock + (BLOCKS_PER_DAY * delayDays);
}
```

### 6. gas 限制问题 (Gas Limit Issues)

**漏洞描述：**
合约逻辑可能导致 gas 消耗过多，影响交易执行。

**安全模式：**
```solidity
// 避免无限制循环
function batchTransfer(address[] calldata recipients, uint256[] calldata amounts) public {
    require(recipients.length == amounts.length, "Arrays length mismatch");
    require(recipients.length <= 100, "Too many recipients"); // 限制数量

    for (uint i = 0; i < recipients.length; i++) {
        // 检查 gas 剩余
        require(gasleft() >= 5000, "Insufficient gas for batch operation");

        recipients[i].transfer(amounts[i]);
    }
}

// 分批处理大量数据
function processLargeArray(uint256[] calldata data) public {
    uint256 batchSize = 50;
    uint256 totalBatches = (data.length + batchSize - 1) / batchSize;

    for (uint i = 0; i < totalBatches; i++) {
        uint256 start = i * batchSize;
        uint256 end = start + batchSize;
        if (end > data.length) end = data.length;

        processBatch(data[start:end]);
    }
}
```

## 安全开发最佳实践

### 1. 代码审查清单
- [ ] 所有外部调用都检查返回值
- [ ] 敏感函数有适当的访问控制
- [ ] 使用 Checks-Effects-Interactions 模式
- [ ] 整数运算考虑溢出保护
- [ ] 避免依赖可操纵的外部数据

### 2. 测试策略
- 边界条件测试
- 重入攻击模拟
- 权限绕过测试
- Gas 消耗分析

### 3. 部署前检查
- 静态分析工具扫描
- 形式化验证
- 第三方审计
- 测试网充分测试

## 工具和资源

### 静态分析工具
- Wake (本技能主要工具)
- Slither
- Mythril
- Securify

### 测试框架
- Hardhat
- Foundry
- Truffle

### 安全库
- OpenZeppelin Contracts
- SafeERC20
- Reentrancy Guard

### 学习资源
- ConsenSmart 安全最佳实践
- Solidity 官方文档
- DeFi 安全报告分析