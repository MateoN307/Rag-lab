import os
import re
from dataclasses import dataclass

CHUNK_SIZE = 400
OVERLAP = 50

# Paths to the test fixtures, expressed relative to this file's location so
# the test suite works regardless of where the repo is cloned to — and so
# the source doesn't bake in any machine-specific directory structure.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(APP_DIR, "..", "tests", "chunker")

FIND_MD_TEST_DIR = os.path.join(TESTS_DIR, "1")
MD_PARSER_TEST_DIR = os.path.join(TESTS_DIR, "2")
CHUNK_FILE_TEST_DIR = os.path.join(TESTS_DIR, "3")
CHUNK_DIR_TEST_DIR = os.path.join(TESTS_DIR, "4")


@dataclass
class Chunk:
    text: str
    source: str
    index: int


def chunk_dir(dir_path: str) -> list[Chunk]:
    """
    Walk `dir_path`, process every .md file found (including subfolders),
    and return a flat list of Chunk records.
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"Not a directory: {dir_path}")

    chunks = []
    for current_dir, _, _ in os.walk(dir_path):
        for file_path in _find_md_files(current_dir):
            source = os.path.relpath(file_path, dir_path)
            chunks.extend(chunk_file(file_path, source))

    return chunks


def chunk_file(file_path: str, source: str) -> list[Chunk]:
    """
    Clean and split a single markdown file's contents into a list of
    Chunk records.
    """
    if not file_path.endswith(".md"):
        raise ValueError(f"Not a markdown file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = _md_parser(text)

    words = text.split()
    total = len(words)

    chunks = []
    start = 0
    index = 0
    while start < total:
        end = start + CHUNK_SIZE + OVERLAP
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append(Chunk(text=chunk_text, source=source, index=index))
        start += CHUNK_SIZE
        index += 1

    return chunks


def _md_parser(text: str) -> str:
    """
    Take the full text of a file already confirmed to be markdown (.md) and
    clean it up for chunking:
      - `![[image embeds]]` are removed entirely
      - `[[wiki links]]` are replaced with their visible label
        (`[[Note Name|Display]]` -> `Display`, `[[Note Name]]` -> `Note Name`)
      - the YAML frontmatter "header" block (the `---` ... `---` block at the
        very top, if present) is stripped
    The remaining text is normalized into a single whitespace-separated
    string (no newlines or extra whitespace).
    """
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda m: m.group(2) if m.group(2) else m.group(1),
        text,
    )

    lines = text.splitlines()

    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                lines = lines[i + 1:]
                break

    text = "\n".join(lines)
    words = text.split()
    return " ".join(words)


def _find_md_files(dir_path: str) -> list[str]:
    """
    Look inside `dir_path` only (not its subfolders — that's chunk_dir's
    job) and return a flat list of full paths to every .md file directly
    in it. Anything that isn't a .md file — including subdirectories — is
    skipped.
    """
    md_files = []
    for entry in os.listdir(dir_path):
        full_path = os.path.join(dir_path, entry)
        if os.path.isfile(full_path) and entry.endswith(".md"):
            md_files.append(full_path)
    return md_files


#### Tests ####

def _test_find_md_files():
    """Edge cases to check: only .md files returned, subdirectories skipped,
    non-.md files skipped, only the immediate directory is scanned."""
    cases = {
        "empty": [],
        "only_dirs": [],
        "dirs_and_other_files": [],
        "only_md": ["a.md", "b.md"],
        "mixed": ["a.md", "b.md"],
    }

    for folder, expected_names in cases.items():
        dir_path = os.path.join(FIND_MD_TEST_DIR, folder)
        expected = sorted(os.path.join(dir_path, name) for name in expected_names)
        result = sorted(_find_md_files(dir_path))

        if result == expected:
            print(f"PASS: {folder}")
        else:
            print(f"FAIL: {folder}")
            missing = [path for path in expected if path not in result]
            extra = [path for path in result if path not in expected]
            if missing:
                print(f"  missing (expected but not returned): {missing}")
            if extra:
                print(f"  extra (returned but not expected): {extra}")


def _test_md_parser():
    """Edge cases to check: file with frontmatter, file without frontmatter,
    file with a body '---' divider but no frontmatter, file with frontmatter
    AND a body divider, frontmatter-only file, empty file, plain wiki link
    ([[Note Name]]), wiki link with display text ([[Note Name|Display]]),
    image embed (![[...]]), and a combination of all link/embed forms plus
    frontmatter in one file."""
    cases = {
        "with_frontmatter.md": (
            "# Sample note This is a note that has frontmatter and nothing "
            "else unusual in its body."
        ),
        "no_frontmatter.md": (
            "# Sample note This is a note that has no frontmatter at all — "
            "it just starts with content."
        ),
        "no_frontmatter_with_divider.md": (
            "# Sample note This note has no frontmatter, but uses a "
            "horizontal rule divider below. --- This text comes after the "
            "divider and should NOT be removed."
        ),
        "frontmatter_with_divider.md": (
            "# Sample note This note has frontmatter, and also a horizontal "
            "rule divider further down. --- This text comes after the "
            "divider and should NOT be removed."
        ),
        "frontmatter_only.md": "",
        "empty.md": "",
        "wiki_link_plain.md": "Note Name is referenced here.",
        "wiki_link_display.md": "Display Text is referenced here.",
        "image_embed.md": "Here is an image: and more text.",
        "mixed_links_embeds.md": (
            "See Project Plan for details, also check the plan and the "
            "diagram below."
        ),
    }

    for filename, expected in cases.items():
        file_path = os.path.join(MD_PARSER_TEST_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        result = _md_parser(text)

        if result == expected:
            print(f"PASS: {filename}")
        else:
            print(f"FAIL: {filename}")
            print(f"  expected: {expected!r}")
            print(f"  got:      {result!r}")


def _test_chunk_file():
    """Edge cases to check: file shorter than one chunk, file spanning
    multiple chunks (overlap correctness), empty/header-only file."""
    cases = {
        "short.md": [
            Chunk(text="one two three four five", source="short.md", index=0),
        ],
        "header_only.md": [],
        "empty.md": [],
        "multi_chunk.md": [
            Chunk(
                text=" ".join(f"word{i}" for i in range(1, 451)),
                source="multi_chunk.md",
                index=0,
            ),
            Chunk(
                text=" ".join(f"word{i}" for i in range(401, 851)),
                source="multi_chunk.md",
                index=1,
            ),
            Chunk(
                text=" ".join(f"word{i}" for i in range(801, 1001)),
                source="multi_chunk.md",
                index=2,
            ),
        ],
    }

    for filename, expected in cases.items():
        file_path = os.path.join(CHUNK_FILE_TEST_DIR, filename)
        result = chunk_file(file_path, filename)

        if result == expected:
            print(f"PASS: {filename}")
        else:
            print(f"FAIL: {filename}")
            print(f"  expected: {expected}")
            print(f"  got:      {result}")


def _test_chunk_dir():
    """Edge cases to check: invalid directory path raises an error, nested
    subdirectories get walked, results from multiple files are concatenated
    correctly with consistent per-file indexing."""
    expected = [
        Chunk(text="one two three four five", source="short.md", index=0),
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=0,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(401, 851)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=1,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(801, 1001)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=2,
        ),
        Chunk(
            text=(
                "# Sample note This is a note that has frontmatter and "
                "nothing else unusual in its body."
            ),
            source=os.path.join("sub_a", "sub_b", "with_frontmatter.md"),
            index=0,
        ),
    ]

    result = chunk_dir(CHUNK_DIR_TEST_DIR)

    sort_key = lambda c: (c.source, c.index)
    sorted_result = sorted(result, key=sort_key)
    sorted_expected = sorted(expected, key=sort_key)

    if sorted_result == sorted_expected:
        print("PASS: chunk_dir output matches expected chunks")
    else:
        print("FAIL: chunk_dir output does not match expected chunks")
        print(f"  expected: {sorted_expected}")
        print(f"  got:      {sorted_result}")

    try:
        chunk_dir(os.path.join(CHUNK_DIR_TEST_DIR, "does_not_exist"))
        print("FAIL: chunk_dir did not raise an error for an invalid directory")
    except ValueError:
        print("PASS: chunk_dir raised ValueError for an invalid directory")


def _inspect_chunks(chunks):
    print(f"Total chunks: {len(chunks)}")

    view = input(
        "View options:\n"
        "  1 - preview every chunk (first 50 characters)\n"
        "  2 - view a specific chunk in full\n"
        "> "
    )

    if view == "1":
        for chunk in chunks:
            print(f"[{chunk.index}] {chunk.source}: {chunk.text[:50]!r}")
    elif view == "2":
        position = int(input(f"Which chunk? (0-{len(chunks) - 1}): "))
        if 0 <= position < len(chunks):
            print(chunks[position])
        else:
            print(f"Out of range: {position}")
    else:
        print(f"Unrecognized option: {view}")


_TESTS = {
    "find_md_files": _test_find_md_files,
    "md_parser": _test_md_parser,
    "chunk_file": _test_chunk_file,
    "chunk_dir": _test_chunk_dir,
}


def _run_individual_test(name):
    test_func = _TESTS.get(name)
    if test_func is None:
        print(f"Unrecognized function: {name}")
    else:
        test_func()


if __name__ == "__main__":
    mode = input(
        "Choose an option:\n"
        "  1 - run all individual function tests\n"
        "  2 - run chunk_dir\n"
        "  3 - run a single function test\n"
        "> "
    )

    if mode == "1":
        for test_name, test_func in _TESTS.items():
            print(f"--- {test_name} ---")
            test_func()
            print()
    elif mode == "2":
        test_dir = input("Enter directory path to test chunk_dir on: ")
        chunks = chunk_dir(test_dir)
        _inspect_chunks(chunks)
    elif mode == "3":
        name = input("Which function? (find_md_files / md_parser / chunk_file / chunk_dir): ")
        _run_individual_test(name)
    else:
        print(f"Unrecognized option: {mode}")
