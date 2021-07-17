pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        withPythonEnv('~/.pyenv/shims/python') {
          sh 'pip install -r functions/requirements.txt'
          sh 'pip install -r tests/requirements.txt'
        }
      }
    }

    stage('test') {
      steps {
        withPythonEnv('~/.pyenv/shims/python') {
          sh 'cd tests; pytest'
        }
      }
    }

    stage('deploy') {
      when {
        branch 'master'
      }
      steps {
        echo 'deploy to aws'
      }
    }
  }
}
