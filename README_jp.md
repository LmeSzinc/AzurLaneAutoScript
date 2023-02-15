**| [英語](README_en.md) | [中国語](README.md) | 日本語 |**


# AzurLaneAutoScript

#### Discord [![](https://img.shields.io/discord/720789890354249748?logo=discord&logoColor=ffffff&color=4e4c97)](https://discord.gg/AQN6GeJ) QQグループ  ![](https://img.shields.io/badge/QQ%20Group-1087735381-4e4c97)
Azur Lane bot with GUI (Supports CN, EN, JP, TW, able to support other servers), designed for 24/7 running scenes, can take over almost all Azur Lane gameplay. Azur Lane, as a mobile game, has entered the late stage of its life cycle. During the period from now to the server down, please reduce the time spent on the Azur Lane and leave everything to Alas.

Alas is a free open source software, link: https://github.com/LmeSzinc/AzurLaneAutoScript

Alasは、GUI機能を搭載されていたアズールレーン用のスクリプトでございます。（日本サーバー、中国サーバー、英語サーバーと台湾（中国）サーバーに対応しています）このスクリプトは、7x24時間稼働する為に設計されたもので、ほぼ全てのゲームシステムを人のように代行できる。
モバイルゲームとして、アズールレーンはもはやライフサイクルのエンディングに迫っています。故に、今から配信終了までの間、アズールレーンに使う時間を少しずつ減らして、全ての操作をAlasに任せてください。

Alasは、無料配布のオープンソースソフトウェアの一つであります。リンク：https://github.com/LmeSzinc/AzurLaneAutoScript

