pipeline {
  agent { docker { image 'python:3.8-alpine' } }
  stages {
    stage('build') {
      steps {
        sh 'pip install -r functions/requirements.txt'
        sh 'pip install -r tests/requirements.txt'
      }
    }
    stage('test') {
      steps {
        sh 'cd tests; pytest'
      }
    }
  }
}
