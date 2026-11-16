plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "io.github.watch8.xmasface"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.watch8.xmasface"
        minSdk = 34
        targetSdk = 36
        versionCode = 9
        versionName = "2.3.2"
    }

    buildTypes {
        debug {
            isMinifyEnabled = true
            isShrinkResources = false
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
