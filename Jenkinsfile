pipeline {
  agent any
  stages {
    stage('build') {
      steps {
	sh 'export PATH=/usr/local/bin:$PATH; echo $PATH'
        withPythonEnv('python3') {
          sh 'pip install -r functions/requirements.txt'
          sh 'pip install -r tests/requirements.txt'
        }
      }
    }

    stage('test') {
      steps {
	sh 'export PATH=/usr/local/bin:$PATH; echo $PATH'
        withPythonEnv('python3') {
          sh 'cd tests; pytest'
        }
      }
    }

    stage('deploy') {
      when {
        branch 'main'
      }
      steps {
        echo 'todo: deploy to aws'
      }
    }
  }
}
