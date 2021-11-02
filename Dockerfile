FROM frost2k5/dragonheart:master

RUN mkdir /Fizilion && chmod 777 /Fizilion && git clone https://github.com/AbOuLfOoOoOuF/ProjectFizilionFork -b pruh /Fizilion
ENV PATH="/Fizilion/bin:$PATH"
WORKDIR /Fizilion
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3","-m","userbot"]
