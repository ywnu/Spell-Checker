import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import spellchecker as pyspell_module

#Windows 98 Color Palette
WIN98_BG = "#c0c0c0"
WIN98_DARK = "#808080"
WIN98_LIGHT = "#ffffff"
WIN98_TITLE_BG = "#000080"
WIN98_TITLE_FG = "#ffffff"
WIN98_TEXT_BG = "#ffffff"
WIN98_TEXT_FG = "#000000"
WIN98_FONT = ("Courier New", 10)
WIN98_FONT_BOLD = ("Courier New", 10, "bold")
WIN98_FONT_SM = ("Courier New", 9)
WIN98_FONT_LG = ("Courier New", 13, "bold")
WIN98_GREEN = "#006400"
WIN98_ORANGE = "#8B4513"
WIN98_RED = "#8B0000"
WIN98_BLUE = "#000080"


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.frequency = 0


class SpellChecker:
    def __init__(self):
        self.root = TrieNode()
        self.all_words_list = []
        self.min_frequency = 1
        self.pyspell = pyspell_module.SpellChecker()

    def insert(self, word, frequency=1):
        word = word.lower().strip()
        if not word:
            return
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if not node.is_end_of_word:
            node.is_end_of_word = True
            self.all_words_list.append(word)
        node.frequency = frequency

    def search(self, word):
        node = self.root
        for char in word.lower().strip():
            if char not in node.children:
                return False
            node = node.children[char]
        if not node.is_end_of_word:
            return False
        return node.frequency >= self.min_frequency
    def get_suggestions(self, word, n=5):
        word = word.lower().strip()
        if not word:
            return []

        candidates = self.pyspell.candidates(word)
        if not candidates:
            return []

        ranked = sorted(candidates, key=lambda w: self.pyspell.word_frequency[w], reverse=True)
        return ranked[:n]


def load_full_dictionary(obj, filename):
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            for line in f:
                parts = line.strip().split(",")
                if not parts:
                    continue
                word = parts[0].strip()
                frequency = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 1
                if word:
                    obj.insert(word, frequency)
        return len(obj.all_words_list)
    except Exception as e:
        raise Exception(f"Error loading file: {e}")


class SpellCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Spell Checker")
        self.root.geometry("820x680")
        self.root.resizable(True, True)
        self.root.configure(bg=WIN98_BG)

        self.checker = SpellChecker()
        self.dictionary_loaded = False

        self._apply_global_style()
        self._build_ui()
        self._load_dictionary_startup()

    def _apply_global_style(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Win98.TFrame", background=WIN98_BG)
        style.configure("Win98.TLabel", background=WIN98_BG, foreground=WIN98_TEXT_FG, font=WIN98_FONT)
        style.configure("Win98.Bold.TLabel", background=WIN98_BG, foreground=WIN98_TEXT_FG, font=WIN98_FONT_BOLD)
        style.configure("Win98.Title.TLabel", background=WIN98_TITLE_BG, foreground=WIN98_TITLE_FG, font=WIN98_FONT_LG)
        style.configure("Win98.Status.TLabel", background=WIN98_BG, foreground=WIN98_BLUE, font=WIN98_FONT_SM, relief="sunken", padding=(4, 2))
        style.configure("Win98.TSeparator", background=WIN98_DARK)

    def _toggle_maximize(self):
        if self.root.state() == "zoomed":
            self.root.state("normal")
        else:
            self.root.state("zoomed")

    def _build_ui(self):
        title_bar = tk.Frame(self.root, bg=WIN98_TITLE_BG, height=28)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="  🔤  Smart Spell Checker",
            bg=WIN98_TITLE_BG,
            fg=WIN98_TITLE_FG,
            font=("Courier New", 11, "bold"),
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # FIX 2: removed the broken nested _toggle_maximize definition
        # FIX 3: removed "cmd if cmd else lambda: None" — all commands are valid functions
        for sym, cmd in [
            ("X", self.root.destroy),
            ("□", self._toggle_maximize),
            ("_", self.root.iconify),
        ]:
            btn = tk.Button(
                title_bar,
                text=sym,
                width=3,
                bg=WIN98_BG,
                fg=WIN98_TEXT_FG,
                font=("Courier New", 9, "bold"),
                relief="raised",
                bd=2,
                cursor="hand2",
                command=cmd,
            )
            btn.pack(side=tk.RIGHT, padx=1, pady=2)

        menu_bar = tk.Frame(self.root, bg=WIN98_BG, bd=1, relief="raised")
        menu_bar.pack(fill=tk.X)
        for item in ("File", "Edit", "View", "Tools", "Help"):
            lbl = tk.Label(
                menu_bar,
                text=item,
                bg=WIN98_BG,
                fg=WIN98_TEXT_FG,
                font=WIN98_FONT,
                padx=8,
                pady=3,
                cursor="hand2",
            )
            lbl.pack(side=tk.LEFT)
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=WIN98_TITLE_BG, fg=WIN98_TITLE_FG))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg=WIN98_BG, fg=WIN98_TEXT_FG))

        status_frame = tk.Frame(self.root, bg=WIN98_BG, relief="sunken", bd=1)
        status_frame.pack(fill=tk.X, padx=4, pady=(4, 0))
        self.status_label = tk.Label(
            status_frame,
            text="⏳ Loading dictionary...",
            bg=WIN98_BG,
            fg="#8B4513",
            font=WIN98_FONT_SM,
            anchor="w",
            padx=6,
            pady=2,
        )
        self.status_label.pack(fill=tk.X)

        content = tk.Frame(self.root, bg=WIN98_BG, padx=8, pady=6)
        content.pack(fill=tk.BOTH, expand=True)

        lbl_in = tk.Label(content, text="Enter Text:", bg=WIN98_BG, fg=WIN98_TEXT_FG, font=WIN98_FONT_BOLD, anchor="w")
        lbl_in.pack(fill=tk.X, pady=(2, 2))

        in_outer = tk.Frame(content, bg=WIN98_BG, relief="sunken", bd=2)
        in_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        self.text_input = scrolledtext.ScrolledText(
            in_outer,
            height=6,
            font=WIN98_FONT,
            wrap=tk.WORD,
            bg=WIN98_TEXT_BG,
            fg=WIN98_TEXT_FG,
            insertbackground=WIN98_TEXT_FG,
            relief="flat",
            bd=0,
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        btn_frame = tk.Frame(content, bg=WIN98_BG)
        btn_frame.pack(fill=tk.X, pady=4)

        for text, cmd in [
            ("✅ Check Spelling", self.check_spelling),
            ("🧹 Clear", self.clear_input),
        ]:
            b = tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                bg="#c0c0c0",
                fg=WIN98_TEXT_FG,
                font=WIN98_FONT_BOLD,
                relief="raised",
                bd=3,
                padx=12,
                pady=5,
                cursor="hand2",
                activebackground=WIN98_BG,
                activeforeground=WIN98_TEXT_FG,
            )
            b.pack(side=tk.LEFT, padx=4)

        sep = tk.Frame(content, bg=WIN98_DARK, height=2)
        sep.pack(fill=tk.X, pady=4)

        lbl_out = tk.Label(content, text="Results:", bg=WIN98_BG, fg=WIN98_TEXT_FG, font=WIN98_FONT_BOLD, anchor="w")
        lbl_out.pack(fill=tk.X, pady=(2, 2))

        out_outer = tk.Frame(content, bg=WIN98_BG, relief="sunken", bd=2)
        out_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        self.text_output = scrolledtext.ScrolledText(
            out_outer,
            height=7,
            font=WIN98_FONT,
            wrap=tk.WORD,
            bg=WIN98_TEXT_BG,
            fg=WIN98_TEXT_FG,
            state=tk.DISABLED,
            relief="flat",
            bd=0,
        )
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.text_output.tag_configure("correct", foreground=WIN98_GREEN, font=WIN98_FONT_BOLD)
        self.text_output.tag_configure("suggestion", foreground=WIN98_ORANGE, font=WIN98_FONT_BOLD)
        self.text_output.tag_configure("error", foreground=WIN98_RED, font=WIN98_FONT_BOLD)
        self.text_output.tag_configure("stats", foreground=WIN98_BLUE, font=WIN98_FONT_BOLD)
        self.text_output.tag_configure("normal", foreground=WIN98_TEXT_FG)

        stats_frame = tk.Frame(self.root, bg=WIN98_BG, relief="sunken", bd=1)
        stats_frame.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.lbl_total = self._stat_label(stats_frame, "Total: 0")
        self.lbl_correct = self._stat_label(stats_frame, "✅ Correct: 0", WIN98_GREEN)
        self.lbl_suggest = self._stat_label(stats_frame, "⚠ Suggest: 0", WIN98_ORANGE)
        self.lbl_error = self._stat_label(stats_frame, "❌ Errors: 0", WIN98_RED)

        bottom = tk.Frame(self.root, bg=WIN98_BG, relief="raised", bd=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.bottom_status = tk.Label(
            bottom,
            text="Ready",
            bg=WIN98_BG,
            fg=WIN98_TEXT_FG,
            font=WIN98_FONT_SM,
            anchor="w",
            padx=6,
            relief="sunken",
            bd=1,
        )
        self.bottom_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        tk.Label(
            bottom,
            text="NUM LOCK",
            bg=WIN98_BG,
            fg=WIN98_TEXT_FG,
            font=WIN98_FONT_SM,
            relief="sunken",
            bd=1,
            padx=6,
        ).pack(side=tk.RIGHT, padx=2, pady=2)

        self.progress = ttk.Progressbar(bottom, orient="horizontal", length=120, mode="determinate")
        self.progress.pack(side=tk.RIGHT, padx=6, pady=4)

    def _stat_label(self, parent, text, color=None):
        lbl = tk.Label(
            parent,
            text=text,
            bg=WIN98_BG,
            fg=color if color else WIN98_TEXT_FG,
            font=WIN98_FONT_SM,
            padx=10,
            pady=2,
            relief="sunken",
            bd=1,
        )
        lbl.pack(side=tk.LEFT, padx=2, pady=2)
        return lbl

    def _load_dictionary_startup(self):
        def load():
            try:
                for i in range(0, 80, 10):
                    self.root.after(i * 10, lambda v=i: self.progress.configure(value=v))
                word_count = load_full_dictionary(self.checker, "dictionary.csv")
                self.dictionary_loaded = True
                self.root.after(0, self._on_dict_loaded, word_count)
            except Exception as e:
                self.root.after(0, self._on_dict_error, str(e))

        threading.Thread(target=load, daemon=True).start()

    def _on_dict_loaded(self, count):
        self.progress.configure(value=100)
        self.status_label.config(text=f"✅ Loaded {count:,} words from dictionary", fg=WIN98_GREEN)
        self.bottom_status.config(text="Dictionary ready — enter text and click Check Spelling")

    def _on_dict_error(self, err):
        self.progress.configure(value=0)
        self.status_label.config(text=f"❌ {err}", fg=WIN98_RED)
        self.bottom_status.config(text="Dictionary load failed")

    def check_spelling(self):
        if not self.dictionary_loaded:
            messagebox.showwarning("Warning", "Dictionary not loaded yet. Please wait...")
            return

        sentence = self.text_input.get("1.0", tk.END).strip()
        if not sentence:
            messagebox.showwarning("Warning", "Please enter some text to check!")
            return

        self.bottom_status.config(text="Checking spelling...")
        threading.Thread(target=self._check_thread, args=(sentence,), daemon=True).start()

    def _check_thread(self, sentence):
        words = re.findall(r"\b\w+\b", sentence)
        results = []
        correct_count = 0
        suggestion_count = 0
        error_count = 0
        corrected_words = []

        for w in words:
            if self.checker.search(w):
                results.append((w, "correct"))
                corrected_words.append(w)
                correct_count += 1
            else:
                suggestions = self.checker.get_suggestions(w, n=5)
                if suggestions:
                    results.append((f"{w} -> {', '.join(suggestions)}", "suggestion"))
                    corrected_words.append(suggestions[0])
                    suggestion_count += 1
                else:
                    results.append((f"{w}?", "error"))
                    corrected_words.append(w)
                    error_count += 1

        corrected_sentence = " ".join(corrected_words)
        self.root.after(
            0,
            self._display_results,
            results,
            correct_count,
            len(words),
            suggestion_count,
            error_count,
            corrected_sentence
        )

    def _display_results(self, results, correct_count, total, suggestions, errors, corrected_sentence):
        self.lbl_total.config(text=f"Total: {total}")
        self.lbl_correct.config(text=f"✅ Correct: {correct_count}")
        self.lbl_suggest.config(text=f"⚠ Suggest: {suggestions}")
        self.lbl_error.config(text=f"❌ Errors: {errors}")

        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete("1.0", tk.END)

        stats = (
            f"Words: {total}  |  Correct: {correct_count}"
            f"  |  Suggestions: {suggestions}  |  Errors: {errors}\n"
        )
        self.text_output.insert(tk.END, stats, "stats")
        self.text_output.insert(tk.END, "-" * 64 + "\n\n", "normal")

        self.text_output.insert(tk.END, "Suggestions:\n\n", "normal")
        for word, tag in results:
            self.text_output.insert(tk.END, word + "\n", tag)

        self.text_output.insert(tk.END, "\nBest corrected sentence:\n", "normal")
        self.text_output.insert(tk.END, corrected_sentence, "correct")

        self.text_output.config(state=tk.DISABLED)

        status = "All words correct!" if errors == 0 and suggestions == 0 else f"Done — {errors + suggestions} issue(s) found"
        self.bottom_status.config(text=status)

    def clear_input(self):
        self.text_input.delete("1.0", tk.END)
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete("1.0", tk.END)
        self.text_output.config(state=tk.DISABLED)

        for lbl, txt in [
            (self.lbl_total, "Total: 0"),
            (self.lbl_correct, "✅ Correct: 0"),
            (self.lbl_suggest, "⚠ Suggest: 0"),
            (self.lbl_error, "❌ Errors: 0"),
        ]:
            lbl.config(text=txt)

        self.bottom_status.config(text="Ready")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = SpellCheckerGUI(root)
    root.mainloop()
