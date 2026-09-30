package com.pexserver.cooldown;

import org.geysermc.geyser.api.connection.GeyserConnection;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

final class JavaMessageReceiver {
    static final String CHANNEL = "geyser_cooldown:attack";
    private final Map<GeyserConnection, Runnable> removers = new HashMap<>();

    synchronized void attach(GeyserConnection connection, java.util.function.BiConsumer<Integer, Long> receive) throws Exception {
        if (removers.containsKey(connection)) return;
        ClassLoader loader = connection.getClass().getClassLoader();
        Object downstream = connection.getClass().getMethod("getDownstream").invoke(connection);
        Object session = downstream.getClass().getMethod("getSession").invoke(downstream);
        Class<?> sessionType = Class.forName("org.geysermc.mcprotocollib.network.Session", true, loader);
        Class<?> listenerType = Class.forName("org.geysermc.mcprotocollib.network.event.session.SessionListener", true, loader);
        Class<?> payloadType = Class.forName("org.geysermc.mcprotocollib.protocol.packet.common.clientbound.ClientboundCustomPayloadPacket", true, loader);
        Object listener = Proxy.newProxyInstance(loader, new Class<?>[]{listenerType}, (proxy, method, args) -> {
            if (method.getDeclaringClass() == Object.class) {
                return switch (method.getName()) {
                    case "hashCode" -> System.identityHashCode(proxy);
                    case "equals" -> proxy == args[0];
                    default -> "GeyserCooldownMessageReceiver";
                };
            }
            if (method.getName().equals("packetReceived") && payloadType.isInstance(args[1])) {
                Object packet = args[1];
                if (CHANNEL.equals(payloadType.getMethod("getChannel").invoke(packet).toString())) {
                    byte[] data = (byte[]) payloadType.getMethod("getData").invoke(packet);
                    if (data.length == 13 && data[0] == 1) {
                        java.nio.ByteBuffer buffer = java.nio.ByteBuffer.wrap(data);
                        buffer.get();
                        int ticks = buffer.getInt();
                        long sequence = buffer.getLong();
                        if (ticks >= 1 && ticks <= 200) receive.accept(ticks, sequence);
                    }
                }
            }
            return null;
        });
        sessionType.getMethod("addListener", listenerType).invoke(session, listener);
        removers.put(connection, () -> {
            try { sessionType.getMethod("removeListener", listenerType).invoke(session, listener); }
            catch (ReflectiveOperationException ignored) {}
        });
        try {
            Class<?> keyType = Class.forName("net.kyori.adventure.key.Key", true, loader);
            Object key = keyType.getMethod("key", String.class).invoke(null, "minecraft:register");
            Class<?> registerType = Class.forName("org.geysermc.mcprotocollib.protocol.packet.common.serverbound.ServerboundCustomPayloadPacket", true, loader);
            Object register = registerType.getConstructor(keyType, byte[].class)
                .newInstance(key, CHANNEL.getBytes(StandardCharsets.UTF_8));
            Class<?> packetType = Class.forName("org.geysermc.mcprotocollib.network.packet.Packet", true, loader);
            connection.getClass().getMethod("sendDownstreamPacket", packetType).invoke(connection, register);
        } catch (Exception e) { detach(connection); throw e; }
    }
    synchronized void detach(GeyserConnection connection) {
        Runnable remove = removers.remove(connection);
        if (remove != null) remove.run();
    }
    synchronized void close() {
        removers.values().forEach(Runnable::run);
        removers.clear();
    }
}
