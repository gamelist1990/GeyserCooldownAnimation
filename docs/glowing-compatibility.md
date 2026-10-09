# GeyserJavaGlowing との互換版

Geyser Cooldown Crossplay Weapons 1.3.0 と GeyserJavaGlowing 0.2.0 は、
どちらも `entity/player.entity.json` を定義するため、元のパックをそのまま重ねると
優先順によって発光用の描画定義、または Cooldown の回復 controller が失われます。

[互換版の成果物](https://github.com/gamelist1990/GeyserJavaGlowing/tree/main/compatibility/glowing-0.2.0-cooldown-1.3.0) と
[生成・検証手順](https://github.com/gamelist1990/GeyserJavaGlowing/blob/main/COOLDOWN_COMPATIBILITY.md) を公開しています。

この互換版は、稼働サーバーのローカル Cooldown 1.3.0 JAR を入力として作成したものです。
サーバーの入力には槍・トライデント等の追加素材が含まれています。
GitHub の通常ビルドを入力にして再生成する場合は、その入力に含まれる素材を統合します。
ローカルの古い開発ソースへ戻したり、現行の武器定義を置き換えたりする処理はありません。

両方の互換パックに同じ統合済みプレイヤー定義と描画素材を同梱し、
この2つの優先順に依存せず、Glowing の輪郭・防具・エリトラと
Cooldown のサーバー通知・回復・武器表示を維持します。
Blurry の固定時間 cooldown controller は自動実行せず、サーバー通知による回復を使います。
既存の互換用 animation alias と作者のクレジットは保持しています。

導入時は、Geyser の `extensions/` にある元の2つの拡張を以下へ置き換えます。

- `GeyserJavaGlowing-0.2.0-cooldown-compat.jar`
- `GeyserCooldownAnimation-1.3.0-glowing-compat.jar`

同じ拡張 ID の元 JAR と互換 JAR を同時に置かないでください。
通常は拡張が同梱パックを配信するため、単独 mcpack を追加する必要はありません。
元の単独パックを手動配置している場合は、対応する互換版へ置き換えます。
再起動後、Bedrock 側でサーバーパックを再取得してください。

JAR 内の Java class と拡張のバージョンは元版と同じです。
RP の patch version は、古いプレイヤー定義のキャッシュを更新するため1増やしています。
SHA-256 は成果物フォルダーの `SHA256SUMS.txt` と `compatibility-report.json` で確認できます。

パック構造・両優先順・controller alias・武器素材・JAR の非RPエントリは検証済みです。
Bedrock 実機での描画と、BerryPVP 等の第3のパックとの表示は別途確認が必要です。
