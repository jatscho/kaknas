import re
from dulwich.repo import Repo, Commit
from dulwich.object_store import tree_lookup_path
from flask import current_app as app

def get_file_contents(tree, path):
    """Gets contents of a file.

    Args:
        tree: A Tree instance containing the file.
        path: An encoded path to the file

    Returns:
        A string containing all contents of the file
    """
    app_config = app.config['GIT_REPOS_FOLDER']
    rep = Repo(app_config + '/terraform')
    (mode,sha) = tree_lookup_path(rep.get_object, tree, path)
    return rep[sha].data.decode()

def find_modules_in_file(file, lastfcommit):
    """Maps all modules in a file.

    Args:
        file: An encoded path to file
        lastfcommit: The latest Commit of the repo

    Returns:
        A nested map containing the key value pairs of modules found in the file.
        For instance, {'skids': {'cybertron/skids': '69ab0e5'}} means that the
        file contains one module with the name cybertron/skids pointing
        to the git ref number 69ab0e5
    """
    file_contents = get_file_contents(lastfcommit.tree, file)
    module_map = {}
    module_regex = re.compile("^module \"(.*)\" {$")
    last_module = ''
    # Loop through every line in the file since it could contain multiple modules
    for line in iter(file_contents.splitlines()):
        module_regex_groups = module_regex.search(line)
        if module_regex_groups:
            last_module = module_regex_groups.group(1)
        regex_match = re.compile('git@github\.com:(.*)\.git\?ref=(.*)//(.*)"')
        groups = regex_match.search(line)
        if groups:
            module_map[last_module] = {groups.group(3): groups.group(2)}
    return module_map

def get_folder_path(file):
    """Gets path of file after project name.

    Args:
        file: A decoded path to file

    Returns:
        A string containing the desired file path.
        For instance, the input 'cognitedata-greenfield/tier2/api/api.tf'
        returns '/tier2/api'
    """
    start_index = file.find('/')
    last_index = file.rfind('/')
    return file[start_index+1:last_index]

def set_state_map(state_map, all_files, lastfcommit):
    """Creates a map of the state of all projects' modules and their paths.

    Args:
        state_map: An empty map
        all_files: A tree of all files in the repo
        lastfcommit: The latest Commit of the repo

    Returns:
        None, but sets state_map to be something like this:
        "{
            'cognitedata-development': {
                '3d/3d-backend': {
                    '3d': {
                        '3d/3d-backend': 'd3af6d7'
                        }
                },
                'cybertron/jetfire': {
                    'jetfire': {
                        'cybertron/jetfire': '673edc0'
                    }
                },
                'cybertron/skids': {
                    'skids': {
                        'cybertron/skids': '69ab0e5'
                    }
                },
            },
            'cognitedata-equinor': {
                'gcp_project': {
                    'gcp_project': {
                        'cdp/gcp_project': 'ef882b3'
                        }
                    },
                'project_vars': {},
                'tier0/iam': {
                    'iam': {
                        'cdp/tier0/iam': '9dd40c3'
                    }
                },
            }
            'cognitedata-europe-west1-1': {
                'gcp_project': {
                    'gcp_project': {
                        'cdp/gcp_project': 'fec550d'
                    }
                },
            },
            'cognitedata-greenfield': {
                'gcp_project': {
                    'gcp_project': {
                        'cdp/gcp_project': 'fec550d'
                    }
                },
                'tier0/iam': {
                    'iam': {
                        'cdp/tier0/iam': '9dd40c3'
                    }
                }
            }
        }
    """
    for file in all_files:
        file_decoded = file.decode()
        if file.endswith(b'.tf'):
            file_split = file_decoded.split('/')
            project = file_split[0]
            if project not in state_map:
                state_map[project] = {}
            folder_path = get_folder_path(file_decoded)
            if folder_path not in state_map[project]:
                state_map[project][folder_path] = {}
            modules_map = find_modules_in_file(file, lastfcommit)
            state_map[project][folder_path].update(modules_map)

