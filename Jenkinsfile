pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        withPythonEnv('/Users/ouj/.pyenv/shims/python') {
          sh 'pip install -r functions/requirements.txt'
          sh 'pip install -r tests/requirements.txt'
        }
      }
    }

    stage('test') {
      steps {
        withPythonEnv('/Users/ouj/.pyenv/shims/python') {
          sh 'cd tests; pytest'
        }
      }
    }

    stage('deploy') {
      when {
        branch 'main'
      }
      steps {
        echo 'deploy to aws'
      }
    }
  }
}
