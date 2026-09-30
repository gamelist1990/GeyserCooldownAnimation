package com.pexserver.cooldown;
import com.sun.net.httpserver.HttpServer;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.GeyserApi;
import org.geysermc.geyser.api.event.lifecycle.*;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.pack.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
public final class GeyserCooldownAnimationExtension implements Extension {
    private HttpServer server;
    private ExecutorService executor;
    private byte[] token;
    private boolean packReady;
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
    @Subscribe public void start(GeyserPostInitializeEvent event) {
        if (server != null || !packReady) return;
        try {
            Path path = dataFolder().resolve("bridge.properties");
            Properties config = new Properties();
            if (Files.exists(path)) try (InputStream in = Files.newInputStream(path)) { config.load(in); }
            if (!config.containsKey("token")) {
                config.setProperty("token", UUID.randomUUID().toString() + UUID.randomUUID());
                config.setProperty("port", "28765");
                try (OutputStream out = Files.newOutputStream(path)) { config.store(out, "Copy token to Paper bridge config; loopback only."); }
            }
            token = config.getProperty("token").getBytes(StandardCharsets.UTF_8);
            if (token.length < 32) throw new IllegalArgumentException("Token must have at least 32 characters");
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", Integer.parseInt(config.getProperty("port", "28765"))), 16);
            executor = new ThreadPoolExecutor(2, 2, 0, TimeUnit.SECONDS, new ArrayBlockingQueue<>(64),
                    r -> { Thread t = new Thread(r, "geyser-cooldown-bridge"); t.setDaemon(true); return t; },
                    new ThreadPoolExecutor.AbortPolicy());
            server.setExecutor(executor);
            server.createContext("/v1/attack", exchange -> {
                int status = 400;
                try {
                    String auth = exchange.getRequestHeaders().getFirst("Authorization");
                    if (!"POST".equals(exchange.getRequestMethod()) || !"/v1/attack".equals(exchange.getRequestURI().getPath())) status = 405;
                    else if (auth == null || !MessageDigest.isEqual(token, auth.getBytes(StandardCharsets.UTF_8))) status = 401;
                    else {
                        byte[] body = exchange.getRequestBody().readNBytes(29);
                        if (body.length == 28) {
                            DataInputStream in = new DataInputStream(new ByteArrayInputStream(body));
                            UUID uuid = new UUID(in.readLong(), in.readLong());
                            int ticks = in.readInt();
                            long sequence = in.readLong();
                            String animation = AnimationSelector.select(ticks);
                            var connection = GeyserApi.api().connectionByUuid(uuid);
                            if (connection == null) status = 204;
                            else {
                                long now = System.nanoTime();
                                stamps.entrySet().removeIf(e -> now - e.getValue().time() > TimeUnit.MINUTES.toNanos(1));
                                synchronized (stamps) {
                                Stamp old = stamps.get(uuid);
                                if (old != null && (old.sequence() == sequence || now - old.time() < TimeUnit.MILLISECONDS.toNanos(45))) status = 204;
                                else {
                                    stamps.put(uuid, new Stamp(sequence, now));
                                    status = sender.send(connection, animation,
                                            () -> logger().error("Unsupported Geyser packet API; animation disabled until restart.")) ? 202 : 503;
                                }
                                }
                            }
                        }
                    }
                } catch (Exception e) { status = 400; }
                finally { exchange.sendResponseHeaders(status, -1); exchange.close(); }
            });
            server.start();
            logger().info("Cooldown animation bridge listening on 127.0.0.1:" + server.getAddress().getPort());
        } catch (Exception e) { stop(); logger().error("Cooldown bridge disabled: " + e.getMessage()); }
    }
    @Subscribe public void shutdown(GeyserShutdownEvent event) { stop(); }
    private void stop() {
        if (server != null) { server.stop(0); server = null; }
        if (executor != null) { executor.shutdownNow(); executor = null; }
        stamps.clear();
    }
}
