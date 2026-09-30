package com.pexserver.cooldown.paper;
import org.bukkit.Bukkit;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import org.bukkit.event.block.Action;
import org.bukkit.plugin.java.JavaPlugin;
import io.papermc.paper.event.player.PrePlayerAttackEntityEvent;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
public final class CooldownBridge extends JavaPlugin implements Listener {
    private ExecutorService worker;
    private URI endpoint;
    private String token;
    private final Map<UUID, Integer> lastTick = new HashMap<>();
    private volatile long lastWarning;
    @Override public void onEnable() {
        saveDefaultConfig();
        token = getConfig().getString("token", "");
        try {
            endpoint = URI.create(getConfig().getString("endpoint", ""));
            if (!"http".equals(endpoint.getScheme()) || !"127.0.0.1".equals(endpoint.getHost())) throw new IllegalArgumentException("Only loopback HTTP is supported");
            if (token.length() < 32) throw new IllegalArgumentException("Copy the extension token into config.yml, then restart");
        } catch (Exception e) { getLogger().warning(e.getMessage()); Bukkit.getPluginManager().disablePlugin(this); return; }
        worker = new ThreadPoolExecutor(1, 1, 0, TimeUnit.SECONDS, new ArrayBlockingQueue<>(64),
                r -> { Thread t = new Thread(r, "geyser-cooldown-paper"); t.setDaemon(true); return t; },
                new ThreadPoolExecutor.AbortPolicy());
        Bukkit.getPluginManager().registerEvents(this, this);
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void attack(PrePlayerAttackEntityEvent event) { submit(event.getPlayer()); }
    @EventHandler(priority = EventPriority.MONITOR)
    public void miss(PlayerInteractEvent event) {
        if (event.getAction() == Action.LEFT_CLICK_AIR) submit(event.getPlayer());
    }
    @EventHandler public void quit(PlayerQuitEvent event) { lastTick.remove(event.getPlayer().getUniqueId()); }
    private void submit(Player player) {
        int tick = Bukkit.getCurrentTick();
        UUID uuid = player.getUniqueId();
        if (Objects.equals(lastTick.put(uuid, tick), tick)) return;
        var speed = player.getAttribute(Attribute.ATTACK_SPEED);
        if (speed == null || !Double.isFinite(speed.getValue()) || speed.getValue() <= 0) return;
        int ticks = (int) Math.max(1, Math.min(200, Math.ceil(20.0 / speed.getValue())));
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream(28);
            DataOutputStream out = new DataOutputStream(bytes);
            out.writeLong(uuid.getMostSignificantBits()); out.writeLong(uuid.getLeastSignificantBits());
            out.writeInt(ticks); out.writeLong(tick);
            byte[] body = bytes.toByteArray();
            long queued = System.nanoTime();
            worker.execute(() -> { if (System.nanoTime() - queued < TimeUnit.MILLISECONDS.toNanos(200)) send(body); });
        } catch (IOException | RejectedExecutionException e) { warn(); }
    }
    private void send(byte[] body) {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) endpoint.toURL().openConnection();
            connection.setConnectTimeout(500); connection.setReadTimeout(500);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestMethod("POST"); connection.setDoOutput(true);
            connection.setFixedLengthStreamingMode(body.length);
            connection.setRequestProperty("Authorization", token);
            connection.setRequestProperty("Content-Type", "application/octet-stream");
            try (OutputStream out = connection.getOutputStream()) { out.write(body); }
            int status = connection.getResponseCode();
            if (status != 202 && status != 204) warn();
        } catch (IOException e) { warn(); }
        finally { if (connection != null) connection.disconnect(); }
    }
    private void warn() {
        long now = System.currentTimeMillis();
        if (now - lastWarning > 30000) { lastWarning = now; getLogger().warning("Cooldown bridge unavailable; check extension and token configuration."); }
    }
    @Override public void onDisable() {
        if (worker != null) worker.shutdownNow();
        lastTick.clear();
    }
}
