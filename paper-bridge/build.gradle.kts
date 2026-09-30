plugins { java }

repositories {
    mavenCentral()
    maven("https://repo.papermc.io/repository/maven-public/")
}
dependencies { compileOnly("io.papermc.paper:paper-api:26.3.build.135-beta") }

java { toolchain.languageVersion.set(JavaLanguageVersion.of(25)) }
tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
    options.release.set(25)
}
val releaseVersion = project.version.toString()

tasks.processResources {
    inputs.property("version", releaseVersion)
    filesMatching("plugin.yml") { expand("version" to releaseVersion) }
}
tasks.jar { archiveBaseName.set("GeyserCooldownPaperBridge") }
