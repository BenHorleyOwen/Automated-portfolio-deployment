import os
import re
import argparse
import shutil

"""Script to generate README.md from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts
presentation sections to compile into a README.md using a template.
test command (short): python .github/scripts/readmescript.py --source D:\obsidian\vaults\vaults\Technology\Projects --destination ./profile --description-only
test command (full):  python3 .github/scripts/readmescript.py --source D:\obsidian\vaults\vaults\Technology\Projects --destination ./profile
"""

def parse_frontmatter(content):
    """Extract frontmatter fields from a markdown file."""
    frontmatter = {}
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if match:
        for line in match.group(1).splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                frontmatter[key.strip()] = value.strip()
    return frontmatter

def search_for_presentable_files(repo_path):
    """
    Search for files marked with 'presentable' in frontmatter.
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

def shift_headings(content, shift_by):
    """Shift all markdown headings down by shift_by levels."""
    def replacer(match):
        new_level = min(len(match.group(1)) + shift_by, 6)
        return '#' * new_level + match.group(2)
    return re.sub(r'^(#{1,6})([\s#])', replacer, content, flags=re.MULTILINE)

def extract_description_only(content_under_presentation):
    """Extract only the content under the ## Description heading."""
    match = re.search(
        r'(?im)^#{1,6}\s*description\s*$\n(.*?)(?=^#{1,6}\s|\Z)',
        content_under_presentation,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return content_under_presentation.strip()

def extract_presentation_sections(file_paths, description_only=False):
    """
    Extract presentation sections from files.
    :param file_paths: list of file paths to extract presentation sections from
    :param description_only: if True, only extract content under ## Description
    :return: list of tuples (file_title, github_url, section_content)
    """
    sections = []
    pattern = re.compile(r'(?m)^# Presentation\s*\n(.*?)(?=^# |\Z)', re.DOTALL)
    for file_path in file_paths:
        file_title = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        frontmatter = parse_frontmatter(content)
        github_url = frontmatter.get('github', None)
        for match in pattern.finditer(content):
            section_content = match.group(1).strip()
            if description_only:
                section_content = extract_description_only(section_content)
            section_content = shift_headings(section_content, shift_by=2)
            sections.append((file_title, github_url, section_content))
    return sections

parser = argparse.ArgumentParser(description='Generate README from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
parser.add_argument('--description-only', action='store_true', default=False, help='Only extract the Description section rather than the full Presentation block')
args = parser.parse_args()

destination_path = args.destination
source_path = args.source
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Template.md')

# generate README content
presentable_files = search_for_presentable_files(source_path)
presentation_sections = extract_presentation_sections(presentable_files, description_only=args.description_only)

# write README
os.makedirs(destination_path, exist_ok=True)
readme_path = os.path.join(destination_path, 'README.md')

with open(template_path, 'r', encoding='utf-8') as template_file:
    template_content = template_file.read()

with open(readme_path, 'w', encoding='utf-8') as readme_file:
    readme_file.write(template_content + "\n\n")
    for file_title, github_url, section in presentation_sections:
        if github_url:
            readme_file.write(f"### [{file_title}]({github_url})\n\n")
        else:
            readme_file.write(f"### {file_title}\n\n")
        readme_file.write(section + "\n\n---\n\n")

print(f'Generated README at {readme_path} from {len(presentation_sections)} sections.')