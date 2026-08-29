from hpprime import *
import gc
import math
import sys

def max_chars():
    return MAX_X,MAX_Y
def safe_int(inp):
        return int(float(inp) + 0.3)

version="EBOOKReader v1.0.0"
font_table = ((4,20,14),(5,17,11),(6,16,9))
TEXT_SIZE = 4 
MAX_X = 20 
MAX_Y = 14
COLOR_LIST = [
    ['#3C3C3Ch', '#E6E6E6h', '#2C3E3Eh', '#333333h', '#5D4037h'],
    ['#FBF7F0h', '#1A1A1Ah', '#C7EDCCh', '#F4F6F8h', '#F5E6C8h']
]
BG_COLOR = "#FBF7F0h"
TEXT_COLOR = "#3C3C3Ch"
def load_set():
    global BG_COLOR,TEXT_COLOR,TEXT_SIZE,MAX_X,MAX_Y
    temps = eval("AFiles(\"BG_COLOR\")")
    if temps != "错误:输入无效":
        BG_COLOR = temps
    temps = eval("AFiles(\"TEXT_COLOR\")")
    if temps != "错误:输入无效":
        TEXT_COLOR = temps
    temps = eval("AFiles(\"FONT_SIZE\")")
    if temps != "错误:输入无效":
        temps = safe_int(temps)
        TEXT_SIZE = font_table[temps][0]
        MAX_X = font_table[temps][1]
        MAX_Y = font_table[temps][2]
load_set()

_index_cache = None
_cache_book_name = ""
_text_cache = None
_text_cache_book = ""
_text_cache_vol = -1

def check_file(file_name):
    files = eval('AFiles()')
    return file_name in files

def unpack_pos(pos_str):
    try:
        parts = pos_str.split(',')
        return int(parts[0]), int(parts[1]), int(parts[2])
    except:
        pass
    return None, None,None

def get_position(book_name):
    pos_str = eval('AFiles("'+book_name+'_Post")')
    parts = pos_str.split(',')
    if len(parts) == 3:
        vol, line, col = parts
        data = load_list(book_name)
        page_idx = find_page_by_coord(data["Pages"], int(vol), int(line), int(col))
        if page_idx is not None:
            return page_idx
    try:
        return int(pos_str) 
    except:
        return 0

def max_line(book_name, vol=0):
    try:
        return safe_int(eval('AFiles("'+book_name+'_'+str(vol)+'_TLINE")'))
    except:
        return None
def max_page(book_name):
    try:
        return safe_int(eval('AFiles("'+book_name+'_TPage")'))
    except:
        try:
            return safe_int(eval('AFiles("'+book_name+'_0_TPage")'))
        except:
            return None
    
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

    files = eval('AFiles()')
    vol_files = []  
    for f in files:
        if f.lower().startswith(book_name) and f.lower().endswith('_book.txt'):
            base = f[:-9]
            if base == book_name:
                vol_files.append((0, f))
            else:
                if '(' in base and base.endswith(')'):
                    lpos = base.rfind('(')
                    rpos = base.rfind(')')
                    if lpos != -1 and rpos != -1 and lpos < rpos:
                        num_str = base[lpos+1:rpos]
                        if num_str.isdigit():
                            vol = int(num_str)
                            vol_files.append((vol, f))

    maxx, maxy = max_chars()
    all_pages = []     
    all_contents = []  
    all_pictures = []   
    global_page = 0  

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

    for vol, fname in vol_files:
        with open(fname, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]

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

        for line_idx, paragraph in enumerate(lines):
            ch, title = parse_ch_structure(paragraph)
            if ch is not None:
                close_current_page()
                local_page_num = len(pages) + 1
                contents.append((title, local_page_num))
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
                    local_page_num = start_page_before + 1
                    pictures.append((pic_name, local_page_num))
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

        vol_page_offset = global_page
        for s_l, s_c, e_l, e_c in pages:
            all_pages.append((vol, s_l, s_c, e_l, e_c))
        for title, local_page in contents:
            all_contents.append((title, local_page + vol_page_offset))
        for pic_name, local_page in pictures:
            all_pictures.append((pic_name, local_page + vol_page_offset))
        global_page += len(pages)
        eval('"' + str(len(lines)) + '"▶AFiles("' + book_name + '_' + str(vol) + '_TLINE")')
        eval('"' + str(len(pages)) + '"▶AFiles("' + book_name + '_' + str(vol) + '_TPage")')
        del lines, contents, pictures, pages
        gc.collect()

    if not all_pages:
        all_pages.append((0, 0, 0, 0, 0))
        global_page = 1

    total_lines_all = 0
    for vol, _ in vol_files:
        try:
            total_lines_all += safe_int(eval('AFiles("' + book_name + '_' + str(vol) + '_TLINE")'))
        except:
            pass
    eval('"' + str(global_page) + '"▶AFiles("' + book_name + '_TPage")')
    eval('"' + str(total_lines_all) + '"▶AFiles("' + book_name + '_TLINE")')

    with open(book_name + "_list.txt", "w", encoding="utf-8") as f:
        f.write("PAGES\n")
        for vol, s_l, s_c, e_l, e_c in all_pages:
            f.write(str(vol) + " " + str(s_l) + " " + str(s_c) + " " + str(e_l) + " " + str(e_c) + "\n")
        f.write("CONTENTS\n")
        for title, pnum in all_contents:
            f.write(str(pnum) + "\t" + title + "\n")
        f.write("PICTURES\n")
        for pic_name, pnum in all_pictures:
            f.write(str(pnum) + "\t" + pic_name + "\n")
    del all_pages, all_contents, all_pictures
    gc.collect()
    return
