import re
import sys


BLOCK = re.compile(
    r"\\begin\{longtable\}\[\]\{@\{\}(?P<spec>.*?)@\{\}\}\s*"
    r"\\caption\{(?P<cap>.*?)\}\\label\{(?P<lab>.*?)\}\\tabularnewline"
    r"(?P<rest>.*?)"
    r"\\end\{longtable\}",
    re.S,
)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _spec(spec: str) -> str:
    if re.fullmatch(r"[lcr]+", spec):
        n = len(spec)
        column = r">{\raggedright\arraybackslash}p{(\linewidth - %d\tabcolsep) * \real{%.4f}}" % (2 * n, 1.0 / n)
        return " ".join([column] * n)
    return re.sub(
        r"(\\linewidth - )(\d+)(\\tabcolsep)",
        lambda match: f"{match.group(1)}{int(match.group(2)) + 2}{match.group(3)}",
        spec,
    )


def _convert(match: re.Match) -> str:
    spec = _spec(_collapse(match.group("spec")))
    caption = match.group("cap")
    label = match.group("lab")
    rest = match.group("rest")

    end_head = rest.find("\\endhead")
    head = rest[:end_head]
    body = rest[end_head + len("\\endhead") :]

    if "\\endfirsthead" in head:
        head = head.split("\\endfirsthead", 1)[1]

    body = body.replace("\\bottomrule\\noalign{}", "", 1)
    body = body.replace("\\endlastfoot", "", 1)

    for old, new in (("\\noalign{}", ""), ("\\tabularnewline", "\\\\")):
        head = head.replace(old, new)
        body = body.replace(old, new)

    return (
        "\\begin{table}[!t]\n\\centering\\footnotesize\n"
        f"\\caption{{{caption}}}\\label{{{label}}}\n"
        f"\\begin{{tabular}}{{{spec}}}\n"
        f"{_collapse(head)}\n{body.strip()}\n\\bottomrule\n"
        "\\end{tabular}\n\\end{table}"
    )


def main() -> int:
    path = sys.argv[1]
    with open(path, encoding="utf-8") as handle:
        tex = handle.read()

    fixed, count = BLOCK.subn(_convert, tex)

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(fixed)

    print(f"longtable_to_table: converted {count} table(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