EN support, thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[@nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, thanks **[@ferina8-14](https://github.com/ferina8-14)**, **[@noname94](https://github.com/noname94)** and **[@railzy](https://github.com/railzy)**.

TW support, thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

GUI development, thanks **[@18870](https://github.com/18870)** , say HURRAY.

![](https://img.shields.io/github/commit-activity/m/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/tokei/lines/github/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/repo-size/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-pr-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97)

これはGUIプレビュー画像の一枚である：
![gui](https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/doc/README.assets/gui.png)



## 機能 Features

- **出撃**：通常海域、イベント海域、チャレンジイベントなどの自動攻略。
- **収穫**：委託、戦術教室、研究、寮舎、オフニャ、大艦隊、収穫、毎日ショップ購入、開発ドックなど。
- **每日**：デイリー、通常海域（ハード）、救助信号、演習、イベントAB海域、イベントSP海域、チャレンジイベント、作戦履歴の自動攻略。
- **セイレーン作戦**：余烬信标，每月开荒，大世界每日，隐秘海域，短猫相接，深渊海域，塞壬要塞。

#### 特殊機能

- **機嫌計算**：艦船の機嫌状態を計算して、好感度下がるのを防ぐ。
- **イベント海域推進**：周回モードでなく、自動的にイベント海域を攻略することができます。
- **セイレーン作戦**：日課任務、ショップ購入、毎月海域攻略などゲーム内全システム操作一括完成。
- **毎月セイレーン作戦海域攻略**：作戦記録（5000石油のアイテム）なくでも全地図自動攻略できる。



## インストール Installation [![](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total?color=4e4c97)](https://github.com/LmeSzinc/AzurLaneAutoScript/releases)

[インストールする方法（中国語）](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_cn)

[インストールする方法（英語）](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en)日本語はいまだ未翻訳の状態です。

[設備対応ドキュメント](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Emulator_cn)様々な設備とエミュレータで、アズールレーンとAlasを実行ようにの説明ドキュメント。（今は中国語しかありません）


## スケジューリングプログラムを正しく使ってください

- **先ずは*プロセス*と*スケジューリングプログラム*をきちんと理解してください**

  Alasでは、全ての任務は単独の「プロセス」となります。それらのプロセスは一つのスケジューリングプログラムで統合に管理されています。一つのプロセスが完了したら、スケジューリングプログラムは自動的に次の実行タイムを最適化してキューに設定します。
  例えば、*研究*プロセスでゲーム内４時間の研究を行った場合なら、スケジューリングプログラムは自動的に*研究*プロセスの次の実行タイムを４時間ぐらい後らせます。

- **Alasの*機嫌計算*システムを理解してください**

  Alasでは、戦艦の機嫌悪い状態を防ぐように機嫌計算機能を搭載しています。これは機嫌悪いになったら出撃を止めるという訳ではなく、常に戦艦の機嫌を120以上に保つということです。（機嫌は120以上にいれば、出撃に得られる経験値は20％上がることになります）たとえば今ある戦艦の機嫌は113となるが、寮舎二層に置くことで一時間50上がるとなります。この状態で、Alasは12分を待って機嫌を120以上になってから出撃プロセスを実行します。

- **スケジューリングプログラムを正しく使ってください**

  スケジューリングプログラムについて、**一つや二つの機能しかオープンしない**、それは間違っている使い方である。**全部あるいはすべでお使いになりそうな機能をオープンする**こそ正しい使い方である。スケジューリングプログラムによって、オープンした機能（プロセス）は全て統合管理で最適なタイミングで実行されます。故に、ゲームとAlasを起動した後は、エミュレータとAlasを最小化して、その存在を忘れればいいでございます。


## バグのご報告について bug How to Report Bugs

質問をする前に、少なくとも５分をかけてきちんと「どの状況で問題が起こったのか」を考えてください。そうすれば、答えをする人も喜んで自分の５分をかけて君の質問を答えるのであります。
当然のことに、「なぜ○○機能は作動しない」「なぜフリーズしたのか」のような質問は答えされません。ちゃんと問題が起こった時の状況を伝えてくれるこそ、バグを特定できるから。

- 質問をする前に、先ずは[よくある質問(FAQ)](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/FAQ_en_cn)を読んでください。
- Alasのアップデータと最新commitをチェックして、お使いのAlasは最新版と確保してください。
- ディレクトリ`log/error`の中では、時間順で保存されているログフィールド（中身はlog.txtと当時のスクリーンショット）が入っています。それを質問をする際に、issuesと共に提出してください。



## 今存在している問題 Known Issues

- **ネット環境によるエラーを処理できません**エラーダイアログの自動処理ができませんのため、その時はスクリプト停止となります。
- **ローエンドパソコンでの作動が保障されていません**ローエンドパソコンでは、パソコン機能の制限によって、通常スクリーンショットのロスタイムは0.5秒以下となるが、ローエンドパソコンでは1秒以上になります。
- **自動演習で戦闘結果は失敗となる可能性があります**デフォルトコンフィグでは、演習中スクリプトは１秒ごとに演習双方のHPを識別します。普通自分のHPが設定値以下になると自動的に撤退しますが、もしその１秒の間で自分の艦隊が全滅になったら、自動撤退機能は作動しないとなります。
- **ADBとuiautomator2が作動しない状況はごくまれに発生します**この状況なら普通エミュレータを再起動すれば解決します。
- **一部の状況でエミュレータでのフリック操作はクリック操作と認識されます**



## Alas コミュニティールール Alas Community Guidelines

[#1416](https://github.com/LmeSzinc/AzurLaneAutoScript/issues/1416)でご参照ください。



## ドキュメント Documents

[海域識別 perspective](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/perspective)

`海域識別`はアズールレーンスクリプトのコアとも言えます。もしも単なる`テンプレートマッチング (Template matching)`でゲーム内の索敵機能を実現するなら、通常単位で艦隊現在地からBOSS単位への道を通行不可になることは不可避となります。そこで、Alasではより適用性の高い海域識別方法が提供している。`module.map_detection`の中で、現在ゲーム内のフールマップをゲットすることができます。例えば下記の通り：

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

[WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki)で全てのドキュメントを読めます。



## 開発にお手伝 Join Development

現在、Alasはまだ開発し続いている。私たちは未来の開発方向を不定期に[Issues](https://github.com/LmeSzinc/AzurLaneAutoScript/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)に発表して、`help wanted`と表記します。
ですので、皆さんからAlasに[Pull Requests](https://github.com/LmeSzinc/AzurLaneAutoScript/pulls)を提出することが歓迎しています。私たちは必ず提出してくれる方々のコートを行列ごとにきちんと読んで分析します。

勿論、[開発ドキュメント](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start)を読むことを忘れないでね。



## 関連プロジェクト Relative Repositories

- [AzurStats](https://azur-stats.lyoko.io/)：Alasに基づいたゲームアイテムドロップ統計システム。
- [AzurLaneUncensored](https://github.com/LmeSzinc/AzurLaneUncensored)：中国サーバー用、立ち絵規制などの回避プラグイン。
- [ALAuto](https://github.com/Egoistically/ALAuto)：英語サーバー向けのアズールレーンスクリプト、現在は開発終了しています。Alasはこのスクリプトをフレームワークとして出来たものである。
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta)：Alasでは、このプロジェクトで使われているホモグラフィを画像解析モジュールに導入しています。
- [PyWebIO](https://github.com/pywebio/PyWebIO)：Alasに使われているGUIクラス。
- [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)：ゲームアークナイトのスクリプト、ゲーム日課を自動的に一括完成できる。 -> [MAAプラグインの使い方](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/submodule_maa_cn)



## お問い合わせ Contact Us

- Discord: [https://discord.gg/AQN6GeJ](https://discord.gg/AQN6GeJ)
- Bilibili 生放送：https://live.bilibili.com/22216705

