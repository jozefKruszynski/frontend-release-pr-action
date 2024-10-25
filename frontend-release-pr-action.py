import argparse

import toml
from github import Auth, Github

parser = argparse.ArgumentParser()

parser.add_argument(
    "--new_release_version",
    type=str,
    help="Whether or not this is a pre-release.",
    required=True,
)
parser.add_argument(
    "--github_token",
    type=str,
    help="Github API Access token",
    required=True,
)


if __name__ == "__main__":
    args = parser.parse_args()

    github = Github(auth=Auth.Token(args.github_token))

    new_version_tag = args.new_release_version
    BRANCH = "dev"
    ORGANIZATION = "music-assistant"
    SERVER_REPO = "server"
    FRONTEND_DEPENDENCY = "music-assistant-frontend"
    LABEL_NAME = "frontend-release"
    MAINTENANCE_LABEL_NAME = "maintenance"

    server_repo = github.get_repo(f"{ORGANIZATION}/{SERVER_REPO}")

    # Get pyproject.toml extract current version and update with new version
    pyproject_file = server_repo.get_contents("pyproject.toml", ref=BRANCH)
    existing_pyproject_contents = toml.loads(
        pyproject_file.decoded_content.decode("utf-8")
    )
    server_dependencies = existing_pyproject_contents["project"][
        "optional-dependencies"
    ]["server"]
    music_assistant_frontend_dependecy = ""
    for x in server_dependencies:
        if x.startswith(FRONTEND_DEPENDENCY):
            music_assistant_frontend_dependecy = x

    music_assistant_frontend_dependecy_new = music_assistant_frontend_dependecy.replace(
        music_assistant_frontend_dependecy.split("==")[1], new_version_tag
    )
    existing_pyproject_file = pyproject_file.decoded_content.decode("utf-8")
    pyproject_new = existing_pyproject_file.replace(
        music_assistant_frontend_dependecy, music_assistant_frontend_dependecy_new
    )

    # Get requirements_all.txt and update with new version
    requirements_file = server_repo.get_contents("requirements_all.txt", ref=BRANCH)
    existing_requirements_file = requirements_file.decoded_content.decode("utf-8")
    requirements_new = existing_requirements_file.replace(
        music_assistant_frontend_dependecy, music_assistant_frontend_dependecy_new
    )

    # Create new branch and PR
    ref = server_repo.get_git_ref(f"heads/{BRANCH}")
    sha = ref.object.sha
    new_branch_name = f"frontend-{new_version_tag}"
    new_branch = server_repo.create_git_ref(
        ref=f"refs/heads/{new_branch_name}", sha=sha
    )

    server_repo.update_file(
        path="pyproject.toml",
        message=f"Update pyproject.toml for {new_version_tag}",
        content=pyproject_new,
        sha=pyproject_file.sha,
        branch=new_branch_name,
    )
    server_repo.update_file(
        path="requirements_all.txt",
        message=f"Update requirements_all.txt for {new_version_tag}",
        content=requirements_new,
        sha=requirements_file.sha,
        branch=new_branch_name,
    )

    pull_request = server_repo.create_pull(
        title=new_branch_name,
        body=f"Bump frontend to {new_version_tag}",
        head=new_branch_name,
        base=BRANCH,
    )

    pull_request.add_to_labels(
        server_repo.get_label(LABEL_NAME), server_repo.get_label(MAINTENANCE_LABEL_NAME)
    )
