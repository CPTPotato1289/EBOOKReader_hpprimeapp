from hpprime import *
import gc
import math

version="EBOOKReader v0.11.0alpha"

#字体大小设置区域如下，按照注释修改
TEXT_SIZE = 4 #显示的字体大小
MAX_X = 20 #每行显示的字个数
MAX_Y = 14 #每一页显示的行数
#注意修改完后请重建所有书本索引
#请注意：修改字体大小会导致原有阅读位置和书签等不可用
#配色数据读取和初始化
COLOR_LIST = [
    ['#3C3C3Ch', '#E6E6E6h', '#2C3E3Eh', '#333333h', '#5D4037h'],
    ['#FBF7F0h', '#1A1A1Ah', '#C7EDCCh', '#F4F6F8h', '#F5E6C8h']
]
BG_COLOR = "#FBF7F0h"
TEXT_COLOR = "#3C3C3Ch"
temps = eval("AFiles(\"BG_COLOR\")")
if temps != "错误:输入无效":
    BG_COLOR = temps
temps = eval("AFiles(\"TEXT_COLOR\")")
if temps != "错误:输入无效":
    TEXT_COLOR = temps
#print ("debug:setting-",BG_COLOR,TEXT_COLOR)
def max_chars():
    return MAX_X,MAX_Y

