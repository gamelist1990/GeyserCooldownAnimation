// Offline Java-side player fixture for the dedicated local visual lab only.
// Uses the same MCProtocolLib classes bundled in the installed Geyser JAR.
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.geysermc.mcprotocollib.network.Session;
import org.geysermc.mcprotocollib.network.event.session.SessionAdapter;
import org.geysermc.mcprotocollib.network.event.session.DisconnectedEvent;
import org.geysermc.mcprotocollib.network.factory.ClientNetworkSessionFactory;
import org.geysermc.mcprotocollib.network.packet.Packet;
import org.geysermc.mcprotocollib.protocol.MinecraftProtocol;
import org.geysermc.mcprotocollib.auth.GameProfile;
import org.geysermc.mcprotocollib.protocol.data.ProtocolState;
import org.geysermc.mcprotocollib.protocol.data.game.entity.player.PositionElement;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.entity.player.ClientboundPlayerPositionPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.ServerboundClientTickEndPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.ServerboundPlayerLoadedPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.level.ServerboundAcceptTeleportationPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.level.ServerboundPlayerInputPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.serverbound.player.ServerboundMovePlayerPosRotPacket;
import org.geysermc.mcprotocollib.protocol.packet.ingame.clientbound.ClientboundPlayerInfoUpdatePacket;

public class VisualProbe {
    private static double x, y, z;
    private static float yaw, pitch;
    private static double velocityX, velocityZ;
    private static double motionLimit, anchorX, anchorZ;
    private static boolean ready, shift, jump;
    private static double velocityY, floorY = 60;

    public static void main(String[] args) throws Exception {
        var id = UUID.nameUUIDFromBytes("OfflinePlayer:VisualProbe".getBytes(StandardCharsets.UTF_8));
        var protocol = new MinecraftProtocol(new GameProfile(id, "VisualProbe"), null);
        System.out.println("Local fixture profile: " + id);
        var session = ClientNetworkSessionFactory.factory()
            .setAddress("127.0.0.1", 25572).setProtocol(protocol).create();
        var timer = Executors.newSingleThreadScheduledExecutor();
        session.addListener(new SessionAdapter() {
            @Override public void packetReceived(Session s, Packet packet) {
                if (packet instanceof ClientboundPlayerInfoUpdatePacket info) {
                    for (var entry : info.getEntries()) {
                        var profile = entry.getProfile();
                        if (profile != null && "VisualProbe".equals(profile.getName())) {
                            boolean hasTexture = profile.getProperties().stream().anyMatch(p -> p.getName().equals("textures"));
                            System.out.println("VisualProbe received profile " + entry.getProfileId() + "; texture_property=" + hasTexture);
                        }
                    }
                }
                if (packet instanceof ClientboundPlayerPositionPacket position) {
                    synchronized (VisualProbe.class) {
                        var relative = position.getRelatives();
                        x = position.getPosition().getX() + (relative.contains(PositionElement.X) ? x : 0);
                        y = position.getPosition().getY() + (relative.contains(PositionElement.Y) ? y : 0);
                        z = position.getPosition().getZ() + (relative.contains(PositionElement.Z) ? z : 0);
                        floorY = y; velocityY = 0;
                        yaw = position.getYRot() + (relative.contains(PositionElement.Y_ROT) ? yaw : 0);
                        pitch = position.getXRot() + (relative.contains(PositionElement.X_ROT) ? pitch : 0);
                        s.send(new ServerboundAcceptTeleportationPacket(position.getId(), x, y, z, yaw, pitch));
                        if (!ready) {
                            s.send(ServerboundPlayerLoadedPacket.INSTANCE);
                            System.out.println("VisualProbe ready in the local lab");
                        }
                        ready = true;
                    }
                }
            }
            @Override public void disconnected(DisconnectedEvent event) {
                System.out.println("VisualProbe disconnected: " + event.getReason());
                timer.shutdownNow();
            }
        });
        session.connect(true);
        timer.scheduleAtFixedRate(() -> {
            synchronized (VisualProbe.class) {
                if (!ready || !session.isConnected() || protocol.getOutboundState() != ProtocolState.GAME) return;
                x += velocityX; z += velocityZ;
                boolean grounded = y <= floorY;
                if (jump && grounded) velocityY = 0.42;
                if (velocityY != 0 || !grounded) {
                    y += velocityY; velocityY = (velocityY - 0.08) * 0.98;
                    if (y <= floorY) { y = floorY; velocityY = 0; }
                }
                grounded = y <= floorY;
                if (motionLimit > 0) {
                    x = Math.clamp(x, anchorX - motionLimit, anchorX + motionLimit);
                    z = Math.clamp(z, anchorZ - motionLimit, anchorZ + motionLimit);
                }
                session.send(new ServerboundPlayerInputPacket(velocityZ < 0, velocityZ > 0,
                    velocityX > 0, velocityX < 0, jump, shift, false));
                session.send(new ServerboundMovePlayerPosRotPacket(grounded, false, x, y, z, yaw, pitch));
                session.send(ServerboundClientTickEndPacket.INSTANCE);
            }
        }, 0, 50, TimeUnit.MILLISECONDS);
        System.out.println("Local fixture only. Commands: pose <yaw> <pitch>, move <dx/tick> <dz/tick>, shift <true|false>, jump <true|false>, bounds <radius>, quit");
        try (var input = new BufferedReader(new InputStreamReader(System.in))) {
            for (String line; (line = input.readLine()) != null;) {
                var fields = line.trim().split("\\s+");
                if (fields[0].equals("quit")) break;
                synchronized (VisualProbe.class) {
                    if (fields.length == 3 && fields[0].equals("pose")) {
                        float nextYaw = Float.parseFloat(fields[1]);
                        float nextPitch = Float.parseFloat(fields[2]);
                        if (!Float.isFinite(nextYaw) || !Float.isFinite(nextPitch) || Math.abs(nextPitch) > 90)
                            throw new IllegalArgumentException("Invalid pose");
                        yaw = nextYaw; pitch = nextPitch;
                    } else if (fields.length == 3 && fields[0].equals("move")) {
                        double nextX = Double.parseDouble(fields[1]), nextZ = Double.parseDouble(fields[2]);
                        if (!Double.isFinite(nextX) || !Double.isFinite(nextZ) || Math.abs(nextX) > 0.25 || Math.abs(nextZ) > 0.25)
                            throw new IllegalArgumentException("Invalid motion");
                        velocityX = nextX; velocityZ = nextZ;
                    } else if (fields.length == 2 && fields[0].equals("jump")) {
                        jump = Boolean.parseBoolean(fields[1]);
                    } else if (fields.length == 2 && fields[0].equals("shift")) {
                        shift = Boolean.parseBoolean(fields[1]);
                    } else if (fields.length == 2 && fields[0].equals("bounds")) {
                        double radius = Double.parseDouble(fields[1]);
                        if (!Double.isFinite(radius) || radius < 0 || radius > 8)
                            throw new IllegalArgumentException("Invalid motion bounds");
                        motionLimit = radius; anchorX = x; anchorZ = z;
                    } else System.out.println("Unknown fixture command");
                }
            }
        } finally {
            timer.shutdownNow();
            session.disconnect("Visual lab fixture stopped");
        }
    }
}
