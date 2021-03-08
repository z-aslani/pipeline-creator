import requests
from src.util.cache import Cache


class RequestUtil:
    @classmethod
    def send_post_request(cls, url, body=None, query_params=None, headers=None):
        response = requests.post(url, json=body, params=query_params, headers=headers)
        return response.json(), response.headers, response.status_code

    @classmethod
    def send_get_request(cls, url, headers, query_params=None):
        response = requests.get(url, params=query_params or {}, headers=headers)
        return response.json(), response.headers, response.status_code

    @classmethod
    def send_delete_request(cls, url, headers):
        requests.delete(url, headers=headers)


class GitlabClient:
    INSTANCE_URL = 'https://git.tapsell.ir'
    JENKINS_URL = 'https://jenkins.pegah.tech'
    API_BASE_URL = 'https://git.tapsell.ir/api/v4'
    PERSONAL_TOKEN = 'bTRPYxLRpGiszToEzMYw'  # TODO: remove this a.s.a.p

    @classmethod
    def get_all_groups(cls):
        cached_groups = Cache.get_list('groups', 'pegah')
        if cached_groups is not None and len(cached_groups) > 0:
            return cached_groups
        url = f'{cls.API_BASE_URL}/groups'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        query_params = {
            'per_page': 100,
        }

        def projector(elem):
            return {
                'id': elem['id'],
                'full_name': elem['full_name'],
                'full_path': elem['full_path'],
                'description': elem['description'],
            }
        groups = []
        current_page = 1
        latest_page = 100000
        while current_page <= latest_page:
            query_params['page'] = current_page
            paginated_groups, headers, _ = RequestUtil.send_get_request(url, query_params=query_params, headers=headers)
            latest_page = int(headers['X-Total-Pages'])
            paginated_groups = list(map(projector, paginated_groups))
            groups.extend(paginated_groups)
            current_page += 1
        Cache.set_list('groups', 'pegah', groups, ttl=24*60*60)
        return groups

    @classmethod
    def search_project_by_name(cls, group, project):
        url = f'{cls.API_BASE_URL}/search'
        query_params = {
            'scope': 'projects',
            'search': project,
        }
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        result_projects, headers, _ = RequestUtil.send_get_request(url, query_params=query_params, headers=headers)
        for result_project in result_projects:
            if result_project.get('namespace').get('path') == group:
                return {
                    'id': result_project['id'],
                    'namespace': result_project['namespace']['path'],
                    'name': result_project['name'],
                    'path': result_project['path'],
                    'description': result_project['description'],
                }, True
        return {}, False

    @classmethod
    def get_group_projects(cls, group_id, page_number):
        # cached_projects = Cache.get_list(f'group_projects:{group_id}', page_number)
        # cached_total_page = Cache.get('projects_total_page', group_id)
        # cached_projects_count = Cache.get('projects_total_count', group_id)
        # if cached_projects is not None and len(cached_projects) > 0:
        #     return cached_projects, cached_total_page, cached_projects_count
        url = f'{cls.API_BASE_URL}/groups/{group_id}/projects'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        query_params = {
            'per_page': 15,
            'with_shared': False,
        }

        def projector(elem):
            pipeline_enabled = cls.pipeline_enabled_for_project_v2(elem['id'])
            # pipeline_enabled = cls.pipeline_enabled_for_project(elem['id'])
            return {
                'id': elem['id'],
                'name': elem['name'],
                'name_with_namespace': elem['name_with_namespace'],
                'path': elem['path'],
                'pipeline_enabled': pipeline_enabled,
            }

        query_params['page'] = page_number
        projects, response_headers, _ = RequestUtil.send_get_request(
            url,
            query_params=query_params,
            headers=headers,
        )
        total_pages = int(response_headers['X-Total-Pages'])
        projects_count = int(response_headers['X-Total'])
        print('before requesting pipelines status')
        projects = list(map(projector, projects))
        # print('before setting cache for group projects')
        # Cache.set_list(f'group_projects:{group_id}', page_number, projects, ttl=60*60)
        # Cache.set('projects_total_page', group_id, total_pages, ttl=60*60)
        # Cache.set('projects_total_count', group_id, projects_count, ttl=60*60)
        return projects, total_pages, projects_count

    @classmethod
    def get_project_info(cls, project_id):
        url = f'{cls.API_BASE_URL}/projects/{project_id}'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        project_details, _, _ = RequestUtil.send_get_request(url, headers=headers)
        project_info = {
            'namespace': project_details['namespace']['path'],
            'path': project_details['path'],
            'name': project_details['name'],
            'description': project_details['description'],
        }
        return project_info

    @classmethod
    def get_project_languages(cls, project_id):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/languages'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        languages, _, _ = RequestUtil.send_get_request(url, headers=headers)
        return languages

    @classmethod
    def get_project_branches(cls, project_id, search=None):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/repository/branches'
        query_params = {
            'per_page': 100,
        }
        if search is not None:
            query_params['search'] = search
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        branches = []
        current_page = 1
        latest_page = 100000
        while current_page <= latest_page:
            query_params['page'] = current_page
            print('before requesting project branches')
            paginated_branches, headers, _ = RequestUtil.send_get_request(url, query_params=query_params, headers=headers)
            print(f"x-total-pages: {headers['X-Total-Pages']}")
            latest_page = int(headers['X-Total-Pages'])
            branches.extend(paginated_branches)
            current_page += 1
        return branches

    @classmethod
    def get_project_production_branch(cls, project_id):
        project_branches = cls.get_project_branches(project_id)
        production_branch = next(
            (branch for branch in project_branches if branch['name'].lower() in ['prod', 'production']),
            {'name': 'master'},
        )
        return production_branch.get('name')

    @classmethod
    def get_project_staging_branch(cls, project_id):
        project_branches = cls.get_project_branches(project_id)
        staging_branch = next(
            (branch for branch in project_branches if branch['name'].lower() in ['staging', 'stg']),
            {},
        )
        return staging_branch.get('name')

    @classmethod
    def create_new_branch_for_repository(cls, project_id, branch_name, base_branch):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/repository/branches'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        query_params = {
            'branch': branch_name,
            'ref': base_branch,
        }
        RequestUtil.send_post_request(url, query_params=query_params, headers=headers)

    @classmethod
    def delete_repository_branch_if_exists(cls, project_id, branch_name):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/repository/branches/{branch_name}'
        headers = {
            'Content-Type': 'application/json',
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        RequestUtil.send_delete_request(url, headers=headers)

    @classmethod
    def upsert_file_to_repository_branch(cls, project_id, branch_name, target_file_path, file_content):
        file_already_exists = cls.file_exists_in_project(project_id, branch_name, target_file_path)
        url = f'{cls.API_BASE_URL}/projects/{project_id}/repository/commits'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        body = {
            'branch': branch_name,
            'commit_message': f'GitLab CI/CD Pipeline Creator: {"update" if file_already_exists else "add"} gitlab-ci file',
            'actions': [
                {
                    'action': 'update' if file_already_exists else 'create',
                    'file_path': target_file_path,
                    'content': file_content,
                },
            ],
        }
        RequestUtil.send_post_request(url, body=body, headers=headers)

    @classmethod
    def pipeline_enabled_for_project(cls, project_id):
        production_branch = cls.get_project_production_branch(project_id)
        cached_project_pipeline_status = Cache.get('project_pipeline_enabled', project_id)
        if cached_project_pipeline_status is not None:
            return cached_project_pipeline_status == 1
        gitlab_ci_file_exists = cls.file_exists_in_project(project_id, production_branch, '.gitlab-ci.yml')
        Cache.set('project_pipeline_enabled', project_id, 1 if gitlab_ci_file_exists else 0)
        return gitlab_ci_file_exists

    @classmethod
    def pipeline_enabled_for_project_v2(cls, project_id):
        cached_pipeline_enabled = Cache.get('pipeline_enabled', project_id)
        if cached_pipeline_enabled is not None:
            return cached_pipeline_enabled == 'True'
        project_branches_set_one = cls.get_project_branches(project_id, 'master')
        project_branches_set_two = cls.get_project_branches(project_id, 'prod')
        possible_branches = project_branches_set_one + project_branches_set_two
        possible_branch_names = map(lambda x: x.get('name'), possible_branches)
        pipeline_already_enabled = False
        for branch_name in possible_branch_names:
            print(f'branch: {branch_name}')
            print(f'project_id: {project_id}')
            gitlab_ci_file_exists = cls.file_exists_in_project(project_id, branch_name, '.gitlab-ci.yml')
            pipeline_already_enabled = pipeline_already_enabled or gitlab_ci_file_exists
        pipeline_status_cache_value = 'True' if pipeline_already_enabled else 'False'
        Cache.set('pipeline_enabled', project_id, pipeline_status_cache_value, 0, True)
        return pipeline_already_enabled

    @classmethod
    def file_exists_in_project(cls, project_id, branch, file_path):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/repository/files/{file_path}'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        query_params = {
            'ref': branch,
        }
        response, _, status_code = RequestUtil.send_get_request(url, headers=headers, query_params=query_params)
        if status_code == 404:
            file_exists = False
        else:
            file_exists = True
        return file_exists

    @classmethod
    def create_merge_request(cls, project_id, source_branch, target_branch):
        url = f'{cls.API_BASE_URL}/projects/{project_id}/merge_requests'
        headers = {
            'PRIVATE-TOKEN': cls.PERSONAL_TOKEN,
        }
        request_body = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': 'Enable Gitlab CI/CD for project',
            'description': 'Gitlab CI/CD migration branch generated by PiplineCreator tool.',
            'remove_source_branch': True,
        }
        response, _, _ = RequestUtil.send_post_request(url, headers=headers, body=request_body)
        return response

    @classmethod
    def invalidate_groups_cache(cls):
        Cache.delete_cache_by_key_prefix('groups:pegah')

    @classmethod
    def invalidate_group_projects_cache(cls, group_id):
        Cache.delete_cache_by_key_prefix(f'group_projects:{group_id}')
        Cache.delete_cache_by_key_prefix(f'projects_total_page:{group_id}')
        Cache.delete_cache_by_key_prefix(f'projects_total_count:{group_id}')

    @classmethod
    def invalidate_project_pipeline_status_cache(cls, project_id):
        Cache.delete_cache('pipeline_enabled', project_id)
