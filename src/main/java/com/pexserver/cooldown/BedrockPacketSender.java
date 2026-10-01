package com.pexserver.cooldown;

import org.geysermc.geyser.api.connection.GeyserConnection;
import org.geysermc.geyser.session.GeyserSession;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/** Compile-time checked Geyser session integration; no reflective access. */
public final class BedrockPacketSender {
    private final AtomicBoolean unsupported = new AtomicBoolean();
    private final AtomicBoolean loggedSend = new AtomicBoolean();

    public boolean send(GeyserConnection connection, String animation, Consumer<String> diagnostic) {
        if (unsupported.get()) return false;
        if (!(connection instanceof GeyserSession session)) {
            fail("Unsupported Geyser connection type: " + connection.getClass().getName(), diagnostic);
            return false;
        }
        try {
            session.executeInEventLoop(() -> {
                if (unsupported.get() || session.isClosed() || !session.isSpawned()
                        || !session.getUpstream().isInitialized()) return;
                try {
                    long runtime = session.getPlayerEntity().geyserId();
                    var upstream = session.getUpstream();
                    var packet = AnimationPacketFactory.create(upstream.getSession().getCodec(),
                            upstream.getCodecHelper(), animation, runtime);
                    session.sendUpstreamPacket(packet);
                    if (loggedSend.compareAndSet(false, true)) {
                        diagnostic.accept("Sent first cooldown animation packet: " + animation
                                + ", runtimeEntityId=" + runtime + ".");
                    }
                } catch (LinkageError | RuntimeException e) {
                    fail("Cooldown animation packet send failed: " + e.getClass().getSimpleName()
                            + ": " + e.getMessage(), diagnostic);
                }
            });
            return true;
        } catch (LinkageError | RuntimeException e) {
            fail("Cooldown animation scheduling failed: " + e.getClass().getSimpleName()
                    + ": " + e.getMessage(), diagnostic);
            return false;
        }
    }

    private void fail(String message, Consumer<String> diagnostic) {
        if (unsupported.compareAndSet(false, true)) diagnostic.accept(message);
    }
}
