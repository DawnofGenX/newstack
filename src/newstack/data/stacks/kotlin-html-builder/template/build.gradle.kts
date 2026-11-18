plugins {
    // kotlin-html-builder
    kotlin("jvm") version "2.0.21"
    application
}

group = "{{ package_name }}"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

tasks.test {
    useJUnitPlatform()
}

application {
    mainClass.set("{{ package_name }}.MainKt")
}
