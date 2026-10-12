package com.pexserver.cooldown;

import org.cloudburstmc.protocol.bedrock.packet.AnimateEntityPacket;
import org.geysermc.geyser.api.connection.GeyserConnection;
import org.geysermc.geyser.session.GeyserSession;

import java.util.concurrent.atomic.AtomicBoolean;

/** Sends cooldown animations using the compile-time checked Geyser Core API. */
public final class BedrockPacketSender {
    private final AtomicBoolean unsupported = new AtomicBoolean();

    public boolean send(GeyserConnection connection, String animation, Runnable failure) {
        if (unsupported.get()) return false;
        if (!(connection instanceof GeyserSession session)) {
            fail(failure);
            return false;
        }
        try {
            session.executeInEventLoop(() -> {
                if (unsupported.get() || session.isClosed()) return;
                try {
                    AnimateEntityPacket packet = new AnimateEntityPacket();
                    packet.setAnimation(animation);
                    packet.setNextState("default");
                    packet.setStopExpression("query.any_animation_finished");
                    packet.setController("__geyser_cooldown");
                    packet.setBlendOutTime(0.0f);
                    packet.getRuntimeEntityIds().add(session.getPlayerEntity().geyserId());
                    session.sendUpstreamPacket(packet);
                } catch (LinkageError | RuntimeException e) {
                    fail(failure);
                }
            });
            return true;
        } catch (LinkageError | RuntimeException e) {
            fail(failure);
            return false;
        }
    }

    private void fail(Runnable failure) {
        if (unsupported.compareAndSet(false, true)) failure.run();
    }
}
