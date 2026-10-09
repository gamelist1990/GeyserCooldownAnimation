# GeyserJavaGlowing との互換性

GeyserCooldownAnimation 1.3.1 以降と GeyserJavaGlowing 0.2.1 以降は、同じ統合済み `entity/player.entity.json` をそれぞれのリソースパックに同梱します。

統合定義には次を同時に保持しています。

- GeyserJavaGlowing の outline material / geometry / render controller、チーム色、防具・ケープ・エリトラ用定義
- GeyserCooldownAnimation の `gca_*` 変数、サーバー時間ベースの recovery controller、武器アニメーション alias
- Glowing 側に残る固定時間 cooldown の自動実行を外し、Cooldown のサーバー通知を優先する構成

そのため、Geyser が2つのパックをどちらの優先順で読み込んでも `entity/player.entity.json` の内容は同じです。専用の互換 JAR や互換 mcpack は必要ありません。

導入は通常版の `GeyserJavaGlowing` と `GeyserCooldownAnimation` を Geyser の `extensions/` に配置して再起動してください。Bedrock 側では更新されたサーバーパックを再取得します。

第三のリソースパックが `entity/player.entity.json` を上書きする場合、そのパックについては別途統合が必要です。
