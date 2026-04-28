import os
import argparse
import re
import readmescript

'''
Script to generate portfolio website json information from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts skills, links and presentation sections to compile into a portfolio.json
'''
# old extractor worked by returning strings, file objects now mutate internally and the extractor has to reflect this. 
class portfolio_extractor(readmescript.extractor):
    """
    Class to extract portfolio information from presentable files, extends original script extractor class to include portfolio specific extraction logic.
    """
    def __init__(self):
        super().__init__()

    def extract(self, file_obj):
        """
        Extract presentable content from a file.
        :param file_path: path to the file to extract presentable content from
        """
        self.extractors = { #easy way to extend future logic
            'description': self.extract_description, #should reference original description extractor
            'index': self.extract_index, # only index is modified and used here
            #'implementation': self.extract_implementation
            #'subproject': self.extract_links
        }

        for key, extractor in self.extractors.items():
            if file_obj.extractions.get(key):
                print(f"Extracting {key} from {file_obj.file_path}")
                extractor(file_obj)

    def extract_description(self, file_obj):
        super().extract_description(file_obj)
        file_obj.description = (file_obj.section_content or "").strip()

    

    def extract_index(self, file_obj): #modified index extract to change how sub projects are added to the index file object directly.
        file_obj.subs = []
        subprojects = []
        pattern = re.compile(r'(?m)^## Index\s*\n(.*?)(?=^## |\Z)', re.DOTALL)
        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')

        for section_match in pattern.finditer(file_obj.content):
            section_body = section_match.group(1)
            for link_match in link_pattern.finditer(section_body):
                subpath = os.path.join(source_path, f"{link_match.group(1)}.md")
                try:
                    tempobj = readmescript.file_object(subpath)
                    tempobj.extractions['description'] = True # for this script, all files extract descriptions the same,rather than relying on a subproejct extraction specifically.
                    self.extract(tempobj)
                    file_obj.subs.append(tempobj)
                except ValueError as e:
                    print(f"Skipping linked file {subpath}: {e}")


    def extract_implementation(self, file_obj):
        pass


def project_yml_write(file_obj, yml_file):
    """
    Write portfolio information from a file object to a yml file.
    Written as function to allow for subproject recursive calling.
    """
    project_name = os.path.splitext(os.path.basename(file_obj.file_path))[0]
    print(f"Writing project {project_name} to yml")
    # build type list from extractions
    types = [key for key, val in file_obj.extractions.items() if val]

    yml_file.write("\n")
    yml_file.write(f"  - name: {project_name}\n")
    yml_file.write(f"    type: [{', '.join(types)}]\n") #changed from a single value, might break website
    yml_file.write(f"    priority: {file_obj.priority}\n")
    yml_file.write(f"    repo: {file_obj.github_url or 'null'}\n")
    yml_file.write(f"    skills: [{file_obj.skills or ''}]\n")
    yml_file.write(f"    description: |\n")
    for line in file_obj.description.splitlines():
        yml_file.write(f"      {line}\n")
    if hasattr(file_obj, 'subs'):
        yml_file.write(f"    subprojects: [{', '.join(sub.file_title for sub in file_obj.subs)}]\n")
        for sub in file_obj.subs:
            project_yml_write(sub, yml_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate projects.yml from presentable files.')
    parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
    parser.add_argument('--source', type=str, required=True, help='Path to source directory')
    args = parser.parse_args()

    destination_path = args.destination
    source_path = args.source

    presentable_files = readmescript.search_for_presentable_files(source_path)
    extractor_instance = portfolio_extractor()
    os.makedirs(destination_path, exist_ok=True)
    yml_path = os.path.join(destination_path, 'projects.yml')

    with open(yml_path, 'w', encoding='utf-8') as yml_file:
        yml_file.write("projects:\n")
        for file in presentable_files:
            extractor_instance.extract(file) #mutates file objects with extracted content
            project_yml_write(file, yml_file)
    print(f'Generated projects.yml at {yml_path} from {len(presentable_files)} sections.')