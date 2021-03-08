import yaml
import sys
from src.custom_dumper import CustomDumper
from src.stack_detector import StackDetector
from src.gitlab_client import GitlabClient
from src.util.cache import Cache


class PipelineCreator:
    BUILD_FILENAMES = {
        'MAVEN': 'build-maven',
        'ANGULAR': 'build-angular',
        'NODEJS': 'build-node',
        'JEKYLL': 'build-jekyll',
    }

    @classmethod
    def project_needs_build_job(cls, project_stack):
        return project_stack in ['MAVEN', 'ANGULAR', 'JEKYLL']

    @classmethod
    def _get_build_filename(cls, project_stack):
        return cls.BUILD_FILENAMES[project_stack]

    @classmethod
    def _get_publish_image_filename(cls, registry):
        image_publish_job_filename = None
        if registry.lower() == 'pegah':
            image_publish_job_filename = 'publish-image-to-pegah-registry'
        elif registry.lower() == 'mediaad':
            image_publish_job_filename = 'publish-image-to-mediaad-registry'
        return image_publish_job_filename

    @classmethod
    def _get_deploy_staging_filename(cls):
        return 'deploy-staging'

    @classmethod
    def _get_deploy_production_filename(cls):
        return 'deploy-production'

    @classmethod
    def _get_purge_cloudflare_cache_filename(cls):
        return 'purge-cloudflare-cache'

    @classmethod
    def replace_strings_in_file(cls, filename, string_replacements):
        try:
            output_filename = filename + '-out'
            with open(f'job_templates/{filename}.yml', 'r') as fin:
                with open(f'job_templates/{output_filename}.yml', 'w') as fout:
                    for line in fin:
                        for existing_string, new_string in string_replacements.items():
                            line = line.replace(existing_string, new_string)
                        fout.write(line)
            return output_filename
        except IOError as io_error:
            print(io_error)
            sys.exit(0)

    @classmethod
    def load_yaml_file_content(cls, filename):
        try:
            with open(f'job_templates/{filename}.yml', 'r') as stream:
                build_job_data = yaml.load(stream, Loader=yaml.FullLoader)
                return build_job_data or {}
        except IOError as io_error:
            print(io_error)
            sys.exit()

    @classmethod
    def load_raw_file_content(cls, filepath):
        try:
            with open(filepath, 'r') as stream:
                file_content = stream.read()
                return file_content
        except IOError as io_error:
            print(io_error)
            sys.exit()

    @classmethod
    def get_init_content(cls):
        init_file_name = 'init'
        init_data = cls.load_yaml_file_content(init_file_name)
        return init_data

    @classmethod
    def get_build_job_content(cls, project_stack, production_branch, has_staging, staging_branch):
        build_file_name = cls._get_build_filename(project_stack)
        replacements = {
            'STAGING_BRANCH': staging_branch if has_staging else 'notyet',
            'PRODUCTION_BRANCH': production_branch,
        }

        output_file_name = cls.replace_strings_in_file(build_file_name, replacements)
        build_data = cls.load_yaml_file_content(output_file_name)
        return build_data

    @classmethod
    def get_semantic_release_job_content(cls, production_branch):
        semantic_release_job_file_name = 'semantic-release'
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
        }
        output_file_name = cls.replace_strings_in_file(semantic_release_job_file_name, replacements)
        semantic_release_job_data = cls.load_yaml_file_content(output_file_name)
        return semantic_release_job_data

    @classmethod
    def get_test_job_content(cls, project_stack, production_branch, has_staging, staging_branch):
        test_job_file_name = 'test-maven'
        replacements = {
            'STAGING_BRANCH': staging_branch if has_staging else 'notyet',
            'PRODUCTION_BRANCH': production_branch,
        }
        output_file_name = cls.replace_strings_in_file(test_job_file_name, replacements)
        test_job_data = cls.load_yaml_file_content(output_file_name)
        return test_job_data

    @classmethod
    def get_publish_image_job_content(cls, project_stack, production_branch, has_staging, staging_branch, registry='pegah'):
        publish_file_name = cls._get_publish_image_filename(registry)
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
            'STAGING_BRANCH': staging_branch if has_staging else 'notyet',
        }
        if cls.project_needs_build_job(project_stack):
            build_job_name = cls._get_build_filename(project_stack)
            replacements['BUILD_JOB_NAME'] = build_job_name
        else:
            replacements['dependencies:'] = 'dependencies: []'
            replacements['    - BUILD_JOB_NAME'] = ''
        output_file_name = cls.replace_strings_in_file(publish_file_name, replacements)
        publish_image_data = cls.load_yaml_file_content(output_file_name)
        return publish_image_data

    @classmethod
    def get_deploy_staging_job_content(cls, staging_branch, auto_deploy):
        deploy_staging_file_name = cls._get_deploy_staging_filename()
        replacements = {
            'STAGING_BRANCH': staging_branch,
            'DEPLOY_MODE': 'on_success' if auto_deploy else 'manual',
        }
        output_file_name = cls.replace_strings_in_file(deploy_staging_file_name, replacements)
        deploy_production_data = cls.load_yaml_file_content(output_file_name)
        return deploy_production_data

    @classmethod
    def get_deploy_production_job_content(cls, production_branch, auto_deploy):
        deploy_production_file_name = cls._get_deploy_production_filename()
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
            'DEPLOY_MODE': 'on_success' if auto_deploy else 'manual',
        }
        output_file_name = cls.replace_strings_in_file(deploy_production_file_name, replacements)
        deploy_production_data = cls.load_yaml_file_content(output_file_name)
        return deploy_production_data

    @classmethod
    def get_deploy_trax_job_content(cls, production_branch):
        deploy_trax_file_name = 'deploy-trax'
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
            'DEPLOY_MODE': 'manual',
        }
        output_file_name = cls.replace_strings_in_file(deploy_trax_file_name, replacements)
        deploy_trax_data = cls.load_yaml_file_content(output_file_name)
        return deploy_trax_data

    @classmethod
    def get_sentry_release_job_content(
            cls, production_branch, project_name_in_sentry, project_stack,
    ):
        sentry_release_file_name = 'sentry-release'
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
            'PROJECT_NAME_IN_SENTRY': project_name_in_sentry,
            'SEMANTIC_RELEASE_JOB_NAME': 'semantic-release',
        }
        build_job_name = cls._get_build_filename(project_stack)
        replacements['BUILD_JOB_NAME'] = build_job_name
        output_file_name = cls.replace_strings_in_file(sentry_release_file_name, replacements)
        sentry_release_job_content = cls.load_yaml_file_content(output_file_name)
        return sentry_release_job_content

    @classmethod
    def get_purge_cloudflare_cache_job_content(cls, production_branch):
        purge_cloudflare_file_name = cls._get_purge_cloudflare_cache_filename()
        replacements = {
            'PRODUCTION_BRANCH': production_branch,
        }
        output_file_name = cls.replace_strings_in_file(purge_cloudflare_file_name, replacements)
        purge_cloudflare_cache_data = cls.load_yaml_file_content(output_file_name)
        return purge_cloudflare_cache_data

    @classmethod
    def save_jobs_data_to_pipeline_file(cls, jobs_data):
        try:
            with open('job_templates/.gitlab-ci.yml', 'w') as output_file:
                yaml.dump(jobs_data, output_file, Dumper=CustomDumper, default_flow_style=False, sort_keys=False)
        except IOError as io_exception:
            print(io_exception)
            sys.exit(0)

    @classmethod
    def commit_changes_to_cicd_branches(cls, pipeline_data, project_id, production_branch, has_staging, staging_branch, project_stack):
        GitlabClient.delete_repository_branch_if_exists(project_id, 'migrate-ci')
        GitlabClient.delete_repository_branch_if_exists(project_id, 'migrate-ci-stg')
        GitlabClient.create_new_branch_for_repository(project_id, 'migrate-ci', production_branch)
        if has_staging:
            GitlabClient.create_new_branch_for_repository(project_id, 'migrate-ci-stg', staging_branch)
        cls.save_jobs_data_to_pipeline_file(pipeline_data)
        gitlab_ci_file_content = cls.load_raw_file_content('job_templates/.gitlab-ci.yml')
        GitlabClient.upsert_file_to_repository_branch(
            project_id, 'migrate-ci', '.gitlab-ci.yml', gitlab_ci_file_content,
        )
        if has_staging:
            GitlabClient.upsert_file_to_repository_branch(
                project_id, 'migrate-ci-stg', '.gitlab-ci.yml', gitlab_ci_file_content,
            )

    @classmethod
    def create_merge_requests_for_cicd_branches(cls, project_id, production_branch, staging_branch, has_staging):
        pipeline_merge_request = GitlabClient.create_merge_request(
            project_id,
            source_branch='migrate-ci',
            target_branch=production_branch,
        )
        production_merge_request_info = {
            'id': pipeline_merge_request.get('id'),
            'title': pipeline_merge_request.get('title'),
            'web_url': pipeline_merge_request.get('web_url'),
            'project_id': pipeline_merge_request.get('project_id'),
            'description': pipeline_merge_request.get('description'),
        }
        staging_merge_request_info = None
        if has_staging:
            staging_pipeline_merge_request = GitlabClient.create_merge_request(
                project_id,
                source_branch='migrate-ci-stg',
                target_branch=staging_branch,
            )
            staging_merge_request_info = {
                'id': staging_pipeline_merge_request.get('id'),
                'title': staging_pipeline_merge_request.get('title'),
                'web_url': staging_pipeline_merge_request.get('web_url'),
                'project_id': staging_pipeline_merge_request.get('project_id'),
                'description': staging_pipeline_merge_request.get('description'),
            }
        return production_merge_request_info, staging_merge_request_info

    @classmethod
    def pipeline_already_enabled_for_project(cls, project_id):
        project_branches = GitlabClient.get_project_branches(project_id)
        project_branch_names = map(lambda x: x.get('name'), project_branches)
        potential_production_branches = filter(
                lambda x: x in ['master', 'prod', 'production'],
                project_branch_names,
            )
        pipeline_already_enabled = False
        for branch in potential_production_branches:
            gitlab_ci_file_exists = GitlabClient.file_exists_in_project(project_id, branch, '.gitlab-ci.yml')
            pipeline_already_enabled = pipeline_already_enabled or gitlab_ci_file_exists
        return pipeline_already_enabled

    @classmethod
    def get_total_number_of_pipelines_created(cls):
        total_count = Cache.get('pipelines_created', 'total_count')
        return total_count

    @classmethod
    def generate_gitlab_ci_file_content(
            cls,
            project_info,
            production_branch,
            staging_branch,
            project_stack,
            production_auto_deploy,
            staging_auto_deploy,
            has_staging,
            has_semantic_release,
            has_sentry_release,
            has_unit_tests,
            deploy_to_trax,
            behind_cloudflare,
            project_name_in_sentry,
    ):
        init_content = cls.get_init_content()

        semantic_release_job_content = {}
        if has_semantic_release or has_sentry_release:
            semantic_release_job_content = cls.get_semantic_release_job_content()

        build_job_content = {}
        if cls.project_needs_build_job(project_stack):
            build_job_content = cls.get_build_job_content(
                project_stack, production_branch, has_staging, staging_branch,
            )

        test_job_content = {}
        if has_unit_tests:
            test_job_content = cls.get_test_job_content(
                project_stack, production_branch, has_staging, staging_branch,
            )

        pegah_registry_image_publish_job_content = cls.get_publish_image_job_content(
            project_stack,
            production_branch,
            has_staging,
            staging_branch,
            'pegah',
        )

        mediaad_registry_image_publish_job_content = {}
        if project_info.get('namespace').lower() == 'tapsell' and deploy_to_trax:
            mediaad_registry_image_publish_job_content = cls.get_publish_image_job_content(
                project_stack, production_branch, has_staging, staging_branch, 'mediaad',
            )

        deploy_staging_job_content = {}
        if has_staging:
            deploy_staging_job_content = cls.get_deploy_staging_job_content(staging_branch, staging_auto_deploy)

        deploy_production_job_content = cls.get_deploy_production_job_content(
            production_branch, production_auto_deploy,
        )

        deploy_trax_job_content = {}
        if project_info.get('namespace').lower() == 'tapsell' and deploy_to_trax:
            deploy_trax_job_content = cls.get_deploy_trax_job_content(production_branch)

        sentry_release_job_content = {}
        if has_sentry_release:
            sentry_release_job_content = cls.get_sentry_release_job_content(
                production_branch,
                project_name_in_sentry,
                project_stack,
            )

        purge_cloudflare_cache_job_content = {}
        if behind_cloudflare:
            purge_cloudflare_cache_job_content = cls.get_purge_cloudflare_cache_job_content(
                production_branch,
            )

        pipeline_aggregated_data = {
            **init_content,
            **semantic_release_job_content,
            **build_job_content,
            **test_job_content,
            **pegah_registry_image_publish_job_content,
            **mediaad_registry_image_publish_job_content,
            **deploy_staging_job_content,
            **deploy_production_job_content,
            **deploy_trax_job_content,
            **sentry_release_job_content,
            **purge_cloudflare_cache_job_content,
        }
        return pipeline_aggregated_data

    @classmethod
    def enable_project_cicd_pipeline(
            cls,
            project_id,
            production_branch_data,
            staging_branch_data,
            has_unit_tests,
            has_semantic_release,
            has_sentry_release,
            behind_cloudflare,
            has_staging,
            deploy_to_trax,
            project_name_in_sentry,
    ):
        project_info = GitlabClient.get_project_info(project_id)
        production_branch, production_auto_deploy = production_branch_data
        staging_branch, staging_auto_deploy = staging_branch_data
        project_stack = StackDetector.detect_project_stack_accurate(project_id, production_branch)

        pipeline_aggregated_data = cls.generate_gitlab_ci_file_content(
            project_info,
            production_branch,
            staging_branch,
            project_stack,
            production_auto_deploy,
            staging_auto_deploy,
            has_staging,
            has_semantic_release,
            has_sentry_release,
            has_unit_tests,
            deploy_to_trax,
            behind_cloudflare,
            project_name_in_sentry,
        )
        cls.commit_changes_to_cicd_branches(
            pipeline_aggregated_data, project_id, production_branch, has_staging, staging_branch, project_stack
        )
        production_merge_request_info, staging_merge_request_info = cls.create_merge_requests_for_cicd_branches(
            project_id,
            production_branch,
            staging_branch,
            has_staging,
        )
        project_shared_runner_url = f'{GitlabClient.INSTANCE_URL}/{project_info.get("namespace")}/{project_info.get("path")}/-/settings/ci_cd'

        project_jenkins_url = f'{GitlabClient.JENKINS_URL}/job/{project_info.get("namespace")}/job/{project_info.get("path")}'

        GitlabClient.invalidate_project_pipeline_status_cache(project_id)

        Cache.increment_key('pipelines_created', 'total_count')
        return {
            'merge_request_info': production_merge_request_info,
            'staging_merge_request_info': staging_merge_request_info,
            'shared_runner_url': project_shared_runner_url,
            'jenkins_url': project_jenkins_url,
        }
