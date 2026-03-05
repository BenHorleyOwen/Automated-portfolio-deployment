import os
import re
import argparse
from unittest import case

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
                    file_obj = file_object(file_path)
                    file_obj.check_type()
                    presentable_files.append(file_obj)
    return presentable_files

def check_for_index(presentable_files):
    """
    Search for files marked with 'Index' in frontmatter.
    :param presentable_files: list of presentable file objects
    :return: list of file objects that are marked as index
    """
    index_files = []
    for file_obj in presentable_files:
        try:
            with open(file_obj.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(r'^---.*?\bIndex\b.*?---', content, re.IGNORECASE | re.DOTALL):
            index_files.append(file_obj) # need to pop duplicate from presentables
            #create tuple which contains md links present in index section
    return index_files

def walk_index_sections(file_obj):
    """
    Walk through index sections and extract md links.
    md links are followed and their content is extracted.
    :param index_files: list of file objects that are marked as index
    :return: list of file objects that are linked in index sections with their extracted content
    """
    # index_sections = []
    # pattern = re.compile(r'(?m)^# Index\s*\n(.*?)(?=^# |\Z)', re.DOTALL)
    # for file_obj in index_files:
    #     file_title = file_obj.file_title
    #     github_url = file_obj.github_url
    #     with open(file_obj.file_path, 'r', encoding='utf-8') as file:
    #         content = file.read()
    #     frontmatter = parse_frontmatter(content)
    #     github_url = frontmatter.get('github', None)
    #     for match in pattern.finditer(content):
    #         section_content = match.group(1).strip()
    #         index_sections.append((file_title, github_url, section_content))
    # return index_sections

def shift_headings(content, shift_by):
    """Shift all markdown headings down by shift_by levels."""
    def replacer(match):
        new_level = min(len(match.group(1)) + shift_by, 6)
        return '#' * new_level + match.group(2)
    return re.sub(r'^(#{1,6})([\s#])', replacer, content, flags=re.MULTILINE)


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
                    file_obj.extend_section_content(f"### [{file_obj.file_title}]({file_obj.github_url})\n\n")
                else:
                    file_obj.extend_section_content(f"### {file_obj.file_title}\n\n")
                file_obj.extend_section_content(self.extract_description(file_obj.content))
                pass

            case 'index': 
                # default extraction + index section walk
                if file_obj.github_url:
                    file_obj.extend_section_content(f"### [{file_obj.file_title}]({file_obj.github_url})\n\n")
                else:
                    file_obj.extend_section_content(f"### {file_obj.file_title}\n\n")
                file_obj.extend_section_content(self.extract_description(file_obj.content))
                # walk index sections and recursively call this fucntion to extract presentable content from linked files
                for sub in walk_index_sections(file_obj): # bulletpoints
                    self.extract_presentable(sub)
                    file.obj.extend_section_content(sub.section_content)
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
        ## check type
        """
        Check the type of the file based on its frontmatter.
        This can be used to determine if the file is an index or a presentation.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.content = file.read()
        except (UnicodeDecodeError, OSError):
            return
        frontmatter = parse_frontmatter(self.content)
        if 'Index' in frontmatter:
            self.type = 'index'
        elif 'subproject' in frontmatter:
            self.type = 'subproject' #this is for indexxed pages
        else:
            self.type = 'presentation'
        ## update github url if it exists in frontmatter
        self.github_url = frontmatter.get('github', None)

    def extend_section_content(self, content):
        if self.section_content is None:
            self.section_content = content
        else:
            self.section_content += content

# def extract_presentation_sections(file_paths, description_only=False): ## I want to modify this to just be a basic section extractor that can be used for both index and presentation sections, and then call it twice in the main function with different section names. I also want to modify it to return a list of tuples (file_title, github_url, section_content) instead of just section content, so that I can use the file title and github url in the README generation.
#     """
#     Extract presentation sections from files.
#     :param file_paths: list of file paths to extract presentation sections from
#     :param description_only: if True, only extract content under ## Description
#     :return: list of tuples (file_title, github_url, section_content)
#     """
#     sections = []
#     pattern = re.compile(r'(?m)^# Presentation\s*\n(.*?)(?=^# |\Z)', re.DOTALL)
#     for file_path in file_paths:
#         file_title = os.path.splitext(os.path.basename(file_path))[0]
#         with open(file_path, 'r', encoding='utf-8') as file:
#             content = file.read()
#         frontmatter = parse_frontmatter(content)
#         github_url = frontmatter.get('github', None)
#         for match in pattern.finditer(content):
#             section_content = match.group(1).strip()
#             if description_only:
#                 section_content = extract_description_only(section_content)
#             section_content = shift_headings(section_content, shift_by=2)
#             sections.append((file_title, github_url, section_content))
#     return sections

# Command-line interface
parser = argparse.ArgumentParser(description='Generate README from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
#parser.add_argument('--description-only', action='store_true', default=False, help='Only extract the Description section rather than the full Presentation block')
args = parser.parse_args()

#desc_only = args.description_only
destination_path = args.destination
source_path = args.source
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Template.md')


# generate README content

presentable_files = search_for_presentable_files(source_path)

##when presentation sections is modified I want it to call it from a loop parsing presentable files
presentation_sections = [] # a list of tuples (file_title, github_url, section_content) that will be used to generate the README content. 
extractor_instance = extractor() 

    # if file not in indexes: #this will need to be changed as i add different versions as a switch case.
    #     presentation_sections.append(extractor_instance.extract_presentable(file))

    #     ## presentation_sections.extend(extract_presentation_sections([file], description_only=args.description_only))
    # else:
    #     ## create list from walk_index and iteratate extract presentable from it
    #     index_sections = walk_index_sections([file])
    #     for entry in index_sections:
    #         presentation_sections.append(extractor_instance.extract_presentable(entry))

# write README
os.makedirs(destination_path, exist_ok=True)
readme_path = os.path.join(destination_path, 'README.md')

with open(template_path, 'r', encoding='utf-8') as template_file:
    template_content = template_file.read()

with open(readme_path, 'w', encoding='utf-8') as readme_file:
    readme_file.write(template_content + "\n\n")
    # for file in presentable files, run their extraction and add to file
    for file in presentable_files:
        extractor_instance.extract_presentable(file)
        readme_file.write(f"### {file.section_content}\n\n")

    # for file_title, github_url, section in presentation_sections:
    #     if github_url:
    #         readme_file.write(f"### [{file_title}]({github_url})\n\n")
    #     else:
    #         readme_file.write(f"### {file_title}\n\n")
    #     readme_file.write(section + "\n\n---\n\n")

print(f'Generated README at {readme_path} from {len(presentation_sections)} sections.')