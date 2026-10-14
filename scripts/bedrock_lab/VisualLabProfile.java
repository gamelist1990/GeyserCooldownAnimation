// Dedicated offline lab only. Supplies a real texture property before spawn.
import com.destroystokyo.paper.profile.ProfileProperty;
import java.nio.charset.StandardCharsets;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerPreLoginEvent;
import org.bukkit.plugin.java.JavaPlugin;

public final class VisualLabProfile extends JavaPlugin implements Listener {
    private String value, signature;
    @Override public void onEnable() {
        try {
            if (getServer().getPort() != 25572 || !getServer().getIp().equals("127.0.0.1"))
                throw new IllegalStateException("VisualLabProfile only supports the isolated lab");
            try (var input = getResource("profile.value"); var signed = getResource("profile.signature")) {
                if (input == null || signed == null) throw new IllegalStateException("Missing public profile property");
                value = new String(input.readAllBytes(), StandardCharsets.UTF_8);
                signature = new String(signed.readAllBytes(), StandardCharsets.UTF_8);
            }
            getServer().getPluginManager().registerEvents(this, this);
        } catch (Exception error) { throw new IllegalStateException("Lab profile setup failed", error); }
    }
    @EventHandler(priority = EventPriority.HIGHEST)
    public void profile(AsyncPlayerPreLoginEvent event) {
        if (!event.getName().equals("VisualProbe")) return;
        var profile = event.getPlayerProfile();
        // A public, signed Mojang property enables the normal skin path. The
        // Geyser lab extension then replaces its bitmap with our synthetic skin.
        profile.setProperty(new ProfileProperty("textures", value, signature));
        event.setPlayerProfile(profile);
        getLogger().info("Pinned VisualProbe texture profile in the isolated lab");
    }
}
