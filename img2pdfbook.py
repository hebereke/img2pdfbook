#!/usr/bin/env python
# coding: utf-8
import os
import re
import math
import argparse
import tkinter as tk
import tkinter.filedialog as tkf
import img2pdf
from PIL import Image

class LayoutProp:
    SIZE_MM ={
        'Paperback' : (105, 148),
        'B6' : (128, 182),
        'A5' : (148, 210),
        'B5' : (182, 257),
        'A4' : (210, 297),
    }
    def __init__(self, size='B5', pixel=96):
        try:
            self.size = SIZE_MM[size]
        except KeyError:
            print('Does not support {}. Use B5 instead of.')
            print('Support page size are {}'.format(size, ','.join(LayoutProp.SIZE_MM.keys())))
            size = SIZE_MM['B5']
    def get_img2pdfFunc(self):
        pagesize=(img2pdf.mm_to_pt(self.size[0]), img2pdf.mm_to_pt(self.size[1]))
        return img2pdf.get_layout_fun(pagesize)

def jpg2pdf(imgs, outpdf, size=None):
    with open(outpdf, 'wb') as f:
        print('output {}'.format(outpdf))
        if size is None:
            f.write(img2pdf.convert(imgs))
        else:
            f.write(img2pdf.convert(imgs, layout_fun=LayoutProp(size).get_img2pdfFunc()))

def get_img_folders(img_folder_root):
    img_folder_root = os.path.abspath(img_folder_root)
    if not os.path.isdir(img_folder_root):
        raise Exception('invalid img_folder: {}'.format(img_folder_root))
    # input images
    img_folders = [os.path.join(img_folder_root, d.name) for d in os.scandir(img_folder_root) if d.is_dir()]
    img_folders.sort(key=lambda x: int(re.match('[^\d]*(\d+)[^\d]*',x).group(1)))
    return img_folders

def output(output_pdf, output_dir, img_folder):
    # output
    if os.path.dirname(output_pdf) == '':
        out_dir = img_folder
        out_file = output_pdf
    else:
        output = os.path.split(output_pdf)
        out_dir = os.path.abspath(output[0])
        out_file = output[1]
    if output_dir is not None:
        out_dir = os.path.abspath(output_dir)
    if not os.path.isdir(out_dir):
        raise Exception('invalid output folder: {}'.format(out_dir))
    return os.path.join(out_dir, out_file)

def convert(params):
    if params.debug:
        print(['{}={}, '.format(p, getattr(params, p)) for p in vars(params)])
    if params.recursive:
        img_folders = get_img_folders(params.img_folder)
    else:
        img_folders = [params.img_folder]
    index = 1
    for d in img_folders:
        imgs = Images(d, params)
        output_pdf = output(params.output_pdf, params.output_dir, params.img_folder)
        if params.recursive:
            out = os.path.splitext(output_pdf)
            out_pdf = out[0] + params.suffix.format(index)
            index += 1
        else:
            out_pdf = output_pdf
        out_pdf = out_pdf + '.pdf'
        if params.debug:
            print(d, imgs.imgs, out_pdf)
        if len(imgs.imgs) > 0:
            jpg2pdf(imgs.imgs, out_pdf)
        if len(imgs.conv_imgs) > 0:
            for f in imgs.conv_imgs:
                os.remove(f)

