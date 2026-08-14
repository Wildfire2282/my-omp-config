/**
 * Bash bang-command autocomplete for omp.
 *
 * While typing a `!` bash command, press Tab:
 *   - first token        -> command-name suggestions (bash builtins + every
 *                           executable on $PATH) with matching bash history
 *                           commands first (most recent, tagged "history")
 *   - token after sudo/env/command/... -> command-name suggestions again
 *   - `$NAME` token      -> environment/shell-variable suggestions whose
 *                           description shows the live value
 *   - `$NAME/…` token    -> file suggestions inside that variable's value
 *   - later tokens       -> file/directory suggestions relative to the session
 *                           cwd (`~/` and `~` expand to $HOME; directories get
 *                           a trailing `/` and no trailing space; executables
 *                           are tagged "executable"; absolute `/…`, `./…` and
 *                           `../…` first tokens complete as paths)
 *
 * Bash-style history expansion happens inline while typing:
 *   `!!`  -> last command, `!$` -> its last word, `!*` -> its arguments,
 *   `!N` / `!-N` -> the Nth / Nth-from-last history entry.
 * History is read from $OMP_BASH_HISTORY when set, else ~/.bash_history.
 *
 * The editor only auto-opens the popup for `/`, `@`, `#`, `skill:` and URL
 * tokens, so `!` completion is Tab-triggered (like a real shell). Once the
 * popup is open, typing continues to filter it live.
 *
 * Everything runs in-process: no bash subprocess (spawning bash takes ~10s on
 * this machine — far beyond the previous 8s timeout, which silently fell back
 * to a PATH scan), so suggestions are instant and builtins still resolve.
 *
 * Install: place in ~/.omp/agent/extensions/ and restart omp.
 */
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import type { AutocompleteItem, AutocompleteProvider } from "@oh-my-pi/pi-tui";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";

let cwd = process.cwd();
let registered = false;

// ---------------------------------------------------------------------------
// Command-name source: bash builtins (fixed set) + executables on $PATH,
// cached per process. `compgen -c` would need a bash subprocess (~10s here),
// so it is replaced by a pure-Node scan; only the PATH, no rc-file aliases.
// ---------------------------------------------------------------------------
const BASH_BUILTINS: Record<string, true> = {
  ".": true, ":": true, alias: true, bg: true, bind: true, break: true,
  builtin: true, caller: true, cd: true, command: true, compgen: true,
  complete: true, compopt: true, continue: true, declare: true, dirs: true,
  disown: true, echo: true, enable: true, eval: true, exec: true,
  exit: true, export: true, false: true, fc: true, fg: true, getopts: true,
  hash: true, help: true, history: true, jobs: true, kill: true, let: true,
  local: true, logout: true, mapfile: true, popd: true, printf: true,
  pushd: true, pwd: true, read: true, readarray: true, readonly: true,
  return: true, set: true, shift: true, shopt: true, source: true,
  suspend: true, test: true, times: true, trap: true, true: true,
  type: true, typeset: true, ulimit: true, umask: true, unalias: true,
  unset: true, wait: true,
};

let commandNames: string[] | null = null;

function scanPathCommands(): Set<string> {
  const names = new Set<string>();
  for (const dir of (process.env.PATH ?? "").split(":")) {
    // /mnt/… is WSL cross-filesystem: statting it is very slow, and its
    // binaries are not bash's anyway.
    if (!dir || dir.startsWith("/mnt/")) continue;
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      continue; // unreadable PATH entry
    }
    let checked = 0;
    for (const entry of entries) {
      if (!(entry.isFile() || entry.isSymbolicLink())) continue;
      if (++checked > 400) break; // oversized dir; don't stat forever
      try {
        if ((statSync(join(dir, entry.name)).mode & 0o111) === 0) continue;
      } catch {
        continue; // vanished or dangling symlink
      }
      names.add(entry.name);
    }
  }
  return names;
}

function loadCommands(): string[] {
  if (commandNames) return commandNames;
  const names = scanPathCommands();
  for (const b of Object.keys(BASH_BUILTINS)) names.add(b);
  commandNames = [...names].sort();
  return commandNames;
}

// ---------------------------------------------------------------------------
// Bash history: $OMP_BASH_HISTORY if set, else ~/.bash_history. Continuation
// lines merged, HISTTIMEFORMAT timestamps dropped, deduped most-recent-wins,
// ordered oldest -> newest.
// ---------------------------------------------------------------------------
let historyCache: string[] | null = null;

