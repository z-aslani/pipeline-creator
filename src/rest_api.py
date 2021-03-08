from flask import Flask, request, jsonify
from flask_cors import CORS
from src.gitlab_client import GitlabClient
from src.stack_detector import StackDetector
from src.pipeline_creator import PipelineCreator


config = {
  'ORIGINS': [
    'http://staff-new.pegah.tech',
    'http://staff.pegah.tech',
    'http://gpc.pegah.tech',
    'https://gpc.pegah.tech'
    'http://navid.pegah.tech:7820',
    'https://staff-new.pegah.tech',
    'https://staff.pegah.tech',
    'https://navid.pegah.tech:7820'
  ]
}
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
response_headers = {}
app.debug = True


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


"""
@api {get} /groups Get all Gitlab groups
@apiName GetAllGroups
@apiGroup Group

@apiSuccess {String} result Request response status, possible values ["OK", "ERR"]
@apiSuccess {Object} data Response data
@apiSuccess {Object[]} data.groups List of groups
@apiSuccess {String} data.groups.id Group ID
@apiSuccess {String} data.groups.full_name Group full name
@apiSuccess {String} data.groups.full_path Group full path
@apiSuccess {String} data.groups.description Group description
"""


@app.route('/groups', methods=['GET'])
def get_all_gitlab_groups():
    groups = GitlabClient.get_all_groups()

    response = {
        'result': 'OK',
        'data': {
            'groups': groups,
        },
    }
    return jsonify(response)


"""
@api {get} /groups/:group_id/projects Get projects of an specific group
@apiName GetGroupProjects
@apiGroup Group

@apiParam {Number} group_id Group ID
@apiParam {Boolean} with_pipeline indicates a query param to get only projects without pipeline

@apiSuccess {String} result Request response status, possible values ["OK", "ERR"]
@apiSuccess {Object} data Response data
@apiSuccess {Object[]} data.projects List of groups
@apiSuccess {String} data.projects.id Project ID
@apiSuccess {String} data.projects.name Project name
@apiSuccess {String} data.projects.name_with_namespace Project name with namespace
@apiSuccess {String} data.projects.description Project description
@apiSuccess {String} data.projects.default_branch Project default branch
"""


@app.route('/groups/<int:group_id>/projects', methods=['GET'])
def get_group_projects(group_id):
    page_number = request.args.get('page') or 1
    projects, total_pages, total_count = GitlabClient.get_group_projects(group_id, page_number)

    response = {
        'result': 'OK',
        'data': {
            'total_pages': total_pages,
            'total_count': total_count,
            'projects': projects,
        },
    }
    return jsonify(response)


"""
@api {get} /projects/:project_id/info Get project info
@apiName GetProjectInfo
@apiGroup Project

@apiParam {Number} project_id Project ID

@apiSuccess {String} result Request response status, possible values ["OK", "ERR"]
@apiSuccess {Object} data Response data
@apiSuccess {Object} data.project_info Project Info
@apiSuccess {String} data.project_info.name Project Name
@apiSuccess {String} data.project_info.namespace Project Namespace
@apiSuccess {String} data.project_info.stack Project stack
@apiSuccess {String} data.project_info.description Project description
"""


@app.route('/projects/<int:project_id>/info', methods=['GET'])
def get_project_info(project_id):
    project_stack = StackDetector.detect_project_stack(project_id)
    formatted_project_stack = StackDetector.format_project_stack(project_stack)
    project_info = GitlabClient.get_project_info(project_id)
    project_info['stack'] = formatted_project_stack

    response = {
        'result': 'OK',
        'data': {
            'project_info': project_info,
        },
    }
    return jsonify(response)


@app.route('/projects/<int:project_id>/stack', methods=['GET'])
def get_project_stack(project_id):
    project_stack = StackDetector.detect_project_stack(project_id)

    response = {
        'result': 'OK',
        'data': {
            'project_stack': project_stack,
        },
    }
    return jsonify(response)


@app.route('/search/project', methods=['GET'])
def get_project_info_by_name():
    group_name = request.args.get('group')
    project_name = request.args.get('project')
    project_info, exists = GitlabClient.search_project_by_name(group_name, project_name)
    if not exists:
        response = {
            'result': 'ERR',
            'data': {
                'message': 'PROJECT_NOT_FOUND',
            },
        }
        return jsonify(response)

    project_stack = StackDetector.detect_project_stack(project_info['id'])
    project_stack = ''.join([project_stack[0], project_stack[1:].lower()])
    if project_stack == 'Maven':
        project_stack = 'Java/Kotlin'
    project_info['stack'] = project_stack
    project_info['pipeline_enabled'] = GitlabClient.pipeline_enabled_for_project_v2(project_info['id'])

    response = {
        'result': 'OK',
        'data': {
            'project_info': project_info,
        },
    }
    return jsonify(response)

"""
@api {get} /projects/:project_id/branches Get project branches
@apiName GetProjectBranches
@apiGroup Project

@apiParam {Number} project_id Project ID

@apiSuccess {String} result Request response status, possible values ["OK", "ERR"]
@apiSuccess {Object} data Response data
@apiSuccess {Object[]} data.branches List of branches
@apiSuccess {String} data.branches.name Branch name
@apiSuccess {String} data.branches.web_url Branch web URL
@apiSuccess {String} data.branches.protected Branch protected status
@apiSuccess {String} data.suggested_production_branch Project probable production branch
@apiSuccess {String} data.suggested_staging_branch Project probable staging branch
"""


