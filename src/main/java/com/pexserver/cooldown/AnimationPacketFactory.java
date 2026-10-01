package com.pexserver.cooldown;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import org.cloudburstmc.protocol.bedrock.codec.BedrockCodec;
import org.cloudburstmc.protocol.bedrock.codec.BedrockCodecHelper;
import org.cloudburstmc.protocol.bedrock.packet.AnimateEntityPacket;
import org.cloudburstmc.protocol.common.util.VarInts;

/** Build with the installed codec, avoiding platform-shaded collection return types. */
final class AnimationPacketFactory {
    private AnimationPacketFactory() { }

    static AnimateEntityPacket create(BedrockCodec codec, BedrockCodecHelper helper,
                                       String animation, long runtimeEntityId) {
        if (codec.getProtocolVersion() < 465) {
            throw new IllegalArgumentException("Cooldown requires Bedrock protocol 465 or later");
        }
        var definition = codec.getPacketDefinition(AnimateEntityPacket.class);
        if (definition == null) throw new IllegalStateException("AnimateEntityPacket is not supported");
        ByteBuf buffer = Unpooled.buffer();
        try {
            // AnimateEntity's v465 body is unchanged in supported modern codecs.
            // The runtime serializer populates its own collection, including on Spigot
            // where fastutil is relocated and a direct getter call would fail to link.
            helper.writeString(buffer, animation);
            helper.writeString(buffer, "default");
            helper.writeString(buffer, "query.any_animation_finished");
            buffer.writeIntLE(0);
            helper.writeString(buffer, "geyser_cooldown_timing");
            buffer.writeFloatLE(0f);
            VarInts.writeUnsignedInt(buffer, 1);
            VarInts.writeUnsignedLong(buffer, runtimeEntityId);
            var packet = definition.getFactory().get();
            definition.getSerializer().deserialize(buffer, helper, packet);
            if (buffer.isReadable()) throw new IllegalStateException("Unexpected animation packet format");
            return packet;
        } finally {
            buffer.release();
        }
    }
}
