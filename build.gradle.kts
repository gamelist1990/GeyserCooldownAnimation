import groovy.json.JsonOutput
import groovy.json.JsonSlurper

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
    compileOnly("org.geysermc.geyser:core:$geyserApiVersion-SNAPSHOT")
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
val packPython = providers.gradleProperty("packPython").orElse(
    if (System.getProperty("os.name").startsWith("Windows")) "python" else "python3"
)
val generatePackAnimations = tasks.register<Exec>("generatePackAnimations") {
    inputs.file("scripts/generate_pack_animations.py")
    outputs.file("resource-pack/animations/cooldown.animation.json")
    commandLine(packPython.get(), "scripts/generate_pack_animations.py")
}
val validateResourcePack = tasks.register<Exec>("validateResourcePack") {
    dependsOn(generatePackAnimations)
    inputs.dir("resource-pack")
    inputs.files("scripts/validate_resource_pack.py", "scripts/generate_pack_animations.py")
    commandLine(packPython.get(), "scripts/validate_resource_pack.py")
}
tasks.named("check") { dependsOn(validateResourcePack) }

val generatePackManifest = tasks.register("generatePackManifest") {
    inputs.file("resource-pack/manifest.json")
    inputs.property("packVersion", packVersion)
    val output = layout.buildDirectory.file("generated/resource-pack/manifest.json")
    outputs.file(output)
    doLast {
        @Suppress("UNCHECKED_CAST")
        val manifest = JsonSlurper().parse(file("resource-pack/manifest.json")) as MutableMap<String, Any>
        @Suppress("UNCHECKED_CAST")
        val header = manifest["header"] as MutableMap<String, Any>
        header["version"] = packVersion
        @Suppress("UNCHECKED_CAST")
        val modules = manifest["modules"] as List<MutableMap<String, Any>>
        modules.forEach { it["version"] = packVersion }
        output.get().asFile.apply {
            parentFile.mkdirs()
            writeText(JsonOutput.prettyPrint(JsonOutput.toJson(manifest)) + "\n", Charsets.UTF_8)
        }
    }
}
val resourcePack = tasks.register<Zip>("resourcePack") {
    dependsOn(validateResourcePack)
    archiveFileName.set("GeyserCooldownAnimation-pack-$releaseVersion.mcpack")
    destinationDirectory.set(layout.buildDirectory.dir("resource-pack"))
    isPreserveFileTimestamps = false
    isReproducibleFileOrder = true
    from("resource-pack") { exclude("manifest.json") }
    dependsOn(generatePackManifest)
    from(layout.buildDirectory.file("generated/resource-pack/manifest.json"))
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
