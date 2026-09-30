package com.pexserver.cooldown;
import org.geysermc.geyser.api.connection.GeyserConnection;
import java.lang.reflect.Method;
import java.util.Collection;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;
/** All unstable Geyser/Cloudburst access is confined to this adapter. */
public final class BedrockPacketSender {
    private volatile boolean unsupported;
    private final AtomicBoolean loggedSend = new AtomicBoolean();
    public boolean send(GeyserConnection connection, String animation, Consumer<String> diagnostic) {
        if (unsupported) return false;
        try {
            Method schedule = connection.getClass().getMethod("executeInEventLoop", Runnable.class);
            schedule.invoke(connection, (Runnable) () -> {
                try {
                    if ((boolean) connection.getClass().getMethod("isClosed").invoke(connection)) return;
                    Object entity = connection.getClass().getMethod("getPlayerEntity").invoke(connection);
                    Method id;
                    try { id = entity.getClass().getMethod("geyserId"); }
                    catch (NoSuchMethodException e) { id = entity.getClass().getMethod("getGeyserId"); }
                    long runtime = ((Number) id.invoke(entity)).longValue();
                    ClassLoader loader = connection.getClass().getClassLoader();
                    Class<?> type = Class.forName("org.cloudburstmc.protocol.bedrock.packet.AnimateEntityPacket", true, loader);
                    Object packet = type.getConstructor().newInstance();
                    type.getMethod("setAnimation", String.class).invoke(packet, animation);
                    type.getMethod("setNextState", String.class).invoke(packet, "default");
                    type.getMethod("setStopExpression", String.class).invoke(packet, "query.any_animation_finished");
                    type.getMethod("setStopExpressionVersion", int.class).invoke(packet, 0);
                    type.getMethod("setController", String.class).invoke(packet, "geyser_cooldown_timing");
                    type.getMethod("setBlendOutTime", float.class).invoke(packet, 0.0f);
                    @SuppressWarnings("unchecked")
                    Collection<Long> ids = (Collection<Long>) type.getMethod("getRuntimeEntityIds").invoke(packet);
                    ids.add(runtime);
                    Class<?> base = Class.forName("org.cloudburstmc.protocol.bedrock.packet.BedrockPacket", true, loader);
                    connection.getClass().getMethod("sendUpstreamPacket", base).invoke(connection, packet);
                    if (loggedSend.compareAndSet(false, true)) {
                        diagnostic.accept("Sent first cooldown animation packet: " + animation + ", runtimeEntityId=" + runtime + ".");
                    }
                } catch (ReflectiveOperationException | LinkageError | RuntimeException e) {
                    if (!unsupported) {
                        unsupported = true;
                        diagnostic.accept("Cooldown animation packet send failed: " + e.getClass().getSimpleName() + ": " + e.getMessage());
                    }
                }
            });
            return true;
        } catch (ReflectiveOperationException | LinkageError | RuntimeException e) {
            if (!unsupported) {
                unsupported = true;
                diagnostic.accept("Cooldown animation scheduling failed: " + e.getClass().getSimpleName() + ": " + e.getMessage());
            }
            return false;
        }
    }
}
