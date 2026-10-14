// Lab-only deterministic skin; never install this extension in production.
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.geysermc.event.subscribe.Subscribe;
import org.geysermc.geyser.api.event.bedrock.SessionSkinApplyEvent;
import org.geysermc.geyser.api.extension.Extension;
import org.geysermc.geyser.api.skin.Skin;
import org.geysermc.geyser.api.skin.SkinGeometry;

public final class VisualLabSkin implements Extension {
    private static final UUID TARGET = UUID.nameUUIDFromBytes(
        "OfflinePlayer:VisualProbe".getBytes(StandardCharsets.UTF_8));
    @Subscribe public void skin(SessionSkinApplyEvent event) {
        if (event.username().equals("VisualProbe"))
            logger().info("VisualProbe skin event: uuid=" + event.uuid() + "; bedrock=" + event.bedrock());
        if (event.bedrock() || !TARGET.equals(event.uuid()) || !event.username().equals("VisualProbe")) return;
        try (var stream = getClass().getResourceAsStream("/fixture.rgba")) {
            if (stream == null) throw new IOException("Missing lab skin");
            var bytes = stream.readAllBytes();
            if (bytes.length != 64 * 64 * 4) throw new IOException("Invalid lab skin size");
            String shape;
            try (var configuration = getClass().getResourceAsStream("/fixture.shape")) {
                shape = configuration == null ? "wide" : new String(configuration.readAllBytes(), StandardCharsets.UTF_8).trim();
            }
            if (!shape.equals("wide") && !shape.equals("slim")) throw new IOException("Invalid lab skin shape");
            // A fresh ID also prevents the Bedrock client from reusing an old
            // bitmap cached before the skin-apply override ran.
            event.skin(new Skin("visual-lab-fixed-" + shape + "-" + UUID.randomUUID(), bytes, false));
            event.geometry(shape.equals("slim") ? SkinGeometry.SLIM : SkinGeometry.WIDE);
            logger().info("Applied fixed " + shape + " lab skin to VisualProbe " + TARGET);
        } catch (IOException error) {
            throw new IllegalStateException("Deterministic lab skin failed", error);
        }
    }
}
