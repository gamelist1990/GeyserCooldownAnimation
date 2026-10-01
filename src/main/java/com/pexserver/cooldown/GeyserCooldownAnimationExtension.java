package com.pexserver.cooldown;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.GeyserApi;
import org.geysermc.geyser.api.event.lifecycle.*;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.pack.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class GeyserCooldownAnimationExtension implements Extension {
    private volatile boolean packReady;
    private final BedrockPacketSender sender = new BedrockPacketSender();
    private final AnimationReplayGate replayGate = new AnimationReplayGate();
    @Subscribe public void packs(GeyserDefineResourcePacksEvent event) {
        try {
            Files.createDirectories(dataFolder());
            Path pack = dataFolder().resolve("geyser-cooldown-animation.mcpack");
            try (InputStream in = getClass().getResourceAsStream("/geyser-cooldown-animation.mcpack")) {
                if (in == null) throw new IOException("Bundled Geyser Cooldown Animation pack missing");
                Files.copy(in, pack, StandardCopyOption.REPLACE_EXISTING);
            }
            ResourcePack resource = ResourcePack.create(PackCodec.path(pack));
            if (event.resourcePacks().stream().noneMatch(p -> p.uuid().equals(resource.uuid()))) event.register(resource);
            packReady = true;
            logger().info("Cooldown resource pack registered: " + resource.uuid());
        } catch (Exception e) { packReady = false; logger().error("Cooldown pack registration failed: " + e.getClass().getSimpleName() + ": " + e.getMessage()); }
    }
    private final GeyserCooldownObserver observer = new GeyserCooldownObserver();
    @Subscribe public void start(GeyserPostInitializeEvent event) {
        for (var connection : GeyserApi.api().onlineConnections()) attach(connection);
        logger().info("Cooldown animation initialized; resourcePackReady=" + packReady + ".");
    }
    @Subscribe public void join(org.geysermc.geyser.api.event.bedrock.SessionJoinEvent event) { attach(event.connection()); }
    @Subscribe public void disconnect(org.geysermc.geyser.api.event.bedrock.SessionDisconnectEvent event) {
        observer.detach(event.connection());
        UUID uuid = event.connection().javaUuid();
        if (uuid != null) replayGate.remove(uuid);
    }
    private void attach(org.geysermc.geyser.api.connection.GeyserConnection connection) {
        try { observer.attach(connection, (ticks, sequence) -> playAnimation(connection.javaUuid(), ticks, sequence), logger()::info); }
        catch (Exception | LinkageError e) {
            logger().error("Geyser cooldown observer unavailable for " + connection.getClass().getName()
                + ": " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }
    public void playAnimation(UUID uuid, int ticks, long sequence) {
        if (!packReady) {
            logger().warning("Cooldown animation skipped: resource pack is not ready.");
            return;
        }
        if (uuid == null || ticks < 1 || ticks > 200) {
            logger().warning("Cooldown animation skipped: invalid player UUID or ticks.");
            return;
        }
        var connection = GeyserApi.api().connectionByUuid(uuid);
        if (connection == null) {
            logger().warning("Cooldown animation skipped: no active Geyser connection for " + uuid + ".");
            return;
        }
        if (!replayGate.accept(uuid, ticks, sequence, System.nanoTime())) return;
        String animation = AnimationSelector.select(ticks);
        sender.send(connection, animation, logger()::info);
    }
    @Subscribe public void shutdown(GeyserShutdownEvent event) { observer.close(); replayGate.clear(); }
}
