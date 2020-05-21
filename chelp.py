#!/usr/bin/python3
import re
import sys
import requests
import subprocess
import urllib.parse


class GoogleTranslator():

    def __init__(self):
        self._url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=at&dt=bd&dt=ex&' \
                    'dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&q={}'
        self._agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0'

    def get_translation(self, quoted_text):
        url = self._url.format('en-US', 'zh-CN', quoted_text)
        self._session = requests.Session()
        header = {}
        if self._agent:
            header['User-Agent'] = self._agent
        argv = {}
        argv['headers'] = header
        argv['timeout'] = float(20)
        resp = self._session.get(url, **argv)

        if resp.status_code is not 200:  # 单次请求量过大，分段发送
            mid_index = len(quoted_text) // 2
            index = quoted_text.index('%0A%0A', mid_index)
            res1 = self.get_translation(quoted_text[:index + 6])
            res2 = self.get_translation(quoted_text[index + 6:])
            res = ('\n\n' + ' ' * 7).join((res1, res2))
            return res

        try:
            obj = resp.json()
        except:
            return None
        res = self.parse_translation(obj)
        return res

    def parse_translation(self, obj):
        paraphrase = ''
        for x in obj[0]:
            if x[0]:
                paraphrase += x[0]
        return paraphrase

    def trans_manual(self, command_name):
        text = subprocess.getoutput('{} --help|cat'.format(command_name))
        text = re.sub(r'^\s+', r'', text)
        # 不翻译命令参数
        # 参数描述前应该有的空格数
        space_len = len(re.search(r'((?<=\n).*[ ]{2,})', text).group())
        desc_text = re.sub(r'((?<=\n).*[ ]{2,})', ' '*space_len, text)
        quoted_text = urllib.parse.quote_plus(desc_text)
        zh_trans = self.get_translation(quoted_text)
        # print(zh_trans)
        text = self.beautify_output(text, zh_trans)
        return text

    def beautify_output(self, en_text, zh_trans):
        """中英对照"""
        en_sections = en_text.split('\n')
        zh_sections = zh_trans.split('\n')
        # 蓝色输出中文翻译
        zh_sections_colored = []
        for sec in zh_sections:
            sec = '\033[34m' + sec + '\033[0m'
            zh_sections_colored.append(sec)


        sections = [a+'\n'+b for a, b in zip(en_sections, zh_sections_colored)]
        res = '\n'.join(sections)
        return res


def parse_options():
    options = {}
    command_name = ''
    argv = sys.argv[1:]
    for arg in argv:
        if arg[:1] != '-':
            command_name += (' ' + arg)
        else:
            key_val = arg.lstrip('-')
            key, _, val = key_val.partition('=')
            options[key.strip()] = val.strip()
    # print(options)
    # print(repr(command_name))
    return options, command_name


def main():
    print('翻译中...\r', end='')
    options, command_name = parse_options()
    translator = GoogleTranslator()
    # if 'm' in options:
    #     res = translator.trans_manual()
    res = translator.trans_manual(command_name)
    if not res: return -1
    print(res)
    return 0


if __name__ == '__main__':
    main()
