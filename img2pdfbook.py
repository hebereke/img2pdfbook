#!/usr/bin/env python
# coding: utf-8
import os
import re
import argparse
import tkinter as tk
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
    img_folders.sort()
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

def convert(img_folder, output_dir, output_pdf, recursive, suffix, tmpdir):
    #print(img_folder, output_dir, output_pdf, recursive, suffix)
    if recursive:
        img_folders = get_img_folders(img_folder)
    else:
        img_folders = [img_folder]
    index = 1
    for d in img_folders:
        imgs = Images(d, tmpdir)
        output_pdf = output(output_pdf, output_dir, img_folder)
        if recursive:
            out = os.path.splitext(output_pdf)
            out_pdf = out[0] + suffix.format(index)
            index += 1
        else:
            out_pdf = output_pdf
        out_pdf = out_pdf + '.pdf'
        #print(d, imgs.imgs, out_pdf)
        if len(imgs.imgs) > 0:
            jpg2pdf(imgs.imgs, out_pdf)
        if len(imgs.conv_imgs) > 0:
            for f in imgs.conv_imgs:
                os.remove(f)

class Images:
    def __init__(self, folder=None, tmpdir=None):
        self.folder = os.path.abspath(folder)
        if not os.path.isdir(self.folder):
            raise Exception('invalid folder: {}'.format(self.folder))
        self.tmpdir = os.path.abspath(tmpdir)
        if not os.path.isdir(self.tmpdir):
            raise Exception('invalid tmpdir: {}'.format(self.tmpdir))
        self.imgs = []
        self.conv_imgs = []
        self.makelist()
    def makelist(self):
        for file in os.scandir(self.folder):
            if not file.is_file():
                continue
            f = os.path.join(self.folder, file.name)
            try:
                img = Image.open(f)
            except:
                print('skip {} which is not available image'.format(f))
                continue
            print(f, img)
            if img.format != 'JPG':
                f = os.path.basename(f)
                f = os.path.splitext(f)[0] + '.jpg'
                f = os.path.join(self.tmpdir, f)
                oimg = img.convert('RGB')
                oimg.save(f, quality=95)
                self.conv_imgs.append(f)
            self.imgs.append(f)
        basename = lambda f: os.path.basename(f)
        if len(self.imgs) > 0:
            self.imgs.sort(key=basename)

class Parameters:
    def __init__(self, initargs=None):
        parser = argparse.ArgumentParser(description='convert Image files to single PDF')
        parser.add_argument('img_folder', help='folder of input images', nargs='?', default='.')
        parser.add_argument('-o', '--output_pdf', help='output file name', metavar='FILE', default='output')
        parser.add_argument('-d', '--output_dir', help='output directory', default=None, metavar='DIR')
        parser.add_argument('-g', '--gui', help='start with GUI', action='store_false')
        parser.add_argument('-r', '--recursive', help='recursive mode', action='store_true')
        parser.add_argument('-s', '--suffix', help='suffix of output file name with recursive mode', default=' 第{:02d}巻')
        parser.add_argument('-t', '--tmpdir', help='temporary directory', metavar='DIR', default=None)
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
        self.master.geometry('400x150')
        if params is None:
            self.p = Parameters()
        else:
            self.p = params
        self.create_widgets()
    def create_widgets(self):
        self.imgfolder_dirdiag = guiDirDiag(master=self, label=u'入力フォルダ', initdir=self.p.img_folder)
        self.imgfolder_dirdiag.grid(row=0, column=0, columnspan=2)
        self.outfolder_dirdiag = guiDirDiag(master=self, label=u'出力フォルダ', initdir=self.p.output_dir)
        self.outfolder_dirdiag.grid(row=1, column=0, columnspan=2)
        self.outputpdf_textbox = guiTextEntry(master=self, label=u'出力ファイル名', inittext=self.p.output_pdf)
        self.outputpdf_textbox.grid(row=2, column=0, columnspan=2)
        self.recursive_check = guiRadioButton(master=self, label=u'入力フォルダ以下の各フォルダで変換', initcond=self.p.recursive)
        self.recursive_check.grid(row=3, column=0)
        self.suffix_textbox = guiTextEntry(master=self, label=u'添字', width=10, inittext=self.p.suffix)
        self.suffix_textbox.grid(row=3, column=1)
        frame = tk.Frame(master=self.master)
        frame.grid(row=4, column=0, columnspan=2)
        button1 = tk.Button(frame, text="実行", command=self.convert)
        button1.grid(row=0,column=0)
        button2 = tk.Button(frame, text=("閉じる"), command=quit)
        button2.grid(row=0,column=1)
    def convert(self):
        convert(self.imgfolder_dirdiag.entry.get(),
                self.outfolder_dirdiag.entry.get(),
                self.outputpdf_textbox.entry.get(),
                self.recursive_check.entry.get(),
                self.suffix_textbox.entry.get(),
                self.p.tmpdir)

class guiDirDiag(tk.Frame):
    def __init__(self, master=None, label=None, initdir=None, width=30):
        super().__init__()
        self.label = label
        self.initdir = initdir
        self.width = width
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.StringVar()
        self.entry.set(self.initdir)
        box = tk.Entry(self, textvariable=self.entry, width=self.width)
        label = tk.Label(self, text=self.label)
        button = tk.Button(self, text=u'フォルダ選択', command=self.dirdialog_clicked)
        label.pack(side='left', anchor=tk.W)
        box.pack(side='left')
        button.pack(side='left')
    def dirdialog_clicked(self):
        initdir = os.path.abspath(os.path.dirname(self.initdir))
        dir = tkf.askdirectory(initialdir = initdir)
        self.entry.set(dir)

class guiTextEntry(tk.Frame):
    def __init__(self, master=None, label=None, inittext=None, width=30):
        super().__init__()
        self.label = label
        self.inittext = inittext
        self.width = width
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.StringVar()
        self.entry.set(self.inittext)
        box = tk.Entry(self, textvariable=self.entry, width=self.width)
        label = tk.Label(self, text=self.label)
        label.pack(side='left', anchor=tk.W)
        box.pack(side='left')

class guiRadioButton(tk.Frame):
    def __init__(self, master=None, label=None, initcond=False):
        super().__init__()
        self.label = label
        self.initcond = initcond
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.BooleanVar()
        self.entry.set(self.initcond)
        checkbox = tk.Checkbutton(self, text=self.label, variable=self.entry)
        checkbox.pack(side='left', anchor=tk.W)

if __name__ == '__main__':
    params = Parameters()
    if params.gui:
        import tkinter as tk
        import tkinter.filedialog as tkf
        root = tk.Tk()
        gui = guiMain(master=root, params=params)
        gui.mainloop()
    else:
        convert(params.img_folder,
                params.output_dir,
                params.output_pdf,
                params.recursive,
                params.suffix,
                params.tmpdir)