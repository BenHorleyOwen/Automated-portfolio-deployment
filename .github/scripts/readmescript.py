import os
import re
import argparse
import shutil
"""Script to generate README.md from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts
presentation sections to compile into a README.md using a template.

potential improvements:
- customize tags to search for in frontmatter and sections to extract
- pull file names and organises by project ID

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
    :return: list of presentation sections from the files, maintains nesting levels
    """
    sections = []
    pattern = re.compile(r'(?im)^(#{1,6})\s*presentation\s*$.*?(?=^(?!\1#)\1\s|^\Z)', re.DOTALL)

    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            for match in pattern.finditer(content):
                sections.append(match.group(0).strip())
    return sections

#overwrite file in checked out repo
parser = argparse.ArgumentParser(description='Generate README from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
args = parser.parse_args()
destination_path = args.destination
source_path = args.source
template_path = './.github/scripts/Template.md'

#generate README content
presentable_files = search_for_presentable_files(source_path)
presentation_sections = extract_presentation_sections(presentable_files)
#open template and save results to README.md in destination
os.makedirs(destination_path, exist_ok=True) #ensure destination directory exists

readme_path = os.path.join(destination_path, 'README.md')
shutil.copyfile(template_path, readme_path)  # Copy template to README.md
with open(readme_path, 'w', encoding='utf-8') as readme_file:
    for section in presentation_sections:
        readme_file.write(section + "\n\n---\n\n")
print(f'Generated README at {readme_path} from {len(presentation_sections)} sections.')
