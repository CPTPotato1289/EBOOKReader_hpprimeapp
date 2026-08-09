py_eval = eval
from hpprime import *
import math

version="EBOOKReader v0.9.0alpha"

#字体大小设置区域如下，按照注释修改
TEXT_SIZE = 4 #显示的字体大小
MAX_X = 20 #每行显示的字个数
MAX_Y = 14 #每一页显示的行数
#注意修改完后请重建所有书本索引
#请注意：修改字体大小会导致原有阅读位置和书签等不可用

#配色数据读取和初始化
COLOR_LIST = [
    ['#3C3C3Ch', '#E6E6E6h', '#2C3E3Eh', '#333333h', '#5D4037h'],
    ['#FBF7F0h', '#1A1A1Ah', '#C7EDCCh', '#F4F6F8h', '#F5E6C8h'],
    ['#D49A6Ah', '#6A9FB5h', '#E8A87Ch', '#C0392Bh', '#B76E79h']
]
BG_COLOR = "#FBF7F0h"
TEXT_COLOR = "#3C3C3Ch"
LB_COLOR = "#D49A6Ah"
temps = eval("AFiles(\"BG_COLOR\")")
if temps != "错误:输入无效":
    BG_COLOR = temps
temps = eval("AFiles(\"TEXT_COLOR\")")
if temps != "错误:输入无效":
    TEXT_COLOR = temps
temps = eval("AFiles(\"LB_COLOR\")")
if temps != "错误:输入无效":
    LB_COLOR = temps
#print ("debug:setting-",BG_COLOR,TEXT_COLOR,LB_COLOR)
def max_chars():
    return MAX_X,MAX_Y-1

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

def get_position(book_name):
    position = 0
    temps = eval('AFiles("'+book_name+'_Post")')
    try:
        position = int(temps)
    except:
        position = 0
    return position
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
        return None, None  
    inner = paragraph[3:end] 
    pos = inner.find('()')
    if pos == -1:
        return None, None 
    num_str = inner[:pos]
    if not num_str.isdigit():
        return None, None
    text = inner[pos+2:] 
    return num_str, text

def build_list(book_name):
    with open(book_name + "_book.txt", 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
        f.close
    maxx, maxy = max_chars()
    contents = []          
    pages = []             
    page_start = None   
    page_end = None      
    line_count = 0   

    def close_current_page():
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
    #print(result)  
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
                show_str = a+' '+b
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
                show_str = a+' '+b+'\n'
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
def jump_page(book_name,page):
    eval('"'+str(get_position(book_name))+'"▶AFiles("'+book_name+'_Return")')
    start_read(book_name,page)
    return
#显示目录
def show_contents(book_name):
    list = load_list(book_name)
    contents = list["Contents"]
    position = get_position(book_name)
    contents_position = 0
    for i in range(len(contents)):
        if contents[i][1] > position+1:
            break
        contents_position = i
    per_page = 10
    page = contents_position//per_page
    total_pages = (len(contents) + per_page - 1) // per_page
    while True:
        show_str = 'CHOOSE(N,"' + book_name + ' 目录","上一页","下一页","跳转"'
        for i in range(page * per_page,min((page+1)* per_page,len(contents))):
            #print(show_str)
            if not(i == contents_position):
                show_str = show_str + ',"' + str(i) + ' ' + contents[i][0] + '"'
            else:
                show_str = show_str + ',"' + str(i) + '▶' + contents[i][0] + '"'
        if eval(show_str+',"返回")') == 0:
            continue
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
            if eval('INPUT(N,"跳转目录页码","跳转到","输入范围：1-'+str(total_pages)+'",'+str(page+1)+','+str(page+1)+')') == 0:
                continue
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
            jump_page(book_name,contents[star_ch][1]-1)
            return

while True:
        if eval("CHOOSE(N,\"菜单\",\"选择书本\",\"设置\",\"关于\",\"退出\")") == 0:
            continue
        get_menu = int(eval("N"))
        if get_menu == 4:
            break
        elif get_menu == 3:
            eval("MSGBOX(\"EBOOKREADER 一款强大的阅读器 made by CPTPotato 版本："+version+"\")")
        elif get_menu == 2:
            if eval('INPUT({{C,{"暖阳","暗夜","清绿","素白","羊皮","自定义"}}},"设置",{"配色方案"},{"修改字体：退出，按Symb，修改7-12行内容"});') == 0:
                continue
            if int(eval("C")) == 6:
                eval('MSGBOX("若出现弹窗请均点击“是”")')
                eval('BGC:="#0h"')
                eval('TXC:="#FFFFFFh"')
                eval('LBC:="#FF0000h"')
                eval('MSGBOX("请保证输入颜色格式正确！")')
                if eval('INPUT({{BGC,[2]},{TXC,[2]},{LBC,[2]}},"自定义颜色",{"背景颜色","文本颜色","标记颜色"},{"输入颜色，形式如#FFFFFFh","输入颜色，形式如#FFFFFFh","输入颜色，形式如#FFFFFFh"})') == 0:
                    eval('MSGBOX("已取消自定义！")')
                TEXT_COLOR = eval('TXC')
                BG_COLOR = eval('BGC')
                LB_COLOR = eval('LBC')
            else:
                TEXT_COLOR = COLOR_LIST[0][int(eval("C"))-1]
                BG_COLOR = COLOR_LIST[1][int(eval("C"))-1]
                LB_COLOR = COLOR_LIST[2][int(eval("C"))-1]
            eval("\""+TEXT_COLOR+"\""+"▶AFiles(\"TEXT_COLOR\")")  
            eval("\""+BG_COLOR+"\""+"▶AFiles(\"BG_COLOR\")")  
            eval("\""+LB_COLOR+"\""+"▶AFiles(\"LB_COLOR\")")  
        elif get_menu == 1:
            book_name = choose_book()
            while True:
                if eval("CHOOSE(N,"+"\""+book_name+"\",\"继续阅读\",\"查看目录\",\"跳转页码\",\"构建索引\",\"返回\")") == 0:
                    continue
                action = int(eval("N"))
                if action == 5:
                    break
                elif action == 4:
                    if eval("MSGBOX(\"确定构建索引？本操作可能耗时较久！\",1)") == 0:
                        continue
                    build_list(book_name)
                    eval('MSGBOX("已构建索引！")')
                elif action == 3:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    list = load_list(book_name)
                    maxpage = len(list["Pages"])
                    position = 0
                    try:
                        position = int(eval('AFiles("'+book_name+'_Return")'))
                    except:
                        position = 0
                    if eval('INPUT(N,"跳转页码","跳转到","范围：1-'+str(maxpage)+' (默认值：上次跳转前位置)",'+str(position+1)+','+str(position+1)+')') == 0:
                        continue
                    page = eval("N")
                    try:
                        page = int(page)
                    except:
                        eval('MSGBOX("错误的输入！")')
                        continue
                    if page > maxpage or page <= 0:
                        eval('MSGBOX("错误的输入！")')
                        continue
                    jump_page(book_name,page-1)
                elif action == 1:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    position =get_position(book_name)
                    start_read(book_name,position)
                elif action == 2:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    show_contents(book_name)
