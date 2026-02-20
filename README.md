# Automated-portfolio-deployment
Public workflows and accompanying scripts which i use to push my notes to my portfolios when I create projects, workflows are called from a git repo contianing an obsidian vault.

To use this it requires an obsidian workspace set up with git and a personal access key in the secrets of the repo the vaults are backed up to, as well as following the abstract documents structure. Moreover, the repo inputs needs to be specified to allow for flexible file structure. 

secrets/inputs:
- TOKEN: account token for workflow to push against repo.
- source_path: internal file structure for where the notes are being kept in the repo.
- destination_repo: where the workflow pushes the results.

the script works by pulling markdown documents tagged as presentable in the frontmatter, and then puts the presentation sections of the md files into a README template
examples of this script working present on my profile README and portfolio page:
- https://github.com/BenHorleyOwen
- https://github.com/BenHorleyOwen/BenHorleyOwen.github.io
