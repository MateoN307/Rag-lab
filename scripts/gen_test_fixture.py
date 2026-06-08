import os


def generate_word_file(dir_path, file_name, word_count):
    """
    Create a file at `dir_path/file_name` containing `word_count` words,
    each word being "word<N>" (word1, word2, word3, ...), separated by
    single spaces. Useful for building fixtures where the exact word
    count and word positions need to be known in advance — e.g. testing
    chunk_file's slicing/overlap math.
    """
    words = [f"word{i}" for i in range(1, word_count + 1)]
    text = " ".join(words)

    file_path = os.path.join(dir_path, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    dir_path = input("Directory to write the file into: ")
    file_name = input("File name (e.g. multi_chunk.md): ")
    word_count = int(input("Number of words to generate: "))

    generate_word_file(dir_path, file_name, word_count)
    print(f"Wrote {word_count} words to {os.path.join(dir_path, file_name)}")
