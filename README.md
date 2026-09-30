# GeyserCooldownAnimation

**Javaの攻撃クールダウンを、Bedrockプレイヤーの手元の動きで表示するGeyser拡張。**

Paperの攻撃速度に応じて、攻撃したBedrockプレイヤー本人へアニメーションを送信します。
専用の **Geyser Cooldown Animation Resource Pack** を同梱して、配布します。

[導入ガイド](INSTALL.md) · [MIT License](LICENSE)

> 開発段階です。Geyser上のロード・パック登録・受信処理は確認済みですが、Paperの実際の攻撃イベント・Velocity経由の実接続・Bedrock実機の表示は未検証です。

> 本拡張機能はCodexを使用して作成されています。
## 機能

- 素手・剣・ツルハシ・斧・メイスの7つの表示プロファイル。
- 攻撃時に手を下げ、クールダウンに合わせて戻す一人称アニメーション。
- 専用パックの自動展開とGeyser経由の配布。
- 同じtickの重複抑制と、プレイヤーの既存接続を使う通信。
- token・endpoint・追加ポート・設定ファイル不要。
- 内部APIの非互換時に表示機能を停止。

## 対応環境

| コンポーネント | 配置先 | 実行環境 |
| --- | --- | --- |
| GeyserCooldownAnimation | Geyserの `extensions/` | Java 21以上、Geyser API 2.11.0以上 |
| GeyserCooldownPaperBridge | Paperの `plugins/` | Java 25以上、Paper 26.3 |
| 専用リソースパック | 拡張JARに同梱 | Bedrockでサーバーパックを適用 |

Geyser-Spigot、Geyser-Velocity、Standaloneから、既存のMinecraft接続でPaperと連携します。
別ホストでも追加のHTTP通信設定は不要です。Velocity専用の追加JARも不要です。
Geyser 2.11.3-b1247の実パケットクラスで受信処理を検証済み。
Velocity経由の実接続とBedrock実機での表示は未検証です。

## 導入

1. GitHub **Releases** から同じバージョンの2つのJAR、または導入用ZIPを取得。
2. Geyserのextensionsへ拡張、Paperのpluginsへ連携JARを配置。
3. 起動し、Bedrockから接続してサーバーパックを適用。

設定ファイルの編集は不要です。Velocity構成では各Paperサーバーへ連携JARを配置します。

詳しいフォルダ例と設定は [INSTALL.md](INSTALL.md) を参照してください。

## 専用パック

剣・斧・メイスの一人称スイングと持ち方はBlurry's Crossplay Animations 2.0を基準にしています。
クールダウンの腕下げはスイング終了後に再生し、剣10、斧・メイス12の下げ幅を使用します。
剣・斧は参照元のCatmull-Rom補間、メイスは線形補間です。

実効攻撃速度から算出したクールダウンを50ms刻み・1～200tickで通知します。
通知は時間を更新するだけで、描画はBedrock側のcontrollerが担当します。
連打時は回復を中断してスイングへ戻り、終了後に残り時間で復帰します。
ツルハシ・hoe・シャベルはカスタム表示と腕下げの対象外です。

ビルドごとにパックのheader/module UUIDを更新します。更新後はサーバーを再起動し、Bedrockクライアントで再接続してください。
参考素材に本プロジェクトのMITライセンスは適用されません。出典は [素材通知](resource-pack/THIRD_PARTY_NOTICES.md) を参照してください。
仕様は [パックREADME](resource-pack/README.md)、v1.2.0の変更は [リリース説明](docs/releases/v1.2.0.md) に記載しています。
