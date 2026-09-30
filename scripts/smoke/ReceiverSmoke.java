package com.pexserver.cooldown;
import java.lang.reflect.*;
import java.nio.ByteBuffer;
import java.util.*;
import org.geysermc.geyser.api.connection.GeyserConnection;
import org.geysermc.mcprotocollib.network.Session;
import org.geysermc.mcprotocollib.network.packet.Packet;
import org.geysermc.mcprotocollib.network.event.session.SessionListener;
import org.geysermc.mcprotocollib.protocol.packet.common.clientbound.ClientboundCustomPayloadPacket;
import org.geysermc.mcprotocollib.protocol.packet.common.serverbound.ServerboundCustomPayloadPacket;
import net.kyori.adventure.key.Key;
public class ReceiverSmoke {
 public interface Bridge extends GeyserConnection { Downstream getDownstream(); void sendDownstreamPacket(Packet packet); }
 public static class Downstream { private final Session session; Downstream(Session s){session=s;} public Session getSession(){return session;} }
 public static void main(String[] args) throws Exception {
  List<SessionListener> listeners = new ArrayList<>();
  Session session = (Session) Proxy.newProxyInstance(ReceiverSmoke.class.getClassLoader(), new Class[]{Session.class},
   (p,m,a)-> { if(m.getName().equals("addListener")) listeners.add((SessionListener)a[0]); if(m.getName().equals("removeListener")) listeners.remove(a[0]); return null; });
  List<Packet> sent = new ArrayList<>();
  Bridge connection = (Bridge) Proxy.newProxyInstance(ReceiverSmoke.class.getClassLoader(), new Class[]{Bridge.class},
   (p,m,a)-> switch(m.getName()) { case "getDownstream" -> new Downstream(session); case "sendDownstreamPacket" -> {sent.add((Packet)a[0]); yield null;}
    case "hashCode" -> System.identityHashCode(p); case "equals" -> p==a[0]; default -> null; });
  JavaMessageReceiver receiver = new JavaMessageReceiver();
  List<Integer> received = new ArrayList<>();
  receiver.attach(connection,(ticks,sequence)-> { if(sequence!=42) throw new AssertionError(); received.add(ticks); });
  receiver.attach(connection,(ticks,sequence)-> {throw new AssertionError("duplicate");});
  if(listeners.size()!=1 || sent.size()!=1) throw new AssertionError("registration");
  ServerboundCustomPayloadPacket registration=(ServerboundCustomPayloadPacket)sent.get(0);
  if(!registration.getChannel().asString().equals("minecraft:register") || !new String(registration.getData(),java.nio.charset.StandardCharsets.UTF_8).equals(JavaMessageReceiver.CHANNEL)) throw new AssertionError("channel");
  SessionListener listener=listeners.get(0);
  byte[] valid=ByteBuffer.allocate(13).put((byte)1).putInt(13).putLong(42).array();
  listener.packetReceived(session,new ClientboundCustomPayloadPacket(Key.key(JavaMessageReceiver.CHANNEL),valid));
  listener.packetReceived(session,new ClientboundCustomPayloadPacket(Key.key("other:channel"),valid));
  listener.packetReceived(session,new ClientboundCustomPayloadPacket(Key.key(JavaMessageReceiver.CHANNEL),new byte[12]));
  byte[] bad=valid.clone(); bad[0]=2;
  listener.packetReceived(session,new ClientboundCustomPayloadPacket(Key.key(JavaMessageReceiver.CHANNEL),bad));
  bad=ByteBuffer.allocate(13).put((byte)1).putInt(201).putLong(42).array();
  listener.packetReceived(session,new ClientboundCustomPayloadPacket(Key.key(JavaMessageReceiver.CHANNEL),bad));
  if(!received.equals(List.of(13))) throw new AssertionError("payload validation");
  receiver.detach(connection); if(!listeners.isEmpty()) throw new AssertionError("detach");
  receiver.attach(connection,(t,s)->{}); receiver.close(); if(!listeners.isEmpty()) throw new AssertionError("shutdown");
  System.out.println("Receiver smoke passed: real Geyser packet classes, registration, duplicate attach, valid/invalid payloads, disconnect and shutdown.");
 }
}
