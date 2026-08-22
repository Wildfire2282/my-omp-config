#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
omp opencode-go usage 紧凑格式 —— 自愈安装器

背景
  omp 升级会用新文件覆盖 dist/cli.js(旧版 bun 分发)或 ~/.local/bin/omp
  二进制(新版 standalone 编译分发 18.0+),导致手工打的 usage segment
  补丁(紧凑格式 `0%-8%-4%`)丢失。本脚本一次性解决:

    1) 自动定位真实产物: bun 全局的 dist/cli.js + standalone 二进制
       (~/.local/bin/omp, 兼容已装 wrapper 的环境);
    2) 把内置 usage segment 渲染改为紧凑格式:5h-7d-月 三窗口百分比,
       `-` 连接,输出如 `0%-8%-4%`(无内部符号依赖,升级后仍可重打);
    3) 在 PATH 优先位置安装自愈 wrapper(`~/.local/bin/omp` 优先):
       每次启动检测补丁标记,缺失则自动重打,再 exec 真 omp;
       若该路径已被 standalone 二进制占用,则把二进制迁移至 omp.real
       再放置 wrapper(解决 18.0+ 覆盖 wrapper 的根因);
    4) 幂等,可重复运行;换环境后重跑一次即可。

用法
  python3 install-omp-usage.py [--bin-dir DIR] [--cli PATH]

  --bin-dir   wrapper 安装目录(默认自动:取 PATH 中优先于 omp 的可写目录,
              首选 ~/.local/bin)
  --cli       显式指定 cli.js/二进制路径(默认自动检测)

说明
  补丁逻辑唯一事实来源是下方 apply_patch()/apply_patch_bytes():wrapper
  内嵌代码由 inspect.getsource() 从本函数生成,避免两处维护漂移。

  失效降级:若 omp 大幅重构导致定位不到 usage segment,补丁安全失败
  (wrapper 打印警告并按未补丁版启动),不会崩溃。
