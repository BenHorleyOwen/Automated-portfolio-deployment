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
                    try:
                        presentable_files.append(file_object(file_path))
                    except ValueError as e:
                        print(f"Skipping {file_path}: {e}")
    return presentable_files


class extractor:
    """
    Class to extract presentable content from files.
    This class can be extended in the future to include more complex extraction logic.
    Current implementation for presentable default and index
    """
    def __init__(self):
        pass
    
    def extract_description(self, file_obj): 
        """Extract only the content under the ## Description heading."""
        match = re.search(
            r'(?im)^#{1,6}\s*description\s*$\n(.*?)(?=^#{1,6}\s|\Z)',
            file_obj.content,
            re.DOTALL
        )
        if match: #upon finding a match the file object information is updated within the method.
        #     return match.group(1).strip()
        # return file_obj.content.strip()  
            if file_obj.github_url:
                file_obj.extend_section_content(f"[{file_obj.file_title}]({file_obj.github_url})\n\n")
            else:
                file_obj.extend_section_content(f"{file_obj.file_title}\n\n")
            file_obj.extend_section_content(match.group(1).strip())
        file_obj.extend_section_content("\n\n")

    def extract_implementation(self, file_obj): #only used for portfolioscript. 
        """Extract only the content under the ## Implementation heading."""
        match = re.search(
            r'(?im)^#{1,6}\s*implementation\s*$\n(.*?)(?=^#{1,6}\s|\Z)',
            file_obj.content,
            re.DOTALL
        )
        if match:
            return match.group(1).strip()
        return file_obj.content.strip()

    def extract_index(self, file_obj): #replace walk_index_sections
        '''
        Walk through index sections and extract md links.
        md links are followed and their content is extracted.
        :param file_obj: file object to walk index sections from
        :param repo_path: path to the repository to resolve linked files
        :return: list of file objects that are linked in index sections with their extracted content
        '''
        subprojects = []
        pattern = re.compile(r'(?m)^## Index\s*\n(.*?)(?=^## |\Z)', re.DOTALL)
        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')

        for section_match in pattern.finditer(file_obj.content):
            section_body = section_match.group(1)
            for link_match in link_pattern.finditer(section_body):
                    subpath = os.path.join(source_path, f"{link_match.group(1)}.md")
                    try:
                        tempobj = file_object(subpath) # force subproject extractions, the tag is redundant now but we can pretend :D
                        tempobj.extractions['subproject'] = True
                        tempobj.extractions['description'] = False
                        subprojects.append(tempobj)
                    except ValueError as e:
                        print(f"Skipping linked file {subpath}: {e}")
                        
        for subproject in subprojects:
            self.extract_subproject(subproject)
            file_obj.extend_section_content(subproject.section_content)
    
    def extract_subproject(self, file_obj): 
        """extract subproject formatted content for index extraction."""
        match = re.search(
                r'(?im)^#{1,6}\s*description\s*$\n(.*?)(?=^#{1,6}\s|\Z)',
                file_obj.content,
                re.DOTALL
            )
        if file_obj.github_url:
            file_obj.extend_section_content(f"- [{file_obj.file_title}]({file_obj.github_url}): {match.group(1).strip()}\n\n")
        else:
            file_obj.extend_section_content(f"- {file_obj.file_title}: {match.group(1).strip()}\n\n")

    def extract_links(self, file_obj):
        # parses wiki links and transforms them into github links from the path of the wiki link file object.
        """Extract all wiki links from the content."""
        return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', file_obj.content)

    def extract_presentable(self, file_obj):
        """
        Extract presentable content from a file.
        :param file_path: path to the file to extract presentable content from
        """
        #fileobj.extractions dict determines which extractions to perform and then this method extends the file object's section_content with the extracted content.
        extractors = { #easy way to extend future logic
            'description': self.extract_description, #description comes first
            'index': self.extract_index,
            'implementation': self.extract_implementation
            #'subproject': self.extract_links, index calls this method, not a standalone extraction
        }
        for key, extractor in extractors.items():
            if file_obj.extractions.get(key):
                extractor(file_obj)

class file_object:
    """
    Class to represent a presentable file with its metadata and content.
    This can be used to store the file path, title, github url, and extracted section content.
    """
    def __init__(self, file_path):
        """
        Check the type of the file based on its frontmatter.
        This can be used to determine if the file is an index or a presentation.
        """

        self.file_path = file_path
        self.file_title = os.path.splitext(os.path.basename(file_path))[0]
        self.section_content = None

        #booleans based on which exractions are required
        self.extractions = {
            'description': False,
            'index': False,
            'implementation': False,
            'subproject': False
        }

        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.content = file.read()
        except (UnicodeDecodeError, OSError) as e:
            raise ValueError(f"Could not read file {self.file_path}: {e}") from e
        if re.search(r'^---.*?\bunpresentable\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            raise ValueError(f"File {self.file_path} is marked as unpresentable, skipping.")
        
        if re.search(r'^---.*?\bindex\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.extractions['index'] = True
        if re.search(r'^---.*?\bpresentable\b.*?---', self.content, re.IGNORECASE | re.DOTALL): #presentable is used for default extraction, which always wants description.
            self.extractions['description'] = True
        if re.search(r'^---.*?\bsubproject\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.extractions['subproject'] = True
        if re.search(r'^---.*?\bimplementation\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.extractions['implementation'] = True

        ## assign priority based on type
        if re.search(r'^---.*?\blowprio\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.priority = 3
        elif re.search(r'^---.*?\bhighprio\b.*?---', self.content, re.IGNORECASE | re.DOTALL):
            self.priority = 1
        else:
            self.priority = 2

        ## update github url if it exists in frontmatter
        frontmatter = parse_frontmatter(self.content)
        self.github_url = frontmatter.get('github', None)
        self.skills = frontmatter.get('skills', None) # can be used in the future for skill extraction in portfolio script
        print(f"Created file object for {self.file_path} with extractions {self.extractions} and priority {self.priority}.")

    def extend_section_content(self, content):
        if self.section_content is None:
            self.section_content = content
        else:
            self.section_content += content

def checkforlinks(content): # exclude files without any hyperlinks from being included in README
    """Check if the content contains any links"""
    return bool(re.search(r'\[.*?\]\(.*?\)', content))

if __name__ == '__main__': # main function to generate README.md from presentable files in a repository
    # Command-line interface
    parser = argparse.ArgumentParser(description='Generate README from presentable files.')
    parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
    parser.add_argument('--source', type=str, required=True, help='Path to source directory')
    args = parser.parse_args()

    destination_path = args.destination
    source_path = args.source
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Template.md')


    # write README
    presentable_files = search_for_presentable_files(source_path) # generates the file objects
    presentable_files = sorted(presentable_files, key=lambda x: x.priority) # sorts the created objects
    extractor_instance = extractor()
    os.makedirs(destination_path, exist_ok=True)
    readme_path = os.path.join(destination_path, 'README.md')

    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_content = template_file.read()

    with open(readme_path, 'w', encoding='utf-8') as readme_file: # generate README content
        readme_file.write(template_content + "\n\n")
        for file in presentable_files:
            extractor_instance.extract_presentable(file)
            if file.section_content and checkforlinks(file.section_content):
                readme_file.write(f"### {file.section_content}\n\n")
                readme_file.write("\n\n---\n\n")
    print(f'Generated README at {readme_path} from {len(presentable_files)} sections.')