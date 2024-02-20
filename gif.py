
def load_file(file_name):
    try:
        with open(file_name, "rb") as file:
            return file.read(), file_name
    except:
        return b"" , "file not found"

def extract_header(data):
    return data[:6].decode()

def extract_screen_descriptor(data):
    width = int.from_bytes(data[6:8], "little")
    height = int.from_bytes(data[8:10], "little")
    packed = bin(data[10])[2:]
    
    gc_fl = int(packed[0])
    cr = int(packed[1:4],2)
    sort_fl = int(packed[4],2)
    gc_size = int(packed[5:8],2)
    
    bcolour_i = data[11]
    pix_asp_ra = data[12]

    return width, height, gc_fl, cr, sort_fl, gc_size, bcolour_i, pix_asp_ra

def extract_global_colour_table(data):
    # logical screen descriptor (N)
    packed = bin(data[10])[2:]
    N = int(packed[5:8],2)

    # number of colours (k)
    k = 2**(N+1)

    # Global colour table : rgb nested-list
    table = []
    newdata = data[13:(13+3*k)]
    for n in range(k):
        table.append([newdata[3*n], newdata[1+3*n], newdata[2+3*n]])

    return table

def extract_image_descriptor(data):
    x = data.find(b",")
    newdata = data[x:x+10]
    left = int.from_bytes(newdata[1:3], "little")
    top = int.from_bytes(newdata[3:5], "little")
    width = int.from_bytes(newdata[5:7], "little")
    height = int.from_bytes(newdata[7:9], "little")
    packed = bin(newdata[9])[2:].zfill(8)

    lc_fl = int(packed[0])
    itl_fl = int(packed[1])
    sort_fl = int(packed[2])
    res = int(packed[3:5])
    lc_size = int(packed[5:8])

    return left, top, width, height, lc_fl, itl_fl, sort_fl, res, lc_size

def extract_image(data):
    # min_code_sz and num_of_bytes location
    x = data.find(b",") + 10
    y = x+1

    # canvas size
    newdata = data[x-10:x]
    w = int.from_bytes(newdata[5:7], "little")
    h = int.from_bytes(newdata[7:9], "little")

    # global colour (k=number of colours) and table  
    packed = bin(data[10])[2:]
    N = int(packed[5:8],2)
    lst_k = [i for i in range(2**(N+1))]
    c_table = extract_global_colour_table(data)
    
    # setting up main variables
    ind_stream = []
    min_code_sz = data[x]
    lst_data = []
    bit_len = min_code_sz + 1
    last = 2+2**min_code_sz
    next_code = last
    prevcode = 0
    
    # initialize the code table
    col_codes = [i for i in range(last)]
    code_table = {key:None for key in col_codes}
    code_table[last-2], code_table[last-1] = ["Clear Code"], ["End of Information Code"]
    for ind, c in enumerate(lst_k):
        code_table.update({ind:[c]})
    
    #collecting all data from all sub-blocks
    while (data[y] != 0):
        start_data = y+1
        end_data = y+data[y]
        encoded_data = "".join(format(i, '08b')[::-1] for i in data[start_data:end_data+1])
        lst_data.extend(list(encoded_data))
        y += data[y] +1
   
    # start reading after "Clear Code"
    code = int("".join(lst_data[2*bit_len-1:bit_len-1:-1]),2)
    del lst_data[:2*bit_len]
    ind_stream.extend(code_table[code])
    prevcode = code

    # lzw decoding loop
    while ind_stream[-1] != "End of Information Code":
        code = int("".join(lst_data[bit_len-1::-1]),2)
    
        if code in code_table:
            ind_stream.extend(code_table[code])
            K = code_table[code][0]
            code_table[next_code] = code_table[prevcode] +[K]

        else:
            plus_K = code_table[prevcode] + [code_table[prevcode][0]]
            ind_stream.extend(plus_K)
            code_table[next_code] = plus_K
        
        del lst_data[:bit_len]
        prevcode = code
        
        if next_code == (2**bit_len)-1:
            bit_len += 1
        next_code += 1

    ind_stream.remove("End of Information Code")

    #create 3D list
    rgb_changed = [c_table[i] for i in ind_stream]  
    img = [rgb_changed[i:i+w] for i in range(0, w*h, w)]

    return img
    
def main():
    print()
    print('GIF Image Viewer') 
    print()
    
    file_name = "sample_1_enlarged.gif"
    data, info = load_file(file_name) 
    for i in range(len(data)):
         print(hex(data[i])) 
    print(type(data))
    print()
    
    # extract GIF signature 
    signature = extract_header(data) 
    print(signature)
    print()
    
    # extract screen descriptor
    scn_w, scn_h, scn_gc_fl, scn_cr, scn_sort_fl, scn_gc_size, scn_bcolour_i, scn_px_ratio = extract_screen_descriptor(data)
    print('screen width: ', end='') 
    print(scn_w)
    print('screen height: ', end='') 
    print(scn_h)
    print('global color table flag: ', end='') 
    print(scn_gc_fl)
    print('colour resolution: ', end='') 
    print(scn_cr)
    print('sort flag: ', end='') 
    print(scn_sort_fl)
    print('global colour size: ', end='') 
    print(scn_gc_size)
    print('background colour index: ', end='') 
    print(scn_bcolour_i)
    print('pixel aspect ratio: ', end='') 
    print(scn_px_ratio)
    print()

    # extract global color map
    gc_table = extract_global_colour_table(data)

    for i in range(2**(scn_gc_size+1)): 
        print("#",end='') 
        print(i,end='\t') 
        print(gc_table[i][0],end='\t') 
        print(gc_table[i][1],end='\t') 
        print(gc_table[i][2])
    print()

    # extract image descriptor
    img_left, img_top, img_w, img_h, img_lc_fl, img_itl_fl, img_sort_fl, img_res, img_lc_size = extract_image_descriptor(data)
    print('image left: ', end='') 
    print(img_left)
    print('image top: ', end='') 
    print(img_top)
    print('image width: ', end='')
    print(img_w)
    print('image height: ', end='')
    print(img_h)
    print('local colour table flag (0: global, 1: local) : ', end='')
    print(img_lc_fl)
    print('interlace flag (0: sequential, 1: interlaced): ', end='') 
    print(img_itl_fl)
    print('sort flag (0: unorderd, 1: ordered): ', end='') 
    print(img_sort_fl)
    print('reserved values: ', end='')
    print(img_res)
    print('local colour table size: ', end='') 
    print(img_lc_size)
    print()

    # extract image data
    img = extract_image(data)
    # print image red channel 
    print('img red channel:') 
    for i in range(len(img)):
        for j in range(len(img[0])): 
            print(img[i][j][0],end='\t')
        print()
    print()
    # print image green channel 
    print('img green channel:') 
    for i in range(len(img)):
        for j in range(len(img[0])): 
            print(img[i][j][1],end='\t')
        print()
    print()
    # print image blue channel 
    print('img blue channel:') 
    for i in range(len(img)):
        for j in range(len(img[0])): 
            print(img[i][j][2],end='\t')
        print()
    print()

if __name__ == "__main__":
    main()
