pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        withPythonEnv('~/.pyenv/versions/3.8.11/bin/python') {
          sh 'pip install -r functions/requirements.txt'
          sh 'pip install -r tests/requirements.txt'
        }
      }
    }

    stage('test') {
      steps {
        withPythonEnv('~/.pyenv/versions/3.8.11/bin/python') {
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
