package com.pexserver.cooldown.paper;
import org.bukkit.Bukkit;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import org.bukkit.event.block.Action;
import org.bukkit.plugin.java.JavaPlugin;
import io.papermc.paper.event.player.PrePlayerAttackEntityEvent;
import java.nio.ByteBuffer;
import java.util.*;

public final class CooldownBridge extends JavaPlugin implements Listener {
    private static final String CHANNEL = "geyser_cooldown:attack";
    private final Map<UUID, Integer> lastTick = new HashMap<>();
    @Override public void onEnable() {
        Bukkit.getMessenger().registerOutgoingPluginChannel(this, CHANNEL);
        Bukkit.getPluginManager().registerEvents(this, this);
        getLogger().info("Cooldown animation bridge enabled; no configuration required.");
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void attack(PrePlayerAttackEntityEvent event) { submit(event.getPlayer()); }
    @EventHandler(priority = EventPriority.MONITOR)
    public void miss(PlayerInteractEvent event) {
        if (event.getAction() == Action.LEFT_CLICK_AIR) submit(event.getPlayer());
    }
    @EventHandler public void quit(PlayerQuitEvent event) { lastTick.remove(event.getPlayer().getUniqueId()); }
    private void submit(Player player) {
        if (!player.getListeningPluginChannels().contains(CHANNEL)) return;
        int tick = Bukkit.getCurrentTick();
        if (Objects.equals(lastTick.put(player.getUniqueId(), tick), tick)) return;
        var speed = player.getAttribute(Attribute.ATTACK_SPEED);
        if (speed == null || !Double.isFinite(speed.getValue()) || speed.getValue() <= 0) return;
        int ticks = (int) Math.max(1, Math.min(200, Math.ceil(20.0 / speed.getValue())));
        byte[] body = ByteBuffer.allocate(13).put((byte) 1).putInt(ticks).putLong(tick).array();
        player.sendPluginMessage(this, CHANNEL, body);
    }
    @Override public void onDisable() {
        Bukkit.getMessenger().unregisterOutgoingPluginChannel(this);
        lastTick.clear();
    }
}
