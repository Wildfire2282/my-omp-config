/**
 * Bash bang-command autocomplete for omp.
 *
 * While typing a `!` bash command, press Tab:
 *   - first token  -> command-name suggestions (bash builtins, aliases,
 *                     and every executable on $PATH, via `compgen -c`)
 *   - later tokens -> file/directory suggestions relative to the session
 *                     cwd (directories get a trailing `/`, no trailing space)
 *
 * The editor only auto-opens the popup for `/`, `@`, `#`, `skill:` and URL
 * tokens, so `!` completion is Tab-triggered (like a real shell). Once the
 * popup is open, typing continues to filter it live.
 *
 * Install: place in ~/.omp/agent/extensions/ and restart omp.
 */
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import type { AutocompleteItem, AutocompleteProvider } from "@oh-my-pi/pi-tui";
import { execFile } from "node:child_process";
import { readdirSync } from "node:fs";
import { resolve } from "node:path";

let cwd = process.cwd();
let registered = false;

// ---------------------------------------------------------------------------
// Command-name source: bash `compgen -c` (PATH order, includes builtins,
// aliases and functions), cached per process; PATH scan as a fallback.
// ---------------------------------------------------------------------------
let commandNames: string[] | null = null;
let commandLoad: Promise<string[]> | null = null;

function scanPathCommands(): string[] {
  const names = new Set<string>();
  for (const dir of (process.env.PATH ?? "").split(":")) {
    if (!dir) continue;
    try {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        if (entry.isFile() || entry.isSymbolicLink()) names.add(entry.name);
      }
    } catch {
      // unreadable PATH entry
    }
  }
  return [...names].sort();
}

function loadCommands(): Promise<string[]> {
  if (commandNames) return Promise.resolve(commandNames);
  if (!commandLoad) {
    const { promise, resolve } = Promise.withResolvers<string[]>();
    commandLoad = promise;
    execFile(
      "bash",
      ["-lc", "compgen -c"],
      { timeout: 8000, windowsHide: true },
      (err, stdout) => {
        if (!err && stdout) {
          const names = stdout
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean);
          if (names.length > 0) {
            commandNames = names;
            resolve(names);
            return;
          }
        }
        commandNames = scanPathCommands();
        resolve(commandNames);
      }
    );
  }
  return commandLoad;
}

// ---------------------------------------------------------------------------
// File suggestions for argument tokens (relative to session cwd).
// ---------------------------------------------------------------------------
function fileItems(token: string): AutocompleteItem[] {
  const slashIdx = token.lastIndexOf("/");
  const dirPart = slashIdx >= 0 ? token.slice(0, slashIdx + 1) : "";
  const base = slashIdx >= 0 ? token.slice(slashIdx + 1) : token;
  const dir = dirPart ? resolve(cwd, dirPart) : cwd;
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
      return {
        value,
        label: value,
        ...(isDir ? { description: "directory" } : {}),
      };
    });
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
    // `!` or `! `: list every command.
    const names = await loadCommands();
    return {
      items: names.slice(0, 60).map((name) => ({ value: name, label: name })),
      prefix: "",
    };
  }

  const token = tokenMatch[1];
  const tokenStart = tokenMatch.index;
  const isFirstToken = afterBang.slice(0, tokenStart).trim() === "";
  if (isFirstToken) {
    const names = await loadCommands();
    const items = names
      .filter((n) => n.startsWith(token))
      .slice(0, 60)
      .map((name) => ({ value: name, label: name }));
    return { items, prefix: token };
  }

  const items = fileItems(token);
  return { items, prefix: token };
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
  const before = (lines[cursorLine] ?? "").slice(0, cursorCol);
  return /^\s*!/.test(before);
}

// ---------------------------------------------------------------------------
// Wrapper: handle `!` lines ourselves, delegate everything else to the
// built-in provider (slash commands, @-mentions, path completion).
// ---------------------------------------------------------------------------
export function wrapProvider(current: AutocompleteProvider): AutocompleteProvider {
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
    getInlineHint(lines, cursorLine, cursorCol) {
      return current.getInlineHint?.(lines, cursorLine, cursorCol) ?? null;
    },
  };
}

export default function bashBangComplete(pi: ExtensionAPI): void {
  pi.on("session_start", (_event, ctx) => {
    cwd = ctx.cwd;
    if (registered) return;
    registered = true;
    ctx.ui.addAutocompleteProvider(wrapProvider);
  });
}