def set_module_state_map(module_state_map, all_files, lastfcommit):
    """Creates a map of the state of all modules, their projects and paths.

    Args:
        module_state_map: An empty map
        all_files: A tree of all files in the repo
        lastfcommit: The latest Commit of the repo

    Returns:
        None, but sets state_map to be something like this:
        { 0:
            {'module_name': '3d',
             'cognitedata-development':
                {'path_to_module': '3d/3d-backend',
                 'module_source': '3d/3d-backend',
                 'git_ref': 'd3af6d7'
                },
             'module_source': '3d/3d-backend'
             },
          1:
            {'module_name': 'ml_api',
             'cognitedata-development':
                {'path_to_module': 'cognite_data_platform/ml_api',
                 'module_source': 'cdp/ml-api',
                 'git_ref': '2b4d805'
                },
             'module_source': 'cdp/ml-api',
             'cognitedata-production':
                {'path_to_module': 'cognite_data_platform/ml_api',
                 'module_source': 'cdp/ml-api',
                 'git_ref': '2b4d805'
                },
             'cognitedata-test':
                {'path_to_module': 'cognite_data_platform/ml_api',
                 'module_source': 'cdp/ml-api',
                 'git_ref': '2b4d805'
                }
            },
        }
    """
    count = 0
    for file in all_files:
        file_decoded = file.decode()
        if file.endswith(b'.tf'):
            file_split = file_decoded.split('/')
            project = file_split[0]
            folder_path = get_folder_path(file_decoded)
            modules_map = find_modules_in_file(file, lastfcommit)
            for module, module_info in modules_map.items():
                module_map_info_obj = None
                for id in module_state_map:
                    if module_state_map[id]["module_name"] == module:
                        module_map_info_obj = module_state_map[id]
                if module_map_info_obj:
                    # module already exists. add new project where module is found
                    if project not in module_map_info_obj:
                        module_map_info_obj[project] = {}
                    for module_source in module_info:
                        module_map_info_obj[project]["path_to_module"] = folder_path
                        module_map_info_obj[project]["module_source"] = module_source
                        module_map_info_obj[project]["git_ref"] = module_info[module_source]
                else:
                    # add new module to map
                    module_state_map[count] = {}
                    module_state_map[count]["module_name"] = module
                    for module_source in module_info:
                        module_state_map[count][project] = {}
                        module_state_map[count][project]["path_to_module"] = folder_path
                        module_state_map[count]["module_source"] = module_source
                        module_state_map[count][project]["module_source"] = module_source
                        module_state_map[count][project]["git_ref"] = module_info[module_source]
                    count += 1
    # set module source to be the one Greenfield points to
    for key, module_info in module_state_map.items():
        if 'cognitedata-greenfield' in module_info:
            module_state_map[key]["module_source"] = module_info["cognitedata-greenfield"]["module_source"]


def get_commit_in_subpath(module_git_ref, all_commits, subpath_commits):
    """Gets Commit that the git_ref sha is pointing to

    Args:
        git_ref: The sha commit that the module is pointing to
        all_commits: A sequential list of all commits made in the terraform-cognite-modules repo
        subpath_commits: A sequential list of commits made in dirfnm

    Returns:
        The Commit object that the module_git_ref is pointing to in the list of subpath_commits
    """
    for index, all_commit in enumerate(all_commits):
        short_module_git_ref = all_commit.id.decode()[0:7]
        if short_module_git_ref == module_git_ref:
            for index_of_commit_after_match in range(index, len(all_commits)):
                commit_after_match = all_commits[index_of_commit_after_match]
                for subpath_commit in subpath_commits:
                    short_subpath_sha = subpath_commit.id.decode()[0:7]
                    if short_subpath_sha == commit_after_match.id.decode()[0:7]:
                        return subpath_commit
    return None

def create_all_commits_list(iterator, all_commits):
    """Finds all commits in the modules_repo and appends to all_commits list

    Args:
        iterator: Iterator to traverse all commits
        all_commits: An empty list

    Returns:
        None
    """
    while True:
        try:
            lastfcommit = next(iterator).commit
        except StopIteration:
            break  # Iterator exhausted: stop the loop
        else:
            all_commits.append(lastfcommit)

def create_subpath_commits_list(iterator_subpath, subpath_commits):
    """Finds all commits in the subfolder dirfnm and appends to subpath_commits list

    Args:
        iterator: Iterator to traverse all commits
        subpath_commits: An empty list

    Returns:
        None
    """
    while True:
        try:
            lastfcommit = next(iterator_subpath).commit
        except StopIteration:
            break  # Iterator exhausted: stop the loop
        else:
            subpath_commits.append(lastfcommit)

def set_diff_module_map(project_commit, project, greenfield_commit, folder_path, module,
                        full_module_path, subpath_commits, diff_module_map, count):
    """Compares the git refs of modules in Greenfield and other projects. If the module
       points to different sha commits, we identify and add them to diff_module_map

    Args:
        project_commit: Commit object in project that is NOT Greenfield
        project: Project of project_commit
        greenfield_commit: Commit object in Greenfield
        folder_path: A string containing the path to the module
        module: A string containing the module name
        full_module_path: A string containing the path to the module, including the project
        subpath_commits: A list of the Commits in the subpath of folder_path
        diff_module_map: A map containing the diffs of modules between Greenfield and all other projects
        count: An integer that acts as a key id for diff_module_map

    Returns:
        None
    """
    if project_commit != greenfield_commit:
        diff_module_map[count] = {}
        diff_module_map[count]["module_name"] = module
        diff_module_map[count][project] = {}
        diff_module_map[count][project]["path_to_module"] = folder_path
        diff_module_map[count][project]["module_source"] = full_module_path
        newer_commit = None
        older_commit = None
        for commit in subpath_commits:
            if commit.id == project_commit.id:
                if newer_commit is None:
                    newer_commit = commit
                    diff_module_map[count][project]["newer_commit"] = commit.id.decode()
                else:
                    older_commit = commit
                    diff_module_map[count][project]["older_commit"] = commit.id.decode()
