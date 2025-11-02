import os
import sys
import re
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
import threading
from pprint import pprint
import datetime
import time
from itertools import zip_longest
import shutil

from googletrans import Translator
# https://py-googletrans.readthedocs.io/en/latest/

# GUIが終了したかを管理するフラグ (アプリ全体で共通化したいのでglobal変数にしている)
GUI_END_FLG = 0

class GUI:
    def __init__(self):
        # 別プロセス実行
        self.start_flg = 0
        self._run_translate_thread = threading.Thread(target=self.__run_process)
        self._run_translate_thread.deamon = True
        self._run_translate_thread.start()

        # テンプレート文字列
        self.header_template = "Key,File,Type,UsedInMainMenu,NoTranslate,english,Context / Alternate Text,german,latam,french,italian,japanese,koreana,polish,brazilian,russian,turkish,schinese,tchinese,spanish"

        # GUI設定
        self.root = tk.Tk()

        win_width  = 570
        win_height = 450 - 70
        self.root.geometry(f"{win_width}x{win_height}")
        # self.root.state("zoomed") # ウィンドウを最大サイズで起動する

        # タイトル表示
        self.root.title("7DTD Text Translator")

        # ヘッダーテンプレート表示
        self.template_outline        = tk.Label(text="", height=4, width=79, relief=tk.SOLID, bd=1)
        self.label_template          = tk.Label(text="A. Template")
        self.header_template_split_0 = ",".join(self.header_template.split(",")[ 0: 7])
        self.header_template_split_1 = ",".join(self.header_template.split(",")[ 7:])

        self.text_header_template_0 = tk.Text(width=90, height=2, font=("Arial", 8), bg="#f0f0f0", relief="flat")
        self.text_header_template_0.insert(tk.END, ",\n".join([self.header_template_split_0, self.header_template_split_1]))
        self.text_header_template_0["state"] = "disable"

        # ファイル選択
        label_file_path = tk.Label(text="B. Text File Path")
        self.textbox_file_path = tk.Entry(width = 40)

        # 参照ボタン
        self.filedialog_btn = tk.Button(self.root, text="browse", command=self.__open_filedialog, font=("", 8))

        # モード選択 (Full or Short)
        label_select_mode = tk.Label(text="C. Select Mode")
        self.combbox_select_mode_values = ("Full", "Short")
        self.combbox_select_mode = ttk.Combobox(width = 12, height=7, values=self.combbox_select_mode_values)
        self.combbox_select_mode.set(self.combbox_select_mode_values[0]) # Fullを初期値として設定
        self.combbox_select_mode.bind("<<ComboboxSelected>>", self.__on_select_mode)

        # 言語選択プルダウンメニュー
        label_language = tk.Label(text="D. Select Language")
        self.combbox_language_values_1 = ("1.Key", "6.english","8.german","9.latam","10.french","11.italian","12.japanese","13.koreana","14.polish","15.brazilian","16.russian","17.turkish","18.schinese","19.tchinese","20.spanish")
        self.combbox_language = ttk.Combobox(width = 12, height=7, values=self.combbox_language_values_1)
        self.combbox_language.set(self.combbox_language_values_1[0]) # Keyを初期値として設定
        self.combbox_language2 = ttk.Combobox(width = 12, height=7, values=self.combbox_language_values_1)
        self.combbox_language2.set(self.combbox_language_values_1[0]) # Keyを初期値として設定
        self.label_arrow = tk.Label(text="->", width="2")

        # 出力先ファイル表示
        self.label_output      = tk.Label(text="E. Output File Path")
        self.label_outfilename = tk.Label(text="")

        # 翻訳開始ボタン
        self.button = tk.Button(self.root, text="F. Start Translation", command=self.__start_process)
        self.label_seconds_per_line = tk.Label(text="30 seconds per line")

        # 各種情報
        self.outline       = tk.Label(text="", height=4, width=17, relief=tk.SOLID, bd=1)
        self.label_orderer = tk.Label(text="I. orderer: az-jp"    )
        self.label_date    = tk.Label(text="   date: 2025/09/09"  )
        self.label_version = tk.Label(text="   version: 7DTD V2.0")

        # 実行時表示部
        self.label_converting    = tk.Label(text="")
        self.label_progress      = tk.Label(text="")
        self.label_progress_line = tk.Label(text="")

        self.label_template         .grid(row=0 , column=0, padx= 10,  pady=(10, 0)               , sticky=tk.W)
        self.text_header_template_0 .grid(row=4 , column=0, padx= 10,  pady=0       , columnspan=5, sticky=tk.W)
        label_file_path             .grid(row=5 , column=0, padx= 10,  pady=(15, 10)              , sticky=tk.W)
        self.textbox_file_path      .grid(row=5 , column=1, padx= 10,  pady=(15, 10), columnspan=5, sticky=tk.W)
        self.filedialog_btn         .grid(row=5 , column=2, padx= 150, pady=(5, 0)                , sticky=tk.W)
        label_select_mode           .grid(row=6 , column=0, padx= 10,  pady=10                    , sticky=tk.W)
        self.combbox_select_mode    .grid(row=6 , column=1, padx= 10,  pady=10                    , sticky=tk.W)
        label_language              .grid(row=7 , column=0, padx= 10,  pady=10                    , sticky=tk.W)
        self.combbox_language       .grid(row=7 , column=1, padx= 10,  pady=10                    , sticky=tk.W)
        self.label_arrow            .grid(row=7 , column=2, padx=  0,  pady=10                    , sticky=tk.W)
        self.combbox_language2      .grid(row=7 , column=2, padx= 30,  pady=10                    , sticky=tk.W)
        self.label_output           .grid(row=8 , column=0, padx= 10,  pady= 5                    , sticky=tk.W)
        self.button                 .grid(row=9 , column=0, padx= 10,  pady=(10,0)                , sticky=tk.W)
        self.label_seconds_per_line .grid(row=10, column=0, padx= 10,  pady=0                     , sticky=tk.W)

        # short用の選択肢を非表示にする
        self.label_arrow.grid_remove()
        self.combbox_language2.grid_remove()

        # 画面リサイズされた時の挙動設定
        self.root.bind("<Configure>", self.__resize_frame)

        # ×ボタンが押されたときの動作
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)

        self.root.mainloop()

    # placeによる配置 (ウィンドウサイズに合わせて動的に変更しやすくするために関数化)
    def __set_place(self, x, y, template_outline_flg):
        # templateの外枠
        if (template_outline_flg == 1):
            self.template_outline.place(x=7, y=5)
        else:
            self.template_outline.place_forget()

        self.label_outfilename.place(x=x, y=y)

        label_orderer_y = y + 82
        self.outline            .place(x=10    , y=label_orderer_y -  2 + 15)
        self.label_orderer      .place(x=14    , y=label_orderer_y +  0 + 15)
        self.label_date         .place(x=14    , y=label_orderer_y + 20 + 15)
        self.label_version      .place(x=14    , y=label_orderer_y + 40 + 15)

        self.label_converting   .place(x=x, y=label_orderer_y +  0 - 42)
        self.label_progress     .place(x=x, y=label_orderer_y + 20 - 42)
        self.label_progress_line.place(x=x, y=label_orderer_y + 40 - 42)

    # リサイズ時の動作
    def __resize_frame(self, event):
        # ウィンドウサイズ取得 (動的に表示内容を切り替えるため)
        self.root.update_idletasks()
        self.__set_place(160, 255 - 60, template_outline_flg=1)

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
                text_file_path   = re.sub("\"$", "", re.sub("^\"", "", self.textbox_file_path.get())) # windows explorerの「パスのコピー」で絶対パスを使った場合に対応するため、先頭と末尾のダブルクォーテーションを削除している
                select_language  = re.sub("[0-9]+\.", "", self.combbox_language .get())
                select_language2 = re.sub("[0-9]+\.", "", self.combbox_language2.get())
                select_mode      = self.combbox_select_mode.get()

                # Shortモードで、翻訳先言語が元の言語と同じ場合はエラーを返す
                if (select_mode == "Short" and select_language == select_language2):
                    print("[ERROR] In Short Mode, the target language cannot be the same as the source language.")
                    self.start_flg = 0
                    self.filedialog_btn["state"] = "normal"
                    self.button["state"] = "normal"
                    continue

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

                # 元のファイルをoldとしてコピー
                shutil.copy(text_file_path, os.path.splitext(text_file_path)[0] + "_old.txt")

                # 出力ファイル名設定
                self.output_filename = text_file_path # f"{os.path.splitext(text_file_path)[0]}_trans.txt"
                self.label_outfilename["text"] = f"G. {self.output_filename}" # 出力ファイル名を表示

                self.__run_text_translate(text_file_path, select_language, select_language2, select_mode)

                self.start_flg = 0
                print("[INFO] Process End...")

                if (GUI_END_FLG == 1): # GUIが閉じていたら終了する
                    break

                self.filedialog_btn["state"] = "normal"
                self.button["state"] = "normal"

            # processが実行されておらず、終了フラグがたっていたら処理を終了させる
            if (self.start_flg == 0 and GUI_END_FLG == 1):
                break

    def __on_select_mode(self, event):
        select_mode = self.combbox_select_mode.get()
        if (select_mode == "Full"):
            self.label_arrow.grid_remove()
            self.combbox_language2.grid_remove()
        elif (select_mode == "Short"):
            self.label_arrow.grid()
            self.combbox_language2.grid()

    def __run_text_translate(self, text_file_path, select_language, select_language2, select_mode):
        global GUI_END_FLG

        self.label_converting   ["text"] = "[ H. Translating ]"
        self.label_progress     ["text"] = "Progress: 0%"

        # 処理開始した時間を取得
        process_start_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # テキストデータ読み込み
        text_header, text_dict_lists = self.__read_text(text_file_path, select_language, select_mode)

        # 翻訳
        translator = Translator()
        for i, item in enumerate(text_dict_lists):
            self.label_progress_line["text"] = f"Progressing line {i+1} of {len(text_dict_lists)}"

            # 空白行 or コメントアウト行は処理しない
            print(item)
            if (item["Key"] == "" or item["Key"].find("<!--") != -1 or item["Key"] == "Key"):
                print(f"[INFO] This row is CommentOut or empty row or multi key line. So, process is skiped.")
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

            # for debug
            print(f"[INFO] select_language         : {select_language}")
            print(f"[INFO] select_language_text    : {select_language_text}")
            print(f"[INFO] src_language            : {src_language[select_language]}")

            translate_start_time = time.time()

            # 翻訳処理 (指定の言語と翻訳後の言語が同じ場合は翻訳しない)
            for key_language in src_language:
                # Keyは翻訳しない
                if (key_language == "Key"):
                    continue

                if (select_mode == "Short" and key_language != select_language2):
                    print(f"[INFO] Short Mode is selected. So, skip translating {key_language}.")
                    continue

                # 翻訳
                item[key_language] = self.__run_googletrans(translator,
                                                            select_language_text,
                                                            select_language,
                                                            src_language[select_language],
                                                            src_language[key_language],
                                                            key_language)

            print(f"Translate Time: {time.time() - translate_start_time}")

            # GUIが終了したときは強制終了
            if (GUI_END_FLG == 1):
                break

            # 処理が終わったら進捗を進める
            self.label_progress["text"] = f"Progress: {round((i+1)/len(text_dict_lists)*100)}%"

        # ファイル出力
        with open(self.output_filename, "w", encoding="utf-8", errors="ignore") as f:
            # 翻訳結果を記入
            for i, item in enumerate(text_dict_lists):
                # ヘッダー記述 (最初だけ)
                if (i == 0):
                    f.writelines(",".join(text_header) + "\n")
                    # 処理開始時間をコメントアウトで記入
                    f.write(f"translationdate,,{process_start_time}{','*17}\n")

                # 内容記述
                if (item["Key"] == "Key"):
                    print(f"Multi Key line is detected. So, skip writing this line.")
                    continue

                # 空白かつコメントアウト行ではないが、指定された言語が空白である場合は、処理をスキップしたことを伝える
                if (item["Key"] != "" and item["Key"].find("<!--") == -1 and item[select_language] == ""):
                    f.write("<!-- The line below is skipping translation because the selected language is blank -->\n")

                # 翻訳した内容を書き込む
                if (select_mode == "Full"):
                    f.writelines(",".join([str(value) for value in item.values()]) + "\n")
                else:
                    write_value = f"{item['Key']},{item[select_language2]}\n" if (select_language2 in item) else ",".join([str(value) for value in item.values()]) + "\n"
                    f.writelines(write_value)
                
            # GUIが終了してたら、GUI Labelに書き込む記述を実行する前にreturnしてあげる(固まらないように)
            if (GUI_END_FLG == 1):
                return

        self.label_converting   ["text"] = "[ H. End of Translation ]"
        self.label_progress_line["text"] = ""

    def __run_googletrans(self, translator, select_language_text, select_language, src_lang, dest_lang, language):
        SLEEP_TIME = 2 # sec. 高速でアクセスしすぎると翻訳エラーになるため

        trans_text = ""

        global GUI_END_FLG
        if (GUI_END_FLG == 1):
            print("[INFO] GUI is END. So, Do not Translation.")
            return trans_text

        try:
            print(f"[INFO] translate: {src_lang} ---> {dest_lang}. language: {language}.")
            if (select_language != language):
                trans_text = translator.translate(select_language_text, src=src_lang, dest=dest_lang).text
                trans_text = trans_text.replace(",", "") # 文章中のカンマを削除する
                print(f"[INFO] {select_language_text} ---> {trans_text}")
            else:
                trans_text = select_language_text
                print(f"[INFO] {select_language} == {language}. So, Do not Translation.")

            # ゲーム内改行コードの前後の空白を削除 (前後ろを分けて置換しているのは、一度に置換してしまうと\nが並んでいるときに、後空白が残ってしまう可能性があるため)
            trans_text = trans_text.replace(" \\n", "\\n") # 前空白
            trans_text = trans_text.replace("\\n ", "\\n") # 後空白
        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(SLEEP_TIME)

        return trans_text

    def __read_text(self, text_file_path, select_language, select_mode):
        text_header = []
        text_elems  = []

        with open(text_file_path, "r", errors="ignore", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()):
                # 改行を削除
                line = line.replace("\n", "")
                # 改行がつながっている場合は、削除する
                line = line.replace("\\n\\n", "")
                # ゲーム内改行コードは、前後に空白を入れる
                line = line.replace("\\n", " \\n ")
                # 文章中の " を削除する
                line = line.replace("\"", "")

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
                if (select_mode == "Full"):
                    text_dict_tmp = dict(zip_longest(text_header, elem))
                else:
                    # Keyの場合はenglishとして扱う
                    select_language = select_language if (select_language != "Key") else "english"

                    text_dict_tmp = {
                        "Key": elem[0],
                        select_language: elem[1],
                    }

            text_dict_lists.append(text_dict_tmp)

        return text_header, text_dict_lists

def main():
    gui = GUI()

if __name__ == "__main__":
    main()