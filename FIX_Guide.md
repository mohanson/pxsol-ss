# pxsol-ss Python 3.12 兼容性修复指南

## 问题概述

本仓库在 Python 3.12 环境下存在以下兼容性问题：

1. **pxsol 库要求 Python 3.14+**
2. **类型注解前向引用问题**：导致 `NameError`
3. **make.py 中的 API 调用错误**
4. **编译输出文件名不匹配**

## 环境要求

- Python 3.12.x
- Rust 和 Cargo（用于编译 Solana 程序）
- Solana CLI 工具
- Surfpool 或 solana-test-validator（本地测试网）

## 快速修复

### 方法 1：使用自动修复脚本（推荐）

```bash
# 1. 下载修复脚本
chmod +x fix_pxsol.sh

# 2. 运行修复
./fix_pxsol.sh

# 3. 按照脚本提示操作
```

### 方法 2：手动修复

#### 步骤 1: 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv ~/pxsol-env

# 激活虚拟环境
source ~/pxsol-env/bin/activate

# 安装 pxsol（会报错 Python 版本不匹配，继续下一步）
pip install git+https://github.com/mohanson/pxsol.git
```

#### 步骤 2: 修复 pxsol 库的类型注解问题

pxsol 库在类定义中使用了前向引用，需要添加 `from __future__ import annotations`：

```bash
# 批量修复所有 Python 文件
find ~/pxsol-env/lib/python3.12/site-packages/pxsol/ -name "*.py" -type f -exec sh -c '
    if ! grep -q "from __future__ import annotations" "$1"; then
        sed -i "1s/^/from __future__ import annotations\n/" "$1"
        echo "已修复: $1"
    fi
' _ {} \;

# 验证修复
python -c "import pxsol; print('导入成功')"
```

**说明**：Python 3.14 引入了 PEP 649，自动延迟注解求值。在 Python 3.12 中需要显式使用 `from __future__ import annotations`。

#### 步骤 3: 修复 make.py 中的问题

**问题 A：错误的方法名**

```python
# 错误
prikey = pxsol.core.PriKey.rand()

# 正确
prikey = pxsol.core.PriKey.random()
```

修复命令：
```bash
sed -i 's/pxsol\.core\.PriKey\.rand()/pxsol.core.PriKey.random()/g' make.py
```

**问题 B：错误的返回值索引**

`derive_pda()` 返回 `PubKey` 对象，不是元组：

```python
# 错误
data_pubkey = prog_pubkey.derive_pda(user.pubkey.p)[0]

# 正确
data_pubkey = prog_pubkey.derive_pda(user.pubkey.p)
```

修复命令：
```bash
sed -i "s/prog_pubkey\.derive_pda(user\.pubkey\.p)\[0\]/prog_pubkey.derive_pda(user.pubkey.p)/g" make.py
```

**问题 C：编译输出文件名不匹配**

Cargo.toml 中 `name = "solana-storage"` 会生成 `solana_storage.so`，但 make.py 期望 `pxsol_ss.so`：

```python
# 错误
with open('target/deploy/pxsol_ss.so', 'rb') as f:

# 正确
with open('target/deploy/solana_storage.so', 'rb') as f:
```

修复命令：
```bash
sed -i "s/pxsol_ss\.so/solana_storage.so/g" make.py
```

#### 步骤 4: 准备部署环境

```bash
# 创建配置目录
mkdir -p res
echo '{}' > res/info.json

# 启动本地测试网
surfpool &

# 等待节点启动
sleep 3
```

#### 步骤 5: 生成密钥并转账

**重要**：不要使用 `11111111111111111111111111111112` 这样的测试私钥，它可能已被系统保留或损坏。

```bash
# 生成新密钥
python -c "
import pxsol
prikey = pxsol.core.PriKey.random()
pubkey = prikey.pubkey()
print(f'私钥: {prikey.base58()}')
print(f'地址: {pubkey.base58()}')
"

# 转账到新地址（使用上面生成的地址）
solana transfer <新地址> 50 --url http://127.0.0.1:8899 --allow-unfunded-recipient

# 验证余额
solana balance <新地址> --url http://127.0.0.1:8899
```

#### 步骤 6: 部署和测试

```bash
# 部署（使用新生成的私钥）
python make.py deploy --prikey <你的私钥>

# 保存数据
python make.py save "Hello Solana!" --prikey <你的私钥>

# 读取数据
python make.py load --prikey <你的私钥>
```

## 常见问题

### Q1: 为什么不能使用 airdrop？

**A**: 本地测试网的 airdrop 会创建账户但不分配数据空间。如果后续操作需要数据空间，会导致 `Transfer: 'from' must not carry data` 错误。使用 `transfer` 可以避免这个问题。

### Q2: 为什么需要全新的随机私钥？

**A**: 简单的测试私钥（如 `111...112`）可能：
- 被 Solana 系统保留
- 已经被分配了数据空间
- 与某些系统账户冲突

使用 `PriKey.random()` 生成的密钥可避免这些问题。

### Q3: Cargo.lock 版本错误怎么办？

**A**: 删除并重新生成：
```bash
rm Cargo.lock
cargo generate-lockfile
```

或更新 Rust：
```bash
rustup update stable
```

## 技术细节

### PEP 649 vs from __future__ import annotations

- **Python 3.14+**: 默认启用延迟注解求值（PEP 649）
- **Python 3.12**: 需要显式导入 `from __future__ import annotations`
- **效果**: 允许类在定义中引用自身类型

### derive_pda 返回值

根据 pxsol 源码，`derive_pda()` 的签名：

```python
def derive_pda(self, seeds: bytes) -> PubKey:
    # 返回单个 PubKey，不是元组
```

### Solana 账户数据空间

Solana 账户有两种状态：
1. **无数据**: 可以进行普通转账
2. **有数据**: 不能作为普通转账的发送方

使用 `transfer` 而不是 `airdrop` 可确保账户处于正确状态。

## 贡献

如果你发现其他问题或有改进建议，请提交 Issue 或 Pull Request。

## 许可证

MIT

---

**维护者**: [Livian7]  
**最后更新**: 2026-01-16