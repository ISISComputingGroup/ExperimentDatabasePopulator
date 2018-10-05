#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {  
    label {
      label "Python_3_tests"
      // Use custom workspace to avoid issue with long filepaths on Win32
      customWorkspace "C:/Exp_DB_Populator/${env.BRANCH_NAME}"
    }
  }
  
  triggers {
    pollSCM('H/2 * * * *')
  }
  
  stages {  
    stage("Checkout") {
      steps {
        echo "Branch: ${env.BRANCH_NAME}"
        checkout scm
      }
    }
    
    stage("Build") {
      steps {
        echo "Build Number: ${env.BUILD_NUMBER}"
        script {
            env.GIT_COMMIT = bat(returnStdout: true, script: '@git rev-parse HEAD').trim()
            env.GIT_BRANCH = bat(returnStdout: true, script: '@git rev-parse --abbrev-ref HEAD').trim()
            echo "git commit: ${env.GIT_COMMIT}"
            echo "git branch: ${env.BRANCH_NAME} ${env.GIT_BRANCH}"
            if (env.BRANCH_NAME != null && env.BRANCH_NAME.startsWith("Release")) {
                env.IS_RELEASE = "YES"
                env.RELEASE_VERSION = "${env.BRANCH_NAME}".replace('Release_', '')
                echo "release version: ${env.RELEASE_VERSION}"
            }
            else {
                env.IS_RELEASE = "NO"
                env.RELEASE_VERSION = ""
            }
        }
        
        bat """
            C:/Python36/Scripts/pip.exe install virtualenv
            C:/Python36/Scripts/virtualenv.exe my_python
            call my_python//Scripts//activate.bat
            call my_python//Scripts//pip.exe install -r requirements.txt
            python.exe run_tests.py --output_dir test-reports
            """
      }
    }
   stage("Unit Test Results") {
    steps {
        junit "test-reports/**/*.xml"
    }
   }
  }
  
  post {
    failure {
      step([$class: 'Mailer', notifyEveryUnstableBuild: true, recipients: 'icp-buildserver@lists.isis.rl.ac.uk', sendToIndividuals: true])
    }
  }
  
  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'5', daysToKeepStr: '7'))
    timeout(time: 60, unit: 'MINUTES')
    disableConcurrentBuilds()
  }
}
