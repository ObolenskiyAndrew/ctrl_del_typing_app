import time
from datetime import date
from tkinter import Tk, Button, Label, Text, Frame, TclError
from tkinter import filedialog as fd
import os
from sys import exit
from csv import reader, writer
import re
import string
import unicodedata


class App(Tk):
    def __init__(self):
        super().__init__()

        # configure the window
        self.title('Typing app')
        self.configure(bg='#323437')

        x_margin = max((self.winfo_screenwidth() - 1150) / 2, 0)
        y_margin = max((self.winfo_screenheight() - 300) / 3.1, 0)
        self.geometry(f'1150x300+{int(x_margin)}+{int(y_margin)}')
        self.resizable(0, 0)

        # configure the frame with text
        self.main_frame = Frame(self, width=920, height=200, bg='#323437')
        self.main_frame.pack(side='top', pady=65, expand=True, fill=None)

        # import and display text
        self.update()
        self.text = TextForTyping()

        # configure timer
        self.timer = Label(
            self.main_frame,
            text='00:00',
            bg='#323437',
            font=('Ubuntu', 18),
            fg="#e2b714"
        )
        self.is_running = False
        self.start_time = time.perf_counter()
        self.TIME_BEFORE_STOP = 5
        self.timer.grid(row=1, column=1, sticky='w')

        # configure progress label
        progress_percent = round(self.text.words_typed / self.text.words_overall * 100, 1)

        self.progress_label = Label(
            self.main_frame,
            bg='#323437',
            text=f' {progress_percent}%    {self.text.words_typed} / {self.text.words_overall}',
            font=('Ubuntu', 18),
            fg="#e2b714"
        )

        self.progress_label.grid(row=1, column=2, columnspan=3, sticky='w')

        # configure button "Select file"
        self.button_select_file = Button(
            self.main_frame,
            text='Select File',
            bg='#323437',
            borderwidth=0,
            font=('Ubuntu', 18),
            fg='#646669',
            activebackground="#323437",
            activeforeground='#e2b714'
        )

        self.button_select_file['command'] = self.text_change
        self.button_select_file.grid(row=1, column=8)

        # set initial values for typing field
        self.letter_number = 0
        self.row_number = 1

        self.typing_field = Text(
            self.main_frame,
            bg='#323437',
            borderwidth=0,
            fg='#646669',
            font=('Ubuntu', 16),
        )

        self.typing_error = False
        self.errors_count = 0
        self.typing_field.tag_config("typed", foreground="#cccbc2")
        self.typing_field.tag_config("error", foreground="#ca4754")
        self.typing_field.insert('1.0', '\n'.join(self.text.text[self.text.symbols_typed:].split('\n')[:3]))
        self.typing_field.configure(state='disabled')
        self.typing_field.grid(row=2, column=1, columnspan=8)

        # activate keyboard listener
        self.bind('<Key>', self.key_listener)

    def text_change(self):
        """Display new text according to newly selected path."""
        path = self.path_select()

        self.text = TextForTyping(path)

        progress_percent = round(self.text.words_typed / self.text.words_overall * 100, 1)
        self.progress_label.config(text=f' {progress_percent}%    {self.text.words_typed} / {self.text.words_overall}')

        self.timer.config(text='00:00')

        self.typing_field.configure(state='normal')
        self.typing_field.delete("1.0", "end")
        self.typing_field.insert('1.0', '\n'.join(self.text.text[self.text.symbols_typed:].split('\n')[:3]))
        self.typing_field.configure(state='disabled')

        self.letter_number = 0
        self.row_number = 1

        self.bind('<Key>', self.key_listener)

    @staticmethod
    def path_select():
        """Ask for new path to .txt file with text for typing."""

        path = fd.askopenfilename(
            title='Select file with text',
            filetypes=(('text files', '*.txt'),)
        )

        if path == '':
            exit(0)

        return path

    def timer_start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.perf_counter()
            self.timer_update()
            self.errors_count = 0

    def timer_stop(self):
        self.is_running = False
        self.make_log()

    def timer_update(self):
        if self.is_running:
            elapsed_time = time.perf_counter() - self.start_time
            minutes = '0' + str(int(elapsed_time // 60)) if elapsed_time // 60 < 10 else str(int(elapsed_time // 60))
            seconds = '0' + str(int(elapsed_time % 60)) if elapsed_time % 60 < 10 else str(int(elapsed_time % 60))
            self.timer.config(text=minutes + ':' + seconds)
            self.timer.after(500, self.timer_update)

            if self.text.symbols_typed == self.text.symbols_overall:
                self.last_letter_time -= self.TIME_BEFORE_STOP
                self.timer_stop()
            elif time.perf_counter() - self.last_letter_time > self.TIME_BEFORE_STOP:
                self.timer_stop()

    def next_letter(self, letter=None, error=None):
        """
        Update displayed letters in the text field and progress label.

        If:
        1.1) transition to third row - deletes first row and adds new third row
        1.2) transition to second row (when started) - changes typing row to second

        2.1) error in letter - highlight it as error, if error where should be space: inserts error letter after word
        2.2) correct letter - transition to next letter
        """
        self.typing_field.configure(state='normal')

        # transition to new row
        if self.text.text[self.text.symbols_typed] == '\n' and not error:

            if self.row_number == 2:
                self.typing_field.delete("1.0", "2.0")
                self.typing_field.insert("end", '\n' + self.text.text[self.text.symbols_typed:].split('\n')[2])
                self.row_number -= 1

            self.letter_number = 0
            self.row_number += 1

        # transition to new letter or error
        else:
            if error:
                if self.text.text[self.text.symbols_typed] in [' ', '\n']:
                    self.typing_field.insert(f"{self.row_number}.{self.letter_number}", letter)

                self.typing_field.tag_add("error", f"{self.row_number}.{self.letter_number}")

            else:
                self.typing_field.tag_add("typed", f"{self.row_number}.{self.letter_number}")
            self.letter_number += 1

        self.text.symbols_typed += 1
        self.typing_field.configure(state='disabled')

        # update of progress label
        end = self.text.symbols_typed == self.text.symbols_overall
        if self.text.text[min(self.text.symbols_typed, self.text.symbols_overall-1)] in [' ', '\n'] or end:
            self.text.words_typed += 1
            progress_percent = round(self.text.words_typed / self.text.words_overall * 100, 1)
            self.progress_label.config(text=f' {progress_percent}%    '
                                                f'{self.text.words_typed} / {self.text.words_overall}')

    def key_listener(self, event=None):
        """
        Get pressed key value and time. If key is suitable ask for typing field update.

        If:
        1.1) end of the text - don't add symbols

        2.1) correct appropriate latter/space - make transition to next letter
        2.2) wrong appropriate latter/space - mark error
        2.3) ctrl+del - delete typed word
        """
        try:
            self.last_letter_time = time.perf_counter()
            if self.text.symbols_typed == self.text.symbols_overall:
                return

            RU = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
            if not self.typing_error and event.char and event.char in string.printable + RU:
                new_line = self.text.text[self.text.symbols_typed] == '\n' and (event.char == ' ' or event.char == '\r')

                if event.char == self.text.text[self.text.symbols_typed] or new_line:
                    self.next_letter()

                    if not self.is_running:
                        self.timer_start()

                else:
                    self.typing_error = True
                    self.next_letter(letter=event.char, error=True)
                    self.errors_count += 1

            if event.char == "":
                self.ctrl_del()

        except TclError:
            pass

    def ctrl_del(self):
        """Delete typed word with or without error and update word counter."""
        # first letter of the line issue fix
        if self.letter_number == 0:
            return

        # update word counter
        if self.text.text[self.text.symbols_typed] in [' ', '\n'] or \
                self.text.text[self.text.symbols_typed - 1] in [' ', '\n']:
            self.text.words_typed -= 1
            progress_percent = round(self.text.words_typed / self.text.words_overall * 100, 1)
            self.progress_label.config(text=f' {progress_percent}%    '
                                            f'{self.text.words_typed} / {self.text.words_overall}')

        # delete typed word with or without error
        self.typing_field.configure(state='normal')
        text_typed = self.text.text[:self.text.symbols_typed]

        if text_typed[-1] in [' ', '\n']:
            if self.typing_error:
                self.typing_field.delete(f"{self.row_number}.{self.letter_number - 1}")
            text_typed = text_typed[:-1]

        shift = self.text.symbols_typed - max(max(text_typed.rfind(' '), 0), max(text_typed.rfind('\n'), 0))

        self.typing_field.tag_remove(
            "typed",
            f"{self.row_number}.{self.letter_number - shift}",
            f"{self.row_number}.{self.letter_number}"
        )

        self.typing_field.tag_remove(
            "error",
            f"{self.row_number}.{self.letter_number - 1}"
        )

        self.text.symbols_typed -= shift - 1
        self.letter_number -= shift - 1

        # first world issue fix
        if f"{self.row_number}.{self.letter_number}" == '1.1':
            self.text.symbols_typed -= 1
            self.letter_number -= 1

        self.typing_error = False
        self.typing_field.configure(state='disabled')

    def make_log(self):
        """Make loge in format: current time and date, start symbol, stop symbol, average speed, average accuracy."""
        time_and_date = time.strftime("%H:%M:%S", time.localtime()) + ' ' + str(date.today())
        start = int(self.text.logs[-1][2]) if len(self.text.logs) > 1 else 0
        stop = self.text.symbols_typed

        if self.text.symbols_typed != self.text.symbols_overall:
            if self.text.text[self.text.symbols_typed] in [' ', '\n']:
                stop += 1

        words_typed = (stop - start) / 5
        time_typed = time.perf_counter() - self.start_time - self.TIME_BEFORE_STOP

        avg_speed = words_typed / time_typed * 60
        if stop != start:
            avg_accuracy = (1 - self.errors_count / (stop - start)) * 100
        else:
            return

        log = [time_and_date, start, stop, avg_speed, avg_accuracy]
        logs_path = "logs" + os.sep + os.path.basename(self.text.path.split('.')[0]) + '.csv'
        with open(logs_path, "w") as f:
            wr = writer(f)
            wr.writerows(self.text.logs + [log])


class TextForTyping:
    def __init__(self, path=None):

        if path:
            self.path = path
            with open('last_link.txt', "w", encoding="utf-8") as f:
                f.write(path)
        else:
            self.path = self.get_path()

        self.logs = self.get_logs()
        self.text = self.get_text()
        self.symbols_typed = self.get_symbols_typed()
        self.symbols_overall = self.get_symbols_overall()
        self.words_typed = self.get_words_typed()
        self.words_overall = self.get_words_overall()

    def __repr__(self):
        return os.path.basename(self.path)

    @staticmethod
    def get_path():
        """Get path from last_link.txt or ask for new path."""
        if os.path.isfile('last_link.txt'):
            with open('last_link.txt', "r", encoding="utf-8") as f:
                path = f.read()

            if path:
                return path

        path = App.path_select()

        with open('last_link.txt', "w", encoding="utf-8") as f:
            f.write(path)

        return path

    def get_logs(self):
        """Get logs from logs.csv or create new logs.csv file."""
        if not os.path.isdir('logs'):
            os.mkdir('logs')

        path_logs = "logs" + os.sep + os.path.basename(self.path.split('.')[0]) + '.csv'

        if os.path.isfile(path_logs):
            with open(path_logs, "r") as f:
                logs = [i for i in reader(f) if i]

        else:
            logs = [['date', 'start', 'stop', 'avg_speed', 'avg_accuracy']]
            with open(path_logs, "w") as f:
                wr = writer(f)
                wr.writerows(logs)

        return logs

    def get_text(self):
        """Get text from the path to cleared .txt file or indicates that there is no text."""
        if not os.path.isdir('texts'):
            os.mkdir('texts')

        path_text = "texts" + os.sep + os.path.basename(self.path)

        if os.path.isfile(path_text):
            with open(path_text, "r", encoding="utf-8") as f:
                text = f.read()

        else:
            text = self.clear_text()

        if not text:
            text = 'No text in this file :('

        return text

    def get_symbols_typed(self):
        if len(self.logs) < 2:
            start = 0
        else:
            start = int(self.logs[-1][2])

        return int(start)

    def get_symbols_overall(self):
        return len(self.text)

    def get_words_typed(self):
        return len(self.text[:self.symbols_typed].split())

    def get_words_overall(self):
        return len(self.text.split())

    def clear_text(self, max_symbols=65):
        """Format text form .txt file from path to new file."""
        with open(self.path, 'r', encoding='utf-8') as f:
            text_all = f.read()

        text_clear = ''.join(c for c in text_all if not unicodedata.category(c) in ['Cf', 'Cs', 'Co', 'Cn', 'C'])
        # text_clear = text_all.encode("ascii", errors="ignore").decode()
        text_clear = re.sub(' +', ' ', text_clear.replace('—', ' - ').strip())
        text_clear = re.sub('\n+', '\n', text_clear)
        text_clear = text_clear.replace(' \n', '\n').replace('\n ', '\n')
        text_clear = re.sub('[“«»„”‹›‘’]', '"', text_clear)

        strings = []
        string = ''
        for word in text_clear.replace('\n', ' \n').split(' '):
            if '\n' in word:
                strings.append(string)
                string = word.replace('\n', '')

            elif len(string + ' ' + word) > max_symbols:
                strings.append(string)
                string = word

            else:
                if string:
                    string += ' ' + word
                else:
                    string += word

        strings.append(string)

        text = '\n'.join(strings)
        path_text = "texts" + os.sep + os.path.basename(self.path)
        with open(path_text, 'w', encoding='utf-8') as f:
            f.write(text)

        return text


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    app = App()
    app.mainloop()
