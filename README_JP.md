# delivery-miffe

ネット動画配信ツール  
[English Document](./README.md)

## 概要

- CMAF（Common Media Application Format : Reference[1]）の低遅延配信（Ultra Low Latency）を簡易に検証するための配信サーバーです。
    - LIVE及びVODのストリーミング配信に対応しています。
    - 動画エンコーダからの入力は、HTTP PUTメソッドで渡されます。

![Overview](./docs/imgs/overview.png)

- Reference
    - [1] ISO/IEC23000-19：“Common media application format (CMAF) for segmented media”

## 実行環境

- python 3.7.x ~ 3.10.x

## 相互接続性

本ツール(delivery-miffe)は、下記OSSとの相互接続性を確認しています。

- エンコーダー
    - [ffmpeg](https://www.ffmpeg.org/)
    - Videon EdgeCaster
    
- 動画再生プレイヤー
    - [dash.js](https://github.com/Dash-Industry-Forum/dash.js)
    - [hls.js](https://github.com/video-dev/hls.js/)
    - [basjoo.js](https://github.com/nhkrd/basjoo.js)

- ネット動画イベント挿入ツール
    - [relay-miffe](https://github.com/nhkrd/relay-miffe)

## フォルダ構成

```
.
├── LICENSE.txt
├── NOTICE.txt
├── README.md
├── content
├── docs
├── test
├── delivery.sh         # start shell
├── deliverymiffe.py
├── input.log           # log file
└── settings.ini        # setting
```

## 使い方

### サーバー起動

- 起動
```
$ ./delivery.sh
($ python3 deliverymiffe.py)
```

IPアドレスとポートは[settings.ini]で設定できます。

### 動作サンプル

- エンコーダーからの配信

ffmpegを用いた場合、[こちらのサンプル](./test/ffmpeg_cmaf.sh)によって本ツールに動画を入力できます。

- 動画再生プレイヤーからのリクエスト

動画再生プレイヤーで下記のようにマニュフェストファイルをリクエストすることで動画を再生できます。

```
# MPEG-DASHの場合
http://[delivery-miffeのIPアドレス]:[delivery-miffeのポート番号]/[動画コンテンツのディレクトリ]/manifest.mpd

# HLSの場合
http://[delivery-miffeのIPアドレス]:[delivery-miffeのポート番号]/[動画コンテンツのディレクトリ]/master.m3u8
```

## その他

### 起動確認用API

delivery-miffeの起動状態をHTTP GETで確認できます。

```
# ブラウザで確認する場合
http://[delivery-miffeのIPアドレス]:[delivery-miffeのポート番号]/status
```

### HTTP DELETEメソッドの有効無効設定

[settings.ini]の下記項目で、HTTP DELETEメソッドの処理の有効無効を切り替えられます。  
エンコーダーからの配信停止時におけるDELETEメソッドを用いたファイル削除を無効にし、LIVE配信された動画をVODとして蓄積することもできます。

```
FileDelete = True #有効
```

## ライセンス

本ソフトウェアのライセンスについては[LICENSE.txt](./LICENSE.txt)および[NOTICE.txt](./NOTICE.txt)を参照ください。
