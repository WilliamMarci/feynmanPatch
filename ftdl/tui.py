# feynmanPatch/ftdl/tui.py

import sys
import os
import json

try:
    import curses
    _CURSES = True
except ImportError:
    _CURSES = False


class FTDLTUI(object):

    def __init__(self):
        self._stdscr = None
        self._file_content = ""
        self._filename = ""
        self._cursor_row = 0
        self._cursor_col = 0
        self._scroll_row = 0
        self._message = ""
        self._message_type = ""
        self._mode = "editor"
        self._ir_text = ""
        self._diag_text = ""
        self._diagrams = []
        self._json_diagrams = []
        self._rrows = 24
        self._rcols = 80

    def main(self):
        if not _CURSES or not sys.stdout.isatty():
            self._fallback()
            return
        try:
            curses.wrapper(self._curses_main)
        except Exception:
            self._fallback()

    def _fallback(self):
        print("FTDL Compiler TUI requires a curses-capable terminal.")
        print("Use the command-line interface instead:")
        print("  python -m ftdl <file.ftdl>")
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            from .compiler import FTDLCompiler
            compiler = FTDLCompiler()
            result = compiler.compile_file(sys.argv[1])
            if result["success"]:
                outpath = os.path.splitext(sys.argv[1])[0] + ".ll"
                with open(outpath, "w", encoding="utf-8") as f:
                    f.write(result["ir"])
                print("compilation successful -> %s" % outpath)
            else:
                print("compilation failed: %s" % result.get("error", "unknown"))

    def _curses_main(self, stdscr):
        self._stdscr = stdscr
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)

        self._rrows, self._rcols = stdscr.getmaxyx()
        stdscr.nodelay(0)
        stdscr.keypad(1)

        if len(sys.argv) > 1:
            path = sys.argv[1]
            if os.path.isfile(path):
                self._filename = path
                with open(path, "r", encoding="utf-8") as f:
                    self._file_content = f.read()

        self._run_loop()

    def _run_loop(self):
        while True:
            self._draw()
            ch = self._stdscr.getch()
            if self._mode == "editor":
                if not self._handle_editor_key(ch):
                    break
            else:
                if not self._handle_viewer_key(ch):
                    break

    def _handle_editor_key(self, ch):
        lines = self._file_content.split("\n") if self._file_content else [""]
        if ch == curses.KEY_F1:
            self._mode = "editor"
        elif ch == curses.KEY_F2:
            self._mode = "ir_viewer"
        elif ch == curses.KEY_F3:
            self._mode = "diag_viewer"
        elif ch == curses.KEY_F4:
            self._mode = "json_viewer"
        elif ch == curses.KEY_F5:
            self._do_compile()
        elif ch == curses.KEY_F6:
            if self._filename:
                self._do_export("json")
        elif ch == curses.KEY_F7:
            self._do_export("tex")
        elif ch == curses.KEY_F8:
            self._do_export("svg")
        elif ch == curses.KEY_F9:
            self._do_export("pdf")
        elif ch in (curses.KEY_F10, 27):
            return False
        elif ch == curses.KEY_UP:
            if self._cursor_row > 0:
                self._cursor_row -= 1
        elif ch == curses.KEY_DOWN:
            if self._cursor_row < len(lines) - 1:
                self._cursor_row += 1
        elif ch == curses.KEY_LEFT:
            if self._cursor_col > 0:
                self._cursor_col -= 1
        elif ch == curses.KEY_RIGHT:
            cur_line = lines[self._cursor_row] if self._cursor_row < len(lines) else ""
            if self._cursor_col < len(cur_line):
                self._cursor_col += 1
        elif ch in (curses.KEY_BACKSPACE, 127):
            self._edit_backspace(lines)
        elif ch == curses.KEY_DC:
            self._edit_delete(lines)
        elif ch == 10:
            self._edit_newline(lines)
        elif 32 <= ch <= 126:
            self._edit_insert(lines, chr(ch))
        return True

    def _handle_viewer_key(self, ch):
        if ch == curses.KEY_F1:
            self._mode = "editor"
        elif ch in (curses.KEY_F10, 27):
            return False
        return True

    def _edit_backspace(self, lines):
        if self._cursor_col > 0:
            line = lines[self._cursor_row]
            lines[self._cursor_row] = line[:self._cursor_col - 1] + line[self._cursor_col:]
            self._cursor_col -= 1
        elif self._cursor_row > 0:
            current = lines.pop(self._cursor_row)
            self._cursor_row -= 1
            self._cursor_col = len(lines[self._cursor_row])
            lines[self._cursor_row] += current
        self._file_content = "\n".join(lines)

    def _edit_delete(self, lines):
        if self._cursor_row < len(lines):
            line = lines[self._cursor_row]
            if self._cursor_col < len(line):
                lines[self._cursor_row] = line[:self._cursor_col] + line[self._cursor_col + 1:]
            elif self._cursor_row + 1 < len(lines):
                nxt = lines.pop(self._cursor_row + 1)
                lines[self._cursor_row] += nxt
        self._file_content = "\n".join(lines)

    def _edit_newline(self, lines):
        while len(lines) <= self._cursor_row:
            lines.append("")
        line = lines[self._cursor_row]
        lines[self._cursor_row] = line[:self._cursor_col]
        lines.insert(self._cursor_row + 1, line[self._cursor_col:])
        self._cursor_row += 1
        self._cursor_col = 0
        self._file_content = "\n".join(lines)

    def _edit_insert(self, lines, ch):
        while len(lines) <= self._cursor_row:
            lines.append("")
        line = lines[self._cursor_row]
        lines[self._cursor_row] = line[:self._cursor_col] + ch + line[self._cursor_col:]
        self._cursor_col += 1
        self._file_content = "\n".join(lines)

    def _do_compile(self):
        from .compiler import FTDLCompiler
        compiler = FTDLCompiler()
        result = compiler.compile_string(self._file_content, filename=self._filename)
        if result["success"]:
            self._message = "Compilation successful!"
            self._message_type = "success"
            self._ir_text = result.get("ir", "")
            self._diagrams = result.get("diagrams", [])
            self._json_diagrams = compiler.export_json(self._diagrams)
            diags = result.get("diagnostics", [])
            self._diag_text = "\n".join(diags) if diags else "(no warnings)"

            if self._json_diagrams:
                self._diag_text += "\n\n%d diagram(s) built\n" % len(self._json_diagrams)
        else:
            self._message = "Error: %s" % result.get("error", "unknown")
            self._message_type = "error"
            self._diag_text = result.get("error", "")
            self._json_diagrams = []
            self._diagrams = []

    def _do_export(self, fmt):
        if not self._filename:
            self._message = "No filename set. Save first (F5 then F6)."
            self._message_type = "error"
            return
        if not self._json_diagrams:
            self._message = "No diagrams to export. Compile first (F5)."
            self._message_type = "error"
            return

        from .compiler import FTDLCompiler
        compiler = FTDLCompiler()
        base = os.path.splitext(self._filename)[0]

        try:
            if fmt == "json":
                for i, d in enumerate(self._json_diagrams):
                    jpath = "%s_%04d.json" % (base, i + 1)
                    with open(jpath, "w", encoding="utf-8") as f:
                        json.dump(d, f, indent=2, sort_keys=False)
                self._message = "Exported %d JSON(s)" % len(self._json_diagrams)
                self._message_type = "success"

            elif fmt == "tex":
                for i, d in enumerate(self._json_diagrams):
                    tex = compiler.export_tex(d)
                    tpath = "%s_%04d.tex" % (base, i + 1)
                    with open(tpath, "w", encoding="utf-8") as f:
                        f.write(tex)
                self._message = "Exported %d TeX(s)" % len(self._json_diagrams)
                self._message_type = "success"

            elif fmt == "svg":
                for i, d in enumerate(self._json_diagrams):
                    svg = compiler.export_svg(d)
                    spath = "%s_%04d.svg" % (base, i + 1)
                    with open(spath, "w", encoding="utf-8") as f:
                        f.write(svg)
                self._message = "Exported %d SVG(s)" % len(self._json_diagrams)
                self._message_type = "success"

            elif fmt == "pdf":
                for i, d in enumerate(self._json_diagrams):
                    tex = compiler.export_tex(d)
                    tpath = "%s_%04d.tex" % (base, i + 1)
                    with open(tpath, "w", encoding="utf-8") as f:
                        f.write(tex)
                    self._compile_pdf(tpath)
                self._message = "Exported %d PDF(s)" % len(self._json_diagrams)
                self._message_type = "success"

        except Exception as e:
            self._message = "Export error: %s" % str(e)
            self._message_type = "error"

    def _compile_pdf(self, tex_path):
        import subprocess
        workdir = os.path.dirname(tex_path) or "."
        basename = os.path.basename(tex_path)
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", basename],
                cwd=workdir, capture_output=True, timeout=30,
            )
            aux = os.path.splitext(tex_path)[0] + ".aux"
            log = os.path.splitext(tex_path)[0] + ".log"
            for f in [aux, log]:
                if os.path.isfile(f):
                    os.remove(f)
        except Exception:
            pass

    def _draw(self):
        self._stdscr.erase()
        self._rrows, self._rcols = self._stdscr.getmaxyx()
        self._draw_status_bar()
        if self._mode == "editor":
            self._draw_editor()
        elif self._mode == "ir_viewer":
            self._draw_text(self._ir_text, "LLVM IR Output")
        elif self._mode == "diag_viewer":
            self._draw_text(self._diag_text, "Diagnostics")
        elif self._mode == "json_viewer":
            json_str = ""
            if self._json_diagrams:
                json_str = json.dumps(self._json_diagrams[0], indent=2)
            self._draw_text(json_str, "Diagram JSON (first)")
        self._draw_help_bar()
        self._stdscr.refresh()

    def _draw_status_bar(self):
        bar = " FTDL Compiler v0.1 | Mode: %s" % self._mode.upper()
        if self._filename:
            bar += " | File: %s" % os.path.basename(self._filename)
        bar = bar.ljust(self._rcols)
        self._stdscr.addstr(0, 0, bar, curses.color_pair(6))

        if self._message:
            color = curses.color_pair(2) if self._message_type == "success" else curses.color_pair(3)
            self._stdscr.addstr(1, 0, "  %s" % self._message[:self._rcols - 2], color)
            self._message = ""

    def _draw_editor(self):
        lines = self._file_content.split("\n") if self._file_content else [""]
        total = max(len(lines), 1)
        view_top = 3
        view_height = max(1, self._rrows - 5)

        if self._cursor_row < self._scroll_row:
            self._scroll_row = self._cursor_row
        if self._cursor_row >= self._scroll_row + view_height:
            self._scroll_row = self._cursor_row - view_height + 1
        if self._scroll_row < 0:
            self._scroll_row = 0

        for i in range(view_height):
            line_idx = self._scroll_row + i
            if line_idx >= total:
                break
            screen_row = view_top + i
            line = lines[line_idx] if line_idx < len(lines) else ""
            prefix = "%4d " % (line_idx + 1)
            self._stdscr.addstr(screen_row, 0, prefix, curses.color_pair(4))

            available = self._rcols - len(prefix)
            display = line[:available]
            if len(display) < available:
                display = display + " " * (available - len(display))

            attr = curses.A_NORMAL
            if line_idx == self._cursor_row:
                attr = curses.color_pair(6)

            try:
                self._stdscr.addstr(screen_row, len(prefix), display, attr)
            except curses.error:
                pass

    def _draw_text(self, text, title):
        if not text:
            self._stdscr.addstr(3, 2, "(empty)", curses.color_pair(4))
            return
        lines = str(text).split("\n")
        view_height = max(1, self._rrows - 5)
        for i in range(min(view_height, len(lines))):
            try:
                self._stdscr.addstr(3 + i, 1, lines[i][:self._rcols - 2], curses.color_pair(5))
            except curses.error:
                break

    def _draw_help_bar(self):
        bar = (" F1:Edit  F2:IR  F3:Diag  F4:JSON  F5:Compile  "
               "F6:JSON  F7:TeX  F8:SVG  F9:PDF  F10:Quit ")
        bar = bar.ljust(self._rcols)
        try:
            self._stdscr.addstr(self._rrows - 1, 0, bar, curses.color_pair(6))
        except curses.error:
            pass


def main():
    tui = FTDLTUI()
    tui.main()


if __name__ == "__main__":
    main()
