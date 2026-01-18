#!/bin/bash
# pxsol-ss 修复脚本
# 用于修复 Python 3.12 兼容性问题
# 
# 问题：
# 1. pxsol 库需要 Python 3.14+，但实际只需添加 future annotations 即可在 3.12 运行
# 2. make.py 中使用了错误的 API 名称和索引操作,已在本人的 make.py 中修复
# 3. make.py 中的文件名与实际编译输出不匹配，已在本人的 make.py 中修复
#
# 作者：[Livian7]
# 日期：2026-01-16

set -e  # 遇到错误立即退出

VENV_PATH="${VENV_PATH:-$HOME/pxsol-env}"
PXSOL_PACKAGE_PATH="$VENV_PATH/lib/python3.12/site-packages/pxsol"

echo "======================================"
echo "pxsol-ss 修复脚本"
echo "======================================"
echo ""

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "错误：虚拟环境不存在: $VENV_PATH"
    echo "请先创建虚拟环境："
    echo "  python3 -m venv $VENV_PATH"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install git+https://github.com/mohanson/pxsol.git"
    exit 1
fi

# 检查 pxsol 是否已安装
if [ ! -d "$PXSOL_PACKAGE_PATH" ]; then
    echo "错误：pxsol 未安装在虚拟环境中"
    echo "请先安装 pxsol："
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install git+https://github.com/mohanson/pxsol.git"
    exit 1
fi

echo "1. 修复 pxsol 库的 Python 3.12 兼容性问题"
echo "   添加 'from __future__ import annotations' 到所有 Python 文件"
echo ""

# 计数器
FIXED_COUNT=0

# 批量修复 pxsol 库文件
find "$PXSOL_PACKAGE_PATH" -name "*.py" -type f | while read -r file; do
    if ! grep -q "from __future__ import annotations" "$file"; then
        sed -i "1s/^/from __future__ import annotations\n/" "$file"
        echo "   已修复: $file"
        FIXED_COUNT=$((FIXED_COUNT + 1))
    fi
done

echo ""
echo "2. 测试 pxsol 导入"
source "$VENV_PATH/bin/activate"
if python -c "import pxsol; print('   导入成功')"; then
    echo "   ✓ pxsol 库修复成功"
else
    echo "   ✗ pxsol 库导入失败"
    exit 1
fi


echo ""
echo "3. 创建必要的目录和文件"
mkdir -p res
if [ ! -f "res/info.json" ]; then
    echo '{}' > res/info.json
    echo "   ✓ 已创建 res/info.json"
else
    echo "   - res/info.json 已存在"
fi

echo ""
echo "======================================"
echo "修复完成！"
echo "======================================"
echo ""
echo "接下来的步骤："
echo ""
echo "1. 确保 Surfpool 本地测试网正在运行"
echo "   surfpool"
echo ""
echo "2. 激活虚拟环境"
echo "   source $VENV_PATH/bin/activate"
echo ""
echo "3. 生成新密钥并部署"
echo "   python make.py deploy"
echo ""
echo "4. 保存数据"
echo "   python make.py save \"你的数据\""
echo ""
echo "5. 读取数据"
echo "   python make.py load"
echo ""
echo "如需帮助，运行: python make.py info"
echo ""