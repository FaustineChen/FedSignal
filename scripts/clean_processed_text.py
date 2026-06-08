# clean text
from pathlib import Path
import re

def remove_minutes_headers_footers(line: str) -> str:
    # odd page
    # "... Minutes of the Federal Open Market Committee    3"
    line = re.sub(
        r"\s+Minutes of the Federal Open Market Committee\s+\d+\s*$",
        "",
        line
    )

    # even page
    # "... 2    April 28–29, 2026"
    line = re.sub(
        r"\s+\d+\s+[A-Z][a-z]+ \d{1,2}[\u2013-]\d{1,2}, \d{4}\s*$",
        "",
        line
    )

    return line.strip()

def remove_statement_and_press_headers(line: str) -> str:
    # statement
    # "For release at 2:00 p.m. EDT                     April 29, 2026"
    line = re.sub(
        r"\s*For release at .*?\b[A-Z][a-z]+ \d{1,2}, \d{4}\s*$",
        "",
        line
    )

    # press conference
    # "April 29, 2026   Chair Powell’s Press Conference  FINAL"
    line = re.sub(
        r"\s*[A-Z][a-z]+ \d{1,2}, \d{4}\s+Chair Powell[’']s Press Conference\s+FINAL\s*$",
        "",
        line
    )

    return line.strip()

def clean_texts(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_files = list(input_path.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files")

    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8")

        # remove literal /n caused by PDF extraction
        text = text.replace("/n", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            if line == "":
                cleaned_lines.append("")
                continue
            
            # remove footer/header of minutes
            line = remove_minutes_headers_footers(line)
            if line == "":
                cleaned_lines.append("")
                continue

            # remove date header
            line = remove_statement_and_press_headers(line)
            if line == "":
                cleaned_lines.append("")
                continue

            # remove Page 1 / Page 1 of 10
            if re.fullmatch(r"Page\s+\d+(\s+of\s+\d+)?", line, flags=re.IGNORECASE):
                continue

            # remove one line page -2-, -0-
            if re.fullmatch(r"-\d+-", line):
                continue

            # remove begining page -2-
            line = re.sub(r"^-\d+-\s*", "", line)

            # remove one line page 0, 1
            if re.fullmatch(r"\d+", line):
                continue

            # remove (more)
            if line.lower() == "(more)":
                continue

            cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines)

        # compress 3+ newlines into 2 newlines
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        # write to new .txt
        output_file = output_path / txt_file.name
        output_file.write_text(cleaned_text, encoding="utf-8")

        print("=" * 20)
        print(f"File: {txt_file.name}")
        print(f"Original characters: {len(text)}")
        print(f"Cleaned characters: {len(cleaned_text)}")
        print(f"Saved to: {output_file}")



    """
    text_path1 = "data/processed/fomc_minutes_20260429.txt"
    text_path2 = "data/processed/fomc_statement_20260429.txt"
    text_path3 = "data/processed/fomc_press_conference_20260429.txt"
    #text = Path(text_path1).read_text(encoding="utf-8")
    #text = Path(text_path2).read_text(encoding="utf-8")
    text = Path(text_path3).read_text(encoding="utf-8")
    text = text.replace("/n", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")

    for i, line in enumerate(lines[:80]):
        line = line.strip()
        line = remove_minutes_headers_footers(line)

        # Page 1 / Page 1 of 10
        if re.fullmatch(r"Page\s+\d+(\s+of\s+\d+)?", line, flags=re.IGNORECASE):
            continue

        # one line page -2-, -0-
        if re.fullmatch(r"-\d+-", line):
            continue

        # begining page -2-
        line = re.sub(r"^-\d+-\s*", "", line)

        # one line page 0, 1
        if re.fullmatch(r"\d+", line):
            continue

        # (more)
        if line.lower() == "(more)":
            continue

        print(i, repr(line))

    """


if __name__ == "__main__":
    clean_texts(input_dir = "data/processed", output_dir = "data/cleaned")