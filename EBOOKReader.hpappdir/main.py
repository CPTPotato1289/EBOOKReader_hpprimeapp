py_eval = eval
from hpprime import *
import math

version="EBOOKReader v0.7.0alpha"

#设置数据读取和初始化
COLOR_LIST = ["#FFFFFFh","#FF0000h","#FFh","#FF00h","#0h"]
SIZE_LIST = [4,5,6]
BG_COLOR = "#FFFFFFh"
TEXT_COLOR = "#0h"
TEXT_SIZE = 4
temps = eval("AFiles(\"BG_COLOR\")")
if temps != "错误:输入无效":
    BG_COLOR = temps
temps = eval("AFiles(\"TEXT_COLOR\")")
if temps != "错误:输入无效":
    TEXT_COLOR = temps
#print ("debug:setting-",BG_COLOR,TEXT_COLOR,TEXT_SIZE)

#主菜单显示
def show_menu():
    eval("CHOOSE(N,\"菜单\",\"选择书本\",\"设置\",\"关于\",\"退出\")")
    choice = eval("N")     
    return choice 

#获取书本列表
def show_book_list():
    files = eval('AFiles()')
    txt_files = ""
    for i in files:
        if i.lower().endswith('_book.txt'):
            prefix = i.split("_")[0]
            if not txt_files:
                txt_files = "\""+prefix+"\""
            else:
                txt_files = txt_files+","+"\""+prefix+"\""
    return txt_files

def check_file(file_name):
    files = eval('AFiles()')
    return file_name in files

#书本选择菜单
def choose_book():
    book_list = show_book_list()
    eval("CHOOSE(N,\"选择书本\","+book_list+")")
    book_number = int(eval("N"))
    lst = [item.strip('"') for item in book_list.split(',')]
    return lst[book_number-1]

def parse_ch_structure(paragraph):
    if not paragraph.startswith('[ch'):
        return None, None
    end = paragraph.find(']')
    if end == -1:
        return None, None  # 没有闭合括号
    inner = paragraph[3:end]  # 从索引3开始，到 ']' 前
    pos = inner.find('()')
    if pos == -1:
        return None, None  # 没有 '()' 分隔符
    num_str = inner[:pos]
    if not num_str.isdigit():
        return None, None
    text = inner[pos+2:]  # 跳过 '()'
    return num_str, text

def max_chars():
    y = 225 / (4 * TEXT_SIZE)
    x = 320 / (4 * TEXT_SIZE)
    return math.floor(x),math.floor(y)-1