_index_cache = None
_cache_book_name = ""
_text_cache = None
_text_cache_book = ""
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
#构建索引
def build_list(book_name):
    global _index_cache, _cache_book_name, _text_cache, _text_cache_book
    _index_cache = None
    _cache_book_name = ""
    _text_cache = None
    _text_cache_book = ""

    with open(book_name + "_book.txt", 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
        f.close
    maxx, maxy = max_chars()
    contents = []    
    pictures = []      
    pages = []             
    page_start = None   
    page_end = None      
    line_count = 0   

    def close_current_page():
        nonlocal page_start, page_end, line_count
        if page_start is not None:
            pages.append((page_start[0], page_start[1], page_end[0], page_end[1]))
            page_start = None
            page_end = None
            line_count = 0

    def add_display_line(line_idx, col_start, col_end):
        nonlocal page_start, page_end, line_count
        start_pos = (line_idx, col_start)
        end_pos = (line_idx, col_end)

        if page_start is None:
            page_start = start_pos
            page_end = end_pos
            line_count = 1
        else:
            if line_count + 1 > maxy:
                pages.append((page_start[0], page_start[1], page_end[0], page_end[1]))
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
            contents.append((title, page_number))
            if paragraph == "":
                add_display_line(line_idx, 0, 0)
            else:
                for col_start, col_end in split_paragraph_by_chars(paragraph):
                    add_display_line(line_idx, col_start, col_end)
            continue

        if paragraph.startswith("[pic:"):
            close_current_page()
            pic_name = paragraph[5:paragraph.find(']')]
            start_page_before = len(pages)
            for col_start, col_end in split_paragraph_by_chars(paragraph):
                add_display_line(line_idx, col_start, col_end)
            close_current_page()
            if len(pages) > start_page_before:
                page_num = start_page_before + 1
                pictures.append((pic_name,page_num))
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
        pages.append((0, 0, 0, 0))
    for idx, page in enumerate(pages):
        s_l, s_c, e_l, e_c = page
        if e_l >= len(lines):
            e_l = len(lines) - 1
        max_col = max(len(lines[e_l]) - 1, 0)
        if e_c > max_col:
            e_c = max_col
        pages[idx] = (s_l, s_c, e_l, e_c)
    result = {"Contents": contents, "Pages": pages,"Pictures": pictures}
    eval('"'+str(len(pages))+'"'+'▶AFiles("'+book_name+'_TPage")')
    #print (result['Pictures'])
    # 删除原来的 with open 写入 repr 的代码，替换为：
    with open(book_name + "_list.txt", "w", encoding="utf-8") as f:
        f.write("PAGES\n")
        for s_l, s_c, e_l, e_c in pages:
            f.write(str(s_l) + " " + str(s_c) + " " + str(e_l) + " " + str(e_c) + "\n")
        f.write("CONTENTS\n")
        for title, pnum in contents:
            f.write(str(pnum) + "\t" + title + "\n")
        f.write("PICTURES\n")
        for pic_name, pnum in pictures:
            f.write(str(pnum) + "\t" + pic_name + "\n")
    del lines, contents, pages, pictures
    gc.collect()
    #print(result)  
    return
def max_page(book_name):
    return int(eval('AFiles("'+book_name+'_TPage")'))
#行号映射页码
def find_page_by_coord(pages, line_idx, col_idx):
    lo, hi = 0, len(pages) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if pages[mid][0] <= line_idx:
            lo = mid + 1
        else:
            hi = mid - 1
    if hi < 0:
        return None
    start_line = pages[hi][0]
    end_line = pages[hi][2]
    end_col = pages[hi][3]
    if line_idx < end_line or (line_idx == end_line and col_idx <= end_col):
        return hi
    else:
        if hi + 1 < len(pages) and pages[hi+1][0] == line_idx:
            return hi + 1
        return None
#时间渲染器
def draw_time():
    timen = eval("Time")
    h = int(timen)
    m = int((timen - h)*60)
    tstr = "%02d:%02d" % (h, m)
    eval('RECT_P(G0,278,226,320,240,'+BG_COLOR+')')
    eval('TEXTOUT_P("' + tstr + '",280,225,3,' + TEXT_COLOR + ',240)')
    return
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
        draw_time()
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
                y += 10
            elif event == 43:
                y -= 10
            elif event == 37:
                x += 10
            elif event == 39:
                x -= 10
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
    global _index_cache, _cache_book_name
    if _cache_book_name == book_name and _index_cache is not None:
        return _index_cache
    data = {"Contents": [], "Pages": [], "Pictures": []}
    with open(book_name + "_list.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    mode = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == "PAGES":
            mode = "pages"
            continue
        elif line == "CONTENTS":
            mode = "contents"
            continue
        elif line == "PICTURES":
            mode = "pictures"
            continue
        if mode == "pages":
            parts = line.split()
            if len(parts) == 4:
                s_l, s_c, e_l, e_c = map(int, parts)
                data["Pages"].append((s_l, s_c, e_l, e_c))
        elif mode == "contents":
            parts = line.split('\t')
            if len(parts) == 2:
                pnum, title = parts
                data["Contents"].append((title, int(pnum)))
        elif mode == "pictures":
            parts = line.split('\t')
            if len(parts) == 2:
                pnum, pic_name = parts
                data["Pictures"].append((pic_name, int(pnum)))
    _cache_book_name = book_name
    _index_cache = data
    return data
    
def load_book_text(book_name):
    global _text_cache, _text_cache_book
    if _text_cache_book == book_name and _text_cache is not None:
        return _text_cache
    with open(book_name + "_book.txt", 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
    _text_cache_book = book_name
    _text_cache = lines
    return lines

#阅读器主函数
def start_read(book_name,page):
    lines = load_book_text(book_name)
    list = load_list(book_name)
    max_page = len(list["Pages"])
    while True:
        eval('"'+str(page)+'"'+'▶AFiles("'+book_name+'_Post")')
        page_info = list["Pages"][page]
        show_str = ""
        if page_info[0] == page_info[2]:
            show_str = lines[page_info[0]][page_info[1]:(page_info[3]+1)]
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
            parts = []
            parts.append(lines[page_info[0]][page_info[1]:])
            a, b = parse_ch_structure(parts[0])
            if a is not None:
                parts[0] = a + ' ' + b
            for i in range(page_info[0]+1, page_info[2]):
                parts.append(lines[i])
            parts.append(lines[page_info[2]][:(page_info[3]+1)])
            show_str = '\n'.join(parts)
        show_text(show_str,book_name+'  '+str(page+1)+'/'+str(max_page))
        while True:
            draw_time()
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
            if gc.mem_free() < 500:
                gc.collect()
def jump_page(book_name,page):
    eval('"'+str(get_position(book_name))+'"▶AFiles("'+book_name+'_Return")')
    start_read(book_name,page)
    return

def show_list(title,list,position):
    per_page = 10
    page = position // per_page
    total_pages = (len(list)+per_page-1) // per_page
    while True:
        items = ['"上一页"','"下一页"','"跳转"']
        for i in range(page * per_page,min((page+1)* per_page,len(list))):
            items.append('"' + list[i] + '"')
        items.append('"返回"')
        options_str = ','.join(items)
        if eval('CHOOSE(N,"' + title + '(' + str(page+1) + '/' + str(total_pages) + ')",' + options_str + ')') == 0:
            continue
        get_choose = int(eval("N"))
        if get_choose == 1:
            if(not page == 0):
                page -= 1
            continue
        elif get_choose == 2:
            if (not page == total_pages - 1):
                page += 1
            continue
        elif get_choose == 3:
            if eval('INPUT(N,"跳转页码","跳转到","输入范围：1-'+str(total_pages)+'",'+str(page+1)+','+str(page+1)+')') == 0:
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
        elif get_choose == 4 + min(per_page,len(list) - page * per_page):
            return -1
        else:
            ret = page * per_page + get_choose - 4
            return ret
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
    title = book_name + ' 目录'
    content_show = []
    for i in range(len(contents)):
        if not(i == contents_position):
            content_show.append(str(i) + '  ' + contents[i][0])
        else : 
            content_show.append(str(i) + '▶' + contents[i][0])
    action = show_list(title,content_show,contents_position)
    if action == -1:
        return
    jump_page(book_name,contents[action][1]-1)
    return
#显示图片列表
def show_piclist(book_name):
    list = load_list(book_name)
    pictures = list["Pictures"]
    if len(pictures) == 0:
        eval('MSGBOX("本书无图片！")')
        return
    title = book_name + ' 图片'
    picls = []
    for i in range(len(pictures)):
        picls.append('P' + str(pictures[i][1]) + ' ' + pictures[i][0])
    action = 0
    while True:
        action = show_list(title,picls,action)
        if action == -1:
            return
        jump_page(book_name,pictures[action][1] - 1)
#检索文本主函数，返回1based页码列表
def search_book(book_name, keyword, start_page=0, end_page=None):
    data = load_list(book_name)
    pages = data["Pages"]
    lines = load_book_text(book_name)
    kw = keyword.strip()
    if not kw:
        return []
    kw_lower = kw.lower()
    kw_len = len(kw)
    total_pages = len(pages)
    if end_page is None or end_page >= total_pages:
        end_page = total_pages - 1
    start_page = max(0, start_page)
    end_page = min(total_pages - 1, end_page)
    if start_page > end_page:
        return []
    start_line = pages[start_page][0] 
    end_line = pages[end_page][2]
    results = []
    MAX_RESULTS = 200
    for line_idx in range(start_line, end_line + 1):
        line = lines[line_idx]
        line_lower = line.lower()
        search_start = 0
        while True:
            col_idx = line_lower.find(kw_lower, search_start)
            if col_idx == -1:
                break
            page_idx = find_page_by_coord(pages, line_idx, col_idx)
            if page_idx is not None and start_page <= page_idx <= end_page:
                ctx_start = max(0, col_idx - 5)
                ctx_end = min(len(line), col_idx + kw_len + 5)
                raw_context = line[ctx_start:ctx_end]
                kw_start_in_ctx = col_idx - ctx_start
                kw_end_in_ctx = kw_start_in_ctx + kw_len
                context = (raw_context[:kw_start_in_ctx] + '~' + raw_context[kw_end_in_ctx:])
                results.append([page_idx + 1,[line_idx, col_idx, col_idx + kw_len],context])
                if len(results) >= MAX_RESULTS:
                    eval('MSGBOX("结果超过200条，仅显示前200条")')
                    del lines, pages, data
                    return results
            search_start = col_idx + 1
    del lines, pages, data
    return results
#展示检索结果
def show_search(book_name, result):
    if not result:
        eval('MSGBOX("无结果！")')
        return
    title = book_name + ' 检索结果'
    resultl = []
    for i in range(len(result)):
        resultl.append('P' + str(result[i][0]) + ' ' + result[i][2])
    action = 0
    while True:
        action = show_list(title,resultl,action)
        if action == -1:
            return   
        jump_page(book_name, result[action][0] - 1)

while True:
        if eval("CHOOSE(N,\"菜单\",\"书架\",\"设置\",\"关于\",\"退出\")") == 0:
            continue
        get_menu = int(eval("N"))
        if get_menu == 4:
            break
        elif get_menu == 3:
            eval("MSGBOX(\"EBOOKREADER 一款强大的阅读器 运行过程中出现创建变量提示请点击是 made by CPTPotato 版本："+version+"\")")
        elif get_menu == 2:
            if eval('INPUT({{C,{"暖阳","暗夜","清绿","素白","羊皮","自定义"}}},"设置",{"配色方案"},{"修改字体：退出，按Symb，修改7-12行内容"});') == 0:
                continue
            if int(eval("C")) == 6:
                eval('BGC:="#0h"')
                eval('TXC:="#FFFFFFh"')
                eval('MSGBOX("请保证输入颜色格式正确！")')
                if eval('INPUT({{BGC,[2]},{TXC,[2]}},"自定义颜色",{"背景颜色","文本颜色"},{"输入颜色，形式如#FFFFFFh","输入颜色，形式如#FFFFFFh"})') == 0:
                    eval('MSGBOX("已取消自定义！")')
                    continue
                TEXT_COLOR = eval('TXC')
                BG_COLOR = eval('BGC')
            else:
                TEXT_COLOR = COLOR_LIST[0][int(eval("C"))-1]
                BG_COLOR = COLOR_LIST[1][int(eval("C"))-1]
            eval("\""+TEXT_COLOR+"\""+"▶AFiles(\"TEXT_COLOR\")")  
            eval("\""+BG_COLOR+"\""+"▶AFiles(\"BG_COLOR\")")  
        elif get_menu == 1:
            _text_cache = None
            _index_cache = None
            _cache_book_name = ""
            _text_cache_book = ""
            gc.collect()
            book_name = choose_book()
            while True:
                if eval("CHOOSE(N,"+"\""+book_name+"\",\"继续阅读\",\"查看目录\",\"跳转页码\",\"查看图片\",\"检索内容\",\"构建索引\",\"返回\")") == 0:
                    continue
                action = int(eval("N"))
                if action == 7:
                    break
                elif action == 5:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    eval('TXS:="文本"')
                    maxpage = max_page(book_name)
                    if eval('INPUT({A,B,{TXS,[2]}},"检索内容",{"起始页","结束页","关键词"},{"检索起始页码","检索结束页码","检索的关键词"},{1,'+str(maxpage)+'},{1,'+str(maxpage)+'})') == 0:
                        continue
                    result = search_book(book_name,eval('TXS'),int(eval('A'))-1,int(eval('B'))-1)
                    show_search(book_name,result)
                elif action == 6:
                    if eval("MSGBOX(\"确定构建索引？本操作可能耗时较久！\",1)") == 0:
                        continue
                    build_list(book_name)
                    eval('MSGBOX("已构建索引！")')
                elif action == 3:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    maxpage = max_page(book_name)
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
                elif action == 4:
                    if not check_file(book_name+"_list.txt"):
                        eval('MSGBOX("请先构建索引！")')
                        continue
                    show_piclist(book_name)
