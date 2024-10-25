import os

import toml
from github import Auth, Github, Label

github = Github(auth=Auth.Token(os.environ["GITHUB_TOKEN"]))

new_version_tag = "566"
BRANCH = "dev"
ORGANIZATION = "music-assistant"
SERVER_REPO = "server"
FRONTEND_DEPENDENCY = "music-assistant-frontend"
LABEL_NAME = "frontend-release"
MAINTENANCE_LABEL_NAME = "maintenance"

server_repo = github.get_repo(f"{ORGANIZATION}/{SERVER_REPO}")

# Get pyproject.toml extract current version and update with new version
pyproject_file = server_repo.get_contents("pyproject.toml", ref=BRANCH)
existing_pyproject_contents = toml.loads(pyproject_file.decoded_content.decode("utf-8"))
server_dependencies = existing_pyproject_contents["project"]["optional-dependencies"][
    "server"
]
music_assistant_frontend_dependecy = ""
for x in server_dependencies:
    if x.startswith(FRONTEND_DEPENDENCY):
        music_assistant_frontend_dependecy = x

music_assistant_frontend_dependecy_new = music_assistant_frontend_dependecy.replace(
    music_assistant_frontend_dependecy.split("==")[1], new_version_tag
)
file = pyproject_file.decoded_content.decode("utf-8")
new_file = file.replace(
    music_assistant_frontend_dependecy, music_assistant_frontend_dependecy_new
)

# Get requirements_all.txt and update with new version
requirements_file = server_repo.get_contents("requirements_all.txt", ref=BRANCH)
existing_requirements_file = requirements_file.decoded_content.decode("utf-8")
requirements_new = existing_requirements_file.replace(
    music_assistant_frontend_dependecy, music_assistant_frontend_dependecy_new
)

labels = (
    server_repo.get_label(LABEL_NAME),
    server_repo.get_label(MAINTENANCE_LABEL_NAME),
)

assert all(isinstance(element, (Label.Label, str)) for element in labels)