"""

import argparse
import inspect
import os
import re
import shutil
import stat
import subprocess
import sys

MARK = "omp-usage-compact"  # 与 apply_patch() replacement 内注释必须一致

# ---------------------------------------------------------------- patch


def apply_patch(src: str) -> str:
    """把内置 usage segment 渲染替换为紧凑格式。输入/输出均为产物全文(文本)。"""
    # 兼容两种间距: 旧 cli.js 为 id:"usage", 新二进制为 id: "usage",
    m = re.search(r'id:\s*"usage"\s*,\s*render\s*\([^)]*\)\s*\{', src)
    if not m:
        raise ValueError("usage segment not found (omp structure changed?)")
    open_brace = src.rfind("{", 0, m.start())
    if open_brace < 0:
        raise ValueError("usage segment object start not found")
    depth = 0
    i = open_brace
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    if i >= len(src):
        raise ValueError("unbalanced braces in usage segment")
    replacement = (
        '{id:"usage",render(_i){let n=_i.usage;'
        'if(!n||!n.fiveHour&&!n.sevenDay&&!n.monthly)return{content:"",visible:!1};'
        "let h=[];"
        'if(n.fiveHour)h.push(`${Math.round(n.fiveHour.percent)}%`);'
        'if(n.sevenDay)h.push(`${Math.round(n.sevenDay.percent)}%`);'
        'if(n.monthly)h.push(`${Math.round(n.monthly.percent)}%`);'
        # 注释内的 MARK 是 wrapper 的"已补丁"检测标记,勿改
        'return{content:h.join("-")/*omp-usage-compact*/,visible:!0}}}'
    )
    return src[:open_brace] + replacement + src[i + 1 :]


def apply_patch_bytes(data: bytes) -> bytes:
    """二进制安全补丁(保持文件大小不变,避免 ELF 结构错位)。"""
    m = re.search(rb'id:\s*"usage"\s*,\s*render\s*\([^)]*\)\s*\{', data)
    if not m:
        raise ValueError("usage segment not found (omp structure changed?)")
    open_brace = data.rfind(b"{", 0, m.start())
    if open_brace < 0:
        raise ValueError("usage segment object start not found")
    depth = 0
    i = open_brace
    while i < len(data):
        b = data[i]
        if b == 123:  # {
            depth += 1
        elif b == 125:  # }
            depth -= 1
            if depth == 0:
                break
        i += 1
    if i >= len(data):
        raise ValueError("unbalanced braces in usage segment")
    replacement = (
        b'{id:"usage",render(_i){let n=_i.usage;'
        b'if(!n||!n.fiveHour&&!n.sevenDay&&!n.monthly)return{content:"",visible:!1};'
        b"let h=[];"
        b'if(n.fiveHour)h.push(`${Math.round(n.fiveHour.percent)}%`);'
        b'if(n.sevenDay)h.push(`${Math.round(n.sevenDay.percent)}%`);'
        b'if(n.monthly)h.push(`${Math.round(n.monthly.percent)}%`);'
        b'return{content:h.join("-")/*omp-usage-compact*/,visible:!0}}}'
    )
    orig_len = i - open_brace + 1
    if len(replacement) > orig_len:
        raise ValueError(f"replacement too long ({len(replacement)} > {orig_len}), need update")
    if len(replacement) < orig_len:
        replacement = replacement[:-1] + b" " * (orig_len - len(replacement)) + b"}"
    return data[:open_brace] + replacement + data[i + 1 :]


# ---------------------------------------------------------------- locate


def is_cli(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            head = f.read(256)
        size = os.path.getsize(path)
    except OSError:
        return False
    # 真 cli.js: bun shebang + 打包产物体积;wrapper/bash 脚本不满足
    return head.startswith(b"#!/usr/bin/env bun") and size > 1024 * 1024


def is_omp_binary(path: str) -> bool:
    """standalone 编译产物: ELF 且内含 usage segment 文本。"""
    if not path or not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            head = f.read(4)
        size = os.path.getsize(path)
    except OSError:
        return False
    if head != b"\x7fELF":
        return False
    if size < 10 * 1024 * 1024:
        return False
    try:
        with open(path, "rb") as f:
            f.seek(size // 2)
            chunk = f.read(4 * 1024 * 1024)
        if b"fiveHour" not in chunk:
            with open(path, "rb") as f:
                data = f.read()
            if b"fiveHour" not in data:
                return False
    except OSError:
        return False
    return True


def find_cli(explicit: str | None) -> str:
    """兼容旧接口:返回首个可用产物路径(优先 cli.js)。"""
    targets = find_targets(explicit)
    if not targets:
        sys.exit(
            "error: 未找到 omp 的 cli.js/二进制。请确认 omp 已安装(bun 全局安装或 standalone),"
            "或用 --cli 显式指定路径。"
        )
    return targets[0]


def find_targets(explicit: str | None) -> list[str]:
    """返回所有待补丁产物路径(去重,保序)。"""
    if explicit:
        p = os.path.realpath(explicit)
        if is_cli(p) or is_omp_binary(p):
            return [p]
        sys.exit(f"error: --cli {explicit} 不是有效的 cli.js/omp 二进制(缺少特征)")
    candidates: list[str] = []

    w = shutil.which("omp")
    if w:
        candidates.append(os.path.realpath(w))
    for extra in [
        os.path.expanduser("~/.local/bin/omp.real"),
        os.path.expanduser("~/.local/bin/omp.bin"),
    ]:
        if os.path.isfile(extra):
            candidates.append(os.path.realpath(extra))

    bun_root = os.environ.get("BUN_INSTALL") or os.path.expanduser("~/.bun")
    candidates.append(
        os.path.realpath(os.path.join(bun_root, "bin", "omp"))
    )
    candidates.append(
        os.path.join(
            bun_root,
            "install",
            "global",
            "node_modules",
            "@oh-my-pi",
            "pi-coding-agent",
            "dist",
            "cli.js",
        )
    )
    candidates.append(os.path.expanduser("~/.local/bin/omp"))

    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        r = os.path.realpath(c)
        if r in seen:
            continue
        seen.add(r)
        if is_cli(r) or is_omp_binary(r):
            result.append(r)
    return result


# ---------------------------------------------------------------- wrapper


def wrapper_script(cli: str) -> str:
    """生成自愈 wrapper(bash)。补丁逻辑从 apply_patch* 源码内嵌,单一事实来源。"""
    patch_src = inspect.getsource(apply_patch)
    patch_bytes_src = inspect.getsource(apply_patch_bytes)
    # wrapper 自身路径(与 CLI 区分,用于检测 omp update 覆盖 wrapper 的场景)
    wrapper_path = os.path.join(os.path.dirname(cli), "omp") if cli.endswith(".real") else cli
    # 若 cli 已是 omp.real,则 wrapper 为同目录的 omp;否则 wrapper 即 cli
    if not cli.endswith(".real"):
        wrapper_path = cli
    return (
        "#!/bin/bash\n"
        "# omp self-healing wrapper (generated by install-omp-usage.py; rerun that script after omp upgrades)\n"
        "set -u\n"
        f'CLI="{cli}"\n'
        f'WRAPPER="{wrapper_path}"\n'
        f'MARK="{MARK}"\n'
        # update 子命令特殊处理:避免 wrapper 被新二进制覆盖后丢失自愈能力
        'if [ "${1:-}" = "update" ]; then\n'
        '    # 先保证当前 CLI 已补丁(正常启动路径)\n'
        '    if [ -f "$CLI" ] && ! grep -q "$MARK" "$CLI"; then\n'
        '        python3 - "$CLI" <<\'PY\' || echo "[omp-usage] patch failed; starting unpatched omp" >&2\n'
        "import os, re, sys, tempfile\n"
        f"{patch_src}\n"
        f"{patch_bytes_src}\n"
        "p=sys.argv[1]\n"
        "is_elf=open(p,'rb').read(4)==b'\\x7fELF'\n"
        "if is_elf:\n"
        "    data=open(p,'rb').read()\n"
        "    patched=apply_patch_bytes(data)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.write(fd,patched)\n"
        "    os.close(fd)\n"
        "    os.replace(tmp,p)\n"
        "else:\n"
        "    src=open(p,encoding='utf-8',errors='replace').read()\n"
        "    patched=apply_patch(src)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.close(fd)\n"
        "    open(tmp,'w',encoding='utf-8').write(patched)\n"
        "    os.replace(tmp,p)\n"
        "PY\n"
        "    fi\n"
        '    "$CLI" "$@"\n'
        '    RC=$?\n'
        '    # omp update 可能把新二进制写入 $WRAPPER(覆盖 wrapper)或 $CLI;需自愈\n'
        '    if [ -f "$WRAPPER" ] && head -c4 "$WRAPPER" 2>/dev/null | od -An -tx1 2>/dev/null | grep -q "7f 45 4c 46"; then\n'
        '        # wrapper 被覆盖:把新二进制移回 CLI 并重建 wrapper\n'
        '        echo "[omp-usage] wrapper overwritten by update, restoring..." >&2\n'
        '        # 先尝试用安装器全量修复(最可靠)\n'
        '        INSTALLER=""\n'
        '        for cand in "$HOME/workspace/my-omp-config/scripts/install-omp-usage.py" "$HOME/.omp/scripts/install-omp-usage.py" ""; do\n'
        '            if [ -f "$cand" ]; then INSTALLER="$cand"; break; fi\n'
        '        done\n'
        '        if [ -n "$INSTALLER" ] && [ -f "$INSTALLER" ]; then\n'
        '            python3 "$INSTALLER" >&2 || true\n'
        '        else\n'
        '            # 降级:手动迁移并补丁\n'
        '            mv -f "$WRAPPER" "$CLI" 2>/dev/null || cp -f "$WRAPPER" "$CLI"\n'
        '            python3 - "$CLI" <<\'PY2\' || echo "[omp-usage] post-update patch failed" >&2\n'
        "import os, re, sys, tempfile\n"
        f"{patch_src}\n"
        f"{patch_bytes_src}\n"
        "p=sys.argv[1]\n"
        "data=open(p,'rb').read()\n"
        "patched=apply_patch_bytes(data)\n"
        "mode=os.stat(p).st_mode\n"
        "fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "os.fchmod(fd,mode)\n"
        "os.write(fd,patched)\n"
        "os.close(fd)\n"
        "os.replace(tmp,p)\n"
        "PY2\n"
        '            # 重建 wrapper 自身:重新生成当前脚本头部(简化:重新运行安装器逻辑需手动)\n'
        '            echo "[omp-usage] please re-run install-omp-usage.py to fully restore wrapper" >&2\n'
        '        fi\n'
        '    else\n'
        '        # 正常情况:CLI 可能被更新为未补丁版本(若 update 写入 CLI)\n'
        '        if [ -f "$CLI" ] && ! grep -q "$MARK" "$CLI"; then\n'
        '            python3 - "$CLI" <<\'PY\' || echo "[omp-usage] post-update patch failed" >&2\n'
        "import os, re, sys, tempfile\n"
        f"{patch_src}\n"
        f"{patch_bytes_src}\n"
        "p=sys.argv[1]\n"
        "is_elf=open(p,'rb').read(4)==b'\\x7fELF'\n"
        "if is_elf:\n"
        "    data=open(p,'rb').read()\n"
        "    patched=apply_patch_bytes(data)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.write(fd,patched)\n"
        "    os.close(fd)\n"
        "    os.replace(tmp,p)\n"
        "else:\n"
        "    src=open(p,encoding='utf-8',errors='replace').read()\n"
        "    patched=apply_patch(src)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.close(fd)\n"
        "    open(tmp,'w',encoding='utf-8').write(patched)\n"
        "    os.replace(tmp,p)\n"
        "PY\n"
        "        fi\n"
        "    fi\n"
        '    exit $RC\n'
        'fi\n'
        'if [ -f "$CLI" ] && ! grep -q "$MARK" "$CLI"; then\n'
        '    python3 - "$CLI" <<\'PY\' || echo "[omp-usage] patch failed; starting unpatched omp" >&2\n'
        "import os, re, sys, tempfile\n"
        "\n"
        f"{patch_src}\n"
        f"{patch_bytes_src}\n"
        "p=sys.argv[1]\n"
        "is_elf=open(p,'rb').read(4)==b'\\x7fELF'\n"
        "if is_elf:\n"
        "    data=open(p,'rb').read()\n"
        "    patched=apply_patch_bytes(data)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.write(fd,patched)\n"
        "    os.close(fd)\n"
        "    os.replace(tmp,p)\n"
        "else:\n"
        "    src=open(p,encoding='utf-8',errors='replace').read()\n"
        "    patched=apply_patch(src)\n"
        "    mode=os.stat(p).st_mode\n"
        "    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(p),suffix='.patched')\n"
        "    os.fchmod(fd,mode)\n"
        "    os.close(fd)\n"
        "    open(tmp,'w',encoding='utf-8').write(patched)\n"
        "    os.replace(tmp,p)\n"
        "PY\n"
        "fi\n"
        'exec "$CLI" "$@"\n'
    )


def pick_bin_dir(cli: str, explicit: str | None) -> str:
    if explicit:
        return os.path.expanduser(explicit)
    path_dirs = [
        os.path.expanduser(d) for d in os.environ.get("PATH", "").split(os.pathsep) if d
    ]
    cli_bin_dir = os.path.dirname(os.path.realpath(shutil.which("omp") or ""))
    preferred = os.path.expanduser("~/.local/bin")
    if preferred in path_dirs and (not cli_bin_dir or path_dirs.index(preferred) < path_dirs.index(cli_bin_dir)):
        return preferred
    for d in path_dirs:
        if not cli_bin_dir or path_dirs.index(d) < path_dirs.index(cli_bin_dir):
            if os.access(d, os.W_OK):
                return d
    return preferred  # 兜底:安装后提示用户补 PATH


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description="omp usage 紧凑格式自愈安装器")
    ap.add_argument("--bin-dir", help="wrapper 安装目录(默认自动)")
    ap.add_argument("--cli", help="cli.js/二进制路径(默认自动检测)")
    args = ap.parse_args()

    if sys.platform not in ("linux", "darwin"):
        sys.exit("error: 仅支持 POSIX(bash wrapper 依赖);Windows 请用 WSL。")
    if not shutil.which("bash"):
        sys.exit("error: 未找到 bash(wrapper 依赖)。")
    if not shutil.which("python3"):
        sys.exit("error: 未找到 python3(wrapper 依赖)。")

    targets = find_targets(args.cli)
    if not targets:
        sys.exit("error: 未找到待补丁产物")
    print(f"[1/3] targets: {', '.join(targets)}")

    for cli in targets:
        is_binary = is_omp_binary(cli)
        if is_binary:
            with open(cli, "rb") as f:
                data = f.read()
            if MARK.encode() in data:
                print(f"      {cli}: 已补丁,跳过。")
                continue
            try:
                patched = apply_patch_bytes(data)
            except ValueError as e:
                print(f"      {cli}: 补丁失败: {e}(omp 结构可能已变化,跳过)", file=sys.stderr)
                continue
            mode = os.stat(cli).st_mode
            import tempfile

            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(cli), suffix=".patched")
            os.fchmod(fd, mode)
            os.write(fd, patched)
            os.close(fd)
            try:
                os.replace(tmp, cli)
            except OSError as e:
                if "Text file busy" in str(e):
                    try:
                        os.unlink(cli)
                    except OSError:
                        pass
                    os.replace(tmp, cli)
                else:
                    raise
            print(f"      {cli}: 已打补丁(usage segment → 紧凑格式,二进制安全)。")
        else:
            with open(cli, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
            if MARK in src:
                print(f"      {cli}: 已补丁,跳过。")
                continue
            try:
                patched = apply_patch(src)
            except ValueError as e:
                print(f"      {cli}: 补丁失败: {e}(omp 结构可能已变化,跳过)", file=sys.stderr)
                continue
            mode = os.stat(cli).st_mode
            if cli.endswith("cli.js") and shutil.which("node"):
                tmp = cli + ".check.js"
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(patched)
                os.chmod(tmp, mode)
                r = subprocess.run(["node", "--check", tmp], capture_output=True)
                if r.returncode != 0:
                    os.unlink(tmp)
                    print(f"      {cli}: 补丁后语法校验失败: {r.stderr.decode(errors='replace')[:300]}", file=sys.stderr)
                    continue
                os.replace(tmp, cli)
            else:
                import tempfile

                fd, tmp = tempfile.mkstemp(dir=os.path.dirname(cli), suffix=".patched")
                os.fchmod(fd, mode)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(patched)
                try:
                    os.replace(tmp, cli)
                except OSError as e:
                    if "Text file busy" in str(e):
                        try:
                            os.unlink(cli)
                        except OSError:
                            pass
                        os.replace(tmp, cli)
                    else:
                        raise
            print(f"      {cli}: 已打补丁(usage segment → 紧凑格式)。")

    primary_cli = targets[0]
    bin_dir = pick_bin_dir(primary_cli, args.bin_dir)
    os.makedirs(bin_dir, exist_ok=True)
    wrapper_path = os.path.join(bin_dir, "omp")

    if os.path.isfile(wrapper_path):
        try:
            with open(wrapper_path, "rb") as f:
                is_elf = f.read(4) == b"\x7fELF"
        except OSError:
            is_elf = False
        if is_elf and os.path.realpath(wrapper_path) == os.path.realpath(primary_cli):
            real_path = os.path.join(bin_dir, "omp.real")
            print(f"      检测到 standalone 二进制占用 wrapper 路径,迁移: {wrapper_path} -> {real_path}")
            try:
                shutil.copy2(wrapper_path, real_path)
                primary_cli = real_path
            except OSError as e:
                print(f"      迁移失败: {e}", file=sys.stderr)
                sys.exit(1)

    script = wrapper_script(primary_cli)
    try:
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(script)
    except OSError as e:
        if "Text file busy" in str(e):
            os.unlink(wrapper_path)
            with open(wrapper_path, "w", encoding="utf-8") as f:
                f.write(script)
        else:
            raise
    os.chmod(wrapper_path, os.stat(wrapper_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[2/3] wrapper: {wrapper_path} -> {primary_cli}")

    path_dirs = [os.path.expanduser(d) for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    w = shutil.which("omp")
    print(f"[3/3] `which omp` -> {w}")
    if w and os.path.realpath(w) != os.path.realpath(wrapper_path):
        print("      注意: 当前 PATH 解析到其他位置的 omp。请把", bin_dir, "放到 PATH 更前面。")
    elif bin_dir not in path_dirs:
        print(f"      注意: {bin_dir} 不在 PATH 中,需手动加入,例如:")
        print(f"        echo 'export PATH=\"{bin_dir}:$PATH\"' >> ~/.bashrc")
    print("\n完成。重启 omp 生效;omp 升级后无需手动处理(wrapper 自动重打补丁)。")
    if len(targets) > 1:
        print(f"      已同时补丁 {len(targets)} 个产物; wrapper 指向 {primary_cli}。")


if __name__ == "__main__":
    main()
