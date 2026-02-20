import os
import re
import argparse

"""Script to generate README.md from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts
presentation sections to compile into a README.md using a template.
potential improvements:
- customize tags to search for in frontmatter and sections to extract
- pull file names and organises by project ID
- add github project hyperlink compatability
test command: python3 .github/scripts/readmescript.py --source ./vaults/Technology/Projects --destination ./profile
"""

def search_for_presentable_files(repo_path):
    """
    Docstring for search_for_presentable_files
    could be modified to search for other tags as needed
    
    :param repo_path: path to the repository to search
    :return: list of file paths that are marked as presentable
    """
    presentable_files = []
    for dirpath, dirnames, filenames in os.walk(repo_path):
        for filename in filenames:
            if filename.endswith('.md'):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except (UnicodeDecodeError, OSError):
                    continue
                if re.search(r'^---.*?\bpresentable\b.*?---', content, re.IGNORECASE | re.DOTALL):
                    presentable_files.append(file_path)
    return presentable_files

def extract_presentation_sections(file_paths):
    """
    Docstring for extract_presentation_sections
    could be modified to extract other sections as needed
    :param file_paths: list of file paths to extract presentation sections from
    :return: list of tuples (file_title, section_content)
    """
    sections = []
    pattern = re.compile(r'(?im)^(#{1,6})\s*presentation\s*$.*?(?=^(?!\1#)\1\s|^\Z)', re.DOTALL)
    for file_path in file_paths:
        file_title = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            for match in pattern.finditer(content):
                sections.append((file_title, match.group(0).strip()))
    return sections

parser = argparse.ArgumentParser(description='Generate README from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
args = parser.parse_args()

destination_path = args.destination
source_path = args.source
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Template.md')

# generate README content
presentable_files = search_for_presentable_files(source_path)
presentation_sections = extract_presentation_sections(presentable_files)

# open template and save results to README.md in destination
os.makedirs(destination_path, exist_ok=True)
readme_path = os.path.join(destination_path, 'README.md')

with open(template_path, 'r', encoding='utf-8') as template_file:
    template_content = template_file.read()

with open(readme_path, 'w', encoding='utf-8') as readme_file:
    readme_file.write(template_content + "\n\n")
    for file_title, section in presentation_sections:
        readme_file.write(f"## {file_title}\n\n")
        readme_file.write(section + "\n\n---\n\n")

print(f'Generated README at {readme_path} from {len(presentation_sections)} sections.')