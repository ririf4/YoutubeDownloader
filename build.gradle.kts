plugins {
    kotlin("jvm") version "2.2.0-Beta1"
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.0-Beta1"
    application
}

repositories {
    google()
    mavenCentral()
}

dependencies {
    implementation("org.jetbrains.compose.desktop:desktop-jvm-windows-x64:1.8.0-beta02")
}

application {
    mainClass.set("MainKt")
}