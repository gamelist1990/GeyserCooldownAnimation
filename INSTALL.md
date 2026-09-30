# 導入ガイド

[READMEへ戻る](README.md)

## 1. JARを配置

GitHub Releasesから同じバージョンの2つのJARを取得します。
導入用ZIPの `extensions/` と `plugins/` にも同じJARが入っています。

| ファイル | 配置先 |
| --- | --- |
| `GeyserCooldownAnimation-<version>.jar` | Geyserの `extensions/` |
| `GeyserCooldownPaperBridge-<version>.jar` | 接続先Paperの `plugins/` |

| Geyser環境 | 拡張の配置例 |
| --- | --- |
| Geyser-Spigot | `plugins/Geyser-Spigot/extensions/` |
| Geyser-Velocity | `plugins/Geyser-Velocity/extensions/` |
| Standalone | 実行ディレクトリの `extensions/` |

フォルダ名は実際のGeyserインストールに合わせてください。
GeyserはJava 21以上、PaperはJava 25以上・26.3が必要です。

**GeyserとPaperは同じホスト上で、127.0.0.1を通じて通信できる必要があります。**
VelocityへPaper連携JARを置くことはできません。

## 2. 起動してtokenを設定

GeyserとPaperを起動すると次のファイルが生成されます。

| ファイル | 用途 |
| --- | --- |
| Geyserの `extensions/geyser-cooldown-animation/bridge.properties` | port・認証token |
| Geyserの `extensions/geyser-cooldown-animation/geyser-cooldown-animation.mcpack` | 自動展開された専用パック |
| Paperの `plugins/GeyserCooldownPaperBridge/config.yml` | 送信先・認証token |

Geyserの `token=` の右側を、Paperの `token` にコピーします。

```yaml
token: 'Geyserのbridge.propertiesに生成されたtoken'
endpoint: 'http://127.0.0.1:28765/v1/attack'
```

設定を保存してPaperを再起動してください。
tokenが空の初回起動ではPaper連携が無効になります。
tokenは公開リポジトリへコミットしないでください。

ポートを変える場合、Geyserの `port` とPaperの `endpoint` を合わせて両方再起動します。
外部IP・別ホスト・別ネットワーク名前空間のコンテナ間通信はこの版では対応していません。

## 3. Bedrockでパックを適用

ログに次の表示が出ることを確認します。

```text
Enabled extension GeyserCooldownAnimation
Cooldown animation bridge listening on 127.0.0.1:28765
```

Bedrockから再接続し、サーバーのリソースパックを適用します。
Geyser 2.11.3では `gameplay.force-resource-packs: true` でパック適用を必須にできます。

専用パックはJARから自動配布されます。
単体のmcpackをGeyserのpacksフォルダへ重ねて配置する必要はありません。
データフォルダの専用パックは起動時にJARの内容へ更新されるため、直接の編集は保持されません。

## 4. 表示を確認

素手・剣・ツルハシ・各斧・メイスで、攻撃と空振りを確認します。
一人称で手元が下がり、プロファイルに応じた時間で元へ戻る想定です。
三人称の右腕位置には専用パックの追加オフセットを適用しません。

連打・武器切り替え・カスタム攻撃速度・他の描画パックとの組み合わせも確認してください。
Geyserのロード・パック登録・通信は検証済みですが、Bedrock実機の見た目は未検証です。

## 更新

1. GeyserとPaperを停止。
2. 旧バージョンの両JARを取り除き、新バージョンを配置。
3. token設定を維持して起動。
4. Bedrockから再接続して確認。

異なるバージョンのJARを複数配置しないでください。
以前の外部パック `cooldown-geyser.mcpack` はこの版では使いません。
以前それをGeyserのpacksフォルダへ手動配置していた場合は、停止中に取り除いてください。

## トラブルシューティング

| 症状 | 確認する内容 |
| --- | --- |
| 拡張がロードされない | 配置先、Java 21以上、Geyser API対応版 |
| `Bundled Geyser Cooldown Animation pack missing` | 配布JARが完全か。公式Release資産を再取得 |
| パック登録に失敗する | 同じUUIDのパックを重複配置していないか、JARの破損 |
| Paper連携が無効になる | token設定、Java 25以上、Paper 26.3 |
| `Cooldown bridge unavailable` | Geyserの起動、同一ホスト、port・token一致 |
| `Unsupported Geyser packet API` | 対応版へ更新して再起動 |
| 通信しているが表示されない | Bedrockへのパック適用、描画パックの競合、一人称視点 |

## 削除

GeyserとPaperを停止して両JARと対応するデータフォルダを削除します。
Bedrockのローカルパックキャッシュが残る場合はクライアント側でも整理してください。
