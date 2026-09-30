package com.pexserver.cooldown;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import org.geysermc.geyser.api.connection.GeyserConnection;
import org.geysermc.geyser.session.GeyserSession;
import org.geysermc.mcprotocollib.network.Session;
import org.geysermc.mcprotocollib.network.event.session.SessionAdapter;
import org.geysermc.mcprotocollib.network.packet.Packet;
import org.geysermc.mcprotocollib.protocol.packet.common.clientbound.ClientboundCustomPayloadPacket;
import org.geysermc.mcprotocollib.protocol.packet.common.serverbound.ServerboundCustomPayloadPacket;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.Consumer;
import java.util.concurrent.atomic.AtomicBoolean;

final class JavaMessageReceiver {
    static final String CHANNEL = "geyser_cooldown:attack";
    private final Map<GeyserConnection, Registration> registrations = new HashMap<>();
    private final AtomicBoolean loggedPayload = new AtomicBoolean();

    synchronized void attach(GeyserConnection connection, BiConsumer<Integer, Long> receive, Consumer<String> diagnostic) {
        if (registrations.containsKey(connection)) return;
        if (!(connection instanceof GeyserSession geyserSession)) {
            throw new IllegalStateException("Unsupported Geyser connection type: " + connection.getClass().getName());
        }

        Session session = geyserSession.getDownstream().getSession();
        SessionAdapter listener = new SessionAdapter() {
            @Override
            public void packetReceived(Session session, Packet packet) {
                if (!(packet instanceof ClientboundCustomPayloadPacket payload)) return;
                ByteBuf encoded = Unpooled.buffer();
                try {
                    payload.serialize(encoded);
                    if (!CHANNEL.equals(readProtocolString(encoded))) return;
                    if (loggedPayload.compareAndSet(false, true)) {
                        diagnostic.accept("Received Paper plugin message on " + CHANNEL + ".");
                    }
                    if (encoded.readableBytes() != 13 || encoded.readUnsignedByte() != 1) return;
                    int ticks = encoded.readInt();
                    long sequence = encoded.readLong();
                    if (ticks >= 1 && ticks <= 200) {
                        receive.accept(ticks, sequence);
                    } else {
                        diagnostic.accept("Rejected cooldown message with invalid ticks: " + ticks);
                    }
                } finally {
                    encoded.release();
                }
            }
        };

        session.addListener(listener);
        try {
            ByteBuf payload = Unpooled.buffer();
            Packet register;
            try {
                writeProtocolString(payload, "minecraft:register");
                payload.writeBytes(CHANNEL.getBytes(StandardCharsets.UTF_8));
                register = new ServerboundCustomPayloadPacket(payload);
            } finally {
                payload.release();
            }
            geyserSession.sendDownstreamPacket(register);
            registrations.put(connection, new Registration(session, listener));
            diagnostic.accept("Attached Java message receiver and registered " + CHANNEL + " for " + connection.javaUuid() + ".");
        } catch (RuntimeException exception) {
            session.removeListener(listener);
            throw exception;
        }
    }

    private static void writeProtocolString(ByteBuf buffer, String value) {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        int length = bytes.length;
        while ((length & ~0x7F) != 0) {
            buffer.writeByte((length & 0x7F) | 0x80);
            length >>>= 7;
        }
        buffer.writeByte(length);
        buffer.writeBytes(bytes);
    }

    private static String readProtocolString(ByteBuf buffer) {
        int length = 0;
        int position = 0;
        byte current;
        do {
            if (position == 5 || !buffer.isReadable()) throw new IllegalArgumentException("Invalid protocol string length");
            current = buffer.readByte();
            length |= (current & 0x7F) << (position++ * 7);
        } while ((current & 0x80) != 0);
        if (length < 0 || length > buffer.readableBytes()) throw new IllegalArgumentException("Invalid protocol string length");
        byte[] bytes = new byte[length];
        buffer.readBytes(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }

    synchronized void detach(GeyserConnection connection) {
        Registration registration = registrations.remove(connection);
        if (registration != null) registration.session().removeListener(registration.listener());
    }

    synchronized void close() {
        registrations.values().forEach(registration -> registration.session().removeListener(registration.listener()));
        registrations.clear();
    }

    private record Registration(Session session, SessionAdapter listener) {}
}
