# ローカルJava 26.3.jarの調査結果

対象: C:\Users\PC_User\AppData\Roaming\.minecraft\versions\26.3\26.3.jar
SHA-256: 4508d006323f24fa02876310c192d739af56516eb259000ac50f0909a68c9a2d
jar内version.json: id=26.3 / Java 25 / build_time=2026-09-15T11:20:48+00:00

Vineflower 1.12.0で対象classのみ逆コンパイル。
生成ソースはbuild/swing-research/source内（cleanで消える調査用ファイル）。
enum switchの補助class不足について警告が出たため、switchのラベルは断定しません。
以下の数式メソッドにはその警告は出ていません。

## 読んだ実装
- FirstPersonHandsAndItemsRenderer.swingArm
- FirstPersonHandsAndItemsRenderer.applyItemArmAttackTransform
- FirstPersonHandsAndItemsRenderer.applyItemArmTransform
- FirstPersonHandsAndItems.tick
- SwingAnimation.DEFAULT
- LivingEntity.getModifiedSwingDuration / swing

## スイング
進行pは0～1。右手、Javaカメラ座標で移動量は
x=-0.4 sin(pi sqrt(p))
y=0.2 sin(2pi sqrt(p))
z=-0.2 sin(pi p)

回転行列は
Ry(45-20 sin(pi p²)) Rz(-20 sin(pi sqrt(p))) Rx(-80 sin(pi sqrt(p))) Ry(-45)
です。単一ボーンのXYZ角を足すのとは異なります。
左右反転はx移動とY/Z回転に適用されます。
既定スイングは6tick。採掘速度と採掘疲労で期間が変化します。

## 手の上下
目標高さは回復率rの3乗、h_next = h + clamp(r³-h,-0.4,0.4)。
描画時の基準移動は (0.56,-0.52-0.6*(1-h),-0.72)。
手の高さとスイングを独立して計算し、重ねて描画します。
必ず「0.3秒待ってから下降」という順番ではありません。

## 現在のパックとの違い
- 現在の回転はCrossplay 2.0由来の横80度・傾き50度。Javaの回転行列とは違います。
- 現在の上下/奥行きは同じ位相を多く使用。Javaは上下と奥行きで位相が違います。
- 現在の下降は待ち時間→直線下降→直線復帰。Javaは3乗目標とtickごとの変化制限です。
- 50ms刻みの200種類はクールダウン所要時間の精度です。軌道の一致を保証しません。

## 保存した計算基準
scripts/java_swing_reference.py に上記の移動、順序付き行列積、手の高さ更新を実装。
1001点で移動範囲、回転の直交性、始端/終端の単位行列、上下更新の制限を確認します。

この計算はJavaカメラ座標です。Bedrockの親ボーン、回転基底、ピボット、
アイテム表示変換、FOVの変換はまだ行っていません。
既存パックへ未検証の座標を直接代入する変更は今回行っていません。

## 移植済み
現在はJavaのスイング移動と4回転の階層、tickごとの3乗回復をパックへ移植しています。座標変換と検証範囲はresource-pack/README.mdを参照。実機の画面座標は未検証です。