@app.route('/projects/<int:project_id>/branches', methods=['GET'])
def get_project_branches(project_id):
    branches = GitlabClient.get_project_branches(project_id)
    suggested_production_branch = GitlabClient.get_project_production_branch(project_id)
    suggested_staging_branch = GitlabClient.get_project_staging_branch(project_id)
    response = {
        'result': 'OK',
        'data': {
            'branches': branches,
            'suggested_production_branch': suggested_production_branch,
            'suggested_staging_branch': suggested_staging_branch,
        },
    }
    return jsonify(response)


@app.route('/behind_cloudflare/<string:project_url>', methods=['GET'])
def get_project_cloudflare_cache_status(project_url):
    # TODO: incomplete

    response = {
        'result': 'OK',
        'data': {},
    }
    return jsonify(response)


"""
@api {get} /pipeline/status/:project_id Get pipeline status of an specific project
@apiName GetProjectPipelineStatus
@apiGroup Pipeline

@apiParam {Number} project_id Project ID

@apiSuccess {String} result Request response status, possible values ["OK", "ERR"]
@apiSuccess {Object} data Response data
@apiSuccess {Boolean} data.pipeline_enabled Pipline enabled or not
"""


@app.route('/pipeline/status/<int:project_id>', methods=['GET'])
def get_project_pipeline_status(project_id):
    project_pipeline_status = PipelineCreator.pipeline_already_enabled_for_project(project_id)

    response = {
        'result': 'OK',
        'data': {
            'pipeline_enabled': project_pipeline_status,
        },
    }
    return jsonify(response)


"""
@api {post} /pipeline/create Create pipeline for project
@apiName CreatePipelineForProject
@apiGroup Group

@apiParam {Number} project_id Project ID
@apiParam {Object} production_branch Production branch data
@apiParam {String} production_branch.name Production branch name
@apiParam {String} production_branch.auto_deploy indicates production env deploy mode
@apiParam {Object} staging_branch Staging branch data
@apiParam {String} staging_branch.name staging branch name
@apiParam {String} staging_branch.auto_deploy indicates staging env deploy mode
@apiParam {Boolean} has_unit_tests Indicates whether maven project has unit tests or not
@apiParam {String} service_url Service URL
@apiParam {Boolean} behind_cloudflare Behind Cloudflare
@apiParam {Boolean} has_staging Has staging
@apiParam {Boolean} push_to_mediaad_registry Push to mediaad registry

@apiSuccess {String} result Request response status
@apiSuccess {Object} data Request response object
@apiSuccess {Object} data.merge_request_info created merge request info
@apiSuccess {String} data.merge_request_info.id created merge request ID
@apiSuccess {String} data.merge_request_info.title created merge request title
@apiSuccess {String} data.merge_request_info.web_url created merge request web URL
@apiSuccess {String} data.merge_request_info.description created merge request description

@apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
      "result": "ERR",
      "data": {
        "message": "PIPELINE_ALREADY_ENABLED"
      }
    }
"""


@app.route('/pipeline/created', methods=['GET'])
def get_total_number_of_created_pipelines():
    total_count = PipelineCreator.get_total_number_of_pipelines_created()

    response = {
        'result': 'OK',
        'data': {
            'total_count': total_count,
        },
    }
    return jsonify(response)


@app.route('/pipeline/create', methods=['POST'])
def create_project_pipeline():
    request_data = request.get_json(force=True)
    project_info = {
        'project_id': request_data.get('project_id'),
        'production_branch_data': (
            request_data.get('production_branch').get('name'),
            request_data.get('production_branch').get('auto_deploy'),
        ),
        'staging_branch_data': (
            request_data.get('staging_branch').get('name'),
            request_data.get('staging_branch').get('auto_deploy'),
        ),
        'has_unit_tests': request_data.get('has_unit_tests') or False,
        'has_semantic_release': request_data.get('has_semantic_release') or False,
        'has_sentry_release': request_data.get('has_sentry_release') or False,
        'project_name_in_sentry': request_data.get('project_name_in_sentry'),
        'behind_cloudflare': request_data.get('behind_cloudflare') or False,
        # 'service_url': request_data.get('service_url'),
        'has_staging': request_data.get('has_staging') or False,
        'deploy_to_trax': request_data.get('deploy_to_trax'),
    }
    # pipeline_already_enabled = PipelineCreator.pipeline_already_enabled_for_project(request_data['project_id'])
    # if pipeline_already_enabled:
    #     return jsonify({
    #         'result': 'ERR',
    #         'data': {
    #             'message': 'PIPELINE_ALREADY_ENABLED',
    #         },
    #     }), 409
    pipeline_creation_result = PipelineCreator.enable_project_cicd_pipeline(**project_info)

    response = {
        'result': 'OK',
        'data': {
            'merge_request_info': pipeline_creation_result.get('merge_request_info'),
            'staging_merge_request_info': pipeline_creation_result.get('staging_merge_request_info'),
            'shared_runner_url': pipeline_creation_result.get('shared_runner_url'),
            'jenkins_url': pipeline_creation_result.get('jenkins_url'),
        },
    }

    return jsonify(response)


app.run(host='0.0.0.0', debug=True)
