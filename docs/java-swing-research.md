# 過去のJavaスイング調査（現在の実装には不使用）

Java近似メイスは撤去し、現在はユーザー指定のOPTIONAL V1.4.0を使用します。以下は調査記録です。

# Java版の一人称スイング調査

対象: Java 1.21.11 の通常攻撃（WHACK）、右手。全Javaバージョン共通の保証ではありません。

## 調査元
- ItemInHandRenderer: https://github.com/H1lkaaaGD/Minecraft_1.21.11_Source/blob/main/net/minecraft/client/renderer/ItemInHandRenderer.java
- LivingEntity: https://github.com/H1lkaaaGD/Minecraft_1.21.11_Source/blob/main/net/minecraft/world/entity/LivingEntity.java
- SwingAnimation: https://github.com/H1lkaaaGD/Minecraft_1.21.11_Source/blob/main/net/minecraft/world/item/component/SwingAnimation.java
- Items（メイスは通常スイングの既定値）: https://github.com/H1lkaaaGD/Minecraft_1.21.11_Source/blob/main/net/minecraft/world/item/Items.java
上記は公開されている逆コンパイルソースのミラーであり、Mojang公式配布サイトではありません。
- Molangの角度単位: https://learn.microsoft.com/en-us/minecraft/creator/reference/content/molangreference/examples/molangconcepts/mathfunctions

## 通常攻撃
攻撃進行を p（0～1）とすると、Javaの移動量は以下です（ブロック単位）。
x = -0.4 sin(pi sqrt(p))
y = 0.2 sin(2 pi sqrt(p))
z = -0.2 sin(pi p)

回転は単純なXYZ角度の足し算ではなく、
Ry(45 - 20 sin(pi p²)) → Rz(-20 sin(pi sqrt(p))) →
Rx(-80 sin(pi sqrt(p))) → Ry(-45)
の順に行列を乗算します。スイングの既定時間は6tick（20TPSで0.3秒）。
LivingEntityは一定以上スイングが進んだ場合に再開始し、採掘速度/採掘疲労でも時間が変わります。

## 手の高さとクールダウン
ItemInHandRenderer.tickは手の目標高さに回復係数の3乗を用い、
1tickの変化量を±0.4に制限し、描画フレーム間で補間します。
この処理は通常スイングの進行とは独立です。現在のサーバー駆動の
スイング後に0.125秒で下げる線形クールダウンは、このJava計算の完全再現ではありません。

## 今回の変更
- 剣: 好みのCrossplay 1.0を維持。
- 斧・トライデント: Crossplay 2.0を採用。
- メイス: Javaの平方根・正弦の移動曲線と回転振幅をMolangへ移植。
  既存の腕変換と同じ40モデル単位/ブロックを用い、深さの符号を変換。
  回転は右腕の単一Eulerボーンへの近似であり、上記の行列積を完全には再現しない。
- Bedrockのvariable.attack_timeを使用するため、animation_length=0.3だけでは
  Bedrock側の実際のスイング時間を6tickへ強制できない。
- 既存の持ち方、FOV、揺れ、エンチャント、攻撃力回復演出は維持。
- ツルハシ・hoe・シャベルの除外、連打の再送制限は維持。

## 完全一致に必要な追加作業
Javaのカメラ座標→Bedrockの腕・アイテム座標の基底変換、回転順序、
ピボット、手持ちモデルの表示変換、FOVを合わせる必要があります。
また実際のJava/Bedrockクライアントで同じFOV・同じ武器・同じ攻撃条件を
撮影し、時間軸とアイテム先端の軌道を比較する必要があります。
現時点では実機比較していないため「Javaと同じ見た目」とは扱いません。

追加修正: 開始直後のスイング区間はサーバー駆動オフセット0、回復時の深さは8モデル単位に制限。回復をattack_timeで隠す条件は撤去。Javaの手の高さ計算と完全一致ではありませんが、スイングを隠す二重加算を避けます。
