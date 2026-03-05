import os
import re
import argparse

"""Script to generate README.md from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts
presentation sections to compile into a README.md using a template.
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
    :return: list of file objects that are marked as presentable
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
                    presentable_files.append(file_object(file_path))
    return presentable_files


def walk_index_sections(file_obj, repo_path):
    """
    Walk through index sections and extract md links.
    md links are followed and their content is extracted.
    :param file_obj: file object to walk index sections from
    :param repo_path: path to the repository to resolve linked files
    :return: list of file objects that are linked in index sections with their extracted content
    """
    subprojects = []
    pattern = re.compile(r'(?m)^## Index\s*\n(.*?)(?=^# |\Z)', re.DOTALL)
    link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')

    for section_match in pattern.finditer(file_obj.content):
        section_body = section_match.group(1)
        for link_match in link_pattern.finditer(section_body):
            subpath = os.path.join(repo_path, f"{link_match.group(1)}.md")
            subprojects.append(file_object(subpath))
    return subprojects


class extractor:
    """
    Class to extract presentable content from files.
    This class can be extended in the future to include more complex extraction logic.
    Current implementation for presentable default and index
    """
    def __init__(self):
        pass
    
    def extract_description(self, content):
        """Extract only the content under the ## Description heading."""
        match = re.search(
            r'(?im)^#{1,6}\s*description\s*$\n(.*?)(?=^#{1,6}\s|\Z)',
            content,
            re.DOTALL
        )
        if match:
            return match.group(1).strip()
        return content.strip()

    def extract_presentable(self, file_obj):
        """
        Extract presentable content from a file.
        :param file_path: path to the file to extract presentable content from
        """
        match file_obj.type:
            case 'presentation':
                # default extraction
                if file_obj.github_url:
                    file_obj.extend_section_content(f"[{file_obj.file_title}]({file_obj.github_url})\n\n")
                else:
                    file_obj.extend_section_content(f"{file_obj.file_title}\n\n")
                file_obj.extend_section_content(self.extract_description(file_obj.content))
                pass

            case 'index': 
                # default extraction + index section walk
                if file_obj.github_url:
                    file_obj.extend_section_content(f"[{file_obj.file_title}]({file_obj.github_url})\n\n")
                else:
                    file_obj.extend_section_content(f"{file_obj.file_title}\n\n")
                file_obj.extend_section_content(f"{self.extract_description(file_obj.content)}\n\n")
                # walk index sections and recursively call this fucntion to extract presentable content from linked files

                for sub in walk_index_sections(file_obj, source_path): # bulletpoints
                    self.extract_presentable(sub)
                    file_obj.extend_section_content(sub.section_content)
                pass

            case 'subproject': ## bulletpoint index references
                file_obj.extend_section_content(f"- [{file_obj.file_title}]({file_obj.github_url}): {self.extract_description(file_obj.content)}\n\n")
                pass

class file_object:
    """
    Class to represent a presentable file with its metadata and content.
    This can be used to store the file path, title, github url, and extracted section content.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_title = os.path.splitext(os.path.basename(file_path))[0]
        self.section_content = None
        """
        Check the type of the file based on its frontmatter.
        This can be used to determine if the file is an index or a presentation.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.content = file.read()
        except (UnicodeDecodeError, OSError):
            return
        
        if re.search(r'^---.*?\bindex\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.type = 'index'
        elif re.search(r'^---.*?\bsubproject\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.type = 'subproject'
        else:
            self.type = 'presentation'
        ## update github url if it exists in frontmatter
        frontmatter = parse_frontmatter(self.content)
        self.github_url = frontmatter.get('github', None)
        print(f"Created file object for {self.file_path} with type {self.type}")

    def extend_section_content(self, content):
        if self.section_content is None:
            self.section_content = content
        else:
            self.section_content += content

# Command-line interface
parser = argparse.ArgumentParser(description='Generate README from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
args = parser.parse_args()

destination_path = args.destination
source_path = args.source
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Template.md')


# write README
presentable_files = search_for_presentable_files(source_path) 
extractor_instance = extractor() 
os.makedirs(destination_path, exist_ok=True)
readme_path = os.path.join(destination_path, 'README.md')

with open(template_path, 'r', encoding='utf-8') as template_file:
    template_content = template_file.read()

with open(readme_path, 'w', encoding='utf-8') as readme_file: # generate README content
    readme_file.write(template_content + "\n\n")
    for file in presentable_files:
        extractor_instance.extract_presentable(file)
        readme_file.write(f"### {file.section_content}\n\n")

print(f'Generated README at {readme_path} from {len(presentable_files)} sections.')

'''current state
- script is back to working as originally intended, indexes are not parsed yet though.
- check regex matches correctly
- need to modify pipeline now that description only call is gone

'''