#行号映射页码
def find_page_by_coord(pages, vol, line_idx, col_idx):
    lo, hi = 0, len(pages) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if pages[mid][0] < vol:
            lo = mid + 1
        elif pages[mid][0] > vol:
            hi = mid - 1
        else:
            if pages[mid][1] <= line_idx:
                lo = mid + 1
            else:
                hi = mid - 1
    if hi < 0:
        return None
    v, s_l, s_c, e_l, e_c = pages[hi]
    if v == vol and (line_idx < e_l or (line_idx == e_l and col_idx <= e_c)):
        return hi
    else:
        if hi + 1 < len(pages):
            v2, s_l2, s_c2, e_l2, e_c2 = pages[hi+1]
            if v2 == vol and s_l2 == line_idx:
                return hi + 1
        return None
#读写书签文件
def load_bookmarks(book_name):
    bookmarks = []
    try:
        with open(book_name + "_bookmarks.txt", 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 4:
                    vol = safe_int(parts[0])
                    s_l = safe_int(parts[1])
                    s_c = safe_int(parts[2])
                    comment = '\t'.join(parts[3:])
                    bookmarks.append((vol, s_l, s_c, comment))
                elif len(parts) == 3: 
                    s_l, s_c, comment = parts
                    bookmarks.append((0, safe_int(s_l), safe_int(s_c), comment))
    except:
        pass
    return bookmarks

def save_bookmarks(book_name, bookmarks):
    with open(book_name + "_bookmarks.txt", 'w', encoding='utf-8') as f:
        for vol, s_l, s_c, comment in bookmarks:
            f.write(str(vol) + "\t" + str(s_l) + "\t" + str(s_c) + "\t" + comment + "\n")
#添加书签
def add_bookmark(book_name, current_page):
    data = load_list(book_name)
    eval('TXS:="书签"')
    if eval('INPUT({{P,[0]},{TXS,[2]}},"添加书签",{"页码","注释"},{"当前页码","输入注释内容"},{' + str(current_page+1) + '},{'+str(current_page+1)+'})') == 0:
        return
    p_input = safe_int(eval('P'))
    if p_input < 1 or p_input > len(data["Pages"]):
        eval('MSGBOX("错误的输入！")')
        return
    vol, s_l, s_c, _, _ = data["Pages"][p_input - 1]
    comment = eval('TXS').strip()
    if comment == "":
        eval('MSGBOX("注释不能为空！")')
        return
    bookmarks = load_bookmarks(book_name)
    bookmarks.append((vol, s_l, s_c, comment))
    bookmarks.sort(key=lambda x: (x[0], x[1], x[2]))
    save_bookmarks(book_name, bookmarks)
    eval('MSGBOX("书签已添加！")')
    return
#书签管理
def manage_bookmarks(book_name):
    bookmarks = load_bookmarks(book_name)
    if not bookmarks:
        eval('MSGBOX("暂无书签！")')
        return
    data = load_list(book_name)
    pages = data["Pages"]
    while True:
        display_items = []
        bookmarks = load_bookmarks(book_name)
        if bookmarks == []:
            return
        for vol, s_l, s_c, comment in bookmarks:
            page_idx = find_page_by_coord(pages, vol, s_l, s_c)
            page_num = str(page_idx + 1) if page_idx is not None else "?"
            short = comment[:10] + ("..." if len(comment) > 10 else "")
            display_items.append("P%s %s" % (page_num, short))
        selected = show_list("书签列表", display_items, 0)
        if selected == -1:
            return
        vol, s_l, s_c, comment = bookmarks[selected]
        page_idx = find_page_by_coord(pages, vol, s_l, s_c)
        opts = '"查看原文","查看注释","删除书签","返回"'
        while True:
            if eval('CHOOSE(N,"书签(P'+ str(page_idx+1) + ')",' + opts + ')') == 0:
                continue
            choice = safe_int(eval('N'))
            if choice == 1:
                jump_page(book_name, page_idx)
            elif choice == 2:
                safe_comment = comment.replace('"', '\\"')
                eval('MSGBOX("' + safe_comment + '")')
            elif choice == 3:
                if eval('MSGBOX("确定删除该书签？",1)') == 0:
                    continue
                del bookmarks[selected]
                save_bookmarks(book_name, bookmarks)
                eval('MSGBOX("已删除书签！")')
                break
            elif choice == 4:
                break
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

def show_pic(floortext,pic_name,page,book_name):
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
            elif event == 3:
                add_bookmark(book_name,page)
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
            if len(parts) == 5:
                vol, s_l, s_c, e_l, e_c = map(int, parts)
            elif len(parts) == 4:  
                s_l, s_c, e_l, e_c = map(int, parts)
                vol = 0
            else:
                continue
            data["Pages"].append((vol, s_l, s_c, e_l, e_c))
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
    
def load_book_text(book_name, vol):
    global _text_cache, _text_cache_book, _text_cache_vol
    if _text_cache_book == book_name and _text_cache_vol == vol and _text_cache is not None:
        return _text_cache
    fname = book_name + "(" + str(vol) + ")_book.txt"
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
    except OSError:
        if vol == 0:
            fname = book_name + "_book.txt"
            with open(fname, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f]
        else:
            raise

    _text_cache_book = book_name
    _text_cache_vol = vol
    _text_cache = lines
    return lines

#阅读器主函数
def start_read(book_name, page):
    data = load_list(book_name)
    pages = data["Pages"]
    total_pages = len(pages)

    current_vol = -1
    lines_cache = None

    while True:
        vol, s_l, s_c, e_l, e_c = pages[page]  

        if current_vol != vol:
            lines_cache = load_book_text(book_name, vol)
            current_vol = vol
        eval('"' + str(vol) + "," + str(s_l) + "," + str(s_c) + '"▶AFiles("' + book_name + '_Post")')

        show_str = ""
        if s_l == e_l:  
            show_str = lines_cache[s_l][s_c:(e_c+1)]
            ch, title = parse_ch_structure(show_str)
            if ch is not None:
                show_str = ch + ' ' + title if ch else title
            elif show_str.startswith("[pic:"):
                try:
                    pic_name = show_str[5:show_str.find(']')]
                    picevent = show_pic(book_name + '  ' + str(page+1) + '/' + str(total_pages),
                                        pic_name, page, book_name)
                    if picevent == 0:
                        return  
                    elif picevent == -1:
                        if page > 0:
                            page -= 1
                        continue
                    elif picevent == 1:
                        if page < total_pages - 1:
                            page += 1
                        continue
                except KeyboardInterrupt:
                    raise
                except:
                    pass
                continue
        else:
            parts = []
            first_line = lines_cache[s_l][s_c:]
            ch, title = parse_ch_structure(first_line)
            if ch is not None:
                first_line = ch + ' ' + title if ch else title
            parts.append(first_line)
            for i in range(s_l+1, e_l):
                parts.append(lines_cache[i])
            last_line = lines_cache[e_l][:(e_c+1)]
            parts.append(last_line)
            show_str = '\n'.join(parts)
        show_text(show_str, book_name + '  ' + str(page+1) + '/' + str(total_pages))
        while True:
            draw_time()   
            key_code = eval("WAIT(0)")
            if key_code == 30 or key_code == 12 or key_code == 8:
                if page < total_pages - 1:
                    page += 1
                    break
            elif key_code == 2 or key_code == 7:
                if page > 0:
                    page -= 1
                    break
            elif key_code == 4:
                gc.collect()
                return
            elif key_code == 3:
                add_bookmark(book_name, page)
                break
                
def jump_page(book_name, page):
    current_page = get_position(book_name)
    data = load_list(book_name)
    s_vol, s_l, s_c = data["Pages"][current_page][0], data["Pages"][current_page][1], data["Pages"][current_page][2]
    start_read(book_name, page)
    eval('"'+str(s_vol)+","+str(s_l)+","+str(s_c)+'"▶AFiles("'+book_name+'_Return")')

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
        get_choose = safe_int(eval("N"))
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
                inpage = safe_int(inpage)
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
#书本选择菜单
def get_book_list():
    files = eval('AFiles()')
    book_vols = {}
    for f in files:
        if f.lower().endswith('_book.txt'):
            base = f[:-9]  
            if '(' in base and base.endswith(')'):
                lpos = base.rfind('(')
                rpos = base.rfind(')')
                if lpos != -1 and rpos != -1 and lpos < rpos:
                    num_str = base[lpos+1:rpos]
                    if num_str.isdigit():
                        prefix = base[:lpos]
                        vol = int(num_str)   # 0-based
                    else:
                        prefix = base
                        vol = 0
                else:
                    prefix = base
                    vol = 0
            else:
                prefix = base
                vol = 0
            line_count = max_line(prefix, vol)
            book_vols.setdefault(prefix, []).append((vol, line_count))

    txt_files = []
    for prefix, vol_list in book_vols.items():
        vol_list.sort()
        total_lines = sum(v[1] for v in vol_list if v[1] is not None)
        pos_str = eval('AFiles("'+prefix+'_Post")')
        parts = pos_str.split(',')
        if len(parts) == 3:
            vol, line, col = parts
            read_lines = 0
            for v, lc in vol_list:
                if v < int(vol):
                    read_lines += lc
                elif v == int(vol):
                    read_lines += int(line)
                    break
        else:
            read_lines = 0
        txt_files.append((prefix, read_lines, total_lines))
    return txt_files

def choose_book():
    global _text_cache,_index_cache,_cache_book_name,_text_cache_book
    _text_cache = None
    _index_cache = None
    _cache_book_name = ""
    _text_cache_book = ""
    gc.collect()
    book_list = get_book_list()
    book_show = []
    for i in range(len(book_list)):
        if not(book_list[i][2] == 0) and not(book_list[i][1] == 0):
            book_show.append("%04.1f%% " % (100*book_list[i][1]/book_list[i][2]) + book_list[i][0])
        else:
            book_show.append('00.0% ' + book_list[i][0])
    action = show_list('书架',book_show,0)
    if action == -1:
        return None
    return book_list[action][0]
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
    total = len(pages)
    if end_page is None or end_page >= total:
        end_page = total - 1
    start = max(0, start_page)
    end = min(total - 1, end_page)
    if start > end:
        return []
    files = eval('AFiles()')
    vols = set()
    for f in files:
        if f.startswith(book_name) and f.endswith('_book.txt'):
            base = f[:-9] 
            if base == book_name:
                vols.add(0)
            else:
                if '(' in base and base.endswith(')'):
                    lpos = base.rfind('(')
                    rpos = base.rfind(')')
                    if lpos != -1 and rpos != -1 and lpos < rpos:
                        num_str = base[lpos+1:rpos]
                        if num_str.isdigit():
                            vols.add(int(num_str))
    vols = sorted(vols)
    results = []
    MAX_RESULTS = 200
    kw_lower = keyword.lower()
    kw_len = len(keyword)
    start_vol = pages[start][0]
    end_vol = pages[end][0]
    target_vols = [v for v in vols if start_vol <= v <= end_vol]

    for vol in target_vols:
        lines = load_book_text(book_name, vol)
        for line_idx, line in enumerate(lines):
            line_lower = line.lower()
            search_start = 0
            while True:
                col_idx = line_lower.find(kw_lower, search_start)
                if col_idx == -1:
                    break
                page_idx = find_page_by_coord(pages, vol, line_idx, col_idx)
                if page_idx is not None and start <= page_idx <= end:
                    ctx_start = max(0, col_idx - 5)
                    ctx_end = min(len(line), col_idx + kw_len + 5)
                    raw_context = line[ctx_start:ctx_end]
                    kw_start_in_ctx = col_idx - ctx_start
                    kw_end_in_ctx = kw_start_in_ctx + kw_len
                    context = raw_context[:kw_start_in_ctx] + '~' + raw_context[kw_end_in_ctx:]
                    results.append([page_idx + 1, [vol, line_idx, col_idx, col_idx+kw_len], context])
                    if len(results) >= MAX_RESULTS:
                        eval('MSGBOX("结果超过200条，仅显示前200条")')
                        return results
                search_start = col_idx + 1
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
    try:
        if eval("CHOOSE(N,\"菜单\",\"书架\",\"设置\",\"关于\",\"退出\")") == 0:
            continue
        get_menu = safe_int(eval("N"))
        if get_menu == 4:
            break
        elif get_menu == 3:
            eval("MSGBOX(\"EBOOKREADER 一款强大的阅读器 运行过程中出现创建变量提示请点击是 made by CPTPotato 版本："+version+"\")")
        elif get_menu == 2:
            if eval('INPUT({{C,{"暖阳","暗夜","清绿","素白","羊皮","自定义"}},{S,{"小","中","大"}}},"设置",{"配色方案","字体大小"},{"自定义颜色","修改字体后请重建所有索引"});') == 0:
                continue
            if safe_int(eval("C")) == 6:
                eval('BGC:="#0h"')
                eval('TXC:="#FFFFFFh"')
                eval('MSGBOX("请保证输入颜色格式正确！")')
                if eval('INPUT({{BGC,[2]},{TXC,[2]}},"自定义颜色",{"背景颜色","文本颜色"},{"输入颜色，形式如#FFFFFFh","输入颜色，形式如#FFFFFFh"})') == 0:
                    eval('MSGBOX("已取消自定义！设置未保存")')
                    continue
                TEXT_COLOR = eval('TXC')
                BG_COLOR = eval('BGC')
            else:
                TEXT_COLOR = COLOR_LIST[0][safe_int(eval("C"))-1]
                BG_COLOR = COLOR_LIST[1][safe_int(eval("C"))-1]
            eval("\""+str(safe_int(eval('S'))-1)+"\""+"▶AFiles(\"FONT_SIZE\")")  
            eval("\""+TEXT_COLOR+"\""+"▶AFiles(\"TEXT_COLOR\")")  
            eval("\""+BG_COLOR+"\""+"▶AFiles(\"BG_COLOR\")")  
            load_set()
        elif get_menu == 1:
            while True:
                book_name = choose_book()
                if book_name == None:
                    break
                while True:
                    if eval("CHOOSE(N,"+"\""+book_name+"\",\"继续阅读\",\"查看目录\",\"跳转页码\",\"查看图片\",\"检索内容\",\"书签管理\",\"构建索引\",\"返回\")") == 0:
                        continue
                    action = safe_int(eval("N"))
                    if action == 8:
                        break
                    elif action == 5:
                        if not check_file(book_name+"_list.txt"):
                            eval('MSGBOX("请先构建索引！")')
                            continue
                        eval('TXS:="文本"')
                        maxpage = max_page(book_name)
                        if eval('INPUT({A,B,{TXS,[2]}},"检索内容",{"起始页","结束页","关键词"},{"检索起始页码","检索结束页码","检索的关键词"},{1,'+str(maxpage)+'},{1,'+str(maxpage)+'})') == 0:
                            continue
                        result = search_book(book_name,eval('TXS'),safe_int(eval('A'))-1,safe_int(eval('B'))-1)
                        show_search(book_name,result)
                    elif action == 7:
                        if eval("MSGBOX(\"确定构建索引？本操作可能耗时较久！\",1)") == 0:
                            continue
                        build_list(book_name)
                        eval('MSGBOX("已构建索引！")')
                    elif action == 3:
                        if not check_file(book_name+"_list.txt"):
                            eval('MSGBOX("请先构建索引！")')
                            continue
                        maxpage = max_page(book_name)
                        ret_str = eval('AFiles("'+book_name+'_Return")')
                        vol,line, col = unpack_pos(ret_str)
                        if line is not None:
                            data = load_list(book_name)
                            position = find_page_by_coord(data["Pages"],vol, line, col)
                        else:
                            position = 0
                        if eval('INPUT(N,"跳转页码","跳转到","范围：1-'+str(maxpage)+' (默认值：上次跳转前位置)",'+str(position+1)+','+str(position+1)+')') == 0:
                            continue
                        page = eval("N")
                        try:
                            page = safe_int(page)
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
                    elif action == 6:
                        if not check_file(book_name+"_list.txt"):
                            eval('MSGBOX("请先构建索引！")')
                            continue
                        manage_bookmarks(book_name)
    except KeyboardInterrupt:
        print('按下on键已退出')
        sys.exit(0)
    except MemoryError:
        eval('MSGBOX("内存不足！尝试按shift+plot调大Heap或使用更小的分卷尺寸后重启")')
    except Exception as e:
        print("发生错误：",repr(e),"程序退出")
        raise
