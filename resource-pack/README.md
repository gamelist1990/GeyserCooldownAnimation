# Geyser Cooldown Crossplay Weapons

剣・斧・メイスのスイングと持ち方はユーザー指定のBlurry's Crossplay Animations 2.0を基準にしています。
ツルハシ・hoe・シャベルはカスタム表示の対象外です。

## スイングとクールダウンの分離
サーバーのanimation.player.cooldown_tick_1～200は、腕を動かさず、
duration（50ms刻み）、通知時刻、再生要求だけをplayer変数へ渡します。
クライアントのrecovery controllerはvariable.attack_time > 0の間、上下動を再生しません。
スイングが終わると剣・斧・メイスに対応した回復アニメーションへ移ります。
剣は下げ幅10、斧・メイスは12。剣・斧は参照元のcatmullrom、メイスは線形です。
連打で再びスイングが始まると回復を中断して待機状態へ戻ります。

通知からスイング終了までの経過時間を差し引き、残り時間で復帰します。
残り時間が0以下なら、復帰を最低50msだけ再生します。
Blurry単体の剣0.3秒・斧1.0417秒・メイス2秒という固定時間は使わないため、
サーバー通知時間を優先した分の違いは残ります。

## 重複と送信
同じsequenceまたは45ms以内の通知だけを抑制し、各server tickの時間更新を許可します。
通知は動きを直接再開しないため、連打で腕下げアニメーションが積み重なりません。
packetのruntime controllerはgeyser_cooldown_timingという専用名です。

## ビルド・確認
./gradlew.bat build
python scripts/package_release.py --version 1.2.0
生成対象はcooldown.animation.json（タイミング通知）です。
weapon_swing.animation.json / recovery.animation.jsonは参考元ベースの定義です。
ビルドごとにheader/module UUIDを更新します。
200種類の通知、状態遷移条件、下げ幅・補間、Java側の重複抑制をテストします。
実機でのtimeline実行・controllerの合成と見た目は未確認です。