def build_list(book_name):
    with open(book_name + "_book.txt", 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
        f.close
    maxx, maxy = max_chars()

    contents = []          # 章节索引 [标题, 页码]
    pages = []             # 页面索引 [[行, 列], [行, 列]]

    # 当前页状态
    page_start = None      # [行, 列]
    page_end = None        # [行, 列]
    line_count = 0         # 当前页已占行数

    def close_current_page():
        """结束当前页，若存在则存入 pages"""
        nonlocal page_start, page_end, line_count
        if page_start is not None:
            pages.append([page_start, page_end])
            page_start = None
            page_end = None
            line_count = 0

    def add_display_line(line_idx, col_start, col_end):
        nonlocal page_start, page_end, line_count
        start_pos = [line_idx, col_start]
        end_pos = [line_idx, col_end]

        if page_start is None:
            page_start = start_pos
            page_end = end_pos
            line_count = 1
        else:
            if line_count + 1 > maxy:
                pages.append([page_start, page_end])
                page_start = start_pos
                page_end = end_pos
                line_count = 1
            else:
                page_end = end_pos
                line_count += 1

    def split_paragraph_by_chars(text):
        if not text:
            return []
        segments = []
        start = 0
        while start < len(text):
            end = min(start + maxx, len(text))
            segments.append((start, end - 1))
            start = end
        return segments

    for line_idx, paragraph in enumerate(lines):
        ch, title = parse_ch_structure(paragraph)
        if ch is not None:
            close_current_page()
            page_number = len(pages) + 1
            contents.append([title, page_number])
            if paragraph == "":
                add_display_line(line_idx, 0, 0)
            else:
                for col_start, col_end in split_paragraph_by_chars(paragraph):
                    add_display_line(line_idx, col_start, col_end)
            continue

        if paragraph.startswith("[pic:"):
            close_current_page()
            for col_start, col_end in split_paragraph_by_chars(paragraph):
                add_display_line(line_idx, col_start, col_end)
            close_current_page()
            continue

        if paragraph == "":
            if page_start is None:
                continue
            if line_count < maxy:
                add_display_line(line_idx, 0, 0)
            continue

        for col_start, col_end in split_paragraph_by_chars(paragraph):
            add_display_line(line_idx, col_start, col_end)
    close_current_page()
    if not pages:
        pages.append([[0, 0], [0, 0]])
    for page in pages:
        end_line, end_col = page[1]
        if end_line >= len(lines):
            end_line = len(lines) - 1
        max_col = max(len(lines[end_line]) - 1, 0)
        page[1][1] = min(end_col, max_col)
    result = {"Contents": contents, "Pages": pages}
    #print (result['Contents'])
    with open(book_name + "_list.txt", "w", encoding="utf-8") as f:
        f.write(repr(result))
        f.close
    #print(result)   # 可保留调试
    return result

#文本渲染器
def show_text(main_text,floor_text):
    eval("RECT_P(G0,0,0,320,240," + BG_COLOR + ")")
    eval('TEXTOUT_P("' + floor_text + '",0,225,3,' + TEXT_COLOR + ',240,'+BG_COLOR+')')
    maxx,___ = max_chars()
    lines = main_text.split('\n')
    y = 0;line_height = int(4 * TEXT_SIZE)
    for para in lines:
        if para == "":
            y += line_height
            continue
        while len(para) > 0:
            line = para[:maxx]
            if line:
                eval(('TEXTOUT_P("'+line+'",0,'+str(y)+','+str(TEXT_SIZE)+','+TEXT_COLOR+')'))
            y += line_height
            para = para[maxx:]
    return
#图片渲染器
def draw_imagine(pic_name,size,position):
    
    weight = int(eval("GROBW_P(G1)"))
    height = int(eval("GROBH_P(G1)"))
    xl=position[0];yt=position[1]
    xr=xl+int(weight * size);yb=yt+int(height*size)
    eval('BLIT_P(G0,'+str(xl)+','+str(yt)+','+str(xr)+','+str(yb)+','+'G1)')
    if xl > 0:
        eval('RECT_P(G0,0,0,'+str(xl)+',240,'+BG_COLOR+')')
    if yt > 0:
        eval('RECT_P(G0,0,0,320,'+str(yt)+','+BG_COLOR+')')
    if xr < 320:
        eval('RECT_P(G0,'+str(xr)+',0,320,240,'+BG_COLOR+')')
    if yb < 240:
        eval('RECT_P(G0,0,'+str(yb)+',320,240,'+BG_COLOR+')')

def show_pic(floortext,pic_name):
    eval('G1:= AFiles("' +pic_name+'")')
    x = 0;y = 0;size=1
    while True:
        draw_imagine(pic_name,size,[x,y])
        eval('TEXTOUT_P("' + floortext + '",0,225,3,' + TEXT_COLOR + ',240,'+BG_COLOR+')')
        event = eval("WAIT(-1)")
        if isinstance(event, int) or isinstance(event, float):
            if event == -1:
                continue
            elif event == 4:
                return 0
            elif event == 2 or event == 7:
                return -1
            elif event == 8 or event == 12 or event == 30:
                return 1
            elif event == 33:
                y -= 10
            elif event == 43:
                y += 10
            elif event == 37:
                x -= 10
            elif event == 39:
                x += 10
            elif event == 50:
                size += 0.1
            elif event == 45 and size > 0.12:
                size -= 0.1
            else:
                continue
        else:
            x_start = x
            y_start = y
            x_ts = int(eval("MOUSE(2)"))
            y_ts = int(eval("MOUSE(3)"))
            while True:
                if int(eval("MOUSE(2)")) == -1:
                    break 
                nx = int(eval("MOUSE(0)"))
                ny = int(eval("MOUSE(1)"))
                x = x_start + nx - x_ts
                y = y_start + ny - y_ts
                draw_imagine(pic_name,size,[x,y])

def load_list(book_name):
    try:
        with open(book_name + "_list.txt", "r", encoding="utf-8") as f:
            content = f.read()
            return py_eval(content)
    except:
        return None
#阅读器主函数
def start_read(book_name,page):
    with open(book_name+"_book.txt", 'r', encoding='utf-8') as f:
        lines = f.readlines()
        f.close
    lines = [line.strip("\n") for line in lines]
    list = load_list(book_name)
    max_page = len(list["Pages"])
    while True:
        eval('"'+str(page)+'"'+'▶AFiles("'+book_name+'_Post")')
        page_info = list["Pages"][page]
        show_str = ""
        if page_info[0][0] == page_info[1][0]:
            show_str = lines[page_info[0][0]][page_info[0][1]:(page_info[1][1]+1)]
            a,b = parse_ch_structure(show_str)
            if not a == None:
                show_str = 'ch'+a+' '+b
            elif show_str.startswith("[pic:"):
                try:
                    #print(show_str)
                    #print("长度:", len(show_str))
                    pic_name = show_str[5:show_str.find(']')]
                    #print(pic_name)
                    picevent = show_pic(book_name+'  '+str(page+1)+'/'+str(max_page),pic_name)
                    if picevent == 0:
                        return
                    elif picevent == -1:
                        if not page == 0:
                            page -= 1
                        continue
                    elif picevent == 1:
                        if not page == max_page -1:
                            page += 1
                        continue
                except:
                    pass                    
        else:
            show_str = lines[page_info[0][0]][page_info[0][1]:] + '\n'
            a,b = parse_ch_structure(show_str)
            if not a == None:
                show_str = 'ch'+a+' '+b+'\n'
            for i in range(page_info[0][0]+1,page_info[1][0]):
                show_str = show_str + lines[i] + '\n'
            show_str = show_str + '\n' + lines[page_info[1][0]][:(page_info[1][1]+1)]
        show_text(show_str,book_name+'  '+str(page+1)+'/'+str(max_page))
        while True:
            key_code = eval("WAIT(0)")
            if key_code == 30 or key_code == 12 or key_code == 8:
                if not page == max_page - 1:
                    page += 1
                    break
            if key_code == 2 or key_code ==  7:
                if not page == 0:
                    page -= 1 
                    break
            if key_code == 4:
                return

def show_contents(book_name):
    list = load_list(book_name)
    contents = list["Contents"]
    page = 0;per_page = 8
    total_pages = (len(contents) + per_page - 1) // per_page
    while True:
        show_str = 'CHOOSE(N,"' + book_name + ' 目录","上一页","下一页","跳转"'
        for i in range(page * per_page,min((page+1)* per_page,len(contents))):
            #print(show_str)
            show_str = show_str + ',"' + 'ch' + str(i) + ' ' + contents[i][0] + '"'
        eval(show_str+',"返回")')
        #print(show_str+',"返回")')
        get_choose = int(eval("N"))
        if get_choose == 1:
            if (not page == 0):
                page -= 1
            continue
        elif get_choose == 2:
            if (not page == total_pages - 1):
                page += 1
            continue
        elif get_choose == 3:
            eval('INPUT(N,"跳转目录页码","跳转到","输入范围：1-'+str(total_pages)+'")')
            inpage = eval("N")
            try:
                inpage = int(inpage)
            except:
                eval('MSGBOX("错误的输入！")')
                continue
            if inpage > total_pages or inpage <= 0:
                eval('MSGBOX("错误的输入！")')
                continue
            page = inpage - 1
        elif get_choose == 4 + min(per_page,len(contents) - page * per_page):
            return
        else:
            star_ch = page * per_page + get_choose - 4
            start_read(book_name,contents[star_ch][1]-1)
            return

while True:
        get_menu = int(show_menu())
        if get_menu == 4:
            break
        elif get_menu == 3:
            eval("MSGBOX(\"EBOOKREADER 一款强大的阅读器 made by CPTPotato 版本："+version+"\")")
        elif get_menu == 2:
            eval("INPUT({{C,{\"白\",\"红\",\"蓝\",\"绿\",\"黑\"}},{B,{\"白\",\"红\",\"蓝\",\"绿\",\"黑\"}}},\"设置\",{\"字体颜色\",\"背景颜色\"},{\"选择\",\"选择\"});")
            TEXT_COLOR = COLOR_LIST[int(eval("C"))-1]
            BG_COLOR = COLOR_LIST[int(eval("B"))-1]
            eval("\""+TEXT_COLOR+"\""+"▶AFiles(\"TEXT_COLOR\")")  
            eval("\""+BG_COLOR+"\""+"▶AFiles(\"BG_COLOR\")")  
        elif get_menu == 1:
            book_name = choose_book()
            while True:
                eval("CHOOSE(N,"+"\""+book_name+"\",\"继续阅读\",\"查看目录\",\"跳转页码\",\"构建索引\",\"返回\")")
                action = int(eval("N"))
                if action == 5:
                    break
                elif action == 4:
                    eval("MSGBOX(\"本操作可能耗时较久！\")")
                    build_list(book_name)
                    eval('MSGBOX("已构建索引！")')
                elif action == 3:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    list = load_list(book_name)
                    maxpage = len(list["Pages"])
                    eval('INPUT(N,"跳转页码","跳转到","输入范围：1-'+str(maxpage)+'")')
                    page = eval("N")
                    try:
                        page = int(page)
                    except:
                        eval('MSGBOX("错误的输入！")')
                        continue
                    if page > maxpage or page <= 0:
                        eval('MSGBOX("错误的输入！")')
                        continue
                    start_read(book_name,page-1)
                elif action == 1:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    position = 0
                    temps = eval('AFiles("'+book_name+'_Post")')
                    try:
                        position = int(temps)
                    except:
                        position = 0
                    start_read(book_name,position)
                elif action == 2:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    show_contents(book_name)