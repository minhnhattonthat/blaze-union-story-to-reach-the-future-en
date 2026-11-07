"""Rows for the chapter cards 1970-2028: title + location (A, @30), title (B), vertical title (C)."""
import json
import sys
sys.path.insert(0, "tools")
import sprite

LOC = {
    "ティエラ・ネザー地区西": "Tiera, Nether District West",
    "ティエラ・ネザー地区中央": "Tiera, Central Nether District",
    "ティエラ・ネザー地区東": "Tiera, Nether District East",
    "ティエラ・ネザー地区北": "Tiera, Nether District North",
    "ティエラ・ネザー地区": "Tiera, Nether District",
    "イストラカ荒原": "Istraka Wastes",
    "イーザー渓谷・桟道東部": "Ether Gorge, East Cliff Road",
    "イーザー渓谷・桟道西部": "Ether Gorge, West Cliff Road",
    "アルベルト侯爵領・市街地": "Albelt Marquisate, Town",
    "アルベルト侯爵領・農村地": "Albelt Marquisate, Farmland",
    "北部辺境・帝国軍駐屯地": "Northern Frontier, Imperial Garrison",
    "ティエラ・ニーベル街区": "Tiera, Nibel Quarter",
    "エルルク山脈・間道": "Erruk Mountains, Back Road",
    "ニルルド砂漠": "Nilrud Desert",
    "ジッカート山・中央キャンプ": "Mount Jikkart, Central Camp",
    "アニス伯爵領": "Anis County",
    "クレドの森・盗賊団のアジト": "Kred Forest, Bandit Hideout",
    "クレドの森・預言者の館": "Kred Forest, Prophet's Manor",
    "トキノ山・山塞": "Mount Tokino, Stronghold",
    "トキノ山・関所": "Mount Tokino, Checkpoint",
    "バリン公爵領": "Balin Duchy",
    "バリン公爵領・北部沿岸": "Balin Duchy, North Coast",
    "ドロミノス湿地帯": "Dorominos Marshes",
    "ティエラ郊外・私兵団邸": "Tiera Outskirts, Private Army Manor",
    "ティエラ郊外・西部街道": "Tiera Outskirts, West Road",
    "ティエラ郊外・北部街道": "Tiera Outskirts, North Road",
    "帝都近郊・凱旋門": "Near the Capital, Triumphal Gate",
    "帝都近郊・桟道東端": "Near the Capital, East End of the Cliff Road",
    "西部地域・ケルヌガ農村群": "Western Region, Kernuga Farmlands",
    "西部地域・山岳都市シャーミネル": "Western Region, Mountain City of Sharminel",
    "運河の船渡し場": "Canal Ferry Landing",
    "魔竜の神殿": "Temple of the Demon Dragon",
    "帝都フレアヴェルク": "Imperial Capital Flarewerk",
    "カノッサ街道": "Canossa Road",
    "カローナ南部・ロドニー街道": "South Karona, Rodney Road",
    "王都パルティナ・正門": "Royal Capital Paltina, Main Gate",
    "パルティナ城・謁見の間": "Paltina Castle, Throne Room",
    "国境付近・カノッサ街道": "Near the Border, Canossa Road",
    "イシュナート要塞": "Ishnart Fortress",
    "国境付近・レグナーの丘": "Near the Border, Regner Hill",
    "ララ岬・封印の祭壇": "Cape Lara, Altar of the Seal",
}
CARDS = """1970 義賊団参上！ ティエラ・ネザー地区西
1971 テンガロンの女 ティエラ・ネザー地区中央
1972 傭兵団対義賊団 ティエラ・ネザー地区東
1973 大人達のルール ティエラ・ネザー地区北
1974 決戦、デイヴィド！ ティエラ・ネザー地区東
1975 力をこの手に イストラカ荒原
1976 フレアヴェルク上洛 イーザー渓谷・桟道東部
1977 駆けてきた姉妹 アルベルト侯爵領・市街地
1978 戦士と狂気 北部辺境・帝国軍駐屯地
1979 夜盗を追え！ ティエラ・ニーベル街区
1980 変わり者、募集中 エルルク山脈・間道
1981 砂漠に拾え、一滴の涙 ニルルド砂漠
1982 貴族の心、そして。 ジッカート山・中央キャンプ
1983 奪う者、奪われる者 アニス伯爵領
1984 それぞれの事情 クレドの森・盗賊団のアジト
1985 帝国の生み出したモノ トキノ山・山塞
1986 大切な物は何処 バリン公爵領
1987 はだしのミゼル ドロミノス湿地帯
1988 輸送船襲撃作戦 バリン公爵領・北部沿岸
1989 庇護の対価 アルベルト侯爵領・農村地
1990 扇げば揺れる麦の穂 アルベルト侯爵領・市街地
1991 懊悩の殉教者 ティエラ郊外・私兵団邸
1993 終わり無き復讐 ティエラ郊外・西部街道
1994 試練は屍を越えて クレドの森・預言者の館
1995 天意の名の下に イストラカ荒原
1996 戦士達の休息-Girl's_Side- ティエラ郊外・北部街道
1997 戦士達の休息-Boy's_Side- 帝都近郊・凱旋門
1998 火の粉は集い、大火へと 西部地域・ケルヌガ農村群
1999 戦火に立つ修羅 西部地域・山岳都市シャーミネル
2000 物欲のなせる罠 イーザー渓谷・桟道西部
2001 戻ってきた戦士 運河の船渡し場
2002 ソルトロード トキノ山・関所
2003 帝都軍事演習 帝都近郊・凱旋門
2004 守るべきもの ティエラ郊外・北部街道
2005 ティエラ炎上 ティエラ・ネザー地区
2006 狂戦士の叫び トキノ山・山塞
2007 歴史は夜、動く ティエラ・ニーベル街区
2008 うつろう時の中で ティエラ郊外・私兵団邸
2009 別離 イストラカ荒原
2010 呼び起こせ、魔竜の血 魔竜の神殿
2011 盾を破るのは矛なのか? 帝都近郊・凱旋門
2012 双竜激突 帝都フレアヴェルク
2013 焔帝ガルカーサ 帝都フレアヴェルク
2014 悲劇 ティエラ郊外・私兵団邸
2015 復讐 カノッサ街道
2016 覚醒 カローナ南部・ロドニー街道
2017 帰郷 王都パルティナ・正門
2018 再会 パルティナ城・謁見の間
2019 黒幕 パルティナ城・謁見の間
2020 血 パルティナ城・謁見の間
2021 はじまりのおわり ティエラ郊外・私兵団邸
2022 残り火 帝都近郊・凱旋門
2023 暴かれし瞳の奥 帝都近郊・桟道東端
2024 その火蓋は切らせない 国境付近・カノッサ街道
2025 死闘、命果てるまで イシュナート要塞
2026 死闘、命果てるまで イシュナート要塞
2027 死の舞踏 国境付近・レグナーの丘
2028 人が勝ち得たもの ララ岬・封印の祭壇"""

