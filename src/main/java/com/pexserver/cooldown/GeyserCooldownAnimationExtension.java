package com.pexserver.cooldown;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.GeyserApi;
import org.geysermc.geyser.api.event.lifecycle.*;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.pack.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
public final class GeyserCooldownAnimationExtension implements Extension {
    private volatile boolean packReady;
    private final BedrockPacketSender sender = new BedrockPacketSender();
    private final Map<UUID, Stamp> stamps = new ConcurrentHashMap<>();
    private record Stamp(long sequence, long time) {}
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
        } catch (Exception e) { packReady = false; logger().error("Cooldown pack registration failed: " + e.getMessage()); }
    }
    private final JavaMessageReceiver receiver = new JavaMessageReceiver();
    @Subscribe public void start(GeyserPostInitializeEvent event) {
        for (var connection : GeyserApi.api().onlineConnections()) attach(connection);
        logger().info("Cooldown animation enabled; no token, endpoint or HTTP port required.");
    }
    @Subscribe public void join(org.geysermc.geyser.api.event.bedrock.SessionJoinEvent event) { attach(event.connection()); }
    @Subscribe public void disconnect(org.geysermc.geyser.api.event.bedrock.SessionDisconnectEvent event) {
        receiver.detach(event.connection());
        UUID uuid = event.connection().javaUuid();
        if (uuid != null) stamps.remove(uuid);
    }
    private void attach(org.geysermc.geyser.api.connection.GeyserConnection connection) {
        try { receiver.attach(connection, (ticks, sequence) -> playAnimation(connection.javaUuid(), ticks, sequence)); }
        catch (Exception e) { logger().error("Cooldown message adapter unavailable: " + e.getClass().getSimpleName()); }
    }
    public void playAnimation(UUID uuid, int ticks, long sequence) {
        if (!packReady || uuid == null || ticks < 1 || ticks > 200) return;
        var connection = GeyserApi.api().connectionByUuid(uuid);
        if (connection == null) return;
        long now = System.nanoTime();
        synchronized (stamps) {
            Stamp old = stamps.get(uuid);
            if (old != null && (old.sequence() == sequence || now - old.time() < TimeUnit.MILLISECONDS.toNanos(45))) return;
            stamps.put(uuid, new Stamp(sequence, now));
        }
        sender.send(connection, AnimationSelector.select(ticks),
            () -> logger().error("Unsupported Geyser packet API; animation disabled until restart."));
    }
    @Subscribe public void shutdown(GeyserShutdownEvent event) { receiver.close(); stamps.clear(); }
}
