from PIL import Image
from base64 import b64encode
from io import BytesIO
from time import time
from random import randint

#   ICON BASE64 HASH        TUPLE OF TEXTS ASSOCIATED WITH ICON         (multiple mappings may exist for each individual icon due to uncertainty of the anti-aliasing that happens on GF servers)
icons_to_texts     =     {
 '+PZPBAAAAwMIBAzlJm2o': ('/vj34N3o5+vr4+f++/wA', '/vf24N/m5urq5eb9/PwA'),
 '23nx7oteW3n45krqB7Vw': ('/vb13dzk5ubl297++fkA', 'APb03uDm5+fm2t4AAAAA' , '/vf23tzl5ubk3N79+foA'),
 '31IyUgYCaWDPALimKmb+': ('/vX03+Hq4+jq2dsAAAAA', '/vb04N/s4+jq2NsAAAAA'),
 '5qov13hCSRKlpIZrkxi7': ('+/X249vo4+vr3OL++/wA', '/PX34ODh4Ofn3t/9/PwA'),
 'AAYrIpL6NH9L8Cl3NQw8': ('/PX049/o4ufm2t4AAAAA', '/PX04+Dn4OXn2t4AAAAA'),
 'Ayofi65ARKfuEiQdDvnd': ('APf23d/t6enq3eAAAAAA', 'APj23N7r6enq3eAAAAAA'),
 'CBIWFA0A9d29on1PJPC3': ('/PX14Nvl4OPk298AAAAA', '/PX039ri3uLj2twAAAAA'),
 'CKBiaqxhODImGhAMEhIS': ('/Pb15ODr5erq3d8AAAAA', '/PX04uHo4+jo3uAAAAAA'),
 'Cw/sc8MQU5LnRrI5v2RU': ('APn43tnk2d/i2dkAAAAA', 'APn53trr3uHk298AAAAA'),
 'DkFxnMHf9xAeJS0yMC85': ('APn53trh4eHi3OAAAAAA', 'APr539vi4+Pk3+IAAAAA'),
 'FsBAjO3/nRh7UYIGrSUC': ('/PHz5OTn5+rp3d79+foA', '+/Dw4eHl5ejo2t3++fkA'),
 'HqQpk9QkVGVxWksd0443': ('+/X229nj4uPl3d8AAAAA', '/PX33Nvm4+Pk3+AAAAAA'),
 'In9Lr7PjGEx+j9TIt2EJ': ('/vr6397l4eXl3uAAAAAA', '/vn53tzh3+Tk3t8AAAAA'),
 'JW1v1cHMWVqHW6DCdCPw': ('/vf24N3q3OHn1tgAAAAA', '/vf239zs2+Ho1tgAAAAA'),
 'K0cwDcaki4WGhpSy5jEe': ('APn54d7k5OTl3eH++fkA', 'APr54d/j5eXk4OH9+foA'),
 'Li80NTg4Oz0+Pjs5NdUy': ('APDv4eHj4OXl3+H+/v4A', 'APLy4+Tp5enq4eT+/v4A'),
 'M+l9yVF6a9Hf08q4o35e': ('/vv74d/m4+fl3eL8/PwA', '/vz64dzj5OXi3N78/PwA'),
 'NTJlQAfFmLDp8Gc7wejy': ('/O3t3t/h3Orq4uQAAAAA', '/e/w4eTk3+zt5ucAAAAA'),
 'O3G4AzZUZW96hqJEJp5B': ('/vPz3uDj4Ojo2t0AAAAA', '/vPw3dzj3+fm19wAAAAA'),
 'OR+F2DNOk6G0qsZLrtHu': ('/vj44eDd2+fn4uYAAAAA', '/vf34Nvh3+bm4uUAAAAA'),
 'Ocsx+FMQwp381bi380ja': ('/PDy4+Pg4O3r4uL/+/sA', '++7w4+Dj4e7t3+IA+/sA'),
 'Pnm4gE9CXJLXYFb/jYBr': ('/vb339/m5Onp3uAAAAAA', '/fb2393n5ero3OAAAAAA'),
 'Qz1BtMm8spx7Wy37vnks': ('APr63uDl3+jp4OIAAAAA', 'APn43t3j3efn3eAAAAAA'),
 'SeSMR/Sqc0kZ/N3MppS2': ('+vP24+Ho5efn4OH9+foA', '+PP25eLn5Ofp3+H++fkA'),
 'Vo2s1OsCFSg+YHORq9MJ': ('/PPz4eDj4Ojo3+EAAAAA', '/PPx393j4Ojn3N8AAAAA'),
 'YqD/fo6SaYJCNwHz5FTn': ('/vb13uDm4err4uMAAAAA', '/vXz3dzk3+np3uEAAAAA'),
 'bcQHDBEMBc+9fzTfc/WQ': ('APn43dro4+fn3N/++fkA', 'APn33Nzm4efm3eD9+foA'),
 'dfeYGYKgEfkZYJ+NwLBd': ('APb349/v5vDv3d4AAAAA', 'APT24OHq4uzt3dwAAAAA'),
 'dnFhxCdeFMjboa7rN/7h': ('/fj529nm4uXs2NsAAAAA', '/vj53Njm4+bq19gAAAAA'),
 'dvFKfY9ejtvHwvkhSyVZ': ('/fX14uTt5ufp3OAAAAAA', '/vX24uXu5eXn3N4AAAAA'),
 'iYeHh4eHh4eHh4eHh4eH': ('/vj34N3n5eno2d0AAAAA',),
 'k2epIVghl3yjDUx9kJ+s': ('APv739zk4ubn4eL9/PwA', 'APr53Nnl3+Tm3eD++/wA'),
 'lWLxIJaaxQZWuRIEH0V9': ('APb13d/q5ujp3uAAAAAA', 'APbz3N7k4uXn3OAAAAAA'),
 'm4x8cndnXV9jXFhXVlda': ('APf23Nnj3OLj2d3++fkA', 'APj32tzi3uPk3d79+foA'),
 'oObRbENHF+gcatya2OtU': ('APj34uHo6Orp3+AAAAAA', 'APj24eHj5efo3eEAAAAA'),
 'pgHHgbRVvMDYssvBUzAp': ('/PT13N3n5Ojp4uQAAAAA', '+/Pz19rf3+Tk3+EAAAAA'),
 'ubm4vLq8ury+wbzAwb7C': ('/vf33tnh4ePj2t4AAAAA', '/vf23djg4ePj2t0AAAAA'),
 'vn6fEoAKgDD0xJt+Zk03': ('+/X23Nnf3t7f29wAAAAA', '/PX339zk4OHj3OAAAAAA'),
 'vreuppmWf243MC7Gw7Cw': ('APz84ODr5+fo2d38/PwA', 'APv63t7l4+Tj19r8/PwA'),
 'whJsa5CySTovcqJI9ZKx': ('APf339zn4+3r4eQAAAAA', 'APj44N/n4+3t5eYAAAAA'),
 'wjeUAIkmznz/Q0tKPQ9U': ('APr539zm6OXm4eMAAAAA', 'APn44d/k5Ofn3+QAAAAA'),
 'xgMqGmp0UJYIohqocUJM': ('APn43dzq3ODk2Nz+/v4A', 'APn439vq3uTl2tz+/v4A'),
 'xgpFi5avYcTSqbE/b0WT': ('/PX05OLn6Ojm2t0AAAAA', '/Pb15eLq6unp298AAAAA'),
 'yatBgon7woVQMiQeIyo6': ('/vb23t3j5Ofn4+UAAAAA', '/vb13Nzf4uXl4eQAAAAA')}
 
