import os

import pandas as pd
from tabulate import tabulate

DEFAULT_EXTENSIONS = ['.config', '.xml', '.json', '.ini']

def search_in_file(filepath, search_str):
    results = []
    search_lower = search_str.lower()
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f, start=1):
            if search_lower in line.lower():
                count = line.lower().count(search_lower)
                results.append((count, i, line.strip()))
    return results

def recursive_search(folder, search_str, extensions):
    records = []
    search_lower = search_str.lower()

    for root, dirs, files in os.walk(folder):
        for file in files:
            full_path = os.path.join(root, file)
            file_lower = file.lower()

            # 1. Check file name 
            if search_lower in file_lower:
                records.append({
                    "Occurrences #": file_lower.count(search_lower),
                    "File": full_path,
                    "Line #": "-",  # No line number for file name match
                    "Line text": f"[MATCH IN FILE NAME] {file}"
                })

            # 2. If extension matches, check contents
            if any(file_lower.endswith(ext) for ext in extensions):
                matches = search_in_file(full_path, search_str)
                for count, line_num, line_text in matches:
                    if len(line_text) > 90:
                        line_text = line_text[:87] + "..."
                    records.append({
                        "Occurrences #": count,
                        "File": full_path,
                        "Line #": line_num,
                        "Line text": line_text
                    })

    return records

def parse_extensions(input_str):
    input_str = input_str.strip()
    if input_str == "*":
        return DEFAULT_EXTENSIONS
    else:
        # Split by comma, ensure each extension starts with a dot
        return [
            ext if ext.startswith('.') else f'.{ext}'
            for ext in input_str.split(',')
        ]

def main():
    folder = input("Enter the folder path: ").strip()
    search_str = input("Enter the string to search for: ").strip()
    ext_input = input("Enter file extensions to search (e.g. config,xml) or '*' for all: ").strip()

    extensions = parse_extensions(ext_input)
    print(f"\nSearching in files with extensions: {', '.join(extensions)}\n")

    results = recursive_search(folder, search_str, extensions)

    if not results:
        print(f"No occurrences of '{search_str}' found in specified file types.")
        return

    df = pd.DataFrame(results)
    print(tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False))  # type: ignore

if __name__ == "__main__":
    main()
