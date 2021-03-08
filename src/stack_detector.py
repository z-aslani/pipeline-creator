from .gitlab_client import GitlabClient


class StackDetector:
    def __init__(self):
        pass

    @classmethod
    def format_project_stack(cls, project_stack):
        formatted_project_stack = ''.join([project_stack[0], project_stack[1:].lower()])
        if formatted_project_stack == 'Maven':
            formatted_project_stack = 'Java/Kotlin'
        elif formatted_project_stack == 'Html':
            formatted_project_stack = 'HTML'
        return formatted_project_stack

    @classmethod
    def detect_project_stack(cls, project_id):
        languages = GitlabClient.get_project_languages(project_id)
        if 'Java' in languages or 'Kotlin' in languages:
            project_stack = 'MAVEN'
        elif 'TypeScript' in languages and 'CSS' in languages:
            project_stack = 'ANGULAR'
        elif 'HTML' in languages and 'CSS' in languages:
            project_stack = 'HTML'
        elif 'TypeScript' in languages or 'JavaScript' in languages:
            project_stack = 'NODEJS'
        elif 'Python' in languages:
            project_stack = 'PYTHON'
        elif 'Ruby' in languages and 'JavaScript' in languages and 'HTML' in languages:
            project_stack = 'JEKYLL'
        elif 'Dockerfile' in languages:
            project_stack = 'DOCKER'
        else:
            project_stack = 'UNKNOWN'
        return project_stack

    @classmethod
    def detect_project_stack_accurate(cls, project_id, branch):
        if GitlabClient.file_exists_in_project(project_id, branch, 'pom.xml'):
            project_stack = 'MAVEN'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'angular.json'):
            project_stack = 'ANGULAR'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'gatsby-config.js'):
            project_stack = 'GATSBY'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'Gemfile')\
                and GitlabClient.file_exists_in_project(project_id, branch, '_config.yml')\
                and GitlabClient.file_exists_in_project(project_id, branch, 'package.json'):
            project_stack = 'JEKYLL'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'requirements.txt') or GitlabClient.file_exists_in_project(project_id, branch, 'requirements.pip'):
            project_stack = 'PYTHON'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'Dockerfile'):
            project_stack = 'DOCKER'
        elif GitlabClient.file_exists_in_project(project_id, branch, 'package.json'):
            project_stack = 'NODEJS'
        else:
            project_stack = 'UNKNOWN'
        return project_stack
