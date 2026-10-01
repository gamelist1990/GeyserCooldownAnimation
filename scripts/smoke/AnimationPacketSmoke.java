package com.pexserver.cooldown;

import io.netty.buffer.Unpooled;
import org.cloudburstmc.protocol.bedrock.codec.v748.Bedrock_v748;

/** Compile against the actual Spigot JAR to check its relocated runtime types. */
public final class AnimationPacketSmoke {
    public static void main(String[] args) throws Exception {
        var codec = Bedrock_v748.CODEC;
        var helper = codec.createHelper();
        for (int ticks = 1; ticks <= 200; ticks++) {
            String name = "animation.player.cooldown_tick_" + ticks;
            long id = 0x1_0000_0000L + ticks;
            var packet = AnimationPacketFactory.create(codec, helper, name, id);
            if (!packet.getAnimation().equals(name) || packet.getRuntimeEntityIds().size() != 1
                    || packet.getRuntimeEntityIds().getLong(0) != id) throw new AssertionError("Packet fields");
            var bytes = Unpooled.buffer();
            try {
                codec.tryEncode(helper, bytes, packet);
                var copy = codec.tryDecode(helper, bytes, codec.getPacketDefinition(packet.getClass()).getId());
                if (!copy.equals(packet) || bytes.isReadable()) throw new AssertionError("Codec round-trip");
            } finally { bytes.release(); }
        }
        System.out.println("PASS: 200 packet round-trips using the installed Spigot codec, without reflection.");
    }
}
