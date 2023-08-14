import os
import sys
import re
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
import threading
from pprint import pprint
import time
from itertools import zip_longest

from googletrans import Translator
# https://py-googletrans.readthedocs.io/en/latest/

# GUIが終了したかを管理するフラグ (アプリ全体で共通化したいのでglobal変数にしている)
GUI_END_FLG = 0

class GUI:
    def __init__(self):
        # 別プロセス実行
        self.start_flg = 0
        self._run_translate_thread = threading.Thread(target=self.__run_process)
        self._run_translate_thread.setDaemon(True)
        self._run_translate_thread.start()

        # テンプレート文字列
        self.header_template = "Key,File,Type,UsedInMainMenu,NoTranslate,english,Context / Alternate Text,german,latam,french,italian,japanese,koreana,polish,brazilian,russian,turkish,schinese,tchinese,spanish"

        # GUI設定
        self.root = tk.Tk()

        win_width  = 570
        win_height = 370
        self.root.geometry(f"{win_width}x{win_height}")
        self.root.state("zoomed") # ウィンドウを最大サイズで起動する

        # タイトル表示
        self.root.title("Text Translator")

        # ヘッダーテンプレート表示
        self.header_template_split_0 = ",".join(self.header_template.split(",")[ 0: 7])
        self.header_template_split_1 = ",".join(self.header_template.split(",")[ 7:])
        self.label_header_template_0 = tk.Label(text=self.header_template_split_0)
        self.label_header_template_1 = tk.Label(text=self.header_template_split_1)

        # ファイル選択
        label_file_path = tk.Label(text="Text File Path")
        self.textbox_file_path = tk.Entry(width = 40)

        # 機能選択プルダウンメニュー
        label_select_function        = tk.Label(text="Select Function")
        self.combbox_function_values = ("1. Translate Key Only", "2. Translate Language")
        self.combbox_function        = ttk.Combobox(width = 20, height = 7, values = self.combbox_function_values)
        self.combbox_function.set(self.combbox_function_values[0])
        self.combbox_function.bind("<<ComboboxSelected>>", self.__update_combbox_language)

        # 参照ボタン
        self.filedialog_btn = tk.Button(self.root, text="browse", command=self.__open_filedialog, font=("", 8))

        # 言語選択プルダウンメニュー
        label_language = tk.Label(text="Select Language")
        self.combbox_language_values_0 = ("Key")
        self.combbox_language_values_1 = ("Key", "english","german","latam","french","italian","japanese","koreana","polish","brazilian","russian","turkish","schinese","tchinese","spanish")
        self.combbox_language = ttk.Combobox(width = 12, height=7, values=self.combbox_language_values_0)
        self.combbox_language.set(self.combbox_language_values_0) # Keyを初期値として設定

        # 翻訳開始ボタン
        self.button = tk.Button(self.root, text="Start Translation", command=self.__start_process)

        # 出力先ファイル表示
        self.label_output      = tk.Label(text="Output File Path")
        self.label_outfilename = tk.Label(text="")

        # 各種情報
        self.label_orderer = tk.Label(text="orderer: az-jp")
        self.label_date    = tk.Label(text="date: 2023/08/14")
        self.label_version = tk.Label(text="version: 7DTD・a21")

        # 実行時表示部
        self.label_converting    = tk.Label(text="")
        self.label_progress      = tk.Label(text="")
        self.label_progress_line = tk.Label(text="")

        self.label_header_template_0.grid(row=0, column=0, padx=10, pady=(10,0), columnspan=5, sticky=tk.W)
        self.label_header_template_1.grid(row=1, column=0, padx=10, pady=(0,10), columnspan=5, sticky=tk.W)
        label_file_path             .grid(row=2, column=0, padx=10, pady=10)
        self.textbox_file_path      .grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        self.filedialog_btn         .grid(row=2, column=2, padx=0 , pady=0 , sticky=tk.W)
        label_select_function       .grid(row=3, column=0, padx=10, pady=10)
        self.combbox_function       .grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        label_language              .grid(row=4, column=0, padx=10, pady=10)
        self.combbox_language       .grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)
        self.button                 .grid(row=5, column=0, padx=10, pady=10)
        self.label_output           .grid(row=6, column=0, padx=10, pady=5)

        # self.__set_place(150, 195)

        # 画面リサイズされた時の挙動設定
        self.root.bind("<Configure>", self.__resize_frame)

        # ×ボタンが押されたときの動作
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)

        self.root.mainloop()

    # placeによる配置 (ウィンドウサイズに合わせて動的に変更しやすくするために関数化)
    def __set_place(self, x, y):
        self.label_outfilename.place(x=x, y=y)

        label_orderer_y = y + 36
        self.label_orderer      .place(x=max(13, x - 125), y=label_orderer_y +  0)
        self.label_date         .place(x=max(13, x - 125), y=label_orderer_y + 20)
        self.label_version      .place(x=max(13, x - 125), y=label_orderer_y + 40)

        self.label_converting   .place(x=x + 80, y=label_orderer_y +  0)
        self.label_progress     .place(x=x + 80, y=label_orderer_y + 20)
        self.label_progress_line.place(x=x + 80, y=label_orderer_y + 40)

    # 機能プルダウンメニューで選択が行われたときに実施
    def __update_combbox_language(self, event):
        if (self.combbox_function.get() == self.combbox_function_values[0]):
            self.combbox_language["values"] = self.combbox_language_values_0
            self.combbox_language.set(self.combbox_language_values_0)
        else:
            self.combbox_language["values"] = self.combbox_language_values_1
            self.combbox_language.set(self.combbox_language_values_1[0])

    # リサイズ時の動作
    def __resize_frame(self, event):
        # ウィンドウサイズ取得 (動的に表示内容を切り替えるため)
        self.root.update_idletasks()
        window_width  = self.root.winfo_width()
        window_height = self.root.winfo_height()
        # print(window_width, window_height)

        # 動的に文字列を表示、非表示するコードのサンプル
        if (window_width < 560):
            self.label_header_template_0.grid_remove()
            self.label_header_template_1.grid_remove()
            self.__set_place(125, 174)
        else:
            self.label_header_template_0.grid()
            self.label_header_template_1.grid()
            self.__set_place(150, 235)

    # 終了の動作
    def __on_closing(self):
        # GUI終了, Scraping処理終了
        global GUI_END_FLG
        GUI_END_FLG = 1
        self.root.destroy()
        self._run_translate_thread.join()

    def __start_process(self):
        if (self.start_flg == 0):
            self.start_flg = 1
        else:
            print("[INFO] Process already running.")

    def __open_filedialog(self):
        filename = filedialog.askopenfilename(title="Open Text File.", filetypes=[("Text File", "*.txt")], initialdir="./")
        if (filename != ""):
            self.textbox_file_path.delete(0, tk.END)
            self.textbox_file_path.insert(tk.END, filename)

    def __run_process(self):
        global GUI_END_FLG
        while(True):
            time.sleep(0.5) # 処理付加削減のために少し止まりながら繰り返す

            if (self.start_flg == 1):
                self.filedialog_btn["state"] = "disable"
                self.button["state"] = "disable"

                print("[INFO] Process Start !!!")
                text_file_path  = re.sub("\"$", "", re.sub("^\"", "", self.textbox_file_path.get())) # windows explorerの「パスのコピー」で絶対パスを使った場合に対応するため、先頭と末尾のダブルクォーテーションを削除している
                select_language = self.combbox_language.get()

                # 出力ファイル名設定
                self.output_filename = f"{os.path.splitext(text_file_path)[0]}_trans.txt"
                self.label_outfilename["text"] = self.output_filename # 出力ファイル名を表示

                # 各設定値が空白の時はエラーを返す
                if (text_file_path == ""):
                    print("[ERROR] Text File Path is empty.")
                    self.start_flg = 0
                    self.filedialog_btn["state"] = "normal"
                    self.button["state"] = "normal"
                    continue
                if (select_language == ""):
                    print("[ERROR] Select Language is empty.")
                    self.start_flg = 0
                    self.filedialog_btn["state"] = "normal"
                    self.button["state"] = "normal"
                    continue
                # ファイルが存在しないときはエラーを返す
                if (os.path.exists(text_file_path) == False):
                    print(f"[ERROR] Text File is not found. {text_file_path}")
                    self.start_flg = 0
                    self.filedialog_btn["state"] = "normal"
                    self.button["state"] = "normal"
                    continue

                self.__run_text_translate(text_file_path, select_language)

                self.start_flg = 0
                print("[INFO] Process End...")

                if (GUI_END_FLG == 1): # GUIが閉じていたら終了する
                    break

                self.filedialog_btn["state"] = "normal"
                self.button["state"] = "normal"

            # processが実行されておらず、終了フラグがたっていたら処理を終了させる
            if (self.start_flg == 0 and GUI_END_FLG == 1):
                break

    def __run_text_translate(self, text_file_path, select_language):
        global GUI_END_FLG

        self.label_converting   ["text"] = "[ Translating ]"
        self.label_progress     ["text"] = "Progress: 0%"

        # テキストデータ読み込み
        text_header, text_dict_lists = self.__read_text(text_file_path)

        # 翻訳
        translator = Translator()
        for i, item in enumerate(text_dict_lists):
            self.label_progress_line["text"] = f"Progressing line {i+1} of {len(text_dict_lists)}"

            # 空白行 or コメントアウト行は処理しない
            if (item["Key"] == "" or item["Key"].find("<!--") != -1):
                print(f"[INFO] This row is CommentOut or empty row. So, process is skiped.")
                print(f"[INFO] {item}")
                # 進捗を進める
                self.label_progress["text"] = f"Progress: {round((i+1)/len(text_dict_lists)*100)}%"
                continue

            select_language_text = item[select_language]
            src_language = {
                "Key"      : "en",
                "english"  : "en",
                "german"   : "de",
                "latam"    : "la",
                "french"   : "fr",
                "italian"  : "it",
                "japanese" : "ja",
                "koreana"  : "ko",
                "polish"   : "pl",
                "brazilian": "pt",
                "russian"  : "ru",
                "turkish"  : "tr",
                "schinese" : "zh-cn",
                "tchinese" : "zh-tw",
                "spanish"  : "es",
            }

            if (select_language_text == ""):
                print(f"{item['Key']} is not have {select_language} word.")
                # 進捗を進める
                self.label_progress["text"] = f"Progress: {round((i+1)/len(text_dict_lists)*100)}%"
                continue

            # # ゲーム用語を単語に分割して翻訳する機能 (不採用) ※ゲーム用語はそのまま出力されてよいということなので
            # if (select_language == "Key"):
            #     print(f"[INFO] pre select_language_text: {select_language_text}")
            #     select_language_text = " ".join(re.findall("[A-Za-z][a-z0-9一-鿯]*", select_language_text))

            # for debug
            print(f"[INFO] select_language         : {select_language}")
            print(f"[INFO] select_language_text    : {select_language_text}")
            print(f"[INFO] src_language            : {src_language[select_language]}")

            # 翻訳処理 (指定の言語と翻訳後の言語が同じ場合は翻訳しない)
            SLEEP_TIME = 2 # sec. 高速でアクセスしすぎると翻訳エラーになるため
            item["english"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="en")   .text if (select_language != "english"  ) else item["english"  ]
            time.sleep(SLEEP_TIME)
            item["german"   ] = translator.translate(select_language_text, src=src_language[select_language], dest="de")   .text if (select_language != "german"   ) else item["german"   ]
            time.sleep(SLEEP_TIME)
            item["latam"    ] = translator.translate(select_language_text, src=src_language[select_language], dest="la")   .text if (select_language != "latam"    ) else item["latam"    ]
            time.sleep(SLEEP_TIME)
            item["french"   ] = translator.translate(select_language_text, src=src_language[select_language], dest="fr")   .text if (select_language != "french"   ) else item["french"   ]
            time.sleep(SLEEP_TIME)
            item["italian"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="it")   .text if (select_language != "italian"  ) else item["italian"  ]
            time.sleep(SLEEP_TIME)
            item["japanese" ] = translator.translate(select_language_text, src=src_language[select_language], dest="ja")   .text if (select_language != "japanese" ) else item["japanese" ]
            time.sleep(SLEEP_TIME)
            item["koreana"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="ko")   .text if (select_language != "koreana"  ) else item["koreana"  ]
            time.sleep(SLEEP_TIME)
            item["polish"   ] = translator.translate(select_language_text, src=src_language[select_language], dest="pl")   .text if (select_language != "polish"   ) else item["polish"   ]
            time.sleep(SLEEP_TIME)
            item["brazilian"] = translator.translate(select_language_text, src=src_language[select_language], dest="pt")   .text if (select_language != "brazilian") else item["brazilian"]
            time.sleep(SLEEP_TIME)
            item["russian"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="ru")   .text if (select_language != "russian"  ) else item["russian"  ]
            time.sleep(SLEEP_TIME)
            item["turkish"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="tr")   .text if (select_language != "turkish"  ) else item["turkish"  ]
            time.sleep(SLEEP_TIME)
            item["schinese" ] = translator.translate(select_language_text, src=src_language[select_language], dest="zh-cn").text if (select_language != "schinese" ) else item["schinese" ]
            time.sleep(SLEEP_TIME)
            item["tchinese" ] = translator.translate(select_language_text, src=src_language[select_language], dest="zh-tw").text if (select_language != "tchinese" ) else item["tchinese" ]
            time.sleep(SLEEP_TIME)
            item["spanish"  ] = translator.translate(select_language_text, src=src_language[select_language], dest="es")   .text if (select_language != "spanish"  ) else item["spanish"  ]
            time.sleep(SLEEP_TIME)

            print(item) # for debug

            # GUIが終了したときは強制終了
            if (GUI_END_FLG == 1):
                return

            # 処理が終わったら進捗を進める
            self.label_progress["text"] = f"Progress: {round((i+1)/len(text_dict_lists)*100)}%"

        # ファイル出力
        with open(self.output_filename, "w", encoding="utf-8", errors="ignore") as f:
            for i, item in enumerate(text_dict_lists):
                # ヘッダー記述 (最初だけ)
                if (i == 0):
                    f.writelines(",".join(text_header) + "\n")

                # 内容記述
                # 空白かつコメントアウト行ではないが、指定された言語が空白である場合は、処理をスキップしたことを伝える
                if (item["Key"] != "" and item["Key"].find("<!--") == -1 and item[select_language] == ""):
                    f.write("<!-- The line below is skipping translation because the selected language is blank -->\n")
                f.writelines(",".join([str(value) for value in item.values()]) + "\n")

        self.label_converting   ["text"] = "[ End of Translation ]"
        self.label_progress_line["text"] = ""

    def __read_text(self, text_file_path):
        text_header = []
        text_elems  = []

        with open(text_file_path, "r", errors="ignore", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()):
                # 改行を削除
                line = line.replace("\n", "")

                line_split = line.split(",")

                if (i == 0):
                    if (line == self.header_template):
                        text_header = line_split
                    else:
                        print("[INFO] Header is not exist.")
                        text_header = self.header_template.split(",")
                        text_elems.append(line_split)
                else:
                    # "," で分割してリストに登録
                    text_elems.append(line_split)

        # データ扱いやすいように辞書型に変換し、変換したものをリストに登録する
        text_dict_lists = []
        for elem in text_elems:
            if (elem[0] == "" or elem[0].find("<!--") != -1):
                text_dict_tmp = dict(zip(text_header, elem))
            else:
                text_dict_tmp = dict(zip_longest(text_header, elem))

                if (self.combbox_function.get() == self.combbox_function_values[0]):
                    # Noneの箇所を置換
                    for key, value in text_dict_tmp.items():
                        if (value == None):
                            text_dict_tmp[key] = ""
                
            text_dict_lists.append(text_dict_tmp)

        return text_header, text_dict_lists

def main():
    gui = GUI()

if __name__ == "__main__":
    main()