def image_hash(image):
    """Will output a "hash" of a greyscale image. The hash is actually just a tuple containg 15 numbers, each of which is the sum of all the pixels in that row modulated by 256. A pixel is just a number between 0 and 255.
    This tuple is then converted into a base64 string, because it is easier to store it in this file.
    """
    sum = [0]*15
    for i in range(0,15):
        for j in range(0,image.size[0]):
            sum[i] = ( sum[i] + image.getpixel((j,i)) ) % 256
    return b64encode(bytes(tuple(sum))).decode('ascii')


def cut_text(image):
    """Takes in the image containing text and cuts in strategically and turns it into greyscale   
    """
    crop_x = 0
    #find left edge of the letter D to undo centering
    for i in range(0,100):
        if image.getpixel((i,7)) != (0,0,0,0):
            crop_x = i-1
            break
    image = image.crop((crop_x+60,0,crop_x+115,15))
    image = image.convert('L')
    return image

def cut_drag(image):
    """Takes in a drag icons image that contains 4 other images, cuts it up strategically, turns it into greyscale and returns a tuple containg the 4 seperate images.
    """
    image = image.crop((0,22,image.size[0],37))
    image = image.convert('L')
    return (
            image.crop((image.size[0]/4 * 0, 0, image.size[0]/4 * 1, image.size[1])),
            image.crop((image.size[0]/4 * 1, 0, image.size[0]/4 * 2, image.size[1])),
            image.crop((image.size[0]/4 * 2, 0, image.size[0]/4 * 3, image.size[1])),
            image.crop((image.size[0]/4 * 3, 0, image.size[0]/4 * 4, image.size[1])),
           )
           
def break_interactive_captcha(text_image, drag_icons):
    """This function will attempt to break the interactive captcha by finding the index of the icon specified by the text inside of the text_image image.
    Parameters
    ----------
    text_image : bytes
        bytes of text_image
    drag_icons : bytes
        bytes of darg_icons
    Returns
    -------
    index : int
        index of the exact image refrenced to by the text in text_image that is contained in the four images in drag_icons
    """
    
    if isinstance(text_image, (bytes, bytearray)):
        text_image = Image.open(BytesIO(text_image))
        assert text_image.size[0] == 330, "Failed to convert text image bytes into Pillow Image object"
    if isinstance(drag_icons, (bytes, bytearray)):
        drag_icons = Image.open(BytesIO(drag_icons))
        assert drag_icons.size == (240,60), "Failed to convert drag icons bytes into Pillow Image object"
        
        
    
    text_image_old = text_image
    text_image = cut_text(text_image)
    text_image_hash = image_hash(text_image)
    
    target = ""
    
    for key, value in icons_to_texts.items():
        if text_image_hash in value:
            target = key
    
    if target == "":
        #if we haven't found target, then something went wrong, save images for later analysis
        rnd = str(round(time()))
        drag_icons.save('drag_icons-{}.png'.format(str(rnd)))
        text_image_old.save('text_image-{}.png'.format(str(rnd)))

    assert target != "", "Couldn't find text image in local store"
    
    i = 0
    for icon in cut_drag(drag_icons):
        if image_hash(icon) == target:
            return i
        i+=1
    
    #if we haven't returned it, then something went wrong, save image for later analysis
    rnd = str(round(time()))
    drag_icons.save('app/lobby_captcha/failures/drag_icons-{}.png'.format(str(rnd)))
    text_image_old.save('app/lobby_captcha/failures/text_image-{}.png'.format(str(rnd)))
    
    raise Exception("Couldn't find icon image in local store")
 
 
 
 
 
 
 
