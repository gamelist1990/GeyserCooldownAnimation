plugins { java }

val extensionId = providers.gradleProperty("id").get()
val extensionName = providers.gradleProperty("name").get()
val author = providers.gradleProperty("author").get()
val geyserApiVersion = "2.11.0"

allprojects {
    group = "com.pexserver"
    version = rootProject.version
    tasks.withType<Jar>().configureEach {
        isPreserveFileTimestamps = false
        isReproducibleFileOrder = true
        from(rootProject.file("LICENSE")) { into("META-INF") }
        from(rootProject.file("THIRD_PARTY_NOTICES.md")) { into("META-INF") }
        from(rootProject.file("licenses/GeyserExtensionTemplate-MIT.txt")) {
            into("META-INF/licenses")
        }
    }
}

repositories {
    maven("https://repo.opencollab.dev/main/")
    mavenCentral()
}

dependencies {
    compileOnly("org.geysermc.geyser:api:$geyserApiVersion-SNAPSHOT")
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.11.4")
}

java { toolchain.languageVersion.set(JavaLanguageVersion.of(21)) }
tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
    options.release.set(21)
}
tasks.jar { archiveBaseName.set("GeyserCooldownAnimation") }

require(Regex("[a-z][a-z0-9-_]{0,63}").matches(extensionId)) { "Invalid extension id" }
require(Regex("^[A-Za-z_.-]+$").matches(extensionName)) { "Invalid extension name" }

val releaseVersion = project.version.toString()

val packVersion = releaseVersion.substringBefore('-').split('.').map { it.toInt() }
require(packVersion.size == 3 && packVersion.all { it in 0..65535 }) { "Pack version must have three numeric components in 0..65535" }
val resourcePack = tasks.register<Zip>("resourcePack") {
    archiveFileName.set("GeyserCooldownAnimation-pack-$releaseVersion.mcpack")
    destinationDirectory.set(layout.buildDirectory.dir("resource-pack"))
    isPreserveFileTimestamps = false
    isReproducibleFileOrder = true
    from("resource-pack") { exclude("manifest.json") }
    from("resource-pack/manifest.json") {
        filter { line -> line.replace("\"version\": [1, 0, 0]", "\"version\": [" + packVersion.joinToString(", ") + "]") }
    }
    from("LICENSE")
}

tasks.test { useJUnitPlatform() }

tasks.processResources {
    dependsOn(resourcePack)
    from(resourcePack.flatMap { it.archiveFile }) { rename { "geyser-cooldown-animation.mcpack" } }
    inputs.property("version", releaseVersion)
    filesMatching("extension.yml") {
        expand("id" to extensionId, "name" to extensionName, "api" to geyserApiVersion,
            "version" to releaseVersion, "author" to author)
    }
}