title = {}
for r in json.load(open("script/eboot_23.json", encoding="utf-8")):
    if 0x236A04 <= r["ptr"] <= 0x236DC8:
        title[r["jp"].replace(" ", "_")] = r["en"]
labels = {}
for line in open("work/sweep/index.tsv", encoding="utf-8"):
    pg, lab, size = line.split("\t")
    if "@" not in lab:
        continue
    f, o = lab.split("@")
    if o.endswith("g"):
        continue
    labels.setdefault(int(f), []).append((int(o, 16), size.strip()))


def bbox(img, y0, y1):
    b = img.crop((0, y0, img.width, y1)).split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
    return (b[0], y0 + b[1], b[2] - b[0], b[3] - b[1]) if b else None


def fmt(b, pad=1, w=None):
    """Japanese ink rows; the English may use the texture's whole width (each card texture is drawn whole)."""
    y0 = max(b[1] - pad, 0)
    return f"0,{y0},{w},{b[1] + b[3] - y0}"


out = ["# Chapter cards (1970-2028): title + location, title alone, vertical title beside the map. Titles from the",
       "# EBOOT's chapter table (0x236A04), so the chronicle and save list read the same. Other files with the same bytes",
       "# (1992, most of 2026) get the edit through gfx.copies."]
for line in CARDS.splitlines():
    f, jp, loc = line.split()
    en = title[jp].replace("_", " ")
    jp = jp.replace("_", " ")
    have = dict((s, o) for o, s in labels.get(int(f), []))
    for size, kind in (("150x36", "A"), ("247x48", "B"), ("247x42", "B"), ("30x180", "C")):
        if size not in have:
            continue
        lab = f"{f}@{have[size]:x}"
        img = sprite.image(lab)
        if kind == "A":
            prof = [sum(1 for x in range(img.width) if img.getpixel((x, y))[3] > 40) for y in range(img.height)]
            cut = min(range(40, 58), key=lambda y: prof[y])
            t, l = bbox(img, 0, cut), bbox(img, cut, img.height)
            out.append(f"{lab}\t{fmt(t, w=img.width)}\tbanner\t{jp}\t{en}")
            # the game cuts the title rect down to the location's first row: keep the English below it
            out.append(f"{lab}\t0,{l[1] + 1},{img.width},{l[3] - 1}\tbanner\t{loc}\t{LOC[loc]}")
        elif kind == "B":
            b = bbox(img, 0, img.height)  # a packed group: the English must keep to the Japanese ink
            out.append(f"{lab}\t{b[0]},{b[1]},{b[2]},{b[3]}\tbanner\t{jp}\t{en}")
        else:
            out.append(f"{lab}\t0,0,{img.width},{img.height}\tvbanner\t{jp}\t{en}")
print("\n".join(out))
