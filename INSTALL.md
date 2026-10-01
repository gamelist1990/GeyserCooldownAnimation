# 導入ガイド

[READMEへ戻る](README.md)

## 1. 拡張JARを配置

[GitHub Releases](https://github.com/gamelist1990/GeyserCooldownAnimation/releases)から取得した
`GeyserCooldownAnimation-<version>.jar`をGeyserの`extensions/`へ配置します。
Paper bridgeは不要です。Java 21以上、Geyser API 2.11.0以上が必要です。

| Geyser環境 | 配置先 |
| --- | --- |
| Geyser-Spigot | plugins/Geyser-Spigot/extensions/ |
| Geyser-Velocity | plugins/Geyser-Velocity/extensions/ |
| Standalone | 実行ディレクトリの extensions/ |

## 2. Geyserの標準クールダウン表示を有効にして起動

Geyserのクールダウン設定を`crosshair`または`hotbar`にしてください。
旧形式の設定名は`show-cooldown`です。プレイヤー個別設定も有効にしてください。
`disabled`の場合、Geyserが開始時刻を記録しないため本拡張も停止します。
標準パックの有無は問いません。標準のインジケーター表示も維持します。

**token・endpoint・追加ポート設定は不要です。**
Geyser自身が持つ開始時刻とJavaサーバー由来の攻撃速度を利用します。
敵への攻撃・空振り・アイテム切替による標準クールダウンに連動します。

ログで次を確認します。

```text
Cooldown animation initialized; resourcePackReady=true.
Attached Geyser cooldown observer for <UUID>.
```

## 3. Bedrockから接続してパックを適用

専用パックは拡張JARから自動展開され、Geyser経由で配布されます。
単体mcpackを重ねて配置する必要はありません。
一人称で剣・斧・メイスの攻撃・空振り・連打・持ち替えを確認してください。

自動展開されたパックは、次回起動時にJARの内容へ更新されます。
監視処理の実接続・Velocity経由のサーバー移動・Bedrock実機の表示は未検証です。

## bridgeを使用する旧版から更新

1. Geyserと旧bridgeを入れたPaperを停止。
2. 旧拡張JARを新しい拡張JARへ交換。
3. 各Paperの`GeyserCooldownPaperBridge-*.jar`を取り除く。
4. 起動してBedrockから再接続。

旧bridgeのデータフォルダと設定ファイルは使用しません。
以前手動配置した同じUUIDのパックがある場合は、停止中に取り除いてください。

## トラブルシューティング

| 症状 | 確認する内容 |
| --- | --- |
| 拡張がロードされない | 配置先、Java 21以上、Geyser対応版 |
| パック登録に失敗する | 同じUUIDのパックの重複、配布JARの破損 |
| Geyser cooldown observer unavailable / stopped | Geyser内部APIの互換性。ログを添えて報告 |
| 動かない | 標準クールダウン設定、個別設定、サーバーパック適用、一人称視点、他のパックとの競合 |
| サーバー移動後だけ表示されない | 移動後のGeyserログと標準インジケーターの動作 |

## 削除

Geyserを停止して拡張JARと対応するデータフォルダを削除します。
