import os
import argparse
import readmescript

'''
Script to generate portfolio website json information from presentable files in a repository.
Looks for files marked with 'presentable' in frontmatter and extracts skills, links and presentation sections to compile into a portfolio.json
'''
# readmescript is imported to reuse the file_object class and the search_for_presentable_files function, as they are relevant for this script as well. The extractor class is defined here to handle the specific extraction logic for the portfolio information, which can be extended in the future as needed.

class portfolio_extractor(readmescript.extractor):
    """
    Class to extract portfolio information from presentable files, extends original script extractor class to include portfolio specific extraction logic.
    """
    def extract_portfolio_info(self, file_obj):# I need to figure out how to handle subprojects.
        """
        Extract portfolio information from a file object.
        This includes skills, github url and presentation sections.
        :param file_obj: file object to extract information from
        """
        # I might neeed to make it so that md links are stripped from descriptions
        if file_obj.type == 'index':
            file_obj.subs = []
            subprojects = readmescript.walk_index_sections(file_obj, os.path.dirname(file_obj.file_path))
            for subproject in subprojects:
                self.extract_portfolio_info(subproject)
                file_obj.subs.append(subproject)
        # make the function update the object's content so index subprojects can recursively call this method like in original script
        file_obj.description = self.extract_description(file_obj.content)
    
def project_yml_write(file_obj, yml_file):
    """
    Write portfolio information from a file object to a yml file.
    written as function to allow for subproject recursive callling.
    """
    project_name = os.path.splitext(os.path.basename(file_obj.file_path))[0]
    yml_file.write(f"  - name: {project_name}\n")
    yml_file.write(f"    type: [{file_obj.type}]\n")
    if file_obj.github_url:
        yml_file.write(f"    repo: {file_obj.github_url}\n")
    else:       yml_file.write(f"    repo: null\n")
    if file_obj.skills:
        yml_file.write(f"    skills: [{file_obj.skills.lower()}]\n")
    else:        yml_file.write(f"    skills: []\n")
    yml_file.write(f"    description: |\n")
    for line in file_obj.description.splitlines():
        yml_file.write(f"      {line}\n")
    if hasattr(file_obj, 'subs'):
        yml_file.write("\n")
        yml_file.write(f"    subprojects: [{', '.join(sub.file_title for sub in file_obj.subs)}]\n")
        for sub in file_obj.subs:
            project_yml_write(sub, yml_file)
    yml_file.write("\n") #the last subproject in the list gets an extra new line, i do not care in the slightest
    


# Command-line interface
parser = argparse.ArgumentParser(description='Generate projects.yml from presentable files.')
parser.add_argument('--destination', type=str, required=True, help='Path to output directory')
parser.add_argument('--source', type=str, required=True, help='Path to source directory')
args = parser.parse_args()

destination_path = args.destination
source_path = args.source
presentable_files = readmescript.search_for_presentable_files(source_path) # generates the file objects
extractor_instance = portfolio_extractor()
os.makedirs(destination_path, exist_ok=True)
yml_path = os.path.join(destination_path, 'projects.yml')

# write projects.yml
with open(yml_path, 'w', encoding='utf-8') as yml_file:
    yml_file.write("projects:\n")
    for file in presentable_files:
        extractor_instance.extract_portfolio_info(file)
        project_yml_write(file, yml_file)
print(f'Generated projects.yml at {yml_path} from {len(presentable_files)} sections.')