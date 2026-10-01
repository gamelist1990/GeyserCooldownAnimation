# GeyserCooldownAnimation

**Javaの攻撃クールダウンを、Bedrockプレイヤーの手元の動きで表示するGeyser拡張。**

Geyser標準クールダウンの開始時刻と攻撃速度を使い、Bedrockプレイヤー本人へアニメーションを送信します。
Paper側のbridgeや追加プラグインは不要です。
専用の **Geyser Cooldown Animation Resource Pack** を同梱して、配布します。

[導入ガイド](INSTALL.md) · [MIT License](LICENSE)

> 開発段階です。クールダウン時間の計算・ビルド・パック検証を実施しています。新しい監視処理の実接続・Velocity経由のサーバー移動・Bedrock実機の表示は未検証です。

> 本拡張機能はCodexを使用して作成されています。
## 機能

- 素手・剣・ツルハシ・斧・メイスの7つの表示プロファイル。
- 攻撃時に手を下げ、クールダウンに合わせて戻す一人称アニメーション。
- 専用パックの自動展開とGeyser経由の配布。
- Geyserのクールダウン開始時刻を監視し、同じ開始時刻の重複通知を抑制。
- token・endpoint・追加ポート・設定ファイル不要。
- 内部APIの非互換時に表示機能を停止。

## 対応環境

| コンポーネント | 配置先 | 実行環境 |
| --- | --- | --- |
| GeyserCooldownAnimation | Geyserの `extensions/` | Java 21以上、Geyser API 2.11.0以上 |
| 専用リソースパック | 拡張JARに同梱 | Bedrockでサーバーパックを適用 |

Geyser-Spigot、Geyser-Velocity、Standaloneで、拡張JARだけを配置します。
JavaサーバーからGeyserへ届く攻撃速度属性を利用します。
Geyser内部APIへ依存するため、Geyser更新時には互換性の確認が必要です。

## 導入

1. GitHub **Releases** から拡張JAR、または導入用ZIPを取得。
2. Geyserのextensionsへ拡張JARを配置。
3. 起動し、Bedrockから接続してサーバーパックを適用。

通常は設定変更不要です。Geyserの標準クールダウン表示を有効にしてください。
`disabled`では開始時刻が更新されず、本拡張も動作しません。
標準パックの有無には依存しません。標準UIの表示も維持します。
攻撃・空振りに加え、Geyserがクールダウンを更新するアイテム切替にも連動します。

詳しいフォルダ例と設定は [INSTALL.md](INSTALL.md) を参照してください。

## 専用パック

剣・斧・メイスの一人称スイングと持ち方はBlurry's Crossplay Animations 2.0を基準にしています。
クールダウンの腕下げはスイング終了後に再生し、剣10、斧・メイス12の下げ幅を使用します。
剣・斧は参照元のCatmull-Rom補間、メイスは線形補間です。

Geyserの実効攻撃速度とtick速度から残り時間を算出し、50ms刻み・1～200tickで通知します。
開始時刻の監視はGeyserのイベントループで10ms間隔です。検知までの経過時間を差し引きます。
通知は時間を更新するだけで、描画はBedrock側のcontrollerが担当します。
連打時は回復を中断してスイングへ戻り、終了後に残り時間で復帰します。
ツルハシ・hoe・シャベルはカスタム表示と腕下げの対象外です。

ビルドごとにパックのheader/module UUIDを更新します。更新後はサーバーを再起動し、Bedrockクライアントで再接続してください。
参考素材に本プロジェクトのMITライセンスは適用されません。出典は [素材通知](resource-pack/THIRD_PARTY_NOTICES.md) を参照してください。
仕様は [パックREADME](resource-pack/README.md)、v1.2.0の変更は [リリース説明](docs/releases/v1.2.0.md) に記載しています。

## パケット送信

1.2.1ではGeyserSessionを型付きで呼び出し、接続のCloudburst codecを使ってアニメーションパケットを生成します。リフレクションは使用しません。クライアントの初期化・スポーンが完了した接続へ送信します。