function loadHistory(): string[] {
  if (historyCache) return historyCache;
  const histPath = process.env.OMP_BASH_HISTORY ?? join(homedir(), ".bash_history");
  let raw: string;
  try {
    raw = readFileSync(histPath, "utf8");
  } catch {
    historyCache = [];
    return historyCache;
  }
  const cmds: string[] = [];
  let current = "";
  for (const line of raw.split("\n")) {
    if (/^#\d+$/.test(line)) continue; // HISTTIMEFORMAT timestamp line
    if (line.endsWith("\\")) {
      current += line.slice(0, -1) + " ";
      continue;
    }
    const cmd = (current + line).trim();
    current = "";
    if (cmd) cmds.push(cmd);
  }
  if (current.trim()) cmds.push(current.trim());
  const seen = new Set<string>();
  for (let i = cmds.length - 1; i >= 0; i--) {
    if (seen.has(cmds[i])) cmds.splice(i, 1);
    else seen.add(cmds[i]);
  }
  historyCache = cmds;
  return cmds;
}

// ---------------------------------------------------------------------------
// Variables: bash dynamic variables + the environment. Sorted, cached.
// ---------------------------------------------------------------------------
const SHELL_VARIABLES = [
  "BASH", "BASHOPTS", "BASHPID", "BASH_ALIASES", "BASH_ARGC", "BASH_ARGV",
  "BASH_ENV", "BASH_LINENO", "BASH_SOURCE", "BASH_SUBSHELL", "BASH_VERSINFO",
  "BASH_VERSION", "COMP_CWORD", "COMP_KEY", "COMP_LINE", "COMP_POINT",
  "COMP_TYPE", "COMP_WORDBREAKS", "DIRSTACK", "EUID", "FUNCNAME",
  "GLOBIGNORE", "GROUPS", "HISTCMD", "HISTCONTROL", "HISTFILE",
  "HISTFILESIZE", "HISTIGNORE", "HISTSIZE", "HOSTNAME", "HOSTTYPE", "IFS",
  "LINENO", "MACHTYPE", "MAIL", "MAILCHECK", "OPTERR", "OPTIND", "OSTYPE",
  "PIPESTATUS", "PPID", "PS1", "PS2", "PS3", "PS4", "PWD", "RANDOM",
  "REPLY", "SECONDS", "SHELL", "SHELLOPTS", "SHLVL", "TIMEFORMAT",
  "TMOUT", "UID",
];

let variableNames: string[] | null = null;

function loadVariables(): string[] {
  if (variableNames) return variableNames;
  const names = new Set<string>(SHELL_VARIABLES);
  for (const k of Object.keys(process.env)) names.add(k);
  variableNames = [...names].sort();
  return variableNames;
}

// ---------------------------------------------------------------------------
// Command-name suggestions: recent history matches first, then PATH/builtins.
// ---------------------------------------------------------------------------
function commandItems(token: string): AutocompleteItem[] {
  const names = loadCommands();
  const hist = loadHistory();
  const items: AutocompleteItem[] = [];
  const seen = new Set<string>();
  let histShown = 0;
  for (let i = hist.length - 1; i >= 0 && histShown < 15; i--) {
    const cmd = hist[i];
    if (!cmd.startsWith(token) || seen.has(cmd)) continue;
    seen.add(cmd);
    items.push({ value: cmd, label: cmd, description: "history" });
    histShown++;
  }
  let shown = 0;
  for (const name of names) {
    if (!name.startsWith(token) || seen.has(name)) continue;
    items.push({
      value: name,
      label: name,
      ...(BASH_BUILTINS[name] ? { description: "builtin" } : {}),
    });
    if (++shown >= 60) break;
  }
  return items;
}

function variableItems(token: string): AutocompleteItem[] {
  const t = token.startsWith("$") ? token.slice(1) : token;
  return loadVariables()
    .filter((n) => n.startsWith(t))
    .map((n) => {
      const v = process.env[n];
      return {
        value: "$" + n,
        label: "$" + n,
        ...(v != null
          ? { description: v.length > 40 ? v.slice(0, 40) + "…" : v }
          : {}),
      };
    });
}

// ---------------------------------------------------------------------------
// File suggestions. Handles `~/`/`~` expansion to $HOME and `$VAR/…`
// expansion to the variable's value; values keep the `~`/`$VAR` form so the
// applied line reads like a shell command.
// ---------------------------------------------------------------------------
function fileItems(token: string): AutocompleteItem[] {
  let dirPart = "";
  let base = token;
  let dir: string;
  if (token === "~") {
    dirPart = "~/";
    base = "";
    dir = homedir();
  } else if (token.startsWith("~/")) {
    const slashIdx = token.lastIndexOf("/");
    dirPart = token.slice(0, slashIdx + 1);
    base = token.slice(slashIdx + 1);
    dir = join(homedir(), token.slice(2, slashIdx));
  } else if (token.startsWith("$")) {
    const vm = /^\$([A-Za-z_][A-Za-z0-9_]*)(\/?)(.*)$/.exec(token);
    if (!vm) return [];
    const val = process.env[vm[1]];
    if (val == null) return [];
    const rest = vm[3];
    const slashIdx = rest.lastIndexOf("/");
    if (slashIdx >= 0) {
      dirPart = "$" + vm[1] + "/" + rest.slice(0, slashIdx + 1);
      base = rest.slice(slashIdx + 1);
      dir = join(val, rest.slice(0, slashIdx + 1));
    } else {
      dirPart = "$" + vm[1] + "/";
      base = rest;
      dir = val;
    }
  } else {
    const slashIdx = token.lastIndexOf("/");
    if (slashIdx >= 0) {
      dirPart = token.slice(0, slashIdx + 1);
      base = token.slice(slashIdx + 1);
      dir = resolve(cwd, dirPart);
    } else {
      base = token;
      dir = cwd;
    }
  }
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
  const showHidden = base.startsWith(".");
  return entries
    .filter(
      (e) => (showHidden || !e.name.startsWith(".")) && e.name.startsWith(base)
    )
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .slice(0, 60)
    .map((e) => {
      const isDir = e.isDirectory();
      const value = dirPart + e.name + (isDir ? "/" : "");
      const item: AutocompleteItem = { value, label: value };
      if (isDir) {
        item.description = "directory";
      } else if (e.isFile() || e.isSymbolicLink()) {
        try {
          if ((statSync(join(dir, e.name)).mode & 0o111) !== 0) {
            item.description = "executable";
          }
        } catch {
          // dangling symlink etc.
        }
      }
      return item;
    });
}

// ---------------------------------------------------------------------------
// Commands that take another command as their argument; the token right
// after them completes as a command name.
// ---------------------------------------------------------------------------
const WRAPPER_COMMANDS: Record<string, true> = {
  sudo: true, doas: true, pkexec: true, env: true, command: true,
  exec: true, xargs: true, time: true, nice: true, nohup: true,
  setsid: true, strace: true, watch: true, timeout: true, ionice: true,
  script: true, ts: true, torsocks: true, proxychains: true, sh: true,
  bash: true, zsh: true, fish: true,
};

function isWrapperContext(afterBang: string, tokenStart: number): boolean {
  const tokens = afterBang.slice(0, tokenStart).trim().split(/\s+/);
  return tokens.length === 1 && WRAPPER_COMMANDS[tokens[0]] === true;
}

// ---------------------------------------------------------------------------
// Suggestions for a `!` bang line. Returns null when the cursor is not in a
// bang context, so the wrapped provider falls through to the built-in one.
// ---------------------------------------------------------------------------
export async function bangSuggestions(
  lines: string[],
  cursorLine: number,
  cursorCol: number
): Promise<{ items: AutocompleteItem[]; prefix: string } | null> {
  const line = lines[cursorLine] ?? "";
  const before = line.slice(0, cursorCol);
  const bang = /^(\s*!)([\s\S]*)$/.exec(before);
  if (!bang) return null;

  const afterBang = bang[2];
  const tokenMatch = /(\S+)$/.exec(afterBang);

  if (!tokenMatch) {
    // `!` or `! `: recent history + every command.
    return { items: commandItems(""), prefix: "" };
  }

  const token = tokenMatch[1];
  const tokenStart = tokenMatch.index;
  const isFirstToken = afterBang.slice(0, tokenStart).trim() === "";
  if (isFirstToken) {
    // `$VAR` / `$VAR/…` complete as variables / files inside the value.
    if (token.startsWith("$")) {
      return {
        items: token.includes("/") ? fileItems(token) : variableItems(token),
        prefix: token,
      };
    }
    // Absolute/relative path used as the command itself.
    if (
      token.startsWith("/") ||
      token.startsWith("./") ||
      token.startsWith("../")
    ) {
      return { items: fileItems(token), prefix: token };
    }
    return { items: commandItems(token), prefix: token };
  }

  // `$VAR` / `$VAR/…` anywhere: variables / files inside the value.
  if (token.startsWith("$")) {
    return {
      items: token.includes("/") ? fileItems(token) : variableItems(token),
      prefix: token,
    };
  }

  // Wrapper command (sudo …): the following token is a command name.
  if (!token.startsWith("-") && isWrapperContext(afterBang, tokenStart)) {
    return { items: commandItems(token), prefix: token };
  }

  return { items: fileItems(token), prefix: token };
}

export function bangApplyCompletion(
  lines: string[],
  cursorLine: number,
  cursorCol: number,
  item: AutocompleteItem,
  prefix: string
): { lines: string[]; cursorLine: number; cursorCol: number } {
  const line = lines[cursorLine] ?? "";
  const beforePrefix = line.slice(0, Math.max(0, cursorCol - prefix.length));
  const afterCursor = line.slice(cursorCol);
  const isDir = item.value.endsWith("/");
  const suffix = isDir ? "" : " ";
  const newLine = beforePrefix + item.value + suffix + afterCursor;
  const newLines = [...lines];
  newLines[cursorLine] = newLine;
  return {
    lines: newLines,
    cursorLine,
    cursorCol: beforePrefix.length + item.value.length + suffix.length,
  };
}

function isBangContext(
  lines: string[],
  cursorLine: number,
  cursorCol: number
): boolean {
  return /^\s*!/.test((lines[cursorLine] ?? "").slice(0, cursorCol));
}

// ---------------------------------------------------------------------------
// Inline bash history expansion while typing: `!!`, `!$`, `!*`, `!N`, `!-N`.
// Synchronous and history-cache-only — never spawns a process, and only fires
// on complete symbol/number expressions so ordinary `!cmd` typing is never
// rewritten mid-word.
// ---------------------------------------------------------------------------
export function tryExpandBang(
  textBeforeCursor: string
): { replaceLen: number; insert: string } | null {
  const m = /(^|\s)!(!|\$|\*|-?\d+)$/.exec(textBeforeCursor);
  if (!m) return null;
  const hist = loadHistory();
  if (hist.length === 0) return null;
  const last = hist[hist.length - 1];
  const expr = m[2];
  let insert: string | null = null;
  if (expr === "!") {
    insert = last;
  } else if (expr === "$") {
    const words = last.trim().split(/\s+/);
    if (words.length > 0) insert = words[words.length - 1];
  } else if (expr === "*") {
    const words = last.trim().split(/\s+/);
    if (words.length > 1) insert = words.slice(1).join(" ");
  } else {
    const n = parseInt(expr, 10);
    if (n >= 0) {
      if (n >= 1 && n <= hist.length) insert = hist[n - 1];
    } else {
      const k = -n;
      if (k >= 1 && k <= hist.length) insert = hist[hist.length - k];
    }
  }
  if (insert == null) return null;
  return { replaceLen: expr.length + 1, insert };
}

// ---------------------------------------------------------------------------
// Wrapper: handle `!` lines ourselves, delegate everything else to the
// built-in provider (slash commands, @-mentions, path completion).
// ---------------------------------------------------------------------------
export function wrapProvider(
  current: AutocompleteProvider
): AutocompleteProvider {
  return {
    async getSuggestions(lines, cursorLine, cursorCol) {
      const bang = await bangSuggestions(lines, cursorLine, cursorCol);
      if (bang) return bang;
      return current.getSuggestions(lines, cursorLine, cursorCol);
    },
    applyCompletion(lines, cursorLine, cursorCol, item, prefix) {
      if (isBangContext(lines, cursorLine, cursorCol)) {
        return bangApplyCompletion(lines, cursorLine, cursorCol, item, prefix);
      }
      return current.applyCompletion(lines, cursorLine, cursorCol, item, prefix);
    },
    async getForceFileSuggestions(lines, cursorLine, cursorCol) {
      const bang = await bangSuggestions(lines, cursorLine, cursorCol);
      if (bang) return bang;
      return (
        current.getForceFileSuggestions?.(lines, cursorLine, cursorCol) ?? null
      );
    },
    shouldTriggerFileCompletion(lines, cursorLine, cursorCol) {
      if (isBangContext(lines, cursorLine, cursorCol)) return true;
      return (
        current.shouldTriggerFileCompletion?.(lines, cursorLine, cursorCol) ??
        true
      );
    },
    trySyncSlashCompletion(text) {
      return current.trySyncSlashCompletion?.(text) ?? null;
    },
    trySyncInlineReplace(textBeforeCursor) {
      if (!/^\s*!/.test(textBeforeCursor)) return null;
      return tryExpandBang(textBeforeCursor);
    },
    getInlineHint(lines, cursorLine, cursorCol) {
      const line = lines[cursorLine] ?? "";
      const before = line.slice(0, cursorCol);
      if (/^\s*!\s*$/.test(before)) return " Tab: 命令补全";
      return current.getInlineHint?.(lines, cursorLine, cursorCol) ?? null;
    },
  };
}

export default function bashBangComplete(pi: ExtensionAPI): void {
  pi.on("session_start", (_event, ctx) => {
    cwd = ctx.cwd;
    // Warm the caches so the first Tab never pays the PATH/history scan.
    loadCommands();
    loadHistory();
    loadVariables();
    if (registered) return;
    registered = true;
    ctx.ui.addAutocompleteProvider(wrapProvider);
  });
}