class Images:
    def __init__(self, folder=None, params=None):
        self.folder = os.path.abspath(folder)
        if not os.path.isdir(self.folder):
            raise Exception('invalid folder: {}'.format(self.folder))
        self.tmpdir = os.path.abspath(params.tmpdir)
        if not os.path.isdir(self.tmpdir):
            raise Exception('invalid tmpdir: {}'.format(self.tmpdir))
        self.imgs = []
        self.conv_imgs = []
        self.makelist(params)
    @staticmethod
    def str2list(strings, end):
        list = []
        for token in strings.split(','):
            token = token.strip()
            m1 = re.match('^\d+$', token)
            m2 = re.match('^(\d+)\-(\d+)$', token)
            m3 = re.match('^(\d+)\-$', token)
            if m1:
                list.append(int(token))
            elif m2:
                s = int(m2.group(1))
                e = int(m2.group(2))
                if s>e:
                    raise ValueError('invalid range: {}'.format(token))
                elif s==e:
                    list.append(s)
                else:
                    list += [i for i in range(s,e+1)]
            elif m3:
                list += [i for i in range(int(m3.group(1)),int(end)+1)]
            else:
                pass
        return list
    def makelist(self, params=None):
        files = [file.name for file in os.scandir(self.folder) if file.is_file()]
        basename = lambda f: os.path.basename(f)
        if len(files) > 0:
            files.sort(key=basename)
        if params.splitpage is not None:
            splitpages = self.str2list(params.splitpage, len(files))
        else:
            splitpages = None
        for i in range(len(files)):
            f = os.path.join(self.folder, files[i])
            print(f, os.path.basename(f), re.match('[^\d]*(\d+)[^\d]*', os.path.basename(f)).group(0))
            try:
                img = Image.open(f)
            except:
                print('skip {} which is not available image'.format(f))
                continue
            if splitpages is not None and splitpages.count(i+1) > 0:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                imgw = img.size[0]
                imgh = img.size[1]
                imgw_crop = img.size[0] - params.splitmargin
                imgw_half = math.floor(img.size[0]/2)
                img1 = img.crop((params.splitmargin, 0, imgw_half, imgh))
                img2 = img.crop((imgw_half, 0, imgw_crop, imgh))
                of = os.path.basename(f)
                of = os.path.splitext(of)[0]
                of1 = os.path.join(self.tmpdir, of + '_1.jpg')
                img1.save(of1, quality=95)
                self.conv_imgs.append(of1)
                self.imgs.append(of1)
                of2 = os.path.join(self.tmpdir, of + '_2.jpg')
                img2.save(of2, quality=95)
                self.conv_imgs.append(of2)
                self.imgs.append(of2)
            elif img.format != 'JPG':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                of = os.path.basename(f)
                of = os.path.splitext(of)[0]
                of = os.path.join(self.tmpdir, of + '.jpg')
                img.save(of, quality=95)
                self.conv_imgs.append(of)
                self.imgs.append(of)
            else:
                self.imgs.append(f)
        if len(self.imgs) > 0:
            self.imgs.sort(key=lambda f: int(re.match('[^\d]*(\d+)[^\d]*', os.path.basename(f)).group(1))

class Parameters:
    def __init__(self, initargs=None):
        parser = argparse.ArgumentParser(description='convert Image files to single PDF')
        parser.add_argument('img_folder', help='folder of input images', nargs='?', default='.')
        parser.add_argument('-o', '--output_pdf', help='output file name', metavar='FILE', default='output')
        parser.add_argument('-d', '--output_dir', help='output directory', default=None, metavar='DIR')
        parser.add_argument('--nogui', help='start with CUI', action='store_true')
        parser.add_argument('-r', '--recursive', help='recursive mode', action='store_true')
        parser.add_argument('-s', '--suffix', help='suffix of output file name with recursive mode', default=' 第{:02d}巻')
        parser.add_argument('-t', '--tmpdir', help='temporary directory', metavar='DIR', default=None)
        parser.add_argument('--split', help='split image to 2 pages', action='store_true')
        parser.add_argument('--splitmargin', help='crop margin at left/right side to split image in pixel', default=0)
        parser.add_argument('--splitpage', help='pages to be split', default=None) # format, '1-, 4-7'
        #parser.add_argument('--merge', help='merge 2 img into single page', default=0)
        #parser.add_argument('--mergepage', help='pages to be merged', default=None) # format, '1-, 4-7'
        parser.add_argument('--debug', help='debug mode', action='store_true')
        args = parser.parse_args(initargs)
        for arg in vars(args):
            setattr(self, arg, getattr(args, arg))
        if self.output_dir is None:
            self.output_dir = self.img_folder
        if self.tmpdir is None:
            self.tmpdir = self.img_folder
    def setOutput(self):
        if os.path.dirname(self.output_pdf) == '':
            out_dir = img_folder
            out_file = output_pdf
        else:
            output = os.path.split(self.output_pdf)
            out_dir = os.path.abspath(output[0])
            out_file = output[1]
        if self.output_dir is not None:
            out_dir = os.path.abspath(self.output_dir)
        if not os.path.isdir(out_dir):
            raise Exception('invalid output folder: {}'.format(out_dir))
        return os.path.join(out_dir, out_file)

class guiMain(tk.Frame):
    def __init__(self, master=None, params=None):
        super().__init__()
        self.master.title(u'img2pdfbook')
        self.master.geometry('550x250')
        if params is None:
            self.params = Parameters()
        else:
            self.params = params
        self.paramsEntry = {}
        self.create_widgets()
        self.pack()
    def create_widgets(self):
        self.imgfolder_dirdiag = guiDirDiag(master=self, label=u'入力フォルダ', initdir=self.params.img_folder)
        self.outfolder_dirdiag = guiDirDiag(master=self, label=u'出力フォルダ', initdir=self.params.output_dir)
        self.outputpdf_textbox = guiTextEntry(master=self, label=u'出力ファイル名', inittext=self.params.output_pdf, boxwidth=40)
        self.imgfolder_dirdiag.pack(anchor=tk.W)
        self.outfolder_dirdiag.pack(anchor=tk.W)
        self.outputpdf_textbox.pack(anchor=tk.W)

        frame_recursive = tk.Frame(master=self)
        self.suffix_textbox = guiTextEntry(master=frame_recursive, label=u'添字', boxwidth=10, inittext=self.params.suffix)
        self.recursive_check = guiRadioButton(master=frame_recursive, label=u'入力フォルダ以下の各フォルダで変換', initcond=self.params.recursive,
            slave_widget=None)
        self.suffix_textbox.grid(row=0, column=1)
        self.recursive_check.grid(row=0, column=0, sticky=tk.W)
        frame_recursive.pack(anchor=tk.W)

        frame_split = tk.Frame(master=self)
        frame_split_textbox = tk.Frame(master=frame_split)
        self.splitpages_textbox = guiTextEntry(master=frame_split_textbox, label=u'分割するページ', boxwidth=5, inittext=self.params.splitpage or '')
        self.splitmargin_textbox = guiTextEntry(master=frame_split_textbox, label=u'分割する際の左右マージン', boxwidth=2, inittext=self.params.splitmargin)
        self.splitpages_textbox.grid(row=0, column=0)
        self.splitmargin_textbox.grid(row=0, column=1)
        self.split_check = guiRadioButton(master=frame_split, label=u'ページを分割', initcond=self.params.split,
            slave_widget=None)
        frame_split_textbox.grid(row=0, column=1)
        self.split_check.grid(row=0, column=0, sticky=tk.W)
        frame_split.pack(anchor=tk.W)

        frame_bottom = tk.Frame(master=self)
        button1 = tk.Button(master=frame_bottom, text="実行", command=self.convert)
        button2 = tk.Button(master=frame_bottom, text=("閉じる"), command=quit)
        button1.grid(row=0, column=0)
        button2.grid(row=0, column=1)
        frame_bottom.pack()
    def convert(self):
        self.params.img_folder = self.imgfolder_dirdiag.entry.get()
        self.params.output_dir = self.outfolder_dirdiag.entry.get()
        self.params.output_pdf = self.outputpdf_textbox.entry.get()
        self.params.recursive = self.recursive_check.entry.get()
        self.params.suffix = self.suffix_textbox.entry.get()
        self.params.split = self.split_check.entry.get()
        self.params.splitmargin = self.splitmargin_textbox.entry.get()
        self.params.splitpage = self.splitpages_textbox.entry.get()
        convert(params)

class guiDirDiag(tk.Frame):
    def __init__(self, master=None, label=None, initdir=None, width=100, boxwidth=30):
        super().__init__(master=master)
        self.label = label
        self.initdir = initdir
        self.boxwidth = boxwidth
        self.width = width
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.StringVar()
        self.entry.set(self.initdir)
        box = tk.Entry(self, textvariable=self.entry, width=self.boxwidth)
        label = tk.Label(self, text=self.label)
        button = tk.Button(self, text=u'フォルダ選択', command=self.dirdialog_clicked)
        label.pack(side=tk.LEFT, anchor=tk.W)
        box.pack(side=tk.LEFT)
        button.pack(side=tk.LEFT)
    def dirdialog_clicked(self):
        initdir = os.path.abspath(os.path.dirname(self.entry.get()))
        dir = tkf.askdirectory(initialdir = initdir)
        if dir is not None:
            self.entry.set(dir)

class guiTextEntry(tk.Frame):
    def __init__(self, master=None, label=None, inittext=None, boxwidth=30):
        super().__init__(master=master)
        self.label = label
        self.inittext = inittext
        self.boxwidth = boxwidth
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.StringVar()
        self.entry.set(self.inittext)
        box = tk.Entry(self, textvariable=self.entry, width=self.boxwidth)
        label = tk.Label(self, text=self.label)
        label.pack(side=tk.LEFT, anchor=tk.W)
        box.pack(side=tk.LEFT)

class guiRadioButton(tk.Frame):
    def __init__(self, master=None, label=None, initcond=False, slave_widget=None):
        super().__init__(master=master)
        self.label = label
        self.initcond = initcond
        self.slave_widget = slave_widget
        self.create_widgets()
        if slave_widget is not None:
            self.interactive()
    def create_widgets(self):
        self.entry = tk.BooleanVar()
        self.entry.set(self.initcond)
        if self.slave_widget is not None:
            checkbox = tk.Checkbutton(master=self, text=self.label, variable=self.entry, command=self.interactive)
        else:
            checkbox = tk.Checkbutton(master=self, text=self.label, variable=self.entry)
        checkbox.pack(side=tk.LEFT, anchor=tk.W)
    def interactive(self):
        if self.entry.get():
            self.slave_widget.grid()
        else:
            self.slave_widget.grid_remove()

if __name__ == '__main__':
    params = Parameters()
    if params.nogui:
        convert(params)
    else:
        root = tk.Tk()
        gui = guiMain(master=root, params=params)
        gui.mainloop()