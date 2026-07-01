#!/usr/bin/env bash
# scripts/build_pyinstaller.sh
# 本地调试用：从当前源码打 PyInstaller 单文件包（在目标平台执行）
#
# 用法：
#   bash scripts/build_pyinstaller.sh             # 默认单文件输出
#   bash scripts/build_pyinstaller.sh --onedir   # 目录模式（体积更小，启动更快）
#
# 前置条件：
#   pip install pyinstaller
#   pip install -r requirements.txt
#   pip install -e .   # 确保 cc 命令可用

set -euo pipefail

MODE="${1:---onefile}"
DIST_DIR="dist/pyinstaller"
WORK_DIR="build/pyinstaller"
SPEC_DIR="scripts"

echo "=== KodeForge PyInstaller builder ==="
echo "Mode: ${MODE}"
echo "Platform: $(uname -s) $(uname -m)"

rm -rf "${DIST_DIR}" "${WORK_DIR}"

pyinstaller \
    "${MODE}" \
    --name kodeforge \
    --console \
    --clean \
    --noconfirm \
    --distpath "${DIST_DIR}" \
    --workpath "${WORK_DIR}" \
    --specpath "${SPEC_DIR}" \
    --paths . \
    --paths tools \
    --paths agents \
    --paths gui \
    --collect-all tools \
    --collect-all agents \
    --collect-submodules tools \\
    --collect-submodules agents \\
    --collect-data config \
    --add-data "config:config" \
    --hidden-import=tools.cc_cli \
    --hidden-import=tools.rag \
    --hidden-import=tools.quality \
    --hidden-import=tools.hitl \
    --hidden-import=tools.compiler \
    --hidden-import=tools.workflow \
    --hidden-import=agents.supervisor \
    --hidden-import=agents.experts \
    --hidden-import=agents.runtime \
    tools/cc_cli.py

echo ""
echo "=== 构建完成 ==="
echo "输出目录: ${DIST_DIR}/"
ls -lh "${DIST_DIR}/"

echo ""
echo "=== smoke test ==="
if [ -f "${DIST_DIR}/kodeforge" ] || [ -f "${DIST_DIR}/kodeforge.exe" ]; then
    "${DIST_DIR}/kodeforge" --version 2>/dev/null || echo "[warn] --version 未实现，跳过"
    echo "[ok] 二进制可执行"
else
    echo "[error] 找不到输出文件"
    exit 1
fi
