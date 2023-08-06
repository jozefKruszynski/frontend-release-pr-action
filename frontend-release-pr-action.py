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
    MAIN = "main"
    ORGANIZATION = "music-assistant"
    SERVER_REPO = "server"
    FRONTEND_DEPENDENCY = "music-assistant-frontend"

    server_repo = github.get_repo(f"{ORGANIZATION}/{SERVER_REPO}")

    pyproject_file = server_repo.get_contents("pyproject.toml", ref=MAIN)

    requirements_file = server_repo.get_contents("requirements_all.txt", ref=MAIN)

    existing_pyproject_contents = toml.loads(
        pyproject_file.decoded_content.decode("utf-8")
    )
    existing_requirements_contents = requirements_file.decoded_content.decode("utf-8")

    existing_pyproject_contents["project"]["optional-dependencies"]["server"] = [
        f"{FRONTEND_DEPENDENCY}=={new_version_tag}"
        if "music-assistant-frontend" in x
        else x
        for x in existing_pyproject_contents["project"]["optional-dependencies"][
            "server"
        ]
    ]

    updated_pyproject = toml.dumps(existing_pyproject_contents)

    updated_lines = []
    for line in existing_requirements_contents.strip().split("\n"):
        package = line.strip().split("==")[0].lower()
        if package == FRONTEND_DEPENDENCY.lower():
            updated_lines.append(f"{FRONTEND_DEPENDENCY}=={new_version_tag}")
        else:
            updated_lines.append(line)

    updated_requirements_contents = "\n".join(updated_lines)

    print(updated_requirements_contents)

    # Create new branch and PR

    ref = server_repo.get_git_ref("heads/main")
    sha = ref.object.sha
    new_branch_name = f"frontend-{new_version_tag}"
    new_branch = server_repo.create_git_ref(
        ref=f"refs/heads/{new_branch_name}", sha=sha
    )

    server_repo.update_file(
        path="pyproject.toml",
        message=f"Update pyproject.toml for {new_version_tag}",
        content=updated_pyproject,
        sha=pyproject_file.sha,
        branch=new_branch_name,
    )
    server_repo.update_file(
        path="requirements_all.txt",
        message=f"Update requirements_all.txt for {new_version_tag}",
        content=updated_requirements_contents,
        sha=requirements_file.sha,
        branch=new_branch_name,
    )

    label = github.label.Label(name="frontend-release", color="17A589")

    server_repo.create_pull(
        title=new_branch_name,
        body=f"Update files for {new_version_tag}",
        head=new_branch_name,
        base="main",
        labels=[label],
    )
